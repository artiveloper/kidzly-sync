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


@dataclass(frozen=True, slots=True)
class SigunguInfo:
    """cpmsapi020 시군구 1건."""

    arcode: str
    sidoname: str
    sigunname: str


@dataclass(frozen=True, slots=True)
class NewDaycareInfo:
    """cpmsapi018 월별 신규 어린이집 1건."""

    daycare_code: str
    sigungu_code: str


@dataclass(frozen=True, slots=True)
class ClosedDaycareInfo:
    """cpmsapi019 월별 폐지 어린이집 1건."""

    daycare_code: str
    abolished_date: str | None


@dataclass(frozen=True, slots=True)
class DaycareSummary:
    """AI 가 생성한 어린이집 요약 — ``daycares.ai_analysis`` 쓰기 모델."""

    summary: str
    who_may_be_interested: list[str]
    things_to_consider: list[str]


@dataclass(frozen=True, slots=True)
class BulkAiSummaryResult:
    total_count: int
    success_count: int
    failed_count: int


@dataclass(frozen=True, slots=True)
class DaycareData:
    """cpmsapi030 어린이집 상세 1건 — ``daycares`` 쓰기 모델.

    필드명이 DB 컬럼명과 1:1로 같다. 컬럼이 73개라
    :mod:`kidzly_sync.infrastructure.persistence.daycare_repository` 가 이 이름으로
    UPSERT SQL 을 만든다 — 이름을 바꾸면 SQL 도 같이 바뀐다.
    """

    daycare_code: str
    sigungu_code: str
    sido_name: str | None
    sigungu_name: str | None
    name: str
    type_name: str | None
    status: str | None
    zip_code: str | None
    address: str | None
    phone: str | None
    fax: str | None
    homepage: str | None
    latitude: str | None
    longitude: str | None
    capacity: int | None
    current_child_count: int | None
    nursery_room_count: int | None
    nursery_room_size: Decimal | None
    playground_count: int | None
    cctv_count: int | None
    childcare_staff_count: int | None
    vehicle_operation: str | None
    representative_name: str | None
    certified_date: str | None
    pause_start_date: str | None
    pause_end_date: str | None
    abolished_date: str | None
    data_standard_date: str | None
    services: str | None
    # 반수 (연령별)
    class_count_age_0: int | None
    class_count_age_1: int | None
    class_count_age_2: int | None
    class_count_age_3: int | None
    class_count_age_4: int | None
    class_count_age_5: int | None
    class_count_infant_mixed: int | None
    class_count_child_mixed: int | None
    class_count_special: int | None
    class_count_total: int | None
    # 아동수 (연령별)
    child_count_age_0: int | None
    child_count_age_1: int | None
    child_count_age_2: int | None
    child_count_age_3: int | None
    child_count_age_4: int | None
    child_count_age_5: int | None
    child_count_infant_mixed: int | None
    child_count_child_mixed: int | None
    child_count_special: int | None
    child_count_total: int | None
    # 교직원 근속년수
    staff_tenure_under_1y: float | None
    staff_tenure_1y_to_2y: float | None
    staff_tenure_2y_to_4y: float | None
    staff_tenure_4y_to_6y: float | None
    staff_tenure_over_6y: float | None
    # 교직원 직종별
    staff_director_count: int | None
    staff_teacher_count: int | None
    staff_special_teacher_count: int | None
    staff_therapist_count: int | None
    staff_nutritionist_count: int | None
    staff_nurse_count: int | None
    staff_nursing_assistant_count: int | None
    staff_cook_count: int | None
    staff_office_count: int | None
    staff_total: int | None
    # 입소대기 아동수
    waiting_child_age_0: int | None
    waiting_child_age_1: int | None
    waiting_child_age_2: int | None
    waiting_child_age_3: int | None
    waiting_child_age_4: int | None
    waiting_child_age_5: int | None
    waiting_child_age_over_6: int | None
    waiting_child_total: int | None
