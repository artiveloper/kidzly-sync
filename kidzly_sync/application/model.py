"""Application 계층 입출력 모델."""

from __future__ import annotations

from dataclasses import dataclass

from kidzly_sync.domain.legal_dong_code import SigunguCodeLevel


@dataclass(frozen=True, slots=True)
class SyncResult:
    total: int
    upserted: int
    closed: int = 0


@dataclass(frozen=True, slots=True)
class LegalDongCodeRecord:
    """법정동코드 API 원본 1건 (가공 전)."""

    code: str
    """법정동코드 (10자리 문자열, 선행 0 보존)"""
    name: str
    """법정동명 원문"""
    abolished_yn: str | None
    """폐지여부: "존재" / "폐지" """


@dataclass(frozen=True, slots=True)
class LegalDongCodePage:
    """법정동코드 API 한 페이지 응답."""

    items: list[LegalDongCodeRecord]
    page: int
    per_page: int
    total_count: int


@dataclass(frozen=True, slots=True)
class SigunguCodeData:
    """``sigungu_codes`` 쓰기 모델 (UPSERT 입력)."""

    code: str
    level: SigunguCodeLevel
    sido_code: str
    sigungu_code: str | None
    emd_code: str | None
    name: str
