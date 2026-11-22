"""childcare 계열 테스트가 공유하는 더블과 픽스처."""

from __future__ import annotations

import dataclasses

from kidzly_sync.application.model import DaycareData, SigunguInfo
from kidzly_sync.config import ChildcareApiConfig
from kidzly_sync.domain.result import Ok


def config(request_interval_ms: int = 0) -> ChildcareApiConfig:
    return ChildcareApiConfig(
        base_url="http://api.childcare.go.kr",
        key_sigungu="K020",
        key_daycare_detail="K030",
        key_new_daycare="K018",
        key_closed_daycare="K019",
        request_interval_ms=request_interval_ms,
    )


def daycare(code: str, **overrides) -> DaycareData:
    """필수 필드만 채운 최소 DaycareData. 나머지 68개는 None 이다."""
    base = {f.name: None for f in dataclasses.fields(DaycareData)}
    base |= {
        "daycare_code": code,
        "sigungu_code": "11110",
        "name": f"테스트어린이집 {code}",
        "status": "정상",
    }
    base |= overrides
    return DaycareData(**base)


def sigungu(arcode: str, sidoname: str = "서울특별시", sigunname: str = "종로구") -> SigunguInfo:
    return SigunguInfo(arcode=arcode, sidoname=sidoname, sigunname=sigunname)


class FakeChildcarePort:
    """호출 내역을 남기고 미리 정한 응답을 돌려준다."""

    def __init__(
        self,
        sigungu_lists: dict[str, object] | None = None,
        details: dict[str, object] | None = None,
        new_daycares: object = None,
        closed_daycares: object = None,
    ) -> None:
        self._sigungu_lists = sigungu_lists or {}
        self._details = details or {}
        self._new = new_daycares
        self._closed = closed_daycares
        self.sigungu_calls: list[str] = []
        self.detail_calls: list[str] = []
        self.new_calls: list[str] = []
        self.closed_calls: list[str] = []

    def fetch_sigungu_list(self, arname: str):
        self.sigungu_calls.append(arname)
        assert arname in self._sigungu_lists, f"예상치 못한 시도: {arname}"
        return self._sigungu_lists[arname]

    def fetch_daycare_details(self, arcode: str):
        self.detail_calls.append(arcode)
        assert arcode in self._details, f"예상치 못한 시군구: {arcode}"
        return self._details[arcode]

    def fetch_new_daycares(self, yyyymm: str):
        self.new_calls.append(yyyymm)
        return self._new

    def fetch_closed_daycares(self, yyyymm: str):
        self.closed_calls.append(yyyymm)
        # 전체 동기화는 여러 달을 조회한다 — 달별 응답을 주면 그것을, 아니면 같은 응답을 돌려준다
        if isinstance(self._closed, dict):
            return self._closed.get(yyyymm, Ok([]))
        return self._closed if self._closed is not None else Ok([])


class RecordingDaycareRepository:
    def __init__(
        self,
        upsert_returns: list[int] | None = None,
        closed_returns: list[int] | None = None,
        sido_names: list[str] | None = None,
        active_by_sido: dict[str, dict[str, str]] | None = None,
        sigungu_of: dict[str, str] | None = None,
    ):
        """``active_by_sido`` 는 DB 에 있는 '정상' 어린이집 — {시도명: {코드: 코드}} 형태로 둔다."""
        self.batches: list[list[DaycareData]] = []
        self.closed_calls: list[tuple[str, str | None]] = []
        self.excluded_codes: set[str] | None = None
        self._upsert_returns = list(upsert_returns) if upsert_returns is not None else None
        self._closed_returns = list(closed_returns) if closed_returns is not None else None
        self._sido_names = sido_names or []
        self._active_by_sido = active_by_sido or {}
        self._sigungu_of = sigungu_of or {}
        self._closed_codes: set[str] = set()

    def find_all_sido_names(self) -> list[str]:
        return list(self._sido_names)

    def find_active_excluding(self, daycare_codes: set[str]) -> list[tuple[str, str]]:
        return [
            (code, self._sigungu_of.get(code, "11110"))
            for codes in self._active_by_sido.values()
            for code in codes
            if code not in daycare_codes and code not in self._closed_codes
        ]

    def count_active_by_sido_excluding(self, daycare_codes: set[str]) -> dict[str, int]:
        self.excluded_codes = set(daycare_codes)
        daycare_codes = set(daycare_codes) | self._closed_codes
        counts = {
            sido: sum(1 for c in codes if c not in daycare_codes)
            for sido, codes in self._active_by_sido.items()
        }
        return {sido: n for sido, n in counts.items() if n}

    def upsert_all(self, daycares: list[DaycareData]) -> int:
        self.batches.append(daycares)
        if self._upsert_returns is not None:
            return self._upsert_returns.pop(0)
        return len(daycares)

    def mark_as_closed(self, daycare_code: str, abolished_date: str | None) -> int:
        self.closed_calls.append((daycare_code, abolished_date))
        self._closed_codes.add(daycare_code)
        if self._closed_returns is not None:
            return self._closed_returns.pop(0)
        return 1


class RecordingSigunguRepository:
    def __init__(self, sido_names: list[str] | None = None) -> None:
        self.batches: list[list[SigunguInfo]] = []
        self.kept_arcodes: set[str] | None = None
        self._sido_names = sido_names or []

    def find_all_sido_names(self) -> list[str]:
        return list(self._sido_names)

    def delete_all_except(self, arcodes: set[str]) -> int:
        self.kept_arcodes = set(arcodes)
        return 0

    def upsert_all(self, sigungus: list[SigunguInfo]) -> int:
        self.batches.append(sigungus)
        return len(sigungus)
