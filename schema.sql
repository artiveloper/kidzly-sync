-- auto-generated definition
create table daycares
(
    daycare_code                  varchar(20)             not null
        primary key,
    sigungu_code                  varchar(10)             not null,
    sido_name                     varchar(50),
    sigungu_name                  varchar(50),
    name                          varchar(150)            not null,
    type_name                     varchar(50),
    status                        varchar(20),
    zip_code                      varchar(10),
    address                       varchar(300),
    phone                         varchar(20),
    fax                           varchar(20),
    homepage                      varchar(200),
    latitude                      varchar(30),
    longitude                     varchar(30),
    capacity                      integer,
    current_child_count           integer,
    nursery_room_count            integer,
    nursery_room_size             numeric(18, 2),
    playground_count              integer,
    cctv_count                    integer,
    childcare_staff_count         integer,
    class_count_total             integer,
    child_count_total             integer,
    staff_total                   integer,
    waiting_child_total           integer,
    representative_name           varchar(60),
    certified_date                varchar(10),
    abolished_date                varchar(10),
    synced_at                     timestamp default now() not null,
    vehicle_operation             varchar(10),
    pause_start_date              varchar(10),
    pause_end_date                varchar(10),
    data_standard_date            varchar(10),
    services                      varchar(150),
    class_count_age_0             integer,
    class_count_age_1             integer,
    class_count_age_2             integer,
    class_count_age_3             integer,
    class_count_age_4             integer,
    class_count_age_5             integer,
    class_count_infant_mixed      integer,
    class_count_child_mixed       integer,
    class_count_special           integer,
    child_count_age_0             integer,
    child_count_age_1             integer,
    child_count_age_2             integer,
    child_count_age_3             integer,
    child_count_age_4             integer,
    child_count_age_5             integer,
    child_count_infant_mixed      integer,
    child_count_child_mixed       integer,
    child_count_special           integer,
    staff_tenure_under_1y         integer,
    staff_tenure_1y_to_2y         integer,
    staff_tenure_2y_to_4y         integer,
    staff_tenure_4y_to_6y         integer,
    staff_tenure_over_6y          integer,
    staff_director_count          integer,
    staff_teacher_count           integer,
    staff_special_teacher_count   integer,
    staff_therapist_count         integer,
    staff_nutritionist_count      integer,
    staff_nurse_count             integer,
    staff_nursing_assistant_count integer,
    staff_cook_count              integer,
    staff_office_count            integer,
    waiting_child_age_0           integer,
    waiting_child_age_1           integer,
    waiting_child_age_2           integer,
    waiting_child_age_3           integer,
    waiting_child_age_4           integer,
    waiting_child_age_5           integer,
    waiting_child_age_over_6      integer
)
    using ???;

comment on table daycares is '어린이집 기본정보 (cpmsapi030)';

comment on column daycares.daycare_code is '어린이집코드';

comment on column daycares.sigungu_code is '시군구코드';

comment on column daycares.sido_name is '시도명';

comment on column daycares.sigungu_name is '시군구명';

comment on column daycares.name is '어린이집명';

comment on column daycares.type_name is '어린이집 유형명';

comment on column daycares.status is '운영상태명';

comment on column daycares.zip_code is '우편번호';

comment on column daycares.address is '주소';

comment on column daycares.phone is '전화번호';

comment on column daycares.fax is '팩스번호';

comment on column daycares.homepage is '홈페이지';

comment on column daycares.latitude is '위도';

comment on column daycares.longitude is '경도';

comment on column daycares.capacity is '정원';

comment on column daycares.current_child_count is '현원';

comment on column daycares.nursery_room_count is '보육실 수';

comment on column daycares.nursery_room_size is '보육실 면적(㎡)';

comment on column daycares.playground_count is '놀이터 수';

comment on column daycares.cctv_count is 'CCTV 설치 수';

comment on column daycares.childcare_staff_count is '차량 수';

comment on column daycares.class_count_total is '반 수 합계';

comment on column daycares.child_count_total is '아동 수 합계';

comment on column daycares.staff_total is '교직원 수 합계';

comment on column daycares.waiting_child_total is '여성 교직원 수 합계';

comment on column daycares.representative_name is '대표자명';

comment on column daycares.certified_date is '인가일자 (YYYYMMDD)';

comment on column daycares.abolished_date is '폐지일자 (YYYYMMDD)';

comment on column daycares.synced_at is '동기화 시각';

comment on column daycares.vehicle_operation is '통학차량운영여부 (운영, 미운영, NULL)';

comment on column daycares.pause_start_date is '휴지시작일자 (YYYYMMDD)';

