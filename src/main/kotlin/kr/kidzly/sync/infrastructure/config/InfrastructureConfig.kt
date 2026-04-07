package kr.kidzly.sync.infrastructure.config

import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.databind.MapperFeature
import com.fasterxml.jackson.dataformat.xml.XmlMapper
import com.fasterxml.jackson.module.kotlin.kotlinModule
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.converter.StringHttpMessageConverter
import org.springframework.web.client.RestClient

@Configuration
class InfrastructureConfig(
    private val childcareApiProperties: ChildcareApiProperties,
) {

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
    fun childcareRestClient(): RestClient =
        RestClient.builder()
            .baseUrl(childcareApiProperties.baseUrl)
            .messageConverters { converters ->
                converters.removeIf { it is StringHttpMessageConverter }
                converters.add(0, StringHttpMessageConverter(Charsets.UTF_8))
            }
            .build()

    @Bean("telegramRestClient")
    fun telegramRestClient(): RestClient =
        RestClient.builder()
            .build()
}
