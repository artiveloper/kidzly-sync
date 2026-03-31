package kr.kidzly.sync.domain.entity

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "sync_histories")
class SyncHistory(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    @Enumerated(EnumType.STRING)
    @Column(name = "sync_type", length = 10, nullable = false)
    val syncType: SyncType,

    @Column(name = "target_year_month", length = 7)
    val targetYearMonth: String? = null,

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 10, nullable = false)
    var status: SyncStatus = SyncStatus.RUNNING,

    @Column(name = "total_count")
    var totalCount: Int = 0,

    @Column(name = "upsert_count")
    var upsertCount: Int = 0,

    @Column(name = "closed_count")
    var closedCount: Int = 0,

    @Column(name = "error_message", length = 2000)
    var errorMessage: String? = null,

    @Column(name = "started_at", nullable = false)
    val startedAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "finished_at")
    var finishedAt: LocalDateTime? = null,
)

enum class SyncType { FULL, DELTA }
enum class SyncStatus { RUNNING, COMPLETED, FAILED }
