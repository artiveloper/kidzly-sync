package kr.kidzly.sync.domain.model

import org.slf4j.LoggerFactory

/** 법정동코드 레벨. 리(里) 레벨은 동기화 대상이 아니므로 상수가 없다. */
enum class SigunguCodeLevel { SIDO, SIGUNGU, EMD }

/**
 * 10자리 법정동코드를 레벨별 절대코드로 분해한 값 객체.
 *
 * 분해는 **자릿수 고정 위치 문자열 절단**으로만 한다.
 * - `법정동명`을 공백 split 하지 않는다 (지명에 공백이 섞인 케이스에서 깨짐)
 * - 숫자 나눗셈으로 자르지 않는다 (선행 0 소실 위험)
 */
data class ParsedLegalDongCode(
    val code: String,
    val level: SigunguCodeLevel,
    val sidoCode: String,
    val sigunguCode: String?,
    val emdCode: String?,
) {
    companion object {
        private val log = LoggerFactory.getLogger(ParsedLegalDongCode::class.java)

        private val CODE_PATTERN = Regex("^[0-9]{10}$")

        /**
         * @return 파싱 실패(10자리 숫자가 아님, 0) 또는 리(里) 레벨이면 null — 호출자가 제외한다.
         */
        fun parse(rawCode: String): ParsedLegalDongCode? {
            val s = rawCode.trim()
            if (!CODE_PATTERN.matches(s)) {
                log.warn("법정동코드 형식 불량 — 제외 (code=$rawCode)")
                return null
            }

            // 10자리는 Int 범위(21억)를 넘으므로 Long으로 다룬다
            val n = s.toLong()
            if (n <= 0L) {
                log.warn("법정동코드 값 오류 — 제외 (code=$rawCode)")
                return null
            }

            // SIDO 조건이 SIGUNGU/EMD 조건을 삼키므로 분기 순서를 바꾸면 안 된다
            val level = when {
                n % 100_000_000L == 0L -> SigunguCodeLevel.SIDO
                n % 100_000L == 0L -> SigunguCodeLevel.SIGUNGU
                n % 100L == 0L -> SigunguCodeLevel.EMD
                // 리(里) 레벨 — 동기화 대상이 아닌 정상 제외이므로 로그를 남기지 않는다
                else -> return null
            }

            return ParsedLegalDongCode(
                code = s,
                level = level,
                sidoCode = s.substring(0, 2),
                sigunguCode = if (level != SigunguCodeLevel.SIDO) s.substring(0, 5) else null,
                emdCode = if (level == SigunguCodeLevel.EMD) s.substring(0, 8) else null,
            )
        }
    }
}
