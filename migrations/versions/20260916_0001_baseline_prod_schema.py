"""운영 스키마 베이스라인 (Flyway V1~V20 에 해당)

Revision ID: 0001
Revises:
Create Date: 2026-09-16

작성 일시: 2026-09-16
변경 내용: Flyway 에서 Alembic 으로 갈아타며 첫 리비전을 세운다. 내용은 운영 DB 의
          pg_dump 산출물인 ``schema.sql`` 그대로다.
배경: 코틀린 배치를 파이썬으로 옮기면서 JVM 을 걷어낸다. Flyway CLI 를 남기면 마이그레이션
      한 가지 때문에 CI 가 계속 JRE 를 받아야 한다.
판단: V1~V20 의 20단계를 Alembic 리비전으로 쪼개 옮기지 않는다. 옮겨봐야 실행될 일이
      없는데(운영은 이미 20단계를 다 거쳤다) 옮기다 틀릴 위험만 생긴다. 대신 운영의
      현재 모습을 한 덩어리로 못 박고, 여기서부터 앞으로만 간다.
      - 운영 DB 는 ``alembic stamp 0001`` 로 실행 없이 표시만 한다.
      - 새 DB(테스트 컨테이너, 로컬)는 이 리비전이 실제로 돌아 운영과 같은 스키마가 된다.
      - ``db/migration/V*.sql`` 은 기록으로 남긴다. 더 이상 실행되지 않는다.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA_SQL = Path(__file__).resolve().parents[2] / "schema.sql"


def upgrade() -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")

    # ``\restrict`` / ``\unrestrict`` 는 psql 클라이언트 지시어라 서버가 모른다.
    statements = "\n".join(line for line in sql.splitlines() if not line.startswith("\\"))
    op.execute(statements)

    # 덤프가 search_path 를 비워 두고 끝난다. 이후 리비전이 public 을 못 찾는 일이 없도록 되돌린다.
    op.execute("SET search_path TO public")


def downgrade() -> None:
    raise NotImplementedError("베이스라인은 되돌리지 않는다 — 되돌릴 일이 생기면 새 리비전을 쓴다")
