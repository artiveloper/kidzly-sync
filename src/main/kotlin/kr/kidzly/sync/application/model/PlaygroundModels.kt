package kr.kidzly.sync.application.model

import java.math.BigDecimal

/** 어린이놀이시설 1건 (safemap.go.kr IF_0007) */
data class PlaygroundData(
    /** 정규화된 objt_id ("1741.0" → "1741") */
    val facilityId: String,
    val facilitySerialNo: String?,
    val sidoCode: String?,
    val sigunguCode: String?,
    val emdCode: String?,
    val name: String,
    val address: String?,
    /** EPSG:3857 Web Mercator X (위경도 아님) */
    val coordX: BigDecimal?,
    /** EPSG:3857 Web Mercator Y (위경도 아님) */
    val coordY: BigDecimal?,
    val installDate: String?,
    val facilityCode1: String?,
    val facilityCode2: String?,
    val installPlaceCode: String?,
    val ownershipCode: String?,
    val indoorOutdoorCode: String?,
    val operationCode: String?,
    val accidentYn: String?,
    val deletedYn: String?,
)

/** IF_0007 한 페이지 응답 */
data class PlaygroundPage(
    val items: List<PlaygroundData>,
    val pageNo: Int,
    val numOfRows: Int,
    val totalCount: Int,
)
