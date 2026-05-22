package kr.kidzly.sync.infrastructure.ai.dto

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty

data class GroqChatRequest(
    val model: String,
    val messages: List<GroqMessage>,
    val temperature: Double = 0.3,
    @JsonProperty("response_format") val responseFormat: GroqResponseFormat = GroqResponseFormat(),
    @JsonProperty("max_completion_tokens") val maxCompletionTokens: Int = 3000,
)

data class GroqMessage(
    val role: String,
    val content: String,
)

data class GroqResponseFormat(
    val type: String = "json_object",
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class GroqChatResponse(
    val choices: List<GroqChoice> = emptyList(),
) {
    fun firstContent(): String? = choices.firstOrNull()?.message?.content
}

@JsonIgnoreProperties(ignoreUnknown = true)
data class GroqChoice(
    val message: GroqMessage,
)
