"""``FullSyncUseCase`` 순회 / 두 층의 실패 처리 / 집계 단위 테스트."""

from __future__ import annotations

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.usecase.full_sync import SIDO_LIST, FullSyncUseCase
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from tests.unit.childcare_fixtures import (
    FakeChildcarePort,
    RecordingDaycareRepository,
    RecordingSigunguRepository,
    config,
    daycare,
    sigungu,
)


def use_case(port, daycare_repo, sigungu_repo) -> FullSyncUseCase:
    return FullSyncUseCase(port, daycare_repo, sigungu_repo, config())


def all_sido_empty() -> dict[str, object]:
    """17개 시도 전부 빈 시군구 목록으로 채운다 (특정 시도만 바꿔 쓰기 위한 바탕)."""
    return {sido: Ok([]) for sido in SIDO_LIST}


# ── 순회 ──────────────────────────────────────────────────────────────────────


def test_visits_all_seventeen_sido():
    port = FakeChildcarePort(sigungu_lists=all_sido_empty())

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=0, upserted=0))
    assert port.sigungu_calls == list(SIDO_LIST)
    assert len(SIDO_LIST) == 17


def test_upserts_the_sigungu_list_of_every_sido_before_walking_its_daycares():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={"11110": Ok([daycare("A")]), "11140": Ok([daycare("B")])},
    )
    sigungu_repo = RecordingSigunguRepository()

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    # 시도마다 한 번씩 (빈 목록도 호출된다)
    assert len(sigungu_repo.batches) == 17
    assert [s.arcode for s in sigungu_repo.batches[0]] == ["11110", "11140"]
    assert port.detail_calls == ["11110", "11140"]


def test_aggregates_received_and_changed_rows_across_sigungu():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Ok([daycare("A"), daycare("B")]),
            "11140": Ok([daycare("C")]),
        },
    )
    # 변경 감지 가드로 실제 변경은 1건뿐인 상황
    daycare_repo = RecordingDaycareRepository(upsert_returns=[1, 0])

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=3, upserted=1))


# ── 실패 처리: 시군구 목록은 fail-fast ─────────────────────────────────────────


def test_fails_fast_when_a_sido_sigungu_list_fails():
    failure = domain_error.NetworkError("connect timed out")
    lists = all_sido_empty()
    lists["부산광역시"] = Err(failure)
    port = FakeChildcarePort(sigungu_lists=lists)

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Err(failure)
    # 서울(1번째)까지만 돌고 부산(2번째)에서 멈춘다
    assert port.sigungu_calls == ["서울특별시", "부산광역시"]


def test_does_not_touch_the_daycare_repository_when_the_first_sido_fails():
    lists = all_sido_empty()
    lists["서울특별시"] = Err(domain_error.Unauthorized())
    port = FakeChildcarePort(sigungu_lists=lists)
    daycare_repo = RecordingDaycareRepository()

    use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert daycare_repo.batches == []


# ── 실패 처리: 어린이집 상세는 건너뛴다 ────────────────────────────────────────


def test_skips_a_failing_sigungu_and_keeps_going():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140"), sigungu("11170")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Ok([daycare("A")]),
            # 시군구 하나가 실패해도 나머지는 살린다 — 주 1회 재실행이 메운다
            "11140": Err(domain_error.ApiCallError(500, None, "서버 오류")),
            "11170": Ok([daycare("C")]),
        },
    )

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=2, upserted=2))
    assert port.detail_calls == ["11110", "11140", "11170"]


def test_a_failing_sigungu_contributes_nothing_to_the_totals():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Err(domain_error.ParseError("깨진 XML")),
            "11140": Ok([daycare("A"), daycare("B")]),
        },
    )
    daycare_repo = RecordingDaycareRepository()

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=2, upserted=2))
    # 실패한 시군구는 upsert 자체가 호출되지 않는다
    assert len(daycare_repo.batches) == 1
