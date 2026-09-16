"""법정동코드 참조 테이블 동기화 (odcloud.kr).

트랜잭션 경계는 :meth:`SigunguCodeRepository.upsert_all` 의 페이지 단위다.
전체를 단일 트랜잭션으로 묶지 않는다.

API 가 레벨을 주지 않으므로 전 페이지를 받아 코드로 판별한다.
리(里) 레벨과 폐지된 코드는 저장하지 않는다.
"""

from __future__ import annotations

import logging
import math
import time

from kidzly_sync.application.model import LegalDongCodeRecord, SigunguCodeData, SyncResult
from kidzly_sync.application.port import LegalDongCodeApiPort
from kidzly_sync.config import LegalDongCodeApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.legal_dong_code import parse_legal_dong_code
from kidzly_sync.domain.repository import SigunguCodeRepository
from kidzly_sync.domain.result import Err, Ok, Result

log = logging.getLogger(__name__)

ABOLISHED_STATUS_ALIVE = "존재"
"""폐지여부 원문값 — 이 값이 아닌 코드(폐지 등)는 저장하지 않는다"""


class SigunguCodeSyncUseCase:
    def __init__(
        self,
        legal_dong_code_api_port: LegalDongCodeApiPort,
        sigungu_code_repository: SigunguCodeRepository,
        config: LegalDongCodeApiConfig,
    ) -> None:
        self._port = legal_dong_code_api_port
        self._repository = sigungu_code_repository
        self._config = config

    def execute(self) -> Result[DomainError, SyncResult]:
        if not self._config.service_key.strip():
            log.error("LEGAL_DONG_CODE_SERVICE_KEY가 설정되지 않아 법정동코드 동기화를 수행할 수 없습니다.")
            return Err(domain_error.Unauthorized())

        per_page = self._config.per_page
        page_no = 1
        total_pages: int | None = None
        fetched_count = 0
        target_count = 0
        upsert_count = 0

        while True:
            result = self._port.fetch_legal_dong_codes(page_no, per_page)
            if isinstance(result, Err):
                # fail-fast: 페이지를 건너뛰면 약 per_page 건이 흔적 없이 누락된다
                log.error("법정동코드 조회 실패 (page=%d): %s", page_no, result.error)
                return result
            page = result.value

            if not page.items:
                log.info("빈 페이지 수신 — 순회 종료 (page=%d)", page_no)
                break

            fetched_count += len(page.items)

            batch = [
                data
                for record in page.items
                if (record.abolished_yn or "").strip() == ABOLISHED_STATUS_ALIVE
                if (data := _to_sigungu_code_data(record)) is not None
            ]

            target_count += len(batch)
            upsert_count += self._repository.upsert_all(batch)

            # 총 페이지 수는 첫 페이지 응답으로 확정한다
            if total_pages is None:
                total_pages = math.ceil(page.total_count / per_page)
                log.info(
                    "법정동코드 전체 %d건 / %d페이지 (perPage=%d)", page.total_count, total_pages, per_page
                )

            log.debug(
                "법정동코드 %d개 upsert (page=%d, 저장대상 누적 %d개)", len(batch), page_no, target_count
            )

            if page_no >= total_pages:
                break
            page_no += 1

            # API 과호출 방지
            time.sleep(self._config.request_interval_ms / 1000)

        # 수신은 했는데 전량 탈락했다면 응답 스키마가 바뀐 것이다.
        # 폐지여부 필터가 allowlist("존재"만 통과)라 필드가 사라지면 전 건이 조용히 걸러지고,
        # 성공으로 보고하면 테이블이 낡은 채로 방치되어도 아무도 알아채지 못한다.
        if fetched_count > 0 and target_count == 0:
            message = (
                f"수신 {fetched_count}건 중 저장 대상 0건 — "
                "응답 스키마 변경 의심 (폐지여부/법정동코드 필드 확인 필요)"
            )
            log.error("법정동코드 동기화 실패: %s", message)
            return Err(domain_error.ParseError(message))

        log.info(
            "법정동코드 동기화 완료 — 수신 %d건, 저장대상 %d건, upserted=%d건",
            fetched_count,
            target_count,
            upsert_count,
        )
        return Ok(SyncResult(total=target_count, upserted=upsert_count))


def _to_sigungu_code_data(record: LegalDongCodeRecord) -> SigunguCodeData | None:
    parsed = parse_legal_dong_code(record.code)
    if parsed is None:
        return None
    return SigunguCodeData(
        code=parsed.code,
        level=parsed.level,
        sido_code=parsed.sido_code,
        sigungu_code=parsed.sigungu_code,
        emd_code=parsed.emd_code,
        name=record.name.strip(),
    )
