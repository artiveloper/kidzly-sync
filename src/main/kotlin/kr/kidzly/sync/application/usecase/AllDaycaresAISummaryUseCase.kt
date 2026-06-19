package kr.kidzly.sync.application.usecase

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.application.model.BulkAiSummaryResult
import kr.kidzly.sync.application.port.AiSummaryPort
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service

@Service
class AllDaycaresAISummaryUseCase(
    private val daycareRepository: DaycareRepository,
    private val aiSummaryPort: AiSummaryPort,
    private val objectMapper: ObjectMapper,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(): BulkAiSummaryResult {
        val daycares = daycareRepository.findAllByStatusAndAiAnalysisIsNull("정상")
        log.info("전체 AI 요약 생성 시작: 대상 어린이집 수={}", daycares.size)

        var successCount = 0
        var failedCount = 0

        daycares.forEach { daycare ->
            aiSummaryPort.generateSummary(daycare).fold(
                ifLeft = { error ->
                    log.error("AI 요약 생성 실패: daycareCode={}, error={}", daycare.daycareCode, error)
                    failedCount++
                },
                ifRight = { summary ->
                    runCatching {
                        val json = objectMapper.writeValueAsString(summary)
                        daycareRepository.saveAiAnalysis(daycare.daycareCode, json)
                        successCount++
                    }.onFailure { e ->
                        log.error("AI 분석 결과 저장 실패: daycareCode={}", daycare.daycareCode, e)
                        failedCount++
                    }
                },
            )
            Thread.sleep(aiSummaryPort.requestIntervalMs)
        }

        log.info("전체 AI 요약 생성 완료: 성공={}, 실패={}", successCount, failedCount)
        return BulkAiSummaryResult(
            totalCount = daycares.size,
            successCount = successCount,
            failedCount = failedCount,
        )
    }
}
