--
-- PostgreSQL database dump
--

\restrict MZLwNzO7FUbmqsndkkPB6XHfOy66H9USjn2sgdaTlHKOkMchEj0W5WTV4N8192C

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: content_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_stats (
    uuid text NOT NULL,
    view_count integer DEFAULT 0 NOT NULL,
    like_count integer DEFAULT 0 NOT NULL
);


--
-- Name: TABLE content_stats; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.content_stats IS '블로그 아티클 조회수·좋아요 집계 (kidzly.kr 소유, 동기화 대상 아님)';


--
-- Name: COLUMN content_stats.uuid; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.content_stats.uuid IS '아티클 식별자 (MDX frontmatter의 uuid)';


--
-- Name: COLUMN content_stats.view_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.content_stats.view_count IS '누적 조회수';


--
-- Name: COLUMN content_stats.like_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.content_stats.like_count IS '누적 좋아요 수';


--
-- Name: daycares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.daycares (
    daycare_code character varying(20) NOT NULL,
    sigungu_code character varying(10) NOT NULL,
    sido_name character varying(50),
    sigungu_name character varying(50),
    name character varying(150) NOT NULL,
    type_name character varying(50),
    status character varying(20),
    zip_code character varying(10),
    address character varying(300),
    phone character varying(20),
    fax character varying(20),
    homepage character varying(200),
    latitude character varying(30),
    longitude character varying(30),
    capacity integer,
    current_child_count integer,
    nursery_room_count integer,
    nursery_room_size numeric(18,2),
    playground_count integer,
    cctv_count integer,
    childcare_staff_count integer,
    class_count_total integer,
    child_count_total integer,
    staff_total integer,
    waiting_child_total integer,
    representative_name character varying(60),
    certified_date character varying(10),
    abolished_date character varying(10),
    synced_at timestamp without time zone DEFAULT now() NOT NULL,
    vehicle_operation character varying(10),
    pause_start_date character varying(10),
    pause_end_date character varying(10),
    data_standard_date character varying(10),
    services character varying(150),
    class_count_age_0 integer,
    class_count_age_1 integer,
    class_count_age_2 integer,
    class_count_age_3 integer,
    class_count_age_4 integer,
    class_count_age_5 integer,
    class_count_infant_mixed integer,
    class_count_child_mixed integer,
    class_count_special integer,
    child_count_age_0 integer,
    child_count_age_1 integer,
    child_count_age_2 integer,
    child_count_age_3 integer,
    child_count_age_4 integer,
    child_count_age_5 integer,
    child_count_infant_mixed integer,
    child_count_child_mixed integer,
    child_count_special integer,
    staff_tenure_under_1y double precision,
    staff_tenure_1y_to_2y double precision,
    staff_tenure_2y_to_4y double precision,
    staff_tenure_4y_to_6y double precision,
    staff_tenure_over_6y double precision,
    staff_director_count integer,
    staff_teacher_count integer,
    staff_special_teacher_count integer,
    staff_therapist_count integer,
    staff_nutritionist_count integer,
    staff_nurse_count integer,
    staff_nursing_assistant_count integer,
    staff_cook_count integer,
    staff_office_count integer,
    waiting_child_age_0 integer,
    waiting_child_age_1 integer,
    waiting_child_age_2 integer,
    waiting_child_age_3 integer,
    waiting_child_age_4 integer,
    waiting_child_age_5 integer,
    waiting_child_age_over_6 integer,
    ai_analysis jsonb
);


--
-- Name: TABLE daycares; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.daycares IS '어린이집 기본정보 (cpmsapi030)';


--
-- Name: COLUMN daycares.daycare_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.daycare_code IS '어린이집코드';


--
-- Name: COLUMN daycares.sigungu_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.sigungu_code IS '시군구코드';


--
-- Name: COLUMN daycares.sido_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.sido_name IS '시도명';


