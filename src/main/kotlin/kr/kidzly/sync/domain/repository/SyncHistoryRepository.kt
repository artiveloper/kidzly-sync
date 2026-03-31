package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.domain.entity.SyncHistory

interface SyncHistoryRepository {
    fun save(syncHistory: SyncHistory): SyncHistory
}
