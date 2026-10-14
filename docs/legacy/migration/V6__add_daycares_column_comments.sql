-- V5에서 추가된 컬럼 코멘트 (기존 컬럼 코멘트는 V4, V7 rename 후 자동 이전됨)

-- 기본정보 신규 컬럼
COMMENT ON COLUMN daycares.vehicle_operation IS '통학차량운영여부 (운영, 미운영, NULL)';
COMMENT ON COLUMN daycares.pause_start_date IS '휴지시작일자 (YYYYMMDD)';
COMMENT ON COLUMN daycares.pause_end_date IS '휴지종료일자 (YYYYMMDD)';
COMMENT ON COLUMN daycares.data_standard_date IS '데이터기준일자 (YYYYMMDD, 실시간 현재시간)';
COMMENT ON COLUMN daycares.services IS '제공서비스 (예: 일반, 일시보육)';

-- 반수 (연령별)
COMMENT ON COLUMN daycares.class_count_age_0 IS '반수-만0세';
COMMENT ON COLUMN daycares.class_count_age_1 IS '반수-만1세';
COMMENT ON COLUMN daycares.class_count_age_2 IS '반수-만2세';
COMMENT ON COLUMN daycares.class_count_age_3 IS '반수-만3세';
COMMENT ON COLUMN daycares.class_count_age_4 IS '반수-만4세';
COMMENT ON COLUMN daycares.class_count_age_5 IS '반수-만5세';
COMMENT ON COLUMN daycares.class_count_infant_mixed IS '반수-영아혼합(만0~2세)';
COMMENT ON COLUMN daycares.class_count_child_mixed IS '반수-유아혼합(만3~5세)';
COMMENT ON COLUMN daycares.class_count_special IS '반수-특수장애';

-- 아동수 (연령별)
COMMENT ON COLUMN daycares.child_count_age_0 IS '아동수-만0세';
COMMENT ON COLUMN daycares.child_count_age_1 IS '아동수-만1세';
COMMENT ON COLUMN daycares.child_count_age_2 IS '아동수-만2세';
COMMENT ON COLUMN daycares.child_count_age_3 IS '아동수-만3세';
COMMENT ON COLUMN daycares.child_count_age_4 IS '아동수-만4세';
COMMENT ON COLUMN daycares.child_count_age_5 IS '아동수-만5세';
COMMENT ON COLUMN daycares.child_count_infant_mixed IS '아동수-영아혼합(만0~2세)';
COMMENT ON COLUMN daycares.child_count_child_mixed IS '아동수-유아혼합(만3~5세)';
COMMENT ON COLUMN daycares.child_count_special IS '아동수-특수장애';

-- 교직원 근속년수
COMMENT ON COLUMN daycares.staff_tenure_under_1y IS '근속년수-1년미만';
COMMENT ON COLUMN daycares.staff_tenure_1y_to_2y IS '근속년수-1년이상~2년미만';
COMMENT ON COLUMN daycares.staff_tenure_2y_to_4y IS '근속년수-2년이상~4년미만';
COMMENT ON COLUMN daycares.staff_tenure_4y_to_6y IS '근속년수-4년이상~6년미만';
COMMENT ON COLUMN daycares.staff_tenure_over_6y IS '근속년수-6년이상';

-- 교직원 직종별 현황
COMMENT ON COLUMN daycares.staff_director_count IS '교직원현황-원장';
COMMENT ON COLUMN daycares.staff_teacher_count IS '교직원현황-보육교사';
COMMENT ON COLUMN daycares.staff_special_teacher_count IS '교직원현황-특수교사';
COMMENT ON COLUMN daycares.staff_therapist_count IS '교직원현황-치료교사';
COMMENT ON COLUMN daycares.staff_nutritionist_count IS '교직원현황-영양사';
COMMENT ON COLUMN daycares.staff_nurse_count IS '교직원현황-간호사';
COMMENT ON COLUMN daycares.staff_nursing_assistant_count IS '교직원현황-간호조무사';
COMMENT ON COLUMN daycares.staff_cook_count IS '교직원현황-조리원';
COMMENT ON COLUMN daycares.staff_office_count IS '교직원현황-사무직원';

-- 입소대기 아동수 (연령별)
COMMENT ON COLUMN daycares.waiting_child_age_0 IS '입소대기아동수-0세';
COMMENT ON COLUMN daycares.waiting_child_age_1 IS '입소대기아동수-1세';
COMMENT ON COLUMN daycares.waiting_child_age_2 IS '입소대기아동수-2세';
COMMENT ON COLUMN daycares.waiting_child_age_3 IS '입소대기아동수-3세';
COMMENT ON COLUMN daycares.waiting_child_age_4 IS '입소대기아동수-4세';
COMMENT ON COLUMN daycares.waiting_child_age_5 IS '입소대기아동수-5세';
COMMENT ON COLUMN daycares.waiting_child_age_over_6 IS '입소대기아동수-6세이상';
