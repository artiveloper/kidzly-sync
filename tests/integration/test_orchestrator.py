"""``SyncOrchestrator`` 의 이력 기록 / 스킵 판단 통합 테스트.

UseCase 는 가짜로 두고, ``sync_histories`` 에 실제로 무엇이 남는지만 본다.
INSERT 후 id 회수, 같은 행 UPDATE, 날짜 경계 판단은 실제 DB 없이 검증할 수 없다.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.orchestrator import SyncOrchestrator
from kidzly_sync.common.time import now_kst
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.entity.sync_history import SyncStatus, SyncType
from kidzly_sync.domain.result import Err, Ok
from kidzly_sync.infrastructure.persistence.sync_history_repository import SyncHistoryRepositoryImpl

pytestmark = pytest.mark.integration


class StubUseCase:
    def __init__(self, result) -> None:
        self._result = result
        self.call_count = 0

    def execute(self):
        self.call_count += 1
        return self._result


class SpyNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, text: str) -> None:
        self.messages.append(text)


@pytest.fixture
def history_repository(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sync_histories")
    conn.commit()
    return SyncHistoryRepositoryImpl(conn)


def latest_history(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, sync_type, status, total_count, upsert_count, error_message, finished_at"
            " FROM sync_histories ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        columns = [d.name for d in cur.description]
        return dict(zip(columns, row, strict=True))


def history_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sync_histories")
        return cur.fetchone()[0]


def build(use_case, history_repository, notifier, *, playground=None) -> SyncOrchestrator:
    return SyncOrchestrator(
        sigungu_code_sync_use_case=use_case,
        playground_full_sync_use_case=playground or StubUseCase(Ok(SyncResult(total=0, upserted=0))),
        sync_history_repository=history_repository,
        telegram_notifier=notifier,
    )


# ── 성공 경로 ─────────────────────────────────────────────────────────────────


def test_records_a_single_completed_row_on_success(conn, history_repository):
    notifier = SpyNotifier()
    orchestrator = build(StubUseCase(Ok(SyncResult(total=49861, upserted=12))), history_repository, notifier)

    assert orchestrator.sigungu_code_sync() is True

    # RUNNING 으로 INSERT 한 뒤 같은 행을 UPDATE 해야 한다 — 두 행이 남으면 id 회수가 깨진 것이다
    assert history_count(conn) == 1
    history = latest_history(conn)
    assert history["sync_type"] == "SIGUNGU_CODE"
    assert history["status"] == SyncStatus.COMPLETED.value
    assert history["total_count"] == 49861
    assert history["upsert_count"] == 12
    assert history["finished_at"] is not None
    assert history["error_message"] is None
    assert "법정동코드 동기화 완료" in notifier.messages[0]


# ── 실패 경로 ─────────────────────────────────────────────────────────────────


def test_records_a_failed_row_with_the_error_message(conn, history_repository):
    notifier = SpyNotifier()
    use_case = StubUseCase(Err(domain_error.NetworkError("connect timed out")))
    orchestrator = build(use_case, history_repository, notifier)

    assert orchestrator.sigungu_code_sync() is False

    assert history_count(conn) == 1
    history = latest_history(conn)
    assert history["status"] == SyncStatus.FAILED.value
    assert "connect timed out" in history["error_message"]
    assert history["finished_at"] is not None
    assert "법정동코드 동기화 실패" in notifier.messages[0]


def test_truncating_column_boundary_is_not_hit_by_a_long_error_message(conn, history_repository):
    # error_message 는 VARCHAR(2000) 이다. 원인 체인이 길어도 INSERT 가 깨지면 안 된다
    notifier = SpyNotifier()
    use_case = StubUseCase(Err(domain_error.ParseError("x" * 1900)))
    orchestrator = build(use_case, history_repository, notifier)

    assert orchestrator.sigungu_code_sync() is False
    assert latest_history(conn)["status"] == SyncStatus.FAILED.value


# ── 당일 성공 스킵 ────────────────────────────────────────────────────────────


def test_skips_without_running_when_a_completed_row_already_exists_today(conn, history_repository):
    use_case = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    build(use_case, history_repository, SpyNotifier()).sigungu_code_sync()
    assert use_case.call_count == 1

    second = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    notifier = SpyNotifier()

    assert build(second, history_repository, notifier).sigungu_code_sync(True) is True

    assert second.call_count == 0
    assert history_count(conn) == 1
    assert notifier.messages == []


def test_does_not_skip_when_todays_only_row_failed(conn, history_repository):
    build(
        StubUseCase(Err(domain_error.Unauthorized())), history_repository, SpyNotifier()
    ).sigungu_code_sync()

    use_case = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    assert build(use_case, history_repository, SpyNotifier()).sigungu_code_sync(True) is True

    assert use_case.call_count == 1
    assert history_count(conn) == 2


def test_does_not_skip_when_the_completed_row_is_from_yesterday(conn, history_repository):
    build(
        StubUseCase(Ok(SyncResult(total=1, upserted=1))), history_repository, SpyNotifier()
    ).sigungu_code_sync()
    with conn.cursor() as cur:
        cur.execute("UPDATE sync_histories SET finished_at = %s", (now_kst() - timedelta(days=1),))
    conn.commit()

    use_case = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    assert build(use_case, history_repository, SpyNotifier()).sigungu_code_sync(True) is True

    assert use_case.call_count == 1


def test_does_not_skip_when_another_sync_type_succeeded_today(conn, history_repository):
    build(
        StubUseCase(Ok(SyncResult(total=1, upserted=1))), history_repository, SpyNotifier()
    ).sigungu_code_sync()
    with conn.cursor() as cur:
        cur.execute("UPDATE sync_histories SET sync_type = %s", (SyncType.PLAYGROUND.value,))
    conn.commit()

    use_case = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    assert build(use_case, history_repository, SpyNotifier()).sigungu_code_sync(True) is True

    assert use_case.call_count == 1


# ── 잡별 이력 분리 ────────────────────────────────────────────────────────────


def test_playground_sync_records_its_own_sync_type(conn, history_repository):
    notifier = SpyNotifier()
    playground = StubUseCase(Ok(SyncResult(total=84251, upserted=12)))
    orchestrator = build(
        StubUseCase(Ok(SyncResult(total=0, upserted=0))),
        history_repository,
        notifier,
        playground=playground,
    )

    assert orchestrator.playground_sync() is True

    history = latest_history(conn)
    assert history["sync_type"] == "PLAYGROUND"
    assert history["status"] == SyncStatus.COMPLETED.value
    assert history["total_count"] == 84251
    assert history["upsert_count"] == 12
    assert "놀이시설 동기화 완료" in notifier.messages[0]


def test_playground_skip_is_judged_separately_from_sigungu_code(conn, history_repository):
    # 같은 날 법정동코드가 성공해도 놀이시설은 돌아야 한다 — sync_type 별로 판단한다
    build(
        StubUseCase(Ok(SyncResult(total=1, upserted=1))), history_repository, SpyNotifier()
    ).sigungu_code_sync()

    playground = StubUseCase(Ok(SyncResult(total=1, upserted=1)))
    assert (
        build(
            StubUseCase(Ok(SyncResult(total=0, upserted=0))),
            history_repository,
            SpyNotifier(),
            playground=playground,
        ).playground_sync(True)
        is True
    )

    assert playground.call_count == 1
    assert history_count(conn) == 2
