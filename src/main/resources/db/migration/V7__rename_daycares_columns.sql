-- V1 기존 컬럼명 → 표준 컬럼명 (약어 제거)
-- PostgreSQL은 RENAME COLUMN 시 코멘트(V4)를 자동 이전함
ALTER TABLE daycares RENAME COLUMN stcode TO daycare_code;
ALTER TABLE daycares RENAME COLUMN arcode TO sigungu_code;
ALTER TABLE daycares RENAME COLUMN sidoname TO sido_name;
ALTER TABLE daycares RENAME COLUMN sigunguname TO sigungu_name;
ALTER TABLE daycares RENAME COLUMN crname TO name;
ALTER TABLE daycares RENAME COLUMN crtypename TO type_name;
ALTER TABLE daycares RENAME COLUMN crstatusname TO status;
ALTER TABLE daycares RENAME COLUMN zipcode TO zip_code;
ALTER TABLE daycares RENAME COLUMN craddr TO address;
ALTER TABLE daycares RENAME COLUMN crtelno TO phone;
ALTER TABLE daycares RENAME COLUMN crfaxno TO fax;
ALTER TABLE daycares RENAME COLUMN crhome TO homepage;
ALTER TABLE daycares RENAME COLUMN la TO latitude;
ALTER TABLE daycares RENAME COLUMN lo TO longitude;
ALTER TABLE daycares RENAME COLUMN crcapat TO capacity;
ALTER TABLE daycares RENAME COLUMN crchcnt TO current_child_count;
ALTER TABLE daycares RENAME COLUMN nrtrroomcnt TO nursery_room_count;
ALTER TABLE daycares RENAME COLUMN nrtrroomsize TO nursery_room_size;
ALTER TABLE daycares RENAME COLUMN plgrdco TO playground_count;
ALTER TABLE daycares RENAME COLUMN cctvinstlcnt TO cctv_count;
ALTER TABLE daycares RENAME COLUMN chcrtescnt TO childcare_staff_count;
ALTER TABLE daycares RENAME COLUMN class_cnt_tot TO class_count_total;
ALTER TABLE daycares RENAME COLUMN child_cnt_tot TO child_count_total;
ALTER TABLE daycares RENAME COLUMN em_cnt_tot TO staff_total;
ALTER TABLE daycares RENAME COLUMN ew_cnt_tot TO waiting_child_total;
ALTER TABLE daycares RENAME COLUMN crrepname TO representative_name;
ALTER TABLE daycares RENAME COLUMN crcnfmdt TO certified_date;
ALTER TABLE daycares RENAME COLUMN crabldt TO abolished_date;

-- 인덱스명 갱신
ALTER INDEX idx_daycares_arcode RENAME TO idx_daycares_sigungu_code;
ALTER INDEX idx_daycares_crstatusname RENAME TO idx_daycares_status;
