"""Ollama (로컬) Chat Completions API 클라이언트.

로컬 서버라 429 rate limit 이 없다 — ``_parse_retry_after_ms`` 는 호출되지 않는다.
"""

from __future__ import annotations

import re

import httpx

from kidzly_sync.config import OllamaApiConfig
from kidzly_sync.infrastructure.ai.abstract_client import DEFAULT_RETRY_WAIT_MS, AbstractAiApiClient

_THINK_TAG_PATTERN = re.compile(r"<think>[\s\S]*?</think>")


class OllamaApiClient(AbstractAiApiClient):
    provider_name = "Ollama"

    def __init__(self, http_client: httpx.Client, config: OllamaApiConfig) -> None:
        self._http = http_client
        self._config = config
        self.request_interval_ms = config.request_interval_ms

    def _execute_request(self, prompt: str) -> str | None:
        response = self._http.post(
            f"{self._config.base_url.rstrip('/')}/v1/chat/completions",
            json={
                "model": self._config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "max_completion_tokens": 3000,
            },
        )
        response.raise_for_status()
        choices = response.json().get("choices", [])
        if not choices:
            return None
        # Qwen3 thinking 모드가 활성화된 경우 <think>...</think> 태그 제거
        return _THINK_TAG_PATTERN.sub("", choices[0]["message"]["content"]).strip()

    def _parse_retry_after_ms(self, response_body: str) -> int:
        return DEFAULT_RETRY_WAIT_MS
