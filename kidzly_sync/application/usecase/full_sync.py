"""어린이집 전체 동기화 (childcare.go.kr).

시도 → 각 시도의 시군구 → 각 시군구의 어린이집 상세 순으로 훑는다.

시도 목록은 코드에 고정하지 않는다. cpmsapi020 은 시도명으로만 조회되고 시도 목록 API 가 없는데,
고정 목록은 행정구역 개편을 따라가지 못한다 — 2026년 광주·전남이 '전남광주통합특별시'로
바뀐 뒤 옛 이름은 0건을 돌려줬고, 약 3,200곳이 반년 동안 갱신되지 않았다. 그래서 시도명은
API 가 이미 돌려준 값(sigungus.sidoname, daycares.sido_name)에서 모은다. 개편된 이름은 증분
동기화(cpmsapi030 응답)로 먼저 들어오므로 다음 전체 동기화가 저절로 따라간다.

실패 처리가 두 층에서 다르다:
- 시군구 목록(cpmsapi020) 실패는 fail-fast — 그 시도 전체가 통째로 빠지므로 덮어둘 수 없다.
  단, 0건은 실패가 아니다 — 개편으로 사라진 옛 시도명이다.
- 어린이집 상세(cpmsapi030) 실패는 경고만 남기고 건너뛴다 — 시군구 하나가 빠져도
  나머지 수백 개는 살릴 수 있고, 주 1회 재실행이 메운다.

끝에 "이번에 API 가 돌려주지 않은 '정상' 어린이집"을 다룬다.
- 폐지 API(cpmsapi019) 최근 ``CLOSED_LOOKBACK_MONTHS`` 개월에 있는 것은 폐지로 바꾼다.
  cpmsapi030 은 폐지 직후 한동안 '정상'으로 돌려주다가 목록에서 빼는데, 그 사이 증분 동기화가
  폐지로 바꿔 둔 행을 전체 동기화가 '정상'으로 덮어쓴다. 그 뒤로는 어느 경로도 다시 폐지로
  돌려놓지 않아, 2026-11 기준 폐원한 180곳이 '정상'으로 남아 있었다. "목록에 없음"과
  "폐지 API 에 있음" 둘 다 맞을 때만 바꾸므로 API 일시 오류로 운영 중인 곳이 폐지되지 않는다.
  폐지 API 에는 그 뒤 재개한 곳도 있어서 상세 조회에 실패한 시군구는 건너뛴다.
- 남은 것은 시도별로 센다 (``SyncResult.stale_by_sido``). 경고 여부는 오케스트레이터가 정한다.
"""

from __future__ import annotations

import logging
import time
from datetime import date

from kidzly_sync.application.model import ClosedDaycareInfo, SyncResult
from kidzly_sync.application.port import ChildcareApiPort
from kidzly_sync.config import ChildcareApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.repository import DaycareRepository, SigunguRepository
from kidzly_sync.domain.result import Err, Ok, Result

log = logging.getLogger(__name__)

#: 폐지 API 를 거슬러 볼 개월 수. 2026-11 정리 때 '정상'으로 남은 폐원 180곳의 폐지 등록 월은
#: 2025-01 한 곳을 빼면 모두 최근 12개월 안이었다. 매주 돌므로 이후 새로 생기는 건 몇 주 안에 잡힌다.
CLOSED_LOOKBACK_MONTHS = 12

# 시작값 — 빈 DB(새 환경·테스트)에서도 전국을 돌 수 있게 한다. 개편된 이름은 DB 에서 더해진다.
SIDO_LIST: tuple[str, ...] = (
    "서울특별시",
    "부산광역시",
    "대구광역시",
    "인천광역시",
    "광주광역시",
    "대전광역시",
    "울산광역시",
    "세종특별자치시",
    "경기도",
    "강원특별자치도",
    "충청북도",
    "충청남도",
    "전북특별자치도",
    "전라남도",
    "경상북도",
    "경상남도",
    "제주특별자치도",
)