comment on column daycares.pause_end_date is '휴지종료일자 (YYYYMMDD)';

comment on column daycares.data_standard_date is '데이터기준일자 (YYYYMMDD, 실시간 현재시간)';

comment on column daycares.services is '제공서비스 (예: 일반, 일시보육)';

comment on column daycares.class_count_age_0 is '반수-만0세';

comment on column daycares.class_count_age_1 is '반수-만1세';

comment on column daycares.class_count_age_2 is '반수-만2세';

comment on column daycares.class_count_age_3 is '반수-만3세';

comment on column daycares.class_count_age_4 is '반수-만4세';

comment on column daycares.class_count_age_5 is '반수-만5세';

comment on column daycares.class_count_infant_mixed is '반수-영아혼합(만0~2세)';

comment on column daycares.class_count_child_mixed is '반수-유아혼합(만3~5세)';

comment on column daycares.class_count_special is '반수-특수장애';

comment on column daycares.child_count_age_0 is '아동수-만0세';

comment on column daycares.child_count_age_1 is '아동수-만1세';

comment on column daycares.child_count_age_2 is '아동수-만2세';

comment on column daycares.child_count_age_3 is '아동수-만3세';

comment on column daycares.child_count_age_4 is '아동수-만4세';

comment on column daycares.child_count_age_5 is '아동수-만5세';

comment on column daycares.child_count_infant_mixed is '아동수-영아혼합(만0~2세)';

comment on column daycares.child_count_child_mixed is '아동수-유아혼합(만3~5세)';

comment on column daycares.child_count_special is '아동수-특수장애';

comment on column daycares.staff_tenure_under_1y is '근속년수-1년미만';

comment on column daycares.staff_tenure_1y_to_2y is '근속년수-1년이상~2년미만';

comment on column daycares.staff_tenure_2y_to_4y is '근속년수-2년이상~4년미만';

comment on column daycares.staff_tenure_4y_to_6y is '근속년수-4년이상~6년미만';

comment on column daycares.staff_tenure_over_6y is '근속년수-6년이상';

comment on column daycares.staff_director_count is '교직원현황-원장';

comment on column daycares.staff_teacher_count is '교직원현황-보육교사';

comment on column daycares.staff_special_teacher_count is '교직원현황-특수교사';

comment on column daycares.staff_therapist_count is '교직원현황-치료교사';

comment on column daycares.staff_nutritionist_count is '교직원현황-영양사';

comment on column daycares.staff_nurse_count is '교직원현황-간호사';

comment on column daycares.staff_nursing_assistant_count is '교직원현황-간호조무사';

comment on column daycares.staff_cook_count is '교직원현황-조리원';

comment on column daycares.staff_office_count is '교직원현황-사무직원';

comment on column daycares.waiting_child_age_0 is '입소대기아동수-0세';

comment on column daycares.waiting_child_age_1 is '입소대기아동수-1세';

comment on column daycares.waiting_child_age_2 is '입소대기아동수-2세';

comment on column daycares.waiting_child_age_3 is '입소대기아동수-3세';

comment on column daycares.waiting_child_age_4 is '입소대기아동수-4세';

comment on column daycares.waiting_child_age_5 is '입소대기아동수-5세';

comment on column daycares.waiting_child_age_over_6 is '입소대기아동수-6세이상';

alter table daycares
    owner to postgres;

create index idx_daycares_sigungu_code
    on daycares using ??? (sigungu_code);

create index idx_daycares_status
    on daycares using ??? (status);

grant delete, insert, references, select, trigger, truncate, update on daycares to anon;

grant delete, insert, references, select, trigger, truncate, update on daycares to authenticated;

grant delete, insert, references, select, trigger, truncate, update on daycares to service_role;



-- auto-generated definition
create table sigungus
(
    arcode    varchar(10)             not null
        primary key,
    sidoname  varchar(50)             not null,
    sigunname varchar(50)             not null,
    synced_at timestamp default now() not null
)
    using ???;

comment on table sigungus is '시군구 정보 (cpmsapi020)';

comment on column sigungus.arcode is '시군구코드';

comment on column sigungus.sidoname is '시도명';

comment on column sigungus.sigunname is '시군구명';

comment on column sigungus.synced_at is '동기화 시각';

alter table sigungus
    owner to postgres;

create index idx_sigungus_sidoname
    on sigungus using ??? (sidoname);

grant delete, insert, references, select, trigger, truncate, update on sigungus to anon;

grant delete, insert, references, select, trigger, truncate, update on sigungus to authenticated;

grant delete, insert, references, select, trigger, truncate, update on sigungus to service_role;


