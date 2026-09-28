"""CLI 인자 해석 단위 테스트.

잡 본체는 가짜로 갈아끼워 DB·API 없이 인자만 검증한다.
"""

from __future__ import annotations

import pytest

from kidzly_sync import cli


@pytest.fixture
def recorded_jobs(monkeypatch):
    """모든 잡을 "받은 skip 값을 기록하는 가짜"로 바꾼다."""
    seen: dict[str, list[bool]] = {}

    def make(name: str):
        def job(stack, args) -> bool:
            seen.setdefault(name, []).append(not args.force)
            return True

        return job

    monkeypatch.setattr(cli, "_JOBS", {name: make(name) for name in cli._JOBS})
    return seen


@pytest.mark.parametrize("job", ["playground", "sigungu-code", "full", "delta"])
def test_skips_when_already_succeeded_today_by_default(recorded_jobs, job):
    # cron 은 성공할 때까지 하루 여러 번 시도하므로 스킵이 기본이어야 한다
    assert cli.main([job]) == 0

    assert recorded_jobs[job] == [True]


@pytest.mark.parametrize("job", ["playground", "sigungu-code", "full", "delta"])
def test_force_disables_the_skip_guard(recorded_jobs, job):
    assert cli.main([job, "--force"]) == 0

    assert recorded_jobs[job] == [False]


def test_returns_one_when_the_job_reports_failure(monkeypatch):
    monkeypatch.setattr(cli, "_JOBS", {"playground": lambda stack, args: False})

    assert cli.main(["playground"]) == 1


def test_returns_one_when_the_job_raises(monkeypatch):
    def boom(stack, args):
        raise RuntimeError("연결 실패")

    monkeypatch.setattr(cli, "_JOBS", {"playground": boom})

    # 예외가 배치 밖으로 새어 나가지 않고 exit code 로 바뀌어야 한다
    assert cli.main(["playground"]) == 1


def test_rejects_an_unknown_job(recorded_jobs):
    with pytest.raises(SystemExit):
        cli.main(["nope"])


# ── delta 의 대상 연월 ────────────────────────────────────────────────────────


def test_converts_the_year_month_argument_to_the_api_format():
    assert cli._resolve_year_month("2026-03") == "202603"
    assert cli._resolve_year_month("2026-12") == "202612"


def test_falls_back_to_the_current_month_when_year_month_is_omitted():
    from datetime import datetime

    # 기준 시계는 러너 로컬 시각이다 (Kotlin YearMonth.now() 와 같다)
    assert cli._resolve_year_month(None) == datetime.now().strftime("%Y%m")


@pytest.mark.parametrize("raw", ["202603", "2026/03", "2026-13", "3월", ""])
def test_rejects_a_malformed_year_month(raw):
    with pytest.raises(SystemExit):
        cli._resolve_year_month(raw)
