package kr.kidzly.sync.infrastructure.api

import arrow.core.Either
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe
import io.mockk.mockk
import kr.kidzly.sync.application.model.PlaygroundPage
import kr.kidzly.sync.domain.error.DomainError
import kr.kidzly.sync.infrastructure.config.ChildcareApiProperties
import kr.kidzly.sync.infrastructure.config.InfrastructureConfig
import kr.kidzly.sync.infrastructure.config.SafemapApiProperties
import org.hamcrest.Matchers.containsString
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.http.converter.StringHttpMessageConverter
import org.springframework.test.web.client.MockRestServiceServer
import org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo
import org.springframework.test.web.client.response.MockRestResponseCreators.withStatus
import org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess
import org.springframework.web.client.RestClient
import java.math.BigDecimal

/**
 * [SafemapApiClient]의 XML 파싱 + 도메인 매핑 + 에러 매핑 단위 테스트.
 *
 * 실제 HTTP 대신 [MockRestServiceServer]로 응답을 주입한다.
 * XmlMapper는 운영 Bean(`InfrastructureConfig.xmlMapper()`)을 그대로 재사용해
 * 설정(ACCEPT_SINGLE_VALUE_AS_ARRAY 등) 차이로 테스트가 거짓 통과하지 않도록 한다.
 */
