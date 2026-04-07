-- 기존 컬럼 타입 수정 (크기 확장만 적용, 축소는 기존 데이터 호환성으로 생략)
ALTER TABLE daycares ALTER COLUMN crname TYPE VARCHAR(150);
ALTER TABLE daycares ALTER COLUMN craddr TYPE VARCHAR(300);
ALTER TABLE daycares ALTER COLUMN la TYPE VARCHAR(30);
ALTER TABLE daycares ALTER COLUMN lo TYPE VARCHAR(30);
ALTER TABLE daycares ALTER COLUMN nrtrroomsize TYPE NUMERIC(18, 2);
ALTER TABLE daycares ALTER COLUMN crrepname TYPE VARCHAR(60);

-- crstdate(cpmsapi019) → crabldt(cpmsapi030) 통합: 동일한 폐지일자 컬럼
ALTER TABLE daycares RENAME COLUMN crstdate TO crabldt;

-- 신규 컬럼 추가: 기본정보 (표준 컬럼명 적용, V7 rename 불필요)
ALTER TABLE daycares ADD COLUMN vehicle_operation     VARCHAR(10);
ALTER TABLE daycares ADD COLUMN pause_start_date      VARCHAR(8);
ALTER TABLE daycares ADD COLUMN pause_end_date        VARCHAR(8);
ALTER TABLE daycares ADD COLUMN data_standard_date    VARCHAR(8);
ALTER TABLE daycares ADD COLUMN services              VARCHAR(150);

-- 신규 컬럼 추가: 반수 (연령별)
ALTER TABLE daycares ADD COLUMN class_count_age_0      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_age_1      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_age_2      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_age_3      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_age_4      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_age_5      INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_infant_mixed INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_child_mixed  INTEGER;
ALTER TABLE daycares ADD COLUMN class_count_special     INTEGER;

-- 신규 컬럼 추가: 아동수 (연령별)
ALTER TABLE daycares ADD COLUMN child_count_age_0      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_age_1      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_age_2      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_age_3      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_age_4      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_age_5      INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_infant_mixed INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_child_mixed  INTEGER;
ALTER TABLE daycares ADD COLUMN child_count_special     INTEGER;

-- 신규 컬럼 추가: 교직원 근속년수
ALTER TABLE daycares ADD COLUMN staff_tenure_under_1y  INTEGER;
ALTER TABLE daycares ADD COLUMN staff_tenure_1y_to_2y  INTEGER;
ALTER TABLE daycares ADD COLUMN staff_tenure_2y_to_4y  INTEGER;
ALTER TABLE daycares ADD COLUMN staff_tenure_4y_to_6y  INTEGER;
ALTER TABLE daycares ADD COLUMN staff_tenure_over_6y   INTEGER;

-- 신규 컬럼 추가: 교직원 직종별 현황
ALTER TABLE daycares ADD COLUMN staff_director_count          INTEGER;
ALTER TABLE daycares ADD COLUMN staff_teacher_count           INTEGER;
ALTER TABLE daycares ADD COLUMN staff_special_teacher_count   INTEGER;
ALTER TABLE daycares ADD COLUMN staff_therapist_count         INTEGER;
ALTER TABLE daycares ADD COLUMN staff_nutritionist_count      INTEGER;
ALTER TABLE daycares ADD COLUMN staff_nurse_count             INTEGER;
ALTER TABLE daycares ADD COLUMN staff_nursing_assistant_count INTEGER;
ALTER TABLE daycares ADD COLUMN staff_cook_count              INTEGER;
ALTER TABLE daycares ADD COLUMN staff_office_count            INTEGER;

-- 신규 컬럼 추가: 입소대기 아동수 (연령별)
ALTER TABLE daycares ADD COLUMN waiting_child_age_0      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_1      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_2      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_3      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_4      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_5      INTEGER;
ALTER TABLE daycares ADD COLUMN waiting_child_age_over_6 INTEGER;
