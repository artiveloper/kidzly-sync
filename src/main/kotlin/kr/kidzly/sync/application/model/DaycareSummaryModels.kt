package kr.kidzly.sync.application.model

data class DaycareSummary(
    val summary: String,
    @com.fasterxml.jackson.annotation.JsonProperty("who_may_be_interested")
    val whoMayBeInterested: List<String>,
    @com.fasterxml.jackson.annotation.JsonProperty("things_to_consider")
    val thingsToConsider: List<String>,
)

data class BulkAiSummaryResult(
    val totalCount: Int,
    val successCount: Int,
    val failedCount: Int,
)
