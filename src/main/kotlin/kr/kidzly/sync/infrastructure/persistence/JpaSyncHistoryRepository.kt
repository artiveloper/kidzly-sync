package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.SyncHistory
import org.springframework.data.jpa.repository.JpaRepository

interface JpaSyncHistoryRepository : JpaRepository<SyncHistory, Long>
