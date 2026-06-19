package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.domain.entity.Daycare
import java.time.LocalDateTime

interface DaycareRepository {
    fun upsertAll(daycares: List<DaycareData>): Int
    fun markAsClosed(daycareCode: String, abolishedDate: String?): Int
    fun findByCode(daycareCode: String): Daycare?
    fun findAllByStatus(status: String): List<Daycare>
    fun findAllByStatusAndAiAnalysisIsNull(status: String): List<Daycare>
    fun findAllByStatusAndSidoNameAndAiAnalysisIsNull(status: String, sidoName: String): List<Daycare>
    fun findAllByStatusAndSyncedAtAfter(status: String, after: LocalDateTime): List<Daycare>
    fun saveAiAnalysis(daycareCode: String, analysisJson: String)
}
