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
    return ChildcareApiClient(http, config(), retry_delay_ms=0, server_error_retry_delay_ms=0), seen


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

# 태그 대소문자는 실제 응답을 따른다 — 기본 필드는 소문자, 통계 필드와 CRREPNAME 은 대문자
# (2026-11-21 cpmsapi030 실응답 확인)
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
  <CRREPNAME>홍길동</CRREPNAME>
  <crcnfmdt>20100301</crcnfmdt>
  <crpausebegindt></crpausebegindt>
  <crpauseenddt></crpauseenddt>
  <crabldt></crabldt>
  <datastdrdt>20260901</datastdrdt>
  <crspec>시간연장,장애아통합</crspec>
  <CLASS_CNT_00>1</CLASS_CNT_00>
  <CLASS_CNT_01>2</CLASS_CNT_01>
  <CLASS_CNT_M2>0</CLASS_CNT_M2>
  <CLASS_CNT_M3>1</CLASS_CNT_M3>
  <CLASS_CNT_M5>2</CLASS_CNT_M5>
  <CLASS_CNT_TOT>9</CLASS_CNT_TOT>
  <CHILD_CNT_00>3</CHILD_CNT_00>
  <CHILD_CNT_M2>0</CHILD_CNT_M2>
  <CHILD_CNT_M3>7</CHILD_CNT_M3>
  <CHILD_CNT_M5>11</CHILD_CNT_M5>
  <CHILD_CNT_TOT>80</CHILD_CNT_TOT>
  <EM_CNT_0Y>2.5</EM_CNT_0Y>
  <EM_CNT_6Y>1.0</EM_CNT_6Y>
  <EM_CNT_A1>1</EM_CNT_A1>
  <EM_CNT_A10>2</EM_CNT_A10>
  <EM_CNT_TOT>15</EM_CNT_TOT>
  <EW_CNT_00>4</EW_CNT_00>
  <EW_CNT_M6>1</EW_CNT_M6>
  <EW_CNT_TOT>20</EW_CNT_TOT>
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
    assert item.representative_name == "홍길동"


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
    assert item.class_count_age_0 == 1
    assert item.class_count_total == 9
    assert item.child_count_age_0 == 3
    assert item.child_count_total == 80
    assert item.staff_total == 15


def test_maps_mixed_age_classes_without_confusing_m2_m3_m5():
    # M3(영유아혼합, 만2~3세)는 명세서 v1.7 에서 M2·M5 사이에 끼어 들어왔다
    item = fetch_details(response_of(DETAIL_ITEM))[0]

    assert (
        item.class_count_infant_mixed,
        item.class_count_infant_child_mixed,
        item.class_count_child_mixed,
    ) == (0, 1, 2)
    assert (
        item.child_count_infant_mixed,
        item.child_count_infant_child_mixed,
        item.child_count_child_mixed,
    ) == (0, 7, 11)


def test_reads_tags_regardless_of_case():
    # 명세서 예시는 소문자, 실제 응답은 일부 대문자 — 어느 쪽으로 와도 같은 값이어야 한다
    lower = fetch_details(response_of(DETAIL_ITEM.lower()))[0]
    upper = fetch_details(response_of(DETAIL_ITEM))[0]

    assert lower == upper


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
    # 5xx 는 재시도하므로 마지막 시도까지 같은 상태를 돌려준다
    client, _ = build_client(responses=[httpx.Response(status) for _ in range(3)])

    result = client.fetch_sigungu_list("서울특별시")

    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == status


def test_retries_http_429_and_then_reports_rate_limit_exceeded():
    client, seen = build_client(responses=[httpx.Response(429) for _ in range(3)])

    result = client.fetch_sigungu_list("서울특별시")

    assert result == Err(domain_error.RateLimitExceeded())
    assert len(seen) == 3


def test_retries_a_transient_http_500_and_succeeds():
    # 2026-11-22 전체 동기화에서 시군구 6곳이 500 을 냈고 몇 초 뒤 재요청은 모두 성공했다
    client, seen = build_client(responses=[httpx.Response(500), xml(response_of(DETAIL_ITEM))])

    result = client.fetch_daycare_details("11110")

    assert isinstance(result, Ok)
    assert [d.daycare_code for d in result.value] == ["11110000001"]
    assert len(seen) == 2


def test_gives_up_on_http_5xx_after_the_configured_attempts():
    client, seen = build_client(responses=[httpx.Response(503) for _ in range(3)])

    result = client.fetch_daycare_details("11110")

    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == 503
    assert len(seen) == 3


@pytest.mark.parametrize("status", [400, 401, 404])
def test_does_not_retry_http_4xx(status):
    # 클라이언트 오류는 다시 보내도 같다
    client, seen = build_client(responses=[httpx.Response(status), xml(response_of())])

    client.fetch_sigungu_list("서울특별시")

    assert len(seen) == 1


def test_waits_briefly_for_5xx_and_long_for_429():
    sleeps: list[float] = []
    queue = [httpx.Response(500), httpx.Response(429), xml(response_of())]
    http = httpx.Client(transport=httpx.MockTransport(lambda request: queue.pop(0)))
    client = ChildcareApiClient(http, config(), retry_delay_ms=60_000, server_error_retry_delay_ms=3_000)
    client._retrying.sleep = sleeps.append

    assert isinstance(client.fetch_sigungu_list("서울특별시"), Ok)
    assert sleeps == [3.0, 60.0]


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
