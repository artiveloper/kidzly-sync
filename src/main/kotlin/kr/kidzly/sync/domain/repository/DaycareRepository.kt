package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.application.model.DaycareData

interface DaycareRepository {
    fun upsertAll(daycares: List<DaycareData>): Int
    fun markAsClosed(daycareCode: String, abolishedDate: String?): Int
}
