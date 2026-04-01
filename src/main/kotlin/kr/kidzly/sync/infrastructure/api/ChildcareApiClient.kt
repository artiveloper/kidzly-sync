package kr.kidzly.sync.infrastructure.api

import arrow.core.Either
import com.fasterxml.jackson.dataformat.xml.XmlMapper
import kr.kidzly.sync.application.model.ClosedDaycareInfo
import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.application.model.NewDaycareInfo
import kr.kidzly.sync.application.model.SigunguInfo
import kr.kidzly.sync.application.port.ChildcareApiPort
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.infrastructure.api.dto.DaycareDetailXmlItem
import kr.kidzly.sync.infrastructure.api.dto.DaycareDetailXmlResponse
import kr.kidzly.sync.infrastructure.api.dto.DaycareListXmlResponse
import kr.kidzly.sync.infrastructure.api.dto.SigunguXmlResponse
import kr.kidzly.sync.infrastructure.config.ChildcareApiProperties
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.http.HttpStatus
import org.springframework.retry.annotation.Backoff
import org.springframework.retry.annotation.Retryable
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClient
import org.springframework.web.client.RestClientException

@Component
class ChildcareApiClient(
    @param:Qualifier("childcareRestClient") private val restClient: RestClient,
    private val xmlMapper: XmlMapper,
    private val props: ChildcareApiProperties,
) : ChildcareApiPort {

    private val log = LoggerFactory.getLogger(javaClass)

    override fun fetchSigunguList(arname: String): Either<DomainError, List<SigunguInfo>> =
        callApi(
            path = "/mediate/rest/cpmsapi020/cpmsapi020/request",
            key = props.keys.sigungu,
            params = mapOf("arname" to arname),
        ) { body ->
            xmlMapper.readValue(body, SigunguXmlResponse::class.java)
                .items
                .map { SigunguInfo(arcode = it.arcode, sidoname = it.sidoname, sigunname = it.sigunname) }
        }

    override fun fetchDaycareDetails(arcode: String): Either<DomainError, List<DaycareData>> =
        callApi(
            path = "/mediate/rest/cpmsapi030/cpmsapi030/request",
            key = props.keys.daycareDetail,
            params = mapOf("arcode" to arcode),
        ) { body ->
            xmlMapper.readValue(body, DaycareDetailXmlResponse::class.java)
                .items
                .filter { it.stcode.isNotBlank() }
                .map { it.toDaycareData(arcode) }
        }

    override fun fetchNewDaycares(yyyymm: String): Either<DomainError, List<NewDaycareInfo>> =
        callApi(
            path = "/mediate/rest/cpmsapi018/cpmsapi018/request",
            key = props.keys.newDaycare,
            params = mapOf("yyyymm" to yyyymm),
        ) { body ->
            xmlMapper.readValue(body, DaycareListXmlResponse::class.java)
                .items
                .filter { it.stcode.isNotBlank() }
                .map { NewDaycareInfo(stcode = it.stcode, arcode = it.arcode) }
        }

    override fun fetchClosedDaycares(yyyymm: String): Either<DomainError, List<ClosedDaycareInfo>> =
        callApi(
            path = "/mediate/rest/cpmsapi019/cpmsapi019/request",
            key = props.keys.closedDaycare,
            params = mapOf("yyyymm" to yyyymm),
        ) { body ->
            xmlMapper.readValue(body, DaycareListXmlResponse::class.java)
                .items
                .filter { it.stcode.isNotBlank() }
                .map { ClosedDaycareInfo(stcode = it.stcode, crstdate = it.crstdate) }
        }

    @Retryable(
        retryFor = [RateLimitException::class],
        maxAttempts = 3,
        backoff = Backoff(delay = 60_000L),
    )
    private fun <T> callApi(
        path: String,
        key: String,
        params: Map<String, String>,
        parser: (String) -> T,
    ): Either<DomainError, T> {
        return try {
            val response = restClient.get()
                .uri { builder ->
                    val uri = builder.path(path)
                        .queryParam("key", key)
                        .also { b -> params.forEach { (k, v) -> b.queryParam(k, v) } }
                        .build()
                    log.debug("API 요청 URI: $uri")
                    uri
                }
                .retrieve()
                .onStatus({ it == HttpStatus.TOO_MANY_REQUESTS }) { _, _ ->
                    throw RateLimitException("일 요청 건수 초과 (path=$path)")
                }
                .onStatus({ it == HttpStatus.UNAUTHORIZED }) { _, _ ->
                    throw UnauthorizedException("인증키가 유효하지 않습니다 (path=$path)")
                }
                .onStatus({ it.is4xxClientError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "클라이언트 오류 (path=$path)")
                }
                .onStatus({ it.is5xxServerError }) { _, response ->
                    throw ApiException(response.statusCode.value(), "서버 오류 (path=$path)")
                }
                .toEntity(String::class.java)

            log.debug("API 응답 상태: ${response.statusCode}, Content-Type: ${response.headers.contentType}, body: ${response.body}")

            val body = response.body
                ?.takeIf { it.isNotBlank() }
                ?: return Either.Left(DomainError.ParseError("빈 응답 (path=$path)"))
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

    private fun DaycareDetailXmlItem.toDaycareData(arcode: String) = DaycareData(
        stcode = stcode,
        arcode = arcode,
        sidoname = sidoname,
        sigunguname = sigunguname,
        crname = crname,
        crtypename = crtypename,
        crstatusname = crstatusname,
        zipcode = zipcode,
        craddr = craddr,
        crtelno = crtelno,
        crfaxno = crfaxno,
        crhome = crhome,
        la = la,
        lo = lo,
        crcapat = crcapat,
        crchcnt = crchcnt,
        nrtrroomcnt = nrtrroomcnt,
        nrtrroomsize = nrtrroomsize,
        plgrdco = plgrdco,
        cctvinstlcnt = cctvinstlcnt,
        chcrtescnt = chcrtescnt,
        classCntTot = classCntTot,
        childCntTot = childCntTot,
        emCntTot = emCntTot,
        ewCntTot = ewCntTot,
        crrepname = crrepname,
        crcnfmdt = crcnfmdt,
        crstdate = crstdate,
    )

}

// @Retryable annotation argument는 compile-time constant여야 하므로 top-level로 선언
class RateLimitException(message: String) : RuntimeException(message)
class UnauthorizedException(message: String) : RuntimeException(message)
class ApiException(val statusCode: Int, message: String) : RuntimeException(message)
