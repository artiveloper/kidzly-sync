package kr.kidzly.sync.application.model

import kr.kidzly.sync.domain.model.SigunguCodeLevel

/** 법정동코드 API 원본 1건 (가공 전) */
data class LegalDongCodeRecord(
    /** 법정동코드 (10자리 문자열, 선행 0 보존) */
    val code: String,
    /** 법정동명 원문 */
    val name: String,
    /** 폐지여부: "존재" / "폐지" */
    val abolishedYn: String?,
)

/** 법정동코드 API 한 페이지 응답 */
data class LegalDongCodePage(
    val items: List<LegalDongCodeRecord>,
    val page: Int,
    val perPage: Int,
    val totalCount: Int,
)

/** sigungu_codes 쓰기 모델 (UPSERT 입력) */
data class SigunguCodeData(
    val code: String,
    val level: SigunguCodeLevel,
    val sidoCode: String,
    val sigunguCode: String?,
    val emdCode: String?,
    val name: String,
)