class FullSyncUseCase:
    def __init__(
        self,
        childcare_api_port: ChildcareApiPort,
        daycare_repository: DaycareRepository,
        sigungu_repository: SigunguRepository,
        config: ChildcareApiConfig,
        today: date | None = None,
    ) -> None:
        self._port = childcare_api_port
        self._daycare_repository = daycare_repository
        self._sigungu_repository = sigungu_repository
        self._config = config
        self._today = today

    def execute(self) -> Result[DomainError, SyncResult]:
        total_count = 0
        upsert_count = 0
        sigungu_count = 0
        seen_codes: set[str] = set()
        seen_arcodes: set[str] = set()
        failed_arcodes: set[str] = set()

        for sidoname in self._sido_names():
            log.debug("시도 '%s' 시군구 목록 조회 시작", sidoname)
            sigungu_result = self._port.fetch_sigungu_list(sidoname)
            if isinstance(sigungu_result, Err):
                log.error("시도 '%s' 시군구 목록 조회 실패: %s", sidoname, sigungu_result.error)
                return sigungu_result

            sigungu_list = sigungu_result.value
            if not sigungu_list:
                log.info(
                    "시도 '%s' 시군구 0개 — 개편으로 더 이상 쓰이지 않는 시도명으로 보고 건너뜀", sidoname
                )
                continue
            log.info("시도 '%s' 시군구 %d개 조회 완료", sidoname, len(sigungu_list))
            sigungu_count += len(sigungu_list)
            seen_arcodes.update(s.arcode for s in sigungu_list)
            self._sigungu_repository.upsert_all(sigungu_list)

            for sigungu in sigungu_list:
                log.debug("시군구 '%s(%s)' 어린이집 조회 시작", sigungu.sigunname, sigungu.arcode)
                detail_result = self._port.fetch_daycare_details(sigungu.arcode)
                if isinstance(detail_result, Err):
                    failed_arcodes.add(sigungu.arcode)
                    log.warning(
                        "시군구 '%s(%s)' 조회 실패: %s — 건너뜀",
                        sigungu.arcode,
                        sigungu.sigunname,
                        detail_result.error,
                    )
                else:
                    daycares = detail_result.value
                    count = self._daycare_repository.upsert_all(daycares)
                    total_count += len(daycares)
                    upsert_count += count
                    seen_codes.update(d.daycare_code for d in daycares)
                    log.debug(
                        "시군구 '%s' 어린이집 %d개 upsert (누적 %d개)",
                        sigungu.sigunname,
                        len(daycares),
                        total_count,
                    )

                # API 과호출 방지
                time.sleep(self._config.request_interval_ms / 1000)

        if sigungu_count == 0:
            # 모든 시도가 0건이면 개편이 아니라 API 쪽 이상이다 — 성공으로 닫으면 아무도 모른다
            log.error("모든 시도에서 시군구가 0개입니다")
            return Err(domain_error.Unknown("모든 시도에서 시군구가 0개입니다 (cpmsapi020)"))

        # 시군구 목록 조회는 하나라도 실패하면 위에서 끝나므로, 여기까지 오면 seen_arcodes 가
        # API 의 현재 시군구 전체다. 개편으로 사라진 옛 시군구(예: 광주·전남 29xxx/46xxx,
        # 대구 편입 전 군위군 47720)를 지운다 — 웹이 sigungus 로 지역 칩을 만들어, 남겨 두면
        # 눌러도 비어 있는 옛 지역이 계속 보인다.
        removed = self._sigungu_repository.delete_all_except(seen_arcodes)
        if removed:
            log.info("API 가 더 이상 돌려주지 않는 시군구 %d개를 sigungus 에서 지웠습니다", removed)

        closed_count = self._close_missing_daycares(seen_codes, failed_arcodes)

        stale = self._daycare_repository.count_active_by_sido_excluding(seen_codes)
        stale_by_sido = tuple(sorted(stale.items(), key=lambda kv: (-kv[1], kv[0])))

        log.info(
            "전체 동기화 완료 — 총 %d개, upserted=%d개, 폐지 반영=%d개, 미갱신 정상=%d개",
            total_count,
            upsert_count,
            closed_count,
            sum(stale.values()),
        )
        return Ok(
            SyncResult(
                total=total_count,
                upserted=upsert_count,
                closed=closed_count,
                stale_by_sido=stale_by_sido,
            )
        )

    def _close_missing_daycares(self, seen_codes: set[str], failed_arcodes: set[str]) -> int:
        """API 목록에 없고 폐지 API 에도 있는 '정상' 어린이집을 폐지로 바꾼다."""
        missing = self._daycare_repository.find_active_excluding(seen_codes)
        candidates = {code for code, sigungu_code in missing if sigungu_code not in failed_arcodes}
        if not candidates:
            return 0

        closed: dict[str, ClosedDaycareInfo] = {}
        for yyyymm in _recent_months(self._today or date.today(), CLOSED_LOOKBACK_MONTHS):
            result = self._port.fetch_closed_daycares(yyyymm)
            if isinstance(result, Err):
                # 한 달이 빠지면 그달 폐지분만 다음 주로 미뤄진다 — 동기화 전체를 실패로 돌릴 일은 아니다
                log.warning("폐지 목록 %s 조회 실패: %s — 이 달은 건너뜀", yyyymm, result.error)
            else:
                closed.update({c.daycare_code: c for c in result.value})
            time.sleep(self._config.request_interval_ms / 1000)

        count = 0
        for code in sorted(candidates & closed.keys()):
            count += self._daycare_repository.mark_as_closed(code, closed[code].abolished_date)
        if count:
            log.info("API 목록에서 빠지고 폐지 API 에 있는 '정상' 어린이집 %d개를 폐지로 바꿨습니다", count)
        return count

    def _sido_names(self) -> list[str]:
        """시작값 순서를 유지하고, API 가 돌려준 적 있는 새 시도명을 뒤에 붙인다."""
        known = set(self._sigungu_repository.find_all_sido_names()) | set(
            self._daycare_repository.find_all_sido_names()
        )
        return [*SIDO_LIST, *sorted(known - set(SIDO_LIST))]


def _recent_months(today: date, count: int) -> list[str]:
    """이번 달부터 거슬러 ``count`` 개월의 yyyymm."""
    months = []
    year, month = today.year, today.month
    for _ in range(count):
        months.append(f"{year}{month:02d}")
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return months
