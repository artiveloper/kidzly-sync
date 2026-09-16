from __future__ import annotations

import psycopg

from kidzly_sync.application.model import SigunguCodeData
from kidzly_sync.common.time import now_kst

UPSERT_SQL = """
    INSERT INTO sigungu_codes (
        code, level, sido_code, sigungu_code, emd_code, name, synced_at
    ) VALUES (
        %(code)s, %(level)s, %(sido_code)s, %(sigungu_code)s, %(emd_code)s, %(name)s, %(synced_at)s
    )
    ON CONFLICT (code) DO UPDATE SET
        level = EXCLUDED.level,
        sido_code = EXCLUDED.sido_code,
        sigungu_code = EXCLUDED.sigungu_code,
        emd_code = EXCLUDED.emd_code,
        name = EXCLUDED.name,
        synced_at = EXCLUDED.synced_at
    WHERE (
        sigungu_codes.level, sigungu_codes.sido_code, sigungu_codes.sigungu_code,
        sigungu_codes.emd_code, sigungu_codes.name
    ) IS DISTINCT FROM (
        EXCLUDED.level, EXCLUDED.sido_code, EXCLUDED.sigungu_code,
        EXCLUDED.emd_code, EXCLUDED.name
    )
"""


class SigunguCodeRepositoryImpl:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def upsert_all(self, codes: list[SigunguCodeData]) -> int:
        if not codes:
            return 0
        synced_at = now_kst()
        params = [
            {
                "code": c.code,
                # 컬럼이 VARCHAR 이므로 enum 이 아니라 이름(문자열)으로 바인딩한다
                "level": c.level.value,
                "sido_code": c.sido_code,
                "sigungu_code": c.sigungu_code,
                "emd_code": c.emd_code,
                "name": c.name,
                "synced_at": synced_at,
            }
            for c in codes
        ]
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, params)
            return cur.rowcount
