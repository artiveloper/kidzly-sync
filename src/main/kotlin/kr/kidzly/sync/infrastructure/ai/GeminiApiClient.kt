package kr.kidzly.sync.infrastructure.ai

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.infrastructure.ai.dto.GeminiContent
import kr.kidzly.sync.infrastructure.ai.dto.GeminiPart
import kr.kidzly.sync.infrastructure.ai.dto.GeminiRequest
import kr.kidzly.sync.infrastructure.ai.dto.GeminiResponse
import kr.kidzly.sync.infrastructure.config.GeminiApiProperties
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient

@Component
@ConditionalOnProperty(name = ["ai.provider"], havingValue = "gemini")
class GeminiApiClient(
    @Qualifier("geminiRestClient") private val restClient: RestClient,
    private val geminiApiProperties: GeminiApiProperties,
    daycareJsonBuilder: DaycareJsonBuilder,
    objectMapper: ObjectMapper,
) : AbstractAiApiClient(daycareJsonBuilder, objectMapper) {

    override val providerName = "Gemini"
    override val requestIntervalMs: Long get() = geminiApiProperties.requestIntervalMs

    override fun executeRequest(prompt: String): String? {
        val request = GeminiRequest(
            contents = listOf(GeminiContent(parts = listOf(GeminiPart(text = prompt)))),
        )
        return restClient.post()
            .uri("/v1beta/models/${geminiApiProperties.model}:generateContent")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(GeminiResponse::class.java)
            ?.firstContent()
    }

    override fun parseRetryAfterMs(responseBody: String): Long {
        val seconds = RETRY_AFTER_PATTERN.find(responseBody)
            ?.groupValues?.get(1)
            ?.toDoubleOrNull()
        return if (seconds != null) (seconds * 1000).toLong() + RETRY_BUFFER_MS else DEFAULT_RETRY_WAIT_MS
    }

    companion object {
        private val RETRY_AFTER_PATTERN = Regex("""retryDelay["\s:]+(\d+)s""")
    }
}
