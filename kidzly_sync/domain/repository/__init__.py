"""Repository 인터페이스. 구현은 Infrastructure 계층에 둔다."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from kidzly_sync.application.model import SigunguCodeData
from kidzly_sync.domain.entity.sync_history import SyncHistory, SyncType


class SigunguCodeRepository(Protocol):
    def upsert_all(self, codes: list[SigunguCodeData]) -> int:
        """변경 감지 가드 포함 UPSERT (code PK 기준). 반환값은 실제로 INSERT/UPDATE 된 행 수."""
        ...


class SyncHistoryRepository(Protocol):
    def save(self, sync_history: SyncHistory) -> SyncHistory:
        """id 가 0이면 INSERT 후 채워 돌려주고, 아니면 UPDATE 한다."""
        ...

    def exists_completed(
        self,
        sync_type: SyncType,
        target_year_month: str | None,
        start: datetime,
        end: datetime,
    ) -> bool: ...
