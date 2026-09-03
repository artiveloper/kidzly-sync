-- 작성 일시: 2026-09-03
-- 변경 내용: playgrounds에 위경도(latitude/longitude) 생성 컬럼과 지도 bbox 인덱스를 추가한다.
-- 배경: safemap.go.kr IF_0007이 주는 coord_x/coord_y는 EPSG:3857 Web Mercator라
--       네이버 지도에 그대로 못 쓰고, bbox 조회도 인덱스를 못 탄다.
-- 검증: 2026-09-03 운영 데이터 표본으로 역변환 확인.
--       (14121752.1891, 4515668.3815) → 37.547286, 126.857858 = 서울 강서구 등촌로39길 71 ✔
--       (14314079.1628, 4283972.1353) → 35.878909, 128.585561 = 대구 북구 칠성남로 50 ✔
-- 설계: 원본은 어디까지나 coord_x/coord_y다. 파생값이 원본과 어긋날 수 없도록
--       동기화 배치가 계산해 넣지 않고 GENERATED ... STORED 로 DB가 계산하게 한다.
--       (역메르카토르: lon = degrees(x / R), lat = degrees(2·atan(exp(y / R)) − π/2), R = 6378137)

ALTER TABLE playgrounds
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION
        GENERATED ALWAYS AS (
            degrees(coord_x::double precision / 6378137.0)
            ) STORED,
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION
        GENERATED ALWAYS AS (
            degrees(2 * atan(exp(coord_y::double precision / 6378137.0)) - pi() / 2)
            ) STORED;

COMMENT ON COLUMN playgrounds.longitude IS '경도(WGS84) — coord_x에서 자동 계산, 직접 입력 불가';
COMMENT ON COLUMN playgrounds.latitude IS '위도(WGS84) — coord_y에서 자동 계산, 직접 입력 불가';

-- 지도 화면의 bbox 조회용. 운영구분·실내외 같은 업무 조건은 넣지 않는다
-- (B003 이용금지가 84,251건 중 535건뿐이라 걸러내는 이득보다 쿼리 결합 비용이 크다).
CREATE INDEX IF NOT EXISTS idx_playgrounds_map_bbox
    ON playgrounds (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
