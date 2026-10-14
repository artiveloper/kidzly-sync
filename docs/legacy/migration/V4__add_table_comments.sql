-- daycares 테이블 및 컬럼 코멘트
COMMENT ON TABLE daycares IS '어린이집 기본정보 (cpmsapi030)';

COMMENT ON COLUMN daycares.stcode IS '어린이집코드';
COMMENT ON COLUMN daycares.arcode IS '시군구코드';
COMMENT ON COLUMN daycares.sidoname IS '시도명';
COMMENT ON COLUMN daycares.sigunguname IS '시군구명';
COMMENT ON COLUMN daycares.crname IS '어린이집명';
COMMENT ON COLUMN daycares.crtypename IS '어린이집 유형명';
COMMENT ON COLUMN daycares.crstatusname IS '운영상태명';
COMMENT ON COLUMN daycares.zipcode IS '우편번호';
COMMENT ON COLUMN daycares.craddr IS '주소';
COMMENT ON COLUMN daycares.crtelno IS '전화번호';
COMMENT ON COLUMN daycares.crfaxno IS '팩스번호';
COMMENT ON COLUMN daycares.crhome IS '홈페이지';
COMMENT ON COLUMN daycares.la IS '위도';
COMMENT ON COLUMN daycares.lo IS '경도';
COMMENT ON COLUMN daycares.crcapat IS '정원';
COMMENT ON COLUMN daycares.crchcnt IS '현원';
COMMENT ON COLUMN daycares.nrtrroomcnt IS '보육실 수';
COMMENT ON COLUMN daycares.nrtrroomsize IS '보육실 면적(㎡)';
COMMENT ON COLUMN daycares.plgrdco IS '놀이터 수';
COMMENT ON COLUMN daycares.cctvinstlcnt IS 'CCTV 설치 수';
COMMENT ON COLUMN daycares.chcrtescnt IS '차량 수';
COMMENT ON COLUMN daycares.class_cnt_tot IS '반 수 합계';
COMMENT ON COLUMN daycares.child_cnt_tot IS '아동 수 합계';
COMMENT ON COLUMN daycares.em_cnt_tot IS '교직원 수 합계';
COMMENT ON COLUMN daycares.ew_cnt_tot IS '여성 교직원 수 합계';
COMMENT ON COLUMN daycares.crrepname IS '대표자명';
COMMENT ON COLUMN daycares.crcnfmdt IS '인가일자 (YYYYMMDD)';
COMMENT ON COLUMN daycares.crstdate IS '폐지일자 (YYYYMMDD)';
COMMENT ON COLUMN daycares.synced_at IS '동기화 시각';

-- sigungus 테이블 및 컬럼 코멘트
COMMENT ON TABLE sigungus IS '시군구 정보 (cpmsapi020)';

COMMENT ON COLUMN sigungus.arcode IS '시군구코드';
COMMENT ON COLUMN sigungus.sidoname IS '시도명';
COMMENT ON COLUMN sigungus.sigunname IS '시군구명';
COMMENT ON COLUMN sigungus.synced_at IS '동기화 시각';

-- sync_histories 테이블 및 컬럼 코멘트
COMMENT ON TABLE sync_histories IS '동기화 실행 이력';

COMMENT ON COLUMN sync_histories.id IS '식별자';
COMMENT ON COLUMN sync_histories.sync_type IS '동기화 유형 (FULL / MONTHLY)';
COMMENT ON COLUMN sync_histories.target_year_month IS '대상 연월 (YYYY-MM, MONTHLY 동기화 시 사용)';
COMMENT ON COLUMN sync_histories.status IS '상태 (RUNNING / SUCCESS / FAILED)';
COMMENT ON COLUMN sync_histories.total_count IS '전체 처리 건수';
COMMENT ON COLUMN sync_histories.upsert_count IS '추가/수정 건수';
COMMENT ON COLUMN sync_histories.closed_count IS '폐지 처리 건수';
COMMENT ON COLUMN sync_histories.error_message IS '오류 메시지';
COMMENT ON COLUMN sync_histories.started_at IS '동기화 시작 시각';
COMMENT ON COLUMN sync_histories.finished_at IS '동기화 완료 시각';
