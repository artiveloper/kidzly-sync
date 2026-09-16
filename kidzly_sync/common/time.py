from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

_KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """KST 벽시계 시각 (naive).

    DB 의 ``TIMESTAMP WITHOUT TIME ZONE`` 컬럼과 Kotlin ``LocalDateTime.now(KST)`` 에
    맞추기 위해 tzinfo 를 떼고 돌려준다. aware 로 바꾸면 기존 저장 값과 어긋난다.
    """
    return datetime.now(_KST).replace(tzinfo=None)
