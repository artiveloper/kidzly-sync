package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "gemini")
data class GeminiApiProperties(
    val apiKey: String,
    val baseUrl: String = "https://generativelanguage.googleapis.com",
    val model: String = "gemini-2.0-flash",
    val requestIntervalMs: Long = 4_000L,
)
