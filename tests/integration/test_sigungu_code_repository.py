"""``SigunguCodeRepositoryImpl`` UPSERT + 변경 감지 가드 통합 테스트.

``ON CONFLICT (code)`` / ``IS DISTINCT FROM`` / enum→VARCHAR 바인딩 / executemany 의
rowcount 합산은 실제 PostgreSQL 없이는 검증할 수 없어 이 부분만 통합 테스트로 다룬다.
"""

from __future__ import annotations

import dataclasses

import pytest

from kidzly_sync.application.model import SigunguCodeData
from kidzly_sync.domain.legal_dong_code import SigunguCodeLevel
from kidzly_sync.infrastructure.persistence.sigungu_code_repository import SigunguCodeRepositoryImpl

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sigungu_codes")
    conn.commit()
    return SigunguCodeRepositoryImpl(conn)


def column_of(conn, code: str, column: str):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {column} FROM sigungu_codes WHERE code = %s", (code,))
        row = cur.fetchone()
        return row[0] if row else None


def row_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sigungu_codes")
        return cur.fetchone()[0]


def sido(code: str) -> SigunguCodeData:
    return SigunguCodeData(
        code=code,
        level=SigunguCodeLevel.SIDO,
        sido_code=code[:2],
        sigungu_code=None,
        emd_code=None,
        name="서울특별시",
    )


def sigungu(code: str) -> SigunguCodeData:
    return SigunguCodeData(
        code=code,
        level=SigunguCodeLevel.SIGUNGU,
        sido_code=code[:2],
        sigungu_code=code[:5],
        emd_code=None,
        name="서울특별시 종로구",
    )


def emd(code: str) -> SigunguCodeData:
    return SigunguCodeData(
        code=code,
        level=SigunguCodeLevel.EMD,
        sido_code=code[:2],
        sigungu_code=code[:5],
        emd_code=code[:8],
        name="서울특별시 종로구 청운동",
    )


# ── code PK 기준 UPSERT ───────────────────────────────────────────────────────


def test_inserts_a_new_row_keyed_by_the_ten_digit_code(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1

    assert row_count(conn) == 1
    assert column_of(conn, "1111010100", "name") == "서울특별시 종로구 청운동"


def test_updates_in_place_instead_of_inserting_a_duplicate_when_the_same_code_returns(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1

    renamed = dataclasses.replace(emd("1111010100"), name="서울특별시 종로구 청운효자동")
    assert repository.upsert_all([renamed]) == 1

    assert row_count(conn) == 1
    assert column_of(conn, "1111010100", "name") == "서울특별시 종로구 청운효자동"


def test_keeps_different_codes_as_separate_rows(conn, repository):
    assert repository.upsert_all([sido("1100000000"), sigungu("1111000000"), emd("1111010100")]) == 3

    assert row_count(conn) == 3


def test_lets_the_later_row_win_when_the_same_code_appears_twice_in_one_batch(conn, repository):
    # executemany 는 행마다 독립 statement 를 실행하므로 ON CONFLICT 가 정상 동작한다
    changed = repository.upsert_all(
        [emd("1111010100"), dataclasses.replace(emd("1111010100"), name="나중 값이 이긴다")]
    )

    assert changed == 2
    assert row_count(conn) == 1
    assert column_of(conn, "1111010100", "name") == "나중 값이 이긴다"


# ── 변경 감지 가드 ────────────────────────────────────────────────────────────


def test_reports_zero_and_keeps_synced_at_when_the_same_data_is_upserted_again(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1
    first_synced_at = column_of(conn, "1111010100", "synced_at")

    # 법정동코드는 거의 불변이라 주 1회 실행이 대부분 no-op 이어야 한다
    assert repository.upsert_all([emd("1111010100")]) == 0
    assert column_of(conn, "1111010100", "synced_at") == first_synced_at


def test_reports_one_and_refreshes_synced_at_when_the_name_changes(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1
    first_synced_at = column_of(conn, "1111010100", "synced_at")

    assert repository.upsert_all([dataclasses.replace(emd("1111010100"), name="개편된 동명")]) == 1

    assert column_of(conn, "1111010100", "synced_at") != first_synced_at


def test_treats_a_level_change_as_a_change(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1

    promoted = dataclasses.replace(emd("1111010100"), level=SigunguCodeLevel.SIGUNGU, emd_code=None)
    assert repository.upsert_all([promoted]) == 1
    assert column_of(conn, "1111010100", "level") == "SIGUNGU"


def test_treats_null_to_value_transitions_on_emd_code_as_a_change(conn, repository):
    assert repository.upsert_all([sigungu("1111000000")]) == 1

    assert repository.upsert_all([dataclasses.replace(sigungu("1111000000"), emd_code="11110101")]) == 1
    assert repository.upsert_all([sigungu("1111000000")]) == 1


def test_counts_only_the_rows_that_actually_changed_inside_a_batch(conn, repository):
    assert repository.upsert_all([emd("1111010100"), emd("1111010200"), emd("1111010300")]) == 3

    changed = repository.upsert_all(
        [
            emd("1111010100"),
            dataclasses.replace(emd("1111010200"), name="신교동 개편"),
            emd("1111010300"),
        ]
    )

    assert changed == 1


def test_returns_zero_without_touching_the_database_for_an_empty_list(conn, repository):
    assert repository.upsert_all([]) == 0

    assert row_count(conn) == 0


# ── 컬럼 매핑 ─────────────────────────────────────────────────────────────────


def test_binds_the_level_enum_as_its_name_so_postgres_accepts_the_varchar_column(conn, repository):
    repository.upsert_all([sido("1100000000"), sigungu("1111000000"), emd("1111010100")])

    assert column_of(conn, "1100000000", "level") == "SIDO"
    assert column_of(conn, "1111000000", "level") == "SIGUNGU"
    assert column_of(conn, "1111010100", "level") == "EMD"


def test_stores_null_for_sigungu_code_and_emd_code_at_sido_level(conn, repository):
    assert repository.upsert_all([sido("1100000000")]) == 1

    assert column_of(conn, "1100000000", "sido_code") == "11"
    assert column_of(conn, "1100000000", "sigungu_code") is None
    assert column_of(conn, "1100000000", "emd_code") is None


def test_stores_null_for_emd_code_at_sigungu_level(conn, repository):
    assert repository.upsert_all([sigungu("1111000000")]) == 1

    assert column_of(conn, "1111000000", "sigungu_code") == "11110"
    assert column_of(conn, "1111000000", "emd_code") is None


def test_stores_every_derived_code_at_emd_level(conn, repository):
    assert repository.upsert_all([emd("1111010100")]) == 1

    assert column_of(conn, "1111010100", "code") == "1111010100"
    assert column_of(conn, "1111010100", "sido_code") == "11"
    assert column_of(conn, "1111010100", "sigungu_code") == "11110"
    assert column_of(conn, "1111010100", "emd_code") == "11110101"


def test_persists_korean_names_without_corruption(conn, repository):
    repository.upsert_all([dataclasses.replace(emd("5013025000"), name="제주특별자치도 서귀포시 대정읍")])

    assert column_of(conn, "5013025000", "name") == "제주특별자치도 서귀포시 대정읍"


def test_accepts_a_200_character_name_at_the_column_boundary(conn, repository):
    long_name = "가" * 200

    assert repository.upsert_all([dataclasses.replace(emd("1111010100"), name=long_name)]) == 1

    assert column_of(conn, "1111010100", "name") == long_name
