package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDateTime

@Repository
class DaycareRepositoryImpl(
    private val jdbcTemplate: NamedParameterJdbcTemplate,
    private val jpaDaycareRepository: JpaDaycareRepository,
) : DaycareRepository {

    @Transactional
    override fun upsertAll(daycares: List<DaycareData>): Int {
        if (daycares.isEmpty()) return 0
        val batchParams = daycares.map { it.toSqlParams() }.toTypedArray()
        return jdbcTemplate.batchUpdate(UPSERT_SQL, batchParams).sum()
    }

    @Transactional
    override fun markAsClosed(stcode: String, crstdate: String?): Int =
        jpaDaycareRepository.markAsClosed(stcode, crstdate)

    private fun DaycareData.toSqlParams() =
        MapSqlParameterSource()
            .addValue("stcode", stcode)
            .addValue("arcode", arcode)
            .addValue("sidoname", sidoname)
            .addValue("sigunguname", sigunguname)
            .addValue("crname", crname)
            .addValue("crtypename", crtypename)
            .addValue("crstatusname", crstatusname)
            .addValue("zipcode", zipcode)
            .addValue("craddr", craddr)
            .addValue("crtelno", crtelno)
            .addValue("crfaxno", crfaxno)
            .addValue("crhome", crhome)
            .addValue("la", la)
            .addValue("lo", lo)
            .addValue("crcapat", crcapat)
            .addValue("crchcnt", crchcnt)
            .addValue("nrtrroomcnt", nrtrroomcnt)
            .addValue("nrtrroomsize", nrtrroomsize)
            .addValue("plgrdco", plgrdco)
            .addValue("cctvinstlcnt", cctvinstlcnt)
            .addValue("chcrtescnt", chcrtescnt)
            .addValue("classCntTot", classCntTot)
            .addValue("childCntTot", childCntTot)
            .addValue("emCntTot", emCntTot)
            .addValue("ewCntTot", ewCntTot)
            .addValue("crrepname", crrepname)
            .addValue("crcnfmdt", crcnfmdt)
            .addValue("crstdate", crstdate)
            .addValue("syncedAt", LocalDateTime.now())

    companion object {
        private val UPSERT_SQL = """
            INSERT INTO daycares (
                stcode, arcode, sidoname, sigunguname, crname, crtypename, crstatusname,
                zipcode, craddr, crtelno, crfaxno, crhome, la, lo,
                crcapat, crchcnt, nrtrroomcnt, nrtrroomsize, plgrdco, cctvinstlcnt, chcrtescnt,
                class_cnt_tot, child_cnt_tot, em_cnt_tot, ew_cnt_tot,
                crrepname, crcnfmdt, crstdate, synced_at
            ) VALUES (
                :stcode, :arcode, :sidoname, :sigunguname, :crname, :crtypename, :crstatusname,
                :zipcode, :craddr, :crtelno, :crfaxno, :crhome, :la, :lo,
                :crcapat, :crchcnt, :nrtrroomcnt, :nrtrroomsize, :plgrdco, :cctvinstlcnt, :chcrtescnt,
                :classCntTot, :childCntTot, :emCntTot, :ewCntTot,
                :crrepname, :crcnfmdt, :crstdate, :syncedAt
            )
            ON CONFLICT (stcode) DO UPDATE SET
                arcode = EXCLUDED.arcode,
                sidoname = EXCLUDED.sidoname,
                sigunguname = EXCLUDED.sigunguname,
                crname = EXCLUDED.crname,
                crtypename = EXCLUDED.crtypename,
                crstatusname = EXCLUDED.crstatusname,
                zipcode = EXCLUDED.zipcode,
                craddr = EXCLUDED.craddr,
                crtelno = EXCLUDED.crtelno,
                crfaxno = EXCLUDED.crfaxno,
                crhome = EXCLUDED.crhome,
                la = EXCLUDED.la,
                lo = EXCLUDED.lo,
                crcapat = EXCLUDED.crcapat,
                crchcnt = EXCLUDED.crchcnt,
                nrtrroomcnt = EXCLUDED.nrtrroomcnt,
                nrtrroomsize = EXCLUDED.nrtrroomsize,
                plgrdco = EXCLUDED.plgrdco,
                cctvinstlcnt = EXCLUDED.cctvinstlcnt,
                chcrtescnt = EXCLUDED.chcrtescnt,
                class_cnt_tot = EXCLUDED.class_cnt_tot,
                child_cnt_tot = EXCLUDED.child_cnt_tot,
                em_cnt_tot = EXCLUDED.em_cnt_tot,
                ew_cnt_tot = EXCLUDED.ew_cnt_tot,
                crrepname = EXCLUDED.crrepname,
                crcnfmdt = EXCLUDED.crcnfmdt,
                crstdate = EXCLUDED.crstdate,
                synced_at = EXCLUDED.synced_at
        """.trimIndent()
    }
}
