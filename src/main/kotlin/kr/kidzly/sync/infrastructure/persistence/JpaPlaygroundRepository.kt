package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.domain.entity.Playground
import org.springframework.data.jpa.repository.JpaRepository

interface JpaPlaygroundRepository : JpaRepository<Playground, String>
