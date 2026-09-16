"""``SigunguCodeSyncUseCase`` 필터 파이프라인 / 페이지네이션 / fail-fast 단위 테스트.

``request_interval_ms=0`` 으로 두어 sleep 대기 없이 실행된다.
"""

from __future__ import annotations

from kidzly_sync.application.model import (
    LegalDongCodePage,
    LegalDongCodeRecord,
    SigunguCodeData,
    SyncResult,
)
from kidzly_sync.application.usecase.sigungu_code_sync import SigunguCodeSyncUseCase
from kidzly_sync.config import LegalDongCodeApiConfig
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.legal_dong_code import SigunguCodeLevel
from kidzly_sync.domain.result import Err, Ok

# ── 테스트 더블 ───────────────────────────────────────────────────────────────


class FakePort:
    """``(page, per_page)`` 로 응답을 골라 주고 호출 내역을 남긴다."""

    def __init__(self, responses: dict[tuple[int, int], object]) -> None:
        self._responses = responses
        self.calls: list[tuple[int, int]] = []

    def fetch_legal_dong_codes(self, page: int, per_page: int):
        self.calls.append((page, per_page))
        assert (page, per_page) in self._responses, f"예상치 못한 호출: page={page}, perPage={per_page}"
        return self._responses[(page, per_page)]


class RecordingRepository:
    """받은 배치를 보관한다. ``returns`` 를 주면 그 순서대로 반환값을 흉내낸다."""

    def __init__(self, returns: list[int] | None = None) -> None:
        self.batches: list[list[SigunguCodeData]] = []
        self._returns = list(returns) if returns is not None else None

    def upsert_all(self, codes: list[SigunguCodeData]) -> int:
        self.batches.append(codes)
        if self._returns is not None:
            return self._returns.pop(0)
        return len(codes)


def config(service_key: str = "TEST_KEY", per_page: int = 1000) -> LegalDongCodeApiConfig:
    return LegalDongCodeApiConfig(
        base_url="https://api.odcloud.kr",
        service_key=service_key,
        per_page=per_page,
        request_interval_ms=0,
    )


def use_case(port, repository, cfg: LegalDongCodeApiConfig | None = None) -> SigunguCodeSyncUseCase:
    return SigunguCodeSyncUseCase(port, repository, cfg or config())


# ── 픽스처 ────────────────────────────────────────────────────────────────────


def record(code: str, name: str, abolished_yn: str | None) -> LegalDongCodeRecord:
    return LegalDongCodeRecord(code=code, name=name, abolished_yn=abolished_yn)


def emd_page(page: int, item_count: int, total_count: int) -> LegalDongCodePage:
    """전부 저장 대상인 정상 페이지 (필터가 아니라 순회를 검증할 때 사용)."""
    return LegalDongCodePage(
        items=[
            record(f"1111{page * 1000 + idx:04d}00", f"테스트동 {page}_{idx}", "존재")
            for idx in range(1, item_count + 1)
        ],
        page=page,
        per_page=item_count,
        total_count=total_count,
    )


def page_of(*items: LegalDongCodeRecord, total_count: int) -> LegalDongCodePage:
    return LegalDongCodePage(items=list(items), page=1, per_page=len(items), total_count=total_count)


# ── 서비스 키 방어 ────────────────────────────────────────────────────────────


def test_returns_unauthorized_without_calling_the_api_when_service_key_is_empty():
    port = FakePort({})
    repository = RecordingRepository()

    result = use_case(port, repository, config(service_key="")).execute()

    assert result == Err(domain_error.Unauthorized())
    assert port.calls == []
    assert repository.batches == []


def test_returns_unauthorized_when_service_key_is_whitespace_only():
    port = FakePort({})
    repository = RecordingRepository()

    result = use_case(port, repository, config(service_key="   ")).execute()

    assert result == Err(domain_error.Unauthorized())
    assert port.calls == []


# ── 페이지네이션 종료 조건 ─────────────────────────────────────────────────────


def test_calls_the_api_exactly_three_times_for_2500_rows_at_1000_per_page():
    port = FakePort(
        {
            (1, 1000): Ok(emd_page(1, 1000, total_count=2500)),
            (2, 1000): Ok(emd_page(2, 1000, total_count=2500)),
            (3, 1000): Ok(emd_page(3, 500, total_count=2500)),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=2500, upserted=2500))
    assert port.calls == [(1, 1000), (2, 1000), (3, 1000)]


