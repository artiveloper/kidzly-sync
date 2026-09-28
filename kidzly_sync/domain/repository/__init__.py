"""Repository 인터페이스. 구현은 Infrastructure 계층에 둔다."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from kidzly_sync.application.model import (
    DaycareData,
    PlaygroundData,
    SigunguCodeData,
    SigunguInfo,
)
from kidzly_sync.domain.entity.sync_history import SyncHistory, SyncType


class SigunguCodeRepository(Protocol):
    def upsert_all(self, codes: list[SigunguCodeData]) -> int:
        """변경 감지 가드 포함 UPSERT (code PK 기준). 반환값은 실제로 INSERT/UPDATE 된 행 수."""
        ...


class PlaygroundRepository(Protocol):
    def upsert_all(self, playgrounds: list[PlaygroundData]) -> int:
        """변경 감지 가드 포함 UPSERT (facility_id PK 기준). 반환값은 실제로 INSERT/UPDATE 된 행 수."""
        ...


class DaycareRepository(Protocol):
    def upsert_all(self, daycares: list[DaycareData]) -> int:
        """변경 감지 가드 포함 UPSERT (daycare_code PK 기준)."""
        ...

    def mark_as_closed(self, daycare_code: str, abolished_date: str | None) -> int:
        """상태를 '폐지'로 바꾼다. 반환값은 실제로 바뀐 행 수 (없는 코드면 0)."""
        ...


class SigunguRepository(Protocol):
    def upsert_all(self, sigungus: list[SigunguInfo]) -> int:
        """변경 감지 가드 없는 UPSERT (arcode PK 기준)."""
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
