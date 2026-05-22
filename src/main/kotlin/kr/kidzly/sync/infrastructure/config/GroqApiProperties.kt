package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "groq")
data class GroqApiProperties(
    val apiKey: String,
    val baseUrl: String = "https://api.groq.com",
    val model: String = "llama-3.3-70b-versatile",
    val requestIntervalMs: Long = 20_000L,
)
