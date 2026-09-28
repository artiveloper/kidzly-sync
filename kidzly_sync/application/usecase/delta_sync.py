"""어린이집 증분 동기화 (childcare.go.kr) — 당월 신규·폐지분만 처리한다.

매일 전국 수만 건을 전량 조회하면 API 키가 소진되고 원본 서버에도 부담이다.
전체 동기화가 주 1회 베이스라인을 맞추고, 여기서는 그 사이의 신규·폐지만 따라간다.

신규시설은 코드만으로는 상세를 얻을 수 없다 — 상세 API 가 시군구 단위라
영향받은 시군구를 통째로 조회한 뒤 신규 코드에 해당하는 것만 골라낸다.
"""

from __future__ import annotations

import logging
import time

from kidzly_sync.application.model import DaycareData, SyncResult
from kidzly_sync.application.port import ChildcareApiPort
from kidzly_sync.config import ChildcareApiConfig
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.repository import DaycareRepository
from kidzly_sync.domain.result import Err, Ok, Result

log = logging.getLogger(__name__)


class DeltaSyncUseCase:
    def __init__(
        self,
        childcare_api_port: ChildcareApiPort,
        daycare_repository: DaycareRepository,
        config: ChildcareApiConfig,
    ) -> None:
        self._port = childcare_api_port
        self._daycare_repository = daycare_repository
        self._config = config

    def execute(self, yyyymm: str) -> Result[DomainError, SyncResult]:
        # ── 신규시설 ──────────────────────────────────────────────────────────
        log.debug("[%s] 신규시설 목록 조회 시작", yyyymm)
        new_result = self._port.fetch_new_daycares(yyyymm)
        if isinstance(new_result, Err):
            log.error("[%s] 신규시설 목록 조회 실패: %s", yyyymm, new_result.error)
            return new_result

        new_daycares = new_result.value
        log.info("[%s] 신규시설 %d개 확인", yyyymm, len(new_daycares))

        # dict.fromkeys 로 중복만 제거하고 순서는 유지한다 — 호출 순서가 재현 가능해야
        # 실패 지점을 로그로 좇을 수 있다.
        affected_arcodes = list(dict.fromkeys(d.sigungu_code for d in new_daycares))
        new_daycare_codes = {d.daycare_code for d in new_daycares}
        log.debug("[%s] 영향받은 시군구: %s", yyyymm, affected_arcodes)

        upsert_list: list[DaycareData] = []
        for arcode in affected_arcodes:
            log.debug("[%s] 시군구 '%s' 상세 조회 시작", yyyymm, arcode)
            detail_result = self._port.fetch_daycare_details(arcode)
            if isinstance(detail_result, Err):
                log.warning("시군구 '%s' 상세 조회 실패: %s — 건너뜀", arcode, detail_result.error)
            else:
                daycares = detail_result.value
                filtered = [d for d in daycares if d.daycare_code in new_daycare_codes]
                upsert_list.extend(filtered)
                log.debug(
                    "[%s] 시군구 '%s' 전체 %d개 중 신규 %d개 추출",
                    yyyymm,
                    arcode,
                    len(daycares),
                    len(filtered),
                )
            time.sleep(self._config.request_interval_ms / 1000)

        upsert_count = 0
        if upsert_list:
            upsert_count = self._daycare_repository.upsert_all(upsert_list)
            log.info("[%s] 신규시설 upsert %d개 완료", yyyymm, upsert_count)

        # ── 폐지시설 ──────────────────────────────────────────────────────────
        log.debug("[%s] 폐지시설 목록 조회 시작", yyyymm)
        closed_result = self._port.fetch_closed_daycares(yyyymm)
        if isinstance(closed_result, Err):
            log.error("[%s] 폐지시설 목록 조회 실패: %s", yyyymm, closed_result.error)
            return closed_result

        closed_daycares = closed_result.value
        log.info("[%s] 폐지시설 %d개 확인", yyyymm, len(closed_daycares))

        closed_count = 0
        for closed in closed_daycares:
            log.debug(
                "[%s] 폐지 처리: daycareCode=%s, abolishedDate=%s",
                yyyymm,
                closed.daycare_code,
                closed.abolished_date,
            )
            closed_count += self._daycare_repository.mark_as_closed(
                closed.daycare_code, closed.abolished_date
            )
        log.info("[%s] 폐지 처리 %d개 완료", yyyymm, closed_count)

        return Ok(
            SyncResult(
                total=len(new_daycares) + len(closed_daycares),
                upserted=upsert_count,
                closed=closed_count,
            )
        )
