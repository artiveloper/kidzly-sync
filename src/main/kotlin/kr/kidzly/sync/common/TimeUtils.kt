package kr.kidzly.sync.common

import java.time.LocalDateTime
import java.time.ZoneId

private val KST = ZoneId.of("Asia/Seoul")

fun nowKst(): LocalDateTime = LocalDateTime.now(KST)
