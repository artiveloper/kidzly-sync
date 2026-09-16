"""``SafemapApiClient`` 의 XML 파싱 + 도메인 매핑 + 에러 매핑 단위 테스트.

실제 HTTP 대신 :class:`httpx.MockTransport` 로 응답을 주입한다.
"""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from kidzly_sync.config import SafemapApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from kidzly_sync.infrastructure.api.safemap_client import SafemapApiClient

BASE_URL = "https://safemap.go.kr"


def build_client(
    *,
    service_key: str = "TEST_SERVICE_KEY",
    responses: list[httpx.Response] | None = None,
) -> tuple[SafemapApiClient, list[httpx.Request]]:
    queue = list(responses or [])
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return queue.pop(0) if queue else httpx.Response(200, text="<response/>")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    config = SafemapApiConfig(
        base_url=BASE_URL, service_key=service_key, page_size=1000, request_interval_ms=0
    )
    # 재시도 간격은 0 — 대기 시간이 테스트를 멈추게 하지 않는다
    return SafemapApiClient(http, config, retry_delay_ms=0), seen


def xml_response(body: str) -> httpx.Response:
    return httpx.Response(200, content=body.encode("utf-8"), headers={"content-type": "application/xml"})


def fetch_ok(xml: str, page_no: int = 1):
    client, _ = build_client(responses=[xml_response(xml)])
    result = client.fetch_playgrounds(page_no=page_no, num_of_rows=1000)
    assert isinstance(result, Ok), result
    return result.value


def fetch_error(xml: str, page_no: int = 1):
    client, _ = build_client(responses=[xml_response(xml)])
    result = client.fetch_playgrounds(page_no, 1000)
    assert isinstance(result, Err), result
    return result.error


def item_xml(
    objt_id: str = "1741.0",
    fclty_cd1: str = "1002057",
    fclty_cd2: str = "4159011800",
    fclty_cd3: str = "",
    fclty_cd4: str = "A004",
    fclty_cd5: str = "C001",
    fclty_cd6: str = "O001",
    fclty_cd7: str = "B001",
    fclty_nm: str = "한마음정육식당 화성동탄능동점",
    ctprvn_cd: str = "41",
    sgg_cd: str = "41590",
    emd_cd: str = "41590118",
    instl_de: str = "20240521",
    adres: str = "경기 화성시 동탄하나1길 68",
    ac_yn: str = "",
    del_yn: str = "",
    x: str = "14144087.4653",
    y: str = "4469799.53254",
) -> str:
    return f"""<item>
      <instl_de>{instl_de}</instl_de>
      <fclty_cd1>{fclty_cd1}</fclty_cd1>
      <ctprvn_cd>{ctprvn_cd}</ctprvn_cd>
      <fclty_cd3>{fclty_cd3}</fclty_cd3>
      <objt_id>{objt_id}</objt_id>
      <fclty_cd2>{fclty_cd2}</fclty_cd2>
      <fclty_cd5>{fclty_cd5}</fclty_cd5>
      <fclty_cd4>{fclty_cd4}</fclty_cd4>
      <fclty_cd7>{fclty_cd7}</fclty_cd7>
      <fclty_cd6>{fclty_cd6}</fclty_cd6>
      <emd_cd>{emd_cd}</emd_cd>
      <fclty_nm>{fclty_nm}</fclty_nm>
      <del_yn>{del_yn}</del_yn>
      <sgg_cd>{sgg_cd}</sgg_cd>
      <ac_yn>{ac_yn}</ac_yn>
      <x>{x}</x>
      <y>{y}</y>
      <adres>{adres}</adres>
    </item>"""


SAMPLE_ITEM = item_xml()
SECOND_ITEM = item_xml(
    objt_id="1742.0",
    fclty_cd1="1002058",
    fclty_nm="능동어린이공원 놀이터",
    adres="경기 화성시 동탄하나1길 70",
    x="14144090.1",
    y="4469800.2",
    del_yn="N",
    ac_yn="Y",
)


