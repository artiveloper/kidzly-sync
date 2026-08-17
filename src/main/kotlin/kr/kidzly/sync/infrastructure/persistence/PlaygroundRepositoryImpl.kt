package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.application.model.PlaygroundData
import kr.kidzly.sync.common.nowKst
import kr.kidzly.sync.domain.entity.Playground
import kr.kidzly.sync.domain.repository.PlaygroundRepository
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional

@Repository
class PlaygroundRepositoryImpl(
    private val jdbcTemplate: NamedParameterJdbcTemplate,
    private val jpaPlaygroundRepository: JpaPlaygroundRepository,
) : PlaygroundRepository {

    @Transactional
    override fun upsertAll(playgrounds: List<PlaygroundData>): Int {
        if (playgrounds.isEmpty()) return 0
        val batchParams = playgrounds.map { it.toSqlParams() }.toTypedArray()
        return jdbcTemplate.batchUpdate(UPSERT_SQL, batchParams).sum()
    }

    @Transactional(readOnly = true)
    override fun findById(facilityId: String): Playground? =
        jpaPlaygroundRepository.findById(facilityId).orElse(null)

    private fun PlaygroundData.toSqlParams() =
        MapSqlParameterSource()
            .addValue("facilityId", facilityId)
            .addValue("facilitySerialNo", facilitySerialNo)
            .addValue("sidoCode", sidoCode)
            .addValue("sigunguCode", sigunguCode)
            .addValue("emdCode", emdCode)
            .addValue("name", name)
            .addValue("address", address)
            .addValue("coordX", coordX)
            .addValue("coordY", coordY)
            .addValue("installDate", installDate)
            .addValue("facilityCode1", facilityCode1)
            .addValue("facilityCode2", facilityCode2)
            .addValue("installPlaceCode", installPlaceCode)
            .addValue("ownershipCode", ownershipCode)
            .addValue("indoorOutdoorCode", indoorOutdoorCode)
            .addValue("operationCode", operationCode)
            .addValue("accidentYn", accidentYn)
            .addValue("deletedYn", deletedYn)
            .addValue("syncedAt", nowKst())

    companion object {
        private val UPSERT_SQL = """
            INSERT INTO playgrounds (
                facility_id, facility_serial_no, sido_code, sigungu_code, emd_code,
                name, address, coord_x, coord_y, install_date,
                facility_code1, facility_code2, install_place_code, ownership_code,
                indoor_outdoor_code, operation_code, accident_yn, deleted_yn,
                synced_at
            ) VALUES (
                :facilityId, :facilitySerialNo, :sidoCode, :sigunguCode, :emdCode,
                :name, :address, :coordX, :coordY, :installDate,
                :facilityCode1, :facilityCode2, :installPlaceCode, :ownershipCode,
                :indoorOutdoorCode, :operationCode, :accidentYn, :deletedYn,
                :syncedAt
            )
            ON CONFLICT (facility_id) DO UPDATE SET
                facility_serial_no = EXCLUDED.facility_serial_no,
                sido_code = EXCLUDED.sido_code,
                sigungu_code = EXCLUDED.sigungu_code,
                emd_code = EXCLUDED.emd_code,
                name = EXCLUDED.name,
                address = EXCLUDED.address,
                coord_x = EXCLUDED.coord_x,
                coord_y = EXCLUDED.coord_y,
                install_date = EXCLUDED.install_date,
                facility_code1 = EXCLUDED.facility_code1,
                facility_code2 = EXCLUDED.facility_code2,
                install_place_code = EXCLUDED.install_place_code,
                ownership_code = EXCLUDED.ownership_code,
                indoor_outdoor_code = EXCLUDED.indoor_outdoor_code,
                operation_code = EXCLUDED.operation_code,
                accident_yn = EXCLUDED.accident_yn,
                deleted_yn = EXCLUDED.deleted_yn,
                synced_at = EXCLUDED.synced_at
            WHERE (
                playgrounds.facility_serial_no, playgrounds.sido_code, playgrounds.sigungu_code,
                playgrounds.emd_code, playgrounds.name, playgrounds.address,
                playgrounds.coord_x, playgrounds.coord_y, playgrounds.install_date,
                playgrounds.facility_code1, playgrounds.facility_code2, playgrounds.install_place_code,
                playgrounds.ownership_code, playgrounds.indoor_outdoor_code, playgrounds.operation_code,
                playgrounds.accident_yn, playgrounds.deleted_yn
            ) IS DISTINCT FROM (
                EXCLUDED.facility_serial_no, EXCLUDED.sido_code, EXCLUDED.sigungu_code,
                EXCLUDED.emd_code, EXCLUDED.name, EXCLUDED.address,
                EXCLUDED.coord_x, EXCLUDED.coord_y, EXCLUDED.install_date,
                EXCLUDED.facility_code1, EXCLUDED.facility_code2, EXCLUDED.install_place_code,
                EXCLUDED.ownership_code, EXCLUDED.indoor_outdoor_code, EXCLUDED.operation_code,
                EXCLUDED.accident_yn, EXCLUDED.deleted_yn
            )
        """.trimIndent()
    }
}
