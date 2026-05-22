package kr.kidzly.sync.infrastructure.ai

import com.fasterxml.jackson.databind.ObjectMapper
import kr.kidzly.sync.domain.entity.Daycare
import org.springframework.stereotype.Component
import java.time.LocalDate

@Component
class DaycareJsonBuilder(private val objectMapper: ObjectMapper) {

    fun build(d: Daycare): String {
        val occupancyRate = if ((d.capacity ?: 0) > 0) {
            (((d.currentChildCount ?: 0) * 100.0) / d.capacity!!).toInt()
        } else null

        val data = linkedMapOf(
            "기본정보" to linkedMapOf(
                "이름" to d.name,
                "유형" to d.typeName,
                "인가일" to d.certifiedDate,
                "운영연수" to calculateOperationYears(d.certifiedDate),
                "상태" to d.status,
            ),
            "규모" to linkedMapOf(
                "정원" to d.capacity,
                "현원" to d.currentChildCount,
                "충원율_퍼센트" to occupancyRate,
                "보육실수" to d.nurseryRoomCount,
                "보육실면적_제곱미터" to d.nurseryRoomSize,
            ),
            "시설" to linkedMapOf(
                "놀이터수" to d.playgroundCount,
                "CCTV수" to d.cctvCount,
                "차량운영" to d.vehicleOperation,
            ),
            "대기아동" to linkedMapOf(
                "총대기수" to d.waitingChildTotal,
                "0세" to d.waitingChildAge0,
                "1세" to d.waitingChildAge1,
                "2세" to d.waitingChildAge2,
                "3세" to d.waitingChildAge3,
                "4세" to d.waitingChildAge4,
                "5세" to d.waitingChildAge5,
                "6세이상" to d.waitingChildAgeOver6,
            ),
            "연령별반수" to linkedMapOf(
                "0세반" to d.classCountAge0,
                "1세반" to d.classCountAge1,
                "2세반" to d.classCountAge2,
                "3세반" to d.classCountAge3,
                "4세반" to d.classCountAge4,
                "5세반" to d.classCountAge5,
                "영아혼합반" to d.classCountInfantMixed,
                "유아혼합반" to d.classCountChildMixed,
                "장애아전문반" to d.classCountSpecial,
                "총반수" to d.classCountTotal,
            ),
            "연령별아동수" to linkedMapOf(
                "0세" to d.childCountAge0,
                "1세" to d.childCountAge1,
                "2세" to d.childCountAge2,
                "3세" to d.childCountAge3,
                "4세" to d.childCountAge4,
                "5세" to d.childCountAge5,
                "영아혼합" to d.childCountInfantMixed,
                "유아혼합" to d.childCountChildMixed,
                "장애아" to d.childCountSpecial,
                "합계" to d.childCountTotal,
            ),
            "교직원근속분포" to linkedMapOf(
                "1년미만" to d.staffTenureUnder1y,
                "1~2년" to d.staffTenure1yTo2y,
                "2~4년" to d.staffTenure2yTo4y,
                "4~6년" to d.staffTenure4yTo6y,
                "6년이상" to d.staffTenureOver6y,
            ),
            "교직원직종현황" to linkedMapOf(
                "원장" to d.staffDirectorCount,
                "보육교사" to d.staffTeacherCount,
                "특수교사" to d.staffSpecialTeacherCount,
                "치료사" to d.staffTherapistCount,
                "영양사" to d.staffNutritionistCount,
                "간호사" to d.staffNurseCount,
                "간호조무사" to d.staffNursingAssistantCount,
                "조리원" to d.staffCookCount,
                "사무원" to d.staffOfficeCount,
                "합계" to d.staffTotal,
            ),
        )

        return objectMapper.writeValueAsString(data)
    }

    private fun calculateOperationYears(certifiedDate: String?): Int? {
        if (certifiedDate == null) return null
        val cleaned = certifiedDate.replace("-", "")
        if (cleaned.length < 4) return null
        return cleaned.take(4).toIntOrNull()?.let { LocalDate.now().year - it }
    }
}
