"""전체 동기화 Telegram 본문 — 미갱신 경고 기준 단위 테스트."""

from __future__ import annotations

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.orchestrator import STALE_WARNING_THRESHOLD, _full_success_body


def body(*stale: tuple[str, int]) -> str:
    return _full_success_body(SyncResult(total=28935, upserted=120, stale_by_sido=stale), 7, 3)


def test_always_reports_the_stale_count():
    assert "미갱신 정상: 0개" in body()


def test_does_not_warn_below_the_threshold():
    text = body(("경기도", STALE_WARNING_THRESHOLD - 1))

    assert f"미갱신 정상: {STALE_WARNING_THRESHOLD - 1}개" in text
    assert "⚠️" not in text


def test_warns_with_a_per_sido_breakdown_at_the_threshold():
    text = body(("전라남도", 818), ("광주광역시", 728))

    assert STALE_WARNING_THRESHOLD == 100
    assert "⚠️" in text
    assert "1546개" in text
    assert "전라남도: 818개" in text
    assert "광주광역시: 728개" in text