class SafemapApiClientTest : FunSpec({

    fun bind(): Pair<SafemapApiClient, MockRestServiceServer> {
        val builder = RestClient.builder()
            .baseUrl(BASE_URL)
            .messageConverters { converters ->
                // 운영 safemapRestClient Bean과 동일 구성 — 누락 시 한글이 ISO-8859-1로 깨진다
                converters.removeIf { it is StringHttpMessageConverter }
                converters.add(0, StringHttpMessageConverter(Charsets.UTF_8))
            }
        val server = MockRestServiceServer.bindTo(builder).build()
        val client = SafemapApiClient(
            restClient = builder.build(),
            xmlMapper = InfrastructureConfig(mockk<ChildcareApiProperties>(relaxed = true)).xmlMapper(),
            props = SafemapApiProperties(
                baseUrl = BASE_URL,
                serviceKey = "TEST_SERVICE_KEY",
                pageSize = 1000,
                requestIntervalMs = 0L,
            ),
        )
        return client to server
    }

    fun respondWith(server: MockRestServiceServer, xml: String) {
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withSuccess(xml, MediaType.APPLICATION_XML))
    }

    fun fetchOk(xml: String): PlaygroundPage {
        val (client, server) = bind()
        respondWith(server, xml)
        val result = client.fetchPlaygrounds(pageNo = 1, numOfRows = 1000)
        server.verify()
        return (result as Either.Right).value
    }

    fun fetchError(xml: String): DomainError {
        val (client, server) = bind()
        respondWith(server, xml)
        return (client.fetchPlaygrounds(1, 1000) as Either.Left).value
    }

    // ── XML 파싱 ──────────────────────────────────────────────────────────────

    test("should parse the nested response>body>items>item structure and page metadata") {
        val page = fetchOk(responseOf(SAMPLE_ITEM, SECOND_ITEM, totalCount = 84251, numOfRows = 2))

        page.items.size shouldBe 2
        page.pageNo shouldBe 1
        page.numOfRows shouldBe 2
        page.totalCount shouldBe 84251
    }

    test("should parse a page that contains only a single item (ACCEPT_SINGLE_VALUE_AS_ARRAY)") {
        val page = fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1))

        page.items.size shouldBe 1
        page.items[0].facilityId shouldBe "1741"
    }

    test("should parse an item page-by-page into every PlaygroundData field") {
        val item = fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1)).items[0]

        item.facilitySerialNo shouldBe "1002057"
        item.sidoCode shouldBe "41"
        item.sigunguCode shouldBe "41590"
        item.emdCode shouldBe "41590118"
        item.address shouldBe "경기 화성시 동탄하나1길 68"
        item.installDate shouldBe "20240521"
        item.facilityCode1 shouldBe "4159011800"
        item.installPlaceCode shouldBe "A004"
        item.ownershipCode shouldBe "C001"
        item.indoorOutdoorCode shouldBe "O001"
        item.operationCode shouldBe "B001"
    }

    test("should normalize objt_id '1741.0' to '1741'") {
        fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1)).items[0].facilityId shouldBe "1741"
    }

    test("should normalize objt_id in exponent notation '1.741E3' to '1741'") {
        val xml = responseOf(itemXml(objtId = "1.741E3"), totalCount = 1, numOfRows = 1)

        fetchOk(xml).items[0].facilityId shouldBe "1741"
    }

    test("should map empty elements such as <del_yn></del_yn> to null") {
        val item = fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1)).items[0]

        item.deletedYn shouldBe null
        item.accidentYn shouldBe null
        item.facilityCode2 shouldBe null // <fclty_cd3></fclty_cd3>
    }

    test("should convert x/y strings to BigDecimal without altering the scale") {
        val item = fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1)).items[0]

        // setScale()을 하지 않아야 매 동기화가 UPDATE로 오탐되지 않는다 (설계 §7.6)
        item.coordX shouldBe BigDecimal("14144087.4653")
        item.coordY shouldBe BigDecimal("4469799.53254")
    }

    test("should return null coordinates when x/y are empty elements") {
        val xml = responseOf(itemXml(x = "", y = ""), totalCount = 1, numOfRows = 1)

        val item = fetchOk(xml).items[0]
        item.coordX shouldBe null
        item.coordY shouldBe null
    }

    test("should return null coordinates when x/y are not numeric instead of failing the page") {
        val xml = responseOf(itemXml(x = "N/A", y = "-"), totalCount = 1, numOfRows = 1)

        val item = fetchOk(xml).items[0]
        item.coordX shouldBe null
        item.coordY shouldBe null
        item.facilityId shouldBe "1741" // 좌표 실패가 아이템 전체를 탈락시키지 않는다
    }

    test("should preserve Korean facility names as UTF-8") {
        val item = fetchOk(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1)).items[0]

        item.name shouldBe "한마음정육식당 화성동탄능동점"
    }

    test("should trim surrounding whitespace on text fields") {
        val xml = responseOf(itemXml(fcltyNm = "  둔촌어린이공원  ", adres = "  서울 강동구  "), totalCount = 1, numOfRows = 1)

        val item = fetchOk(xml).items[0]
        item.name shouldBe "둔촌어린이공원"
        item.address shouldBe "서울 강동구"
    }

    test("should drop items whose objt_id is blank or unparsable") {
        val xml = responseOf(
            itemXml(objtId = ""),
            itemXml(objtId = "not-a-number"),
            SAMPLE_ITEM,
            totalCount = 3,
            numOfRows = 3,
        )

        val page = fetchOk(xml)
        page.items.size shouldBe 1
        page.items[0].facilityId shouldBe "1741"
    }

    test("should drop items whose fclty_nm is blank because name is NOT NULL") {
        val xml = responseOf(itemXml(objtId = "10", fcltyNm = "   "), SAMPLE_ITEM, totalCount = 2, numOfRows = 2)

        val page = fetchOk(xml)
        page.items.size shouldBe 1
        page.items[0].facilityId shouldBe "1741"
    }

    test("should return an empty item list when items element has no children") {
        val page = fetchOk(
            """
            <response>
              <header><resultCode>00</resultCode><resultMsg>NORMAL_SERVICE</resultMsg></header>
              <body><items></items><numOfRows>0</numOfRows><pageNo>90</pageNo><totalCount>84251</totalCount></body>
            </response>
            """.trimIndent(),
        )

        page.items.size shouldBe 0
        page.totalCount shouldBe 84251
    }

    // ── 에러 매핑 ─────────────────────────────────────────────────────────────

    test("should map HTTP 200 with resultCode != 00 to ApiCallError(200, resultCode, resultMsg)") {
        val error = fetchError(
            """
            <response>
              <header><resultCode>99</resultCode><resultMsg>SERVICE_ERROR</resultMsg></header>
              <body><items></items><numOfRows>0</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body>
            </response>
            """.trimIndent(),
        )

        error shouldBe DomainError.ApiCallError(HttpStatus.OK.value(), "99", "SERVICE_ERROR")
    }

    test("should map a missing header (resultCode absent) to ApiCallError rather than silently succeeding") {
        val error = fetchError(
            """
            <response>
              <body><items></items><numOfRows>0</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body>
            </response>
            """.trimIndent(),
        )

        error shouldBe DomainError.ApiCallError(HttpStatus.OK.value(), "", "")
    }

    test("should map an empty response body to ParseError") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withSuccess("", MediaType.APPLICATION_XML))

        val error = (client.fetchPlaygrounds(7, 1000) as Either.Left).value

        error.shouldBeParseErrorContaining("pageNo=7")
    }

    test("should map a blank (whitespace only) response body to ParseError") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withSuccess("   \n  ", MediaType.APPLICATION_XML))

        val error = (client.fetchPlaygrounds(1, 1000) as Either.Left).value

        error.shouldBeParseErrorContaining("빈 응답")
    }

    test("should map malformed XML to ParseError") {
        val error = fetchError("<response><header><resultCode>00</resultCode>")

        (error is DomainError.ParseError) shouldBe true
    }

    test("should map HTTP 401 to DomainError.Unauthorized") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withStatus(HttpStatus.UNAUTHORIZED))

        (client.fetchPlaygrounds(1, 1000) as Either.Left).value shouldBe DomainError.Unauthorized
    }

    test("should map HTTP 500 to ApiCallError with the upstream status code") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withStatus(HttpStatus.INTERNAL_SERVER_ERROR))

        val error = (client.fetchPlaygrounds(1, 1000) as Either.Left).value

        (error as DomainError.ApiCallError).statusCode shouldBe 500
        error.code shouldBe null
    }

    test("should map HTTP 400 to ApiCallError with the upstream status code") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withStatus(HttpStatus.BAD_REQUEST))

        val error = (client.fetchPlaygrounds(1, 1000) as Either.Left).value

        (error as DomainError.ApiCallError).statusCode shouldBe 400
    }

    test("should propagate RateLimitException on HTTP 429 so that @Retryable can act on it") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("/openapi2/IF_0007")))
            .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS))

        val thrown = runCatching { client.fetchPlaygrounds(1, 1000) }.exceptionOrNull()

        thrown.shouldNotBeNull()
        (thrown is RateLimitException) shouldBe true
    }

    // ── 요청 파라미터 ──────────────────────────────────────────────────────────

    test("should send serviceKey, pageNo, numOfRows and returnType=XML on the request URI") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("serviceKey=TEST_SERVICE_KEY")))
            .andRespond(withSuccess(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1), MediaType.APPLICATION_XML))

        client.fetchPlaygrounds(pageNo = 42, numOfRows = 500)

        server.verify()
    }

    test("should honour the numOfRows argument instead of re-reading the configured pageSize") {
        val (client, server) = bind()
        server.expect(requestTo(containsString("numOfRows=500")))
            .andRespond(withSuccess(responseOf(SAMPLE_ITEM, totalCount = 1, numOfRows = 1), MediaType.APPLICATION_XML))

        client.fetchPlaygrounds(pageNo = 42, numOfRows = 500)

        server.verify()
    }
})

