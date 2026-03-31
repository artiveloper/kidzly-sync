package kr.kidzly.sync.presentation

import kr.kidzly.sync.application.SyncOrchestrator
import org.slf4j.LoggerFactory
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import java.time.YearMonth

@Component
class SyncScheduler(
    private val syncOrchestrator: SyncOrchestrator,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    /** 매주 일요일 03:00 — 전체 동기화 */
    @Scheduled(cron = "0 0 3 * * SUN")
    fun fullSync() {
        log.info("=== 전체 동기화 스케줄 실행 ===")
        syncOrchestrator.fullSync()
    }

    /** 매일 02:00 — 당월 증분 동기화 */
    @Scheduled(cron = "0 0 2 * * *")
    fun deltaSync() {
        val currentMonth = YearMonth.now()
        log.info("=== 증분 동기화 스케줄 실행 (대상월=$currentMonth) ===")
        syncOrchestrator.deltaSync(currentMonth)
    }
}
