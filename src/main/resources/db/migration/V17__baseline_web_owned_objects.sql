-- 작성 일시: 2026-09-03
-- 변경 내용: kidzly.kr(웹)이 Supabase SQL 에디터에서 직접 만들어 쓰던 객체를 Flyway 이력으로 편입한다.
--            대상 = content_stats 테이블, daycares 조회 인덱스 13개, 조회용 뷰 2개.
-- 배경: 이 객체들은 실제 DB에는 있으나 어떤 마이그레이션에도 없어 재현이 불가능했다.
--       이제부터 이 DB의 스키마 소유자는 Flyway 하나다.
-- 주의: 운영 DB에는 이미 존재하므로 IF NOT EXISTS / OR REPLACE 로 멱등하게 작성한다.
--       신규 DB(테스트컨테이너 포함)에서는 실제로 생성된다.

-- ── 확장 ─────────────────────────────────────────────
-- 어린이집명·주소 부분 일치 검색(ILIKE '%...%')이 인덱스를 타게 한다.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ── 아티클 조회수·좋아요 집계 (웹 전용, 동기화 배치가 건드리지 않는다) ──
CREATE TABLE IF NOT EXISTS content_stats
(
    uuid       TEXT    NOT NULL PRIMARY KEY,
    view_count INTEGER NOT NULL DEFAULT 0,
    like_count INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE content_stats IS '블로그 아티클 조회수·좋아요 집계 (kidzly.kr 소유, 동기화 대상 아님)';
COMMENT ON COLUMN content_stats.uuid IS '아티클 식별자 (MDX frontmatter의 uuid)';
COMMENT ON COLUMN content_stats.view_count IS '누적 조회수';
COMMENT ON COLUMN content_stats.like_count IS '누적 좋아요 수';

-- ── 검색 인덱스 ───────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_daycares_name_trgm
    ON daycares USING gin (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_daycares_address_trgm
    ON daycares USING gin (address gin_trgm_ops);

-- ── 지도 bbox 조회 인덱스 ─────────────────────────────
-- latitude/longitude가 varchar라 float8 캐스팅 표현식 인덱스가 따로 필요하다.
CREATE INDEX IF NOT EXISTS idx_daycares_map_bbox
    ON daycares (status, latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_daycares_status_latlng_float
    ON daycares (status, (latitude::double precision), (longitude::double precision))
    WHERE status = '정상' AND latitude <> '' AND longitude <> '';

-- 주변 어린이집 조회 — 시군구 단위로 후보를 뽑고 애플리케이션에서 거리 정렬한다.
CREATE INDEX IF NOT EXISTS idx_daycares_nearby
    ON daycares (sigungu_code)
    INCLUDE (daycare_code, name, type_name, address, latitude, longitude)
    WHERE status = '정상' AND latitude IS NOT NULL AND longitude IS NOT NULL;

-- ── 지역 목록·랭킹 인덱스 ─────────────────────────────
CREATE INDEX IF NOT EXISTS idx_daycares_sido_name
    ON daycares (sido_name);

CREATE INDEX IF NOT EXISTS idx_daycares_sigungu_status
    ON daycares (sigungu_code, status);

CREATE INDEX IF NOT EXISTS idx_daycares_ranking_capacity
    ON daycares (capacity DESC)
    WHERE status = '정상' AND capacity > 0;

CREATE INDEX IF NOT EXISTS idx_daycares_ranking_certified
    ON daycares (certified_date DESC)
    WHERE status = '정상' AND certified_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_daycares_ranking_waiting
    ON daycares (waiting_child_total DESC)
    WHERE status = '정상' AND waiting_child_total > 0;

CREATE INDEX IF NOT EXISTS idx_daycares_sido_capacity
    ON daycares (sido_name, capacity DESC)
    WHERE status = '정상' AND capacity > 0;

CREATE INDEX IF NOT EXISTS idx_daycares_sido_certified
    ON daycares (sido_name, certified_date DESC)
    WHERE status = '정상' AND certified_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_daycares_sido_waiting
    ON daycares (sido_name, waiting_child_total DESC)
    WHERE status = '정상' AND waiting_child_total > 0;

-- ── 필터 옵션 뷰 ──────────────────────────────────────
-- 웹 필터 UI가 하드코딩 대신 실제 데이터에서 선택지를 읽는다.
CREATE OR REPLACE VIEW daycare_type_names AS
SELECT DISTINCT type_name
FROM daycares
WHERE status = '정상'
  AND type_name IS NOT NULL
  AND type_name <> ''
ORDER BY type_name;

-- services는 콤마 구분 문자열이라 unnest로 펼쳐 개별 서비스명을 뽑는다.
CREATE OR REPLACE VIEW daycare_service_types AS
SELECT DISTINCT TRIM(BOTH FROM s.service_name) AS service_name
FROM daycares,
     LATERAL unnest(string_to_array(daycares.services, ',')) s(service_name)
WHERE daycares.status = '정상'
  AND daycares.services IS NOT NULL
  AND TRIM(BOTH FROM s.service_name) <> ''
ORDER BY TRIM(BOTH FROM s.service_name);
