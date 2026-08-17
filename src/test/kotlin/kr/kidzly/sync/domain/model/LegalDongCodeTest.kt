package kr.kidzly.sync.domain.model

import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe

/**
 * [ParsedLegalDongCode.parse] 레벨 판별 / 코드 절단 단위 테스트 (설계 §3.1 검증 케이스 표).
 *
 * 외부 의존이 없는 순수 도메인 규칙이라 Spring 컨텍스트 없이 실행된다.
 */
class LegalDongCodeTest : FunSpec({

    // ── 레벨 판별 ─────────────────────────────────────────────────────────────

    test("should classify a code whose last 8 digits are zero as SIDO") {
        val parsed = ParsedLegalDongCode.parse("1100000000").shouldNotBeNull()

        parsed.level shouldBe SigunguCodeLevel.SIDO
        parsed.code shouldBe "1100000000"
        parsed.sidoCode shouldBe "11"
        parsed.sigunguCode shouldBe null
        parsed.emdCode shouldBe null
    }

    test("should classify a code whose last 5 digits are zero as SIGUNGU") {
        val parsed = ParsedLegalDongCode.parse("1111000000").shouldNotBeNull()

        parsed.level shouldBe SigunguCodeLevel.SIGUNGU
        parsed.sidoCode shouldBe "11"
        parsed.sigunguCode shouldBe "11110"
        parsed.emdCode shouldBe null
    }

    test("should classify a code whose last 2 digits are zero as EMD") {
        val parsed = ParsedLegalDongCode.parse("1111010100").shouldNotBeNull()

        parsed.level shouldBe SigunguCodeLevel.EMD
        parsed.sidoCode shouldBe "11"
        parsed.sigunguCode shouldBe "11110"
        parsed.emdCode shouldBe "11110101"
    }

    test("should classify the new Jeju code 5000000000 as SIDO") {
        val parsed = ParsedLegalDongCode.parse("5000000000").shouldNotBeNull()

        parsed.level shouldBe SigunguCodeLevel.SIDO
        parsed.sidoCode shouldBe "50"
    }

    test("should not let the SIDO branch be swallowed by the SIGUNGU condition") {
        // 1100000000 은 n % 100_000L == 0L 도 참이라 분기 순서가 뒤바뀌면 SIGUNGU로 오분류된다
        val sido = ParsedLegalDongCode.parse("1100000000").shouldNotBeNull()

        sido.level shouldBe SigunguCodeLevel.SIDO
        sido.sigunguCode shouldBe null
    }

    // ── Int 오버플로 함정 (설계 §7.3) ──────────────────────────────────────────

    test("should classify codes above Int.MAX_VALUE without overflow at every level") {
        // 4173025321 > 2_147_483_647 — Int 연산이면 오버플로로 조용히 틀린 답이 나온다
        ParsedLegalDongCode.parse("4100000000").shouldNotBeNull().level shouldBe SigunguCodeLevel.SIDO
        ParsedLegalDongCode.parse("4173000000").shouldNotBeNull().level shouldBe SigunguCodeLevel.SIGUNGU
        ParsedLegalDongCode.parse("4173025300").shouldNotBeNull().level shouldBe SigunguCodeLevel.EMD
        ParsedLegalDongCode.parse("4173025321") shouldBe null
    }

    test("should cut the codes correctly for an EMD code above Int.MAX_VALUE") {
        val parsed = ParsedLegalDongCode.parse("4173025300").shouldNotBeNull()

        parsed.sidoCode shouldBe "41"
        parsed.sigunguCode shouldBe "41730"
        parsed.emdCode shouldBe "41730253"
    }

    test("should classify the largest possible 10 digit code without overflow") {
        // Long 경계 확인용 — Int 였다면 음수로 뒤집힌다
        ParsedLegalDongCode.parse("9999999999") shouldBe null
        ParsedLegalDongCode.parse("9999999900").shouldNotBeNull().level shouldBe SigunguCodeLevel.EMD
        ParsedLegalDongCode.parse("9999900000").shouldNotBeNull().level shouldBe SigunguCodeLevel.SIGUNGU
        ParsedLegalDongCode.parse("9900000000").shouldNotBeNull().level shouldBe SigunguCodeLevel.SIDO
    }

    // ── 리(里) 레벨 제외 ───────────────────────────────────────────────────────

    test("should return null for a ri level code (last 2 digits are not zero)") {
        ParsedLegalDongCode.parse("4173025321") shouldBe null
        ParsedLegalDongCode.parse("1111010101") shouldBe null
        ParsedLegalDongCode.parse("4825032025") shouldBe null
    }

    // ── 형식 불량 / 0 방어 ────────────────────────────────────────────────────

    test("should return null when the code is shorter than 10 digits") {
        ParsedLegalDongCode.parse("111101010") shouldBe null
    }

    test("should return null when the code is longer than 10 digits") {
        ParsedLegalDongCode.parse("11110101000") shouldBe null
    }

    test("should return null when the code contains a non digit character") {
        ParsedLegalDongCode.parse("11110101AB") shouldBe null
        ParsedLegalDongCode.parse("11110101-0") shouldBe null
    }

    test("should return null for a non ASCII digit that Char.isDigit would accept") {
        // 아라비아-인도 숫자(٠١٢…). [0-9]{10} 정규식이라야 걸러진다
        ParsedLegalDongCode.parse("١١١١٠١٠١٠٠") shouldBe null
    }

    test("should return null for the all zero code") {
        ParsedLegalDongCode.parse("0000000000") shouldBe null
    }

    test("should return null for a blank input") {
        ParsedLegalDongCode.parse("") shouldBe null
        ParsedLegalDongCode.parse("          ") shouldBe null
    }

    // ── 정규화 ────────────────────────────────────────────────────────────────

    test("should trim surrounding whitespace before parsing and store the trimmed code") {
        val parsed = ParsedLegalDongCode.parse("  1111010100 \n").shouldNotBeNull()

        parsed.code shouldBe "1111010100"
        parsed.level shouldBe SigunguCodeLevel.EMD
    }

    test("should preserve the raw 10 digit code as the primary key value") {
        // 나눗셈 절단이면 선행 0이 사라진다 — substring 절단이라야 원본이 보존된다
        val parsed = ParsedLegalDongCode.parse("0511010100")

        // 시도코드 05는 실제로는 존재하지 않지만 선행 0 보존 자체를 검증한다
        parsed.shouldNotBeNull()
        parsed.code shouldBe "0511010100"
        parsed.sidoCode shouldBe "05"
        parsed.sigunguCode shouldBe "05110"
        parsed.emdCode shouldBe "05110101"
    }

    test("should derive every code from the raw string so that prefixes always match") {
        val parsed = ParsedLegalDongCode.parse("2611010100").shouldNotBeNull()
        val sigunguCode = parsed.sigunguCode.shouldNotBeNull()
        val emdCode = parsed.emdCode.shouldNotBeNull()

        parsed.code.startsWith(parsed.sidoCode) shouldBe true
        parsed.code.startsWith(sigunguCode) shouldBe true
        parsed.code.startsWith(emdCode) shouldBe true
        parsed.sidoCode.length shouldBe 2
        sigunguCode.length shouldBe 5
        emdCode.length shouldBe 8
    }
})