--
-- Name: COLUMN daycares.sigungu_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.sigungu_name IS '시군구명';


--
-- Name: COLUMN daycares.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.name IS '어린이집명';


--
-- Name: COLUMN daycares.type_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.type_name IS '어린이집 유형명';


--
-- Name: COLUMN daycares.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.status IS '운영상태명';


--
-- Name: COLUMN daycares.zip_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.zip_code IS '우편번호';


--
-- Name: COLUMN daycares.address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.address IS '주소';


--
-- Name: COLUMN daycares.phone; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.phone IS '전화번호';


--
-- Name: COLUMN daycares.fax; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.fax IS '팩스번호';


--
-- Name: COLUMN daycares.homepage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.homepage IS '홈페이지';


--
-- Name: COLUMN daycares.latitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.latitude IS '위도';


--
-- Name: COLUMN daycares.longitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.longitude IS '경도';


--
-- Name: COLUMN daycares.capacity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.capacity IS '정원';


--
-- Name: COLUMN daycares.current_child_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.current_child_count IS '현원';


--
-- Name: COLUMN daycares.nursery_room_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.nursery_room_count IS '보육실 수';


--
-- Name: COLUMN daycares.nursery_room_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.nursery_room_size IS '보육실 면적(㎡)';


--
-- Name: COLUMN daycares.playground_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.playground_count IS '놀이터 수';


--
-- Name: COLUMN daycares.cctv_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.cctv_count IS 'CCTV 설치 수';


--
-- Name: COLUMN daycares.childcare_staff_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.childcare_staff_count IS '보육교직원 수';


--
-- Name: COLUMN daycares.class_count_total; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_total IS '반 수 합계';


--
-- Name: COLUMN daycares.child_count_total; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_total IS '아동 수 합계';


--
-- Name: COLUMN daycares.staff_total; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_total IS '교직원 수 합계';


--
-- Name: COLUMN daycares.waiting_child_total; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_total IS '입소대기 아동 수 합계';


--
-- Name: COLUMN daycares.representative_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.representative_name IS '대표자명';


--
-- Name: COLUMN daycares.certified_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.certified_date IS '인가일자 (YYYYMMDD)';


--
-- Name: COLUMN daycares.abolished_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.abolished_date IS '폐지일자 (YYYYMMDD)';


--
-- Name: COLUMN daycares.synced_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.synced_at IS '동기화 시각';


--
-- Name: COLUMN daycares.vehicle_operation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.vehicle_operation IS '통학차량운영여부 (운영, 미운영, NULL)';


--
-- Name: COLUMN daycares.pause_start_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.pause_start_date IS '휴지시작일자 (YYYYMMDD)';


--
-- Name: COLUMN daycares.pause_end_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.pause_end_date IS '휴지종료일자 (YYYYMMDD)';


--
-- Name: COLUMN daycares.data_standard_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.data_standard_date IS '데이터기준일자 (YYYYMMDD, 실시간 현재시간)';


--
-- Name: COLUMN daycares.services; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.services IS '제공서비스 (예: 일반, 일시보육)';


--
-- Name: COLUMN daycares.class_count_age_0; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_0 IS '반수-만0세';


--
-- Name: COLUMN daycares.class_count_age_1; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_1 IS '반수-만1세';


--
-- Name: COLUMN daycares.class_count_age_2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_2 IS '반수-만2세';


--
-- Name: COLUMN daycares.class_count_age_3; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_3 IS '반수-만3세';


--
-- Name: COLUMN daycares.class_count_age_4; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_4 IS '반수-만4세';


--
-- Name: COLUMN daycares.class_count_age_5; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_age_5 IS '반수-만5세';


--
-- Name: COLUMN daycares.class_count_infant_mixed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_infant_mixed IS '반수-영아혼합(만0~2세)';


--
-- Name: COLUMN daycares.class_count_child_mixed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_child_mixed IS '반수-유아혼합(만3~5세)';


