package kr.kidzly.sync.presentation

import kr.kidzly.sync.application.SyncOrchestrator
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.presentation.dto.ApiResponse
import org.slf4j.LoggerFactory
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.time.YearMonth
import java.time.format.DateTimeParseException

@RestController
@RequestMapping("/api/v1/sync")
class SyncController(
    private val syncOrchestrator: SyncOrchestrator,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    /**
     * 전체 동기화 수동 실행
     * POST /api/v1/sync/full
     */
    @PostMapping("/full")
    fun triggerFullSync(): ResponseEntity<ApiResponse<String>> {
        log.info("=== 전체 동기화 수동 실행 요청 ===")
        Thread.ofVirtual().name("manual-full-sync").start {
            syncOrchestrator.fullSync()
        }
        return ResponseEntity.accepted()
            .body(ApiResponse.ok("전체 동기화가 백그라운드에서 시작되었습니다."))
    }

    /**
     * 증분 동기화 수동 실행
     * POST /api/v1/sync/delta?yearMonth=2026-03  (생략 시 당월)
     */
    @PostMapping("/delta")
    fun triggerDeltaSync(
        @RequestParam(required = false) yearMonth: String?,
    ): ResponseEntity<ApiResponse<String>> {
        val targetMonth = if (yearMonth != null) {
            try {
                YearMonth.parse(yearMonth)
            } catch (e: DateTimeParseException) {
                return ResponseEntity.badRequest()
                    .body(ApiResponse.error("INVALID_YEAR_MONTH", "yearMonth 형식이 올바르지 않습니다. 예: 2026-03"))
            }
        } else {
            YearMonth.now()
        }

        log.info("=== 증분 동기화 수동 실행 요청 (대상월=$targetMonth) ===")
        Thread.ofVirtual().name("manual-delta-sync-$targetMonth").start {
            syncOrchestrator.deltaSync(targetMonth)
        }
        return ResponseEntity.accepted()
            .body(ApiResponse.ok("증분 동기화(${targetMonth})가 백그라운드에서 시작되었습니다."))
    }

    /**
     * 시군구 목록 동기화 (cpmsapi020)
     * POST /api/v1/sync/sigungu?sidoname=서울특별시  — 특정 시도
     * POST /api/v1/sync/sigungu                   — 전체 17개 시도 (백그라운드)
     */
    @PostMapping("/sigungu")
    fun triggerSigunguSync(
        @RequestParam(required = false) sidoname: String?,
    ): ResponseEntity<ApiResponse<String>> {
        return if (sidoname != null) {
            val result = syncOrchestrator.syncSigungu(sidoname)
            ResponseEntity.ok(ApiResponse.ok("시군구 동기화 완료 — total=${result.total}, upserted=${result.upserted}"))
        } else {
            log.info("=== 전체 시군구 동기화 수동 실행 요청 ===")
            Thread.ofVirtual().name("manual-sigungu-sync-all").start {
                syncOrchestrator.syncSigungu()
            }
            ResponseEntity.accepted()
                .body(ApiResponse.ok("전체 시군구 동기화가 백그라운드에서 시작되었습니다."))
        }
    }

    /**
     * 특정 시군구의 어린이집 상세 동기화 (cpmsapi030)
     * POST /api/v1/sync/daycare-detail?arcode=11010
     */
    @PostMapping("/daycare-detail")
    fun triggerDaycareDetailSync(
        @RequestParam arcode: String,
    ): ResponseEntity<ApiResponse<SyncResult>> {
        val result = syncOrchestrator.syncDaycareDetail(arcode)
        return ResponseEntity.ok(ApiResponse.ok(result))
    }

    /**
     * 월별 신규 어린이집 동기화 (cpmsapi018)
     * POST /api/v1/sync/new-daycare?yearMonth=2026-03  (생략 시 당월)
     */
    @PostMapping("/new-daycare")
    fun triggerNewDaycareSync(
        @RequestParam(required = false) yearMonth: String?,
    ): ResponseEntity<ApiResponse<SyncResult>> {
        val targetMonth = parseYearMonth(yearMonth)
            ?: return ResponseEntity.badRequest()
                .body(ApiResponse.error("INVALID_YEAR_MONTH", "yearMonth 형식이 올바르지 않습니다. 예: 2026-03"))
        val result = syncOrchestrator.syncNewDaycare(targetMonth)
        return ResponseEntity.ok(ApiResponse.ok(result))
    }

    /**
     * 월별 폐지 어린이집 동기화 (cpmsapi019)
     * POST /api/v1/sync/closed-daycare?yearMonth=2026-03  (생략 시 당월)
     */
    @PostMapping("/closed-daycare")
    fun triggerClosedDaycareSync(
        @RequestParam(required = false) yearMonth: String?,
    ): ResponseEntity<ApiResponse<SyncResult>> {
        val targetMonth = parseYearMonth(yearMonth)
            ?: return ResponseEntity.badRequest()
                .body(ApiResponse.error("INVALID_YEAR_MONTH", "yearMonth 형식이 올바르지 않습니다. 예: 2026-03"))
        val result = syncOrchestrator.syncClosedDaycare(targetMonth)
        return ResponseEntity.ok(ApiResponse.ok(result))
    }

    private fun parseYearMonth(value: String?): YearMonth? =
        if (value == null) YearMonth.now()
        else try { YearMonth.parse(value) } catch (e: DateTimeParseException) { null }
}
