package kr.kidzly.sync.domain.entity

import jakarta.persistence.*
import kr.kidzly.sync.common.nowKst
import kr.kidzly.sync.domain.model.SigunguCodeLevel
import java.time.LocalDateTime

/**
 * 국토교통부 공식 법정동코드 참조 테이블 (odcloud.kr, 리 레벨 제외)
 *
 * 조회 전용 엔티티. 쓰기는 [kr.kidzly.sync.infrastructure.persistence.SigunguCodeRepositoryImpl]의
 * JDBC UPSERT를 통해서만 수행한다 (Playground와 동일 패턴).
 */
@Entity
@Table(
    name = "sigungu_codes",
    indexes = [
        Index(name = "idx_sigungu_codes_sigungu_code", columnList = "sigungu_code"),
        Index(name = "idx_sigungu_codes_emd_code", columnList = "emd_code"),
    ],
)
class SigunguCode(
    @Id
    @Column(name = "code", length = 10)
    val code: String,

    @Enumerated(EnumType.STRING)
    @Column(name = "level", length = 10, nullable = false)
    val level: SigunguCodeLevel,

    @Column(name = "sido_code", length = 2, nullable = false)
    val sidoCode: String,

    @Column(name = "sigungu_code", length = 5)
    val sigunguCode: String?,

    @Column(name = "emd_code", length = 8)
    val emdCode: String?,

    @Column(name = "name", length = 200, nullable = false)
    val name: String,

    /** 마지막 변경 반영 시각 (변경 감지 가드에 의해 내용 변경이 없으면 갱신되지 않음) */
    @Column(name = "synced_at", nullable = false)
    val syncedAt: LocalDateTime = nowKst(),
)