--
-- Name: COLUMN daycares.class_count_special; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.class_count_special IS '반수-특수장애';


--
-- Name: COLUMN daycares.child_count_age_0; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_0 IS '아동수-만0세';


--
-- Name: COLUMN daycares.child_count_age_1; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_1 IS '아동수-만1세';


--
-- Name: COLUMN daycares.child_count_age_2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_2 IS '아동수-만2세';


--
-- Name: COLUMN daycares.child_count_age_3; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_3 IS '아동수-만3세';


--
-- Name: COLUMN daycares.child_count_age_4; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_4 IS '아동수-만4세';


--
-- Name: COLUMN daycares.child_count_age_5; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_age_5 IS '아동수-만5세';


--
-- Name: COLUMN daycares.child_count_infant_mixed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_infant_mixed IS '아동수-영아혼합(만0~2세)';


--
-- Name: COLUMN daycares.child_count_child_mixed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_child_mixed IS '아동수-유아혼합(만3~5세)';


--
-- Name: COLUMN daycares.child_count_special; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.child_count_special IS '아동수-특수장애';


--
-- Name: COLUMN daycares.staff_tenure_under_1y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_tenure_under_1y IS '근속년수-1년미만';


--
-- Name: COLUMN daycares.staff_tenure_1y_to_2y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_tenure_1y_to_2y IS '근속년수-1년이상~2년미만';


--
-- Name: COLUMN daycares.staff_tenure_2y_to_4y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_tenure_2y_to_4y IS '근속년수-2년이상~4년미만';


--
-- Name: COLUMN daycares.staff_tenure_4y_to_6y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_tenure_4y_to_6y IS '근속년수-4년이상~6년미만';


--
-- Name: COLUMN daycares.staff_tenure_over_6y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_tenure_over_6y IS '근속년수-6년이상';


--
-- Name: COLUMN daycares.staff_director_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_director_count IS '교직원현황-원장';


--
-- Name: COLUMN daycares.staff_teacher_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_teacher_count IS '교직원현황-보육교사';


--
-- Name: COLUMN daycares.staff_special_teacher_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_special_teacher_count IS '교직원현황-특수교사';


--
-- Name: COLUMN daycares.staff_therapist_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_therapist_count IS '교직원현황-치료교사';


--
-- Name: COLUMN daycares.staff_nutritionist_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_nutritionist_count IS '교직원현황-영양사';


--
-- Name: COLUMN daycares.staff_nurse_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_nurse_count IS '교직원현황-간호사';


--
-- Name: COLUMN daycares.staff_nursing_assistant_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_nursing_assistant_count IS '교직원현황-간호조무사';


--
-- Name: COLUMN daycares.staff_cook_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_cook_count IS '교직원현황-조리원';


--
-- Name: COLUMN daycares.staff_office_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.staff_office_count IS '교직원현황-사무직원';


--
-- Name: COLUMN daycares.waiting_child_age_0; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_0 IS '입소대기아동수-0세';


--
-- Name: COLUMN daycares.waiting_child_age_1; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_1 IS '입소대기아동수-1세';


--
-- Name: COLUMN daycares.waiting_child_age_2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_2 IS '입소대기아동수-2세';


--
-- Name: COLUMN daycares.waiting_child_age_3; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_3 IS '입소대기아동수-3세';


--
-- Name: COLUMN daycares.waiting_child_age_4; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_4 IS '입소대기아동수-4세';


--
-- Name: COLUMN daycares.waiting_child_age_5; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_5 IS '입소대기아동수-5세';


--
-- Name: COLUMN daycares.waiting_child_age_over_6; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.waiting_child_age_over_6 IS '입소대기아동수-6세이상';


--
-- Name: COLUMN daycares.ai_analysis; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.daycares.ai_analysis IS 'AI 요약 분석 결과 (summary, strengths, considerations, tags)';


