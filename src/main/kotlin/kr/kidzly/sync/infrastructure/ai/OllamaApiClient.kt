package kr.kidzly.sync.infrastructure.ai

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.infrastructure.ai.dto.GroqChatRequest
import kr.kidzly.sync.infrastructure.ai.dto.GroqChatResponse
import kr.kidzly.sync.infrastructure.ai.dto.GroqMessage
import kr.kidzly.sync.infrastructure.config.OllamaApiProperties
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient

@Component
@ConditionalOnProperty(name = ["ai.provider"], havingValue = "ollama")
class OllamaApiClient(
    @Qualifier("ollamaRestClient") private val restClient: RestClient,
    private val ollamaApiProperties: OllamaApiProperties,
    daycareJsonBuilder: DaycareJsonBuilder,
    objectMapper: ObjectMapper,
) : AbstractAiApiClient(daycareJsonBuilder, objectMapper) {

    override val providerName = "Ollama"
    override val requestIntervalMs: Long get() = ollamaApiProperties.requestIntervalMs

    override fun executeRequest(prompt: String): String? {
        val request = GroqChatRequest(
            model = ollamaApiProperties.model,
            messages = listOf(GroqMessage(role = "user", content = prompt)),
        )
        val content = restClient.post()
            .uri("/v1/chat/completions")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(GroqChatResponse::class.java)
            ?.firstContent()

        // Qwen3 thinking 모드가 활성화된 경우 <think>...</think> 태그 제거
        return content?.let { THINK_TAG_PATTERN.replace(it, "").trim() }
    }

    // Ollama는 로컬 서버라 429 rate limit이 없으므로 호출되지 않음
    override fun parseRetryAfterMs(responseBody: String): Long = DEFAULT_RETRY_WAIT_MS

    companion object {
        private val THINK_TAG_PATTERN = Regex("""<think>[\s\S]*?</think>""")
    }
}
