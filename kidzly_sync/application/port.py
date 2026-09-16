"""외부 시스템 접근 Port. 구현은 Infrastructure 계층에 둔다."""

from __future__ import annotations

from typing import Protocol

from kidzly_sync.application.model import LegalDongCodePage
from kidzly_sync.domain.error import DomainError
from kidzly_sync.domain.result import Result


class LegalDongCodeApiPort(Protocol):
    """법정동코드 조회 (odcloud.kr)."""

    def fetch_legal_dong_codes(self, page: int, per_page: int) -> Result[DomainError, LegalDongCodePage]:
        """한 페이지를 조회한다. ``per_page`` 상한은 2000 이다."""
        ...
