package kr.kidzly.sync.infrastructure.notification

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient

@Component
class TelegramNotifier(
    @Qualifier("telegramRestClient") private val restClient: RestClient,
    @Value("\${telegram.bot-token}") private val botToken: String,
    @Value("\${telegram.chat-id}") private val chatId: String,
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun sendMessage(text: String) {
        try {
            restClient.post()
                .uri("https://api.telegram.org/bot$botToken/sendMessage")
                .contentType(MediaType.APPLICATION_JSON)
                .body(
                    mapOf(
                        "chat_id" to chatId,
                        "text" to text,
                        "parse_mode" to "HTML",
                    ),
                )
                .retrieve()
                .toBodilessEntity()
        } catch (e: Exception) {
            // 알림 실패가 동기화 자체를 중단시키면 안 됨
            log.error("텔레그램 알림 전송 실패: ${e.message}", e)
        }
    }
}
