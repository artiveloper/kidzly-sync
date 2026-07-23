package kr.kidzly.sync.application

import arrow.core.Either
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.application.usecase.DeltaSyncUseCase
import kr.kidzly.sync.application.usecase.FullSyncUseCase
import kr.kidzly.sync.application.usecase.IncrementalDaycaresSummaryUseCase
import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncType
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.DaycareRepository
import kr.kidzly.sync.domain.repository.SigunguRepository
import kr.kidzly.sync.domain.repository.SyncHistoryRepository
import kr.kidzly.sync.infrastructure.notification.TelegramNotifier
import java.time.YearMonth

class SyncOrchestratorTest : FunSpec({

    fun newOrchestrator(
        fullSyncUseCase: FullSyncUseCase = mockk(),
        deltaSyncUseCase: DeltaSyncUseCase = mockk(),
        syncHistoryRepository: SyncHistoryRepository = mockk(),
    ): SyncOrchestrator {
        every { syncHistoryRepository.save(any()) } answers { firstArg() }
        return SyncOrchestrator(
            fullSyncUseCase = fullSyncUseCase,
            deltaSyncUseCase = deltaSyncUseCase,
            incrementalDaycaresSummaryUseCase = mockk<IncrementalDaycaresSummaryUseCase>(relaxed = true),
            childcareApiPort = mockk<ChildcareApiPort>(),
            daycareRepository = mockk<DaycareRepository>(),
            sigunguRepository = mockk<SigunguRepository>(),
            syncHistoryRepository = syncHistoryRepository,
            telegramNotifier = mockk<TelegramNotifier>(relaxed = true),
        )
    }

    test("deltaSync: 오늘 이미 성공했으면 UseCase를 호출하지 않고 true를 반환한다") {
        val deltaSyncUseCase = mockk<DeltaSyncUseCase>()
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every {
            syncHistoryRepository.existsCompleted(SyncType.DELTA, "202607", any(), any())
        } returns true
        val orchestrator = newOrchestrator(deltaSyncUseCase = deltaSyncUseCase, syncHistoryRepository = syncHistoryRepository)

        val result = orchestrator.deltaSync(YearMonth.of(2026, 7), skipIfAlreadySucceededToday = true)

        result shouldBe true
        verify(exactly = 0) { deltaSyncUseCase.execute(any()) }
    }

    test("deltaSync: skipIfAlreadySucceededToday=false(기본값)면 기존 이력과 무관하게 항상 실행한다") {
        val deltaSyncUseCase = mockk<DeltaSyncUseCase>()
        every { deltaSyncUseCase.execute(any()) } returns Either.Right(SyncResult(total = 1, upserted = 0, closed = 0))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every { syncHistoryRepository.existsCompleted(any(), any(), any(), any()) } returns true
        val orchestrator = newOrchestrator(deltaSyncUseCase = deltaSyncUseCase, syncHistoryRepository = syncHistoryRepository)

        val result = orchestrator.deltaSync(YearMonth.of(2026, 7))

        result shouldBe true
        verify(exactly = 1) { deltaSyncUseCase.execute(YearMonth.of(2026, 7)) }
    }

    test("deltaSync: UseCase가 실패(Either.Left)하면 false를 반환한다") {
        val deltaSyncUseCase = mockk<DeltaSyncUseCase>()
        every { deltaSyncUseCase.execute(any()) } returns Either.Left(DomainError.NetworkError("connect timed out"))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(deltaSyncUseCase = deltaSyncUseCase, syncHistoryRepository = syncHistoryRepository)

        val result = orchestrator.deltaSync(YearMonth.of(2026, 7))

        result shouldBe false
    }

    test("fullSync: 오늘 이미 성공했으면 UseCase를 호출하지 않고 true를 반환한다") {
        val fullSyncUseCase = mockk<FullSyncUseCase>()
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every {
            syncHistoryRepository.existsCompleted(SyncType.FULL, null, any(), any())
        } returns true
        val orchestrator = newOrchestrator(fullSyncUseCase = fullSyncUseCase, syncHistoryRepository = syncHistoryRepository)

        val result = orchestrator.fullSync(skipIfAlreadySucceededToday = true)

        result shouldBe true
        verify(exactly = 0) { fullSyncUseCase.execute() }
    }

    test("fullSync: UseCase가 실패(Either.Left)하면 false를 반환한다") {
        val fullSyncUseCase = mockk<FullSyncUseCase>()
        every { fullSyncUseCase.execute() } returns Either.Left(DomainError.NetworkError("connect timed out"))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(fullSyncUseCase = fullSyncUseCase, syncHistoryRepository = syncHistoryRepository)

        val result = orchestrator.fullSync()

        result shouldBe false
    }
})
