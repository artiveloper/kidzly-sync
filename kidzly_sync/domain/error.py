"""도메인 에러 계층.

Kotlin ``sealed class DomainError`` 를 옮긴 것으로 멤버와 필드가 1:1 대응한다.
Infrastructure 예외는 여기서 값으로 바뀌어 Application 계층까지 올라온다.
"""

from __future__ import annotations

from dataclasses import dataclass


class DomainError:
    """모든 도메인 에러의 상위 타입 (직접 인스턴스화하지 않는다)."""


@dataclass(frozen=True, slots=True)
class NotFound(DomainError):
    id: str
    resource: str


@dataclass(frozen=True, slots=True)
class ApiCallError(DomainError):
    status_code: int
    code: str | None
    message: str


@dataclass(frozen=True, slots=True)
class ParseError(DomainError):
    message: str
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class NetworkError(DomainError):
    message: str
    cause: BaseException | None = None


@dataclass(frozen=True, slots=True)
class RateLimitExceeded(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class Unauthorized(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class Unknown(DomainError):
    message: str
    cause: BaseException | None = None


def to_detailed_message(error: DomainError) -> str:
    """텔레그램 알림용 상세 문자열 — 원인 예외 체인을 끝까지 펼친다.

    Kotlin ``SyncOrchestrator.toDetailedMessage()`` 와 동일한 출력 형태를 유지한다.
    """
    lines = [str(error)]
    cause = getattr(error, "cause", None)
    current = cause.__cause__ if cause is not None else None
    while current is not None:
        lines.append(f"\n  Caused by: {type(current).__module__}.{type(current).__qualname__}: {current}")
        current = current.__cause__
    return "".join(lines)