--
-- Name: daycare_service_types; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.daycare_service_types AS
 SELECT DISTINCT TRIM(BOTH FROM s.service_name) AS service_name
   FROM public.daycares,
    LATERAL unnest(string_to_array((daycares.services)::text, ','::text)) s(service_name)
  WHERE (((daycares.status)::text = '정상'::text) AND (daycares.services IS NOT NULL) AND (TRIM(BOTH FROM s.service_name) <> ''::text))
  ORDER BY (TRIM(BOTH FROM s.service_name));


--
-- Name: daycare_type_names; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.daycare_type_names AS
 SELECT DISTINCT type_name
   FROM public.daycares
  WHERE (((status)::text = '정상'::text) AND (type_name IS NOT NULL) AND ((type_name)::text <> ''::text))
  ORDER BY type_name;


--
-- Name: places; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.places (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    summary character varying(40) NOT NULL,
    rating numeric(2,1),
    place_type character varying(20) NOT NULL,
    age_groups text[] DEFAULT '{}'::text[] NOT NULL,
    indoor_outdoor character varying(10) NOT NULL,
    is_free boolean NOT NULL,
    has_parking boolean,
    opening_hours character varying(200) NOT NULL,
    closed_days character varying(200) NOT NULL,
    price_detail character varying(300),
    parking_detail character varying(300),
    has_nursing_room boolean,
    has_diaper_table boolean,
    address character varying(300) NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    thumbnail_url character varying(500),
    last_verified_at date NOT NULL,
    is_published boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT places_age_groups_check CHECK ((age_groups <@ ARRAY['infant'::text, 'toddler'::text, 'preschool'::text, 'elementary'::text])),
    CONSTRAINT places_indoor_outdoor_check CHECK (((indoor_outdoor)::text = ANY ((ARRAY['indoor'::character varying, 'outdoor'::character varying, 'mixed'::character varying])::text[]))),
    CONSTRAINT places_latitude_check CHECK (((latitude >= (33)::double precision) AND (latitude <= (39)::double precision))),
    CONSTRAINT places_longitude_check CHECK (((longitude >= (124)::double precision) AND (longitude <= (132)::double precision))),
    CONSTRAINT places_place_type_check CHECK (((place_type)::text = ANY ((ARRAY['kids_cafe'::character varying, 'park'::character varying, 'indoor_playground'::character varying, 'museum'::character varying, 'zoo'::character varying, 'library'::character varying, 'cafe'::character varying])::text[]))),
    CONSTRAINT places_rating_check CHECK (((rating IS NULL) OR ((rating >= (0)::numeric) AND (rating <= (5)::numeric))))
);


--
-- Name: TABLE places; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.places IS '아이 놀거리 지도 — 운영자 큐레이션 장소. 정부 데이터인 playgrounds 와 별개다';


--
-- Name: COLUMN places.summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.summary IS '핀을 누를지 결정하는 한 줄 소개. 시설 나열이 아니라 장소의 성격을 쓴다';


--
-- Name: COLUMN places.rating; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.rating IS '리뷰 평균 0.0~5.0. 확보 전까지 NULL';


--
-- Name: COLUMN places.place_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.place_type IS 'kids_cafe=키즈카페 park=공원 indoor_playground=실내놀이터 museum=체험관·박물관 zoo=동물원·수목원 library=도서관 cafe=카페';


--
-- Name: COLUMN places.age_groups; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.age_groups IS 'infant=영아 toddler=걸음마 preschool=유아 elementary=초등';


--
-- Name: COLUMN places.indoor_outdoor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.indoor_outdoor IS 'indoor=실내 outdoor=실외 mixed=혼합';


--
-- Name: COLUMN places.has_parking; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.has_parking IS 'NULL 은 아직 확인 안 됨. FALSE(불가)와 구분한다';


--
-- Name: COLUMN places.opening_hours; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.opening_hours IS '요일별로 다르면 한 문자열에 함께 적는다. 요일별 구조화는 추후 과제';


