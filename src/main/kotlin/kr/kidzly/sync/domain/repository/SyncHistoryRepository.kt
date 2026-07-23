package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncType
import java.time.LocalDateTime

interface SyncHistoryRepository {
    fun save(syncHistory: SyncHistory): SyncHistory
    fun existsCompleted(
        syncType: SyncType,
        targetYearMonth: String?,
        from: LocalDateTime,
        to: LocalDateTime,
    ): Boolean
}
