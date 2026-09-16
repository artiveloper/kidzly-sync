"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

작성 일시:
변경 내용:
배경:
판단:
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "op.execute(\"\"\"\n    \"\"\")"}


def downgrade() -> None:
    ${downgrades if downgrades else "raise NotImplementedError(\"운영 스키마는 앞으로만 간다 — 되돌릴 일이 생기면 새 리비전을 쓴다\")"}
