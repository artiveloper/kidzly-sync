"""Alembic 실행 환경.

접속 정보는 ``alembic.ini`` 가 아니라 배치와 똑같은 환경변수에서 읽는다
(``DB_URL`` / ``DB_USERNAME`` / ``DB_PASSWORD``). 시크릿을 파일로 떨어뜨리지 않기 위함이다.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 스키마의 단일 소유자는 리비전 파일의 생 SQL 이다. autogenerate 는 쓰지 않는다.
target_metadata = None


def _database_url() -> str:
    # 기존 GitHub Secret 은 Spring 용 JDBC URL 이다. 두 배치가 같은 값을 쓰도록 접두사만 걷어낸다.
    raw = os.environ["DB_URL"].removeprefix("jdbc:")
    url = make_url(raw).set(drivername="postgresql+psycopg")
    return url.set(
        username=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
    ).render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
