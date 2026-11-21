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

    def find_all_by_status_and_synced_at_after(self, status: str, after: datetime) -> list[DaycareData]:
        """AI 요약 생성 대상 조회 — 상태가 일치하고 ``after`` 이후 동기화된 건."""
        ...

    def save_ai_analysis(self, daycare_code: str, analysis_json: str) -> None:
        """``ai_analysis`` jsonb 컬럼에 저장한다."""
        ...

    def find_all_sido_names(self) -> list[str]:
        """저장된 어린이집의 시도명 (중복 제거). API 응답에서 온 값이라 개편된 시도명이 먼저 나타난다."""
        ...

    def count_active_by_sido_excluding(self, daycare_codes: set[str]) -> dict[str, int]:
        """``daycare_codes`` 에 없는 '정상' 어린이집 수를 시도명별로 센다."""
        ...


class SigunguRepository(Protocol):
    def upsert_all(self, sigungus: list[SigunguInfo]) -> int:
        """변경 감지 가드 없는 UPSERT (arcode PK 기준)."""
        ...

    def find_all_sido_names(self) -> list[str]:
        """지금까지 cpmsapi020 이 돌려준 시도명 (중복 제거)."""
        ...

    def delete_all_except(self, arcodes: set[str]) -> int:
        """``arcodes`` 에 없는 시군구를 지운다. 반환값은 지운 행 수."""
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
