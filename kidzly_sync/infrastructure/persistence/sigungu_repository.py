from __future__ import annotations

import psycopg

from kidzly_sync.application.model import SigunguInfo
from kidzly_sync.common.time import now_kst

# 다른 테이블과 달리 변경 감지 가드가 없다 — 시군구는 220여 건뿐이라
# 매번 전 건 UPDATE 해도 비용이 없다.
UPSERT_SQL = """
    INSERT INTO sigungus (arcode, sidoname, sigunname, synced_at)
    VALUES (%(arcode)s, %(sidoname)s, %(sigunname)s, %(synced_at)s)
    ON CONFLICT (arcode) DO UPDATE SET
        sidoname  = EXCLUDED.sidoname,
        sigunname = EXCLUDED.sigunname,
        synced_at = EXCLUDED.synced_at
"""


class SigunguRepositoryImpl:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def upsert_all(self, sigungus: list[SigunguInfo]) -> int:
        if not sigungus:
            return 0
        synced_at = now_kst()
        params = [
            {
                "arcode": s.arcode,
                "sidoname": s.sidoname,
                "sigunname": s.sigunname,
                "synced_at": synced_at,
            }
            for s in sigungus
        ]
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, params)
            return cur.rowcount
