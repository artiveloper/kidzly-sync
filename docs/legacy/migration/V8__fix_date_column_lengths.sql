-- pause_start_date, pause_end_date, data_standard_date 컬럼 타입 수정
-- API에서 'YYYY-MM-DD' 형식(10자)으로 반환하므로 VARCHAR(8) → VARCHAR(10)으로 확장
ALTER TABLE daycares ALTER COLUMN pause_start_date TYPE VARCHAR(10);
ALTER TABLE daycares ALTER COLUMN pause_end_date   TYPE VARCHAR(10);
ALTER TABLE daycares ALTER COLUMN data_standard_date TYPE VARCHAR(10);
