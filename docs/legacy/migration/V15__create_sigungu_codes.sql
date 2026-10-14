CREATE TABLE sigungu_codes
(
    code         VARCHAR(10)  NOT NULL PRIMARY KEY,
    level        VARCHAR(10)  NOT NULL,
    sido_code    VARCHAR(2)   NOT NULL,
    sigungu_code VARCHAR(5),
    emd_code     VARCHAR(8),
    name         VARCHAR(200) NOT NULL,
    synced_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sigungu_codes_sigungu_code ON sigungu_codes (sigungu_code);
CREATE INDEX idx_sigungu_codes_emd_code ON sigungu_codes (emd_code);

COMMENT ON TABLE sigungu_codes IS '국토교통부 공식 법정동코드 참조 테이블 (odcloud.kr, 리 레벨 제외)';
COMMENT ON COLUMN sigungu_codes.code IS '법정동코드 원본 10자리 (예: 1111010100)';
COMMENT ON COLUMN sigungu_codes.level IS '코드 레벨 (SIDO / SIGUNGU / EMD)';
COMMENT ON COLUMN sigungu_codes.sido_code IS '시도코드 — code 앞 2자리 (모든 레벨)';
COMMENT ON COLUMN sigungu_codes.sigungu_code IS '시군구코드 — code 앞 5자리 (SIGUNGU/EMD 레벨만)';
COMMENT ON COLUMN sigungu_codes.emd_code IS '읍면동코드 — code 앞 8자리 (EMD 레벨만)';
COMMENT ON COLUMN sigungu_codes.name IS '법정동명 원문 (예: 서울특별시 종로구 청운동)';
COMMENT ON COLUMN sigungu_codes.synced_at IS '마지막 변경 반영 시각 (변경 없으면 갱신되지 않음)';

COMMENT ON COLUMN sync_histories.sync_type IS '동기화 유형 (FULL / DELTA / PLAYGROUND / SIGUNGU_CODE)';
