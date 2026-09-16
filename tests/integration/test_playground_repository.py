"""``PlaygroundRepositoryImpl`` UPSERT + 변경 감지 가드 통합 테스트.

``IS DISTINCT FROM`` 가드와 ``NUMERIC(15,4)`` 반올림의 상호작용은 실제 PostgreSQL
없이는 검증할 수 없어 이 부분만 통합 테스트로 다룬다.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from kidzly_sync.application.model import PlaygroundData
from kidzly_sync.infrastructure.persistence.playground_repository import PlaygroundRepositoryImpl

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM playgrounds")
    conn.commit()
    return PlaygroundRepositoryImpl(conn)


def column_of(conn, facility_id: str, column: str):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {column} FROM playgrounds WHERE facility_id = %s", (facility_id,))
        row = cur.fetchone()
        return row[0] if row else None


def sample(facility_id: str) -> PlaygroundData:
    return PlaygroundData(
        facility_id=facility_id,
        facility_serial_no="1002057",
        sido_code="41",
        sigungu_code="41590",
        emd_code="41590118",
        name="한마음정육식당 화성동탄능동점",
        address="경기 화성시 동탄하나1길 68",
        coord_x=Decimal("14144087.4653"),
        coord_y=Decimal("4469799.53254"),
        install_date="20240521",
        facility_code1="4159011800",
        facility_code2=None,
        install_place_code="A004",
        ownership_code="C001",
        indoor_outdoor_code="O001",
        operation_code="B001",
        accident_yn=None,
        deleted_yn=None,
    )


def test_inserts_a_new_row_and_reports_one_changed_row(conn, repository):
    assert repository.upsert_all([sample("1741")]) == 1

    assert column_of(conn, "1741", "name") == "한마음정육식당 화성동탄능동점"


def test_reports_zero_and_keeps_synced_at_when_the_same_data_is_upserted_again(conn, repository):
    assert repository.upsert_all([sample("1741")]) == 1
    first_synced_at = column_of(conn, "1741", "synced_at")

    # 변경 감지 가드의 핵심 — 내용이 동일하면 디스크 IO 가 발생하지 않아야 한다
    assert repository.upsert_all([sample("1741")]) == 0
    assert column_of(conn, "1741", "synced_at") == first_synced_at


def test_reports_one_and_refreshes_synced_at_when_a_single_field_changes(conn, repository):
    assert repository.upsert_all([sample("1741")]) == 1
    first_synced_at = column_of(conn, "1741", "synced_at")

    assert repository.upsert_all([dataclasses.replace(sample("1741"), operation_code="B003")]) == 1

    assert column_of(conn, "1741", "name") == "한마음정육식당 화성동탄능동점"
    assert column_of(conn, "1741", "synced_at") != first_synced_at


def test_treats_null_to_value_transitions_as_a_change(conn, repository):
    assert repository.upsert_all([dataclasses.replace(sample("1741"), deleted_yn=None)]) == 1

    assert repository.upsert_all([dataclasses.replace(sample("1741"), deleted_yn="Y")]) == 1
    assert repository.upsert_all([dataclasses.replace(sample("1741"), deleted_yn=None)]) == 1


def test_does_not_report_a_change_when_coordinates_differ_only_beyond_column_precision(conn, repository):
    # coord_y=4469799.53254 는 컬럼 정의(NUMERIC(15,4))상 4469799.5325 로 반올림 저장된다.
    # 이미 반올림된 값을 다시 넣어도 UPDATE 로 오탐되면 안 된다 — 스케일을 고정하지 않는 근거다.
    assert repository.upsert_all([sample("1741")]) == 1

    rounded = dataclasses.replace(sample("1741"), coord_y=Decimal("4469799.5325"))
    assert repository.upsert_all([rounded]) == 0


def test_counts_only_the_rows_that_actually_changed_inside_a_batch(conn, repository):
    assert repository.upsert_all([sample("1"), sample("2"), sample("3")]) == 3

    changed = repository.upsert_all(
        [
            sample("1"),
            dataclasses.replace(sample("2"), address="서울 강동구 둔촌동"),
            sample("3"),
        ]
    )

    assert changed == 1


def test_returns_zero_without_touching_the_database_for_an_empty_list(conn, repository):
    assert repository.upsert_all([]) == 0


def test_handles_a_duplicated_facility_id_inside_the_same_batch(conn, repository):
    # executemany 는 행마다 독립 statement 를 실행하므로 ON CONFLICT 가 정상 동작한다
    changed = repository.upsert_all(
        [sample("1741"), dataclasses.replace(sample("1741"), name="나중 값이 이긴다")]
    )

    assert changed == 2
    assert column_of(conn, "1741", "name") == "나중 값이 이긴다"


def test_persists_korean_text_without_corruption(conn, repository):
    repository.upsert_all([sample("1741")])

    assert column_of(conn, "1741", "address") == "경기 화성시 동탄하나1길 68"


def test_lets_the_database_derive_latitude_and_longitude_from_the_web_mercator_coords(conn, repository):
    # V18 생성 컬럼. 배치가 계산해 넣지 않으므로 UPSERT 에 없어야 하고, DB 가 채워야 한다.
    repository.upsert_all([sample("1741")])

    latitude = column_of(conn, "1741", "latitude")
    longitude = column_of(conn, "1741", "longitude")
    assert latitude is not None and longitude is not None
    # 경기 화성 — 한국 영역 안이어야 한다
    assert 33 < float(latitude) < 39
    assert 124 < float(longitude) < 132


def test_keeps_latitude_and_longitude_null_when_coords_are_missing(conn, repository):
    # V19 — 좌표 미입력이 (0,0) 기니만 앞바다로 변환되던 것을 NULL 로 고쳤다
    repository.upsert_all([dataclasses.replace(sample("1741"), coord_x=None, coord_y=None)])

    assert column_of(conn, "1741", "latitude") is None
    assert column_of(conn, "1741", "longitude") is None
