package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.application.model.PlaygroundData
import kr.kidzly.sync.domain.entity.Playground

interface PlaygroundRepository {
    /** 변경 감지 가드 포함 UPSERT. 반환값 = 실제로 INSERT/UPDATE된 행 수 */
    fun upsertAll(playgrounds: List<PlaygroundData>): Int

    fun findById(facilityId: String): Playground?
}
