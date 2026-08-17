package kr.kidzly.sync.infrastructure.api.dto

import com.fasterxml.jackson.annotation.JsonProperty

/**
 * odcloud.kr 법정동코드 조회 응답 (JSON).
 *
 * safemap(XML)과 달리 header/resultCode 래퍼가 없다 — 실패는 HTTP 상태로 전달된다.
 * 필드명이 한글이므로 @JsonProperty 로 명시 매핑한다.
 */
data class LegalDongCodeJsonResponse(
    val page: Int = 0,
    val perPage: Int = 0,
    val totalCount: Int = 0,
    val currentCount: Int = 0,
    /** 에러 응답에는 존재하지 않으므로 nullable */
    val data: List<LegalDongCodeJsonItem>? = null,
)

data class LegalDongCodeJsonItem(
    @param:JsonProperty("법정동코드") val code: String? = null,
    @param:JsonProperty("법정동명") val name: String? = null,
    @param:JsonProperty("폐지여부") val abolishedYn: String? = null,
)
