package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "ollama")
data class OllamaApiProperties(
    val baseUrl: String = "http://localhost:11434",
    val model: String = "qwen3:8b",
    val requestIntervalMs: Long = 0L,
)
