package kr.kidzly.sync.application.usecase

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.application.model.BulkAiSummaryResult
import kr.kidzly.sync.application.port.AiSummaryPort
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service

@Service
class SidoAISummaryUseCase(
    private val daycareRepository: DaycareRepository,
    private val aiSummaryPort: AiSummaryPort,
    private val objectMapper: ObjectMapper,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun execute(sidoName: String): BulkAiSummaryResult {
        val daycares = daycareRepository.findAllByStatusAndSidoNameAndAiAnalysisIsNull("정상", sidoName)
        log.info("시도별 AI 요약 생성 시작: sidoName={}, 대상 어린이집 수={}", sidoName, daycares.size)

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

        log.info("시도별 AI 요약 생성 완료: sidoName={}, 성공={}, 실패={}", sidoName, successCount, failedCount)
        return BulkAiSummaryResult(
            totalCount = daycares.size,
            successCount = successCount,
            failedCount = failedCount,
        )
    }
}
