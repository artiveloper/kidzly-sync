"""``DeltaSyncUseCase`` 신규 추출 / 폐지 처리 / 집계 단위 테스트."""

from __future__ import annotations

from kidzly_sync.application.model import ClosedDaycareInfo, NewDaycareInfo, SyncResult
from kidzly_sync.application.usecase.delta_sync import DeltaSyncUseCase
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from tests.unit.childcare_fixtures import (
    FakeChildcarePort,
    RecordingDaycareRepository,
    config,
    daycare,
)

YYYYMM = "202603"


def use_case(port, repo) -> DeltaSyncUseCase:
    return DeltaSyncUseCase(port, repo, config())


def new(code: str, arcode: str) -> NewDaycareInfo:
    return NewDaycareInfo(daycare_code=code, sigungu_code=arcode)


def closed(code: str, date: str | None = "20260315") -> ClosedDaycareInfo:
    return ClosedDaycareInfo(daycare_code=code, abolished_date=date)


# ── 신규시설 ──────────────────────────────────────────────────────────────────


def test_fetches_each_affected_sigungu_once_even_when_several_new_daycares_share_it():
    port = FakeChildcarePort(
        new_daycares=Ok([new("A", "11110"), new("B", "11110"), new("C", "11140")]),
        details={"11110": Ok([daycare("A"), daycare("B")]), "11140": Ok([daycare("C")])},
        closed_daycares=Ok([]),
    )

    use_case(port, RecordingDaycareRepository()).execute(YYYYMM)

    assert port.detail_calls == ["11110", "11140"]


def test_keeps_only_the_new_codes_out_of_the_whole_sigungu_response():
    # 상세 API 는 시군구 단위라 기존 시설까지 함께 온다 — 신규 코드만 골라내야 한다
    port = FakeChildcarePort(
        new_daycares=Ok([new("NEW1", "11110")]),
        details={"11110": Ok([daycare("OLD1"), daycare("NEW1"), daycare("OLD2")])},
        closed_daycares=Ok([]),
    )
    repo = RecordingDaycareRepository()

    use_case(port, repo).execute(YYYYMM)

    assert [d.daycare_code for d in repo.batches[0]] == ["NEW1"]


def test_upserts_every_affected_sigungu_in_a_single_batch():
    port = FakeChildcarePort(
        new_daycares=Ok([new("A", "11110"), new("C", "11140")]),
        details={"11110": Ok([daycare("A")]), "11140": Ok([daycare("C")])},
        closed_daycares=Ok([]),
    )
    repo = RecordingDaycareRepository()

    use_case(port, repo).execute(YYYYMM)

    assert len(repo.batches) == 1
    assert [d.daycare_code for d in repo.batches[0]] == ["A", "C"]


def test_never_touches_the_repository_when_there_are_no_new_daycares():
    port = FakeChildcarePort(new_daycares=Ok([]), closed_daycares=Ok([]))
    repo = RecordingDaycareRepository()

    result = use_case(port, repo).execute(YYYYMM)

    assert repo.batches == []
    assert port.detail_calls == []
    assert result == Ok(SyncResult(total=0, upserted=0, closed=0))


def test_skips_a_failing_sigungu_without_failing_the_whole_run():
    port = FakeChildcarePort(
        new_daycares=Ok([new("A", "11110"), new("C", "11140")]),
        details={
            "11110": Err(domain_error.ApiCallError(500, None, "서버 오류")),
            "11140": Ok([daycare("C")]),
        },
        closed_daycares=Ok([]),
    )
    repo = RecordingDaycareRepository()

    result = use_case(port, repo).execute(YYYYMM)

    assert [d.daycare_code for d in repo.batches[0]] == ["C"]
    assert result.value.upserted == 1


# ── 폐지시설 ──────────────────────────────────────────────────────────────────


def test_marks_every_closed_daycare_with_its_abolished_date():
    port = FakeChildcarePort(
        new_daycares=Ok([]),
        closed_daycares=Ok([closed("X", "20260301"), closed("Y", None)]),
    )
    repo = RecordingDaycareRepository()

    use_case(port, repo).execute(YYYYMM)

    assert repo.closed_calls == [("X", "20260301"), ("Y", None)]


def test_counts_only_the_rows_the_update_actually_hit():
    # 이미 폐지 처리됐거나 우리 DB 에 없는 코드는 0을 돌려준다
    port = FakeChildcarePort(
        new_daycares=Ok([]),
        closed_daycares=Ok([closed("X"), closed("없는코드"), closed("Z")]),
    )
    repo = RecordingDaycareRepository(closed_returns=[1, 0, 1])

    result = use_case(port, repo).execute(YYYYMM)

    assert result.value.closed == 2


# ── fail-fast ─────────────────────────────────────────────────────────────────


def test_fails_fast_when_the_new_daycare_list_fails():
    failure = domain_error.Unauthorized()
    port = FakeChildcarePort(new_daycares=Err(failure))
    repo = RecordingDaycareRepository()

    result = use_case(port, repo).execute(YYYYMM)

    assert result == Err(failure)
    assert port.closed_calls == []
    assert repo.batches == []


def test_fails_when_the_closed_daycare_list_fails_even_after_a_successful_upsert():
    failure = domain_error.NetworkError("connect timed out")
    port = FakeChildcarePort(
        new_daycares=Ok([new("A", "11110")]),
        details={"11110": Ok([daycare("A")])},
        closed_daycares=Err(failure),
    )
    repo = RecordingDaycareRepository()

    result = use_case(port, repo).execute(YYYYMM)

    assert result == Err(failure)
    # 신규분은 이미 커밋되어 있다 (부분 성공 유지)
    assert len(repo.batches) == 1


# ── 집계 ──────────────────────────────────────────────────────────────────────


def test_total_counts_received_new_and_closed_rows_not_the_upserted_ones():
    port = FakeChildcarePort(
        new_daycares=Ok([new("A", "11110"), new("B", "11110")]),
        details={"11110": Ok([daycare("A")])},  # B 는 상세에 없어 빠진다
        closed_daycares=Ok([closed("X")]),
    )
    repo = RecordingDaycareRepository(upsert_returns=[1], closed_returns=[1])

    result = use_case(port, repo).execute(YYYYMM)

    # 수신 신규 2 + 폐지 1 = 3
    assert result == Ok(SyncResult(total=3, upserted=1, closed=1))


def test_passes_the_target_month_to_both_list_apis():
    port = FakeChildcarePort(new_daycares=Ok([]), closed_daycares=Ok([]))

    use_case(port, RecordingDaycareRepository()).execute("202612")

    assert port.new_calls == ["202612"]
    assert port.closed_calls == ["202612"]
