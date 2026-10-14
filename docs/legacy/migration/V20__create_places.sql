-- 작성 일시: 2026-09-16
-- 변경 내용: 아이 놀거리 지도용 큐레이션 테이블 places 를 신설한다. 어드민이 CRUD 하고 웹은 읽는다.
-- 배경: 지금까지 이 DB의 모든 테이블은 정부 API 동기화 결과였다. places 는 처음으로
--       사람이 직접 입력·검증하는 테이블이다. 필드는 '키즐리_놀거리지도_필드정의' 정의서를 따른다.
-- 판단: 기존 playgrounds(어린이놀이시설 안전관리시스템, 84,251건)와 합치지 않고 분리한다.
--       ①playgrounds 는 동기화 배치가 쓰기를 소유해 사람이 고친 값이 다음 upsert 에 덮인다.
--       ②playgrounds 는 설치장소 대부분이 주택단지 놀이터라 '주말에 갈 곳'이라는 모수와 다르다.
--       ③신선도 지표가 다르다 — playgrounds 는 synced_at(기계), places 는 last_verified_at(사람).
--       불리언 3종은 정의서 지시대로 nullable 이다. NULL(아직 확인 안 됨)과 FALSE(없음)를 구분한다.
--       이 DB 최초로 RLS 를 켠다. places 는 공개 anon 키로 읽히는데 쓰기가 가능한 테이블이라,
--       정책 없이 두면 누구나 PostgREST 로 놀거리 데이터를 고칠 수 있다.
CREATE TABLE places
(
    id               BIGSERIAL PRIMARY KEY,

    -- 핀 요약
    name             VARCHAR(100)     NOT NULL,
    summary          VARCHAR(40)      NOT NULL,
    rating           NUMERIC(2, 1),

    -- 필터 축 (정의서 상한 5개)
    place_type       VARCHAR(20)      NOT NULL,
    age_groups       TEXT[]           NOT NULL DEFAULT '{}',
    indoor_outdoor   VARCHAR(10)      NOT NULL,
    is_free          BOOLEAN          NOT NULL,
    has_parking      BOOLEAN,

    -- 상세
    opening_hours    VARCHAR(200)     NOT NULL,
    closed_days      VARCHAR(200)     NOT NULL,
    price_detail     VARCHAR(300),
    parking_detail   VARCHAR(300),
    has_nursing_room BOOLEAN,
    has_diaper_table BOOLEAN,
    address          VARCHAR(300)     NOT NULL,
    latitude         DOUBLE PRECISION NOT NULL,
    longitude        DOUBLE PRECISION NOT NULL,
    thumbnail_url    VARCHAR(500),
    last_verified_at DATE             NOT NULL,

    -- 운영
    is_published     BOOLEAN          NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    CONSTRAINT places_place_type_check CHECK (place_type IN
                                              ('kids_cafe', 'park', 'indoor_playground', 'museum',
                                               'zoo', 'library', 'cafe')),
    CONSTRAINT places_indoor_outdoor_check CHECK (indoor_outdoor IN ('indoor', 'outdoor', 'mixed')),
    CONSTRAINT places_age_groups_check CHECK (age_groups <@
                                              ARRAY ['infant', 'toddler', 'preschool', 'elementary']),
    CONSTRAINT places_rating_check CHECK (rating IS NULL OR rating BETWEEN 0 AND 5),
    -- 한국 영역 밖 좌표는 입력 실수다. playgrounds 가 겪은 (0,0) 유입을 애초에 막는다.
    CONSTRAINT places_latitude_check CHECK (latitude BETWEEN 33 AND 39),
    CONSTRAINT places_longitude_check CHECK (longitude BETWEEN 124 AND 132)
);

-- 지도 bbox 조회가 주 경로다. 발행된 행만 읽으므로 is_published 를 선두에 둔다.
CREATE INDEX idx_places_bounds ON places (is_published, latitude, longitude);
CREATE INDEX idx_places_place_type ON places (place_type);
-- 어드민 목록 기본 정렬
CREATE INDEX idx_places_updated_at ON places (updated_at DESC);

COMMENT ON TABLE places IS '아이 놀거리 지도 — 운영자 큐레이션 장소. 정부 데이터인 playgrounds 와 별개다';
COMMENT ON COLUMN places.summary IS '핀을 누를지 결정하는 한 줄 소개. 시설 나열이 아니라 장소의 성격을 쓴다';
COMMENT ON COLUMN places.rating IS '리뷰 평균 0.0~5.0. 확보 전까지 NULL';
COMMENT ON COLUMN places.place_type IS 'kids_cafe=키즈카페 park=공원 indoor_playground=실내놀이터 museum=체험관·박물관 zoo=동물원·수목원 library=도서관 cafe=카페';
COMMENT ON COLUMN places.age_groups IS 'infant=영아 toddler=걸음마 preschool=유아 elementary=초등';
COMMENT ON COLUMN places.indoor_outdoor IS 'indoor=실내 outdoor=실외 mixed=혼합';
COMMENT ON COLUMN places.has_parking IS 'NULL 은 아직 확인 안 됨. FALSE(불가)와 구분한다';
COMMENT ON COLUMN places.has_nursing_room IS 'NULL 은 아직 확인 안 됨. FALSE(없음)와 구분한다';
COMMENT ON COLUMN places.has_diaper_table IS 'NULL 은 아직 확인 안 됨. FALSE(없음)와 구분한다';
COMMENT ON COLUMN places.opening_hours IS '요일별로 다르면 한 문자열에 함께 적는다. 요일별 구조화는 추후 과제';
COMMENT ON COLUMN places.last_verified_at IS '운영자가 마지막으로 정보를 확인한 날. "N개월 전 확인" 배지의 근거';
COMMENT ON COLUMN places.is_published IS 'FALSE 면 작성 중인 초안이라 공개 지도에 노출하지 않는다';

-- 공개 웹은 anon 키로 읽는다. 발행된 행만 읽히고, 쓰기는 RLS 를 우회하는 service role(어드민 API)만 가능하다.
-- TO 절을 두지 않아 anon·authenticated 역할이 없는 로컬 검증 DB 에서도 그대로 적용된다.
ALTER TABLE places ENABLE ROW LEVEL SECURITY;

CREATE POLICY places_public_read ON places
    FOR SELECT
    USING (is_published);
