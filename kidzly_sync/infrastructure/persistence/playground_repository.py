from __future__ import annotations

import psycopg

from kidzly_sync.application.model import PlaygroundData
from kidzly_sync.common.time import now_kst

# latitude/longitude 는 coord_x/coord_y 로부터 DB 가 계산하는 생성 컬럼이라 여기서 쓰지 않는다 (V18).
UPSERT_SQL = """
    INSERT INTO playgrounds (
        facility_id, facility_serial_no, sido_code, sigungu_code, emd_code,
        name, address, coord_x, coord_y, install_date,
        facility_code1, facility_code2, install_place_code, ownership_code,
        indoor_outdoor_code, operation_code, accident_yn, deleted_yn,
        synced_at
    ) VALUES (
        %(facility_id)s, %(facility_serial_no)s, %(sido_code)s, %(sigungu_code)s, %(emd_code)s,
        %(name)s, %(address)s, %(coord_x)s, %(coord_y)s, %(install_date)s,
        %(facility_code1)s, %(facility_code2)s, %(install_place_code)s, %(ownership_code)s,
        %(indoor_outdoor_code)s, %(operation_code)s, %(accident_yn)s, %(deleted_yn)s,
        %(synced_at)s
    )
    ON CONFLICT (facility_id) DO UPDATE SET
        facility_serial_no = EXCLUDED.facility_serial_no,
        sido_code = EXCLUDED.sido_code,
        sigungu_code = EXCLUDED.sigungu_code,
        emd_code = EXCLUDED.emd_code,
        name = EXCLUDED.name,
        address = EXCLUDED.address,
        coord_x = EXCLUDED.coord_x,
        coord_y = EXCLUDED.coord_y,
        install_date = EXCLUDED.install_date,
        facility_code1 = EXCLUDED.facility_code1,
        facility_code2 = EXCLUDED.facility_code2,
        install_place_code = EXCLUDED.install_place_code,
        ownership_code = EXCLUDED.ownership_code,
        indoor_outdoor_code = EXCLUDED.indoor_outdoor_code,
        operation_code = EXCLUDED.operation_code,
        accident_yn = EXCLUDED.accident_yn,
        deleted_yn = EXCLUDED.deleted_yn,
        synced_at = EXCLUDED.synced_at
    WHERE (
        playgrounds.facility_serial_no, playgrounds.sido_code, playgrounds.sigungu_code,
        playgrounds.emd_code, playgrounds.name, playgrounds.address,
        playgrounds.coord_x, playgrounds.coord_y, playgrounds.install_date,
        playgrounds.facility_code1, playgrounds.facility_code2, playgrounds.install_place_code,
        playgrounds.ownership_code, playgrounds.indoor_outdoor_code, playgrounds.operation_code,
        playgrounds.accident_yn, playgrounds.deleted_yn
    ) IS DISTINCT FROM (
        EXCLUDED.facility_serial_no, EXCLUDED.sido_code, EXCLUDED.sigungu_code,
        EXCLUDED.emd_code, EXCLUDED.name, EXCLUDED.address,
        EXCLUDED.coord_x, EXCLUDED.coord_y, EXCLUDED.install_date,
        EXCLUDED.facility_code1, EXCLUDED.facility_code2, EXCLUDED.install_place_code,
        EXCLUDED.ownership_code, EXCLUDED.indoor_outdoor_code, EXCLUDED.operation_code,
        EXCLUDED.accident_yn, EXCLUDED.deleted_yn
    )
"""


class PlaygroundRepositoryImpl:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def upsert_all(self, playgrounds: list[PlaygroundData]) -> int:
        if not playgrounds:
            return 0
        synced_at = now_kst()
        params = [
            {
                "facility_id": p.facility_id,
                "facility_serial_no": p.facility_serial_no,
                "sido_code": p.sido_code,
                "sigungu_code": p.sigungu_code,
                "emd_code": p.emd_code,
                "name": p.name,
                "address": p.address,
                "coord_x": p.coord_x,
                "coord_y": p.coord_y,
                "install_date": p.install_date,
                "facility_code1": p.facility_code1,
                "facility_code2": p.facility_code2,
                "install_place_code": p.install_place_code,
                "ownership_code": p.ownership_code,
                "indoor_outdoor_code": p.indoor_outdoor_code,
                "operation_code": p.operation_code,
                "accident_yn": p.accident_yn,
                "deleted_yn": p.deleted_yn,
                "synced_at": synced_at,
            }
            for p in playgrounds
        ]
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, params)
            return cur.rowcount
