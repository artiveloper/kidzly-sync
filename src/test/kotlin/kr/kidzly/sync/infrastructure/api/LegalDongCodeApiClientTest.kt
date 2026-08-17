package kr.kidzly.sync.infrastructure.api

import arrow.core.Either
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import io.mockk.mockk
import kr.kidzly.sync.application.model.LegalDongCodePage
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.infrastructure.config.ChildcareApiProperties
import kr.kidzly.sync.infrastructure.config.InfrastructureConfig
import kr.kidzly.sync.infrastructure.config.LegalDongCodeApiProperties
import org.hamcrest.Matchers.containsString
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.http.converter.StringHttpMessageConverter
import org.springframework.test.web.client.MockRestServiceServer
import org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo
import org.springframework.test.web.client.response.MockRestResponseCreators.withStatus
import org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess
import org.springframework.web.client.RestClient

/**
 * [LegalDongCodeApiClient]의 JSON 파싱 + 에러 매핑 + 요청 파라미터 단위 테스트.
 *
 * 실제 HTTP 대신 [MockRestServiceServer]로 응답을 주입한다.
 * ObjectMapper는 운영 Bean(`InfrastructureConfig.objectMapper()`)을 그대로 재사용해
 * 설정(FAIL_ON_UNKNOWN_PROPERTIES 등) 차이로 테스트가 거짓 통과하지 않도록 한다.
 */
