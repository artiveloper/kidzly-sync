package kr.kidzly.sync.application.model

data class SigunguInfo(
    val arcode: String,
    val sidoname: String,
    val sigunname: String,
)

data class NewDaycareInfo(
    val daycareCode: String,
    val sigunguCode: String,
)

data class ClosedDaycareInfo(
    val daycareCode: String,
    val abolishedDate: String?,
)

data class DaycareData(
    val daycareCode: String,
    val sigunguCode: String,
    val sidoName: String?,
    val sigunguName: String?,
    val name: String,
    val typeName: String?,
    val status: String?,
    val zipCode: String?,
    val address: String?,
    val phone: String?,
    val fax: String?,
    val homepage: String?,
    val latitude: String?,
    val longitude: String?,
    val capacity: Int?,
    val currentChildCount: Int?,
    val nurseryRoomCount: Int?,
    val nurseryRoomSize: java.math.BigDecimal?,
    val playgroundCount: Int?,
    val cctvCount: Int?,
    val childcareStaffCount: Int?,
    val vehicleOperation: String?,
    val representativeName: String?,
    val certifiedDate: String?,
    val pauseStartDate: String?,
    val pauseEndDate: String?,
    val abolishedDate: String?,
    val dataStandardDate: String?,
    val services: String?,
    // 반수 (연령별)
    val classCountAge0: Int?,
    val classCountAge1: Int?,
    val classCountAge2: Int?,
    val classCountAge3: Int?,
    val classCountAge4: Int?,
    val classCountAge5: Int?,
    val classCountInfantMixed: Int?,
    val classCountChildMixed: Int?,
    val classCountSpecial: Int?,
    val classCountTotal: Int?,
    // 아동수 (연령별)
    val childCountAge0: Int?,
    val childCountAge1: Int?,
    val childCountAge2: Int?,
    val childCountAge3: Int?,
    val childCountAge4: Int?,
    val childCountAge5: Int?,
    val childCountInfantMixed: Int?,
    val childCountChildMixed: Int?,
    val childCountSpecial: Int?,
    val childCountTotal: Int?,
    // 교직원 근속년수
    val staffTenureUnder1y: Double?,
    val staffTenure1yTo2y: Double?,
    val staffTenure2yTo4y: Double?,
    val staffTenure4yTo6y: Double?,
    val staffTenureOver6y: Double?,
    // 교직원 직종별
    val staffDirectorCount: Int?,
    val staffTeacherCount: Int?,
    val staffSpecialTeacherCount: Int?,
    val staffTherapistCount: Int?,
    val staffNutritionistCount: Int?,
    val staffNurseCount: Int?,
    val staffNursingAssistantCount: Int?,
    val staffCookCount: Int?,
    val staffOfficeCount: Int?,
    val staffTotal: Int?,
    // 입소대기 아동수
    val waitingChildAge0: Int?,
    val waitingChildAge1: Int?,
    val waitingChildAge2: Int?,
    val waitingChildAge3: Int?,
    val waitingChildAge4: Int?,
    val waitingChildAge5: Int?,
    val waitingChildAgeOver6: Int?,
    val waitingChildTotal: Int?,
)

data class SyncResult(
    val total: Int,
    val upserted: Int,
    val closed: Int = 0,
)
