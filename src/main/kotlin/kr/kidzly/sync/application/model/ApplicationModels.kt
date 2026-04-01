package kr.kidzly.sync.application.model

data class SigunguInfo(
    val arcode: String,
    val sidoname: String,
    val sigunname: String,
)

data class NewDaycareInfo(
    val stcode: String,
    val arcode: String,
)

data class ClosedDaycareInfo(
    val stcode: String,
    val crstdate: String?,
)

data class DaycareData(
    val stcode: String,
    val arcode: String,
    val sidoname: String?,
    val sigunguname: String?,
    val crname: String,
    val crtypename: String?,
    val crstatusname: String?,
    val zipcode: String?,
    val craddr: String?,
    val crtelno: String?,
    val crfaxno: String?,
    val crhome: String?,
    val la: String?,
    val lo: String?,
    val crcapat: Int?,
    val crchcnt: Int?,
    val nrtrroomcnt: Int?,
    val nrtrroomsize: java.math.BigDecimal?,
    val plgrdco: Int?,
    val cctvinstlcnt: Int?,
    val chcrtescnt: Int?,
    val classCntTot: Int?,
    val childCntTot: Int?,
    val emCntTot: Int?,
    val ewCntTot: Int?,
    val crrepname: String?,
    val crcnfmdt: String?,
    val crstdate: String?,
)

data class SyncResult(
    val total: Int,
    val upserted: Int,
    val closed: Int = 0,
)
