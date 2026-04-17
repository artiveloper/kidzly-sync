package kr.kidzly.sync

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.runApplication
import org.springframework.retry.annotation.EnableRetry

@SpringBootApplication
@EnableRetry
@ConfigurationPropertiesScan
class KidzlySyncApplication

fun main(args: Array<String>) {
    runApplication<KidzlySyncApplication>(*args)
}