def response_of(*items: str, total_count: int, num_of_rows: int, page_no: int = 1) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<response>\n"
        "  <header><resultCode>00</resultCode><resultMsg>NORMAL_SERVICE</resultMsg></header>\n"
        "  <body>\n"
        f"    <items>{chr(10).join(items)}</items>\n"
        f"    <numOfRows>{num_of_rows}</numOfRows>\n"
        f"    <pageNo>{page_no}</pageNo>\n"
        f"    <totalCount>{total_count}</totalCount>\n"
        "  </body>\n"
        "</response>"
    )


# ── XML 파싱 ──────────────────────────────────────────────────────────────────


def test_parses_the_nested_response_body_items_item_structure_and_page_metadata():
    page = fetch_ok(response_of(SAMPLE_ITEM, SECOND_ITEM, total_count=84251, num_of_rows=2))

    assert len(page.items) == 2
    assert page.page_no == 1
    assert page.num_of_rows == 2
    assert page.total_count == 84251


def test_parses_a_page_that_contains_only_a_single_item():
    page = fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1))

    assert len(page.items) == 1
    assert page.items[0].facility_id == "1741"


def test_parses_an_item_into_every_playground_data_field():
    item = fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)).items[0]

    assert item.facility_serial_no == "1002057"
    assert item.sido_code == "41"
    assert item.sigungu_code == "41590"
    assert item.emd_code == "41590118"
    assert item.address == "경기 화성시 동탄하나1길 68"
    assert item.install_date == "20240521"
    assert item.facility_code1 == "4159011800"
    assert item.install_place_code == "A004"
    assert item.ownership_code == "C001"
    assert item.indoor_outdoor_code == "O001"
    assert item.operation_code == "B001"


def test_normalizes_objt_id_with_a_decimal_point():
    assert fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)).items[0].facility_id == "1741"


def test_normalizes_objt_id_in_exponent_notation():
    xml = response_of(item_xml(objt_id="1.741E3"), total_count=1, num_of_rows=1)

    assert fetch_ok(xml).items[0].facility_id == "1741"


def test_maps_empty_elements_to_none():
    item = fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)).items[0]

    assert item.deleted_yn is None
    assert item.accident_yn is None
    assert item.facility_code2 is None  # <fclty_cd3></fclty_cd3>


def test_converts_x_y_to_decimal_without_altering_the_scale():
    item = fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)).items[0]

    # 반올림하지 않아야 매 동기화가 UPDATE 로 오탐되지 않는다
    assert item.coord_x == Decimal("14144087.4653")
    assert item.coord_y == Decimal("4469799.53254")
    assert str(item.coord_y) == "4469799.53254"


def test_returns_none_coordinates_when_x_y_are_empty_elements():
    item = fetch_ok(response_of(item_xml(x="", y=""), total_count=1, num_of_rows=1)).items[0]

    assert item.coord_x is None
    assert item.coord_y is None


@pytest.mark.parametrize(("x", "y"), [("N/A", "-"), ("NaN", "Infinity")])
def test_returns_none_coordinates_when_x_y_are_not_numeric_instead_of_failing_the_page(x, y):
    item = fetch_ok(response_of(item_xml(x=x, y=y), total_count=1, num_of_rows=1)).items[0]

    assert item.coord_x is None
    assert item.coord_y is None
    # 좌표 실패가 아이템 전체를 탈락시키지 않는다
    assert item.facility_id == "1741"


def test_preserves_korean_facility_names_as_utf8():
    item = fetch_ok(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)).items[0]

    assert item.name == "한마음정육식당 화성동탄능동점"


def test_trims_surrounding_whitespace_on_text_fields():
    xml = response_of(
        item_xml(fclty_nm="  둔촌어린이공원  ", adres="  서울 강동구  "), total_count=1, num_of_rows=1
    )

    item = fetch_ok(xml).items[0]
    assert item.name == "둔촌어린이공원"
    assert item.address == "서울 강동구"


def test_drops_items_whose_objt_id_is_blank_or_unparsable():
    xml = response_of(
        item_xml(objt_id=""),
        item_xml(objt_id="not-a-number"),
        SAMPLE_ITEM,
        total_count=3,
        num_of_rows=3,
    )

    page = fetch_ok(xml)
    assert len(page.items) == 1
    assert page.items[0].facility_id == "1741"


