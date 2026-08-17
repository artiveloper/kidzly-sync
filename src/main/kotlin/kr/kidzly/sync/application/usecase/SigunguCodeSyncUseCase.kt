package kr.kidzly.sync.application.usecase

import arrow.core.Either
import kr.kidzly.sync.application.model.SigunguCodeData
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.LegalDongCodeApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.model.ParsedLegalDongCode
import kr.kidzly.sync.domain.repository.SigunguCodeRepository
import kr.kidzly.sync.infrastructure.config.LegalDongCodeApiProperties
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import kotlin.math.ceil

/**
 * 법정동코드 참조 테이블 동기화 (odcloud.kr).
 *
 * 트랜잭션 경계는 [SigunguCodeRepository.upsertAll]의 페이지 단위다.
 * 전체를 단일 트랜잭션으로 묶지 않는다 (PlaygroundFullSyncUseCase와 동일 정책).
 *
 * API가 레벨을 주지 않으므로 전 페이지를 받아 코드로 판별한다.
 * 리(里) 레벨과 폐지된 코드는 저장하지 않는다.
 */
@Service
class SigunguCodeSyncUseCase(
    private val legalDongCodeApiPort: LegalDongCodeApiPort,
    private val sigunguCodeRepository: SigunguCodeRepository,
    private val props: LegalDongCodeApiProperties,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(): Either<DomainError, SyncResult> {
        if (props.serviceKey.isBlank()) {
            log.error("LEGAL_DONG_CODE_SERVICE_KEY가 설정되지 않아 법정동코드 동기화를 수행할 수 없습니다.")
            return Either.Left(DomainError.Unauthorized)
        }

        var pageNo = 1
        var totalPages: Int? = null
        var fetchedCount = 0
        var targetCount = 0
        var upsertCount = 0

        while (true) {
            val page = legalDongCodeApiPort.fetchLegalDongCodes(pageNo, props.perPage).fold(
                ifLeft = { error ->
                    // fail-fast: 페이지를 건너뛰면 약 perPage건이 흔적 없이 누락된다
                    log.error("법정동코드 조회 실패 (page=$pageNo): $error")
                    return Either.Left(error)
                },
                ifRight = { it },
            )

            if (page.items.isEmpty()) {
                log.info("빈 페이지 수신 — 순회 종료 (page=$pageNo)")
                break
            }

            fetchedCount += page.items.size

            val batch = page.items
                .filter { it.abolishedYn?.trim() == ABOLISHED_STATUS_ALIVE }
                .mapNotNull { record ->
                    ParsedLegalDongCode.parse(record.code)?.let { parsed ->
                        SigunguCodeData(
                            code = parsed.code,
                            level = parsed.level,
                            sidoCode = parsed.sidoCode,
                            sigunguCode = parsed.sigunguCode,
                            emdCode = parsed.emdCode,
                            name = record.name.trim(),
                        )
                    }
                }

            targetCount += batch.size
            upsertCount += sigunguCodeRepository.upsertAll(batch)

            // 총 페이지 수는 첫 페이지 응답으로 확정한다
            val pages = totalPages ?: ceil(page.totalCount / props.perPage.toDouble()).toInt().also {
                totalPages = it
                log.info("법정동코드 전체 ${page.totalCount}건 / ${it}페이지 (perPage=${props.perPage})")
            }

            log.debug("법정동코드 ${batch.size}개 upsert (page=$pageNo, 저장대상 누적 ${targetCount}개)")

            if (pageNo >= pages) break
            pageNo++

            // API 과호출 방지
            Thread.sleep(props.requestIntervalMs)
        }

        // 수신은 했는데 전량 탈락했다면 응답 스키마가 바뀐 것이다.
        // 폐지여부 필터가 allowlist("존재"만 통과)라 필드가 사라지면 전 건이 조용히 걸러지고,
        // 성공으로 보고하면 테이블이 낡은 채로 방치되어도 아무도 알아채지 못한다.
        if (fetchedCount > 0 && targetCount == 0) {
            val message = "수신 ${fetchedCount}건 중 저장 대상 0건 — 응답 스키마 변경 의심 (폐지여부/법정동코드 필드 확인 필요)"
            log.error("법정동코드 동기화 실패: $message")
            return Either.Left(DomainError.ParseError(message))
        }

        log.info("법정동코드 동기화 완료 — 수신 ${fetchedCount}건, 저장대상 ${targetCount}건, upserted=${upsertCount}건")
        return Either.Right(SyncResult(total = targetCount, upserted = upsertCount))
    }

    companion object {
        /** 폐지여부 원문값 — 이 값이 아닌 코드(폐지 등)는 저장하지 않는다 */
        private const val ABOLISHED_STATUS_ALIVE = "존재"
    }
}
