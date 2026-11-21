"""``SigunguRepositoryImpl`` (``sigungus``, cpmsapi020 결과) 통합 테스트."""

from __future__ import annotations

import pytest

from kidzly_sync.application.model import SigunguInfo
from kidzly_sync.infrastructure.persistence.sigungu_repository import SigunguRepositoryImpl

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sigungus")
    conn.commit()
    return SigunguRepositoryImpl(conn)


def test_finds_distinct_sido_names_returned_by_the_api(conn, repository):
    repository.upsert_all(
        [
            SigunguInfo(arcode="11110", sidoname="서울특별시", sigunname="종로구"),
            SigunguInfo(arcode="11140", sidoname="서울특별시", sigunname="중구"),
            SigunguInfo(arcode="12110", sidoname="전남광주통합특별시", sigunname="목포시"),
        ]
    )

    assert sorted(repository.find_all_sido_names()) == ["서울특별시", "전남광주통합특별시"]


def test_finds_nothing_in_an_empty_table(conn, repository):
    assert repository.find_all_sido_names() == []
