"""``DaycareRepositoryImpl`` UPSERT / 변경 감지 가드 / 폐지 처리 통합 테스트.

컬럼이 73개라 SQL 을 생성해서 쓴다 — 생성된 SQL 이 실제 PostgreSQL 에서 도는지,
그리고 71개 가드 컬럼이 빠짐없이 변경을 잡아내는지가 이 파일의 핵심이다.
"""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal

import pytest

from kidzly_sync.application.model import DaycareData
from kidzly_sync.common.time import now_kst
from kidzly_sync.infrastructure.persistence.daycare_repository import (
    GUARDED_COLUMNS,
    DaycareRepositoryImpl,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM daycares")
    conn.commit()
    return DaycareRepositoryImpl(conn)


def column_of(conn, daycare_code: str, column: str):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {column} FROM daycares WHERE daycare_code = %s", (daycare_code,))
        row = cur.fetchone()
        return row[0] if row else None


def row_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM daycares")
        return cur.fetchone()[0]


def sample(code: str = "11110000001", **overrides) -> DaycareData:
    base = {f.name: None for f in dataclasses.fields(DaycareData)}
    base |= {
        "daycare_code": code,
        "sigungu_code": "11110",
        "sido_name": "서울특별시",
        "sigungu_name": "종로구",
        "name": "청운어린이집",
        "type_name": "국공립",
        "status": "정상",
        "address": "서울특별시 종로구 청운동 1",
        "latitude": "37.5869",
        "longitude": "126.9690",
        "capacity": 99,
        "current_child_count": 80,
        "nursery_room_size": Decimal("250.75"),
        "staff_tenure_under_1y": 2.5,
        "staff_total": 15,
        "waiting_child_total": 20,
    }
    base |= overrides
    return DaycareData(**base)


# ── UPSERT ────────────────────────────────────────────────────────────────────


def test_inserts_a_new_row(conn, repository):
    assert repository.upsert_all([sample()]) == 1

    assert row_count(conn) == 1
    assert column_of(conn, "11110000001", "name") == "청운어린이집"
    assert column_of(conn, "11110000001", "capacity") == 99


def test_updates_in_place_instead_of_inserting_a_duplicate(conn, repository):
    assert repository.upsert_all([sample()]) == 1

    assert repository.upsert_all([sample(name="청운어린이집(개칭)")]) == 1

    assert row_count(conn) == 1
    assert column_of(conn, "11110000001", "name") == "청운어린이집(개칭)"


def test_returns_zero_without_touching_the_database_for_an_empty_list(conn, repository):
    assert repository.upsert_all([]) == 0

    assert row_count(conn) == 0


def test_persists_korean_text_and_numeric_types_without_corruption(conn, repository):
    repository.upsert_all([sample()])

    assert column_of(conn, "11110000001", "address") == "서울특별시 종로구 청운동 1"
    assert column_of(conn, "11110000001", "nursery_room_size") == Decimal("250.75")
    assert float(column_of(conn, "11110000001", "staff_tenure_under_1y")) == 2.5


# ── 변경 감지 가드 ────────────────────────────────────────────────────────────


def test_reports_zero_and_keeps_synced_at_when_the_same_data_is_upserted_again(conn, repository):
    assert repository.upsert_all([sample()]) == 1
    first_synced_at = column_of(conn, "11110000001", "synced_at")

    assert repository.upsert_all([sample()]) == 0
    assert column_of(conn, "11110000001", "synced_at") == first_synced_at


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("sigungu_code", "11140"),
        ("name", "다른이름"),
        ("status", "폐지"),
        ("capacity", 100),
        ("nursery_room_size", Decimal("300.00")),
        ("staff_tenure_under_1y", 3.0),
        ("waiting_child_age_over_6", 7),
        ("services", "시간연장"),
    ],
)
def test_detects_a_change_in_any_guarded_column(conn, repository, column, value):
    assert repository.upsert_all([sample()]) == 1

    assert repository.upsert_all([sample(**{column: value})]) == 1
    assert column_of(conn, "11110000001", column) is not None


