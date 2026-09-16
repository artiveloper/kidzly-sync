"""법정동코드 값 객체 — 외부 의존이 없는 순수 도메인 규칙."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)

_CODE_PATTERN = re.compile(r"^[0-9]{10}$")


class SigunguCodeLevel(Enum):
    """법정동코드 레벨. 리(里) 레벨은 동기화 대상이 아니므로 상수가 없다."""

    SIDO = "SIDO"
    SIGUNGU = "SIGUNGU"
    EMD = "EMD"


@dataclass(frozen=True, slots=True)
class ParsedLegalDongCode:
    """10자리 법정동코드를 레벨별 절대코드로 분해한 값 객체.

    분해는 **자릿수 고정 위치 문자열 절단**으로만 한다.
    - `법정동명`을 공백 split 하지 않는다 (지명에 공백이 섞인 케이스에서 깨짐)
    - 숫자 나눗셈으로 자르지 않는다 (선행 0 소실 위험)
    """

    code: str
    level: SigunguCodeLevel
    sido_code: str
    sigungu_code: str | None
    emd_code: str | None


def parse_legal_dong_code(raw_code: str) -> ParsedLegalDongCode | None:
    """파싱 실패(10자리 숫자가 아님, 0) 또는 리(里) 레벨이면 ``None`` — 호출자가 제외한다."""
    s = raw_code.strip()
    # ``str.isdigit()`` 는 아라비아-인도 숫자(٠١٢…)도 참이라 정규식이라야 걸러진다
    if not _CODE_PATTERN.match(s):
        log.warning("법정동코드 형식 불량 — 제외 (code=%s)", raw_code)
        return None

    n = int(s)
    if n <= 0:
        log.warning("법정동코드 값 오류 — 제외 (code=%s)", raw_code)
        return None

    # SIDO 조건이 SIGUNGU/EMD 조건을 삼키므로 분기 순서를 바꾸면 안 된다
    if n % 100_000_000 == 0:
        level = SigunguCodeLevel.SIDO
    elif n % 100_000 == 0:
        level = SigunguCodeLevel.SIGUNGU
    elif n % 100 == 0:
        level = SigunguCodeLevel.EMD
    else:
        # 리(里) 레벨 — 동기화 대상이 아닌 정상 제외이므로 로그를 남기지 않는다
        return None

    return ParsedLegalDongCode(
        code=s,
        level=level,
        sido_code=s[:2],
        sigungu_code=s[:5] if level is not SigunguCodeLevel.SIDO else None,
        emd_code=s[:8] if level is SigunguCodeLevel.EMD else None,
    )
