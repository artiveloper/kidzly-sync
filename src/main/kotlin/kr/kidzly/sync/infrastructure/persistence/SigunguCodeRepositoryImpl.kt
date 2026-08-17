package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.application.model.SigunguCodeData
import kr.kidzly.sync.common.nowKst
import kr.kidzly.sync.domain.entity.SigunguCode
import kr.kidzly.sync.domain.repository.SigunguCodeRepository
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional

@Repository
class SigunguCodeRepositoryImpl(
    private val jdbcTemplate: NamedParameterJdbcTemplate,
    private val jpaSigunguCodeRepository: JpaSigunguCodeRepository,
) : SigunguCodeRepository {

    @Transactional
    override fun upsertAll(codes: List<SigunguCodeData>): Int {
        if (codes.isEmpty()) return 0
        val batchParams = codes.map { it.toSqlParams() }.toTypedArray()
        return jdbcTemplate.batchUpdate(UPSERT_SQL, batchParams).sum()
    }

    @Transactional(readOnly = true)
    override fun findById(code: String): SigunguCode? =
        jpaSigunguCodeRepository.findById(code).orElse(null)

    private fun SigunguCodeData.toSqlParams() =
        MapSqlParameterSource()
            .addValue("code", code)
            // JDBC는 enum을 모르므로 name(String)으로 바인딩한다
            .addValue("level", level.name)
            .addValue("sidoCode", sidoCode)
            .addValue("sigunguCode", sigunguCode)
            .addValue("emdCode", emdCode)
            .addValue("name", name)
            .addValue("syncedAt", nowKst())

    companion object {
        private val UPSERT_SQL = """
            INSERT INTO sigungu_codes (
                code, level, sido_code, sigungu_code, emd_code, name, synced_at
            ) VALUES (
                :code, :level, :sidoCode, :sigunguCode, :emdCode, :name, :syncedAt
            )
            ON CONFLICT (code) DO UPDATE SET
                level = EXCLUDED.level,
                sido_code = EXCLUDED.sido_code,
                sigungu_code = EXCLUDED.sigungu_code,
                emd_code = EXCLUDED.emd_code,
                name = EXCLUDED.name,
                synced_at = EXCLUDED.synced_at
            WHERE (
                sigungu_codes.level, sigungu_codes.sido_code, sigungu_codes.sigungu_code,
                sigungu_codes.emd_code, sigungu_codes.name
            ) IS DISTINCT FROM (
                EXCLUDED.level, EXCLUDED.sido_code, EXCLUDED.sigungu_code,
                EXCLUDED.emd_code, EXCLUDED.name
            )
        """.trimIndent()
    }
}
