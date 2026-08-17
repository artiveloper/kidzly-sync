package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.application.model.SigunguCodeData
import kr.kidzly.sync.domain.entity.SigunguCode

interface SigunguCodeRepository {
    /** 변경 감지 가드 포함 UPSERT (code PK 기준). 반환값 = 실제로 INSERT/UPDATE된 행 수 */
    fun upsertAll(codes: List<SigunguCodeData>): Int

    fun findById(code: String): SigunguCode?
}
