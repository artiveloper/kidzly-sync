package kr.kidzly.sync.presentation

import kr.kidzly.sync.application.SyncOrchestrator
import org.slf4j.LoggerFactory
import org.springframework.boot.ApplicationArguments
import org.springframework.boot.ApplicationRunner
import org.springframework.boot.ExitCodeGenerator
import org.springframework.boot.SpringApplication
import org.springframework.context.ConfigurableApplicationContext
import org.springframework.stereotype.Component
import java.time.YearMonth

/**
 * GitHub Actions one-shot 실행용 러너.
 * 환경변수 SYNC_JOB 이 없으면 아무것도 하지 않음 (일반 서버 기동 시).
 *
 * SYNC_JOB=FULL  → fullSync() 실행 후 종료
 * SYNC_JOB=DELTA → deltaSync() 실행 후 종료 (SYNC_YEAR_MONTH=2026-03 로 월 지정 가능)
 */
@Component
class SyncJobRunner(
    private val syncOrchestrator: SyncOrchestrator,
    private val applicationContext: ConfigurableApplicationContext,
) : ApplicationRunner {
    private val log = LoggerFactory.getLogger(javaClass)

    override fun run(args: ApplicationArguments) {
        val job = System.getenv("SYNC_JOB") ?: return

        val success = try {
            when (job.uppercase()) {
                "FULL" -> {
                    log.info("=== [BATCH] 전체 동기화 실행 ===")
                    syncOrchestrator.fullSync(skipIfAlreadySucceededToday = true)
                }
                "DELTA" -> {
                    val yearMonth = System.getenv("SYNC_YEAR_MONTH")
                        ?.let { YearMonth.parse(it) }
                        ?: YearMonth.now()
                    log.info("=== [BATCH] 증분 동기화 실행 (대상월=$yearMonth) ===")
                    syncOrchestrator.deltaSync(yearMonth, skipIfAlreadySucceededToday = true)
                }
                else -> {
                    log.error("알 수 없는 SYNC_JOB 값: $job (FULL 또는 DELTA 만 허용)")
                    false
                }
            }
        } catch (e: Exception) {
            log.error("[BATCH] 동기화 실패", e)
            false
        }

        SpringApplication.exit(applicationContext, ExitCodeGenerator { if (success) 0 else 1 })
    }
}
