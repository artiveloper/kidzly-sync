"""AI 요약 생성 베이스 클라이언트.

재시도(429)·프롬프트 템플릿 적용·JSON 파싱을 여기서 공통으로 처리하고,
구현체는 실제 HTTP 호출(``_execute_request``)과 429 응답 바디 파싱만 맡는다.
Kotlin ``AbstractAiApiClient`` 와 1:1 대응한다.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from importlib import resources

import httpx

from kidzly_sync.application.model import DaycareData, DaycareSummary
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Err, Ok, Result
from kidzly_sync.infrastructure.ai import daycare_json_builder

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BUFFER_MS = 1_000
DEFAULT_RETRY_WAIT_MS = 30_000
"""응답 본문에 retryDelay 가 없을 때 fallback"""

_PROMPT_TEMPLATE = (
    resources.files("kidzly_sync.infrastructure.ai.prompts") / "daycare-ai-summary.txt"
).read_text(encoding="utf-8")


class AbstractAiApiClient(ABC):
    provider_name: str
    request_interval_ms: int

    @abstractmethod
    def _execute_request(self, prompt: str) -> str | None:
        """null 반환 시 "empty response" 에러로 처리한다."""
        ...

    @abstractmethod
    def _parse_retry_after_ms(self, response_body: str) -> int:
        """429 응답 본문 포맷이 provider 마다 달라 각 구현체에서 파싱한다."""
        ...

    def generate_summary(self, daycare: DaycareData) -> Result[DomainError, DaycareSummary]:
        return self._attempt(daycare, attempt=1)

    def _attempt(self, daycare: DaycareData, attempt: int) -> Result[DomainError, DaycareSummary]:
        try:
            prompt = _PROMPT_TEMPLATE.replace("{{어린이집JSON}}", daycare_json_builder.build(daycare))

            content = self._execute_request(prompt)
            if content is None:
                return Err(domain_error.Unknown(f"{self.provider_name} API returned empty response"))

            log.debug("%s raw content for daycare=%s: %s", self.provider_name, daycare.daycare_code, content)

            parsed = json.loads(content)
            return Ok(
                DaycareSummary(
                    summary=parsed["summary"],
                    who_may_be_interested=parsed["who_may_be_interested"],
                    things_to_consider=parsed["things_to_consider"],
                )
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt <= MAX_RETRIES:
                wait_ms = self._parse_retry_after_ms(e.response.text)
                log.warning(
                    "Rate limit: daycareCode=%s, %dms 후 재시도 (%d/%d)",
                    daycare.daycare_code,
                    wait_ms,
                    attempt,
                    MAX_RETRIES,
                )
                time.sleep(wait_ms / 1000)
                return self._attempt(daycare, attempt + 1)
            log.error(
                "%s API HTTP error: status=%s, body=%s",
                self.provider_name,
                e.response.status_code,
                e.response.text,
                exc_info=True,
            )
            return Err(domain_error.ApiCallError(e.response.status_code, None, str(e)))
        except Exception as e:
            log.error(
                "%s API call failed for daycare=%s", self.provider_name, daycare.daycare_code, exc_info=True
            )
            return Err(domain_error.Unknown(f"{self.provider_name} API call failed: {e}", e))