class LegalDongCodeApiClientTest : FunSpec({

    fun bind(serviceKey: String = "TEST_SERVICE_KEY"): Pair<LegalDongCodeApiClient, MockRestServiceServer> {
        val builder = RestClient.builder()
            .baseUrl(BASE_URL)
            .messageConverters { converters ->
                // 운영 legalDongCodeRestClient Bean과 동일 구성 — 누락 시 법정동명이 ISO-8859-1로 깨진다
                converters.removeIf { it is StringHttpMessageConverter }
                converters.add(0, StringHttpMessageConverter(Charsets.UTF_8))
            }
        val server = MockRestServiceServer.bindTo(builder).build()
        val client = LegalDongCodeApiClient(
            restClient = builder.build(),
            objectMapper = InfrastructureConfig(mockk<ChildcareApiProperties>(relaxed = true)).objectMapper(),
            props = LegalDongCodeApiProperties(
                baseUrl = BASE_URL,
                serviceKey = serviceKey,
                perPage = 1000,
                requestIntervalMs = 0L,
            ),
        )
        return client to server
    }

    fun respondWith(server: MockRestServiceServer, json: String) {
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withSuccess(json, MediaType.APPLICATION_JSON))
    }

    fun fetchOk(json: String, page: Int = 1): LegalDongCodePage {
        val (client, server) = bind()
        respondWith(server, json)
        val result = client.fetchLegalDongCodes(page = page, perPage = 1000)
        server.verify()
        return (result as Either.Right).value
    }

    fun fetchError(json: String, page: Int = 1): DomainError {
        val (client, server) = bind()
        respondWith(server, json)
        return (client.fetchLegalDongCodes(page, 1000) as Either.Left).value
    }

    // ── JSON 파싱 ─────────────────────────────────────────────────────────────

    test("should parse the odcloud envelope and its page metadata") {
        val page = fetchOk(responseOf(CHEONGUN_DONG, JONGNO_GU, totalCount = 49861, perPage = 1000, page = 1))

        page.items.size shouldBe 2
        page.page shouldBe 1
        page.perPage shouldBe 1000
        page.totalCount shouldBe 49861
    }

    test("should map the Korean JSON property names onto the record fields") {
        val record = fetchOk(responseOf(CHEONGUN_DONG, totalCount = 1)).items[0]

        record.code shouldBe "1111010100"
        record.name shouldBe "서울특별시 종로구 청운동"
        record.abolishedYn shouldBe "존재"
    }

    test("should preserve Korean legal dong names as UTF-8") {
        fetchOk(responseOf(itemJson(name = "제주특별자치도 서귀포시 대정읍 상모리"), totalCount = 1))
            .items[0].name shouldBe "제주특별자치도 서귀포시 대정읍 상모리"
    }

    test("should keep 폐지 records because the client does not apply the business filter") {
        // 폐지여부 필터와 레벨 판별은 UseCase 책임이다 (설계 §2.1)
        val page = fetchOk(
            responseOf(
                itemJson(code = "1111010100", abolishedYn = "존재"),
                itemJson(code = "1111010200", abolishedYn = "폐지"),
                itemJson(code = "4173025321", abolishedYn = "존재"), // 리 레벨
                totalCount = 3,
            ),
        )

        page.items.size shouldBe 3
        page.items.map { it.abolishedYn } shouldBe listOf("존재", "폐지", "존재")
    }

    test("should trim surrounding whitespace on every text field") {
        val record = fetchOk(
            responseOf(itemJson(code = "  1111010100 ", name = "  청운동  ", abolishedYn = " 존재 "), totalCount = 1),
        ).items[0]

        record.code shouldBe "1111010100"
        record.name shouldBe "청운동"
        record.abolishedYn shouldBe "존재"
    }

    test("should map a missing or blank 폐지여부 to null instead of an empty string") {
        fetchOk(responseOf(itemJson(abolishedYn = "   "), totalCount = 1)).items[0].abolishedYn shouldBe null
        fetchOk("""{"page":1,"perPage":1000,"totalCount":1,"data":[{"법정동코드":"1111010100","법정동명":"청운동"}]}""")
            .items[0].abolishedYn shouldBe null
    }

    test("should ignore unknown properties such as matchCount and currentCount") {
        val page = fetchOk(
            """
            {"currentCount":1,"data":[{"법정동코드":"1111010100","법정동명":"청운동","폐지여부":"존재","비고":"x"}],
             "matchCount":49861,"page":1,"perPage":1000,"totalCount":49861}
            """.trimIndent(),
        )

        page.items.size shouldBe 1
        page.totalCount shouldBe 49861
    }

    test("should accept a numeric 법정동코드 by coercing it to a string") {
        val page = fetchOk("""{"page":1,"perPage":1000,"totalCount":1,"data":[{"법정동코드":1111010100,"법정동명":"청운동","폐지여부":"존재"}]}""")

        page.items[0].code shouldBe "1111010100"
    }

    test("should drop items whose 법정동코드 is missing or blank") {
        val page = fetchOk(
            responseOf(
                itemJson(code = "   "),
                """{"법정동명":"코드 없음","폐지여부":"존재"}""",
                CHEONGUN_DONG,
                totalCount = 3,
            ),
        )

        page.items.size shouldBe 1
        page.items[0].code shouldBe "1111010100"
    }

    test("should drop items whose 법정동명 is missing or blank because name is NOT NULL") {
        val page = fetchOk(
            responseOf(
                itemJson(code = "1111010200", name = "  "),
                """{"법정동코드":"1111010300","폐지여부":"존재"}""",
                CHEONGUN_DONG,
                totalCount = 3,
            ),
        )

        page.items.size shouldBe 1
        page.items[0].code shouldBe "1111010100"
    }

    test("should return an empty item list when data is an empty array") {
        val page = fetchOk("""{"page":51,"perPage":1000,"totalCount":49861,"data":[]}""")

        page.items.size shouldBe 0
        page.totalCount shouldBe 49861
    }

    test("should fall back to the requested page number when the response page is 0 or absent") {
        val page = fetchOk("""{"perPage":1000,"totalCount":1,"data":[$CHEONGUN_DONG]}""", page = 7)

        page.page shouldBe 7
    }

    // ── 에러 매핑 ─────────────────────────────────────────────────────────────

    test("should map a response without the data field to ParseError") {
        val error = fetchError("""{"code":"ERROR","msg":"SERVICE KEY IS NOT REGISTERED ERROR"}""", page = 3)

        error.shouldBeParseErrorContaining("data 필드 없음")
        error.shouldBeParseErrorContaining("page=3")
    }

    test("should map an explicit null data field to ParseError") {
        fetchError("""{"page":1,"perPage":1000,"totalCount":0,"data":null}""")
            .shouldBeParseErrorContaining("data 필드 없음")
    }

    test("should map an empty response body to ParseError") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withSuccess("", MediaType.APPLICATION_JSON))

        val error = (client.fetchLegalDongCodes(9, 1000) as Either.Left).value

        error.shouldBeParseErrorContaining("빈 응답")
        error.shouldBeParseErrorContaining("page=9")
    }

    test("should map a blank (whitespace only) response body to ParseError") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withSuccess("   \n  ", MediaType.APPLICATION_JSON))

        (client.fetchLegalDongCodes(1, 1000) as Either.Left).value.shouldBeParseErrorContaining("빈 응답")
    }

    test("should map malformed JSON to ParseError") {
        val error = fetchError("""{"page":1,"data":[{"법정동코드":""")

        (error is DomainError.ParseError) shouldBe true
    }

    test("should map an HTML error page to ParseError instead of throwing") {
        val error = fetchError("<html><body>Gateway</body></html>")

        (error is DomainError.ParseError) shouldBe true
    }

    test("should map HTTP 401 to DomainError.Unauthorized") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withStatus(HttpStatus.UNAUTHORIZED))

        (client.fetchLegalDongCodes(1, 1000) as Either.Left).value shouldBe DomainError.Unauthorized
    }

    test("should map HTTP 500 to ApiCallError with the upstream status code") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withStatus(HttpStatus.INTERNAL_SERVER_ERROR))

        val error = (client.fetchLegalDongCodes(1, 1000) as Either.Left).value

        (error as DomainError.ApiCallError).statusCode shouldBe 500
        error.code shouldBe null
    }

    test("should map HTTP 404 (stale UDDI path) to ApiCallError 404") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withStatus(HttpStatus.NOT_FOUND))

        val error = (client.fetchLegalDongCodes(1, 1000) as Either.Left).value

        (error as DomainError.ApiCallError).statusCode shouldBe 404
    }

    test("should propagate RateLimitException on HTTP 429 so that @Retryable can act on it") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/api/15123287/v1/uddi:")))
            .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS))

        val thrown = runCatching { client.fetchLegalDongCodes(1, 1000) }.exceptionOrNull()

        thrown.shouldNotBeNull()
        (thrown is RateLimitException) shouldBe true
    }

    // ── 요청 파라미터 ──────────────────────────────────────────────────────────

    test("should pass an already percent-encoded Encoding key through untouched") {
        // '%'가 있으면 이미 인코딩된 값(Encoding 키)으로 판단해 그대로 전송한다 —
        // Decoding 키인지 Encoding 키인지 운영자가 구분할 필요가 없도록 자동 판별한다.
        val (client, server) = bind(serviceKey = "abc%2Bdef%3D")
        server.expect(requestTo(containsString("serviceKey=abc%2Bdef%3D")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(1, 1000)

        server.verify()
    }

    test("should percent-encode '+' and '=' in a Decoding key (review issue M-1 fixed)") {
        // '+' 는 query 에서 합법 문자라 UriBuilder 에 맡기면 인코딩되지 않고,
        // 서버가 query 의 '+' 를 공백으로 디코딩하면 401 이 난다.
        // 직접 percent-encode 후 pre-encoded URI 로 넘기므로 이제 %2B 로 전송되어야 한다.
        val (client, server) = bind(serviceKey = "abc+def=")
        server.expect(requestTo(containsString("serviceKey=abc%2Bdef%3D")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(1, 1000)

        server.verify()
    }

    test("should percent-encode '/' in a Decoding key so a Base64 key survives intact") {
        val (client, server) = bind(serviceKey = "a/b+c==")
        server.expect(requestTo(containsString("serviceKey=a%2Fb%2Bc%3D%3D")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(1, 1000)

        server.verify()
    }

    test("should leave an alphanumeric service key untouched") {
        val (client, server) = bind(serviceKey = "PLAIN123key")
        server.expect(requestTo(containsString("serviceKey=PLAIN123key")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(1, 1000)

        server.verify()
    }

    test("should send page, perPage and returnType=JSON on the request URI") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("page=42")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(page = 42, perPage = 500)

        server.verify()
    }

    test("should honour the perPage argument instead of re-reading the configured perPage") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("perPage=500")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(page = 42, perPage = 500)

        server.verify()
    }

    test("should request the JSON return type") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("returnType=JSON")))
            .andRespond(withSuccess(responseOf(CHEONGUN_DONG, totalCount = 1), MediaType.APPLICATION_JSON))

        client.fetchLegalDongCodes(1, 1000)

        server.verify()
    }
})

private const val BASE_URL = "https://api.odcloud.kr"

private fun DomainError.shouldBeParseErrorContaining(fragment: String) {
    (this is DomainError.ParseError) shouldBe true
    ((this as DomainError.ParseError).message.contains(fragment)) shouldBe true
}

private fun itemJson(
    code: String = "1111010100",
    name: String = "서울특별시 종로구 청운동",
    abolishedYn: String = "존재",
): String = """{"법정동코드":"$code","법정동명":"$name","폐지여부":"$abolishedYn"}"""

private val CHEONGUN_DONG = itemJson()

private val JONGNO_GU = itemJson(code = "1111000000", name = "서울특별시 종로구")

private fun responseOf(
    vararg items: String,
    totalCount: Int,
    perPage: Int = 1000,
    page: Int = 1,
): String = """
    {
      "page": $page,
      "perPage": $perPage,
      "totalCount": $totalCount,
      "currentCount": ${items.size},
      "matchCount": $totalCount,
      "data": [${items.joinToString(",")}]
    }
""".trimIndent()
