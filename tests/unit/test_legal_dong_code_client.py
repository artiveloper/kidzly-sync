"""``LegalDongCodeApiClient`` 의 JSON 파싱 + 에러 매핑 + 요청 파라미터 단위 테스트.

실제 HTTP 대신 :class:`httpx.MockTransport` 로 응답을 주입한다.
"""

from __future__ import annotations

import json

import httpx
import pytest

from kidzly_sync.config import LegalDongCodeApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from kidzly_sync.infrastructure.api.legal_dong_code_client import LegalDongCodeApiClient

BASE_URL = "https://api.odcloud.kr"


def build_client(
    *,
    service_key: str = "TEST_SERVICE_KEY",
    responses: list[httpx.Response] | None = None,
) -> tuple[LegalDongCodeApiClient, list[httpx.Request]]:
    queue = list(responses or [])
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return queue.pop(0) if queue else httpx.Response(200, text="{}")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    config = LegalDongCodeApiConfig(
        base_url=BASE_URL, service_key=service_key, per_page=1000, request_interval_ms=0
    )
    # 재시도 간격은 0 — 대기 시간이 테스트를 멈추게 하지 않는다
    return LegalDongCodeApiClient(http, config, retry_delay_ms=0), seen


def json_response(body: str) -> httpx.Response:
    return httpx.Response(200, content=body.encode("utf-8"), headers={"content-type": "application/json"})


def fetch_ok(body: str, page: int = 1):
    client, _ = build_client(responses=[json_response(body)])
    result = client.fetch_legal_dong_codes(page=page, per_page=1000)
    assert isinstance(result, Ok), result
    return result.value


def fetch_error(body: str, page: int = 1):
    client, _ = build_client(responses=[json_response(body)])
    result = client.fetch_legal_dong_codes(page, 1000)
    assert isinstance(result, Err), result
    return result.error


def item_json(
    code: str = "1111010100",
    name: str = "서울특별시 종로구 청운동",
    abolished_yn: str = "존재",
) -> str:
    return json.dumps({"법정동코드": code, "법정동명": name, "폐지여부": abolished_yn}, ensure_ascii=False)


CHEONGUN_DONG = item_json()
JONGNO_GU = item_json(code="1111000000", name="서울특별시 종로구")


def response_of(*items: str, total_count: int, per_page: int = 1000, page: int = 1) -> str:
    return (
        f'{{"page": {page}, "perPage": {per_page}, "totalCount": {total_count}, '
        f'"currentCount": {len(items)}, "matchCount": {total_count}, "data": [{",".join(items)}]}}'
    )


# ── JSON 파싱 ─────────────────────────────────────────────────────────────────


def test_parses_the_odcloud_envelope_and_its_page_metadata():
    page = fetch_ok(response_of(CHEONGUN_DONG, JONGNO_GU, total_count=49861, per_page=1000, page=1))

    assert len(page.items) == 2
    assert page.page == 1
    assert page.per_page == 1000
    assert page.total_count == 49861


def test_maps_the_korean_json_property_names_onto_the_record_fields():
    record = fetch_ok(response_of(CHEONGUN_DONG, total_count=1)).items[0]

    assert record.code == "1111010100"
    assert record.name == "서울특별시 종로구 청운동"
    assert record.abolished_yn == "존재"


def test_preserves_korean_legal_dong_names_as_utf8():
    page = fetch_ok(response_of(item_json(name="제주특별자치도 서귀포시 대정읍 상모리"), total_count=1))

    assert page.items[0].name == "제주특별자치도 서귀포시 대정읍 상모리"


def test_keeps_abolished_records_because_the_client_does_not_apply_the_business_filter():
    # 폐지여부 필터와 레벨 판별은 UseCase 책임이다
    page = fetch_ok(
        response_of(
            item_json(code="1111010100", abolished_yn="존재"),
            item_json(code="1111010200", abolished_yn="폐지"),
            item_json(code="4173025321", abolished_yn="존재"),  # 리 레벨
            total_count=3,
        )
    )

    assert len(page.items) == 3
    assert [r.abolished_yn for r in page.items] == ["존재", "폐지", "존재"]


def test_trims_surrounding_whitespace_on_every_text_field():
    record = fetch_ok(
        response_of(item_json(code="  1111010100 ", name="  청운동  ", abolished_yn=" 존재 "), total_count=1)
    ).items[0]

    assert record.code == "1111010100"
    assert record.name == "청운동"
    assert record.abolished_yn == "존재"


def test_maps_a_missing_or_blank_abolished_field_to_none_instead_of_an_empty_string():
    assert fetch_ok(response_of(item_json(abolished_yn="   "), total_count=1)).items[0].abolished_yn is None

    body = '{"page":1,"perPage":1000,"totalCount":1,"data":[{"법정동코드":"1111010100","법정동명":"청운동"}]}'
    assert fetch_ok(body).items[0].abolished_yn is None


def test_ignores_unknown_properties_such_as_match_count_and_current_count():
    page = fetch_ok(
        '{"currentCount":1,'
        '"data":[{"법정동코드":"1111010100","법정동명":"청운동","폐지여부":"존재","비고":"x"}],'
        '"matchCount":49861,"page":1,"perPage":1000,"totalCount":49861}'
    )

    assert len(page.items) == 1
    assert page.total_count == 49861


def test_accepts_a_numeric_code_by_coercing_it_to_a_string():
    page = fetch_ok(
        '{"page":1,"perPage":1000,"totalCount":1,'
        '"data":[{"법정동코드":1111010100,"법정동명":"청운동","폐지여부":"존재"}]}'
    )

    assert page.items[0].code == "1111010100"


