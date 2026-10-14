"""증분 동기화 이후 AI 요약 생성 — 방금 바뀐 '정상' 어린이집만 대상으로 한다."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime

from kidzly_sync.application.model import BulkAiSummaryResult
from kidzly_sync.application.port import AiSummaryPort
from kidzly_sync.domain.repository import DaycareRepository
from kidzly_sync.domain.result import Err

log = logging.getLogger(__name__)

STATUS_NORMAL = "정상"


class IncrementalDaycaresSummaryUseCase:
    def __init__(self, daycare_repository: DaycareRepository, ai_summary_port: AiSummaryPort) -> None:
        self._daycare_repository = daycare_repository
        self._ai_summary_port = ai_summary_port

    def execute(self, since: datetime) -> BulkAiSummaryResult:
        daycares = self._daycare_repository.find_all_by_status_and_synced_at_after(STATUS_NORMAL, since)
        log.info("증분 AI 요약 생성 시작: 기준시각=%s, 대상 어린이집 수=%d", since, len(daycares))

        success_count = 0
        failed_count = 0

        for daycare in daycares:
            result = self._ai_summary_port.generate_summary(daycare)
            if isinstance(result, Err):
                log.error("AI 요약 생성 실패: daycareCode=%s, error=%s", daycare.daycare_code, result.error)
                failed_count += 1
            else:
                summary = result.value
                try:
                    body = json.dumps(
                        {
                            "summary": summary.summary,
                            "who_may_be_interested": summary.who_may_be_interested,
                            "things_to_consider": summary.things_to_consider,
                        },
                        ensure_ascii=False,
                    )
                    self._daycare_repository.save_ai_analysis(daycare.daycare_code, body)
                    success_count += 1
                except Exception:
                    log.error("AI 분석 결과 저장 실패: daycareCode=%s", daycare.daycare_code, exc_info=True)
                    failed_count += 1

            time.sleep(self._ai_summary_port.request_interval_ms / 1000)

        log.info("증분 AI 요약 생성 완료: 성공=%d, 실패=%d", success_count, failed_count)
        return BulkAiSummaryResult(
            total_count=len(daycares),
            success_count=success_count,
            failed_count=failed_count,
        )
