package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.SigunguCode
import org.springframework.data.jpa.repository.JpaRepository

interface JpaSigunguCodeRepository : JpaRepository<SigunguCode, String>