def test_every_guarded_column_exists_in_the_table(conn):
    """생성한 SQL 의 컬럼명이 실제 스키마와 어긋나면 여기서 걸린다."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema='public' AND table_name='daycares'"
        )
        actual = {r[0] for r in cur.fetchall()}

    assert set(GUARDED_COLUMNS) <= actual
    # ai_analysis 는 배치가 쓰지 않는 컬럼이라 가드에 없어야 한다
    assert "ai_analysis" in actual
    assert "ai_analysis" not in GUARDED_COLUMNS


def test_treats_null_to_value_transitions_as_a_change(conn, repository):
    assert repository.upsert_all([sample(fax=None)]) == 1

    assert repository.upsert_all([sample(fax="02-000-0001")]) == 1
    assert repository.upsert_all([sample(fax=None)]) == 1


def test_treats_empty_string_and_null_as_different(conn, repository):
    # childcare 응답은 빈 엘리먼트를 ''로 준다 — NULL 과 섞이면 매번 UPDATE 로 오탐된다
    assert repository.upsert_all([sample(fax=None)]) == 1

    assert repository.upsert_all([sample(fax="")]) == 1
    assert column_of(conn, "11110000001", "fax") == ""
    assert repository.upsert_all([sample(fax="")]) == 0


def test_counts_only_the_rows_that_actually_changed_inside_a_batch(conn, repository):
    assert repository.upsert_all([sample("A"), sample("B"), sample("C")]) == 3

    changed = repository.upsert_all([sample("A"), sample("B", capacity=120), sample("C")])

    assert changed == 1


def test_does_not_wipe_ai_analysis_on_upsert(conn, repository):
    # ai_analysis 는 배치가 아니라 AI 요약 경로가 쓴다 — UPSERT 가 건드리면 안 된다
    repository.upsert_all([sample()])
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE daycares SET ai_analysis = %s::jsonb WHERE daycare_code = %s",
            ('{"summary": "요약"}', "11110000001"),
        )
    conn.commit()

    repository.upsert_all([sample(capacity=120)])

    assert column_of(conn, "11110000001", "ai_analysis") == {"summary": "요약"}


# ── 폐지 처리 ─────────────────────────────────────────────────────────────────


def test_marks_a_daycare_as_closed_with_its_abolished_date(conn, repository):
    repository.upsert_all([sample()])

    assert repository.mark_as_closed("11110000001", "20260315") == 1

    assert column_of(conn, "11110000001", "status") == "폐지"
    assert column_of(conn, "11110000001", "abolished_date") == "20260315"


def test_accepts_a_null_abolished_date(conn, repository):
    repository.upsert_all([sample()])

    assert repository.mark_as_closed("11110000001", None) == 1

    assert column_of(conn, "11110000001", "status") == "폐지"
    assert column_of(conn, "11110000001", "abolished_date") is None


def test_returns_zero_for_a_daycare_code_that_is_not_in_the_table(conn, repository):
    # 우리 DB 에 없는 시설이 폐지 목록에 올 수 있다 — 집계에 잡히면 안 된다
    assert repository.mark_as_closed("없는코드", "20260315") == 0


def test_refreshes_synced_at_when_closing(conn, repository):
    repository.upsert_all([sample()])
    before = column_of(conn, "11110000001", "synced_at")

    repository.mark_as_closed("11110000001", "20260315")

    assert column_of(conn, "11110000001", "synced_at") != before


# ── AI 요약 대상 조회 / 저장 ──────────────────────────────────────────────────


def test_finds_normal_status_daycares_synced_after_the_checkpoint(conn, repository):
    checkpoint = now_kst()
    repository.upsert_all([sample("A")])  # checkpoint 이후 upsert → synced_at > checkpoint

    found = repository.find_all_by_status_and_synced_at_after("정상", checkpoint)

    assert [d.daycare_code for d in found] == ["A"]


def test_excludes_daycares_synced_before_the_checkpoint(conn, repository):
    repository.upsert_all([sample("A")])
    checkpoint = now_kst() + timedelta(seconds=1)

    found = repository.find_all_by_status_and_synced_at_after("정상", checkpoint)

    assert found == []


def test_excludes_daycares_with_a_different_status(conn, repository):
    checkpoint = now_kst()
    repository.upsert_all([sample("A", status="폐지")])

    found = repository.find_all_by_status_and_synced_at_after("정상", checkpoint)

    assert found == []


def test_reconstructs_every_field_of_the_found_daycare(conn, repository):
    checkpoint = now_kst()
    repository.upsert_all([sample()])

    found = repository.find_all_by_status_and_synced_at_after("정상", checkpoint)

    assert len(found) == 1
    assert found[0].name == "청운어린이집"
    assert found[0].capacity == 99
    assert found[0].nursery_room_size == Decimal("250.75")


def test_saves_the_ai_analysis_as_jsonb(conn, repository):
    repository.upsert_all([sample()])

    repository.save_ai_analysis("11110000001", '{"summary": "요약"}')

    assert column_of(conn, "11110000001", "ai_analysis") == {"summary": "요약"}


def test_save_ai_analysis_is_a_no_op_for_an_unknown_daycare_code(conn, repository):
    # 존재하지 않는 코드라도 예외 없이 조용히 지나가야 한다 (행 수를 보고하지 않는 메서드다)
    repository.save_ai_analysis("없는코드", '{"summary": "요약"}')
