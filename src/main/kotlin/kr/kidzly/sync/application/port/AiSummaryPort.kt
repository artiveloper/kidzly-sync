package kr.kidzly.sync.application.port

import arrow.core.Either
import kr.kidzly.sync.application.model.DaycareSummary
import kr.kidzly.sync.domain.entity.Daycare
import kr.kidzly.sync.domain.error.DomainError

interface AiSummaryPort {
    fun generateSummary(daycare: Daycare): Either<DomainError, DaycareSummary>
    val requestIntervalMs: Long
}
