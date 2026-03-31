package kr.kidzly.sync.domain.entity

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.LocalDateTime

@Entity
@Table(name = "sigungus")
class Sigungu(
    @Id
    @Column(name = "arcode", length = 10)
    val arcode: String,

    @Column(name = "sidoname", length = 50, nullable = false)
    val sidoname: String,

    @Column(name = "sigunname", length = 50, nullable = false)
    val sigunname: String,

    @Column(name = "synced_at", nullable = false)
    val syncedAt: LocalDateTime = LocalDateTime.now(),
)
