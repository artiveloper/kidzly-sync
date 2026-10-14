-- 작성 일시: 2026-09-03
-- 변경 내용: playgrounds 위경도 생성 컬럼이 coord=0(좌표 미입력)을 위경도 0,0으로 변환하던 것을 NULL로 바꾼다.
-- 배경: V18 적용 후 운영 데이터를 보니 84,251건 중 2,467건이 coord_x=0, coord_y=0이다.
--       원본이 좌표 미입력을 0으로 채운 것인데, V18은 이를 유효한 좌표로 보고
--       위경도 (0, 0) — 기니만 앞바다 — 를 만들어냈다. bbox 인덱스에도 그대로 들어갔다.
--       0은 NULL이 아니므로 V18의 `WHERE latitude IS NOT NULL` 조건으로는 걸러지지 않는다.
-- 판단: 경도 0(그리니치)·위도 0(적도)은 한국 데이터에서 나올 수 없으므로 0을 결측 표시로 취급해도 안전하다.
-- 주의: PG17의 ALTER COLUMN ... SET EXPRESSION은 테스트 컨테이너(postgres:16)에서 못 쓴다.
--       DROP 후 재추가로 처리한다. 인덱스는 컬럼과 함께 삭제되므로 다시 만든다.

ALTER TABLE playgrounds
    DROP COLUMN IF EXISTS longitude,
    DROP COLUMN IF EXISTS latitude;

ALTER TABLE playgrounds
    ADD COLUMN longitude DOUBLE PRECISION
        GENERATED ALWAYS AS (
            degrees(NULLIF(coord_x, 0)::double precision / 6378137.0)
            ) STORED,
    ADD COLUMN latitude DOUBLE PRECISION
        GENERATED ALWAYS AS (
            degrees(2 * atan(exp(NULLIF(coord_y, 0)::double precision / 6378137.0)) - pi() / 2)
            ) STORED;

COMMENT ON COLUMN playgrounds.longitude IS '경도(WGS84) — coord_x에서 자동 계산, 직접 입력 불가. coord_x=0(좌표 미입력)이면 NULL';
COMMENT ON COLUMN playgrounds.latitude IS '위도(WGS84) — coord_y에서 자동 계산, 직접 입력 불가. coord_y=0(좌표 미입력)이면 NULL';

CREATE INDEX idx_playgrounds_map_bbox
    ON playgrounds (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
