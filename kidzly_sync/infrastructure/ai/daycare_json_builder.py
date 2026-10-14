"""어린이집 운영 데이터 → AI 프롬프트용 JSON.

Kotlin ``DaycareJsonBuilder`` 와 동일한 9개 섹션·한글 키를 그대로 옮긴다.
"""

from __future__ import annotations

import json
from datetime import date

from kidzly_sync.application.model import DaycareData


def build(daycare: DaycareData) -> str:
    capacity = daycare.capacity or 0
    occupancy_rate = (
        int((daycare.current_child_count or 0) * 100.0 / capacity) if capacity > 0 else None
    )

    data = {
        "기본정보": {
            "이름": daycare.name,
            "유형": daycare.type_name,
            "인가일": daycare.certified_date,
            "운영연수": _calculate_operation_years(daycare.certified_date),
            "상태": daycare.status,
        },
        "규모": {
            "정원": daycare.capacity,
            "현원": daycare.current_child_count,
            "충원율_퍼센트": occupancy_rate,
            "보육실수": daycare.nursery_room_count,
            "보육실면적_제곱미터": float(daycare.nursery_room_size)
            if daycare.nursery_room_size is not None
            else None,
        },
        "시설": {
            "놀이터수": daycare.playground_count,
            "CCTV수": daycare.cctv_count,
            "차량운영": daycare.vehicle_operation,
        },
        "대기아동": {
            "총대기수": daycare.waiting_child_total,
            "0세": daycare.waiting_child_age_0,
            "1세": daycare.waiting_child_age_1,
            "2세": daycare.waiting_child_age_2,
            "3세": daycare.waiting_child_age_3,
            "4세": daycare.waiting_child_age_4,
            "5세": daycare.waiting_child_age_5,
            "6세이상": daycare.waiting_child_age_over_6,
        },
        "연령별반수": {
            "0세반": daycare.class_count_age_0,
            "1세반": daycare.class_count_age_1,
            "2세반": daycare.class_count_age_2,
            "3세반": daycare.class_count_age_3,
            "4세반": daycare.class_count_age_4,
            "5세반": daycare.class_count_age_5,
            "영아혼합반": daycare.class_count_infant_mixed,
            "유아혼합반": daycare.class_count_child_mixed,
            "장애아전문반": daycare.class_count_special,
            "총반수": daycare.class_count_total,
        },
        "연령별아동수": {
            "0세": daycare.child_count_age_0,
            "1세": daycare.child_count_age_1,
            "2세": daycare.child_count_age_2,
            "3세": daycare.child_count_age_3,
            "4세": daycare.child_count_age_4,
            "5세": daycare.child_count_age_5,
            "영아혼합": daycare.child_count_infant_mixed,
            "유아혼합": daycare.child_count_child_mixed,
            "장애아": daycare.child_count_special,
            "합계": daycare.child_count_total,
        },
        "교직원근속분포": {
            "1년미만": daycare.staff_tenure_under_1y,
            "1~2년": daycare.staff_tenure_1y_to_2y,
            "2~4년": daycare.staff_tenure_2y_to_4y,
            "4~6년": daycare.staff_tenure_4y_to_6y,
            "6년이상": daycare.staff_tenure_over_6y,
        },
        "교직원직종현황": {
            "원장": daycare.staff_director_count,
            "보육교사": daycare.staff_teacher_count,
            "특수교사": daycare.staff_special_teacher_count,
            "치료사": daycare.staff_therapist_count,
            "영양사": daycare.staff_nutritionist_count,
            "간호사": daycare.staff_nurse_count,
            "간호조무사": daycare.staff_nursing_assistant_count,
            "조리원": daycare.staff_cook_count,
            "사무원": daycare.staff_office_count,
            "합계": daycare.staff_total,
        },
    }

    return json.dumps(data, ensure_ascii=False)


def _calculate_operation_years(certified_date: str | None) -> int | None:
    if certified_date is None:
        return None
    cleaned = certified_date.replace("-", "")
    if len(cleaned) < 4:
        return None
    try:
        year = int(cleaned[:4])
    except ValueError:
        return None
    return date.today().year - year