def test_stops_after_the_first_page_when_total_count_fits_into_a_single_page():
    port = FakePort({(1, 1000): Ok(emd_page(1, 30, total_count=30))})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result.value.total == 30
    assert port.calls == [(1, 1000)]


def test_fixes_the_page_count_from_the_first_response_and_ignores_a_later_change():
    port = FakePort(
        {
            (1, 1000): Ok(emd_page(1, 1000, total_count=2000)),
            # 순회 도중 원본 totalCount 가 늘어도 첫 페이지 기준(2페이지)에서 종료한다
            (2, 1000): Ok(emd_page(2, 1000, total_count=9000)),
        }
    )
    repository = RecordingRepository()

    use_case(port, repository).execute()

    assert port.calls == [(1, 1000), (2, 1000)]


def test_stops_as_soon_as_a_page_returns_an_empty_item_list():
    # totalCount 가 비정상적으로 커도 빈 페이지에서 반드시 멈춘다 (무한 루프 방지)
    port = FakePort(
        {
            (1, 1000): Ok(emd_page(1, 1000, total_count=999_999)),
            (2, 1000): Ok(emd_page(2, 0, total_count=999_999)),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result.value.total == 1000
    assert port.calls == [(1, 1000), (2, 1000)]
    assert len(repository.batches) == 1


def test_returns_an_empty_result_and_never_touches_the_repository_when_the_first_page_is_empty():
    port = FakePort({(1, 1000): Ok(emd_page(1, 0, total_count=0))})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=0, upserted=0))
    assert repository.batches == []


def test_passes_the_configured_per_page_to_the_port():
    port = FakePort({(1, 250): Ok(emd_page(1, 5, total_count=5))})
    repository = RecordingRepository()

    use_case(port, repository, config(per_page=250)).execute()

    assert port.calls == [(1, 250)]


# ── fail-fast ─────────────────────────────────────────────────────────────────


def test_fails_fast_and_skips_the_remaining_pages_when_page_two_returns_err():
    failure = domain_error.NetworkError("connect timed out")
    port = FakePort(
        {
            (1, 1000): Ok(emd_page(1, 1000, total_count=3000)),
            (2, 1000): Err(failure),
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Err(failure)
    assert port.calls == [(1, 1000), (2, 1000)]
    # 실패 이전 페이지는 이미 커밋되어 있다 (페이지 단위 트랜잭션, 부분 성공 유지)
    assert len(repository.batches) == 1


def test_returns_the_very_first_failure_when_page_one_already_fails():
    failure = domain_error.ParseError("data 필드 없음 (page=1)")
    port = FakePort({(1, 1000): Err(failure)})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Err(failure)
    assert repository.batches == []


# ── 폐지여부 필터 ─────────────────────────────────────────────────────────────


def test_keeps_only_the_records_whose_abolished_field_is_alive():
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("1111010100", "서울특별시 종로구 청운동", "존재"),
                    record("1111010200", "서울특별시 종로구 신교동", "폐지"),
                    record("1111010300", "서울특별시 종로구 궁정동", None),
                    record("1111010400", "서울특별시 종로구 효자동", ""),
                    total_count=4,
                )
            )
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert [c.code for c in repository.batches[0]] == ["1111010100"]
    assert result.value.total == 1


def test_absorbs_whitespace_around_the_alive_marker():
    port = FakePort({(1, 1000): Ok(page_of(record("1111010100", "청운동", " 존재 "), total_count=1))})
    repository = RecordingRepository()

    use_case(port, repository).execute()

    assert [c.code for c in repository.batches[0]] == ["1111010100"]


# ── 리(里) 레벨 / 형식 불량 제외 ───────────────────────────────────────────────


def test_excludes_ri_level_and_malformed_codes_while_keeping_sido_sigungu_emd():
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("1100000000", "서울특별시", "존재"),
                    record("1111000000", "서울특별시 종로구", "존재"),
                    record("1111010100", "서울특별시 종로구 청운동", "존재"),
                    record("4173025321", "경기도 이천시 부발읍 아미리", "존재"),  # 리 레벨
                    record("411730253", "자릿수 불량", "존재"),
                    record("11110101AB", "숫자 아님", "존재"),
                    record("0000000000", "제로 코드", "존재"),
                    total_count=7,
                )
            )
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert [c.code for c in repository.batches[0]] == ["1100000000", "1111000000", "1111010100"]
    assert result.value.total == 3


# ── 도메인 변환 ───────────────────────────────────────────────────────────────


