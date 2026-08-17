package kr.kidzly.sync.application.usecase

import arrow.core.Either
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.collections.shouldContainExactly
import io.kotest.matchers.shouldBe
import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import io.mockk.verify
import kr.kidzly.sync.application.model.LegalDongCodePage
import kr.kidzly.sync.application.model.LegalDongCodeRecord
import kr.kidzly.sync.application.model.SigunguCodeData
import kr.kidzly.sync.application.model.SyncResult
import kr.kidzly.sync.application.port.LegalDongCodeApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.domain.model.SigunguCodeLevel
import kr.kidzly.sync.domain.repository.SigunguCodeRepository
import kr.kidzly.sync.infrastructure.config.LegalDongCodeApiProperties

/**
 * [SigunguCodeSyncUseCase] 필터 파이프라인 / 페이지네이션 / fail-fast 단위 테스트.
 *
 * `requestIntervalMs = 0`으로 두어 Thread.sleep 대기 없이 실행된다.
 */
class SigunguCodeSyncUseCaseTest : FunSpec({

    fun props(serviceKey: String = "TEST_KEY", perPage: Int = 1000) = LegalDongCodeApiProperties(
        baseUrl = "https://api.odcloud.kr",
        serviceKey = serviceKey,
        perPage = perPage,
        requestIntervalMs = 0L,
    )

    fun useCase(
        port: LegalDongCodeApiPort,
        repository: SigunguCodeRepository,
        props: LegalDongCodeApiProperties = props(),
    ) = SigunguCodeSyncUseCase(port, repository, props)

    /** upsertAll 이 받은 배치를 그대로 세어 돌려주는 기본 스텁 */
    fun SigunguCodeRepository.countingUpsert() {
        every { upsertAll(any()) } answers { firstArg<List<SigunguCodeData>>().size }
    }

    // ── 서비스 키 방어 ────────────────────────────────────────────────────────

    test("should return Unauthorized without calling the API when serviceKey is empty") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()

        val result = useCase(port, repository, props(serviceKey = "")).execute()

        result shouldBe Either.Left(DomainError.Unauthorized)
        verify(exactly = 0) { port.fetchLegalDongCodes(any(), any()) }
        verify(exactly = 0) { repository.upsertAll(any()) }
    }

    test("should return Unauthorized when serviceKey is whitespace only") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()

        val result = useCase(port, repository, props(serviceKey = "   ")).execute()

        result shouldBe Either.Left(DomainError.Unauthorized)
        verify(exactly = 0) { port.fetchLegalDongCodes(any(), any()) }
    }

    // ── 페이지네이션 종료 조건 ─────────────────────────────────────────────────

    test("should call the API exactly 3 times when totalCount=2500 and perPage=1000") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 1000, totalCount = 2500))
        every { port.fetchLegalDongCodes(2, 1000) } returns Either.Right(emdPage(2, 1000, totalCount = 2500))
        every { port.fetchLegalDongCodes(3, 1000) } returns Either.Right(emdPage(3, 500, totalCount = 2500))
        repository.countingUpsert()

        val result = useCase(port, repository).execute()

        result shouldBe Either.Right(SyncResult(total = 2500, upserted = 2500))
        verify(exactly = 1) { port.fetchLegalDongCodes(1, 1000) }
        verify(exactly = 1) { port.fetchLegalDongCodes(2, 1000) }
        verify(exactly = 1) { port.fetchLegalDongCodes(3, 1000) }
        verify(exactly = 0) { port.fetchLegalDongCodes(4, any()) }
    }

    test("should stop after the first page when totalCount fits into a single page") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 30, totalCount = 30))
        repository.countingUpsert()

        val result = useCase(port, repository).execute()

        (result as Either.Right).value.total shouldBe 30
        verify(exactly = 1) { port.fetchLegalDongCodes(any(), any()) }
    }

    test("should fix the page count from the first response and ignore a later totalCount change") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 1000, totalCount = 2000))
        // 순회 도중 원본 totalCount가 늘어도 첫 페이지 기준(2페이지)에서 종료한다
        every { port.fetchLegalDongCodes(2, 1000) } returns Either.Right(emdPage(2, 1000, totalCount = 9000))
        repository.countingUpsert()

        useCase(port, repository).execute()

        verify(exactly = 0) { port.fetchLegalDongCodes(3, any()) }
    }

    test("should stop as soon as a page returns an empty item list") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        // totalCount가 비정상적으로 커도 빈 페이지에서 반드시 멈춘다 (무한 루프 방지)
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 1000, totalCount = 999_999))
        every { port.fetchLegalDongCodes(2, 1000) } returns Either.Right(emdPage(2, 0, totalCount = 999_999))
        repository.countingUpsert()

        val result = useCase(port, repository).execute()

        (result as Either.Right).value.total shouldBe 1000
        verify(exactly = 0) { port.fetchLegalDongCodes(3, any()) }
        verify(exactly = 1) { repository.upsertAll(any()) }
    }

    test("should return an empty result and never touch the repository when the first page is empty") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 0, totalCount = 0))

        val result = useCase(port, repository).execute()

        result shouldBe Either.Right(SyncResult(total = 0, upserted = 0))
        verify(exactly = 0) { repository.upsertAll(any()) }
    }

    test("should pass the configured perPage to the port") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 250) } returns Either.Right(emdPage(1, 5, totalCount = 5))
        repository.countingUpsert()

        useCase(port, repository, props(perPage = 250)).execute()

        verify(exactly = 1) { port.fetchLegalDongCodes(1, 250) }
    }

    // ── fail-fast ────────────────────────────────────────────────────────────

    test("should fail fast and skip the remaining pages when page 2 returns Left") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        val failure = DomainError.NetworkError("connect timed out")
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 1000, totalCount = 3000))
        every { port.fetchLegalDongCodes(2, 1000) } returns Either.Left(failure)
        repository.countingUpsert()

        val result = useCase(port, repository).execute()

        result shouldBe Either.Left(failure)
        verify(exactly = 0) { port.fetchLegalDongCodes(3, any()) }
        // 실패 이전 페이지는 이미 커밋되어 있다 (페이지 단위 트랜잭션, 부분 성공 유지)
        verify(exactly = 1) { repository.upsertAll(any()) }
    }

    test("should return the very first failure when page 1 already fails") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        val failure = DomainError.ParseError("data 필드 없음 (page=1)")
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Left(failure)

        val result = useCase(port, repository).execute()

        result shouldBe Either.Left(failure)
        verify(exactly = 0) { repository.upsertAll(any()) }
    }

    // ── 폐지여부 필터 ─────────────────────────────────────────────────────────

    test("should keep only the records whose 폐지여부 is 존재") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("1111010100", "서울특별시 종로구 청운동", "존재"),
                record("1111010200", "서울특별시 종로구 신교동", "폐지"),
                record("1111010300", "서울특별시 종로구 궁정동", null),
                record("1111010400", "서울특별시 종로구 효자동", ""),
                totalCount = 4,
            ),
        )
        val batch = slot<List<SigunguCodeData>>()
        every { repository.upsertAll(capture(batch)) } answers { batch.captured.size }

        val result = useCase(port, repository).execute()

        batch.captured.map { it.code } shouldContainExactly listOf("1111010100")
        (result as Either.Right).value.total shouldBe 1
    }

    test("should absorb whitespace around 존재 so a padded value is not dropped") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(record("1111010100", "청운동", " 존재 "), totalCount = 1),
        )
        val batch = slot<List<SigunguCodeData>>()
        every { repository.upsertAll(capture(batch)) } answers { batch.captured.size }

        useCase(port, repository).execute()

        batch.captured.map { it.code } shouldContainExactly listOf("1111010100")
    }

    // ── 리(里) 레벨 / 형식 불량 제외 ───────────────────────────────────────────

    test("should exclude ri level and malformed codes while keeping SIDO SIGUNGU EMD") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("1100000000", "서울특별시", "존재"),
                record("1111000000", "서울특별시 종로구", "존재"),
                record("1111010100", "서울특별시 종로구 청운동", "존재"),
                record("4173025321", "경기도 이천시 부발읍 아미리", "존재"), // 리 레벨
                record("411730253", "자릿수 불량", "존재"),
                record("11110101AB", "숫자 아님", "존재"),
                record("0000000000", "제로 코드", "존재"),
                totalCount = 7,
            ),
        )
        val batch = slot<List<SigunguCodeData>>()
        every { repository.upsertAll(capture(batch)) } answers { batch.captured.size }

        val result = useCase(port, repository).execute()

        batch.captured.map { it.code } shouldContainExactly
            listOf("1100000000", "1111000000", "1111010100")
        (result as Either.Right).value.total shouldBe 3
    }

    // ── 도메인 변환 ───────────────────────────────────────────────────────────

    test("should map each level onto the right sido sigungu emd columns") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("4100000000", "경기도", "존재"),
                record("4173000000", "경기도 이천시", "존재"),
                record("4173025300", "경기도 이천시 부발읍", "존재"),
                totalCount = 3,
            ),
        )
        val batch = slot<List<SigunguCodeData>>()
        every { repository.upsertAll(capture(batch)) } answers { batch.captured.size }

        useCase(port, repository).execute()

        batch.captured[0] shouldBe SigunguCodeData(
            code = "4100000000",
            level = SigunguCodeLevel.SIDO,
            sidoCode = "41",
            sigunguCode = null,
            emdCode = null,
            name = "경기도",
        )
        batch.captured[1] shouldBe SigunguCodeData(
            code = "4173000000",
            level = SigunguCodeLevel.SIGUNGU,
            sidoCode = "41",
            sigunguCode = "41730",
            emdCode = null,
            name = "경기도 이천시",
        )
        batch.captured[2] shouldBe SigunguCodeData(
            code = "4173025300",
            level = SigunguCodeLevel.EMD,
            sidoCode = "41",
            sigunguCode = "41730",
            emdCode = "41730253",
            name = "경기도 이천시 부발읍",
        )
    }

    test("should trim the name but never split it on whitespace") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(record("1111010100", "  서울특별시 종로구 청운동  ", "존재"), totalCount = 1),
        )
        val batch = slot<List<SigunguCodeData>>()
        every { repository.upsertAll(capture(batch)) } answers { batch.captured.size }

        useCase(port, repository).execute()

        batch.captured[0].name shouldBe "서울특별시 종로구 청운동"
    }

    // ── 집계 (SyncResult 의미) ────────────────────────────────────────────────

    test("should report total as the rows that survived the filters, not the rows received") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("1111010100", "청운동", "존재"),
                record("1111010101", "청운1리", "존재"), // 리 레벨 — 수신했지만 저장 대상 아님
                record("1111010200", "신교동", "폐지"), // 폐지 — 수신했지만 저장 대상 아님
                totalCount = 3,
            ),
        )
        every { repository.upsertAll(any()) } answers { firstArg<List<SigunguCodeData>>().size }

        val result = (useCase(port, repository).execute() as Either.Right).value

        // 수신 3건이지만 total 은 필터 통과 1건이어야 한다 (설계 §2.3)
        result.total shouldBe 1
        result.upserted shouldBe 1
        result.closed shouldBe 0
    }

    test("should report upserted as the rows the change detection guard actually wrote") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 10) } returns Either.Right(emdPage(1, 10, totalCount = 20))
        every { port.fetchLegalDongCodes(2, 10) } returns Either.Right(emdPage(2, 10, totalCount = 20))
        // 변경 감지 가드로 실제 변경은 3건뿐인 상황
        every { repository.upsertAll(any()) } returnsMany listOf(3, 0)

        val result = (useCase(port, repository, props(perPage = 10)).execute() as Either.Right).value

        result.total shouldBe 20
        result.upserted shouldBe 3
    }

    // ── 전량 탈락 방어 (리뷰 이슈 M-2) ────────────────────────────────────────

    test("should fail with ParseError when rows were received but every one of them was filtered out") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(record("1111010101", "청운1리", "존재"), totalCount = 1),
        )
        every { repository.upsertAll(any()) } returns 0

        val result = useCase(port, repository).execute()

        // 성공으로 보고하면 테이블이 낡은 채 방치되어도 아무도 알아채지 못한다
        val error = (result as Either.Left).value
        (error is DomainError.ParseError) shouldBe true
        (error as DomainError.ParseError).message.contains("저장 대상 0건") shouldBe true
    }

    test("should fail when the 폐지여부 field disappears from the response schema") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        // 데이터셋 판이 바뀌어 폐지여부가 전부 null 이 되면 allowlist 필터가 전 건을 떨군다
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("1100000000", "서울특별시", null),
                record("1111000000", "서울특별시 종로구", null),
                record("1111010100", "서울특별시 종로구 청운동", null),
                totalCount = 3,
            ),
        )
        every { repository.upsertAll(any()) } returns 0

        val result = useCase(port, repository).execute()

        ((result as Either.Left).value is DomainError.ParseError) shouldBe true
    }

    test("should NOT fail when the dataset itself is legitimately empty") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        // 수신 0건이면 필터 탓이 아니므로 가드가 발동하면 안 된다
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(emdPage(1, 0, totalCount = 0))

        val result = useCase(port, repository).execute()

        result shouldBe Either.Right(SyncResult(total = 0, upserted = 0))
    }

    test("should NOT fail when at least one record survives the filters") {
        val port = mockk<LegalDongCodeApiPort>()
        val repository = mockk<SigunguCodeRepository>()
        every { port.fetchLegalDongCodes(1, 1000) } returns Either.Right(
            pageOf(
                record("1111010100", "청운동", "존재"),
                record("1111010101", "청운1리", "존재"),
                totalCount = 2,
            ),
        )
        every { repository.upsertAll(any()) } answers { firstArg<List<SigunguCodeData>>().size }

        useCase(port, repository).execute() shouldBe Either.Right(SyncResult(total = 1, upserted = 1))
    }
})

// ── 픽스처 ────────────────────────────────────────────────────────────────────

/** 전부 EMD 레벨·"존재"인 정상 페이지 (필터가 아니라 순회를 검증할 때 사용) */
private fun emdPage(page: Int, itemCount: Int, totalCount: Int) = LegalDongCodePage(
    items = (1..itemCount).map { idx ->
        // 1111 + 6자리, 뒤 2자리는 항상 00 → EMD 레벨
        record("1111%04d00".format(page * 1000 + idx), "테스트동 ${page}_$idx", "존재")
    },
    page = page,
    perPage = itemCount,
    totalCount = totalCount,
)

private fun pageOf(vararg items: LegalDongCodeRecord, totalCount: Int) = LegalDongCodePage(
    items = items.toList(),
    page = 1,
    perPage = items.size,
    totalCount = totalCount,
)

private fun record(code: String, name: String, abolishedYn: String?) =
    LegalDongCodeRecord(code = code, name = name, abolishedYn = abolishedYn)