def test_drops_items_whose_name_is_blank_because_name_is_not_null():
    xml = response_of(item_xml(objt_id="10", fclty_nm="   "), SAMPLE_ITEM, total_count=2, num_of_rows=2)

    page = fetch_ok(xml)
    assert len(page.items) == 1
    assert page.items[0].facility_id == "1741"


def test_returns_an_empty_item_list_when_items_element_has_no_children():
    page = fetch_ok(
        "<response>"
        "<header><resultCode>00</resultCode><resultMsg>NORMAL_SERVICE</resultMsg></header>"
        "<body><items></items><numOfRows>0</numOfRows><pageNo>90</pageNo>"
        "<totalCount>84251</totalCount></body>"
        "</response>"
    )

    assert page.items == []
    assert page.total_count == 84251


# ── 에러 매핑 ─────────────────────────────────────────────────────────────────


def test_maps_http_200_with_a_non_success_result_code_to_api_call_error():
    error = fetch_error(
        "<response>"
        "<header><resultCode>99</resultCode><resultMsg>SERVICE_ERROR</resultMsg></header>"
        "<body><items></items><numOfRows>0</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body>"
        "</response>"
    )

    assert error == domain_error.ApiCallError(200, "99", "SERVICE_ERROR")


def test_maps_a_missing_header_to_api_call_error_rather_than_silently_succeeding():
    error = fetch_error(
        "<response>"
        "<body><items></items><numOfRows>0</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body>"
        "</response>"
    )

    assert error == domain_error.ApiCallError(200, "", "")


@pytest.mark.parametrize("body", ["", "   \n  "])
def test_maps_an_empty_or_blank_response_body_to_parse_error(body):
    client, _ = build_client(responses=[xml_response(body)])

    result = client.fetch_playgrounds(7, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)
    assert "빈 응답" in result.error.message
    assert "pageNo=7" in result.error.message


def test_maps_malformed_xml_to_parse_error():
    error = fetch_error("<response><header><resultCode>00</resultCode>")

    assert isinstance(error, domain_error.ParseError)


def test_maps_http_401_to_unauthorized():
    client, _ = build_client(responses=[httpx.Response(401)])

    assert client.fetch_playgrounds(1, 1000) == Err(domain_error.Unauthorized())


@pytest.mark.parametrize("status", [400, 500])
def test_maps_http_error_statuses_to_api_call_error_with_the_upstream_status_code(status):
    client, _ = build_client(responses=[httpx.Response(status)])

    result = client.fetch_playgrounds(1, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == status


def test_retries_http_429_three_times_and_then_reports_rate_limit_exceeded():
    client, seen = build_client(responses=[httpx.Response(429) for _ in range(3)])

    result = client.fetch_playgrounds(1, 1000)

    assert result == Err(domain_error.RateLimitExceeded())
    assert len(seen) == 3


def test_recovers_when_a_retry_after_429_succeeds():
    client, seen = build_client(
        responses=[
            httpx.Response(429),
            xml_response(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1)),
        ]
    )

    result = client.fetch_playgrounds(1, 1000)

    assert isinstance(result, Ok)
    assert len(seen) == 2


def test_maps_a_transport_failure_to_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connect timed out", request=request)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    config = SafemapApiConfig(base_url=BASE_URL, service_key="KEY", page_size=1000, request_interval_ms=0)

    result = SafemapApiClient(http, config, retry_delay_ms=0).fetch_playgrounds(1, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.NetworkError)


# ── 요청 파라미터 ──────────────────────────────────────────────────────────────


def test_sends_service_key_page_no_num_of_rows_and_return_type_xml():
    client, seen = build_client(
        responses=[xml_response(response_of(SAMPLE_ITEM, total_count=1, num_of_rows=1))]
    )

    client.fetch_playgrounds(page_no=42, num_of_rows=500)

    url = str(seen[0].url)
    assert "/openapi2/IF_0007" in url
    assert "serviceKey=TEST_SERVICE_KEY" in url
    assert "pageNo=42" in url
    # 인자로 받은 numOfRows 를 쓴다 (설정값을 다시 읽지 않는다)
    assert "numOfRows=500" in url
    assert "returnType=XML" in url
