"""``AbstractAiApiClient`` 재시도 / 에러 변환 단위 테스트."""

from __future__ import annotations

import httpx

from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from kidzly_sync.infrastructure.ai.abstract_client import MAX_RETRIES, AbstractAiApiClient
from tests.unit.childcare_fixtures import daycare

VALID_JSON = '{"summary": "요약", "who_may_be_interested": ["A"], "things_to_consider": ["B"]}'


def _status_error(status_code: int, body: str = "") -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/x")
    response = httpx.Response(status_code, text=body, request=request)
    return httpx.HTTPStatusError(str(status_code), request=request, response=response)


class FakeClient(AbstractAiApiClient):
    provider_name = "Fake"
    request_interval_ms = 0

    def __init__(self, responses: list[object], retry_after_ms: int = 5_000) -> None:
        self._responses = list(responses)
        self._retry_after_ms = retry_after_ms
        self.execute_calls = 0

    def _execute_request(self, prompt: str) -> str | None:
        self.execute_calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def _parse_retry_after_ms(self, response_body: str) -> int:
        return self._retry_after_ms


# ── 성공 ──────────────────────────────────────────────────────────────────────


def test_parses_a_successful_response_into_a_daycare_summary():
    result = FakeClient(responses=[VALID_JSON]).generate_summary(daycare("A"))

    assert isinstance(result, Ok)
    assert result.value.summary == "요약"
    assert result.value.who_may_be_interested == ["A"]
    assert result.value.things_to_consider == ["B"]


# ── 에러 변환 ─────────────────────────────────────────────────────────────────


def test_treats_a_none_response_as_an_empty_response_error():
    result = FakeClient(responses=[None]).generate_summary(daycare("A"))

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.Unknown)
    assert "empty response" in result.error.message


def test_wraps_a_non_429_http_error_as_an_api_call_error():
    result = FakeClient(responses=[_status_error(500)]).generate_summary(daycare("A"))

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == 500


def test_wraps_an_unexpected_exception_as_unknown():
    result = FakeClient(responses=[RuntimeError("boom")]).generate_summary(daycare("A"))

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.Unknown)
    assert "boom" in result.error.message


def test_a_malformed_json_response_is_wrapped_as_unknown_rather_than_crashing():
    result = FakeClient(responses=["이것은 JSON이 아니다"]).generate_summary(daycare("A"))

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.Unknown)


# ── 429 재시도 ────────────────────────────────────────────────────────────────


def test_retries_a_429_and_succeeds_on_the_next_attempt(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(
        "kidzly_sync.infrastructure.ai.abstract_client.time.sleep", lambda s: sleeps.append(s)
    )
    client = FakeClient(responses=[_status_error(429), VALID_JSON], retry_after_ms=2_000)

    result = client.generate_summary(daycare("A"))

    assert isinstance(result, Ok)
    assert client.execute_calls == 2
    assert sleeps == [2.0]


def test_gives_up_after_max_retries_and_reports_the_last_429_as_an_api_call_error(monkeypatch):
    monkeypatch.setattr("kidzly_sync.infrastructure.ai.abstract_client.time.sleep", lambda s: None)
    # 최초 호출(attempt=1) + MAX_RETRIES 번 재시도 = 총 MAX_RETRIES+1 번 호출하고도 전부 429
    client = FakeClient(responses=[_status_error(429) for _ in range(MAX_RETRIES + 1)])

    result = client.generate_summary(daycare("A"))

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ApiCallError)
    assert result.error.status_code == 429
    assert client.execute_calls == MAX_RETRIES + 1
