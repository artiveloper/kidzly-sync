"""외부 시스템 접근 Port. 구현은 Infrastructure 계층에 둔다."""

from __future__ import annotations

from typing import Protocol

from kidzly_sync.application.model import (
    ClosedDaycareInfo,
    DaycareData,
    DaycareSummary,
    LegalDongCodePage,
    NewDaycareInfo,
    PlaygroundPage,
    SigunguInfo,
)
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Result


class LegalDongCodeApiPort(Protocol):
    """법정동코드 조회 (odcloud.kr)."""

    def fetch_legal_dong_codes(self, page: int, per_page: int) -> Result[DomainError, LegalDongCodePage]:
        """한 페이지를 조회한다. ``per_page`` 상한은 2000 이다."""
        ...


class SafemapApiPort(Protocol):
    """어린이놀이시설정보 조회 (safemap.go.kr IF_0007)."""

    def fetch_playgrounds(self, page_no: int, num_of_rows: int) -> Result[DomainError, PlaygroundPage]:
        """한 페이지를 조회한다. HTTP 200 이어도 header.resultCode 가 "00" 이 아니면 실패다."""
        ...


class ChildcareApiPort(Protocol):
    """보육통합정보시스템 (childcare.go.kr)."""

    def fetch_sigungu_list(self, arname: str) -> Result[DomainError, list[SigunguInfo]]:
        """시도명으로 시군구 목록 조회 (cpmsapi020)."""
        ...

    def fetch_daycare_details(self, arcode: str) -> Result[DomainError, list[DaycareData]]:
        """시군구코드로 어린이집 상세 목록 조회 (cpmsapi030)."""
        ...

    def fetch_new_daycares(self, yyyymm: str) -> Result[DomainError, list[NewDaycareInfo]]:
        """월별 신규시설 목록 조회 (cpmsapi018)."""
        ...

    def fetch_closed_daycares(self, yyyymm: str) -> Result[DomainError, list[ClosedDaycareInfo]]:
        """월별 폐지시설 목록 조회 (cpmsapi019)."""
        ...


class AiSummaryPort(Protocol):
    """어린이집 AI 요약 생성 (Groq / Gemini / Ollama — ``ai.provider`` 로 택일)."""

    request_interval_ms: int
    """호출 사이 대기 시간 — provider 별 rate limit 에 맞춘 값."""

    def generate_summary(self, daycare: DaycareData) -> Result[DomainError, DaycareSummary]:
        """운영 데이터를 바탕으로 부모 관점 요약을 생성한다."""
        ...
