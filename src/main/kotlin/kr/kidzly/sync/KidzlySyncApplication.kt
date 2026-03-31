package kr.kidzly.sync

import kr.kidzly.sync.infrastructure.config.ChildcareApiProperties
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.boot.runApplication
import org.springframework.retry.annotation.EnableRetry
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
@EnableRetry
@EnableConfigurationProperties(ChildcareApiProperties::class)
class KidzlySyncApplication

fun main(args: Array<String>) {
    runApplication<KidzlySyncApplication>(*args)
}
