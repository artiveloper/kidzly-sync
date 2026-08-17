package kr.kidzly.sync.infrastructure.api.dto

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlElementWrapper
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement

// ── IF_0007: 어린이놀이시설정보 조회 ──────────────────────────────────────────
//
// 주의: childcare(cpmsapi0xx)는 response > item 구조라 useWrapping = false 였으나,
// IF_0007은 response > body > items > item 구조다. items 래퍼를 반드시 사용한다.

@JacksonXmlRootElement(localName = "response")
data class PlaygroundXmlResponse(
    val header: PlaygroundXmlHeader = PlaygroundXmlHeader(),
    val body: PlaygroundXmlBody = PlaygroundXmlBody(),
)

data class PlaygroundXmlHeader(
    val resultCode: String = "",
    val resultMsg: String = "",
)

data class PlaygroundXmlBody(
    /** `<items>` 래퍼. 빈 엘리먼트(`<items></items>`)면 null로 내려오므로 nullable이다. */
    val items: PlaygroundXmlItems? = null,
    val numOfRows: Int = 0,
    val pageNo: Int = 0,
    val totalCount: Int = 0,
)

/**
 * `<items>` 래퍼를 별도 타입으로 둔다.
 *
 * `@JacksonXmlElementWrapper(localName = "items")`를 리스트에 직접 붙이면 Kotlin 생성자 프로퍼티에서
 * "Could not find creator property with name 'items'"로 역직렬화가 통째로 실패한다
 * (`@JacksonXmlProperty(localName = "item")`이 생성자 프로퍼티 이름까지 `item`으로 바꿔버리기 때문).
 * 래퍼를 타입으로 분리하고 내부 리스트는 `useWrapping = false`로 두는 방식이
 * 기존 `KizleXmlResponses.kt`에서 이미 검증된 패턴이다.
 */
data class PlaygroundXmlItems(
    @JacksonXmlElementWrapper(useWrapping = false)
    @JacksonXmlProperty(localName = "item")
    val item: List<PlaygroundXmlItem> = emptyList(),
)

data class PlaygroundXmlItem(
    @JacksonXmlProperty(localName = "objt_id") val objtId: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd1") val fcltyCd1: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd2") val fcltyCd2: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd3") val fcltyCd3: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd4") val fcltyCd4: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd5") val fcltyCd5: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd6") val fcltyCd6: String? = null,
    @JacksonXmlProperty(localName = "fclty_cd7") val fcltyCd7: String? = null,
    @JacksonXmlProperty(localName = "fclty_nm") val fcltyNm: String? = null,
    @JacksonXmlProperty(localName = "ctprvn_cd") val ctprvnCd: String? = null,
    @JacksonXmlProperty(localName = "sgg_cd") val sggCd: String? = null,
    @JacksonXmlProperty(localName = "emd_cd") val emdCd: String? = null,
    @JacksonXmlProperty(localName = "instl_de") val instlDe: String? = null,
    @JacksonXmlProperty(localName = "adres") val adres: String? = null,
    @JacksonXmlProperty(localName = "ac_yn") val acYn: String? = null,
    @JacksonXmlProperty(localName = "del_yn") val delYn: String? = null,
    // 빈 엘리먼트(<x></x>)가 내려오므로 String으로 받아 BigDecimal로 안전 변환한다
    val x: String? = null,
    val y: String? = null,
)
