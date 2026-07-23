package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncStatus
import kr.kidzly.sync.domain.entity.SyncType
import kr.kidzly.sync.domain.repository.SyncHistoryRepository
import org.springframework.stereotype.Repository
import java.time.LocalDateTime

@Repository
class SyncHistoryRepositoryImpl(
    private val jpaSyncHistoryRepository: JpaSyncHistoryRepository,
) : SyncHistoryRepository {

    override fun save(syncHistory: SyncHistory): SyncHistory =
        jpaSyncHistoryRepository.save(syncHistory)

    override fun existsCompleted(
        syncType: SyncType,
        targetYearMonth: String?,
        from: LocalDateTime,
        to: LocalDateTime,
    ): Boolean =
        if (targetYearMonth != null) {
            jpaSyncHistoryRepository.existsBySyncTypeAndTargetYearMonthAndStatusAndFinishedAtBetween(
                syncType, targetYearMonth, SyncStatus.COMPLETED, from, to,
            )
        } else {
            jpaSyncHistoryRepository.existsBySyncTypeAndStatusAndFinishedAtBetween(
                syncType, SyncStatus.COMPLETED, from, to,
            )
        }
}
