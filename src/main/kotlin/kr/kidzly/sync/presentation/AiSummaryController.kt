package kr.kidzly.sync.presentation

import kr.kidzly.sync.application.model.BulkAiSummaryResult
import kr.kidzly.sync.application.model.DaycareSummary
import kr.kidzly.sync.application.usecase.AllDaycaresAISummaryUseCase
import kr.kidzly.sync.application.usecase.DaycareAISummaryUseCase
import kr.kidzly.sync.application.usecase.SidoAISummaryUseCase
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.presentation.dto.ApiResponse
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/v1/daycares")
class AiSummaryController(
    private val daycareAISummaryUseCase: DaycareAISummaryUseCase,
    private val allDaycaresAISummaryUseCase: AllDaycaresAISummaryUseCase,
    private val sidoAISummaryUseCase: SidoAISummaryUseCase,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    /**
     * 전체 어린이집(status=정상) AI 요약 일괄 생성
     * POST /api/v1/daycares/ai-summary
     */
    @PostMapping("/ai-summary")
    fun generateAllSummaries(): ResponseEntity<ApiResponse<BulkAiSummaryResult>> {
        log.info("전체 어린이집 AI 요약 일괄 생성 요청")
        val result = allDaycaresAISummaryUseCase.execute()
        return ResponseEntity.ok(ApiResponse.ok(result))
    }

    /**
     * 시도별 어린이집 AI 요약 일괄 생성
     * POST /api/v1/daycares/ai-summary/sido?sidoName=서울특별시
     */
    @PostMapping("/ai-summary/sido")
    fun generateSummariesBySido(
        @RequestParam sidoName: String,
    ): ResponseEntity<ApiResponse<BulkAiSummaryResult>> {
        log.info("시도별 AI 요약 일괄 생성 요청: sidoName={}", sidoName)
        val result = sidoAISummaryUseCase.execute(sidoName)
        return ResponseEntity.ok(ApiResponse.ok(result))
    }

    /**
     * 어린이집 AI 요약 생성
     * POST /api/v1/daycares/{daycareCode}/ai-summary
     */
    @PostMapping("/{daycareCode}/ai-summary")
    fun generateSummary(
        @PathVariable daycareCode: String,
    ): ResponseEntity<ApiResponse<DaycareSummary>> {
        log.info("AI 요약 요청: daycareCode={}", daycareCode)
        return daycareAISummaryUseCase.execute(daycareCode).fold(
            ifLeft = { error ->
                when (error) {
                    is DomainError.NotFound ->
                        ResponseEntity.status(HttpStatus.NOT_FOUND)
                            .body(ApiResponse.error("NOT_FOUND", "어린이집을 찾을 수 없습니다: $daycareCode"))
                    is DomainError.ApiCallError -> {
                        log.error("AI API 오류: status={}, message={}", error.statusCode, error.message)
                        ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                            .body(ApiResponse.error("AI_API_ERROR", "AI 서비스 호출에 실패했습니다."))
                    }
                    else -> {
                        log.error("AI 요약 생성 실패: daycareCode={}, error={}", daycareCode, error)
                        ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                            .body(ApiResponse.error("AI_SUMMARY_ERROR", "AI 요약 생성에 실패했습니다."))
                    }
                }
            },
            ifRight = { summary ->
                ResponseEntity.ok(ApiResponse.ok(summary))
            },
        )
    }
}
