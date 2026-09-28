"""배치 진입점 — GitHub Actions one-shot 실행용.

``kidzly-sync playground`` 처럼 잡 이름을 인자로 받아 한 번 실행하고 종료한다.
성공은 exit code 0, 실패는 1이다.
"""

from __future__ import annotations

import argparse
import logging
import sys
from argparse import Namespace
from collections.abc import Callable
from contextlib import ExitStack
from datetime import datetime

import httpx
import psycopg

from kidzly_sync.application.orchestrator import SyncOrchestrator
from kidzly_sync.application.usecase.delta_sync import DeltaSyncUseCase
from kidzly_sync.application.usecase.full_sync import FullSyncUseCase
from kidzly_sync.application.usecase.playground_full_sync import PlaygroundFullSyncUseCase
from kidzly_sync.application.usecase.sigungu_code_sync import SigunguCodeSyncUseCase
from kidzly_sync.config import (
    ChildcareApiConfig,
    DatabaseConfig,
    LegalDongCodeApiConfig,
    SafemapApiConfig,
    TelegramConfig,
)
from kidzly_sync.infrastructure.api.childcare_client import ChildcareApiClient
from kidzly_sync.infrastructure.api.legal_dong_code_client import LegalDongCodeApiClient
from kidzly_sync.infrastructure.api.safemap_client import SafemapApiClient
from kidzly_sync.infrastructure.notification.telegram import TelegramNotifier
from kidzly_sync.infrastructure.persistence.daycare_repository import DaycareRepositoryImpl
from kidzly_sync.infrastructure.persistence.playground_repository import PlaygroundRepositoryImpl
from kidzly_sync.infrastructure.persistence.sigungu_code_repository import SigunguCodeRepositoryImpl
from kidzly_sync.infrastructure.persistence.sigungu_repository import SigunguRepositoryImpl
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


def _build_orchestrator(stack: ExitStack) -> SyncOrchestrator:
    """조립 지점. 서비스 키가 없는 잡의 UseCase 도 함께 만든다 — 키 검사는 실행 시점에 한다."""
    conn = stack.enter_context(psycopg.connect(DatabaseConfig.from_env().conninfo))
    http = stack.enter_context(httpx.Client(timeout=_HTTP_TIMEOUT))

    legal_dong_config = LegalDongCodeApiConfig.from_env()
    safemap_config = SafemapApiConfig.from_env()
    childcare_config = ChildcareApiConfig.from_env()
    childcare_client = ChildcareApiClient(http, childcare_config)
    daycare_repository = DaycareRepositoryImpl(conn)

    return SyncOrchestrator(
        sigungu_code_sync_use_case=SigunguCodeSyncUseCase(
            legal_dong_code_api_port=LegalDongCodeApiClient(http, legal_dong_config),
            sigungu_code_repository=SigunguCodeRepositoryImpl(conn),
            config=legal_dong_config,
        ),
        playground_full_sync_use_case=PlaygroundFullSyncUseCase(
            safemap_api_port=SafemapApiClient(http, safemap_config),
            playground_repository=PlaygroundRepositoryImpl(conn),
            config=safemap_config,
        ),
        full_sync_use_case=FullSyncUseCase(
            childcare_api_port=childcare_client,
            daycare_repository=daycare_repository,
            sigungu_repository=SigunguRepositoryImpl(conn),
            config=childcare_config,
        ),
        delta_sync_use_case=DeltaSyncUseCase(
            childcare_api_port=childcare_client,
            daycare_repository=daycare_repository,
            config=childcare_config,
        ),
        sync_history_repository=SyncHistoryRepositoryImpl(conn),
        telegram_notifier=TelegramNotifier(http, TelegramConfig.from_env()),
    )


def _run_sigungu_code(stack: ExitStack, args: Namespace) -> bool:
    log.info("=== [BATCH] 법정동코드 동기화 실행 ===")
    return _build_orchestrator(stack).sigungu_code_sync(not args.force)


def _run_playground(stack: ExitStack, args: Namespace) -> bool:
    log.info("=== [BATCH] 놀이시설 동기화 실행 ===")
    return _build_orchestrator(stack).playground_sync(not args.force)


def _run_full(stack: ExitStack, args: Namespace) -> bool:
    log.info("=== [BATCH] 전체 동기화 실행 ===")
    return _build_orchestrator(stack).full_sync(not args.force)


def _run_delta(stack: ExitStack, args: Namespace) -> bool:
    yyyymm = _resolve_year_month(args.year_month)
    log.info("=== [BATCH] 증분 동기화 실행 (대상월=%s) ===", yyyymm)
    return _build_orchestrator(stack).delta_sync(yyyymm, not args.force)


def _resolve_year_month(raw: str | None) -> str:
    """``2026-03`` 을 ``202603`` 으로 바꾼다. 생략하면 당월.

    기준 시계는 러너의 로컬 시각이다 (GitHub Actions 에서는 UTC). KST 로 바꾸면
    월말 UTC 저녁 슬롯이 다음 달을 가리켜, 그 달 마지막 몇 시간의 신규·폐지분을
    아무 실행도 집어가지 않게 된다.
    """
    if raw is None:
        return datetime.now().strftime("%Y%m")
    try:
        return datetime.strptime(raw, "%Y-%m").strftime("%Y%m")
    except ValueError:
        raise SystemExit(f"year-month 형식이 올바르지 않습니다: {raw!r} (예: 2026-03)") from None


# 잡이 늘어나면 여기에만 추가한다
_JOBS: dict[str, Callable[[ExitStack, Namespace], bool]] = {
    "sigungu-code": _run_sigungu_code,
    "playground": _run_playground,
    "full": _run_full,
    "delta": _run_delta,
}


def main(argv: list[str] | None = None) -> int:
    _configure_logging()

    parser = argparse.ArgumentParser(prog="kidzly-sync", description="kidzly 공공 API 동기화 배치")
    parser.add_argument("job", choices=sorted(_JOBS), help="실행할 동기화 잡")
    parser.add_argument(
        "--force",
        action="store_true",
        # cron 은 성공할 때까지 하루 여러 번 시도하므로 스킵 가드가 기본이다.
        # 사람이 직접 돌릴 때는 이미 성공했더라도 다시 돌려야 할 때가 있다
        # (두 구현의 결과 비교, 원본이 바뀐 뒤 재동기화 등).
        help="오늘 이미 성공했더라도 건너뛰지 않고 실행한다",
    )
    parser.add_argument(
        "--year-month",
        metavar="YYYY-MM",
        help="delta 잡의 대상 연월 (예: 2026-03). 생략하면 당월",
    )
    args = parser.parse_args(argv)

    with ExitStack() as stack:
        try:
            success = _JOBS[args.job](stack, args)
        except Exception:
            log.exception("[BATCH] 동기화 실패")
            return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
