"""``ChildcareApiClient`` 의 XML 파싱 + 73개 필드 매핑 + 에러 매핑 단위 테스트."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import httpx
import pytest

from kidzly_sync.application.model import DaycareData
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from kidzly_sync.infrastructure.api import childcare_client as cc
from kidzly_sync.infrastructure.api.childcare_client import ChildcareApiClient
from tests.unit.childcare_fixtures import config


def build_client(
    responses: list[httpx.Response] | None = None,
) -> tuple[ChildcareApiClient, list[httpx.Request]]:
    queue = list(responses or [])
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return queue.pop(0) if queue else httpx.Response(200, text="<response/>")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return ChildcareApiClient(http, config(), retry_delay_ms=0), seen


def xml(body: str) -> httpx.Response:
    return httpx.Response(200, content=body.encode("utf-8"), headers={"content-type": "text/xml"})


def response_of(*items: str) -> str:
    return "<?xml version='1.0' encoding='UTF-8'?><response>" + "".join(items) + "</response>"


# ── 매핑 완전성 ───────────────────────────────────────────────────────────────


def test_every_daycare_field_is_covered_by_exactly_one_mapping():
    """필드를 추가하고 매핑을 빠뜨리면 여기서 걸린다 — 컬럼이 73개라 눈으로는 못 잡는다."""
    fields = {f.name for f in dataclasses.fields(DaycareData)}
    mapped = set(cc._TEXT_FIELDS) | set(cc._INT_FIELDS) | set(cc._FLOAT_FIELDS) | set(cc._DECIMAL_FIELDS)
    # 이 둘은 XML 이 아니라 요청 인자와 필터에서 온다
    derived = {"daycare_code", "sigungu_code"}

    assert mapped | derived == fields
    assert not (mapped & derived)


def test_no_xml_tag_is_mapped_twice():
    tags = (
        list(cc._TEXT_FIELDS.values())
        + list(cc._INT_FIELDS.values())
        + list(cc._FLOAT_FIELDS.values())
        + list(cc._DECIMAL_FIELDS.values())
    )
    assert len(tags) == len(set(tags))


# ── cpmsapi030 파싱 ───────────────────────────────────────────────────────────

DETAIL_ITEM = """<item>
  <stcode>11110000001</stcode>
  <sidoname>서울특별시</sidoname>
  <sigunname>종로구</sigunname>
  <crname>청운어린이집</crname>
  <crtypename>국공립</crtypename>
  <crstatusname>정상</crstatusname>
  <zipcode>03047</zipcode>
  <craddr>서울특별시 종로구 청운동 1</craddr>
  <crtelno>02-000-0000</crtelno>
  <crfaxno></crfaxno>
  <crhome>http://example.kr</crhome>
  <la>37.5869</la>
  <lo>126.9690</lo>
  <crcapat>99</crcapat>
  <crchcnt>80</crchcnt>
  <nrtrroomcnt>5</nrtrroomcnt>
  <nrtrroomsize>250.75</nrtrroomsize>
  <plgrdco>1</plgrdco>
  <cctvinstlcnt>12</cctvinstlcnt>
  <chcrtescnt>15</chcrtescnt>
  <crcargbname>없음</crcargbname>
  <crrepname>홍길동</crrepname>
  <crcnfmdt>20100301</crcnfmdt>
  <crpausebegindt></crpausebegindt>
  <crpauseenddt></crpauseenddt>
  <crabldt></crabldt>
  <datastdrdt>20260901</datastdrdt>
  <crspec>시간연장,장애아통합</crspec>
  <class_cnt_00>1</class_cnt_00>
  <class_cnt_01>2</class_cnt_01>
  <class_cnt_tot>9</class_cnt_tot>
  <child_cnt_00>3</child_cnt_00>
  <child_cnt_tot>80</child_cnt_tot>
  <em_cnt_0y>2.5</em_cnt_0y>
  <em_cnt_6y>1.0</em_cnt_6y>
  <em_cnt_a1>1</em_cnt_a1>
  <em_cnt_a10>2</em_cnt_a10>
  <em_cnt_tot>15</em_cnt_tot>
  <ew_cnt_00>4</ew_cnt_00>
  <ew_cnt_m6>1</ew_cnt_m6>
  <ew_cnt_tot>20</ew_cnt_tot>
