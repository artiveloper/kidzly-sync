from __future__ import annotations

import logging

import httpx

from kidzly_sync.config import TelegramConfig

log = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, http_client: httpx.Client, config: TelegramConfig) -> None:
        self._http = http_client
        self._config = config

    def send_message(self, text: str) -> None:
        try:
            self._http.post(
                f"https://api.telegram.org/bot{self._config.bot_token}/sendMessage",
                json={"chat_id": self._config.chat_id, "text": text, "parse_mode": "HTML"},
            )
        except Exception as e:
            # 알림 실패가 동기화 자체를 중단시키면 안 됨
            log.error("텔레그램 알림 전송 실패: %s", e, exc_info=True)
