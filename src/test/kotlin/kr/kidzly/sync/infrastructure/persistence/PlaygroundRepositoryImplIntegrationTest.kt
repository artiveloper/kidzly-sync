package kr.kidzly.sync.infrastructure.persistence

import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.mockk.mockk
import kr.kidzly.sync.application.model.PlaygroundData
import org.flywaydb.core.Flyway
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.jdbc.datasource.DriverManagerDataSource
import org.testcontainers.DockerClientFactory
import org.testcontainers.containers.PostgreSQLContainer
import org.testcontainers.utility.DockerImageName
import java.math.BigDecimal
import java.time.LocalDateTime

/**
 * [PlaygroundRepositoryImpl] UPSERT + 변경 감지 가드 통합 테스트 (Testcontainers + PostgreSQL).
 *
 * `IS DISTINCT FROM` 가드와 `NUMERIC(15,4)` 반올림 상호작용은 실제 PostgreSQL 없이는 검증할 수 없어
 * 이 부분만 통합 테스트로 다룬다. Spring 컨텍스트는 띄우지 않는다 (환경변수 의존 회피).
 *
 * Docker를 사용할 수 없는 환경에서는 모든 케이스가 스킵된다.
 */
class PlaygroundRepositoryImplIntegrationTest : FunSpec({

    val dockerAvailable = runCatching { DockerClientFactory.instance().isDockerAvailable }
        .onFailure { System.err.println("[PlaygroundRepositoryImplIntegrationTest] Docker 사용 불가 — 스킵: $it") }
        .getOrDefault(false)
    lateinit var jdbc: NamedParameterJdbcTemplate
    lateinit var repository: PlaygroundRepositoryImpl

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
        repository = PlaygroundRepositoryImpl(jdbc, mockk<JpaPlaygroundRepository>(relaxed = true))
    }

    afterSpec {
        if (dockerAvailable) postgres.stop()
    }

    beforeTest {
        if (dockerAvailable) jdbc.update("DELETE FROM playgrounds", MapSqlParameterSource())
    }

    fun syncedAtOf(facilityId: String): LocalDateTime? =
        jdbc.queryForObject(
            "SELECT synced_at FROM playgrounds WHERE facility_id = :id",
            MapSqlParameterSource("id", facilityId),
            LocalDateTime::class.java,
        )

    fun nameOf(facilityId: String): String? =
        jdbc.queryForObject(
            "SELECT name FROM playgrounds WHERE facility_id = :id",
            MapSqlParameterSource("id", facilityId),
            String::class.java,
        )

    test("should insert a new row and report 1 changed row").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sample("1741"))) shouldBe 1

        nameOf("1741") shouldBe "한마음정육식당 화성동탄능동점"
    }

    test("should report 0 and keep synced_at when the same data is upserted again")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(sample("1741"))) shouldBe 1
            val firstSyncedAt = syncedAtOf("1741")

            // 변경 감지 가드의 핵심 — 내용이 동일하면 디스크 IO가 발생하지 않아야 한다
            repository.upsertAll(listOf(sample("1741"))) shouldBe 0
            syncedAtOf("1741") shouldBe firstSyncedAt
        }

    test("should report 1 and refresh synced_at when a single field changes")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(sample("1741"))) shouldBe 1
            val firstSyncedAt = syncedAtOf("1741")

            repository.upsertAll(listOf(sample("1741").copy(operationCode = "B003"))) shouldBe 1

            nameOf("1741") shouldBe "한마음정육식당 화성동탄능동점"
            syncedAtOf("1741") shouldNotBe firstSyncedAt
        }

    test("should treat null <-> value transitions as a change").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sample("1741").copy(deletedYn = null))) shouldBe 1

        repository.upsertAll(listOf(sample("1741").copy(deletedYn = "Y"))) shouldBe 1
        repository.upsertAll(listOf(sample("1741").copy(deletedYn = null))) shouldBe 1
    }

    test("should not report a change when coordinates only differ beyond NUMERIC(15,4) precision")
        .config(enabled = dockerAvailable) {
            // coordY=4469799.53254 는 컬럼 정의상 4469799.5325 로 반올림 저장된다.
            // 이미 반올림된 값을 다시 넣어도 UPDATE로 오탐되면 안 된다 (BigDecimal 스케일 미고정 정책의 근거).
            repository.upsertAll(listOf(sample("1741"))) shouldBe 1

            val rounded = sample("1741").copy(coordY = BigDecimal("4469799.5325"))
            repository.upsertAll(listOf(rounded)) shouldBe 0
        }

    test("should count only the rows that actually changed inside a batch")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(listOf(sample("1"), sample("2"), sample("3"))) shouldBe 3

            val changed = repository.upsertAll(
                listOf(sample("1"), sample("2").copy(address = "서울 강동구 둔촌동"), sample("3")),
            )

            changed shouldBe 1
        }

    test("should return 0 without touching the database for an empty list")
        .config(enabled = dockerAvailable) {
            repository.upsertAll(emptyList()) shouldBe 0
        }

    test("should handle a duplicated facility_id inside the same batch (row-by-row statements)")
        .config(enabled = dockerAvailable) {
            // batchUpdate는 행마다 독립 statement를 실행하므로 ON CONFLICT가 정상 동작한다 (설계 §9-B)
            val changed = repository.upsertAll(
                listOf(sample("1741"), sample("1741").copy(name = "나중 값이 이긴다")),
            )

            changed shouldBe 2
            nameOf("1741") shouldBe "나중 값이 이긴다"
        }

    test("should persist Korean text without corruption").config(enabled = dockerAvailable) {
        repository.upsertAll(listOf(sample("1741")))

        jdbc.queryForObject(
            "SELECT address FROM playgrounds WHERE facility_id = :id",
            MapSqlParameterSource("id", "1741"),
            String::class.java,
        ) shouldBe "경기 화성시 동탄하나1길 68"
    }
})

private val postgres = PostgreSQLContainer<Nothing>(DockerImageName.parse("postgres:16-alpine"))

private fun sample(facilityId: String) = PlaygroundData(
    facilityId = facilityId,
    facilitySerialNo = "1002057",
    sidoCode = "41",
    sigunguCode = "41590",
    emdCode = "41590118",
    name = "한마음정육식당 화성동탄능동점",
    address = "경기 화성시 동탄하나1길 68",
    coordX = BigDecimal("14144087.4653"),
    coordY = BigDecimal("4469799.53254"),
    installDate = "20240521",
    facilityCode1 = "4159011800",
    facilityCode2 = null,
    installPlaceCode = "A004",
    ownershipCode = "C001",
    indoorOutdoorCode = "O001",
    operationCode = "B001",
    accidentYn = null,
    deletedYn = null,
)
