package kr.kidzly.sync.infrastructure.config

import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.databind.MapperFeature
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.dataformat.xml.XmlMapper
import com.fasterxml.jackson.module.kotlin.kotlinModule
import org.apache.hc.client5.http.config.ConnectionConfig
import org.apache.hc.client5.http.config.RequestConfig
import org.apache.hc.client5.http.impl.classic.HttpClients
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager
import org.apache.hc.core5.util.Timeout
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Primary
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory
import org.springframework.http.converter.StringHttpMessageConverter
import org.springframework.web.client.RestClient

@Configuration
class InfrastructureConfig(
    private val childcareApiProperties: ChildcareApiProperties,
) {

    @Bean
    @Primary
    fun objectMapper(): ObjectMapper =
        ObjectMapper()
            .registerModule(kotlinModule())
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)

    @Bean
    fun xmlMapper(): XmlMapper =
        XmlMapper.builder()
            .addModule(kotlinModule())
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            .configure(DeserializationFeature.ACCEPT_SINGLE_VALUE_AS_ARRAY, true)
            .configure(DeserializationFeature.ACCEPT_EMPTY_STRING_AS_NULL_OBJECT, true)
            .configure(MapperFeature.ACCEPT_CASE_INSENSITIVE_PROPERTIES, true)
            .build()

    @Bean("childcareRestClient")
    fun childcareRestClient(): RestClient {
        val connectionConfig = ConnectionConfig.custom()
            .setConnectTimeout(Timeout.ofSeconds(30))
            .build()

        val connectionManager = PoolingHttpClientConnectionManager()
        connectionManager.maxTotal = 10
        connectionManager.defaultMaxPerRoute = 5
        connectionManager.setDefaultConnectionConfig(connectionConfig)

        val requestConfig = RequestConfig.custom()
            .setConnectionRequestTimeout(Timeout.ofSeconds(10))
            .setResponseTimeout(Timeout.ofSeconds(60))
            .build()

        val httpClient = HttpClients.custom()
            .setConnectionManager(connectionManager)
            .setDefaultRequestConfig(requestConfig)
            .build()

        return RestClient.builder()
            .baseUrl(childcareApiProperties.baseUrl)
            .requestFactory(HttpComponentsClientHttpRequestFactory(httpClient))
            .messageConverters { converters ->
                converters.removeIf { it is StringHttpMessageConverter }
                converters.add(0, StringHttpMessageConverter(Charsets.UTF_8))
            }
            .build()
    }

    @Bean("telegramRestClient")
    fun telegramRestClient(): RestClient =
        RestClient.builder()
            .build()

    @Bean("groqRestClient")
    @ConditionalOnProperty(name = ["ai.provider"], havingValue = "groq", matchIfMissing = true)
    fun groqRestClient(groqApiProperties: GroqApiProperties): RestClient =
        RestClient.builder()
            .baseUrl(groqApiProperties.baseUrl)
            .defaultHeader("Authorization", "Bearer ${groqApiProperties.apiKey}")
            .build()
}
