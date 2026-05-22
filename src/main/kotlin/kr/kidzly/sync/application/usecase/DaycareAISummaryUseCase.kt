package kr.kidzly.sync.application.usecase

import arrow.core.Either
import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.application.model.DaycareSummary
import kr.kidzly.sync.application.port.AiSummaryPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service

@Service
class DaycareAISummaryUseCase(
    private val daycareRepository: DaycareRepository,
    private val aiSummaryPort: AiSummaryPort,
    private val objectMapper: ObjectMapper,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    // @Transactional 없음 — 외부 AI API 호출이 포함되므로 트랜잭션을 열어두지 않음
    fun execute(daycareCode: String): Either<DomainError, DaycareSummary> {
        val daycare = daycareRepository.findByCode(daycareCode)
            ?: return Either.Left(DomainError.NotFound(daycareCode, "Daycare"))

        return aiSummaryPort.generateSummary(daycare).onRight { summary ->
            runCatching {
                val json = objectMapper.writeValueAsString(summary)
                daycareRepository.saveAiAnalysis(daycareCode, json)
            }.onFailure { e ->
                log.error("AI 분석 결과 저장 실패: daycareCode={}", daycareCode, e)
            }
        }
    }
}
