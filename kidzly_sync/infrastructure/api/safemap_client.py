"""safemap.go.kr 어린이놀이시설정보(IF_0007) 클라이언트.

odcloud(법정동코드)와의 차이:
- 응답이 XML 이고 구조가 response > body > items > item 이다 (items 래퍼 존재)
- HTTP 200 이어도 header.resultCode 가 "00" 이 아니면 실패다
"""

from __future__ import annotations

import logging
from decimal import Decimal
from urllib.parse import quote
from xml.etree import ElementTree

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from kidzly_sync.application.model import PlaygroundData, PlaygroundPage
from kidzly_sync.config import SafemapApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Err, Ok, Result
from kidzly_sync.infrastructure.api.errors import ApiError, RateLimitError, UnauthorizedError

log = logging.getLogger(__name__)

PATH = "/openapi2/IF_0007"
RESULT_CODE_SUCCESS = "00"


class SafemapApiClient:
    def __init__(
        self,
        http_client: httpx.Client,
        config: SafemapApiConfig,
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

    def fetch_playgrounds(self, page_no: int, num_of_rows: int) -> Result[DomainError, PlaygroundPage]:
        result = self._call_api(page_no, num_of_rows)
        if isinstance(result, Err):
            return result
        return self._to_page(result.value)

    # ── 응답 변환 ─────────────────────────────────────────────────────────────

    def _to_page(self, root: ElementTree.Element) -> Result[DomainError, PlaygroundPage]:
        header = root.find("header")
        # header 자체가 없으면 resultCode 는 빈 문자열이다 — "00" 이 아니므로 실패로 떨어진다.
        # 조용히 성공 처리하면 응답 구조가 바뀐 것을 아무도 알아채지 못한다.
        result_code = _text(header, "resultCode") or ""
        result_msg = _text(header, "resultMsg") or ""
        if result_code != RESULT_CODE_SUCCESS:
            log.error("IF_0007 응답 오류 (resultCode=%s, resultMsg=%s)", result_code, result_msg)
            return Err(domain_error.ApiCallError(200, result_code, result_msg))

        body = root.find("body")
        items_el = body.find("items") if body is not None else None
        items = items_el.findall("item") if items_el is not None else []

        return Ok(
            PlaygroundPage(
                items=[d for item in items if (d := self._to_playground_data(item)) is not None],
                page_no=_int_text(body, "pageNo"),
                num_of_rows=_int_text(body, "numOfRows"),
                total_count=_int_text(body, "totalCount"),
            )
        )

    def _to_playground_data(self, item: ElementTree.Element) -> PlaygroundData | None:
        """식별자 또는 시설명이 없는 아이템은 저장할 수 없으므로 제외한다."""
        facility_id = self._normalize_facility_id(_text(item, "objt_id"))
        if facility_id is None:
            return None
        name = _blank_to_none(_text(item, "fclty_nm"))
        if name is None:
            return None

        return PlaygroundData(
            facility_id=facility_id,
            facility_serial_no=_blank_to_none(_text(item, "fclty_cd1")),
            sido_code=_blank_to_none(_text(item, "ctprvn_cd")),
            sigungu_code=_blank_to_none(_text(item, "sgg_cd")),
            emd_code=_blank_to_none(_text(item, "emd_cd")),
            name=name,
            address=_blank_to_none(_text(item, "adres")),
            coord_x=self._to_decimal(_text(item, "x")),
            coord_y=self._to_decimal(_text(item, "y")),
            install_date=_blank_to_none(_text(item, "instl_de")),
            facility_code1=_blank_to_none(_text(item, "fclty_cd2")),
            facility_code2=_blank_to_none(_text(item, "fclty_cd3")),
            install_place_code=_blank_to_none(_text(item, "fclty_cd4")),
            ownership_code=_blank_to_none(_text(item, "fclty_cd5")),
            indoor_outdoor_code=_blank_to_none(_text(item, "fclty_cd6")),
            operation_code=_blank_to_none(_text(item, "fclty_cd7")),
            accident_yn=_blank_to_none(_text(item, "ac_yn")),
            deleted_yn=_blank_to_none(_text(item, "del_yn")),
        )

    def _normalize_facility_id(self, raw: str | None) -> str | None:
        """objt_id 정규화: "1741.0" → "1741".

        점 앞을 잘라내는 방식은 지수 표기("1.741E3")에서 깨지므로 Decimal 을 경유한다.
        """
        text = _blank_to_none(raw)
        if text is None:
            return None
        try:
            value = Decimal(text)
            if not value.is_finite():
                raise ArithmeticError(text)
            return str(int(value))
        except (ArithmeticError, ValueError):
            log.warning("objt_id 정규화 실패 — 아이템 제외 (objt_id=%s)", raw)
            return None

    def _to_decimal(self, raw: str | None) -> Decimal | None:
        """스케일을 건드리지 않는다. 반올림하면 매 동기화가 UPDATE 로 오탐된다."""
        text = _blank_to_none(raw)
        if text is None:
            return None
        try:
            value = Decimal(text)
            # NaN·Infinity 는 Decimal 이 받아주지만 좌표로는 값이 아니다
            if not value.is_finite():
                raise ArithmeticError(text)
            return value
        except (ArithmeticError, ValueError):
            log.warning("좌표 변환 실패 — null 처리 (value=%s)", raw)
            return None

    # ── HTTP ─────────────────────────────────────────────────────────────────

    def _build_url(self, page_no: int, num_of_rows: int) -> str:
        key = self._config.service_key
        encoded_key = key if "%" in key else quote(key, safe="")
        base = self._config.base_url.rstrip("/")
        return (
            f"{base}{PATH}?serviceKey={encoded_key}&pageNo={page_no}&numOfRows={num_of_rows}&returnType=XML"
        )

    def _call_api(self, page_no: int, num_of_rows: int) -> Result[DomainError, ElementTree.Element]:
        try:
            return self._retrying(self._request_once, page_no, num_of_rows)
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

    def _request_once(self, page_no: int, num_of_rows: int) -> Result[DomainError, ElementTree.Element]:
        log.debug("IF_0007 요청 (pageNo=%d, numOfRows=%d)", page_no, num_of_rows)
        response = self._http.get(self._build_url(page_no, num_of_rows))

        status = response.status_code
        if status == 429:
            raise RateLimitError(f"일 요청 건수 초과 (path={PATH}, pageNo={page_no})")
        if status == 401:
            raise UnauthorizedError(f"인증키가 유효하지 않습니다 (path={PATH})")
        if 400 <= status < 500:
            raise ApiError(status, f"클라이언트 오류 (path={PATH}, pageNo={page_no})")
        if status >= 500:
            raise ApiError(status, f"서버 오류 (path={PATH}, pageNo={page_no})")

        log.debug("IF_0007 응답 상태: %d, Content-Type: %s", status, response.headers.get("content-type"))

        # XML 선언의 encoding 을 존중해야 하므로 str 이 아니라 bytes 로 넘긴다.
        # 누락 시 시설명·주소 한글이 깨진다.
        body = response.content
        if not body.strip():
            return Err(domain_error.ParseError(f"빈 응답 (path={PATH}, pageNo={page_no})"))

        try:
            return Ok(ElementTree.fromstring(body))
        except ElementTree.ParseError as e:
            log.error("XML 파싱 오류: %s", e, exc_info=True)
            return Err(domain_error.ParseError(f"{e} (path={PATH}, pageNo={page_no})", e))


def _text(element: ElementTree.Element | None, tag: str) -> str | None:
    if element is None:
        return None
    child = element.find(tag)
    return child.text if child is not None else None


def _int_text(element: ElementTree.Element | None, tag: str) -> int:
    """응답에 없거나 숫자가 아니면 0 — Kotlin DTO 의 기본값과 같다."""
    text = _blank_to_none(_text(element, tag))
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _blank_to_none(value: str | None) -> str | None:
    """빈 엘리먼트(``<del_yn></del_yn>``)는 None 으로 내려온다."""
    if value is None:
        return None
    text = value.strip()
    return text or None
