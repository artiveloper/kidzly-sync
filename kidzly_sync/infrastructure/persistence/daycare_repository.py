"""``daycares`` UPSERT.

컬럼이 73개라 SQL 을 손으로 쓰지 않고 :class:`DaycareData` 의 필드 목록에서 만든다.
손으로 쓰면 INSERT 컬럼 / VALUES / DO UPDATE SET / IS DISTINCT FROM 네 곳에 같은
이름을 반복해야 하는데, 한 곳만 어긋나도 변경 감지가 조용히 망가진다 — 컴파일도
테스트도 통과하면서 매 동기화가 전 건 UPDATE 로 잡히거나, 반대로 바뀐 값을 놓친다.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

import psycopg

from kidzly_sync.application.model import DaycareData
from kidzly_sync.common.time import now_kst

#: DB 컬럼명과 1:1로 같다 (DaycareData 의 docstring 참고)
ALL_COLUMNS: tuple[str, ...] = tuple(f.name for f in dataclasses.fields(DaycareData))

PK_COLUMN = "daycare_code"

#: 변경 감지 대상 — PK 를 뺀 전부. synced_at 은 "언제 확인했나"라서 비교에 넣지 않는다
#: (넣으면 매번 달라져 항상 UPDATE 가 된다).
GUARDED_COLUMNS: tuple[str, ...] = tuple(c for c in ALL_COLUMNS if c != PK_COLUMN)


def _build_upsert_sql() -> str:
    insert_columns = ", ".join((*ALL_COLUMNS, "synced_at"))
    placeholders = ", ".join(f"%({c})s" for c in (*ALL_COLUMNS, "synced_at"))
    assignments = ",\n        ".join(f"{c} = EXCLUDED.{c}" for c in (*GUARDED_COLUMNS, "synced_at"))
    current = ", ".join(f"daycares.{c}" for c in GUARDED_COLUMNS)
    incoming = ", ".join(f"EXCLUDED.{c}" for c in GUARDED_COLUMNS)
    return f"""
    INSERT INTO daycares ({insert_columns})
    VALUES ({placeholders})
    ON CONFLICT ({PK_COLUMN}) DO UPDATE SET
        {assignments}
    WHERE ({current}) IS DISTINCT FROM ({incoming})
    """


UPSERT_SQL = _build_upsert_sql()

# JPQL 의 CURRENT_TIMESTAMP 를 그대로 옮긴다. 다른 경로가 now_kst() 를 쓰는 것과
# 다르지만, 폐지 처리는 변경 감지 대상이 아니라 synced_at 값이 집계에 영향을 주지 않는다.
MARK_AS_CLOSED_SQL = """
    UPDATE daycares
    SET status = '폐지', abolished_date = %(abolished_date)s, synced_at = CURRENT_TIMESTAMP
    WHERE daycare_code = %(daycare_code)s
"""

FIND_BY_STATUS_AND_SYNCED_AT_AFTER_SQL = f"""
    SELECT {", ".join(ALL_COLUMNS)} FROM daycares
    WHERE status = %(status)s AND synced_at > %(after)s
"""

SAVE_AI_ANALYSIS_SQL = """
    UPDATE daycares SET ai_analysis = CAST(%(analysis_json)s AS jsonb) WHERE daycare_code = %(daycare_code)s
"""


class DaycareRepositoryImpl:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def upsert_all(self, daycares: list[DaycareData]) -> int:
        if not daycares:
            return 0
        synced_at = now_kst()
        params = [{**dataclasses.asdict(d), "synced_at": synced_at} for d in daycares]
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, params)
            return cur.rowcount

    def mark_as_closed(self, daycare_code: str, abolished_date: str | None) -> int:
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(
                MARK_AS_CLOSED_SQL,
                {"daycare_code": daycare_code, "abolished_date": abolished_date},
            )
            return cur.rowcount

    def find_all_by_status_and_synced_at_after(self, status: str, after: datetime) -> list[DaycareData]:
        with self._conn.cursor() as cur:
            cur.execute(FIND_BY_STATUS_AND_SYNCED_AT_AFTER_SQL, {"status": status, "after": after})
            return [DaycareData(**dict(zip(ALL_COLUMNS, row, strict=True))) for row in cur.fetchall()]

    def save_ai_analysis(self, daycare_code: str, analysis_json: str) -> None:
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(SAVE_AI_ANALYSIS_SQL, {"daycare_code": daycare_code, "analysis_json": analysis_json})
