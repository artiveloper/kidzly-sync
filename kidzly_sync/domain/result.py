"""Arrow-kt ``Either<E, A>`` 를 대신하는 최소 결과 타입.

UseCase 는 실패를 예외가 아니라 값으로 돌려준다. 호출자가 ``fold`` 로 두 갈래를
반드시 처리하게 만들어, 실패 경로가 조용히 누락되는 것을 막는 것이 목적이다.

``Either.Left`` -> :class:`Err`, ``Either.Right`` -> :class:`Ok` 로 1:1 대응한다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ok[A]:
    value: A

    def is_ok(self) -> bool:
        return True

    def fold[B](self, if_err: Callable[[object], B], if_ok: Callable[[A], B]) -> B:
        return if_ok(self.value)

    def map[B](self, f: Callable[[A], B]) -> Ok[B]:
        return Ok(f(self.value))

    def flat_map[E, B](self, f: Callable[[A], Result[E, B]]) -> Result[E, B]:
        return f(self.value)


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def is_ok(self) -> bool:
        return False

    def fold[B](self, if_err: Callable[[E], B], if_ok: Callable[[object], B]) -> B:
        return if_err(self.error)

    def map(self, f: Callable[[object], object]) -> Err[E]:
        return self

    def flat_map(self, f: Callable[[object], object]) -> Err[E]:
        return self


type Result[E, A] = Ok[A] | Err[E]
