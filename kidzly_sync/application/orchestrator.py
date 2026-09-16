"""동기화 잡의 실행·이력 기록·알림을 묶는 오케스트레이터.

UseCase 가 "무엇을 동기화하는가"를 맡고, 여기서는 "언제 건너뛰고, 무엇을 남기고,
누구에게 알리는가"만 다룬다.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from kidzly_sync.application.usecase.sigungu_code_sync import SigunguCodeSyncUseCase
from kidzly_sync.common.time import now_kst
from kidzly_sync.domain.entity.sync_history import SyncHistory, SyncStatus, SyncType
from kidzly_sync.domain.error import to_detailed_message
from kidzly_sync.domain.repository import SyncHistoryRepository
from kidzly_sync.domain.result import Err
from kidzly_sync.infrastructure.notification.telegram import TelegramNotifier

log = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SyncOrchestrator:
    def __init__(
        self,
        sigungu_code_sync_use_case: SigunguCodeSyncUseCase,
        sync_history_repository: SyncHistoryRepository,
        telegram_notifier: TelegramNotifier,
    ) -> None:
        self._sigungu_code_sync_use_case = sigungu_code_sync_use_case
        self._sync_history_repository = sync_history_repository
        self._telegram_notifier = telegram_notifier

    def sigungu_code_sync(self, skip_if_already_succeeded_today: bool = False) -> bool:
        """법정동코드 동기화 (odcloud.kr)."""
        if skip_if_already_succeeded_today and self._exists_completed_today(SyncType.SIGUNGU_CODE, None):
            log.info("오늘 이미 법정동코드 동기화 성공 이력이 있어 스킵합니다.")
            return True

        history = self._sync_history_repository.save(
            SyncHistory(sync_type=SyncType.SIGUNGU_CODE, started_at=now_kst())
        )
        log.info("법정동코드 동기화 시작 (id=%d)", history.id)

        result = self._sigungu_code_sync_use_case.execute()

        if isinstance(result, Err):
            message = to_detailed_message(result.error)
            history.status = SyncStatus.FAILED
            history.error_message = message
            history.finished_at = now_kst()
            self._sync_history_repository.save(history)

            log.error("법정동코드 동기화 실패: %s", message)
            self._telegram_notifier.send_message(
                "❌ <b>법정동코드 동기화 실패</b>\n"
                f"- 시작: {history.started_at.strftime(DATETIME_FORMAT)}\n"
                f"- 오류: {message}"
            )
            return False

        sync_result = result.value
        history.status = SyncStatus.COMPLETED
        history.total_count = sync_result.total
        history.upsert_count = sync_result.upserted
        history.finished_at = now_kst()
        self._sync_history_repository.save(history)

        duration = history.finished_at - history.started_at
        minutes, seconds = _minutes_and_seconds(duration)
        log.info(
            "법정동코드 동기화 완료 — total=%d, upserted=%d, 소요=%d분",
            sync_result.total,
            sync_result.upserted,
            minutes,
        )
        self._telegram_notifier.send_message(
            "✅ <b>법정동코드 동기화 완료</b>\n"
            f"- 총 처리: {sync_result.total}개\n"
            f"- Upsert: {sync_result.upserted}개\n"
            f"- 소요 시간: {minutes}분 {seconds}초"
        )
        return True

    def _exists_completed_today(self, sync_type: SyncType, target_year_month: str | None) -> bool:
        today_start = now_kst().replace(hour=0, minute=0, second=0, microsecond=0)
        return self._sync_history_repository.exists_completed(
            sync_type, target_year_month, today_start, today_start + timedelta(days=1)
        )


def _minutes_and_seconds(duration: timedelta) -> tuple[int, int]:
    """``Duration.toMinutes()`` / ``toSecondsPart()`` 와 같은 분해."""
    total_seconds = int(duration.total_seconds())
    return total_seconds // 60, total_seconds % 60
