package kr.kidzly.sync.application.model

data class DaycareSummary(
    val summary: String,
    val strengths: List<String>,
    val considerations: List<String>,
    val tags: List<String>,
)

data class BulkAiSummaryResult(
    val totalCount: Int,
    val successCount: Int,
    val failedCount: Int,
)
