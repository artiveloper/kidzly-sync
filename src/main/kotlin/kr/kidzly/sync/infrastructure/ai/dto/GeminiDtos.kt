package kr.kidzly.sync.infrastructure.ai.dto

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty

data class GeminiRequest(
    val contents: List<GeminiContent>,
    @JsonProperty("generationConfig") val generationConfig: GeminiGenerationConfig = GeminiGenerationConfig(),
)

data class GeminiContent(
    val parts: List<GeminiPart>,
    val role: String = "user",
)

data class GeminiPart(
    val text: String,
)

data class GeminiGenerationConfig(
    @JsonProperty("responseMimeType") val responseMimeType: String = "application/json",
    @JsonProperty("maxOutputTokens") val maxOutputTokens: Int = 3000,
    val temperature: Double = 0.3,
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class GeminiResponse(
    val candidates: List<GeminiCandidate> = emptyList(),
) {
    fun firstContent(): String? = candidates.firstOrNull()?.content?.parts?.firstOrNull()?.text
}

@JsonIgnoreProperties(ignoreUnknown = true)
data class GeminiCandidate(
    val content: GeminiContent,
)
