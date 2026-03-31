package kr.kidzly.sync.application

import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.application.usecase.DeltaSyncUseCase
import kr.kidzly.sync.application.usecase.FullSyncUseCase
import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncStatus
import kr.kidzly.sync.domain.entity.SyncType
import kr.kidzly.sync.domain.repository.DaycareRepository
import kr.kidzly.sync.domain.repository.SigunguRepository
import kr.kidzly.sync.domain.repository.SyncHistoryRepository
import kr.kidzly.sync.infrastructure.notification.TelegramNotifier
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.time.YearMonth
import java.time.format.DateTimeFormatter

@Service
class SyncOrchestrator(
    private val fullSyncUseCase: FullSyncUseCase,
    private val deltaSyncUseCase: DeltaSyncUseCase,
    private val childcareApiPort: ChildcareApiPort,
    private val daycareRepository: DaycareRepository,
    private val sigunguRepository: SigunguRepository,
    private val syncHistoryRepository: SyncHistoryRepository,
    private val telegramNotifier: TelegramNotifier,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun fullSync() {
        val history = syncHistoryRepository.save(
            SyncHistory(
                syncType = SyncType.FULL,
                startedAt = LocalDateTime.now()
            ),
        )

        log.info("전체 동기화 시작 (id=${history.id})")

        fullSyncUseCase.execute().fold(
            ifLeft = { error ->
                val message = error.toString()
                history.status = SyncStatus.FAILED
                history.errorMessage = message
                history.finishedAt = LocalDateTime.now()
                syncHistoryRepository.save(history)

                log.error("전체 동기화 실패: $message")
                telegramNotifier.sendMessage(
                    """
                    ❌ <b>전체 동기화 실패</b>
                    - 시작: ${history.startedAt.format(DATETIME_FORMAT)}
                    - 오류: $message
                    """.trimIndent(),
                )
            },
            ifRight = { result ->
                history.status = SyncStatus.COMPLETED
                history.totalCount = result.total
                history.upsertCount = result.upserted
                history.finishedAt = LocalDateTime.now()
                syncHistoryRepository.save(history)

                val duration = java.time.Duration.between(history.startedAt, history.finishedAt)
                log.info("전체 동기화 완료 — total=${result.total}, upserted=${result.upserted}, 소요=${duration.toMinutes()}분")
                telegramNotifier.sendMessage(
                    """
                    ✅ <b>전체 동기화 완료</b>
                    - 총 처리: ${result.total}개
                    - Upsert: ${result.upserted}개
                    - 소요 시간: ${duration.toMinutes()}분 ${duration.toSecondsPart()}초
                    """.trimIndent(),
                )
            },
        )
    }

    fun deltaSync(targetMonth: YearMonth = YearMonth.now()) {
        val yyyymm = targetMonth.format(DateTimeFormatter.ofPattern("yyyyMM"))
        val history = syncHistoryRepository.save(
            SyncHistory(
                syncType = SyncType.DELTA,
                targetYearMonth = yyyymm,
                startedAt = LocalDateTime.now(),
            ),
        )

        log.info("증분 동기화 시작 (id=${history.id}, 대상월=$yyyymm)")

        deltaSyncUseCase.execute(targetMonth).fold(
            ifLeft = { error ->
                val message = error.toString()
                history.status = SyncStatus.FAILED
                history.errorMessage = message
                history.finishedAt = LocalDateTime.now()
                syncHistoryRepository.save(history)

                log.error("증분 동기화 실패: $message")
                telegramNotifier.sendMessage(
                    """
                    ❌ <b>증분 동기화 실패</b> ($yyyymm)
                    - 시작: ${history.startedAt.format(DATETIME_FORMAT)}
                    - 오류: $message
                    """.trimIndent(),
                )
            },
            ifRight = { result ->
                history.status = SyncStatus.COMPLETED
                history.totalCount = result.total
                history.upsertCount = result.upserted
                history.closedCount = result.closed
                history.finishedAt = LocalDateTime.now()
                syncHistoryRepository.save(history)

                log.info("증분 동기화 완료 — upserted=${result.upserted}, closed=${result.closed}")
                telegramNotifier.sendMessage(
                    """
                    ✅ <b>증분 동기화 완료</b> ($yyyymm)
                    - 신규 upsert: ${result.upserted}개
                    - 폐지 처리: ${result.closed}개
                    """.trimIndent(),
                )
            },
        )
    }

    /** 시군구 목록 동기화 (cpmsapi020) — sidoname 생략 시 전체 17개 시도 순회 */
    fun syncSigungu(sidoname: String? = null): SyncResult {
        val targets = if (sidoname != null) listOf(sidoname) else SIDO_LIST
        var total = 0
        var upserted = 0
        for (sido in targets) {
            log.info("시군구 동기화 시작 (시도=$sido)")
            childcareApiPort.fetchSigunguList(sido).fold(
                ifLeft = { error -> log.error("시군구 동기화 실패 (시도=$sido): $error") },
                ifRight = { sigungus ->
                    upserted += sigunguRepository.upsertAll(sigungus)
                    total += sigungus.size
                    log.info("시군구 동기화 완료 (시도=$sido, ${sigungus.size}개)")
                },
            )
        }
        return SyncResult(total = total, upserted = upserted)
    }

    /** 특정 시군구의 어린이집 상세 동기화 (cpmsapi030) */
    fun syncDaycareDetail(arcode: String): SyncResult {
        log.info("어린이집 상세 동기화 시작 (arcode=$arcode)")
        return childcareApiPort.fetchDaycareDetails(arcode).fold(
            ifLeft = { error ->
                log.error("어린이집 상세 동기화 실패 (arcode=$arcode): $error")
                throw RuntimeException(error.toString())
            },
            ifRight = { daycares ->
                val count = daycareRepository.upsertAll(daycares)
                log.info("어린이집 상세 동기화 완료 (arcode=$arcode, ${count}개)")
                SyncResult(total = daycares.size, upserted = count)
            },
        )
    }

    /** 월별 신규 어린이집 동기화 (cpmsapi018) */
    fun syncNewDaycare(targetMonth: YearMonth): SyncResult {
        val yyyymm = targetMonth.format(DateTimeFormatter.ofPattern("yyyyMM"))
        log.info("신규 어린이집 동기화 시작 (대상월=$yyyymm)")
        return childcareApiPort.fetchNewDaycares(yyyymm).fold(
            ifLeft = { error ->
                log.error("신규 어린이집 동기화 실패 ($yyyymm): $error")
                throw RuntimeException(error.toString())
            },
            ifRight = { newDaycares ->
                val affectedArcodes = newDaycares.map { it.arcode }.toSet()
                val newStcodes = newDaycares.map { it.stcode }.toSet()
                var upsertCount = 0
                for (arcode in affectedArcodes) {
                    childcareApiPort.fetchDaycareDetails(arcode).fold(
                        ifLeft = { error -> log.warn("시군구 '$arcode' 상세 조회 실패: $error — 건너뜀") },
                        ifRight = { daycares ->
                            upsertCount += daycareRepository.upsertAll(daycares.filter { it.stcode in newStcodes })
                        },
                    )
                    Thread.sleep(REQUEST_INTERVAL_MS)
                }
                log.info("신규 어린이집 동기화 완료 ($yyyymm, ${upsertCount}개)")
                SyncResult(total = newDaycares.size, upserted = upsertCount)
            },
        )
    }

    /** 월별 폐지 어린이집 동기화 (cpmsapi019) */
    fun syncClosedDaycare(targetMonth: YearMonth): SyncResult {
        val yyyymm = targetMonth.format(DateTimeFormatter.ofPattern("yyyyMM"))
        log.info("폐지 어린이집 동기화 시작 (대상월=$yyyymm)")
        return childcareApiPort.fetchClosedDaycares(yyyymm).fold(
            ifLeft = { error ->
                log.error("폐지 어린이집 동기화 실패 ($yyyymm): $error")
                throw RuntimeException(error.toString())
            },
            ifRight = { closedDaycares ->
                var closedCount = 0
                for (closed in closedDaycares) {
                    closedCount += daycareRepository.markAsClosed(closed.stcode, closed.crstdate)
                }
                log.info("폐지 어린이집 동기화 완료 ($yyyymm, ${closedCount}개)")
                SyncResult(total = closedDaycares.size, upserted = 0, closed = closedCount)
            },
        )
    }

    companion object {
        private const val REQUEST_INTERVAL_MS = 200L
        private val DATETIME_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

        val SIDO_LIST = listOf(
            "서울특별시", "부산광역시", "대구광역시", "인천광역시",
            "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
            "경기도", "강원특별자치도", "충청북도", "충청남도",
            "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
        )
    }
}
