"""Gemini generateContent API 클라이언트."""

from __future__ import annotations

import re

import httpx

from kidzly_sync.config import GeminiApiConfig
from kidzly_sync.infrastructure.ai.abstract_client import (
    DEFAULT_RETRY_WAIT_MS,
    RETRY_BUFFER_MS,
    AbstractAiApiClient,
)

_RETRY_AFTER_PATTERN = re.compile(r'retryDelay["\s:]+(\d+)s')


class GeminiApiClient(AbstractAiApiClient):
    provider_name = "Gemini"

    def __init__(self, http_client: httpx.Client, config: GeminiApiConfig) -> None:
        self._http = http_client
        self._config = config
        self.request_interval_ms = config.request_interval_ms

    def _execute_request(self, prompt: str) -> str | None:
        response = self._http.post(
            f"{self._config.base_url.rstrip('/')}/v1beta/models/{self._config.model}:generateContent",
            headers={"x-goog-api-key": self._config.api_key},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 3000,
                    "temperature": 0.3,
                },
            },
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        return parts[0]["text"] if parts else None

    def _parse_retry_after_ms(self, response_body: str) -> int:
        match = _RETRY_AFTER_PATTERN.search(response_body)
        if match is None:
            return DEFAULT_RETRY_WAIT_MS
        return int(float(match.group(1)) * 1000) + RETRY_BUFFER_MS
