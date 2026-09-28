"""childcare.go.kr(보육통합정보시스템) 클라이언트 — cpmsapi018/019/020/030.

safemap(IF_0007)과의 차이:
- 응답이 response > item 평면 구조다 (items 래퍼가 없다)
- header/resultCode 래퍼가 없어 실패는 HTTP 상태로만 전달된다
- API 마다 인증키가 다르다
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from typing import TypeVar
from urllib.parse import quote
from xml.etree import ElementTree

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from kidzly_sync.application.model import (
    ClosedDaycareInfo,
    DaycareData,
    NewDaycareInfo,
    SigunguInfo,
)
from kidzly_sync.config import ChildcareApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Err, Ok, Result
from kidzly_sync.infrastructure.api.errors import ApiError, RateLimitError, UnauthorizedError

log = logging.getLogger(__name__)

T = TypeVar("T")

SIGUNGU_PATH = "/mediate/rest/cpmsapi020/cpmsapi020/request"
DAYCARE_DETAIL_PATH = "/mediate/rest/cpmsapi030/cpmsapi030/request"
NEW_DAYCARE_PATH = "/mediate/rest/cpmsapi018/cpmsapi018/request"
CLOSED_DAYCARE_PATH = "/mediate/rest/cpmsapi019/cpmsapi019/request"

# ── cpmsapi030 필드 매핑 ──────────────────────────────────────────────────────
# 왼쪽이 DaycareData 필드(=DB 컬럼), 오른쪽이 XML 엘리먼트 이름이다.
# sigungu_code 는 응답에 없고 요청 인자(arcode)에서 온다.

_TEXT_FIELDS: dict[str, str] = {
    "sido_name": "sidoname",
    "sigungu_name": "sigunname",
    "name": "crname",
    "type_name": "crtypename",
    "status": "crstatusname",
    "zip_code": "zipcode",
    "address": "craddr",
    "phone": "crtelno",
    "fax": "crfaxno",
    "homepage": "crhome",
    "latitude": "la",
    "longitude": "lo",
    "vehicle_operation": "crcargbname",
    "representative_name": "crrepname",
    "certified_date": "crcnfmdt",
    "pause_start_date": "crpausebegindt",
    "pause_end_date": "crpauseenddt",
    "abolished_date": "crabldt",
    "data_standard_date": "datastdrdt",
    "services": "crspec",
}

_INT_FIELDS: dict[str, str] = {
    "capacity": "crcapat",
    "current_child_count": "crchcnt",
    "nursery_room_count": "nrtrroomcnt",
    "playground_count": "plgrdco",
    "cctv_count": "cctvinstlcnt",
    "childcare_staff_count": "chcrtescnt",
    "class_count_age_0": "class_cnt_00",
    "class_count_age_1": "class_cnt_01",
    "class_count_age_2": "class_cnt_02",
    "class_count_age_3": "class_cnt_03",
    "class_count_age_4": "class_cnt_04",
    "class_count_age_5": "class_cnt_05",
    "class_count_infant_mixed": "class_cnt_m2",
    "class_count_child_mixed": "class_cnt_m5",
    "class_count_special": "class_cnt_sp",
    "class_count_total": "class_cnt_tot",
    "child_count_age_0": "child_cnt_00",
    "child_count_age_1": "child_cnt_01",
    "child_count_age_2": "child_cnt_02",
    "child_count_age_3": "child_cnt_03",
    "child_count_age_4": "child_cnt_04",
    "child_count_age_5": "child_cnt_05",
    "child_count_infant_mixed": "child_cnt_m2",
    "child_count_child_mixed": "child_cnt_m5",
    "child_count_special": "child_cnt_sp",
    "child_count_total": "child_cnt_tot",
    "staff_director_count": "em_cnt_a1",
    "staff_teacher_count": "em_cnt_a2",
    "staff_special_teacher_count": "em_cnt_a3",
    "staff_therapist_count": "em_cnt_a4",
    "staff_nutritionist_count": "em_cnt_a5",
    "staff_nurse_count": "em_cnt_a6",
    "staff_nursing_assistant_count": "em_cnt_a10",
    "staff_cook_count": "em_cnt_a7",
    "staff_office_count": "em_cnt_a8",
    "staff_total": "em_cnt_tot",
    "waiting_child_age_0": "ew_cnt_00",
    "waiting_child_age_1": "ew_cnt_01",
    "waiting_child_age_2": "ew_cnt_02",
    "waiting_child_age_3": "ew_cnt_03",
    "waiting_child_age_4": "ew_cnt_04",
    "waiting_child_age_5": "ew_cnt_05",
    "waiting_child_age_over_6": "ew_cnt_m6",
    "waiting_child_total": "ew_cnt_tot",
}

_FLOAT_FIELDS: dict[str, str] = {
    "staff_tenure_under_1y": "em_cnt_0y",
    "staff_tenure_1y_to_2y": "em_cnt_1y",
    "staff_tenure_2y_to_4y": "em_cnt_2y",
    "staff_tenure_4y_to_6y": "em_cnt_4y",
    "staff_tenure_over_6y": "em_cnt_6y",
}

_DECIMAL_FIELDS: dict[str, str] = {
    "nursery_room_size": "nrtrroomsize",
}


class ChildcareApiClient:
    def __init__(
        self,
        http_client: httpx.Client,
        config: ChildcareApiConfig,
        retry_max_attempts: int | None = None,
        retry_delay_ms: int | None = None,
    ) -> None:
        self._http = http_client
        self._config = config
        self._retrying = Retrying(
            retry=retry_if_exception_type(RateLimitError),
            stop=stop_after_attempt(retry_max_attempts or config.retry_max_attempts),
            wait=wait_fixed((retry_delay_ms if retry_delay_ms is not None else config.retry_delay_ms) / 1000),
            reraise=True,
        )

    # ── Port 구현 ─────────────────────────────────────────────────────────────

    def fetch_sigungu_list(self, arname: str) -> Result[DomainError, list[SigunguInfo]]:
        """시도명으로 시군구 목록 조회 (cpmsapi020)."""
        return self._call_api(
            SIGUNGU_PATH,
            self._config.key_sigungu,
            {"arname": arname},
            lambda root: [
                SigunguInfo(
                    arcode=_text(item, "arcode") or "",
                    sidoname=_text(item, "sidoname") or "",
                    sigunname=_text(item, "sigunname") or "",
                )
                for item in root.findall("item")
            ],
        )

    def fetch_daycare_details(self, arcode: str) -> Result[DomainError, list[DaycareData]]:
        """시군구코드로 어린이집 상세 목록 조회 (cpmsapi030)."""
        return self._call_api(
            DAYCARE_DETAIL_PATH,
            self._config.key_daycare_detail,
            {"arcode": arcode},
            lambda root: [
                _to_daycare_data(item, arcode)
                for item in root.findall("item")
                if (_text(item, "stcode") or "").strip()
            ],
        )

    def fetch_new_daycares(self, yyyymm: str) -> Result[DomainError, list[NewDaycareInfo]]:
        """월별 신규시설 목록 조회 (cpmsapi018)."""
        return self._call_api(
            NEW_DAYCARE_PATH,
            self._config.key_new_daycare,
            {"yyyymm": yyyymm},
            lambda root: [
                NewDaycareInfo(daycare_code=code, sigungu_code=_text(item, "arcode") or "")
                for item in root.findall("item")
                if (code := (_text(item, "stcode") or "").strip())
            ],
        )

    def fetch_closed_daycares(self, yyyymm: str) -> Result[DomainError, list[ClosedDaycareInfo]]:
        """월별 폐지시설 목록 조회 (cpmsapi019)."""
        return self._call_api(
            CLOSED_DAYCARE_PATH,
            self._config.key_closed_daycare,
            {"yyyymm": yyyymm},
            lambda root: [
                ClosedDaycareInfo(daycare_code=code, abolished_date=_text(item, "crstdate"))
                for item in root.findall("item")
                if (code := (_text(item, "stcode") or "").strip())
            ],
        )

    # ── HTTP ─────────────────────────────────────────────────────────────────

    def _build_url(self, path: str, key: str, params: dict[str, str]) -> str:
        query = "&".join(
            [f"key={quote(key, safe='')}"] + [f"{k}={quote(v, safe='')}" for k, v in params.items()]
        )
        return f"{self._config.base_url.rstrip('/')}{path}?{query}"

    def _call_api(
        self,
        path: str,
        key: str,
        params: dict[str, str],
        parse: Callable[[ElementTree.Element], T],
    ) -> Result[DomainError, T]:
        try:
            result = self._retrying(self._request_once, path, key, params)
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

        if isinstance(result, Err):
            return result

        try:
            return Ok(parse(result.value))
        except (ElementTree.ParseError, ValueError, InvalidOperation) as e:
            # 숫자 필드가 깨진 응답은 이 시군구 전체를 실패로 돌린다.
            # 조용히 null 로 채우면 잘못된 값이 그대로 저장된다.
            log.error("XML 파싱 오류: %s", e, exc_info=True)
            return Err(domain_error.ParseError(f"{e} (path={path})", e))

    def _request_once(self, path: str, key: str, params: dict[str, str]) -> Result[DomainError, object]:
        url = self._build_url(path, key, params)
        log.debug("API 요청 (path=%s, params=%s)", path, params)
        response = self._http.get(url)

        status = response.status_code
        if status == 429:
            raise RateLimitError(f"일 요청 건수 초과 (path={path})")
        if status == 401:
            raise UnauthorizedError(f"인증키가 유효하지 않습니다 (path={path})")
        if 400 <= status < 500:
            raise ApiError(status, f"클라이언트 오류 (path={path})")
        if status >= 500:
            raise ApiError(status, f"서버 오류 (path={path})")

        log.debug("API 응답 상태: %d, Content-Type: %s", status, response.headers.get("content-type"))

        body = response.content
        if not body.strip():
            return Err(domain_error.ParseError(f"빈 응답 (path={path})"))

        try:
            return Ok(ElementTree.fromstring(body))
        except ElementTree.ParseError as e:
            log.error("XML 파싱 오류: %s", e, exc_info=True)
            return Err(domain_error.ParseError(f"{e} (path={path})", e))


# ── cpmsapi030 → DaycareData ─────────────────────────────────────────────────


def _to_daycare_data(item: ElementTree.Element, sigungu_code: str) -> DaycareData:
    values: dict[str, object] = {
        "daycare_code": (_text(item, "stcode") or "").strip(),
        "sigungu_code": sigungu_code,
    }
    for field, tag in _TEXT_FIELDS.items():
        values[field] = _text(item, tag)
    for field, tag in _INT_FIELDS.items():
        values[field] = _to_int(_text(item, tag))
    for field, tag in _FLOAT_FIELDS.items():
        values[field] = _to_float(_text(item, tag))
    for field, tag in _DECIMAL_FIELDS.items():
        values[field] = _to_decimal(_text(item, tag))
    # name 은 NOT NULL 이라 빈 값이면 빈 문자열로 둔다 (Kotlin DTO 의 기본값과 같다)
    values["name"] = values["name"] or ""
    return DaycareData(**values)  # type: ignore[arg-type]


def _text(element: ElementTree.Element, tag: str) -> str | None:
    """엘리먼트 부재와 빈 엘리먼트를 구분한다.

    safemap 클라이언트와 달리 여기서는 문자열을 trim 하지 않는다 — Kotlin 쪽도
    Jackson 이 읽은 값을 그대로 DaycareData 에 넣었다.

    구분이 중요한 이유: ``IS DISTINCT FROM`` 가드에서 NULL 과 '' 은 다른 값이다.
    - 엘리먼트가 아예 없으면 Kotlin DTO 의 기본값(null)이 남는다 → None
    - ``<crfaxno></crfaxno>`` 는 Jackson 이 빈 문자열로 읽는다 → ''
      (EMPTY_ELEMENT_AS_NULL 을 켜지 않았으므로 null 이 아니다)
    """
    child = element.find(tag)
    if child is None:
        return None
    return child.text if child.text is not None else ""


def _blank_to_none(value: str | None) -> str | None:
    """빈 엘리먼트는 None 으로 본다 (Jackson 의 ACCEPT_EMPTY_STRING_AS_NULL_OBJECT)."""
    if value is None:
        return None
    return value.strip() or None


def _to_int(value: str | None) -> int | None:
    text = _blank_to_none(value)
    return None if text is None else int(text)


def _to_float(value: str | None) -> float | None:
    text = _blank_to_none(value)
    return None if text is None else float(text)


def _to_decimal(value: str | None) -> Decimal | None:
    text = _blank_to_none(value)
    return None if text is None else Decimal(text)
