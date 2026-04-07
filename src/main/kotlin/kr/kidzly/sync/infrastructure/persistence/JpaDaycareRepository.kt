package kr.kidzly.sync.infrastructure.persistence

import jakarta.transaction.Transactional
import kr.kidzly.sync.domain.entity.Daycare
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param

interface JpaDaycareRepository : JpaRepository<Daycare, String> {

    @Modifying
    @Transactional
    @Query(
        """
        UPDATE Daycare d
        SET d.status = '폐지', d.abolishedDate = :abolishedDate, d.syncedAt = CURRENT_TIMESTAMP
        WHERE d.daycareCode = :daycareCode
        """,
    )
    fun markAsClosed(
        @Param("daycareCode") daycareCode: String,
        @Param("abolishedDate") abolishedDate: String?,
    ): Int
}
