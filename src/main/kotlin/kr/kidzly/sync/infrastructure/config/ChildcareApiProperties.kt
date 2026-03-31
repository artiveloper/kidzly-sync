package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "childcare.api")
data class ChildcareApiProperties(
    val baseUrl: String,
    val retryMaxAttempts: Int = 3,
    val retryDelayMs: Long = 60_000L,
    val keys: Keys,
) {
    data class Keys(
        val sigungu: String,          // cpmsapi020
        val daycareDetail: String,    // cpmsapi030
        val newDaycare: String,       // cpmsapi018
        val closedDaycare: String,    // cpmsapi019
    )
}
