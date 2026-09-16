"""API 클라이언트 내부 예외.

호출부로 새어 나가는 것은 :class:`RateLimitError` 뿐이다 (재시도 대상).
나머지는 클라이언트 안에서 :mod:`kidzly_sync.domain.error` 값으로 변환된다.
"""

from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(Exception):
    """HTTP 429. 일 요청 건수 초과 — 시간을 두고 재시도한다."""


class UnauthorizedError(Exception):
    """HTTP 401. 인증키가 유효하지 않다 — 재시도해도 소용없다."""
