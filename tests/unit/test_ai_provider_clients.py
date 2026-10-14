"""provider 별 429 응답 파싱 / Ollama think 태그 제거 단위 테스트.

HTTP 호출 자체는 테스트하지 않는다 (``_execute_request`` 는 그대로 외부 API 호출이다) —
각 provider 가 추가하는 파싱 로직만 검증한다.
"""

from __future__ import annotations

from kidzly_sync.config import GeminiApiConfig, GroqApiConfig, OllamaApiConfig
from kidzly_sync.infrastructure.ai.abstract_client import DEFAULT_RETRY_WAIT_MS, RETRY_BUFFER_MS
from kidzly_sync.infrastructure.ai.gemini_client import GeminiApiClient
from kidzly_sync.infrastructure.ai.groq_client import GroqApiClient
from kidzly_sync.infrastructure.ai.ollama_client import _THINK_TAG_PATTERN, OllamaApiClient


def groq_client() -> GroqApiClient:
    return GroqApiClient(http_client=None, config=GroqApiConfig(api_key="k"))


def gemini_client() -> GeminiApiClient:
    return GeminiApiClient(http_client=None, config=GeminiApiConfig(api_key="k"))


def ollama_client() -> OllamaApiClient:
    return OllamaApiClient(http_client=None, config=OllamaApiConfig())


# ── Groq ──────────────────────────────────────────────────────────────────────


def test_groq_parses_seconds_only():
    assert groq_client()._parse_retry_after_ms("Please try again in 12.5s") == 12_500 + RETRY_BUFFER_MS


def test_groq_parses_minutes_and_seconds():
    ms = groq_client()._parse_retry_after_ms("Please try again in 1m30s")
    assert ms == int((90) * 1000) + RETRY_BUFFER_MS


def test_groq_falls_back_to_default_when_the_pattern_is_absent():
    assert groq_client()._parse_retry_after_ms("rate limited, no detail") == DEFAULT_RETRY_WAIT_MS


# ── Gemini ────────────────────────────────────────────────────────────────────


def test_gemini_parses_retry_delay_seconds():
    body = '"retryDelay": "7s"'
    assert gemini_client()._parse_retry_after_ms(body) == 7_000 + RETRY_BUFFER_MS


def test_gemini_falls_back_to_default_when_the_pattern_is_absent():
    assert gemini_client()._parse_retry_after_ms("{}") == DEFAULT_RETRY_WAIT_MS


# ── Ollama ────────────────────────────────────────────────────────────────────


def test_ollama_never_rate_limits_so_it_always_returns_the_default_wait():
    assert ollama_client()._parse_retry_after_ms("anything") == DEFAULT_RETRY_WAIT_MS


def test_ollama_strips_think_tags_from_qwen3_thinking_mode_output():
    content = "<think>혼자 생각하는 중...</think>{\"summary\": \"요약\"}"

    stripped = _THINK_TAG_PATTERN.sub("", content).strip()

    assert stripped == '{"summary": "요약"}'
