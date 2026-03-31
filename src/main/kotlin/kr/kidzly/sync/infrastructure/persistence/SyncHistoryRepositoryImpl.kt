package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.repository.SyncHistoryRepository
import org.springframework.stereotype.Repository

@Repository
class SyncHistoryRepositoryImpl(
    private val jpaSyncHistoryRepository: JpaSyncHistoryRepository,
) : SyncHistoryRepository {

    override fun save(syncHistory: SyncHistory): SyncHistory =
        jpaSyncHistoryRepository.save(syncHistory)
}
