package kr.kidzly.sync.application.usecase

import arrow.core.Either
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kr.kidzly.sync.application.model.PlaygroundData
import kr.kidzly.sync.application.model.PlaygroundPage
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.SafemapApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.repository.PlaygroundRepository
import kr.kidzly.sync.infrastructure.config.SafemapApiProperties

/**
 * [PlaygroundFullSyncUseCase] 페이지네이션 순회 / fail-fast / 방어 로직 단위 테스트.
 *
 * `requestIntervalMs = 0`으로 두어 Thread.sleep 대기 없이 실행된다.
 */
class PlaygroundFullSyncUseCaseTest : FunSpec({

    fun props(serviceKey: String = "TEST_KEY", pageSize: Int = 1000) = SafemapApiProperties(
        baseUrl = "https://safemap.go.kr",
        serviceKey = serviceKey,
        pageSize = pageSize,
        requestIntervalMs = 0L,
    )

    // ── 페이지네이션 종료 조건 ─────────────────────────────────────────────────

    test("should call the API exactly 3 times when totalCount=2500 and pageSize=1000") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 1000, totalCount = 2500))
        every { port.fetchPlaygrounds(2, 1000) } returns Either.Right(page(2, 1000, totalCount = 2500))
        every { port.fetchPlaygrounds(3, 1000) } returns Either.Right(page(3, 500, totalCount = 2500))
        every { repository.upsertAll(any()) } answers { firstArg<List<PlaygroundData>>().size }

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        result shouldBe Either.Right(SyncResult(total = 2500, upserted = 2500))
        verify(exactly = 1) { port.fetchPlaygrounds(1, 1000) }
        verify(exactly = 1) { port.fetchPlaygrounds(2, 1000) }
        verify(exactly = 1) { port.fetchPlaygrounds(3, 1000) }
        verify(exactly = 0) { port.fetchPlaygrounds(4, any()) }
    }

    test("should stop after the first page when totalCount fits into a single page") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 30, totalCount = 30))
        every { repository.upsertAll(any()) } returns 30

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        (result as Either.Right).value.total shouldBe 30
        verify(exactly = 1) { port.fetchPlaygrounds(any(), any()) }
    }

    test("should fix the page count from the first response and ignore a later totalCount change") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 1000, totalCount = 2000))
        // 순회 도중 원본 totalCount가 늘어도 첫 페이지 기준(2페이지)에서 종료한다
        every { port.fetchPlaygrounds(2, 1000) } returns Either.Right(page(2, 1000, totalCount = 9000))
        every { repository.upsertAll(any()) } answers { firstArg<List<PlaygroundData>>().size }

        PlaygroundFullSyncUseCase(port, repository, props()).execute()

        verify(exactly = 0) { port.fetchPlaygrounds(3, any()) }
    }

    test("should stop as soon as a page returns an empty item list") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        // totalCount가 비정상적으로 커도 빈 페이지에서 반드시 멈춘다 (무한 루프 방지)
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 1000, totalCount = 999_999))
        every { port.fetchPlaygrounds(2, 1000) } returns Either.Right(page(2, 0, totalCount = 999_999))
        every { repository.upsertAll(any()) } answers { firstArg<List<PlaygroundData>>().size }

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        (result as Either.Right).value.total shouldBe 1000
        verify(exactly = 0) { port.fetchPlaygrounds(3, any()) }
        verify(exactly = 1) { repository.upsertAll(any()) }
    }

    test("should return an empty result and never touch the repository when the first page is empty") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 0, totalCount = 0))

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        result shouldBe Either.Right(SyncResult(total = 0, upserted = 0))
        verify(exactly = 0) { repository.upsertAll(any()) }
    }

    // ── fail-fast ────────────────────────────────────────────────────────────

    test("should fail fast and skip the remaining pages when page 2 returns Left") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        val failure = DomainError.NetworkError("connect timed out")
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Right(page(1, 1000, totalCount = 3000))
        every { port.fetchPlaygrounds(2, 1000) } returns Either.Left(failure)
        every { repository.upsertAll(any()) } answers { firstArg<List<PlaygroundData>>().size }

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        result shouldBe Either.Left(failure)
        verify(exactly = 0) { port.fetchPlaygrounds(3, any()) }
        // 실패 이전 페이지는 이미 커밋되어 있다 (부분 성공 유지)
        verify(exactly = 1) { repository.upsertAll(any()) }
    }

    test("should return the very first failure when page 1 already fails") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        val failure = DomainError.ApiCallError(200, "99", "SERVICE_ERROR")
        every { port.fetchPlaygrounds(1, 1000) } returns Either.Left(failure)

        val result = PlaygroundFullSyncUseCase(port, repository, props()).execute()

        result shouldBe Either.Left(failure)
        verify(exactly = 0) { repository.upsertAll(any()) }
    }

    // ── 서비스 키 방어 ────────────────────────────────────────────────────────

    test("should return Unauthorized without calling the API when serviceKey is empty") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()

        val result = PlaygroundFullSyncUseCase(port, repository, props(serviceKey = "")).execute()

        result shouldBe Either.Left(DomainError.Unauthorized)
        verify(exactly = 0) { port.fetchPlaygrounds(any(), any()) }
    }

    test("should return Unauthorized when serviceKey is whitespace only") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()

        val result = PlaygroundFullSyncUseCase(port, repository, props(serviceKey = "   ")).execute()

        result shouldBe Either.Left(DomainError.Unauthorized)
        verify(exactly = 0) { port.fetchPlaygrounds(any(), any()) }
    }

    // ── 집계 ─────────────────────────────────────────────────────────────────

    test("should report total as received rows and upserted as rows actually changed") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 10) } returns Either.Right(page(1, 10, totalCount = 20))
        every { port.fetchPlaygrounds(2, 10) } returns Either.Right(page(2, 10, totalCount = 20))
        // 변경 감지 가드로 실제 변경은 3건뿐인 상황
        every { repository.upsertAll(any()) } returnsMany listOf(3, 0)

        val result = (PlaygroundFullSyncUseCase(port, repository, props(pageSize = 10)).execute() as Either.Right).value

        result.total shouldBe 20
        result.upserted shouldBe 3
        result.closed shouldBe 0
    }

    test("should pass the configured pageSize to the port as numOfRows") {
        val port = mockk<SafemapApiPort>()
        val repository = mockk<PlaygroundRepository>()
        every { port.fetchPlaygrounds(1, 250) } returns Either.Right(page(1, 5, totalCount = 5))
        every { repository.upsertAll(any()) } returns 5

        PlaygroundFullSyncUseCase(port, repository, props(pageSize = 250)).execute()

        verify(exactly = 1) { port.fetchPlaygrounds(1, 250) }
    }
})

private fun page(pageNo: Int, itemCount: Int, totalCount: Int) = PlaygroundPage(
    items = (1..itemCount).map { playgroundData("${pageNo}_$it") },
    pageNo = pageNo,
    numOfRows = itemCount,
    totalCount = totalCount,
)

private fun playgroundData(id: String) = PlaygroundData(
    facilityId = id,
    facilitySerialNo = null,
    sidoCode = null,
    sigunguCode = null,
    emdCode = null,
    name = "테스트 놀이터 $id",
    address = null,
    coordX = null,
    coordY = null,
    installDate = null,
    facilityCode1 = null,
    facilityCode2 = null,
    installPlaceCode = null,
    ownershipCode = null,
    indoorOutdoorCode = null,
    operationCode = null,
    accidentYn = null,
    deletedYn = null,
)
