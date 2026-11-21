"""``FullSyncUseCase`` 순회 / 두 층의 실패 처리 / 집계 단위 테스트."""

from __future__ import annotations

from kidzly_sync.application.model import SyncResult
from kidzly_sync.application.usecase.full_sync import SIDO_LIST, FullSyncUseCase
from kidzly_sync.domain import error as domain_error
from kidzly_sync.domain.result import Err, Ok
from tests.unit.childcare_fixtures import (
    FakeChildcarePort,
    RecordingDaycareRepository,
    RecordingSigunguRepository,
    config,
    daycare,
    sigungu,
)


def use_case(port, daycare_repo, sigungu_repo) -> FullSyncUseCase:
    return FullSyncUseCase(port, daycare_repo, sigungu_repo, config())


def all_sido_empty() -> dict[str, object]:
    """17개 시도 전부 빈 시군구 목록으로 채운다 (특정 시도만 바꿔 쓰기 위한 바탕)."""
    return {sido: Ok([]) for sido in SIDO_LIST}


# ── 순회 ──────────────────────────────────────────────────────────────────────


def with_seoul(*arcodes: str) -> dict[str, object]:
    """서울만 시군구가 있고 나머지 시도는 0건 — 전부 0건이면 실패라 하나는 채워 둔다."""
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu(a) for a in arcodes])
    return lists


def test_visits_every_seed_sido_when_the_db_knows_no_other_name():
    port = FakeChildcarePort(sigungu_lists=with_seoul("11110"), details={"11110": Ok([])})

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=0, upserted=0))
    assert port.sigungu_calls == list(SIDO_LIST)


def test_also_visits_sido_names_the_api_returned_before():
    # 2026 광주·전남 통합 — 증분 동기화(cpmsapi030)가 들여온 새 시도명을 다음 전체 동기화가 따라간다
    lists = with_seoul("11110")
    lists["전남광주통합특별시"] = Ok([sigungu("12110", sidoname="전남광주통합특별시", sigunname="목포시")])
    port = FakeChildcarePort(
        sigungu_lists=lists, details={"11110": Ok([]), "12110": Ok([daycare("46110000101")])}
    )
    daycare_repo = RecordingDaycareRepository(sido_names=["서울특별시", "전남광주통합특별시"])

    result = use_case(port, daycare_repo, RecordingSigunguRepository(sido_names=["광주광역시"])).execute()

    assert port.sigungu_calls == [*SIDO_LIST, "전남광주통합특별시"]
    assert port.detail_calls == ["11110", "12110"]
    assert result == Ok(SyncResult(total=1, upserted=1))


def test_takes_new_sido_names_from_the_sigungu_table_too():
    lists = with_seoul("11110")
    lists["새특별시"] = Ok([])
    port = FakeChildcarePort(sigungu_lists=lists, details={"11110": Ok([])})

    use_case(
        port, RecordingDaycareRepository(), RecordingSigunguRepository(sido_names=["새특별시"])
    ).execute()

    assert port.sigungu_calls[-1] == "새특별시"


def test_skips_a_sido_with_no_sigungu_instead_of_failing():
    # 개편으로 사라진 옛 시도명은 INFO-200(0건)을 돌려준다 — 실패가 아니다
    port = FakeChildcarePort(sigungu_lists=with_seoul("11110"), details={"11110": Ok([daycare("A")])})
    sigungu_repo = RecordingSigunguRepository()

    result = use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert isinstance(result, Ok)
    # 0건 시도는 저장할 것도 없다
    assert len(sigungu_repo.batches) == 1


def test_fails_when_every_sido_returns_no_sigungu():
    # 전부 0건이면 개편이 아니라 API 이상이다 — 성공으로 닫으면 아무도 모른다
    port = FakeChildcarePort(sigungu_lists=all_sido_empty())

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert isinstance(result, Err)
    assert isinstance(result.error, domain_error.Unknown)


def test_upserts_the_sigungu_list_of_every_sido_before_walking_its_daycares():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={"11110": Ok([daycare("A")]), "11140": Ok([daycare("B")])},
    )
    sigungu_repo = RecordingSigunguRepository()

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert len(sigungu_repo.batches) == 1
    assert [s.arcode for s in sigungu_repo.batches[0]] == ["11110", "11140"]
    assert port.detail_calls == ["11110", "11140"]


def test_aggregates_received_and_changed_rows_across_sigungu():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Ok([daycare("A"), daycare("B")]),
            "11140": Ok([daycare("C")]),
        },
    )
    # 변경 감지 가드로 실제 변경은 1건뿐인 상황
    daycare_repo = RecordingDaycareRepository(upsert_returns=[1, 0])

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=3, upserted=1))


# ── 실패 처리: 시군구 목록은 fail-fast ─────────────────────────────────────────


def test_fails_fast_when_a_sido_sigungu_list_fails():
    failure = domain_error.NetworkError("connect timed out")
    lists = all_sido_empty()
    lists["부산광역시"] = Err(failure)
    port = FakeChildcarePort(sigungu_lists=lists)

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Err(failure)
    # 서울(1번째)까지만 돌고 부산(2번째)에서 멈춘다
    assert port.sigungu_calls == ["서울특별시", "부산광역시"]


