package kr.kidzly.sync.infrastructure.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "safemap.api")
data class SafemapApiProperties(
    val baseUrl: String,
    /** 미설정 시 빈 문자열 — FULL/DELTA 배치 기동을 막지 않기 위함 (UseCase 진입 시 검사) */
    val serviceKey: String,
    val pageSize: Int = 1000,
    val requestIntervalMs: Long = 200L,
)
