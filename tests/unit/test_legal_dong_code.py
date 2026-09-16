"""``parse_legal_dong_code`` 레벨 판별 / 코드 절단 단위 테스트.

외부 의존이 없는 순수 도메인 규칙이다.
"""

from __future__ import annotations

import pytest

from kidzly_sync.domain.legal_dong_code import SigunguCodeLevel, parse_legal_dong_code

# ── 레벨 판별 ─────────────────────────────────────────────────────────────────


def test_classifies_code_with_eight_trailing_zeros_as_sido():
    parsed = parse_legal_dong_code("1100000000")

    assert parsed is not None
    assert parsed.level is SigunguCodeLevel.SIDO
    assert parsed.code == "1100000000"
    assert parsed.sido_code == "11"
    assert parsed.sigungu_code is None
    assert parsed.emd_code is None


def test_classifies_code_with_five_trailing_zeros_as_sigungu():
    parsed = parse_legal_dong_code("1111000000")

    assert parsed is not None
    assert parsed.level is SigunguCodeLevel.SIGUNGU
    assert parsed.sido_code == "11"
    assert parsed.sigungu_code == "11110"
    assert parsed.emd_code is None


def test_classifies_code_with_two_trailing_zeros_as_emd():
    parsed = parse_legal_dong_code("1111010100")

    assert parsed is not None
    assert parsed.level is SigunguCodeLevel.EMD
    assert parsed.sido_code == "11"
    assert parsed.sigungu_code == "11110"
    assert parsed.emd_code == "11110101"


def test_classifies_the_new_jeju_code_as_sido():
    parsed = parse_legal_dong_code("5000000000")

    assert parsed is not None
    assert parsed.level is SigunguCodeLevel.SIDO
    assert parsed.sido_code == "50"


def test_sido_branch_is_not_swallowed_by_the_sigungu_condition():
    # 1100000000 은 n % 100_000 == 0 도 참이라 분기 순서가 뒤바뀌면 SIGUNGU 로 오분류된다
    parsed = parse_legal_dong_code("1100000000")

    assert parsed is not None
    assert parsed.level is SigunguCodeLevel.SIDO
    assert parsed.sigungu_code is None


# ── 큰 수 처리 (Kotlin 의 Int 오버플로 함정에 해당) ────────────────────────────


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("4100000000", SigunguCodeLevel.SIDO),
        ("4173000000", SigunguCodeLevel.SIGUNGU),
        ("4173025300", SigunguCodeLevel.EMD),
    ],
)
def test_classifies_codes_above_int_max_at_every_level(code, expected):
    parsed = parse_legal_dong_code(code)

    assert parsed is not None
    assert parsed.level is expected


def test_cuts_the_codes_correctly_for_a_large_emd_code():
    parsed = parse_legal_dong_code("4173025300")

    assert parsed is not None
    assert parsed.sido_code == "41"
    assert parsed.sigungu_code == "41730"
    assert parsed.emd_code == "41730253"


def test_classifies_the_largest_possible_ten_digit_code():
    assert parse_legal_dong_code("9999999999") is None
    assert parse_legal_dong_code("9999999900").level is SigunguCodeLevel.EMD
    assert parse_legal_dong_code("9999900000").level is SigunguCodeLevel.SIGUNGU
    assert parse_legal_dong_code("9900000000").level is SigunguCodeLevel.SIDO


# ── 리(里) 레벨 제외 ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("code", ["4173025321", "1111010101", "4825032025"])
def test_returns_none_for_ri_level_codes(code):
    assert parse_legal_dong_code(code) is None


# ── 형식 불량 / 0 방어 ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "code",
    [
        "111101010",  # 10자리 미만
        "11110101000",  # 10자리 초과
        "11110101AB",  # 숫자 아님
        "11110101-0",
        "١١١١٠١٠١٠٠",  # 아라비아-인도 숫자 — str.isdigit() 은 참이라 정규식이라야 걸러진다
        "0000000000",  # 전부 0
        "",
        "          ",
    ],
)
def test_returns_none_for_malformed_codes(code):
    assert parse_legal_dong_code(code) is None


# ── 정규화 ────────────────────────────────────────────────────────────────────


def test_trims_surrounding_whitespace_and_stores_the_trimmed_code():
    parsed = parse_legal_dong_code("  1111010100 \n")

    assert parsed is not None
    assert parsed.code == "1111010100"
    assert parsed.level is SigunguCodeLevel.EMD


def test_preserves_the_raw_ten_digit_code_as_the_primary_key_value():
    # 나눗셈 절단이면 선행 0이 사라진다 — 문자열 절단이라야 원본이 보존된다
    # 시도코드 05는 실제로는 존재하지 않지만 선행 0 보존 자체를 검증한다
    parsed = parse_legal_dong_code("0511010100")

    assert parsed is not None
    assert parsed.code == "0511010100"
    assert parsed.sido_code == "05"
    assert parsed.sigungu_code == "05110"
    assert parsed.emd_code == "05110101"


def test_every_code_is_a_prefix_of_the_raw_code():
    parsed = parse_legal_dong_code("2611010100")

    assert parsed is not None
    assert parsed.sigungu_code is not None
    assert parsed.emd_code is not None
    assert parsed.code.startswith(parsed.sido_code)
    assert parsed.code.startswith(parsed.sigungu_code)
    assert parsed.code.startswith(parsed.emd_code)
    assert len(parsed.sido_code) == 2
    assert len(parsed.sigungu_code) == 5
    assert len(parsed.emd_code) == 8