def test_does_not_touch_the_daycare_repository_when_the_first_sido_fails():
    lists = all_sido_empty()
    lists["서울특별시"] = Err(domain_error.Unauthorized())
    port = FakeChildcarePort(sigungu_lists=lists)
    daycare_repo = RecordingDaycareRepository()

    use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert daycare_repo.batches == []


# ── 실패 처리: 어린이집 상세는 건너뛴다 ────────────────────────────────────────


def test_skips_a_failing_sigungu_and_keeps_going():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140"), sigungu("11170")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Ok([daycare("A")]),
            # 시군구 하나가 실패해도 나머지는 살린다 — 주 1회 재실행이 메운다
            "11140": Err(domain_error.ApiCallError(500, None, "서버 오류")),
            "11170": Ok([daycare("C")]),
        },
    )

    result = use_case(port, RecordingDaycareRepository(), RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=2, upserted=2))
    assert port.detail_calls == ["11110", "11140", "11170"]


def test_a_failing_sigungu_contributes_nothing_to_the_totals():
    lists = all_sido_empty()
    lists["서울특별시"] = Ok([sigungu("11110"), sigungu("11140")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={
            "11110": Err(domain_error.ParseError("깨진 XML")),
            "11140": Ok([daycare("A"), daycare("B")]),
        },
    )
    daycare_repo = RecordingDaycareRepository()

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert result == Ok(SyncResult(total=2, upserted=2))
    # 실패한 시군구는 upsert 자체가 호출되지 않는다
    assert len(daycare_repo.batches) == 1


# ── 미갱신 집계 ───────────────────────────────────────────────────────────────


def test_counts_active_daycares_the_api_did_not_return_by_sido():
    port = FakeChildcarePort(
        sigungu_lists=with_seoul("11110"),
        details={"11110": Ok([daycare("A"), daycare("B")])},
    )
    daycare_repo = RecordingDaycareRepository(
        active_by_sido={
            "서울특별시": {"A": "A", "B": "B", "C": "C"},
            "광주광역시": {"G1": "G1", "G2": "G2"},
        }
    )

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert daycare_repo.excluded_codes == {"A", "B"}
    assert result == Ok(SyncResult(total=2, upserted=2, stale_by_sido=(("광주광역시", 2), ("서울특별시", 1))))
    assert result.value.stale_count == 3


def test_daycares_of_a_failing_sigungu_show_up_as_stale():
    # 시군구 상세 실패는 건너뛰지만 결과에는 남아야 한다 — 로그 한 줄로 묻히지 않게
    port = FakeChildcarePort(
        sigungu_lists=with_seoul("11110", "11140"),
        details={
            "11110": Ok([daycare("A")]),
            "11140": Err(domain_error.ApiCallError(500, None, "서버 오류")),
        },
    )
    daycare_repo = RecordingDaycareRepository(active_by_sido={"서울특별시": {"A": "A", "B": "B"}})

    result = use_case(port, daycare_repo, RecordingSigunguRepository()).execute()

    assert result.value.stale_by_sido == (("서울특별시", 1),)


# ── 옛 시군구 정리 ─────────────────────────────────────────────────────────────


def test_keeps_only_the_sigungu_the_api_returned_this_run():
    # 개편으로 사라진 옛 시군구가 sigungus 에 남으면 웹에 빈 지역 칩이 계속 보인다
    lists = with_seoul("11110", "11140")
    lists["전남광주통합특별시"] = Ok([sigungu("12110", sidoname="전남광주통합특별시")])
    port = FakeChildcarePort(
        sigungu_lists=lists,
        details={"11110": Ok([]), "11140": Ok([]), "12110": Ok([])},
    )
    sigungu_repo = RecordingSigunguRepository(sido_names=["전남광주통합특별시"])

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert sigungu_repo.kept_arcodes == {"11110", "11140", "12110"}


def test_keeps_a_sigungu_whose_detail_call_failed():
    # 상세(cpmsapi030) 실패는 그 시군구가 사라졌다는 뜻이 아니다
    port = FakeChildcarePort(
        sigungu_lists=with_seoul("11110"),
        details={"11110": Err(domain_error.ApiCallError(500, None, "서버 오류"))},
    )
    sigungu_repo = RecordingSigunguRepository()

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert sigungu_repo.kept_arcodes == {"11110"}


def test_deletes_nothing_when_a_sigungu_list_call_fails():
    # 목록이 불완전하면 지울 기준이 없다
    lists = with_seoul("11110")
    lists["부산광역시"] = Err(domain_error.NetworkError("timeout"))
    port = FakeChildcarePort(sigungu_lists=lists, details={"11110": Ok([])})
    sigungu_repo = RecordingSigunguRepository()

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert sigungu_repo.kept_arcodes is None


def test_deletes_nothing_when_every_sido_is_empty():
    port = FakeChildcarePort(sigungu_lists=all_sido_empty())
    sigungu_repo = RecordingSigunguRepository()

    use_case(port, RecordingDaycareRepository(), sigungu_repo).execute()

    assert sigungu_repo.kept_arcodes is None