def test_drops_items_whose_code_is_missing_or_blank():
    page = fetch_ok(
        response_of(
            item_json(code="   "),
            '{"법정동명":"코드 없음","폐지여부":"존재"}',
            CHEONGUN_DONG,
            total_count=3,
        )
    )

    assert len(page.items) == 1
    assert page.items[0].code == "1111010100"


def test_drops_items_whose_name_is_missing_or_blank_because_name_is_not_null():
    page = fetch_ok(
        response_of(
            item_json(code="1111010200", name="  "),
            '{"법정동코드":"1111010300","폐지여부":"존재"}',
            CHEONGUN_DONG,
            total_count=3,
        )
    )

    assert len(page.items) == 1
    assert page.items[0].code == "1111010100"


def test_returns_an_empty_item_list_when_data_is_an_empty_array():
    page = fetch_ok('{"page":51,"perPage":1000,"totalCount":49861,"data":[]}')

    assert page.items == []
    assert page.total_count == 49861


def test_falls_back_to_the_requested_page_number_when_the_response_page_is_zero_or_absent():
    page = fetch_ok(f'{{"perPage":1000,"totalCount":1,"data":[{CHEONGUN_DONG}]}}', page=7)

    assert page.page == 7


# ── 에러 매핑 ─────────────────────────────────────────────────────────────────


def test_maps_a_response_without_the_data_field_to_parse_error():
    error = fetch_error('{"code":"ERROR","msg":"SERVICE KEY IS NOT REGISTERED ERROR"}', page=3)

    assert isinstance(error, domain_error.ParseError)
    assert "data 필드 없음" in error.message
    assert "page=3" in error.message


def test_maps_an_explicit_null_data_field_to_parse_error():
    error = fetch_error('{"page":1,"perPage":1000,"totalCount":0,"data":null}')

    assert isinstance(error, domain_error.ParseError)
    assert "data 필드 없음" in error.message


@pytest.mark.parametrize("body", ["", "   \n  "])
def test_maps_an_empty_or_blank_response_body_to_parse_error(body):
    client, _ = build_client(responses=[json_response(body)])

    result = client.fetch_legal_dong_codes(9, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)
    assert "빈 응답" in result.error.message
    assert "page=9" in result.error.message


def test_maps_malformed_json_to_parse_error():
    assert isinstance(fetch_error('{"page":1,"data":[{"법정동코드":'), domain_error.ParseError)


def test_maps_an_html_error_page_to_parse_error_instead_of_raising():
    assert isinstance(fetch_error("<html><body>Gateway</body></html>"), domain_error.ParseError)


def test_maps_http_401_to_unauthorized():
    client, _ = build_client(responses=[httpx.Response(401)])

    result = client.fetch_legal_dong_codes(1, 1000)

    assert result == Err(domain_error.Unauthorized())


@pytest.mark.parametrize("status", [404, 500])
def test_maps_http_error_statuses_to_api_call_error_with_the_upstream_status_code(status):
    client, _ = build_client(responses=[httpx.Response(status)])

    result = client.fetch_legal_dong_codes(1, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == status
    assert result.error.code is None


def test_retries_http_429_three_times_and_then_reports_rate_limit_exceeded():
    client, seen = build_client(responses=[httpx.Response(429) for _ in range(3)])

    result = client.fetch_legal_dong_codes(1, 1000)

    assert result == Err(domain_error.RateLimitExceeded())
    assert len(seen) == 3


def test_recovers_when_a_retry_after_429_succeeds():
    client, seen = build_client(
        responses=[httpx.Response(429), json_response(response_of(CHEONGUN_DONG, total_count=1))]
    )

    result = client.fetch_legal_dong_codes(1, 1000)

    assert isinstance(result, Ok)
    assert len(seen) == 2


def test_maps_a_transport_failure_to_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connect timed out", request=request)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    config = LegalDongCodeApiConfig(
        base_url=BASE_URL, service_key="KEY", per_page=1000, request_interval_ms=0
    )

    result = LegalDongCodeApiClient(http, config, retry_delay_ms=0).fetch_legal_dong_codes(1, 1000)

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.NetworkError)


# ── 요청 파라미터 ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("service_key", "expected"),
    [
        # '%'가 있으면 이미 인코딩된 값(Encoding 키)으로 판단해 그대로 전송한다
        ("abc%2Bdef%3D", "serviceKey=abc%2Bdef%3D"),
        # '+' 는 query 에서 합법 문자라 라이브러리에 맡기면 인코딩되지 않고,
        # 서버가 query 의 '+' 를 공백으로 디코딩하면 401 이 난다
        ("abc+def=", "serviceKey=abc%2Bdef%3D"),
        ("a/b+c==", "serviceKey=a%2Fb%2Bc%3D%3D"),
        ("PLAIN123key", "serviceKey=PLAIN123key"),
    ],
)
def test_encodes_the_service_key_so_both_key_forms_survive(service_key, expected):
    client, seen = build_client(
        service_key=service_key, responses=[json_response(response_of(CHEONGUN_DONG, total_count=1))]
    )

    client.fetch_legal_dong_codes(1, 1000)

    assert expected in str(seen[0].url)


def test_sends_page_per_page_and_return_type_json_on_the_request_uri():
    client, seen = build_client(responses=[json_response(response_of(CHEONGUN_DONG, total_count=1))])

    client.fetch_legal_dong_codes(page=42, per_page=500)

    url = str(seen[0].url)
    assert "/api/15123287/v1/uddi:" in url
    assert "page=42" in url
    # 인자로 받은 perPage 를 쓴다 (설정값을 다시 읽지 않는다)
    assert "perPage=500" in url
    assert "returnType=JSON" in url
