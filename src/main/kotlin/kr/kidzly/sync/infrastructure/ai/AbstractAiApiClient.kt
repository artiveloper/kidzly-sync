package kr.kidzly.sync.infrastructure.ai

import arrow.core.Either
import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.application.model.DaycareSummary
import kr.kidzly.sync.application.port.AiSummaryPort
import kr.kidzly.sync.domain.entity.Daycare
import kr.kidzly.sync.domain.error.DomainError
import org.slf4j.LoggerFactory
import org.springframework.core.io.ClassPathResource
import org.springframework.web.client.RestClientResponseException

abstract class AbstractAiApiClient(
    private val daycareJsonBuilder: DaycareJsonBuilder,
    private val objectMapper: ObjectMapper,
) : AiSummaryPort {

    private val log = LoggerFactory.getLogger(javaClass)
    private val promptTemplate = ClassPathResource("prompts/daycare-ai-summary.txt")
        .inputStream.bufferedReader().readText()

    protected abstract val providerName: String

    // null 반환 시 "empty response" 에러로 처리
    protected abstract fun executeRequest(prompt: String): String?

    // 429 응답 본문 포맷이 provider마다 다르므로 각 구현체에서 파싱
    protected abstract fun parseRetryAfterMs(responseBody: String): Long

    override fun generateSummary(daycare: Daycare): Either<DomainError, DaycareSummary> =
        attempt(daycare, attempt = 1)

    private fun attempt(daycare: Daycare, attempt: Int): Either<DomainError, DaycareSummary> {
        return try {
            val prompt = promptTemplate.replace("{{어린이집JSON}}", daycareJsonBuilder.build(daycare))

            val content = executeRequest(prompt)
                ?: return Either.Left(DomainError.Unknown("$providerName API returned empty response"))

            log.debug("{} raw content for daycare={}: {}", providerName, daycare.daycareCode, content)

            Either.Right(objectMapper.readValue(content, DaycareSummary::class.java))
        } catch (e: RestClientResponseException) {
            if (e.statusCode.value() == 429 && attempt <= MAX_RETRIES) {
                val waitMs = parseRetryAfterMs(e.responseBodyAsString)
                log.warn("Rate limit: daycareCode={}, {}ms 후 재시도 ({}/{})", daycare.daycareCode, waitMs, attempt, MAX_RETRIES)
                Thread.sleep(waitMs)
                attempt(daycare, attempt + 1)
            } else {
                log.error("{} API HTTP error: status={}, body={}", providerName, e.statusCode, e.responseBodyAsString, e)
                Either.Left(DomainError.ApiCallError(e.statusCode.value(), null, e.message ?: "$providerName API HTTP error"))
            }
        } catch (e: Exception) {
            log.error("{} API call failed for daycare={}", providerName, daycare.daycareCode, e)
            Either.Left(DomainError.Unknown("$providerName API call failed: ${e.message}", e))
        }
    }

    companion object {
        const val MAX_RETRIES = 3
        const val RETRY_BUFFER_MS = 1_000L
        const val DEFAULT_RETRY_WAIT_MS = 30_000L // 응답 본문에 retryDelay가 없을 때 fallback
    }
}
