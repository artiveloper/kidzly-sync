package kr.kidzly.sync.infrastructure.persistence

import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.domain.repository.DaycareRepository
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDateTime

@Repository
class DaycareRepositoryImpl(
    private val jdbcTemplate: NamedParameterJdbcTemplate,
    private val jpaDaycareRepository: JpaDaycareRepository,
) : DaycareRepository {

    @Transactional
    override fun upsertAll(daycares: List<DaycareData>): Int {
        if (daycares.isEmpty()) return 0
        val batchParams = daycares.map { it.toSqlParams() }.toTypedArray()
        return jdbcTemplate.batchUpdate(UPSERT_SQL, batchParams).sum()
    }

    @Transactional
    override fun markAsClosed(daycareCode: String, abolishedDate: String?): Int =
        jpaDaycareRepository.markAsClosed(daycareCode, abolishedDate)

    private fun DaycareData.toSqlParams() =
        MapSqlParameterSource()
            .addValue("daycareCode", daycareCode)
            .addValue("sigunguCode", sigunguCode)
            .addValue("sidoName", sidoName)
            .addValue("sigunguName", sigunguName)
            .addValue("name", name)
            .addValue("typeName", typeName)
            .addValue("status", status)
            .addValue("zipCode", zipCode)
            .addValue("address", address)
            .addValue("phone", phone)
            .addValue("fax", fax)
            .addValue("homepage", homepage)
            .addValue("latitude", latitude)
            .addValue("longitude", longitude)
            .addValue("capacity", capacity)
            .addValue("currentChildCount", currentChildCount)
            .addValue("nurseryRoomCount", nurseryRoomCount)
            .addValue("nurseryRoomSize", nurseryRoomSize)
            .addValue("playgroundCount", playgroundCount)
            .addValue("cctvCount", cctvCount)
            .addValue("childcareStaffCount", childcareStaffCount)
            .addValue("vehicleOperation", vehicleOperation)
            .addValue("representativeName", representativeName)
            .addValue("certifiedDate", certifiedDate)
            .addValue("pauseStartDate", pauseStartDate)
            .addValue("pauseEndDate", pauseEndDate)
            .addValue("abolishedDate", abolishedDate)
            .addValue("dataStandardDate", dataStandardDate)
            .addValue("services", services)
            .addValue("classCountAge0", classCountAge0)
            .addValue("classCountAge1", classCountAge1)
            .addValue("classCountAge2", classCountAge2)
            .addValue("classCountAge3", classCountAge3)
            .addValue("classCountAge4", classCountAge4)
            .addValue("classCountAge5", classCountAge5)
            .addValue("classCountInfantMixed", classCountInfantMixed)
            .addValue("classCountChildMixed", classCountChildMixed)
            .addValue("classCountSpecial", classCountSpecial)
            .addValue("classCountTotal", classCountTotal)
            .addValue("childCountAge0", childCountAge0)
            .addValue("childCountAge1", childCountAge1)
            .addValue("childCountAge2", childCountAge2)
            .addValue("childCountAge3", childCountAge3)
            .addValue("childCountAge4", childCountAge4)
            .addValue("childCountAge5", childCountAge5)
            .addValue("childCountInfantMixed", childCountInfantMixed)
            .addValue("childCountChildMixed", childCountChildMixed)
            .addValue("childCountSpecial", childCountSpecial)
            .addValue("childCountTotal", childCountTotal)
            .addValue("staffTenureUnder1y", staffTenureUnder1y)
            .addValue("staffTenure1yTo2y", staffTenure1yTo2y)
            .addValue("staffTenure2yTo4y", staffTenure2yTo4y)
            .addValue("staffTenure4yTo6y", staffTenure4yTo6y)
            .addValue("staffTenureOver6y", staffTenureOver6y)
            .addValue("staffDirectorCount", staffDirectorCount)
            .addValue("staffTeacherCount", staffTeacherCount)
            .addValue("staffSpecialTeacherCount", staffSpecialTeacherCount)
            .addValue("staffTherapistCount", staffTherapistCount)
            .addValue("staffNutritionistCount", staffNutritionistCount)
            .addValue("staffNurseCount", staffNurseCount)
            .addValue("staffNursingAssistantCount", staffNursingAssistantCount)
            .addValue("staffCookCount", staffCookCount)
            .addValue("staffOfficeCount", staffOfficeCount)
            .addValue("staffTotal", staffTotal)
            .addValue("waitingChildAge0", waitingChildAge0)
            .addValue("waitingChildAge1", waitingChildAge1)
            .addValue("waitingChildAge2", waitingChildAge2)
            .addValue("waitingChildAge3", waitingChildAge3)
            .addValue("waitingChildAge4", waitingChildAge4)
            .addValue("waitingChildAge5", waitingChildAge5)
            .addValue("waitingChildAgeOver6", waitingChildAgeOver6)
            .addValue("waitingChildTotal", waitingChildTotal)
            .addValue("syncedAt", LocalDateTime.now())

    companion object {
        private val UPSERT_SQL = """
            INSERT INTO daycares (
                daycare_code, sigungu_code, sido_name, sigungu_name, name, type_name, status,
                zip_code, address, phone, fax, homepage, latitude, longitude,
                capacity, current_child_count, nursery_room_count, nursery_room_size,
                playground_count, cctv_count, childcare_staff_count,
                vehicle_operation, representative_name, certified_date,
                pause_start_date, pause_end_date, abolished_date, data_standard_date, services,
                class_count_age_0, class_count_age_1, class_count_age_2, class_count_age_3,
                class_count_age_4, class_count_age_5, class_count_infant_mixed,
                class_count_child_mixed, class_count_special, class_count_total,
                child_count_age_0, child_count_age_1, child_count_age_2, child_count_age_3,
                child_count_age_4, child_count_age_5, child_count_infant_mixed,
                child_count_child_mixed, child_count_special, child_count_total,
                staff_tenure_under_1y, staff_tenure_1y_to_2y, staff_tenure_2y_to_4y,
                staff_tenure_4y_to_6y, staff_tenure_over_6y,
                staff_director_count, staff_teacher_count, staff_special_teacher_count,
                staff_therapist_count, staff_nutritionist_count, staff_nurse_count,
                staff_nursing_assistant_count, staff_cook_count, staff_office_count, staff_total,
                waiting_child_age_0, waiting_child_age_1, waiting_child_age_2, waiting_child_age_3,
                waiting_child_age_4, waiting_child_age_5, waiting_child_age_over_6, waiting_child_total,
                synced_at
            ) VALUES (
                :daycareCode, :sigunguCode, :sidoName, :sigunguName, :name, :typeName, :status,
                :zipCode, :address, :phone, :fax, :homepage, :latitude, :longitude,
                :capacity, :currentChildCount, :nurseryRoomCount, :nurseryRoomSize,
                :playgroundCount, :cctvCount, :childcareStaffCount,
                :vehicleOperation, :representativeName, :certifiedDate,
                :pauseStartDate, :pauseEndDate, :abolishedDate, :dataStandardDate, :services,
                :classCountAge0, :classCountAge1, :classCountAge2, :classCountAge3,
                :classCountAge4, :classCountAge5, :classCountInfantMixed,
                :classCountChildMixed, :classCountSpecial, :classCountTotal,
                :childCountAge0, :childCountAge1, :childCountAge2, :childCountAge3,
                :childCountAge4, :childCountAge5, :childCountInfantMixed,
                :childCountChildMixed, :childCountSpecial, :childCountTotal,
                :staffTenureUnder1y, :staffTenure1yTo2y, :staffTenure2yTo4y,
                :staffTenure4yTo6y, :staffTenureOver6y,
                :staffDirectorCount, :staffTeacherCount, :staffSpecialTeacherCount,
                :staffTherapistCount, :staffNutritionistCount, :staffNurseCount,
                :staffNursingAssistantCount, :staffCookCount, :staffOfficeCount, :staffTotal,
                :waitingChildAge0, :waitingChildAge1, :waitingChildAge2, :waitingChildAge3,
                :waitingChildAge4, :waitingChildAge5, :waitingChildAgeOver6, :waitingChildTotal,
                :syncedAt
            )
            ON CONFLICT (daycare_code) DO UPDATE SET
                sigungu_code = EXCLUDED.sigungu_code,
                sido_name = EXCLUDED.sido_name,
                sigungu_name = EXCLUDED.sigungu_name,
                name = EXCLUDED.name,
                type_name = EXCLUDED.type_name,
                status = EXCLUDED.status,
                zip_code = EXCLUDED.zip_code,
                address = EXCLUDED.address,
                phone = EXCLUDED.phone,
                fax = EXCLUDED.fax,
                homepage = EXCLUDED.homepage,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                capacity = EXCLUDED.capacity,
                current_child_count = EXCLUDED.current_child_count,
                nursery_room_count = EXCLUDED.nursery_room_count,
                nursery_room_size = EXCLUDED.nursery_room_size,
                playground_count = EXCLUDED.playground_count,
                cctv_count = EXCLUDED.cctv_count,
                childcare_staff_count = EXCLUDED.childcare_staff_count,
                vehicle_operation = EXCLUDED.vehicle_operation,
                representative_name = EXCLUDED.representative_name,
                certified_date = EXCLUDED.certified_date,
                pause_start_date = EXCLUDED.pause_start_date,
                pause_end_date = EXCLUDED.pause_end_date,
                abolished_date = EXCLUDED.abolished_date,
                data_standard_date = EXCLUDED.data_standard_date,
                services = EXCLUDED.services,
                class_count_age_0 = EXCLUDED.class_count_age_0,
                class_count_age_1 = EXCLUDED.class_count_age_1,
                class_count_age_2 = EXCLUDED.class_count_age_2,
                class_count_age_3 = EXCLUDED.class_count_age_3,
                class_count_age_4 = EXCLUDED.class_count_age_4,
                class_count_age_5 = EXCLUDED.class_count_age_5,
                class_count_infant_mixed = EXCLUDED.class_count_infant_mixed,
                class_count_child_mixed = EXCLUDED.class_count_child_mixed,
                class_count_special = EXCLUDED.class_count_special,
                class_count_total = EXCLUDED.class_count_total,
                child_count_age_0 = EXCLUDED.child_count_age_0,
                child_count_age_1 = EXCLUDED.child_count_age_1,
                child_count_age_2 = EXCLUDED.child_count_age_2,
                child_count_age_3 = EXCLUDED.child_count_age_3,
                child_count_age_4 = EXCLUDED.child_count_age_4,
                child_count_age_5 = EXCLUDED.child_count_age_5,
                child_count_infant_mixed = EXCLUDED.child_count_infant_mixed,
                child_count_child_mixed = EXCLUDED.child_count_child_mixed,
                child_count_special = EXCLUDED.child_count_special,
                child_count_total = EXCLUDED.child_count_total,
                staff_tenure_under_1y = EXCLUDED.staff_tenure_under_1y,
                staff_tenure_1y_to_2y = EXCLUDED.staff_tenure_1y_to_2y,
                staff_tenure_2y_to_4y = EXCLUDED.staff_tenure_2y_to_4y,
                staff_tenure_4y_to_6y = EXCLUDED.staff_tenure_4y_to_6y,
                staff_tenure_over_6y = EXCLUDED.staff_tenure_over_6y,
                staff_director_count = EXCLUDED.staff_director_count,
                staff_teacher_count = EXCLUDED.staff_teacher_count,
                staff_special_teacher_count = EXCLUDED.staff_special_teacher_count,
                staff_therapist_count = EXCLUDED.staff_therapist_count,
                staff_nutritionist_count = EXCLUDED.staff_nutritionist_count,
                staff_nurse_count = EXCLUDED.staff_nurse_count,
                staff_nursing_assistant_count = EXCLUDED.staff_nursing_assistant_count,
                staff_cook_count = EXCLUDED.staff_cook_count,
                staff_office_count = EXCLUDED.staff_office_count,
                staff_total = EXCLUDED.staff_total,
                waiting_child_age_0 = EXCLUDED.waiting_child_age_0,
                waiting_child_age_1 = EXCLUDED.waiting_child_age_1,
                waiting_child_age_2 = EXCLUDED.waiting_child_age_2,
                waiting_child_age_3 = EXCLUDED.waiting_child_age_3,
                waiting_child_age_4 = EXCLUDED.waiting_child_age_4,
                waiting_child_age_5 = EXCLUDED.waiting_child_age_5,
                waiting_child_age_over_6 = EXCLUDED.waiting_child_age_over_6,
                waiting_child_total = EXCLUDED.waiting_child_total,
                synced_at = EXCLUDED.synced_at
        """.trimIndent()
    }
}
