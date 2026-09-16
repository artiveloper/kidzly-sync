"""``PlaygroundFullSyncUseCase`` 페이지네이션 순회 / fail-fast / 방어 로직 단위 테스트.

``request_interval_ms=0`` 으로 두어 sleep 대기 없이 실행된다.
"""

from __future__ import annotations

from kidzly_sync.application.model import PlaygroundData, PlaygroundPage, SyncResult
from kidzly_sync.application.usecase.playground_full_sync import PlaygroundFullSyncUseCase
from kidzly_sync.config import SafemapApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok

# ── 테스트 더블 ───────────────────────────────────────────────────────────────


class FakePort:
    def __init__(self, responses: dict[tuple[int, int], object]) -> None:
        self._responses = responses
        self.calls: list[tuple[int, int]] = []

    def fetch_playgrounds(self, page_no: int, num_of_rows: int):
        self.calls.append((page_no, num_of_rows))
        assert (page_no, num_of_rows) in self._responses, (
            f"예상치 못한 호출: pageNo={page_no}, numOfRows={num_of_rows}"
        )
        return self._responses[(page_no, num_of_rows)]


class RecordingRepository:
    def __init__(self, returns: list[int] | None = None) -> None:
        self.batches: list[list[PlaygroundData]] = []
        self._returns = list(returns) if returns is not None else None

    def upsert_all(self, playgrounds: list[PlaygroundData]) -> int:
        self.batches.append(playgrounds)
        if self._returns is not None:
            return self._returns.pop(0)
        return len(playgrounds)


def config(service_key: str = "TEST_KEY", page_size: int = 1000) -> SafemapApiConfig:
    return SafemapApiConfig(
        base_url="https://safemap.go.kr",
        service_key=service_key,
        page_size=page_size,
        request_interval_ms=0,
    )


def use_case(port, repository, cfg: SafemapApiConfig | None = None) -> PlaygroundFullSyncUseCase:
    return PlaygroundFullSyncUseCase(port, repository, cfg or config())


# ── 픽스처 ────────────────────────────────────────────────────────────────────


def playground_data(facility_id: str) -> PlaygroundData:
    return PlaygroundData(
        facility_id=facility_id,
        facility_serial_no=None,
        sido_code=None,
        sigungu_code=None,
        emd_code=None,
        name=f"테스트 놀이터 {facility_id}",
        address=None,
        coord_x=None,
        coord_y=None,
        install_date=None,
        facility_code1=None,
        facility_code2=None,
        install_place_code=None,
        ownership_code=None,
        indoor_outdoor_code=None,
        operation_code=None,
        accident_yn=None,
        deleted_yn=None,
    )


def page(page_no: int, item_count: int, total_count: int) -> PlaygroundPage:
    return PlaygroundPage(
        items=[playground_data(f"{page_no}_{i}") for i in range(1, item_count + 1)],
        page_no=page_no,
        num_of_rows=item_count,
        total_count=total_count,
    )


# ── 페이지네이션 종료 조건 ─────────────────────────────────────────────────────


def test_calls_the_api_exactly_three_times_for_2500_rows_at_1000_per_page():
    port = FakePort(
        {
            (1, 1000): Ok(page(1, 1000, total_count=2500)),
            (2, 1000): Ok(page(2, 1000, total_count=2500)),
            (3, 1000): Ok(page(3, 500, total_count=2500)),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=2500, upserted=2500))
    assert port.calls == [(1, 1000), (2, 1000), (3, 1000)]


def test_stops_after_the_first_page_when_total_count_fits_into_a_single_page():
    port = FakePort({(1, 1000): Ok(page(1, 30, total_count=30))})
    repository = RecordingRepository(returns=[30])

    result = use_case(port, repository).execute()

    assert result.value.total == 30
    assert port.calls == [(1, 1000)]


def test_fixes_the_page_count_from_the_first_response_and_ignores_a_later_change():
    port = FakePort(
        {
            (1, 1000): Ok(page(1, 1000, total_count=2000)),
            # 순회 도중 원본 totalCount 가 늘어도 첫 페이지 기준(2페이지)에서 종료한다
            (2, 1000): Ok(page(2, 1000, total_count=9000)),
        }
    )
    repository = RecordingRepository()

    use_case(port, repository).execute()

    assert port.calls == [(1, 1000), (2, 1000)]


def test_stops_as_soon_as_a_page_returns_an_empty_item_list():
    # totalCount 가 비정상적으로 커도 빈 페이지에서 반드시 멈춘다 (무한 루프 방지)
    port = FakePort(
        {
            (1, 1000): Ok(page(1, 1000, total_count=999_999)),
            (2, 1000): Ok(page(2, 0, total_count=999_999)),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result.value.total == 1000
    assert port.calls == [(1, 1000), (2, 1000)]
    assert len(repository.batches) == 1


def test_returns_an_empty_result_and_never_touches_the_repository_when_the_first_page_is_empty():
    port = FakePort({(1, 1000): Ok(page(1, 0, total_count=0))})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=0, upserted=0))
    assert repository.batches == []


def test_passes_the_configured_page_size_to_the_port_as_num_of_rows():
    port = FakePort({(1, 250): Ok(page(1, 5, total_count=5))})
    repository = RecordingRepository(returns=[5])

    use_case(port, repository, config(page_size=250)).execute()

    assert port.calls == [(1, 250)]


# ── fail-fast ─────────────────────────────────────────────────────────────────


def test_fails_fast_and_skips_the_remaining_pages_when_page_two_returns_err():
    failure = domain_error.NetworkError("connect timed out")
    port = FakePort(
        {
            (1, 1000): Ok(page(1, 1000, total_count=3000)),
            (2, 1000): Err(failure),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Err(failure)
    assert port.calls == [(1, 1000), (2, 1000)]
    # 실패 이전 페이지는 이미 커밋되어 있다 (부분 성공 유지)
    assert len(repository.batches) == 1


def test_returns_the_very_first_failure_when_page_one_already_fails():
    failure = domain_error.ApiCallError(200, "99", "SERVICE_ERROR")
    port = FakePort({(1, 1000): Err(failure)})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Err(failure)
    assert repository.batches == []


# ── 서비스 키 방어 ────────────────────────────────────────────────────────────


def test_returns_unauthorized_without_calling_the_api_when_service_key_is_empty():
    port = FakePort({})
    repository = RecordingRepository()

    result = use_case(port, repository, config(service_key="")).execute()

    assert result == Err(domain_error.Unauthorized())
    assert port.calls == []


def test_returns_unauthorized_when_service_key_is_whitespace_only():
    port = FakePort({})
    repository = RecordingRepository()

    result = use_case(port, repository, config(service_key="   ")).execute()

    assert result == Err(domain_error.Unauthorized())
    assert port.calls == []


# ── 집계 ──────────────────────────────────────────────────────────────────────


def test_reports_total_as_received_rows_and_upserted_as_rows_actually_changed():
    port = FakePort(
        {
            (1, 10): Ok(page(1, 10, total_count=20)),
            (2, 10): Ok(page(2, 10, total_count=20)),
        }
    )
    # 변경 감지 가드로 실제 변경은 3건뿐인 상황
    repository = RecordingRepository(returns=[3, 0])

    result = use_case(port, repository, config(page_size=10)).execute()

    assert result.value.total == 20
    assert result.value.upserted == 3
    assert result.value.closed == 0