</item>"""


def fetch_details(body: str, arcode: str = "11110"):
    client, _ = build_client(responses=[xml(body)])
    result = client.fetch_daycare_details(arcode)
    assert isinstance(result, Ok), result
    return result.value


def test_maps_the_identifier_and_the_requested_sigungu_code():
    item = fetch_details(response_of(DETAIL_ITEM), arcode="11110")[0]

    assert item.daycare_code == "11110000001"
    # 응답에 없는 값 — 요청 인자에서 온다
    assert item.sigungu_code == "11110"


def test_maps_text_fields():
    item = fetch_details(response_of(DETAIL_ITEM))[0]

    assert item.sido_name == "서울특별시"
    assert item.sigungu_name == "종로구"
    assert item.name == "청운어린이집"
    assert item.type_name == "국공립"
    assert item.status == "정상"
    assert item.address == "서울특별시 종로구 청운동 1"
    assert item.latitude == "37.5869"
    assert item.services == "시간연장,장애아통합"


def test_maps_numeric_fields_with_their_types():
    item = fetch_details(response_of(DETAIL_ITEM))[0]

    assert item.capacity == 99
    assert item.cctv_count == 12
    assert item.nursery_room_size == Decimal("250.75")
    assert item.staff_tenure_under_1y == 2.5
    assert item.staff_nursing_assistant_count == 2  # em_cnt_a10 — a1 과 헷갈리기 쉽다
    assert item.staff_director_count == 1
    assert item.waiting_child_age_over_6 == 1
    assert item.waiting_child_total == 20


def test_distinguishes_an_absent_element_from_an_empty_one():
    # IS DISTINCT FROM 가드에서 NULL 과 '' 은 다른 값이다
    item = fetch_details(response_of(DETAIL_ITEM))[0]

    assert item.fax == ""  # <crfaxno></crfaxno> 가 있다
    assert item.homepage == "http://example.kr"
    assert item.vehicle_operation == "없음"
    # 응답에 아예 없는 엘리먼트
    assert item.class_count_age_5 is None
    assert item.child_count_special is None


def test_maps_empty_numeric_elements_to_none():
    item = fetch_details(response_of(DETAIL_ITEM))[0]

    assert item.pause_start_date == ""
    assert item.abolished_date == ""


def test_drops_items_without_a_stcode():
    body = response_of(
        "<item><crname>코드 없음</crname></item>",
        "<item><stcode>  </stcode></item>",
        DETAIL_ITEM,
    )

    items = fetch_details(body)

    assert len(items) == 1
    assert items[0].daycare_code == "11110000001"


def test_returns_an_empty_list_when_the_response_has_no_items():
    assert fetch_details(response_of()) == []


def test_fails_the_whole_page_when_a_numeric_field_is_malformed():
    # 조용히 null 로 채우면 잘못된 값이 그대로 저장된다 — 이 시군구 전체를 실패로 돌린다
    body = response_of(DETAIL_ITEM.replace("<crcapat>99</crcapat>", "<crcapat>없음</crcapat>"))
    client, _ = build_client(responses=[xml(body)])

    result = client.fetch_daycare_details("11110")

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)


# ── cpmsapi020 / 018 / 019 ────────────────────────────────────────────────────


def test_parses_the_sigungu_list():
    body = response_of(
        "<item><sidoname>서울특별시</sidoname><sigunname>종로구</sigunname><arcode>11110</arcode></item>",
        "<item><sidoname>서울특별시</sidoname><sigunname>중구</sigunname><arcode>11140</arcode></item>",
    )
    client, _ = build_client(responses=[xml(body)])

    result = client.fetch_sigungu_list("서울특별시")

    assert isinstance(result, Ok)
    assert [(s.arcode, s.sigunname) for s in result.value] == [("11110", "종로구"), ("11140", "중구")]


def test_parses_the_new_daycare_list_and_drops_rows_without_a_code():
    body = response_of(
        "<item><stcode>A1</stcode><arcode>11110</arcode><crname>신규</crname></item>",
        "<item><arcode>11140</arcode><crname>코드 없음</crname></item>",
    )
    client, _ = build_client(responses=[xml(body)])

    result = client.fetch_new_daycares("202603")

    assert isinstance(result, Ok)
    assert [(n.daycare_code, n.sigungu_code) for n in result.value] == [("A1", "11110")]


def test_parses_the_closed_daycare_list_with_its_abolished_date():
    body = response_of(
        "<item><stcode>B1</stcode><arcode>11110</arcode><crstdate>20260315</crstdate></item>",
        "<item><stcode>B2</stcode><arcode>11110</arcode></item>",
    )
    client, _ = build_client(responses=[xml(body)])

    result = client.fetch_closed_daycares("202603")

    assert isinstance(result, Ok)
    assert [(c.daycare_code, c.abolished_date) for c in result.value] == [
        ("B1", "20260315"),
        ("B2", None),
    ]


# ── 에러 매핑 ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("body", [b"", b"   \n  "])
def test_maps_an_empty_response_body_to_parse_error(body):
    client, _ = build_client(responses=[httpx.Response(200, content=body)])

    result = client.fetch_sigungu_list("서울특별시")

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)
    assert "빈 응답" in result.error.message


def test_maps_malformed_xml_to_parse_error():
    client, _ = build_client(responses=[xml("<response><item>")])

    result = client.fetch_sigungu_list("서울특별시")

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)


def test_maps_http_401_to_unauthorized():
    client, _ = build_client(responses=[httpx.Response(401)])

    assert client.fetch_sigungu_list("서울특별시") == Err(domain_error.Unauthorized())


@pytest.mark.parametrize("status", [400, 404, 500])
def test_maps_http_error_statuses_to_api_call_error(status):
    client, _ = build_client(responses=[httpx.Response(status)])

    result = client.fetch_sigungu_list("서울특별시")

    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == status


def test_retries_http_429_and_then_reports_rate_limit_exceeded():
    client, seen = build_client(responses=[httpx.Response(429) for _ in range(3)])

    result = client.fetch_sigungu_list("서울특별시")

    assert result == Err(domain_error.RateLimitExceeded())
    assert len(seen) == 3


# ── 요청 파라미터 ──────────────────────────────────────────────────────────────


def test_each_api_uses_its_own_key_and_path():
    cases = [
        (lambda c: c.fetch_sigungu_list("서울특별시"), cc.SIGUNGU_PATH, "key=K020", "arname="),
        (lambda c: c.fetch_daycare_details("11110"), cc.DAYCARE_DETAIL_PATH, "key=K030", "arcode=11110"),
        (lambda c: c.fetch_new_daycares("202603"), cc.NEW_DAYCARE_PATH, "key=K018", "yyyymm=202603"),
        (lambda c: c.fetch_closed_daycares("202603"), cc.CLOSED_DAYCARE_PATH, "key=K019", "yyyymm=202603"),
    ]
    for call, path, key, param in cases:
        client, seen = build_client(responses=[xml(response_of())])
        call(client)
        url = str(seen[0].url)
        assert path in url
        assert key in url
        assert param in url


def test_percent_encodes_the_korean_sido_name_in_the_query():
    client, seen = build_client(responses=[xml(response_of())])

    client.fetch_sigungu_list("서울특별시")

    assert "arname=%EC%84%9C%EC%9A%B8" in str(seen[0].url)
