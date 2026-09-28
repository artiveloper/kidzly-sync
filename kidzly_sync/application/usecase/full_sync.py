"""어린이집 전체 동기화 (childcare.go.kr).

17개 시도 → 각 시도의 시군구 → 각 시군구의 어린이집 상세 순으로 훑는다.

실패 처리가 두 층에서 다르다:
- 시군구 목록(cpmsapi020) 실패는 fail-fast — 그 시도 전체가 통째로 빠지므로 덮어둘 수 없다.
- 어린이집 상세(cpmsapi030) 실패는 경고만 남기고 건너뛴다 — 시군구 하나가 빠져도
  나머지 수백 개는 살릴 수 있고, 주 1회 재실행이 메운다.
"""

from __future__ import annotations

import logging
import time

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.port import ChildcareApiPort
from kidzly_sync.config import ChildcareApiConfig
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.repository import DaycareRepository, SigunguRepository
from kidzly_sync.domain.result import Err, Ok, Result

log = logging.getLogger(__name__)

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
    ) -> None:
        self._port = childcare_api_port
        self._daycare_repository = daycare_repository
        self._sigungu_repository = sigungu_repository
        self._config = config

    def execute(self) -> Result[DomainError, SyncResult]:
        total_count = 0
        upsert_count = 0

        for sidoname in SIDO_LIST:
            log.debug("시도 '%s' 시군구 목록 조회 시작", sidoname)
            sigungu_result = self._port.fetch_sigungu_list(sidoname)
            if isinstance(sigungu_result, Err):
                log.error("시도 '%s' 시군구 목록 조회 실패: %s", sidoname, sigungu_result.error)
                return sigungu_result

            sigungu_list = sigungu_result.value
            log.info("시도 '%s' 시군구 %d개 조회 완료", sidoname, len(sigungu_list))
            self._sigungu_repository.upsert_all(sigungu_list)

            for sigungu in sigungu_list:
                log.debug("시군구 '%s(%s)' 어린이집 조회 시작", sigungu.sigunname, sigungu.arcode)
                detail_result = self._port.fetch_daycare_details(sigungu.arcode)
                if isinstance(detail_result, Err):
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
                    log.debug(
                        "시군구 '%s' 어린이집 %d개 upsert (누적 %d개)",
                        sigungu.sigunname,
                        len(daycares),
                        total_count,
                    )

                # API 과호출 방지
                time.sleep(self._config.request_interval_ms / 1000)

        log.info("전체 동기화 완료 — 총 %d개, upserted=%d개", total_count, upsert_count)
        return Ok(SyncResult(total=total_count, upserted=upsert_count))