--
-- Name: COLUMN places.has_nursing_room; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.has_nursing_room IS 'NULL 은 아직 확인 안 됨. FALSE(없음)와 구분한다';


--
-- Name: COLUMN places.has_diaper_table; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.has_diaper_table IS 'NULL 은 아직 확인 안 됨. FALSE(없음)와 구분한다';


--
-- Name: COLUMN places.last_verified_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.last_verified_at IS '운영자가 마지막으로 정보를 확인한 날. "N개월 전 확인" 배지의 근거';


--
-- Name: COLUMN places.is_published; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.places.is_published IS 'FALSE 면 작성 중인 초안이라 공개 지도에 노출하지 않는다';


--
-- Name: places_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.places_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: places_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.places_id_seq OWNED BY public.places.id;


--
-- Name: playgrounds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.playgrounds (
    facility_id character varying(20) NOT NULL,
    facility_serial_no character varying(20),
    sido_code character varying(10),
    sigungu_code character varying(10),
    emd_code character varying(20),
    name character varying(200) NOT NULL,
    address character varying(500),
    coord_x numeric(15,4),
    coord_y numeric(15,4),
    install_date character varying(8),
    facility_code1 character varying(20),
    facility_code2 character varying(20),
    install_place_code character varying(10),
    ownership_code character varying(10),
    indoor_outdoor_code character varying(10),
    operation_code character varying(10),
    accident_yn character varying(1),
    deleted_yn character varying(1),
    synced_at timestamp without time zone DEFAULT now() NOT NULL,
    longitude double precision GENERATED ALWAYS AS (degrees(((NULLIF(coord_x, (0)::numeric))::double precision / (6378137.0)::double precision))) STORED,
    latitude double precision GENERATED ALWAYS AS (degrees((((2)::double precision * atan(exp(((NULLIF(coord_y, (0)::numeric))::double precision / (6378137.0)::double precision)))) - (pi() / (2)::double precision)))) STORED
);


--
-- Name: TABLE playgrounds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.playgrounds IS '어린이놀이시설정보 (safemap.go.kr IF_0007)';


--
-- Name: COLUMN playgrounds.facility_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.facility_id IS '시설 일련번호 (objt_id, 소수점 제거 정규화)';


--
-- Name: COLUMN playgrounds.facility_serial_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.facility_serial_no IS '놀이시설 일련번호 (fclty_cd1)';


--
-- Name: COLUMN playgrounds.sido_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.sido_code IS '시도코드 (ctprvn_cd)';


--
-- Name: COLUMN playgrounds.sigungu_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.sigungu_code IS '시군구코드 (sgg_cd)';


--
-- Name: COLUMN playgrounds.emd_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.emd_code IS '읍면동코드 (emd_cd)';


--
-- Name: COLUMN playgrounds.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.name IS '놀이시설명 (fclty_nm)';


--
-- Name: COLUMN playgrounds.address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.address IS '주소 (adres)';


--
-- Name: COLUMN playgrounds.coord_x; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.coord_x IS 'X좌표 — EPSG:3857 Web Mercator (위경도 아님)';


--
-- Name: COLUMN playgrounds.coord_y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.coord_y IS 'Y좌표 — EPSG:3857 Web Mercator (위경도 아님)';


--
-- Name: COLUMN playgrounds.install_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.install_date IS '설치일자 (instl_de, YYYYMMDD)';


--
-- Name: COLUMN playgrounds.facility_code1; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.facility_code1 IS '놀이시설코드1 (fclty_cd2)';


--
-- Name: COLUMN playgrounds.facility_code2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.facility_code2 IS '놀이시설코드2 (fclty_cd3)';