private const val BASE_URL = "https://safemap.go.kr"

private fun DomainError.shouldBeParseErrorContaining(fragment: String) {
    (this is DomainError.ParseError) shouldBe true
    ((this as DomainError.ParseError).message.contains(fragment)) shouldBe true
}

/** 요구사항 문서의 실제 응답 샘플 그대로 (빈 엘리먼트 포함) */
private val SAMPLE_ITEM = itemXml()

private val SECOND_ITEM = itemXml(
    objtId = "1742.0",
    fcltyCd1 = "1002058",
    fcltyNm = "능동어린이공원 놀이터",
    adres = "경기 화성시 동탄하나1길 70",
    x = "14144090.1",
    y = "4469800.2",
    delYn = "N",
    acYn = "Y",
)

@Suppress("LongParameterList")
private fun itemXml(
    objtId: String = "1741.0",
    fcltyCd1: String = "1002057",
    fcltyCd2: String = "4159011800",
    fcltyCd3: String = "",
    fcltyCd4: String = "A004",
    fcltyCd5: String = "C001",
    fcltyCd6: String = "O001",
    fcltyCd7: String = "B001",
    fcltyNm: String = "한마음정육식당 화성동탄능동점",
    ctprvnCd: String = "41",
    sggCd: String = "41590",
    emdCd: String = "41590118",
    instlDe: String = "20240521",
    adres: String = "경기 화성시 동탄하나1길 68",
    acYn: String = "",
    delYn: String = "",
    x: String = "14144087.4653",
    y: String = "4469799.53254",
): String = """
    <item>
      <instl_de>$instlDe</instl_de>
      <fclty_cd1>$fcltyCd1</fclty_cd1>
      <ctprvn_cd>$ctprvnCd</ctprvn_cd>
      <fclty_cd3>$fcltyCd3</fclty_cd3>
      <objt_id>$objtId</objt_id>
      <fclty_cd2>$fcltyCd2</fclty_cd2>
      <fclty_cd5>$fcltyCd5</fclty_cd5>
      <fclty_cd4>$fcltyCd4</fclty_cd4>
      <fclty_cd7>$fcltyCd7</fclty_cd7>
      <fclty_cd6>$fcltyCd6</fclty_cd6>
      <emd_cd>$emdCd</emd_cd>
      <fclty_nm>$fcltyNm</fclty_nm>
      <del_yn>$delYn</del_yn>
      <sgg_cd>$sggCd</sgg_cd>
      <ac_yn>$acYn</ac_yn>
      <x>$x</x>
      <y>$y</y>
      <adres>$adres</adres>
    </item>
""".trimIndent()

// XML 선언은 문서 맨 앞이어야 하므로 trimIndent 대상 밖에서 붙인다
private fun responseOf(vararg items: String, totalCount: Int, numOfRows: Int, pageNo: Int = 1): String =
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + """
    <response>
      <header>
        <resultCode>00</resultCode>
        <resultMsg>NORMAL_SERVICE</resultMsg>
      </header>
      <body>
        <items>
    ${items.joinToString("\n")}
        </items>
        <numOfRows>$numOfRows</numOfRows>
        <pageNo>$pageNo</pageNo>
        <totalCount>$totalCount</totalCount>
      </body>
    </response>
""".trimIndent()
