from __future__ import annotations

from datetime import datetime

import psycopg

from kidzly_sync.domain.entity.sync_history import SyncHistory, SyncStatus, SyncType

_INSERT_SQL = """
    INSERT INTO sync_histories (
        sync_type, target_year_month, status, total_count, upsert_count,
        closed_count, error_message, started_at, finished_at
    ) VALUES (
        %(sync_type)s, %(target_year_month)s, %(status)s, %(total_count)s, %(upsert_count)s,
        %(closed_count)s, %(error_message)s, %(started_at)s, %(finished_at)s
    )
    RETURNING id
"""

_UPDATE_SQL = """
    UPDATE sync_histories SET
        sync_type = %(sync_type)s,
        target_year_month = %(target_year_month)s,
        status = %(status)s,
        total_count = %(total_count)s,
        upsert_count = %(upsert_count)s,
        closed_count = %(closed_count)s,
        error_message = %(error_message)s,
        started_at = %(started_at)s,
        finished_at = %(finished_at)s
    WHERE id = %(id)s
"""

_EXISTS_SQL = """
    SELECT EXISTS (
        SELECT 1 FROM sync_histories
        WHERE sync_type = %(sync_type)s
          AND status = %(status)s
          AND finished_at BETWEEN %(start)s AND %(end)s
          AND (%(target_year_month)s::varchar IS NULL OR target_year_month = %(target_year_month)s)
    )
"""


class SyncHistoryRepositoryImpl:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def save(self, sync_history: SyncHistory) -> SyncHistory:
        params = {
            "id": sync_history.id,
            "sync_type": sync_history.sync_type.value,
            "target_year_month": sync_history.target_year_month,
            "status": sync_history.status.value,
            "total_count": sync_history.total_count,
            "upsert_count": sync_history.upsert_count,
            "closed_count": sync_history.closed_count,
            "error_message": sync_history.error_message,
            "started_at": sync_history.started_at,
            "finished_at": sync_history.finished_at,
        }
        with self._conn.transaction(), self._conn.cursor() as cur:
            if sync_history.id:
                cur.execute(_UPDATE_SQL, params)
            else:
                cur.execute(_INSERT_SQL, params)
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("sync_histories INSERT 가 id 를 돌려주지 않았습니다")
                sync_history.id = row[0]
        return sync_history

    def exists_completed(
        self,
        sync_type: SyncType,
        target_year_month: str | None,
        start: datetime,
        end: datetime,
    ) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                _EXISTS_SQL,
                {
                    "sync_type": sync_type.value,
                    "status": SyncStatus.COMPLETED.value,
                    "start": start,
                    "end": end,
                    "target_year_month": target_year_month,
                },
            )
            row = cur.fetchone()
            return bool(row and row[0])
