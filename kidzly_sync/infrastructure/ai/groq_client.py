"""Groq Chat Completions API 클라이언트 (OpenAI 호환)."""

from __future__ import annotations

import re

import httpx

from kidzly_sync.config import GroqApiConfig
from kidzly_sync.infrastructure.ai.abstract_client import (
    DEFAULT_RETRY_WAIT_MS,
    RETRY_BUFFER_MS,
    AbstractAiApiClient,
)

_RETRY_AFTER_PATTERN = re.compile(r"Please try again in (?:([\d.]+)m)?([\d.]+)s")


class GroqApiClient(AbstractAiApiClient):
    provider_name = "Groq"

    def __init__(self, http_client: httpx.Client, config: GroqApiConfig) -> None:
        self._http = http_client
        self._config = config
        self.request_interval_ms = config.request_interval_ms

    def _execute_request(self, prompt: str) -> str | None:
        response = self._http.post(
            f"{self._config.base_url.rstrip('/')}/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._config.api_key}"},
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
        return choices[0]["message"]["content"] if choices else None

    def _parse_retry_after_ms(self, response_body: str) -> int:
        match = _RETRY_AFTER_PATTERN.search(response_body)
        if match is None:
            return DEFAULT_RETRY_WAIT_MS
        minutes = float(match.group(1)) if match.group(1) else 0.0
        seconds = float(match.group(2)) if match.group(2) else 0.0
        total_ms = int((minutes * 60 + seconds) * 1000)
        return total_ms + RETRY_BUFFER_MS if total_ms > 0 else DEFAULT_RETRY_WAIT_MS
