"""odcloud.kr 법정동코드 조회 클라이언트.

safemap(IF_0007)과의 차이:
- 응답이 JSON이고 header/resultCode 래퍼가 없다 — 실패는 HTTP 상태로만 전달된다
- 폐지여부 필터와 레벨 판별은 여기서 하지 않는다 (UseCase 책임)
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import quote

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from kidzly_sync.application.model import LegalDongCodePage, LegalDongCodeRecord
from kidzly_sync.config import LegalDongCodeApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Err, Ok, Result
from kidzly_sync.infrastructure.api.errors import ApiError, RateLimitError, UnauthorizedError

log = logging.getLogger(__name__)

PATH = "/api/15123287/v1/uddi:b68902fa-d058-4a17-b188-ff46b7eaaac7"
"""데이터셋 판(edition)이 바뀌면 무효가 된다 — 404 발생 시 이 상수를 갱신할 것"""


class LegalDongCodeApiClient:
    def __init__(
        self,
        http_client: httpx.Client,
        config: LegalDongCodeApiConfig,
        retry_max_attempts: int = 3,
        retry_delay_ms: int = 60_000,
    ) -> None:
        self._http = http_client
        self._config = config
        self._retrying = Retrying(
            retry=retry_if_exception_type(RateLimitError),
            stop=stop_after_attempt(retry_max_attempts),
            wait=wait_fixed(retry_delay_ms / 1000),
            reraise=True,
        )

    def fetch_legal_dong_codes(self, page: int, per_page: int) -> Result[DomainError, LegalDongCodePage]:
        result = self._call_api(page, per_page)
        if isinstance(result, Err):
            return result
        return self._to_page(result.value, requested_page=page)

    # ── 응답 변환 ─────────────────────────────────────────────────────────────

    def _to_page(self, payload: Any, requested_page: int) -> Result[DomainError, LegalDongCodePage]:
        # odcloud는 에러 바디에도 HTTP 200을 주는 판이 있어 data 누락을 방어한다
        if not isinstance(payload, dict) or payload.get("data") is None:
            return Err(domain_error.ParseError(f"data 필드 없음 (page={requested_page})"))

        items = payload["data"]
        if not isinstance(items, list):
            return Err(domain_error.ParseError(f"data 필드 형식 오류 (page={requested_page})"))

        response_page = _as_int(payload.get("page"))
        return Ok(
            LegalDongCodePage(
                items=[r for item in items if (r := self._to_record(item)) is not None],
                page=response_page if response_page > 0 else requested_page,
                per_page=_as_int(payload.get("perPage")),
                total_count=_as_int(payload.get("totalCount")),
            )
        )

    def _to_record(self, item: Any) -> LegalDongCodeRecord | None:
        """코드 또는 법정동명이 없는 아이템은 저장할 수 없으므로 제외한다."""
        if not isinstance(item, dict):
            return None

        name = _blank_to_none(item.get("법정동명"))
        code = _blank_to_none(item.get("법정동코드"))
        if code is None:
            log.warning("법정동코드 없음 — 아이템 제외 (법정동명=%s)", name)
            return None
        if name is None:
            log.warning("법정동명 없음 — 아이템 제외 (법정동코드=%s)", code)
            return None

        return LegalDongCodeRecord(code=code, name=name, abolished_yn=_blank_to_none(item.get("폐지여부")))

    # ── HTTP ─────────────────────────────────────────────────────────────────

    def _build_url(self, page: int, per_page: int) -> str:
        """serviceKey를 직접 percent-encode 한 뒤 **pre-encoded URL** 로 넘긴다.

        인코딩을 HTTP 라이브러리에 맡기면 ``=`` 는 인코딩되지만 ``+`` 는 query 합법 문자라
        그대로 전송되고, 서버가 query 의 ``+`` 를 공백으로 디코딩하면 ``+`` 가 든 Decoding 키는
        401 이 난다.

        공공데이터포털은 Encoding 키(이미 ``%2B`` 등으로 인코딩된 형태)와 Decoding 키(원문)를
        둘 다 발급하는데, 운영자가 어느 쪽을 등록할지 코드가 강제하지 않는다 — 이미 인코딩된 값은
        Base64 알파벳(``A-Za-z0-9+/=``)에 없는 ``%`` 를 반드시 포함하므로, 그 유무로 자동 판별해
        두 형태 모두 그대로 붙여넣으면 동작하게 한다.
        """
        key = self._config.service_key
        encoded_key = key if "%" in key else quote(key, safe="")
        base = self._config.base_url.rstrip("/")
        return f"{base}{PATH}?serviceKey={encoded_key}&page={page}&perPage={per_page}&returnType=JSON"

    def _call_api(self, page: int, per_page: int) -> Result[DomainError, Any]:
        try:
            return self._retrying(self._request_once, page, per_page)
        except RateLimitError as e:
            log.warning("Rate limit 초과 — 재시도를 모두 소진했습니다: %s", e)
            return Err(domain_error.RateLimitExceeded())
        except UnauthorizedError as e:
            log.error("인증 실패: %s", e)
            return Err(domain_error.Unauthorized())
        except ApiError as e:
            log.error("API 오류 (%d): %s", e.status_code, e)
            return Err(domain_error.ApiCallError(e.status_code, None, str(e)))
        except httpx.RequestError as e:
            log.error("네트워크 오류: %s", e, exc_info=True)
            return Err(domain_error.NetworkError(str(e), e))

    def _request_once(self, page: int, per_page: int) -> Result[DomainError, Any]:
        log.debug("법정동코드 요청 (page=%d, perPage=%d)", page, per_page)
        response = self._http.get(self._build_url(page, per_page))

        status = response.status_code
        if status == 429:
            raise RateLimitError(f"일 요청 건수 초과 (path={PATH}, page={page})")
        if status == 401:
            raise UnauthorizedError(f"인증키가 유효하지 않습니다 (path={PATH})")
        if 400 <= status < 500:
            raise ApiError(status, f"클라이언트 오류 (path={PATH}, page={page})")
        if status >= 500:
            raise ApiError(status, f"서버 오류 (path={PATH}, page={page})")

        log.debug("법정동코드 응답 상태: %d, Content-Type: %s", status, response.headers.get("content-type"))

        # 누락 시 법정동명 한글이 ISO-8859-1로 깨진다
        body = response.content.decode("utf-8", errors="replace")
        if not body.strip():
            return Err(domain_error.ParseError(f"빈 응답 (path={PATH}, page={page})"))

        try:
            return Ok(json.loads(body))
        except ValueError as e:
            log.error("JSON 파싱 오류: %s", e, exc_info=True)
            return Err(domain_error.ParseError(str(e), e))


def _as_int(value: Any) -> int:
    """응답에 없거나 숫자가 아니면 0 — Kotlin DTO 의 기본값과 같다."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _blank_to_none(value: Any) -> str | None:
    """숫자로 온 법정동코드도 문자열로 받아 준다 (Jackson 의 강제 변환과 동일)."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
