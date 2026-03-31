package kr.kidzly.sync.domain.repository

import kr.kidzly.sync.application.model.SigunguInfo

interface SigunguRepository {
    fun upsertAll(sigungus: List<SigunguInfo>): Int
}
