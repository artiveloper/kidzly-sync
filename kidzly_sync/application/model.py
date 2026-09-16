"""Application 계층 입출력 모델."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

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


@dataclass(frozen=True, slots=True)
class PlaygroundData:
    """어린이놀이시설 1건 (safemap.go.kr IF_0007)."""

    facility_id: str
    """정규화된 objt_id ("1741.0" → "1741")"""
    facility_serial_no: str | None
    sido_code: str | None
    sigungu_code: str | None
    emd_code: str | None
    name: str
    address: str | None
    coord_x: Decimal | None
    """EPSG:3857 Web Mercator X (위경도 아님)"""
    coord_y: Decimal | None
    """EPSG:3857 Web Mercator Y (위경도 아님)"""
    install_date: str | None
    facility_code1: str | None
    facility_code2: str | None
    install_place_code: str | None
    ownership_code: str | None
    indoor_outdoor_code: str | None
    operation_code: str | None
    accident_yn: str | None
    deleted_yn: str | None


@dataclass(frozen=True, slots=True)
class PlaygroundPage:
    """IF_0007 한 페이지 응답."""

    items: list[PlaygroundData]
    page_no: int
    num_of_rows: int
    total_count: int
