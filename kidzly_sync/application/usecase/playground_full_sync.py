"""어린이놀이시설정보(safemap.go.kr IF_0007) 전체 동기화.

트랜잭션 경계는 :meth:`PlaygroundRepository.upsert_all` 의 페이지 단위다.
전체를 단일 트랜잭션으로 묶지 않는다.
"""

from __future__ import annotations

import logging
import math
import time

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.port import SafemapApiPort
from kidzly_sync.config import SafemapApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.repository import PlaygroundRepository
from kidzly_sync.domain.result import Err, Ok, Result

log = logging.getLogger(__name__)


class PlaygroundFullSyncUseCase:
    def __init__(
        self,
        safemap_api_port: SafemapApiPort,
        playground_repository: PlaygroundRepository,
        config: SafemapApiConfig,
    ) -> None:
        self._port = safemap_api_port
        self._repository = playground_repository
        self._config = config

    def execute(self) -> Result[DomainError, SyncResult]:
        if not self._config.service_key.strip():
            log.error("SAFEMAP_SERVICE_KEY가 설정되지 않아 놀이시설 동기화를 수행할 수 없습니다.")
            return Err(domain_error.Unauthorized())

        page_size = self._config.page_size
        page_no = 1
        total_pages: int | None = None
        total_count = 0
        upsert_count = 0

        while True:
            result = self._port.fetch_playgrounds(page_no, page_size)
            if isinstance(result, Err):
                # fail-fast: 페이지를 건너뛰면 약 page_size 건이 흔적 없이 누락된다
                log.error("놀이시설 조회 실패 (pageNo=%d): %s", page_no, result.error)
                return result
            page = result.value

            if not page.items:
                log.info("빈 페이지 수신 — 순회 종료 (pageNo=%d)", page_no)
                break

            upsert_count += self._repository.upsert_all(page.items)
            total_count += len(page.items)

            # 총 페이지 수는 첫 페이지 응답으로 확정한다
            if total_pages is None:
                total_pages = math.ceil(page.total_count / page_size)
                log.info(
                    "놀이시설 전체 %d건 / %d페이지 (pageSize=%d)", page.total_count, total_pages, page_size
                )

            log.debug("놀이시설 %d개 upsert (pageNo=%d, 누적 %d개)", len(page.items), page_no, total_count)

            if page_no >= total_pages:
                break
            page_no += 1

            # API 과호출 방지
            time.sleep(self._config.request_interval_ms / 1000)

        log.info("놀이시설 동기화 완료 — 총 %d개, upserted=%d개", total_count, upsert_count)
        return Ok(SyncResult(total=total_count, upserted=upsert_count))
