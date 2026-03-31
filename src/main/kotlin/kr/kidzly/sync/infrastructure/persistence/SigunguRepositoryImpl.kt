package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.application.model.SigunguInfo
import kr.kidzly.sync.domain.repository.SigunguRepository
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDateTime

@Repository
class SigunguRepositoryImpl(
    private val jdbcTemplate: NamedParameterJdbcTemplate,
) : SigunguRepository {

    @Transactional
    override fun upsertAll(sigungus: List<SigunguInfo>): Int {
        if (sigungus.isEmpty()) return 0
        val batchParams = sigungus.map { it.toSqlParams() }.toTypedArray()
        return jdbcTemplate.batchUpdate(UPSERT_SQL, batchParams).sum()
    }

    private fun SigunguInfo.toSqlParams() =
        MapSqlParameterSource()
            .addValue("arcode", arcode)
            .addValue("sidoname", sidoname)
            .addValue("sigunname", sigunname)
            .addValue("syncedAt", LocalDateTime.now())

    companion object {
        private val UPSERT_SQL = """
            INSERT INTO sigungus (arcode, sidoname, sigunname, synced_at)
            VALUES (:arcode, :sidoname, :sigunname, :syncedAt)
            ON CONFLICT (arcode) DO UPDATE SET
                sidoname  = EXCLUDED.sidoname,
                sigunname = EXCLUDED.sigunname,
                synced_at = EXCLUDED.synced_at
        """.trimIndent()
    }
}
