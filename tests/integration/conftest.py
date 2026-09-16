"""통합 테스트용 PostgreSQL 컨테이너.

스키마는 운영과 같은 경로(Alembic 리비전)로 만든다. 테스트가 손으로 만든 DDL 을 쓰면
운영 스키마와 어긋나도 초록불이 뜬다.

Docker 를 쓸 수 없는 환경에서는 모든 케이스가 스킵된다.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_conninfo() -> str:
    if not _docker_available():
        pytest.skip("Docker 사용 불가 — 통합 테스트 스킵")

    from alembic import command
    from alembic.config import Config
    from testcontainers.postgres import PostgresContainer

    # Ryuk(정리용 사이드카)은 도커 소켓을 마운트하는데, 소켓 경로를 옮겨 쓰는 Docker Desktop
    # 설정에서는 마운트가 실패한다. 컨테이너는 아래 with 블록이 직접 멈추므로 꺼도 된다.
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

    with PostgresContainer("postgres:16-alpine", driver=None) as container:
        conninfo = container.get_connection_url()
        previous = {k: os.environ.get(k) for k in ("DB_URL", "DB_USERNAME", "DB_PASSWORD")}
        os.environ["DB_URL"] = conninfo
        os.environ["DB_USERNAME"] = container.username
        os.environ["DB_PASSWORD"] = container.password
        try:
            config = Config(str(REPO_ROOT / "alembic.ini"))
            config.set_main_option("script_location", str(REPO_ROOT / "migrations"))
            command.upgrade(config, "head")
            yield conninfo
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


@pytest.fixture
def conn(postgres_conninfo: str):
    with psycopg.connect(postgres_conninfo) as connection:
        yield connection
