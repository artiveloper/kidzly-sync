package kr.kidzly.sync.domain.entity

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(
    name = "daycares",
    indexes = [Index(name = "idx_daycares_arcode", columnList = "arcode")],
)
class Daycare(
    @Id
    @Column(name = "stcode", length = 20)
    val stcode: String,

    @Column(name = "arcode", length = 10, nullable = false)
    val arcode: String,

    @Column(name = "sidoname", length = 50)
    val sidoname: String?,

    @Column(name = "sigunguname", length = 50)
    val sigunguname: String?,

    @Column(name = "crname", length = 100, nullable = false)
    val crname: String,

    @Column(name = "crtypename", length = 50)
    val crtypename: String?,

    @Column(name = "crstatusname", length = 20)
    val crstatusname: String?,

    @Column(name = "zipcode", length = 10)
    val zipcode: String?,

    @Column(name = "craddr", length = 200)
    val craddr: String?,

    @Column(name = "crtelno", length = 20)
    val crtelno: String?,

    @Column(name = "crfaxno", length = 20)
    val crfaxno: String?,

    @Column(name = "crhome", length = 200)
    val crhome: String?,

    @Column(name = "la", length = 20)
    val la: String?,

    @Column(name = "lo", length = 20)
    val lo: String?,

    @Column(name = "crcapat")
    val crcapat: Int?,

    @Column(name = "crchcnt")
    val crchcnt: Int?,

    @Column(name = "nrtrroomcnt")
    val nrtrroomcnt: Int?,

    @Column(name = "nrtrroomsize")
    val nrtrroomsize: Double?,

    @Column(name = "plgrdco")
    val plgrdco: Int?,

    @Column(name = "cctvinstlcnt")
    val cctvinstlcnt: Int?,

    @Column(name = "chcrtescnt")
    val chcrtescnt: Int?,

    @Column(name = "class_cnt_tot")
    val classCntTot: Int?,

    @Column(name = "child_cnt_tot")
    val childCntTot: Int?,

    @Column(name = "em_cnt_tot")
    val emCntTot: Int?,

    @Column(name = "ew_cnt_tot")
    val ewCntTot: Int?,

    @Column(name = "crrepname", length = 50)
    val crrepname: String?,

    @Column(name = "crcnfmdt", length = 10)
    val crcnfmdt: String?,

    @Column(name = "crstdate", length = 10)
    val crstdate: String?,

    @Column(name = "synced_at", nullable = false)
    val syncedAt: LocalDateTime = LocalDateTime.now(),
)
