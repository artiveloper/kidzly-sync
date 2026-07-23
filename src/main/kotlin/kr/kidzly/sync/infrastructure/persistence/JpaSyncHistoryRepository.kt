package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncStatus
import kr.kidzly.sync.domain.entity.SyncType
import org.springframework.data.jpa.repository.JpaRepository
import java.time.LocalDateTime

interface JpaSyncHistoryRepository : JpaRepository<SyncHistory, Long> {
    fun existsBySyncTypeAndTargetYearMonthAndStatusAndFinishedAtBetween(
        syncType: SyncType,
        targetYearMonth: String,
        status: SyncStatus,
        from: LocalDateTime,
        to: LocalDateTime,
    ): Boolean

    fun existsBySyncTypeAndStatusAndFinishedAtBetween(
        syncType: SyncType,
        status: SyncStatus,
        from: LocalDateTime,
        to: LocalDateTime,
    ): Boolean
}
