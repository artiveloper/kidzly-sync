"""``IncrementalDaycaresSummaryUseCase`` 성공/실패 집계 및 호출 간 대기 단위 테스트."""

from __future__ import annotations

from datetime import datetime

from kidzly_sync.application.model import DaycareSummary
from kidzly_sync.application.usecase.incremental_daycares_summary import (
    STATUS_NORMAL,
    IncrementalDaycaresSummaryUseCase,
)
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from tests.unit.childcare_fixtures import daycare

SINCE = datetime(2026, 3, 1, 9, 0, 0)


class FakeDaycareRepository:
    def __init__(self, targets: list) -> None:
        self._targets = targets
        self.find_calls: list[tuple[str, datetime]] = []
        self.saved: list[tuple[str, str]] = []

    def find_all_by_status_and_synced_at_after(self, status: str, after: datetime):
        self.find_calls.append((status, after))
        return self._targets

    def save_ai_analysis(self, daycare_code: str, analysis_json: str) -> None:
        self.saved.append((daycare_code, analysis_json))


class FakeAiSummaryPort:
    def __init__(self, results: dict[str, object], request_interval_ms: int = 0) -> None:
        self._results = results
        self.request_interval_ms = request_interval_ms
        self.calls: list[str] = []

    def generate_summary(self, target):
        self.calls.append(target.daycare_code)
        return self._results[target.daycare_code]


def summary(text: str = "요약") -> DaycareSummary:
    return DaycareSummary(summary=text, who_may_be_interested=["A"], things_to_consider=["B"])


def use_case(repo, port) -> IncrementalDaycaresSummaryUseCase:
    return IncrementalDaycaresSummaryUseCase(repo, port)


# ── 대상 조회 ─────────────────────────────────────────────────────────────────


def test_looks_up_normal_status_daycares_synced_after_the_given_checkpoint():
    repo = FakeDaycareRepository([])
    use_case(repo, FakeAiSummaryPort({})).execute(SINCE)

    assert repo.find_calls == [(STATUS_NORMAL, SINCE)]


# ── 성공/실패 집계 ────────────────────────────────────────────────────────────


def test_counts_each_successful_summary_and_persists_it():
    targets = [daycare("A"), daycare("B")]
    repo = FakeDaycareRepository(targets)
    port = FakeAiSummaryPort({"A": Ok(summary("A요약")), "B": Ok(summary("B요약"))})

    result = use_case(repo, port).execute(SINCE)

    assert result.total_count == 2
    assert result.success_count == 2
    assert result.failed_count == 0
    assert [code for code, _ in repo.saved] == ["A", "B"]
    assert '"summary": "A요약"' in repo.saved[0][1]


def test_counts_a_failed_generation_without_touching_the_repository():
    targets = [daycare("A")]
    repo = FakeDaycareRepository(targets)
    port = FakeAiSummaryPort({"A": Err(domain_error.RateLimitExceeded())})

    result = use_case(repo, port).execute(SINCE)

    assert result.success_count == 0
    assert result.failed_count == 1
    assert repo.saved == []


def test_mixed_success_and_failure_are_both_counted():
    targets = [daycare("A"), daycare("B"), daycare("C")]
    repo = FakeDaycareRepository(targets)
    port = FakeAiSummaryPort(
        {
            "A": Ok(summary()),
            "B": Err(domain_error.Unknown("boom")),
            "C": Ok(summary()),
        }
    )

    result = use_case(repo, port).execute(SINCE)

    assert result.total_count == 3
    assert result.success_count == 2
    assert result.failed_count == 1


def test_a_save_failure_counts_as_failed_rather_than_crashing():
    targets = [daycare("A")]
    repo = FakeDaycareRepository(targets)

    def boom(daycare_code, analysis_json):
        raise RuntimeError("DB down")

    repo.save_ai_analysis = boom
    port = FakeAiSummaryPort({"A": Ok(summary())})

    result = use_case(repo, port).execute(SINCE)

    assert result.success_count == 0
    assert result.failed_count == 1


# ── provider 호출 간 대기 ─────────────────────────────────────────────────────


def test_sleeps_the_ports_request_interval_between_each_call(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(
        "kidzly_sync.application.usecase.incremental_daycares_summary.time.sleep",
        lambda s: sleeps.append(s),
    )
    targets = [daycare("A"), daycare("B")]
    repo = FakeDaycareRepository(targets)
    # groq_api_properties 를 더 이상 쓰지 않는다 — port 자신의 request_interval_ms 를 쓴다 (Kotlin 버그 수정)
    port = FakeAiSummaryPort(
        {"A": Ok(summary()), "B": Ok(summary())}, request_interval_ms=20_000
    )

    use_case(repo, port).execute(SINCE)

    assert sleeps == [20.0, 20.0]
