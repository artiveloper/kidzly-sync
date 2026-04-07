package kr.kidzly.sync.domain.entity

import jakarta.persistence.*
import java.math.BigDecimal
import java.time.LocalDateTime

@Entity
@Table(
    name = "daycares",
    indexes = [
        Index(name = "idx_daycares_sigungu_code", columnList = "sigungu_code"),
        Index(name = "idx_daycares_status", columnList = "status"),
    ],
)
class Daycare(
    @Id
    @Column(name = "daycare_code", length = 20)
    val daycareCode: String,

    @Column(name = "sigungu_code", length = 10, nullable = false)
    val sigunguCode: String,

    @Column(name = "sido_name", length = 50)
    val sidoName: String?,

    @Column(name = "sigungu_name", length = 50)
    val sigunguName: String?,

    @Column(name = "name", length = 150, nullable = false)
    val name: String,

    @Column(name = "type_name", length = 50)
    val typeName: String?,

    @Column(name = "status", length = 20)
    var status: String?,

    @Column(name = "zip_code", length = 10)
    val zipCode: String?,

    @Column(name = "address", length = 300)
    val address: String?,

    @Column(name = "phone", length = 20)
    val phone: String?,

    @Column(name = "fax", length = 20)
    val fax: String?,

    @Column(name = "homepage", length = 200)
    val homepage: String?,

    @Column(name = "latitude", length = 30)
    val latitude: String?,

    @Column(name = "longitude", length = 30)
    val longitude: String?,

    @Column(name = "capacity")
    val capacity: Int?,

    @Column(name = "current_child_count")
    val currentChildCount: Int?,

    @Column(name = "nursery_room_count")
    val nurseryRoomCount: Int?,

    @Column(name = "nursery_room_size")
    val nurseryRoomSize: BigDecimal?,

    @Column(name = "playground_count")
    val playgroundCount: Int?,

    @Column(name = "cctv_count")
    val cctvCount: Int?,

    @Column(name = "childcare_staff_count")
    val childcareStaffCount: Int?,

    @Column(name = "vehicle_operation", length = 10)
    val vehicleOperation: String?,

    @Column(name = "representative_name", length = 60)
    val representativeName: String?,

    @Column(name = "certified_date", length = 10)
    val certifiedDate: String?,

    @Column(name = "pause_start_date", length = 10)
    val pauseStartDate: String?,

    @Column(name = "pause_end_date", length = 10)
    val pauseEndDate: String?,

    @Column(name = "abolished_date", length = 10)
    var abolishedDate: String?,

    @Column(name = "data_standard_date", length = 10)
    val dataStandardDate: String?,

    @Column(name = "services", length = 150)
    val services: String?,

    // 반수 (연령별)
    @Column(name = "class_count_age_0") val classCountAge0: Int?,
    @Column(name = "class_count_age_1") val classCountAge1: Int?,
    @Column(name = "class_count_age_2") val classCountAge2: Int?,
    @Column(name = "class_count_age_3") val classCountAge3: Int?,
    @Column(name = "class_count_age_4") val classCountAge4: Int?,
    @Column(name = "class_count_age_5") val classCountAge5: Int?,
    @Column(name = "class_count_infant_mixed") val classCountInfantMixed: Int?,
    @Column(name = "class_count_child_mixed") val classCountChildMixed: Int?,
    @Column(name = "class_count_special") val classCountSpecial: Int?,
    @Column(name = "class_count_total") val classCountTotal: Int?,

    // 아동수 (연령별)
    @Column(name = "child_count_age_0") val childCountAge0: Int?,
    @Column(name = "child_count_age_1") val childCountAge1: Int?,
    @Column(name = "child_count_age_2") val childCountAge2: Int?,
    @Column(name = "child_count_age_3") val childCountAge3: Int?,
    @Column(name = "child_count_age_4") val childCountAge4: Int?,
    @Column(name = "child_count_age_5") val childCountAge5: Int?,
    @Column(name = "child_count_infant_mixed") val childCountInfantMixed: Int?,
    @Column(name = "child_count_child_mixed") val childCountChildMixed: Int?,
    @Column(name = "child_count_special") val childCountSpecial: Int?,
    @Column(name = "child_count_total") val childCountTotal: Int?,

    // 교직원 근속년수
    @Column(name = "staff_tenure_under_1y") val staffTenureUnder1y: Double?,
    @Column(name = "staff_tenure_1y_to_2y") val staffTenure1yTo2y: Double?,
    @Column(name = "staff_tenure_2y_to_4y") val staffTenure2yTo4y: Double?,
    @Column(name = "staff_tenure_4y_to_6y") val staffTenure4yTo6y: Double?,
    @Column(name = "staff_tenure_over_6y") val staffTenureOver6y: Double?,

    // 교직원 직종별 현황
    @Column(name = "staff_director_count") val staffDirectorCount: Int?,
    @Column(name = "staff_teacher_count") val staffTeacherCount: Int?,
    @Column(name = "staff_special_teacher_count") val staffSpecialTeacherCount: Int?,
    @Column(name = "staff_therapist_count") val staffTherapistCount: Int?,
    @Column(name = "staff_nutritionist_count") val staffNutritionistCount: Int?,
    @Column(name = "staff_nurse_count") val staffNurseCount: Int?,
    @Column(name = "staff_nursing_assistant_count") val staffNursingAssistantCount: Int?,
    @Column(name = "staff_cook_count") val staffCookCount: Int?,
    @Column(name = "staff_office_count") val staffOfficeCount: Int?,
    @Column(name = "staff_total") val staffTotal: Int?,

    // 입소대기 아동수 (연령별)
    @Column(name = "waiting_child_age_0") val waitingChildAge0: Int?,
    @Column(name = "waiting_child_age_1") val waitingChildAge1: Int?,
    @Column(name = "waiting_child_age_2") val waitingChildAge2: Int?,
    @Column(name = "waiting_child_age_3") val waitingChildAge3: Int?,
    @Column(name = "waiting_child_age_4") val waitingChildAge4: Int?,
    @Column(name = "waiting_child_age_5") val waitingChildAge5: Int?,
    @Column(name = "waiting_child_age_over_6") val waitingChildAgeOver6: Int?,
    @Column(name = "waiting_child_total") val waitingChildTotal: Int?,

    @Column(name = "synced_at", nullable = false)
    val syncedAt: LocalDateTime = LocalDateTime.now(),
)
