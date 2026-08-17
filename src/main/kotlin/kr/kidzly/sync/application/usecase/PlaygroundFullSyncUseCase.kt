package kr.kidzly.sync.application.usecase

import arrow.core.Either
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.SafemapApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.PlaygroundRepository
import kr.kidzly.sync.infrastructure.config.SafemapApiProperties
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import kotlin.math.ceil

/**
 * 어린이놀이시설정보(safemap.go.kr IF_0007) 전체 동기화.
 *
 * 트랜잭션 경계는 [PlaygroundRepository.upsertAll]의 페이지 단위다.
 * 전체를 단일 트랜잭션으로 묶지 않는다 (FullSyncUseCase와 동일 정책).
 */
@Service
class PlaygroundFullSyncUseCase(
    private val safemapApiPort: SafemapApiPort,
    private val playgroundRepository: PlaygroundRepository,
    private val props: SafemapApiProperties,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(): Either<DomainError, SyncResult> {
        if (props.serviceKey.isBlank()) {
            log.error("SAFEMAP_SERVICE_KEY가 설정되지 않아 놀이시설 동기화를 수행할 수 없습니다.")
            return Either.Left(DomainError.Unauthorized)
        }

        var pageNo = 1
        var totalPages: Int? = null
        var totalCount = 0
        var upsertCount = 0

        while (true) {
            val page = safemapApiPort.fetchPlaygrounds(pageNo, props.pageSize).fold(
                ifLeft = { error ->
                    // fail-fast: 페이지를 건너뛰면 약 pageSize건이 흔적 없이 누락된다
                    log.error("놀이시설 조회 실패 (pageNo=$pageNo): $error")
                    return Either.Left(error)
                },
                ifRight = { it },
            )

            if (page.items.isEmpty()) {
                log.info("빈 페이지 수신 — 순회 종료 (pageNo=$pageNo)")
                break
            }

            upsertCount += playgroundRepository.upsertAll(page.items)
            totalCount += page.items.size

            // 총 페이지 수는 첫 페이지 응답으로 확정한다
            val pages = totalPages ?: ceil(page.totalCount / props.pageSize.toDouble()).toInt().also {
                totalPages = it
                log.info("놀이시설 전체 ${page.totalCount}건 / ${it}페이지 (pageSize=${props.pageSize})")
            }

            log.debug("놀이시설 ${page.items.size}개 upsert (pageNo=$pageNo, 누적 ${totalCount}개)")

            if (pageNo >= pages) break
            pageNo++

            // API 과호출 방지
            Thread.sleep(props.requestIntervalMs)
        }

        log.info("놀이시설 동기화 완료 — 총 ${totalCount}개, upserted=${upsertCount}개")
        return Either.Right(SyncResult(total = totalCount, upserted = upsertCount))
    }
}
