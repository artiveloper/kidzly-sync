package kr.kidzly.sync.infrastructure.api

import arrow.core.Either
import arrow.core.flatMap
import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.application.model.LegalDongCodePage
import kr.kidzly.sync.application.model.LegalDongCodeRecord
import kr.kidzly.sync.application.port.LegalDongCodeApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.infrastructure.api.dto.LegalDongCodeJsonItem
import kr.kidzly.sync.infrastructure.api.dto.LegalDongCodeJsonResponse
import kr.kidzly.sync.infrastructure.config.LegalDongCodeApiProperties
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.http.HttpStatus
import org.springframework.retry.annotation.Backoff
import org.springframework.retry.annotation.Retryable
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient
import org.springframework.web.client.RestClientException
import org.springframework.web.util.UriComponentsBuilder
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

/**
 * odcloud.kr 법정동코드 조회 클라이언트.
 *
 * safemap(IF_0007)과의 차이:
 * - 응답이 JSON이고 header/resultCode 래퍼가 없다 — 실패는 HTTP 상태로만 전달된다
 * - 폐지여부 필터와 레벨 판별은 여기서 하지 않는다 (UseCase 책임)
 */
@Component
class LegalDongCodeApiClient(
    @param:Qualifier("legalDongCodeRestClient") private val restClient: RestClient,
    private val objectMapper: ObjectMapper,
    private val props: LegalDongCodeApiProperties,
) : LegalDongCodeApiPort {

    private val log = LoggerFactory.getLogger(javaClass)

    override fun fetchLegalDongCodes(page: Int, perPage: Int): Either<DomainError, LegalDongCodePage> =
        callApi(page, perPage) { body ->
            objectMapper.readValue(body, LegalDongCodeJsonResponse::class.java)
        }.flatMap { response -> response.toLegalDongCodePage(page) }

    private fun LegalDongCodeJsonResponse.toLegalDongCodePage(
        requestedPage: Int,
    ): Either<DomainError, LegalDongCodePage> {
        // odcloud는 에러 바디에도 HTTP 200을 주는 판이 있어 data 누락을 방어한다
        val items = data
            ?: return Either.Left(DomainError.ParseError("data 필드 없음 (page=$requestedPage)"))

        return Either.Right(
            LegalDongCodePage(
                items = items.mapNotNull { it.toRecord() },
                page = page.takeIf { it > 0 } ?: requestedPage,
                perPage = perPage,
                totalCount = totalCount,
            ),
        )
    }

    /** 코드 또는 법정동명이 없는 아이템은 저장할 수 없으므로 제외한다. */
    private fun LegalDongCodeJsonItem.toRecord(): LegalDongCodeRecord? {
        val legalDongCode = code?.trim()?.takeIf { it.isNotBlank() }
            ?: run {
                log.warn("법정동코드 없음 — 아이템 제외 (법정동명=$name)")
                return null
            }
        val legalDongName = name?.trim()?.takeIf { it.isNotBlank() }
            ?: run {
                log.warn("법정동명 없음 — 아이템 제외 (법정동코드=$legalDongCode)")
                return null
            }
        return LegalDongCodeRecord(
            code = legalDongCode,
            name = legalDongName,
            abolishedYn = abolishedYn?.trim()?.takeIf { it.isNotBlank() },
        )
    }

    /**
     * serviceKey를 직접 percent-encode 한 뒤 **pre-encoded URI**(`build(true)`)로 넘긴다.
     *
     * `UriBuilder.queryParam()`에 맡기면 `=`는 `%3D`로 인코딩되지만 `+`는 query 합법 문자라
     * 그대로 전송되고, 서버가 query의 `+`를 공백으로 디코딩하면 `+`가 든 Decoding 키는 401이 난다.
     * [URLEncoder]로 먼저 인코딩하고 재인코딩을 막아야 모든 특수문자가 안전하게 전달된다.
     *
     * 공공데이터포털은 Encoding 키(이미 `%2B` 등으로 인코딩된 형태)와 Decoding 키(원문)를
     * 둘 다 발급하는데, 운영자가 어느 쪽을 등록할지 코드가 강제하지 않는다 — 이미 인코딩된 값은
     * Base64 알파벳(`A-Za-z0-9+/=`)에 없는 `%`를 반드시 포함하므로, 그 유무로 자동 판별해
     * 두 형태 모두 그대로 붙여넣으면 동작하게 한다.
     */
    private fun buildUri(page: Int, perPage: Int): URI {
        val encodedServiceKey = if (props.serviceKey.contains('%')) {
            props.serviceKey
        } else {
            URLEncoder.encode(props.serviceKey, StandardCharsets.UTF_8)
        }
        return UriComponentsBuilder.fromUriString(props.baseUrl)
            .path(PATH)
            .queryParam("serviceKey", encodedServiceKey)
            .queryParam("page", page)
            .queryParam("perPage", perPage)
            .queryParam("returnType", "JSON")
            .build(true)
            .toUri()
    }

    @Retryable(
        retryFor = [RateLimitException::class],
        maxAttempts = 3,
        backoff = Backoff(delay = 60_000L),
    )
    private fun <T> callApi(
        page: Int,
        perPage: Int,
        parser: (String) -> T,
    ): Either<DomainError, T> {
        return try {
            log.debug("법정동코드 요청 (page=$page, perPage=$perPage)")
            val response = restClient.get()
                .uri(buildUri(page, perPage))
                .retrieve()
                .onStatus({ it == HttpStatus.TOO_MANY_REQUESTS }) { _, _ ->
                    throw RateLimitException("일 요청 건수 초과 (path=$PATH, page=$page)")
                }
                .onStatus({ it == HttpStatus.UNAUTHORIZED }) { _, _ ->
                    throw UnauthorizedException("인증키가 유효하지 않습니다 (path=$PATH)")
                }
                .onStatus({ it.is4xxClientError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "클라이언트 오류 (path=$PATH, page=$page)")
                }
                .onStatus({ it.is5xxServerError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "서버 오류 (path=$PATH, page=$page)")
                }
                .toEntity(String::class.java)

            log.debug("법정동코드 응답 상태: ${response.statusCode}, Content-Type: ${response.headers.contentType}")

            val body = response.body
                ?.takeIf { it.isNotBlank() }
                ?: return Either.Left(DomainError.ParseError("빈 응답 (path=$PATH, page=$page)"))
            Either.Right(parser(body))
        } catch (e: RateLimitException) {
            log.warn("Rate limit 초과, 재시도 예정: ${e.message}")
            throw e
        } catch (e: UnauthorizedException) {
            log.error("인증 실패: ${e.message}")
            Either.Left(DomainError.Unauthorized)
        } catch (e: ApiException) {
            log.error("API 오류 (${e.statusCode}): ${e.message}")
            Either.Left(DomainError.ApiCallError(e.statusCode, null, e.message ?: ""))
        } catch (e: RestClientException) {
            log.error("네트워크 오류: ${e.message}", e)
            Either.Left(DomainError.NetworkError(e.message ?: "네트워크 오류", e))
        } catch (e: Exception) {
            log.error("JSON 파싱 오류: ${e.message}", e)
            Either.Left(DomainError.ParseError(e.message ?: "파싱 오류", e))
        }
    }

    companion object {
        /** 데이터셋 판(edition)이 바뀌면 무효가 된다 — 404 발생 시 이 상수를 갱신할 것 */
        private const val PATH = "/api/15123287/v1/uddi:b68902fa-d058-4a17-b188-ff46b7eaaac7"
    }
}
