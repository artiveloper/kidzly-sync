"""배치 진입점 — GitHub Actions one-shot 실행용.

``kidzly-sync sigungu-code`` 처럼 잡 이름을 인자로 받아 한 번 실행하고 종료한다.
성공은 exit code 0, 실패는 1이다.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from contextlib import ExitStack

import httpx
import psycopg

from kidzly_sync.application.orchestrator import SyncOrchestrator
from kidzly_sync.application.usecase.sigungu_code_sync import SigunguCodeSyncUseCase
from kidzly_sync.config import DatabaseConfig, LegalDongCodeApiConfig, TelegramConfig
from kidzly_sync.infrastructure.api.legal_dong_code_client import LegalDongCodeApiClient
from kidzly_sync.infrastructure.notification.telegram import TelegramNotifier
from kidzly_sync.infrastructure.persistence.sigungu_code_repository import SigunguCodeRepositoryImpl
from kidzly_sync.infrastructure.persistence.sync_history_repository import SyncHistoryRepositoryImpl

log = logging.getLogger(__name__)

# 운영 RestClient Bean 과 같은 타임아웃 (connect 30s / read 60s / pool 10s)
_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=60.0, write=60.0, pool=10.0)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s",
        stream=sys.stdout,
    )


def _run_sigungu_code(stack: ExitStack) -> bool:
    conn = stack.enter_context(psycopg.connect(DatabaseConfig.from_env().conninfo))
    http = stack.enter_context(httpx.Client(timeout=_HTTP_TIMEOUT))

    legal_dong_config = LegalDongCodeApiConfig.from_env()
    use_case = SigunguCodeSyncUseCase(
        legal_dong_code_api_port=LegalDongCodeApiClient(http, legal_dong_config),
        sigungu_code_repository=SigunguCodeRepositoryImpl(conn),
        config=legal_dong_config,
    )
    orchestrator = SyncOrchestrator(
        sigungu_code_sync_use_case=use_case,
        sync_history_repository=SyncHistoryRepositoryImpl(conn),
        telegram_notifier=TelegramNotifier(http, TelegramConfig.from_env()),
    )
    log.info("=== [BATCH] 법정동코드 동기화 실행 ===")
    return orchestrator.sigungu_code_sync(skip_if_already_succeeded_today=True)


# 잡이 늘어나면 여기에만 추가한다
_JOBS: dict[str, Callable[[ExitStack], bool]] = {
    "sigungu-code": _run_sigungu_code,
}


def main(argv: list[str] | None = None) -> int:
    _configure_logging()

    parser = argparse.ArgumentParser(prog="kidzly-sync", description="kidzly 공공 API 동기화 배치")
    parser.add_argument("job", choices=sorted(_JOBS), help="실행할 동기화 잡")
    args = parser.parse_args(argv)

    with ExitStack() as stack:
        try:
            success = _JOBS[args.job](stack)
        except Exception:
            log.exception("[BATCH] 동기화 실패")
            return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