--
-- Name: COLUMN playgrounds.install_place_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.install_place_code IS '설치장소코드 (fclty_cd4). 연속 범위가 아니며 실사용 코드는 22개.
A001=목욕장업소, A002=도로휴게시설, A003=도시공원, A004=식품접객업소, A005=아동복지시설,
A006=어린이집, A007=유치원, A008=대규모점포, A009=의료기관, A010=주택단지,
A011=학교, A012=학원, A013=놀이제공영업소, A020=주상복합, A022=박물관,
A023=종교시설, A030=자연휴양림, A031=하천, A032=야영장, A033=공공도서관,
A092=육아종합지원센터, A093=유아교육진흥원';


--
-- Name: COLUMN playgrounds.ownership_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.ownership_code IS '민간/공공구분 (fclty_cd5, C001=민간 C002=공공)';


--
-- Name: COLUMN playgrounds.indoor_outdoor_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.indoor_outdoor_code IS '실내외구분 (fclty_cd6, O001=실내 O002=실외)';


--
-- Name: COLUMN playgrounds.operation_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.operation_code IS '운영구분 (fclty_cd7, B001=운영 B003=이용금지)';


--
-- Name: COLUMN playgrounds.accident_yn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.accident_yn IS '사고이력정보 (ac_yn)';


--
-- Name: COLUMN playgrounds.deleted_yn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.deleted_yn IS '삭제여부 (del_yn)';


--
-- Name: COLUMN playgrounds.synced_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.synced_at IS '마지막 변경 반영 시각 (변경 없으면 갱신되지 않음)';


--
-- Name: COLUMN playgrounds.longitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.longitude IS '경도(WGS84) — coord_x에서 자동 계산, 직접 입력 불가. coord_x=0(좌표 미입력)이면 NULL';


--
-- Name: COLUMN playgrounds.latitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.playgrounds.latitude IS '위도(WGS84) — coord_y에서 자동 계산, 직접 입력 불가. coord_y=0(좌표 미입력)이면 NULL';


