package kr.kidzly.sync.domain.entity

import jakarta.persistence.*
import kr.kidzly.sync.common.nowKst
import java.math.BigDecimal
import java.time.LocalDateTime

/**
 * 어린이놀이시설정보 (safemap.go.kr IF_0007)
 *
 * 조회 전용 엔티티. 쓰기는 [kr.kidzly.sync.infrastructure.persistence.PlaygroundRepositoryImpl]의
 * JDBC UPSERT를 통해서만 수행한다 (Daycare와 동일 패턴).
 */
@Entity
@Table(
    name = "playgrounds",
    indexes = [
        Index(name = "idx_playgrounds_sigungu_code", columnList = "sigungu_code"),
    ],
)
class Playground(
    @Id
    @Column(name = "facility_id", length = 20)
    val facilityId: String,

    @Column(name = "facility_serial_no", length = 20)
    val facilitySerialNo: String?,

    @Column(name = "sido_code", length = 10)
    val sidoCode: String?,

    @Column(name = "sigungu_code", length = 10)
    val sigunguCode: String?,

    @Column(name = "emd_code", length = 20)
    val emdCode: String?,

    @Column(name = "name", length = 200, nullable = false)
    val name: String,

    @Column(name = "address", length = 500)
    val address: String?,

    /** X좌표 — EPSG:3857 Web Mercator (위경도 아님) */
    @Column(name = "coord_x", precision = 15, scale = 4)
    val coordX: BigDecimal?,

    /** Y좌표 — EPSG:3857 Web Mercator (위경도 아님) */
    @Column(name = "coord_y", precision = 15, scale = 4)
    val coordY: BigDecimal?,

    @Column(name = "install_date", length = 8)
    val installDate: String?,

    @Column(name = "facility_code1", length = 20)
    val facilityCode1: String?,

    @Column(name = "facility_code2", length = 20)
    val facilityCode2: String?,

    @Column(name = "install_place_code", length = 10)
    val installPlaceCode: String?,

    @Column(name = "ownership_code", length = 10)
    val ownershipCode: String?,

    @Column(name = "indoor_outdoor_code", length = 10)
    val indoorOutdoorCode: String?,

    @Column(name = "operation_code", length = 10)
    val operationCode: String?,

    @Column(name = "accident_yn", length = 1)
    val accidentYn: String?,

    @Column(name = "deleted_yn", length = 1)
    val deletedYn: String?,

    /** 마지막 변경 반영 시각 (변경 감지 가드에 의해 내용 변경이 없으면 갱신되지 않음) */
    @Column(name = "synced_at", nullable = false)
    val syncedAt: LocalDateTime = nowKst(),
)
