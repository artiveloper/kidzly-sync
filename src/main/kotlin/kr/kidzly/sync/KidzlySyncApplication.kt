package kr.kidzly.sync

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.runApplication
import org.springframework.retry.annotation.EnableRetry
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
@EnableRetry
@ConfigurationPropertiesScan
class KidzlySyncApplication

fun main(args: Array<String>) {
    runApplication<KidzlySyncApplication>(*args)
}
