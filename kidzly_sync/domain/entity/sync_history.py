from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from kidzly_sync.common.time import now_kst


class SyncType(Enum):
    FULL = "FULL"
    DELTA = "DELTA"
    PLAYGROUND = "PLAYGROUND"
    SIGUNGU_CODE = "SIGUNGU_CODE"


class SyncStatus(Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class SyncHistory:
    """``sync_histories`` 한 행. 실행 중 상태가 바뀌므로 가변 객체다."""

    sync_type: SyncType
    target_year_month: str | None = None
    status: SyncStatus = SyncStatus.RUNNING
    total_count: int = 0
    upsert_count: int = 0
    closed_count: int = 0
    error_message: str | None = None
    started_at: datetime = field(default_factory=now_kst)
    finished_at: datetime | None = None
    id: int = 0
