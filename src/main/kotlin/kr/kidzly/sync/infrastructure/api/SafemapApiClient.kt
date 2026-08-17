package kr.kidzly.sync.infrastructure.api

import arrow.core.Either
import arrow.core.flatMap
import com.fasterxml.jackson.dataformat.xml.XmlMapper
import kr.kidzly.sync.application.model.PlaygroundData
import kr.kidzly.sync.application.model.PlaygroundPage
import kr.kidzly.sync.application.port.SafemapApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.infrastructure.api.dto.PlaygroundXmlItem
import kr.kidzly.sync.infrastructure.api.dto.PlaygroundXmlResponse
import kr.kidzly.sync.infrastructure.config.SafemapApiProperties
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.http.HttpStatus
import org.springframework.retry.annotation.Backoff
import org.springframework.retry.annotation.Retryable
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient
import org.springframework.web.client.RestClientException
import java.math.BigDecimal

/**
 * safemap.go.kr 어린이놀이시설정보(IF_0007) 클라이언트.
 *
 * childcare와의 차이:
 * - 응답 구조가 response > body > items > item (items 래퍼 존재)
 * - HTTP 200이어도 header.resultCode 가 "00"이 아니면 실패다
 */
@Component
class SafemapApiClient(
    @param:Qualifier("safemapRestClient") private val restClient: RestClient,
    private val xmlMapper: XmlMapper,
    private val props: SafemapApiProperties,
) : SafemapApiPort {

    private val log = LoggerFactory.getLogger(javaClass)

    override fun fetchPlaygrounds(pageNo: Int, numOfRows: Int): Either<DomainError, PlaygroundPage> =
        callApi(pageNo, numOfRows) { body ->
            xmlMapper.readValue(body, PlaygroundXmlResponse::class.java)
        }.flatMap { response -> response.toPlaygroundPage() }

    private fun PlaygroundXmlResponse.toPlaygroundPage(): Either<DomainError, PlaygroundPage> {
        if (header.resultCode != RESULT_CODE_SUCCESS) {
            log.error("IF_0007 응답 오류 (resultCode=${header.resultCode}, resultMsg=${header.resultMsg})")
            return Either.Left(
                DomainError.ApiCallError(HttpStatus.OK.value(), header.resultCode, header.resultMsg),
            )
        }
        return Either.Right(
            PlaygroundPage(
                items = body.items?.item.orEmpty().mapNotNull { it.toPlaygroundData() },
                pageNo = body.pageNo,
                numOfRows = body.numOfRows,
                totalCount = body.totalCount,
            ),
        )
    }

    /** 식별자 또는 시설명이 없는 아이템은 저장할 수 없으므로 제외한다. */
    private fun PlaygroundXmlItem.toPlaygroundData(): PlaygroundData? {
        val facilityId = objtId?.normalizeFacilityId() ?: return null
        val facilityName = fcltyNm?.trim()?.takeIf { it.isNotBlank() } ?: return null
        return PlaygroundData(
            facilityId = facilityId,
            facilitySerialNo = fcltyCd1.normalizeBlank(),
            sidoCode = ctprvnCd.normalizeBlank(),
            sigunguCode = sggCd.normalizeBlank(),
            emdCode = emdCd.normalizeBlank(),
            name = facilityName,
            address = adres.normalizeBlank(),
            coordX = x.toBigDecimalOrNull(),
            coordY = y.toBigDecimalOrNull(),
            installDate = instlDe.normalizeBlank(),
            facilityCode1 = fcltyCd2.normalizeBlank(),
            facilityCode2 = fcltyCd3.normalizeBlank(),
            installPlaceCode = fcltyCd4.normalizeBlank(),
            ownershipCode = fcltyCd5.normalizeBlank(),
            indoorOutdoorCode = fcltyCd6.normalizeBlank(),
            operationCode = fcltyCd7.normalizeBlank(),
            accidentYn = acYn.normalizeBlank(),
            deletedYn = delYn.normalizeBlank(),
        )
    }

    /**
     * objt_id 정규화: "1741.0" → "1741".
     * substringBefore('.')는 지수 표기("1.741E3")에서 깨지므로 BigDecimal을 경유한다.
     */
    private fun String.normalizeFacilityId(): String? =
        trim().takeIf { it.isNotBlank() }
            ?.let { raw ->
                runCatching { BigDecimal(raw).toBigInteger().toString() }
                    .onFailure { log.warn("objt_id 정규화 실패 — 아이템 제외 (objt_id=$raw)") }
                    .getOrNull()
            }

    private fun String?.normalizeBlank(): String? = this?.trim()?.takeIf { it.isNotBlank() }

    private fun String?.toBigDecimalOrNull(): BigDecimal? =
        normalizeBlank()?.let { raw ->
            runCatching { BigDecimal(raw) }
                .onFailure { log.warn("좌표 변환 실패 — null 처리 (value=$raw)") }
                .getOrNull()
        }

    @Retryable(
        retryFor = [RateLimitException::class],
        maxAttempts = 3,
        backoff = Backoff(delay = 60_000L),
    )
    private fun <T> callApi(
        pageNo: Int,
        numOfRows: Int,
        parser: (String) -> T,
    ): Either<DomainError, T> {
        return try {
            val response = restClient.get()
                .uri { builder ->
                    val uri = builder.path(PATH)
                        .queryParam("serviceKey", props.serviceKey)
                        .queryParam("pageNo", pageNo)
                        .queryParam("numOfRows", numOfRows)
                        .queryParam("returnType", "XML")
                        .build()
                    log.debug("IF_0007 요청 (pageNo=$pageNo, numOfRows=$numOfRows)")
                    uri
                }
                .retrieve()
                .onStatus({ it == HttpStatus.TOO_MANY_REQUESTS }) { _, _ ->
                    throw RateLimitException("일 요청 건수 초과 (path=$PATH, pageNo=$pageNo)")
                }
                .onStatus({ it == HttpStatus.UNAUTHORIZED }) { _, _ ->
                    throw UnauthorizedException("인증키가 유효하지 않습니다 (path=$PATH)")
                }
                .onStatus({ it.is4xxClientError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "클라이언트 오류 (path=$PATH, pageNo=$pageNo)")
                }
                .onStatus({ it.is5xxServerError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "서버 오류 (path=$PATH, pageNo=$pageNo)")
                }
                .toEntity(String::class.java)

            log.debug("IF_0007 응답 상태: ${response.statusCode}, Content-Type: ${response.headers.contentType}")

            val body = response.body
                ?.takeIf { it.isNotBlank() }
                ?: return Either.Left(DomainError.ParseError("빈 응답 (path=$PATH, pageNo=$pageNo)"))
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
            log.error("XML 파싱 오류: ${e.message}", e)
            Either.Left(DomainError.ParseError(e.message ?: "파싱 오류", e))
        }
    }

    companion object {
        private const val PATH = "/openapi2/IF_0007"
        private const val RESULT_CODE_SUCCESS = "00"
    }
}
