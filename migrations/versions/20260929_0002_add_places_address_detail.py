"""places 에 상세 주소 컬럼 address_detail 추가

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-29

작성 일시: 2026-09-29
변경 내용: places 에 상세 주소 컬럼 address_detail 을 추가한다. 선택 입력이라 nullable 이다.
배경: address 는 카카오 우편번호로 검색·선택한 기본 주소이며 네이버 지오코딩의 입력이 된다.
      건물명·동·층·호수 같은 상세 주소는 좌표 변환 대상이 아니고, 기본 주소에 이어 붙이면
      수정 화면에서 다시 떼어낼 수 없어 재검색 시 지오코딩 입력이 오염된다. 별도 컬럼으로 둔다.
판단: address 가 VARCHAR(300) 이라 상세는 VARCHAR(200) 이면 충분하다. NOT NULL 로 두지 않는다 —
      상세 주소가 없는 장소(공원 등)가 흔하고, 정의서도 필수로 규정하지 않는다.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE places ADD COLUMN address_detail VARCHAR(200)")
    op.execute(
        "COMMENT ON COLUMN places.address_detail IS "
        "'건물명·동·층·호수 등 상세 주소. 좌표 변환에는 쓰지 않는다. 없으면 NULL'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE places DROP COLUMN address_detail")
