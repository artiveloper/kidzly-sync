package kr.kidzly.sync.infrastructure.persistence

import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.mockk.mockk
import kr.kidzly.sync.application.model.SigunguCodeData
import kr.kidzly.sync.domain.model.SigunguCodeLevel
import org.flywaydb.core.Flyway
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.jdbc.datasource.DriverManagerDataSource
import org.testcontainers.DockerClientFactory
import org.testcontainers.containers.PostgreSQLContainer
import org.testcontainers.utility.DockerImageName
import java.time.LocalDateTime

/**
 * [SigunguCodeRepositoryImpl] UPSERT + 변경 감지 가드 통합 테스트 (Testcontainers + PostgreSQL).
 *
 * `ON CONFLICT (code)` / `IS DISTINCT FROM` / enum→VARCHAR 바인딩은 실제 PostgreSQL 없이는
 * 검증할 수 없어 이 부분만 통합 테스트로 다룬다. Spring 컨텍스트는 띄우지 않는다 (환경변수 의존 회피).
 *
 * Docker를 사용할 수 없는 환경에서는 모든 케이스가 스킵된다.
 */
class SigunguCodeRepositoryImplIntegrationTest : FunSpec({

    val dockerAvailable = runCatching { DockerClientFactory.instance().isDockerAvailable }
        .onFailure { System.err.println("[SigunguCodeRepositoryImplIntegrationTest] Docker 사용 불가 — 스킵: $it") }
        .getOrDefault(false)
    lateinit var jdbc: NamedParameterJdbcTemplate
    lateinit var repository: SigunguCodeRepositoryImpl

    beforeSpec {
        if (!dockerAvailable) return@beforeSpec
        postgres.start()
        Flyway.configure()
            .dataSource(postgres.jdbcUrl, postgres.username, postgres.password)
            .locations("classpath:db/migration")
            .load()
            .migrate()
        val dataSource = DriverManagerDataSource(postgres.jdbcUrl, postgres.username, postgres.password)
            .apply { setDriverClassName("org.postgresql.Driver") }
        jdbc = NamedParameterJdbcTemplate(dataSource)
        repository = SigunguCodeRepositoryImpl(jdbc, mockk<JpaSigunguCodeRepository>(relaxed = true))
    }

    afterSpec {
        if (dockerAvailable) postgres.stop()
    }

    beforeTest {
        if (dockerAvailable) jdbc.update("DELETE FROM sigungu_codes", MapSqlParameterSource())
    }

    fun <T> columnOf(code: String, column: String, type: Class<T>): T? =
        jdbc.queryForObject(
            "SELECT $column FROM sigungu_codes WHERE code = :code",
            MapSqlParameterSource("code", code),
            type,
        )

    fun stringOf(code: String, column: String): String? = columnOf(code, column, String::class.java)

    fun syncedAtOf(code: String): LocalDateTime? = columnOf(code, "synced_at", LocalDateTime::class.java)

    fun rowCount(): Int =
        jdbc.queryForObject(
            "SELECT COUNT(*) FROM sigungu_codes",
            MapSqlParameterSource(),
            Int::class.javaObjectType,
        ) ?: -1

    // ── code PK 기준 UPSERT ───────────────────────────────────────────────────

    test("should insert a new row keyed by the 10 digit code").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1

        rowCount() shouldBe 1
        stringOf("1111010100", "name") shouldBe "서울특별시 종로구 청운동"
    }

    test("should update in place instead of inserting a duplicate when the same code returns")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1

            repository.upsertAll(listOf(emd("1111010100").copy(name = "서울특별시 종로구 청운효자동"))) shouldBe 1

            rowCount() shouldBe 1
            stringOf("1111010100", "name") shouldBe "서울특별시 종로구 청운효자동"
        }

    test("should keep different codes as separate rows").config(enabled = dockerAvailable) {
        repository.upsertAll(
            listOf(sido("1100000000"), sigungu("1111000000"), emd("1111010100")),
        ) shouldBe 3

        rowCount() shouldBe 3
    }

    test("should let the later row win when the same code appears twice in one batch")
        .config(enabled = dockerAvailable) {
            // batchUpdate는 행마다 독립 statement를 실행하므로 ON CONFLICT가 정상 동작한다
            val changed = repository.upsertAll(
                listOf(emd("1111010100"), emd("1111010100").copy(name = "나중 값이 이긴다")),
            )

            changed shouldBe 2
            rowCount() shouldBe 1
            stringOf("1111010100", "name") shouldBe "나중 값이 이긴다"
        }

    // ── 변경 감지 가드 ────────────────────────────────────────────────────────

    test("should report 0 and keep synced_at when the same data is upserted again")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1
            val firstSyncedAt = syncedAtOf("1111010100")

            // 법정동코드는 거의 불변이라 주 1회 실행이 대부분 no-op 이어야 한다
            repository.upsertAll(listOf(emd("1111010100"))) shouldBe 0
            syncedAtOf("1111010100") shouldBe firstSyncedAt
        }

    test("should report 1 and refresh synced_at when the name changes").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1
        val firstSyncedAt = syncedAtOf("1111010100")

        repository.upsertAll(listOf(emd("1111010100").copy(name = "개편된 동명"))) shouldBe 1

        syncedAtOf("1111010100") shouldNotBe firstSyncedAt
    }

    test("should treat a level change as a change").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1

        val promoted = emd("1111010100").copy(level = SigunguCodeLevel.SIGUNGU, emdCode = null)
        repository.upsertAll(listOf(promoted)) shouldBe 1
        stringOf("1111010100", "level") shouldBe "SIGUNGU"
    }

    test("should treat null <-> value transitions on emd_code as a change").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sigungu("1111000000"))) shouldBe 1

        repository.upsertAll(listOf(sigungu("1111000000").copy(emdCode = "11110101"))) shouldBe 1
        repository.upsertAll(listOf(sigungu("1111000000"))) shouldBe 1
    }

    test("should count only the rows that actually changed inside a batch").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("1111010100"), emd("1111010200"), emd("1111010300"))) shouldBe 3

        val changed = repository.upsertAll(
            listOf(
                emd("1111010100"),
                emd("1111010200").copy(name = "신교동 개편"),
                emd("1111010300"),
            ),
        )

        changed shouldBe 1
    }

    test("should return 0 without touching the database for an empty list").config(enabled = dockerAvailable) {
        repository.upsertAll(emptyList()) shouldBe 0

        rowCount() shouldBe 0
    }

    // ── 컬럼 매핑 ─────────────────────────────────────────────────────────────

    test("should bind the level enum as its name so PostgreSQL accepts the VARCHAR column")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(sido("1100000000"), sigungu("1111000000"), emd("1111010100")))

            stringOf("1100000000", "level") shouldBe "SIDO"
            stringOf("1111000000", "level") shouldBe "SIGUNGU"
            stringOf("1111010100", "level") shouldBe "EMD"
        }

    test("should store NULL for sigungu_code and emd_code at SIDO level").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sido("1100000000"))) shouldBe 1

        stringOf("1100000000", "sido_code") shouldBe "11"
        stringOf("1100000000", "sigungu_code") shouldBe null
        stringOf("1100000000", "emd_code") shouldBe null
    }

    test("should store NULL for emd_code at SIGUNGU level").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sigungu("1111000000"))) shouldBe 1

        stringOf("1111000000", "sigungu_code") shouldBe "11110"
        stringOf("1111000000", "emd_code") shouldBe null
    }

    test("should store every derived code at EMD level").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("1111010100"))) shouldBe 1

        stringOf("1111010100", "code") shouldBe "1111010100"
        stringOf("1111010100", "sido_code") shouldBe "11"
        stringOf("1111010100", "sigungu_code") shouldBe "11110"
        stringOf("1111010100", "emd_code") shouldBe "11110101"
    }

    test("should persist Korean names without corruption").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(emd("5013025000").copy(name = "제주특별자치도 서귀포시 대정읍")))

        stringOf("5013025000", "name") shouldBe "제주특별자치도 서귀포시 대정읍"
    }

    test("should accept a 200 character name (column boundary)").config(enabled = dockerAvailable) {
        val longName = "가".repeat(200)

        repository.upsertAll(listOf(emd("1111010100").copy(name = longName))) shouldBe 1

        stringOf("1111010100", "name") shouldBe longName
    }
})

private val postgres = PostgreSQLContainer<Nothing>(DockerImageName.parse("postgres:16-alpine"))

private fun sido(code: String) = SigunguCodeData(
    code = code,
    level = SigunguCodeLevel.SIDO,
    sidoCode = code.substring(0, 2),
    sigunguCode = null,
    emdCode = null,
    name = "서울특별시",
)

private fun sigungu(code: String) = SigunguCodeData(
    code = code,
    level = SigunguCodeLevel.SIGUNGU,
    sidoCode = code.substring(0, 2),
    sigunguCode = code.substring(0, 5),
    emdCode = null,
    name = "서울특별시 종로구",
)

private fun emd(code: String) = SigunguCodeData(
    code = code,
    level = SigunguCodeLevel.EMD,
    sidoCode = code.substring(0, 2),
    sigunguCode = code.substring(0, 5),
    emdCode = code.substring(0, 8),
    name = "서울특별시 종로구 청운동",
)
