package kr.kidzly.sync.application.usecase

import arrow.core.Either
import kr.kidzly.sync.application.SyncOrchestrator
import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.DaycareRepository
import kr.kidzly.sync.domain.repository.SigunguRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service

@Service
class FullSyncUseCase(
    private val childcareApiPort: ChildcareApiPort,
    private val daycareRepository: DaycareRepository,
    private val sigunguRepository: SigunguRepository,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(): Either<DomainError, SyncResult> {
        val allDaycares = mutableListOf<DaycareData>()

        for (sidoname in SyncOrchestrator.SIDO_LIST) {
            log.debug("시도 '$sidoname' 시군구 목록 조회 시작")
            val sigunguResult = childcareApiPort.fetchSigunguList(sidoname)
            if (sigunguResult.isLeft()) {
                log.error("시도 '$sidoname' 시군구 목록 조회 실패: ${sigunguResult.leftOrNull()}")
                return Either.Left(sigunguResult.leftOrNull()!!)
            }
            val sigunguList = sigunguResult.getOrNull()!!
            log.info("시도 '$sidoname' 시군구 ${sigunguList.size}개 조회 완료")
            sigunguRepository.upsertAll(sigunguList)

            for (sigungu in sigunguList) {
                log.debug("시군구 '${sigungu.sigunname}(${sigungu.arcode})' 어린이집 조회 시작")
                childcareApiPort.fetchDaycareDetails(sigungu.arcode).fold(
                    ifLeft = { error ->
                        log.warn("시군구 '${sigungu.arcode}(${sigungu.sigunname})' 조회 실패: $error — 건너뜀")
                    },
                    ifRight = { daycares ->
                        allDaycares.addAll(daycares)
                        log.debug("시군구 '${sigungu.sigunname}' 어린이집 ${daycares.size}개 수집 (누적 ${allDaycares.size}개)")
                    },
                )

                // API 과호출 방지
                Thread.sleep(REQUEST_INTERVAL_MS)
            }
        }

        log.info("전체 수집 완료 — 총 ${allDaycares.size}개, upsert 시작")
        val upsertCount = daycareRepository.upsertAll(allDaycares)

        return Either.Right(SyncResult(total = allDaycares.size, upserted = upsertCount))
    }

    companion object {
        private const val REQUEST_INTERVAL_MS = 200L
    }
}
