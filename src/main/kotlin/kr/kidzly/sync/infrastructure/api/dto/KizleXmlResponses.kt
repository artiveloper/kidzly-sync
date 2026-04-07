package kr.kidzly.sync.infrastructure.api.dto

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlElementWrapper
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement

// ── cpmsapi020: 시군구 조회 ────────────────────────────────────────────────────

@JacksonXmlRootElement(localName = "response")
data class SigunguXmlResponse(
    @JacksonXmlElementWrapper(useWrapping = false)
    @JacksonXmlProperty(localName = "item")
    val items: List<SigunguXmlItem> = emptyList(),
)

data class SigunguXmlItem(
    val sidoname: String = "",
    val sigunname: String = "",  // cpmsapi020은 sigunname (sigungu아님)
    val arcode: String = "",
)

// ── cpmsapi030: 어린이집별 기본정보 조회 ──────────────────────────────────────

@JacksonXmlRootElement(localName = "response")
data class DaycareDetailXmlResponse(
    @JacksonXmlElementWrapper(useWrapping = false)
    @JacksonXmlProperty(localName = "item")
    val items: List<DaycareDetailXmlItem> = emptyList(),
)

data class DaycareDetailXmlItem(
    val sidoname: String? = null,
    @JacksonXmlProperty(localName = "sigunname") val sigunguname: String? = null,
    val stcode: String = "",
    val crname: String = "",
    val crtypename: String? = null,
    val crstatusname: String? = null,
    val zipcode: String? = null,
    val craddr: String? = null,
    val crtelno: String? = null,
    val crfaxno: String? = null,
    val crhome: String? = null,
    val la: String? = null,
    val lo: String? = null,
    val crcapat: Int? = null,
    val crchcnt: Int? = null,
    val nrtrroomcnt: Int? = null,
    val nrtrroomsize: java.math.BigDecimal? = null,
    val plgrdco: Int? = null,
    val cctvinstlcnt: Int? = null,
    val chcrtescnt: Int? = null,
    val crcargbname: String? = null,
    val crrepname: String? = null,
    val crcnfmdt: String? = null,
    val crpausebegindt: String? = null,
    val crpauseenddt: String? = null,
    val crabldt: String? = null,
    val datastdrdt: String? = null,
    val crspec: String? = null,

    @JacksonXmlProperty(localName = "class_cnt_00") val classCnt00: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_01") val classCnt01: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_02") val classCnt02: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_03") val classCnt03: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_04") val classCnt04: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_05") val classCnt05: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_m2") val classCntM2: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_m5") val classCntM5: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_sp") val classCntSp: Int? = null,
    @JacksonXmlProperty(localName = "class_cnt_tot") val classCntTot: Int? = null,

    @JacksonXmlProperty(localName = "child_cnt_00") val childCnt00: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_01") val childCnt01: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_02") val childCnt02: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_03") val childCnt03: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_04") val childCnt04: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_05") val childCnt05: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_m2") val childCntM2: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_m5") val childCntM5: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_sp") val childCntSp: Int? = null,
    @JacksonXmlProperty(localName = "child_cnt_tot") val childCntTot: Int? = null,

    @JacksonXmlProperty(localName = "em_cnt_0y") val emCnt0y: Double? = null,
    @JacksonXmlProperty(localName = "em_cnt_1y") val emCnt1y: Double? = null,
    @JacksonXmlProperty(localName = "em_cnt_2y") val emCnt2y: Double? = null,
    @JacksonXmlProperty(localName = "em_cnt_4y") val emCnt4y: Double? = null,
    @JacksonXmlProperty(localName = "em_cnt_6y") val emCnt6y: Double? = null,
    @JacksonXmlProperty(localName = "em_cnt_a1") val emCntA1: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a2") val emCntA2: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a3") val emCntA3: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a4") val emCntA4: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a5") val emCntA5: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a6") val emCntA6: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a10") val emCntA10: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a7") val emCntA7: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_a8") val emCntA8: Int? = null,
    @JacksonXmlProperty(localName = "em_cnt_tot") val emCntTot: Int? = null,

    @JacksonXmlProperty(localName = "ew_cnt_00") val ewCnt00: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_01") val ewCnt01: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_02") val ewCnt02: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_03") val ewCnt03: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_04") val ewCnt04: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_05") val ewCnt05: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_m6") val ewCntM6: Int? = null,
    @JacksonXmlProperty(localName = "ew_cnt_tot") val ewCntTot: Int? = null,
)

// ── cpmsapi018/019: 월별 신규/폐지시설 조회 ───────────────────────────────────

@JacksonXmlRootElement(localName = "response")
data class DaycareListXmlResponse(
    @JacksonXmlElementWrapper(useWrapping = false)
    @JacksonXmlProperty(localName = "item")
    val items: List<DaycareListXmlItem> = emptyList(),
)

data class DaycareListXmlItem(
    val stcode: String = "",
    val arcode: String = "",
    val crname: String = "",
    val frstcnfmdt: String? = null,  // 신규 개설일 (cpmsapi018)
    val crstdate: String? = null,    // 폐지일 (cpmsapi019)
)
