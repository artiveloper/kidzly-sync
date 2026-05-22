package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient

@Configuration
@ConditionalOnProperty(name = ["ai.provider"], havingValue = "gemini")
@EnableConfigurationProperties(GeminiApiProperties::class)
class GeminiConfig(private val geminiApiProperties: GeminiApiProperties) {

    @Bean("geminiRestClient")
    fun geminiRestClient(): RestClient =
        RestClient.builder()
            .baseUrl(geminiApiProperties.baseUrl)
            .defaultHeader("x-goog-api-key", geminiApiProperties.apiKey)
            .build()
}
