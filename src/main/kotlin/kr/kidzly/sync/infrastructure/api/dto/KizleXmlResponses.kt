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
    val sigunguname: String? = null,
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
    val nrtrroomsize: Double? = null,
    val plgrdco: Int? = null,
    val cctvinstlcnt: Int? = null,
    val chcrtescnt: Int? = null,
    val crrepname: String? = null,
    val crcnfmdt: String? = null,
    val crstdate: String? = null,

    @JacksonXmlProperty(localName = "class_cnt_tot")
    val classCntTot: Int? = null,

    @JacksonXmlProperty(localName = "child_cnt_tot")
    val childCntTot: Int? = null,

    @JacksonXmlProperty(localName = "em_cnt_tot")
    val emCntTot: Int? = null,

    @JacksonXmlProperty(localName = "ew_cnt_tot")
    val ewCntTot: Int? = null,
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
