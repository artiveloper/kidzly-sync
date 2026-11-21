"""daycares 에 운영자 메모 컬럼 operator_note 추가

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-22

작성 일시: 2026-11-22
변경 내용: daycares 에 운영자 메모 operator_note(TEXT)를 추가한다.
배경: 어린이집이 공공 API(cpmsapi030)에 없는 정보의 정정을 요청해 온다. 예) 요게벳어린이집
      (47190000057) — 정보공개포털 총현원 35명 = 일반보육 32 + 방과후/시간제 3 인데, API 현원
      crchcnt 는 시간제 인원을 빼고 32 를 준다. 동기화 값을 고치면 다음 배치가 다시 덮어쓰므로,
      API 값은 그대로 두고 화면에 별도로 표기할 메모를 둔다.
판단: 어린이집당 메모 하나면 충분해 별도 테이블 대신 컬럼으로 둔다 (이력·복수 메모가 필요해지면
      daycare_notes 테이블로 옮긴다). DaycareData 에 넣지 않는다 — 넣으면 UPSERT 가 매 동기화마다
      NULL 로 지운다. ai_analysis 와 같은 "배치가 쓰지 않는 컬럼" 이다.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE daycares ADD COLUMN operator_note TEXT")
    op.execute(
        "COMMENT ON COLUMN daycares.operator_note IS "
        "'운영자 메모 — 어린이집 요청 등 공공 API 에 없는 정보를 화면에 따로 표기한다. "
        "동기화가 건드리지 않는다. 없으면 NULL'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE daycares DROP COLUMN operator_note")
