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