def test_maps_each_level_onto_the_right_sido_sigungu_emd_columns():
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("4100000000", "경기도", "존재"),
                    record("4173000000", "경기도 이천시", "존재"),
                    record("4173025300", "경기도 이천시 부발읍", "존재"),
                    total_count=3,
                )
            )
        }
    )
    repository = RecordingRepository()

    use_case(port, repository).execute()

    batch = repository.batches[0]
    assert batch[0] == SigunguCodeData(
        code="4100000000",
        level=SigunguCodeLevel.SIDO,
        sido_code="41",
        sigungu_code=None,
        emd_code=None,
        name="경기도",
    )
    assert batch[1] == SigunguCodeData(
        code="4173000000",
        level=SigunguCodeLevel.SIGUNGU,
        sido_code="41",
        sigungu_code="41730",
        emd_code=None,
        name="경기도 이천시",
    )
    assert batch[2] == SigunguCodeData(
        code="4173025300",
        level=SigunguCodeLevel.EMD,
        sido_code="41",
        sigungu_code="41730",
        emd_code="41730253",
        name="경기도 이천시 부발읍",
    )


def test_trims_the_name_but_never_splits_it_on_whitespace():
    port = FakePort(
        {(1, 1000): Ok(page_of(record("1111010100", "  서울특별시 종로구 청운동  ", "존재"), total_count=1))}
    )
    repository = RecordingRepository()

    use_case(port, repository).execute()

    assert repository.batches[0][0].name == "서울특별시 종로구 청운동"


# ── 집계 (SyncResult 의미) ────────────────────────────────────────────────────


def test_reports_total_as_the_rows_that_survived_the_filters_not_the_rows_received():
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("1111010100", "청운동", "존재"),
                    record("1111010101", "청운1리", "존재"),  # 리 레벨 — 수신했지만 저장 대상 아님
                    record("1111010200", "신교동", "폐지"),  # 폐지 — 수신했지만 저장 대상 아님
                    total_count=3,
                )
            )
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    # 수신 3건이지만 total 은 필터 통과 1건이어야 한다
    assert result.value.total == 1
    assert result.value.upserted == 1
    assert result.value.closed == 0


def test_reports_upserted_as_the_rows_the_change_detection_guard_actually_wrote():
    port = FakePort(
        {
            (1, 10): Ok(emd_page(1, 10, total_count=20)),
            (2, 10): Ok(emd_page(2, 10, total_count=20)),
        }
    )
    # 변경 감지 가드로 실제 변경은 3건뿐인 상황
    repository = RecordingRepository(returns=[3, 0])

    result = use_case(port, repository, config(per_page=10)).execute()

    assert result.value.total == 20
    assert result.value.upserted == 3


# ── 전량 탈락 방어 ────────────────────────────────────────────────────────────


def test_fails_with_parse_error_when_rows_were_received_but_all_were_filtered_out():
    port = FakePort({(1, 1000): Ok(page_of(record("1111010101", "청운1리", "존재"), total_count=1))})
    repository = RecordingRepository(returns=[0])

    result = use_case(port, repository).execute()

    # 성공으로 보고하면 테이블이 낡은 채 방치되어도 아무도 알아채지 못한다
    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)
    assert "저장 대상 0건" in result.error.message


def test_fails_when_the_abolished_field_disappears_from_the_response_schema():
    # 데이터셋 판이 바뀌어 폐지여부가 전부 None 이 되면 allowlist 필터가 전 건을 떨군다
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("1100000000", "서울특별시", None),
                    record("1111000000", "서울특별시 종로구", None),
                    record("1111010100", "서울특별시 종로구 청운동", None),
                    total_count=3,
                )
            )
        }
    )
    repository = RecordingRepository(returns=[0])

    result = use_case(port, repository).execute()

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.ParseError)


def test_does_not_fail_when_the_dataset_itself_is_legitimately_empty():
    # 수신 0건이면 필터 탓이 아니므로 가드가 발동하면 안 된다
    port = FakePort({(1, 1000): Ok(emd_page(1, 0, total_count=0))})
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=0, upserted=0))


def test_does_not_fail_when_at_least_one_record_survives_the_filters():
    port = FakePort(
        {
            (1, 1000): Ok(
                page_of(
                    record("1111010100", "청운동", "존재"),
                    record("1111010101", "청운1리", "존재"),
                    total_count=2,
                )
            )
        }
    )
    repository = RecordingRepository()

    result = use_case(port, repository).execute()

    assert result == Ok(SyncResult(total=1, upserted=1))