--
-- Name: sigungu_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sigungu_codes (
    code character varying(10) NOT NULL,
    level character varying(10) NOT NULL,
    sido_code character varying(2) NOT NULL,
    sigungu_code character varying(5),
    emd_code character varying(8),
    name character varying(200) NOT NULL,
    synced_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sigungu_codes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sigungu_codes IS '국토교통부 공식 법정동코드 참조 테이블 (odcloud.kr, 리 레벨 제외)';


--
-- Name: COLUMN sigungu_codes.code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.code IS '법정동코드 원본 10자리 (예: 1111010100)';


--
-- Name: COLUMN sigungu_codes.level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.level IS '코드 레벨 (SIDO / SIGUNGU / EMD)';


--
-- Name: COLUMN sigungu_codes.sido_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.sido_code IS '시도코드 — code 앞 2자리 (모든 레벨)';


--
-- Name: COLUMN sigungu_codes.sigungu_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.sigungu_code IS '시군구코드 — code 앞 5자리 (SIGUNGU/EMD 레벨만)';


--
-- Name: COLUMN sigungu_codes.emd_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.emd_code IS '읍면동코드 — code 앞 8자리 (EMD 레벨만)';


--
-- Name: COLUMN sigungu_codes.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.name IS '법정동명 원문 (예: 서울특별시 종로구 청운동)';


--
-- Name: COLUMN sigungu_codes.synced_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungu_codes.synced_at IS '마지막 변경 반영 시각 (변경 없으면 갱신되지 않음)';


--
-- Name: sigungus; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sigungus (
    arcode character varying(10) NOT NULL,
    sidoname character varying(50) NOT NULL,
    sigunname character varying(50) NOT NULL,
    synced_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sigungus; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sigungus IS '시군구 정보 (cpmsapi020)';


--
-- Name: COLUMN sigungus.arcode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungus.arcode IS '시군구코드';


--
-- Name: COLUMN sigungus.sidoname; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungus.sidoname IS '시도명';


--
-- Name: COLUMN sigungus.sigunname; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungus.sigunname IS '시군구명';


--
-- Name: COLUMN sigungus.synced_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sigungus.synced_at IS '동기화 시각';


--
-- Name: sync_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_histories (
    id bigint NOT NULL,
    sync_type character varying(20) NOT NULL,
    target_year_month character varying(7),
    status character varying(10) DEFAULT 'RUNNING'::character varying NOT NULL,
    total_count integer DEFAULT 0 NOT NULL,
    upsert_count integer DEFAULT 0 NOT NULL,
    closed_count integer DEFAULT 0 NOT NULL,
    error_message character varying(2000),
    started_at timestamp without time zone DEFAULT now() NOT NULL,
    finished_at timestamp without time zone
);


--
-- Name: TABLE sync_histories; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sync_histories IS '동기화 실행 이력';


--
-- Name: COLUMN sync_histories.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.id IS '식별자';


--
-- Name: COLUMN sync_histories.sync_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.sync_type IS '동기화 유형 (FULL / DELTA / PLAYGROUND / SIGUNGU_CODE)';


--
-- Name: COLUMN sync_histories.target_year_month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.target_year_month IS '대상 연월 (YYYY-MM, MONTHLY 동기화 시 사용)';


--
-- Name: COLUMN sync_histories.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.status IS '상태 (RUNNING / SUCCESS / FAILED)';


--
-- Name: COLUMN sync_histories.total_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.total_count IS '전체 처리 건수';


--
-- Name: COLUMN sync_histories.upsert_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.upsert_count IS '추가/수정 건수';


--
-- Name: COLUMN sync_histories.closed_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.closed_count IS '폐지 처리 건수';


--
-- Name: COLUMN sync_histories.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.error_message IS '오류 메시지';


--
-- Name: COLUMN sync_histories.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.started_at IS '동기화 시작 시각';


--
-- Name: COLUMN sync_histories.finished_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sync_histories.finished_at IS '동기화 완료 시각';


--
-- Name: sync_histories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sync_histories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sync_histories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sync_histories_id_seq OWNED BY public.sync_histories.id;


--
-- Name: places id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places ALTER COLUMN id SET DEFAULT nextval('public.places_id_seq'::regclass);


--
-- Name: sync_histories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_histories ALTER COLUMN id SET DEFAULT nextval('public.sync_histories_id_seq'::regclass);


--
-- Name: content_stats content_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_stats
    ADD CONSTRAINT content_stats_pkey PRIMARY KEY (uuid);


--
-- Name: daycares daycares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daycares
    ADD CONSTRAINT daycares_pkey PRIMARY KEY (daycare_code);


--
-- Name: places places_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT places_pkey PRIMARY KEY (id);


--
-- Name: playgrounds playgrounds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playgrounds
    ADD CONSTRAINT playgrounds_pkey PRIMARY KEY (facility_id);


--
-- Name: sigungu_codes sigungu_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sigungu_codes
    ADD CONSTRAINT sigungu_codes_pkey PRIMARY KEY (code);


--
-- Name: sigungus sigungus_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sigungus
    ADD CONSTRAINT sigungus_pkey PRIMARY KEY (arcode);


--
-- Name: sync_histories sync_histories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_histories
    ADD CONSTRAINT sync_histories_pkey PRIMARY KEY (id);


--
-- Name: idx_daycares_address_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_address_trgm ON public.daycares USING gin (address public.gin_trgm_ops);


--
-- Name: idx_daycares_map_bbox; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_map_bbox ON public.daycares USING btree (status, latitude, longitude) WHERE ((latitude IS NOT NULL) AND (longitude IS NOT NULL));


--
-- Name: idx_daycares_name_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_name_trgm ON public.daycares USING gin (name public.gin_trgm_ops);


--
-- Name: idx_daycares_nearby; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_nearby ON public.daycares USING btree (sigungu_code) INCLUDE (daycare_code, name, type_name, address, latitude, longitude) WHERE (((status)::text = '정상'::text) AND (latitude IS NOT NULL) AND (longitude IS NOT NULL));


--
-- Name: idx_daycares_ranking_capacity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_ranking_capacity ON public.daycares USING btree (capacity DESC) WHERE (((status)::text = '정상'::text) AND (capacity > 0));


--
-- Name: idx_daycares_ranking_certified; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_ranking_certified ON public.daycares USING btree (certified_date DESC) WHERE (((status)::text = '정상'::text) AND (certified_date IS NOT NULL));


--
-- Name: idx_daycares_ranking_waiting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_ranking_waiting ON public.daycares USING btree (waiting_child_total DESC) WHERE (((status)::text = '정상'::text) AND (waiting_child_total > 0));


--
-- Name: idx_daycares_sido_capacity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sido_capacity ON public.daycares USING btree (sido_name, capacity DESC) WHERE (((status)::text = '정상'::text) AND (capacity > 0));


--
-- Name: idx_daycares_sido_certified; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sido_certified ON public.daycares USING btree (sido_name, certified_date DESC) WHERE (((status)::text = '정상'::text) AND (certified_date IS NOT NULL));


--
-- Name: idx_daycares_sido_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sido_name ON public.daycares USING btree (sido_name);


--
-- Name: idx_daycares_sido_waiting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sido_waiting ON public.daycares USING btree (sido_name, waiting_child_total DESC) WHERE (((status)::text = '정상'::text) AND (waiting_child_total > 0));


--
-- Name: idx_daycares_sigungu_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sigungu_code ON public.daycares USING btree (sigungu_code);


--
-- Name: idx_daycares_sigungu_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_sigungu_status ON public.daycares USING btree (sigungu_code, status);


--
-- Name: idx_daycares_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_status ON public.daycares USING btree (status);


--
-- Name: idx_daycares_status_latlng_float; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daycares_status_latlng_float ON public.daycares USING btree (status, ((latitude)::double precision), ((longitude)::double precision)) WHERE (((status)::text = '정상'::text) AND ((latitude)::text <> ''::text) AND ((longitude)::text <> ''::text));


--
-- Name: idx_places_bounds; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_places_bounds ON public.places USING btree (is_published, latitude, longitude);


--
-- Name: idx_places_place_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_places_place_type ON public.places USING btree (place_type);


--
-- Name: idx_places_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_places_updated_at ON public.places USING btree (updated_at DESC);


--
-- Name: idx_playgrounds_map_bbox; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_playgrounds_map_bbox ON public.playgrounds USING btree (latitude, longitude) WHERE ((latitude IS NOT NULL) AND (longitude IS NOT NULL));


--
-- Name: idx_playgrounds_sigungu_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_playgrounds_sigungu_code ON public.playgrounds USING btree (sigungu_code);


--
-- Name: idx_sigungu_codes_emd_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sigungu_codes_emd_code ON public.sigungu_codes USING btree (emd_code);


--
-- Name: idx_sigungu_codes_sigungu_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sigungu_codes_sigungu_code ON public.sigungu_codes USING btree (sigungu_code);


--
-- Name: idx_sigungus_sidoname; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sigungus_sidoname ON public.sigungus USING btree (sidoname);


--
-- Name: idx_sync_histories_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sync_histories_started_at ON public.sync_histories USING btree (started_at DESC);


--
-- Name: idx_sync_histories_sync_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sync_histories_sync_type ON public.sync_histories USING btree (sync_type);


--
-- Name: places; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.places ENABLE ROW LEVEL SECURITY;

--
-- Name: places places_public_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY places_public_read ON public.places FOR SELECT USING (is_published);


--
-- PostgreSQL database dump complete
--

\unrestrict MZLwNzO7FUbmqsndkkPB6XHfOy66H9USjn2sgdaTlHKOkMchEj0W5WTV4N8192C

