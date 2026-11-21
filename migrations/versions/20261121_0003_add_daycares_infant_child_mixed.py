"""daycares 에 영유아혼합(만2~3세) 반수·아동수 컬럼 추가

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-21

작성 일시: 2026-11-21
변경 내용: daycares 에 class_count_infant_child_mixed, child_count_infant_child_mixed 를 추가한다.
배경: cpmsapi030 명세서 v1.7(2026-04-16)이 반수·아동수에 영유아혼합(만2~3세) 항목
      class_cnt_m3 / child_cnt_m3 를 추가했다. 기존 혼합반 컬럼은 영아혼합(M2, 만0~2세)과
      유아혼합(M5, 만3~5세)뿐이라 이 값을 담을 곳이 없다.
판단: 이름은 기존 infant_mixed(영아) / child_mixed(유아)에 맞춰 영유아 = infant_child 로 짓는다.
      다른 반수·아동수 컬럼과 같이 nullable integer 다 — 응답에 항목이 없는 경우(NULL)와
      0 을 구분해야 하고, 컬럼 추가만이라 기존 행 재작성 없이 끝난다.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE daycares ADD COLUMN class_count_infant_child_mixed INTEGER")
    op.execute("ALTER TABLE daycares ADD COLUMN child_count_infant_child_mixed INTEGER")
    op.execute("COMMENT ON COLUMN daycares.class_count_infant_child_mixed IS '반수-영유아혼합(만2~3세)'")
    op.execute("COMMENT ON COLUMN daycares.child_count_infant_child_mixed IS '아동수-영유아혼합(만2~3세)'")


def downgrade() -> None:
    op.execute("ALTER TABLE daycares DROP COLUMN child_count_infant_child_mixed")
    op.execute("ALTER TABLE daycares DROP COLUMN class_count_infant_child_mixed")
