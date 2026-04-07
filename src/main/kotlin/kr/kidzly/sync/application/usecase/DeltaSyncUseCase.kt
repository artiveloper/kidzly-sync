package kr.kidzly.sync.application.usecase

import arrow.core.Either
import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import java.time.YearMonth
import java.time.format.DateTimeFormatter

@Service
class DeltaSyncUseCase(
    private val childcareApiPort: ChildcareApiPort,
    private val daycareRepository: DaycareRepository,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(targetMonth: YearMonth): Either<DomainError, SyncResult> {
        val yyyymm = targetMonth.format(DateTimeFormatter.ofPattern("yyyyMM"))

        // 신규시설 처리 — 영향받은 시군구 전체를 다시 동기화
        log.debug("[$yyyymm] 신규시설 목록 조회 시작")
        val newDaycaresResult = childcareApiPort.fetchNewDaycares(yyyymm)
        if (newDaycaresResult.isLeft()) {
            log.error("[$yyyymm] 신규시설 목록 조회 실패: ${newDaycaresResult.leftOrNull()}")
            return Either.Left(newDaycaresResult.leftOrNull()!!)
        }
        val newDaycares = newDaycaresResult.getOrNull()!!
        log.info("[$yyyymm] 신규시설 ${newDaycares.size}개 확인")

        val affectedArcodes = newDaycares.map { it.sigunguCode }.toSet()
        val newDaycareCodes = newDaycares.map { it.daycareCode }.toSet()
        log.debug("[$yyyymm] 영향받은 시군구: $affectedArcodes")

        val upsertList = mutableListOf<DaycareData>()
        for (arcode in affectedArcodes) {
            log.debug("[$yyyymm] 시군구 '$arcode' 상세 조회 시작")
            childcareApiPort.fetchDaycareDetails(arcode).fold(
                ifLeft = { error ->
                    log.warn("시군구 '$arcode' 상세 조회 실패: $error — 건너뜀")
                },
                ifRight = { daycares ->
                    // 신규 daycare_code 포함된 항목만 upsert (해당 시군구 전체 갱신)
                    val filtered = daycares.filter { it.daycareCode in newDaycareCodes }
                    upsertList.addAll(filtered)
                    log.debug("[$yyyymm] 시군구 '$arcode' 전체 ${daycares.size}개 중 신규 ${filtered.size}개 추출")
                },
            )
            Thread.sleep(REQUEST_INTERVAL_MS)
        }

        val upsertCount = if (upsertList.isNotEmpty()) {
            daycareRepository.upsertAll(upsertList).also {
                log.info("[$yyyymm] 신규시설 upsert ${it}개 완료")
            }
        } else 0

        // 폐지시설 처리
        log.debug("[$yyyymm] 폐지시설 목록 조회 시작")
        val closedDaycaresResult = childcareApiPort.fetchClosedDaycares(yyyymm)
        if (closedDaycaresResult.isLeft()) {
            log.error("[$yyyymm] 폐지시설 목록 조회 실패: ${closedDaycaresResult.leftOrNull()}")
            return Either.Left(closedDaycaresResult.leftOrNull()!!)
        }
        val closedDaycares = closedDaycaresResult.getOrNull()!!
        log.info("[$yyyymm] 폐지시설 ${closedDaycares.size}개 확인")

        var closedCount = 0
        for (closed in closedDaycares) {
            log.debug("[$yyyymm] 폐지 처리: daycareCode=${closed.daycareCode}, abolishedDate=${closed.abolishedDate}")
            closedCount += daycareRepository.markAsClosed(closed.daycareCode, closed.abolishedDate)
        }
        log.info("[$yyyymm] 폐지 처리 ${closedCount}개 완료")

        return Either.Right(
            SyncResult(
                total = newDaycares.size + closedDaycares.size,
                upserted = upsertCount,
                closed = closedCount,
            ),
        )
    }

    companion object {
        private const val REQUEST_INTERVAL_MS = 200L
    }
}
