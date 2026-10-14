"""환경변수 기반 설정.

Spring 의 ``application.yml`` + ``@ConfigurationProperties`` 를 대신한다.
기본값은 기존 ``application.yml`` 과 동일하게 맞춰 두었다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return default if raw is None or raw.strip() == "" else int(raw)


@dataclass(frozen=True, slots=True)
class LegalDongCodeApiConfig:
    base_url: str
    service_key: str
    """미설정 시 빈 문자열 — 다른 배치의 기동을 막지 않기 위함 (UseCase 진입 시 검사)"""
    per_page: int = 1000
    request_interval_ms: int = 200

    @classmethod
    def from_env(cls) -> LegalDongCodeApiConfig:
        return cls(
            base_url=os.environ.get("LEGAL_DONG_CODE_BASE_URL", "https://api.odcloud.kr"),
            service_key=os.environ.get("LEGAL_DONG_CODE_SERVICE_KEY", ""),
            per_page=_env_int("LEGAL_DONG_CODE_PER_PAGE", 1000),
            request_interval_ms=_env_int("LEGAL_DONG_CODE_REQUEST_INTERVAL_MS", 200),
        )


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    bot_token: str
    chat_id: str

    @classmethod
    def from_env(cls) -> TelegramConfig:
        return cls(
            bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
        )


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    conninfo: str

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        url = os.environ["DB_URL"]
        # 기존 GitHub Secret 은 Spring 용 JDBC URL 이다. 두 배치가 같은 값을 쓰도록 접두사만 걷어낸다.
        uri = url.removeprefix("jdbc:")
        return cls(
            conninfo=make_conninfo(
                uri,
                user=os.environ["DB_USERNAME"],
                password=os.environ["DB_PASSWORD"],
            )
        )


@dataclass(frozen=True, slots=True)
class SafemapApiConfig:
    base_url: str
    service_key: str
    """미설정 시 빈 문자열 — 다른 배치의 기동을 막지 않기 위함 (UseCase 진입 시 검사)"""
    page_size: int = 1000
    request_interval_ms: int = 200

    @classmethod
    def from_env(cls) -> SafemapApiConfig:
        return cls(
            base_url=os.environ.get("SAFEMAP_BASE_URL", "https://safemap.go.kr"),
            service_key=os.environ.get("SAFEMAP_SERVICE_KEY", ""),
            page_size=_env_int("SAFEMAP_PAGE_SIZE", 1000),
            request_interval_ms=_env_int("SAFEMAP_REQUEST_INTERVAL_MS", 200),
        )


@dataclass(frozen=True, slots=True)
class ChildcareApiConfig:
    """childcare.go.kr — API 마다 인증키가 다르다 (cpmsapi018/019/020/030)."""

    base_url: str
    key_sigungu: str
    key_daycare_detail: str
    key_new_daycare: str
    key_closed_daycare: str
    retry_max_attempts: int = 3
    retry_delay_ms: int = 60_000
    """429 응답 시 1분 대기"""
    request_interval_ms: int = 200

    @classmethod
    def from_env(cls) -> ChildcareApiConfig:
        return cls(
            base_url=os.environ.get("CHILDCARE_BASE_URL", "http://api.childcare.go.kr"),
            key_sigungu=os.environ.get("KIZLE_KEY_SIGUNGU", ""),
            key_daycare_detail=os.environ.get("KIZLE_KEY_DETAIL", ""),
            key_new_daycare=os.environ.get("KIZLE_KEY_NEW", ""),
            key_closed_daycare=os.environ.get("KIZLE_KEY_CLOSED", ""),
            retry_max_attempts=_env_int("CHILDCARE_RETRY_MAX_ATTEMPTS", 3),
            retry_delay_ms=_env_int("CHILDCARE_RETRY_DELAY_MS", 60_000),
            request_interval_ms=_env_int("CHILDCARE_REQUEST_INTERVAL_MS", 200),
        )


def ai_provider_from_env() -> str:
    """``ai.provider`` 를 대신한다 — groq / gemini / ollama, 기본 groq."""
    return os.environ.get("AI_PROVIDER", "groq")


@dataclass(frozen=True, slots=True)
class GeminiApiConfig:
    api_key: str
    """미설정 시 빈 문자열 — 다른 배치의 기동을 막지 않기 위함 (UseCase 진입 시 검사)"""
    base_url: str = "https://generativelanguage.googleapis.com"
    model: str = "gemini-2.0-flash"
    request_interval_ms: int = 4_000

    @classmethod
    def from_env(cls) -> GeminiApiConfig:
        return cls(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            base_url=os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            request_interval_ms=_env_int("GEMINI_REQUEST_INTERVAL_MS", 4_000),
        )


@dataclass(frozen=True, slots=True)
class GroqApiConfig:
    api_key: str
    """미설정 시 빈 문자열 — 다른 배치의 기동을 막지 않기 위함 (UseCase 진입 시 검사)"""
    base_url: str = "https://api.groq.com"
    model: str = "openai/gpt-oss-120b"
    """application.yml 에 고정된 실제 운영 모델 — Kotlin 클래스 기본값(llama-3.3-70b-versatile)과 다르다"""
    request_interval_ms: int = 20_000

    @classmethod
    def from_env(cls) -> GroqApiConfig:
        return cls(
            api_key=os.environ.get("GROQ_API_KEY", ""),
            base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com"),
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            request_interval_ms=_env_int("GROQ_REQUEST_INTERVAL_MS", 20_000),
        )


@dataclass(frozen=True, slots=True)
class OllamaApiConfig:
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:14b"
    """application.yml 에 고정된 실제 운영 모델 — Kotlin 클래스 기본값(qwen3:8b)과 다르다"""
    request_interval_ms: int = 0

    @classmethod
    def from_env(cls) -> OllamaApiConfig:
        return cls(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.environ.get("OLLAMA_MODEL", "qwen3:14b"),
            request_interval_ms=_env_int("OLLAMA_REQUEST_INTERVAL_MS", 0),
        )
