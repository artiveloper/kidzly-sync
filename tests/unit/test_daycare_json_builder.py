"""``daycare_json_builder.build`` 필드 매핑 / 파생값 계산 단위 테스트."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from kidzly_sync.infrastructure.ai import daycare_json_builder
from tests.unit.childcare_fixtures import daycare


def build(code: str = "A", **overrides) -> dict:
    return json.loads(daycare_json_builder.build(daycare(code, **overrides)))


# ── 충원율 ────────────────────────────────────────────────────────────────────


def test_occupancy_rate_is_the_truncated_percentage_of_capacity():
    data = build(capacity=20, current_child_count=15)

    assert data["규모"]["충원율_퍼센트"] == 75


def test_occupancy_rate_truncates_toward_zero_rather_than_rounding():
    data = build(capacity=7, current_child_count=5)  # 71.43% → 71

    assert data["규모"]["충원율_퍼센트"] == 71


def test_occupancy_rate_is_none_when_capacity_is_zero():
    data = build(capacity=0, current_child_count=5)

    assert data["규모"]["충원율_퍼센트"] is None


def test_occupancy_rate_is_none_when_capacity_is_missing():
    data = build(capacity=None, current_child_count=5)

    assert data["규모"]["충원율_퍼센트"] is None


def test_occupancy_rate_treats_a_missing_current_child_count_as_zero():
    data = build(capacity=10, current_child_count=None)

    assert data["규모"]["충원율_퍼센트"] == 0


# ── 운영연수 ──────────────────────────────────────────────────────────────────


def test_operation_years_is_derived_from_the_certified_date_year():
    data = build(certified_date="2015-03-01")

    assert data["기본정보"]["운영연수"] == date.today().year - 2015


def test_operation_years_handles_dates_without_hyphens():
    data = build(certified_date="20150301")

    assert data["기본정보"]["운영연수"] == date.today().year - 2015


def test_operation_years_is_none_when_certified_date_is_missing():
    data = build(certified_date=None)

    assert data["기본정보"]["운영연수"] is None


def test_operation_years_is_none_when_the_date_is_too_short_to_hold_a_year():
    data = build(certified_date="201")

    assert data["기본정보"]["운영연수"] is None


# ── 필드 매핑 ─────────────────────────────────────────────────────────────────


def test_maps_facility_and_staff_fields_into_their_sections():
    data = build(
        name="소망어린이집",
        type_name="민간",
        status="정상",
        nursery_room_count=3,
        nursery_room_size=Decimal("45.5"),
        playground_count=1,
        cctv_count=4,
        vehicle_operation="운영",
        waiting_child_total=2,
        class_count_total=3,
        child_count_total=20,
        staff_tenure_over_6y=1.5,
        staff_total=5,
    )

    assert data["기본정보"]["이름"] == "소망어린이집"
    assert data["기본정보"]["유형"] == "민간"
    assert data["기본정보"]["상태"] == "정상"
    assert data["규모"]["보육실수"] == 3
    assert data["규모"]["보육실면적_제곱미터"] == 45.5
    assert data["시설"]["놀이터수"] == 1
    assert data["시설"]["CCTV수"] == 4
    assert data["시설"]["차량운영"] == "운영"
    assert data["대기아동"]["총대기수"] == 2
    assert data["연령별반수"]["총반수"] == 3
    assert data["연령별아동수"]["합계"] == 20
    assert data["교직원근속분포"]["6년이상"] == 1.5
    assert data["교직원직종현황"]["합계"] == 5


def test_nursery_room_size_is_none_when_missing():
    data = build(nursery_room_size=None)

    assert data["규모"]["보육실면적_제곱미터"] is None


def test_output_keeps_korean_text_readable_rather_than_escaping_it():
    # ensure_ascii=False — \uXXXX 로 깨지지 않고 그대로 담겨야 프롬프트에서 읽힌다
    raw = daycare_json_builder.build(daycare("A", name="소망어린이집"))

    assert "소망어린이집" in raw
