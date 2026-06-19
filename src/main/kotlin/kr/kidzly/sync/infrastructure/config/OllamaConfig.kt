package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient

@Configuration
@ConditionalOnProperty(name = ["ai.provider"], havingValue = "ollama")
@EnableConfigurationProperties(OllamaApiProperties::class)
class OllamaConfig(private val ollamaApiProperties: OllamaApiProperties) {

    @Bean("ollamaRestClient")
    fun ollamaRestClient(): RestClient =
        RestClient.builder()
            .baseUrl(ollamaApiProperties.baseUrl)
            .build()
}
