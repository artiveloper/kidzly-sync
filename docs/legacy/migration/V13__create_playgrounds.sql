CREATE TABLE playgrounds
(
    facility_id         VARCHAR(20)  NOT NULL PRIMARY KEY,
    facility_serial_no  VARCHAR(20),
    sido_code           VARCHAR(10),
    sigungu_code        VARCHAR(10),
    emd_code            VARCHAR(20),
    name                VARCHAR(200) NOT NULL,
    address             VARCHAR(500),
    coord_x             NUMERIC(15, 4),
    coord_y             NUMERIC(15, 4),
    install_date        VARCHAR(8),
    facility_code1      VARCHAR(20),
    facility_code2      VARCHAR(20),
    install_place_code  VARCHAR(10),
    ownership_code      VARCHAR(10),
    indoor_outdoor_code VARCHAR(10),
    operation_code      VARCHAR(10),
    accident_yn         VARCHAR(1),
    deleted_yn          VARCHAR(1),
    synced_at           TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_playgrounds_sigungu_code ON playgrounds (sigungu_code);

COMMENT ON TABLE playgrounds IS '어린이놀이시설정보 (safemap.go.kr IF_0007)';
COMMENT ON COLUMN playgrounds.facility_id IS '시설 일련번호 (objt_id, 소수점 제거 정규화)';
COMMENT ON COLUMN playgrounds.facility_serial_no IS '놀이시설 일련번호 (fclty_cd1)';
COMMENT ON COLUMN playgrounds.sido_code IS '시도코드 (ctprvn_cd)';
COMMENT ON COLUMN playgrounds.sigungu_code IS '시군구코드 (sgg_cd)';
COMMENT ON COLUMN playgrounds.emd_code IS '읍면동코드 (emd_cd)';
COMMENT ON COLUMN playgrounds.name IS '놀이시설명 (fclty_nm)';
COMMENT ON COLUMN playgrounds.address IS '주소 (adres)';
COMMENT ON COLUMN playgrounds.coord_x IS 'X좌표 — EPSG:3857 Web Mercator (위경도 아님)';
COMMENT ON COLUMN playgrounds.coord_y IS 'Y좌표 — EPSG:3857 Web Mercator (위경도 아님)';
COMMENT ON COLUMN playgrounds.install_date IS '설치일자 (instl_de, YYYYMMDD)';
COMMENT ON COLUMN playgrounds.facility_code1 IS '놀이시설코드1 (fclty_cd2)';
COMMENT ON COLUMN playgrounds.facility_code2 IS '놀이시설코드2 (fclty_cd3)';
COMMENT ON COLUMN playgrounds.install_place_code IS '설치장소코드 (fclty_cd4, A001~A093)';
COMMENT ON COLUMN playgrounds.ownership_code IS '민간/공공구분 (fclty_cd5, C001=민간 C002=공공)';
COMMENT ON COLUMN playgrounds.indoor_outdoor_code IS '실내외구분 (fclty_cd6, O001=실내 O002=실외)';
COMMENT ON COLUMN playgrounds.operation_code IS '운영구분 (fclty_cd7, B001=운영 B003=이용금지)';
COMMENT ON COLUMN playgrounds.accident_yn IS '사고이력정보 (ac_yn)';
COMMENT ON COLUMN playgrounds.deleted_yn IS '삭제여부 (del_yn)';
COMMENT ON COLUMN playgrounds.synced_at IS '마지막 변경 반영 시각 (변경 없으면 갱신되지 않음)';
