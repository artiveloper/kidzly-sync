package kr.kidzly.sync.infrastructure.ai

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.infrastructure.ai.dto.GroqChatRequest
import kr.kidzly.sync.infrastructure.ai.dto.GroqChatResponse
import kr.kidzly.sync.infrastructure.ai.dto.GroqMessage
import kr.kidzly.sync.infrastructure.config.GroqApiProperties
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient

@Component
@ConditionalOnProperty(name = ["ai.provider"], havingValue = "groq", matchIfMissing = true)
class GroqApiClient(
    @Qualifier("groqRestClient") private val restClient: RestClient,
    private val groqApiProperties: GroqApiProperties,
    daycareJsonBuilder: DaycareJsonBuilder,
    objectMapper: ObjectMapper,
) : AbstractAiApiClient(daycareJsonBuilder, objectMapper) {

    override val providerName = "Groq"
    override val requestIntervalMs: Long get() = groqApiProperties.requestIntervalMs

    override fun executeRequest(prompt: String): String? {
        val request = GroqChatRequest(
            model = groqApiProperties.model,
            messages = listOf(GroqMessage(role = "user", content = prompt)),
        )
        return restClient.post()
            .uri("/openai/v1/chat/completions")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(GroqChatResponse::class.java)
            ?.firstContent()
    }

    override fun parseRetryAfterMs(responseBody: String): Long {
        val match = RETRY_AFTER_PATTERN.find(responseBody) ?: return DEFAULT_RETRY_WAIT_MS
        val minutes = match.groupValues[1].toDoubleOrNull() ?: 0.0
        val seconds = match.groupValues[2].toDoubleOrNull() ?: 0.0
        val totalMs = ((minutes * 60 + seconds) * 1000).toLong()
        return if (totalMs > 0) totalMs + RETRY_BUFFER_MS else DEFAULT_RETRY_WAIT_MS
    }

    companion object {
        private val RETRY_AFTER_PATTERN = Regex("""Please try again in (?:([\d.]+)m)?([\d.]+)s""")
    }
}
