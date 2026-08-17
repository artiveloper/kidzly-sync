package kr.kidzly.sync.application

import arrow.core.Either
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.application.usecase.DeltaSyncUseCase
import kr.kidzly.sync.application.usecase.FullSyncUseCase
import kr.kidzly.sync.application.usecase.IncrementalDaycaresSummaryUseCase
import kr.kidzly.sync.application.usecase.PlaygroundFullSyncUseCase
import kr.kidzly.sync.application.usecase.SigunguCodeSyncUseCase
import kr.kidzly.sync.domain.entity.SyncHistory
import kr.kidzly.sync.domain.entity.SyncStatus
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
        playgroundFullSyncUseCase: PlaygroundFullSyncUseCase = mockk(),
        sigunguCodeSyncUseCase: SigunguCodeSyncUseCase = mockk(),
        syncHistoryRepository: SyncHistoryRepository = mockk(),
        telegramNotifier: TelegramNotifier = mockk(relaxed = true),
    ): SyncOrchestrator {
        every { syncHistoryRepository.save(any()) } answers { firstArg() }
        return SyncOrchestrator(
            fullSyncUseCase = fullSyncUseCase,
            deltaSyncUseCase = deltaSyncUseCase,
            incrementalDaycaresSummaryUseCase = mockk<IncrementalDaycaresSummaryUseCase>(relaxed = true),
            playgroundFullSyncUseCase = playgroundFullSyncUseCase,
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            childcareApiPort = mockk<ChildcareApiPort>(),
            daycareRepository = mockk<DaycareRepository>(),
            sigunguRepository = mockk<SigunguRepository>(),
            syncHistoryRepository = syncHistoryRepository,
            telegramNotifier = telegramNotifier,
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

    test("playgroundSync: 오늘 이미 성공했으면 UseCase를 호출하지 않고 true를 반환한다") {
        val playgroundFullSyncUseCase = mockk<PlaygroundFullSyncUseCase>()
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every {
            syncHistoryRepository.existsCompleted(SyncType.PLAYGROUND, null, any(), any())
        } returns true
        val orchestrator = newOrchestrator(
            playgroundFullSyncUseCase = playgroundFullSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.playgroundSync(skipIfAlreadySucceededToday = true)

        result shouldBe true
        verify(exactly = 0) { playgroundFullSyncUseCase.execute() }
    }

    test("playgroundSync: 성공하면 이력에 total/upsert 건수를 기록하고 true를 반환한다") {
        val playgroundFullSyncUseCase = mockk<PlaygroundFullSyncUseCase>()
        every { playgroundFullSyncUseCase.execute() } returns Either.Right(SyncResult(total = 84251, upserted = 12))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(
            playgroundFullSyncUseCase = playgroundFullSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.playgroundSync()

        result shouldBe true
        val saved = mutableListOf<SyncHistory>()
        verify { syncHistoryRepository.save(capture(saved)) }
        saved.last().syncType shouldBe SyncType.PLAYGROUND
        saved.last().totalCount shouldBe 84251
        saved.last().upsertCount shouldBe 12
    }

    test("playgroundSync: UseCase가 Unauthorized(Left)를 반환하면 false를 반환한다") {
        val playgroundFullSyncUseCase = mockk<PlaygroundFullSyncUseCase>()
        every { playgroundFullSyncUseCase.execute() } returns Either.Left(DomainError.Unauthorized)
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(
            playgroundFullSyncUseCase = playgroundFullSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.playgroundSync()

        result shouldBe false
    }

    // ── 법정동코드 동기화 (SIGUNGU_CODE) ───────────────────────────────────────

    test("sigunguCodeSync: 오늘 이미 성공했으면 UseCase를 호출하지 않고 true를 반환한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every {
            syncHistoryRepository.existsCompleted(SyncType.SIGUNGU_CODE, null, any(), any())
        } returns true
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.sigunguCodeSync(skipIfAlreadySucceededToday = true)

        result shouldBe true
        verify(exactly = 0) { sigunguCodeSyncUseCase.execute() }
        verify(exactly = 0) { syncHistoryRepository.save(any()) }
    }

    test("sigunguCodeSync: skipIfAlreadySucceededToday=false(기본값)면 기존 이력과 무관하게 항상 실행한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        every { sigunguCodeSyncUseCase.execute() } returns Either.Right(SyncResult(total = 5000, upserted = 0))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        every { syncHistoryRepository.existsCompleted(any(), any(), any(), any()) } returns true
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.sigunguCodeSync()

        result shouldBe true
        verify(exactly = 1) { sigunguCodeSyncUseCase.execute() }
    }

    test("sigunguCodeSync: 성공하면 SIGUNGU_CODE 이력을 COMPLETED로 기록하고 true를 반환한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        every { sigunguCodeSyncUseCase.execute() } returns Either.Right(SyncResult(total = 5218, upserted = 3))
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.sigunguCodeSync()

        result shouldBe true
        val saved = mutableListOf<SyncHistory>()
        verify { syncHistoryRepository.save(capture(saved)) }
        saved.last().syncType shouldBe SyncType.SIGUNGU_CODE
        saved.last().status shouldBe SyncStatus.COMPLETED
        saved.last().totalCount shouldBe 5218
        saved.last().upsertCount shouldBe 3
        // 폐지 코드를 물리 삭제하지 않으므로 closedCount는 사용하지 않는다 (설계 §2.4)
        saved.last().closedCount shouldBe 0
        saved.last().targetYearMonth shouldBe null
    }

    test("sigunguCodeSync: 성공하면 완료 텔레그램 알림을 1회 발송한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        every { sigunguCodeSyncUseCase.execute() } returns Either.Right(SyncResult(total = 5218, upserted = 3))
        val telegramNotifier = mockk<TelegramNotifier>(relaxed = true)
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = mockk(),
            telegramNotifier = telegramNotifier,
        )

        orchestrator.sigunguCodeSync()

        val messages = mutableListOf<String>()
        verify(exactly = 1) { telegramNotifier.sendMessage(capture(messages)) }
        messages.last().contains("법정동코드 동기화 완료") shouldBe true
        messages.last().contains("5218") shouldBe true
    }

    test("sigunguCodeSync: UseCase가 Unauthorized(Left)를 반환하면 이력을 FAILED로 기록하고 false를 반환한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        // LEGAL_DONG_CODE_SERVICE_KEY 미등록 시의 경로
        every { sigunguCodeSyncUseCase.execute() } returns Either.Left(DomainError.Unauthorized)
        val syncHistoryRepository = mockk<SyncHistoryRepository>()
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = syncHistoryRepository,
        )

        val result = orchestrator.sigunguCodeSync()

        result shouldBe false
        val saved = mutableListOf<SyncHistory>()
        verify { syncHistoryRepository.save(capture(saved)) }
        saved.last().status shouldBe SyncStatus.FAILED
        saved.last().errorMessage shouldNotBe null
    }

    test("sigunguCodeSync: 실패하면 실패 텔레그램 알림을 1회 발송한다") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        every { sigunguCodeSyncUseCase.execute() } returns
            Either.Left(DomainError.ParseError("data 필드 없음 (page=1)"))
        val telegramNotifier = mockk<TelegramNotifier>(relaxed = true)
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = mockk(),
            telegramNotifier = telegramNotifier,
        )

        orchestrator.sigunguCodeSync() shouldBe false

        val messages = mutableListOf<String>()
        verify(exactly = 1) { telegramNotifier.sendMessage(capture(messages)) }
        messages.last().contains("법정동코드 동기화 실패") shouldBe true
    }

    test("sigunguCodeSync: 실패해도 예외를 던지지 않고 false만 반환한다 (배치 exit code 경로 유지)") {
        val sigunguCodeSyncUseCase = mockk<SigunguCodeSyncUseCase>()
        every { sigunguCodeSyncUseCase.execute() } returns
            Either.Left(DomainError.NetworkError("connect timed out"))
        val orchestrator = newOrchestrator(
            sigunguCodeSyncUseCase = sigunguCodeSyncUseCase,
            syncHistoryRepository = mockk(),
        )

        runCatching { orchestrator.sigunguCodeSync() }.getOrNull() shouldBe false
    }
})
