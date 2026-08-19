# 작업 계획: 법정동코드(sigungu_codes) 참조 테이블 신설

> 작성일: 2026-08-17 · 상태: **설계 확정, 구현 대기**
> 후속 작업 시 `kidzly-feature` 스킬(architect → implementer → tester)로 진행

---

## 1. 배경

`playgrounds`(놀이시설, safemap.go.kr)와 `daycares`/`sigungus`(어린이집, cpmsapi020)가 각자 다른 시군구 코드 체계를 쓰고 있어 지역 기준으로 두 데이터를 엮기 어렵다는 문제를 조사하며 나온 후속 작업이다.

### 조사로 확인된 사실

| 사실 | 근거 |
|---|---|
| `sigungus.arcode`(어린이집 API 코드)는 대부분 국토교통부 공식 법정동코드와 값이 동일하다 | 실제 DB 대조: `sigungus` ↔ `playgrounds` 조인 시 87.8%(73,977/84,251건) 일치 |
| `playgrounds.sigungu_code`(safemap)도 대부분 법정동코드와 동일하다 | 위와 동일 |
| **전남·광주 통합권역**(`sido_code=12`, "전남광주통합특별시")은 safemap에만 존재, 어린이집 API·국토부 공식 법정동코드 어디에도 없다 | `playgrounds` 27개 시군구코드(전남 22개 시군 + 광주 5개 구 합산과 정확히 일치) 확인, 법정동코드 API "통합" 검색 0건 |
| 어린이집 API(cpmsapi020)는 **국토부 법정동코드보다 오히려 앞서 있는 부분도 있다** (인천 제물포구·영종구·서해구·검단구, 화성시 만세구·효행구·병점구·동탄구 — 법정동코드엔 없음) | `sigungus`에 실재, 법정동코드 API엔 없음 (실시간 대조) |
| 어린이집 API는 반대로 **뒤처진 부분도 있다** (제주=`49`, 법정동코드는 이미 `50`) | `sigungus`에 prefix `50` 0건, `49`만 존재 |
| `daycares` 전체 60,223건 중 8.7%(5,250건, 30개 코드)가 법정동코드와 불일치 | 실측 대조. 위 3가지 원인이 섞여 있음 (신설구/구식코드/광주통합 잔존 데이터) |
| 세 시스템(어린이집 API / 국토부 법정동코드 / safemap)은 **각자 다른 속도로 행정구역 개편을 반영** — 어느 하나를 "정답"으로 강제 치환할 수 없다 | 위 전체 |

### 결론

기존 `daycares`/`sigungus`/`playgrounds`의 코드 컬럼은 **그대로 둔다.** 대신 국토부 공식 법정동코드를 별도 참조 테이블로 동기화해서, 필요할 때(주로 `playgrounds`) 조인해 지역명을 얻는 방식으로 간다.

---

## 2. 최종 설계

### 2.1 신규 테이블 `sigungu_codes`

```sql
CREATE TABLE sigungu_codes
(
    code           VARCHAR(10)  NOT NULL PRIMARY KEY,  -- 법정동코드 원본 10자리 (예: 1111010100)
    level          VARCHAR(10)  NOT NULL,               -- 'SIDO' / 'SIGUNGU' / 'EMD'
    sido_code      VARCHAR(2)   NOT NULL,               -- 앞 2자리, 모든 레벨에 항상 값 있음
    sigungu_code   VARCHAR(5),                          -- 시도+시군구 5자리 절대값 (SIGUNGU, EMD 레벨만)
    emd_code       VARCHAR(8),                          -- 시도+시군구+읍면동 8자리 절대값 (EMD 레벨만)
    name           VARCHAR(200) NOT NULL,               -- 법정동명 원문 (예: "서울특별시 종로구 청운동")
    synced_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sigungu_codes_sigungu_code ON sigungu_codes (sigungu_code);
CREATE INDEX idx_sigungu_codes_emd_code ON sigungu_codes (emd_code);
```

- 이름은 `sigungu_codes`로 확정 (3단계를 다 담지만 이름은 시군구 위주로 짧게 — 팀 합의 사항, 코드 리뷰 시 재론하지 않음)
- **"리" 레벨은 동기화 대상에서 제외** — `playgrounds.emd_code`가 8자리(읍면동)까지만 쓰므로 그 이상 세분화는 불필요
- `sido_code`/`sigungu_code`/`emd_code`는 **`법정동명` 문자열을 공백으로 split해서 얻지 않는다** — 코드 자릿수 고정 위치로 파싱한다 (지명에 공백이 섞인 케이스로 깨지는 것 방지)

### 2.2 코드 레벨 판별 규칙

10자리 법정동코드 `code`에 대해:

```
SIDO   : code % 100000000 == 0                        (뒤 8자리 = 0)
SIGUNGU: code % 100000 == 0  AND  code % 100000000 != 0  (뒤 5자리 = 0, 뒤 8자리 ≠ 0)
EMD    : code % 100 == 0  AND  code % 100000 != 0         (뒤 2자리 = 0, 뒤 5자리 ≠ 0)
(리 레벨: 그 외 → 동기화 제외)
```

### 2.3 데이터 소스

| 항목 | 값 |
|---|---|
| Host | `api.odcloud.kr` |
| Path (2025-08 최신판) | `/api/15123287/v1/uddi:b68902fa-d058-4a17-b188-ff46b7eaaac7` |
| 인증 | Query `serviceKey` (공공데이터포털 발급키, 실제 값은 `${LEGAL_DONG_CODE_SERVICE_KEY:}` 환경변수로 주입 — safemap 때와 동일하게 기본값 없이 쓰면 기존 배치가 깨지므로 **빈 기본값 필수**) |
| 요청 파라미터 | `page`, `perPage`(2000까지 확인됨, 상한 미확인이나 2000이면 충분), `returnType` |
| 응답 구조 | `{page, perPage, totalCount, currentCount, matchCount, data: [{법정동코드, 법정동명, 폐지여부}]}` |
| 총 건수 | 49,861건 (2025-08 기준, 리 레벨 포함) — `폐지여부="존재"`인 것만 사용 |
| 필터링 후 예상 건수 | 시도(17) + 시군구(약 264) + 읍면동(약 3,500~4,000 추정) — 실측 필요 |

### 2.4 영향 범위

- **`daycares`/`sigungus`**: 변경 없음
- **`playgrounds`**: 변경 없음 (컬럼 추가 없음, sync 로직 무변경)
- **조인은 조회 시점에만**:
  ```sql
  playgrounds p JOIN sigungu_codes sc
    ON sc.sigungu_code = p.sigungu_code AND sc.level = 'SIGUNGU'
  ```
- 매칭 실패(전남광주통합권역 등)는 그냥 결과 없음(NULL) — 강제 매핑 테이블 만들지 않음

---

## 3. 구현 계획 (착수 시 `kidzly-feature`로 진행)

1. **Flyway 마이그레이션** (`V15__create_sigungu_codes.sql`) → 검증: `sigungu_codes` 테이블 생성, 인덱스 확인
2. **Port/Client**: `LegalDongCodeApiPort`, `LegalDongCodeApiClient` (JSON 파싱, 페이지네이션) → 검증: 단위 테스트로 시도/시군구/읍면동 레벨 판별 및 코드 파싱 로직 확인
3. **Properties/Config**: `LegalDongCodeApiProperties` (prefix `legaldong.api`), `application.yml`에 `service-key: ${LEGAL_DONG_CODE_SERVICE_KEY:}` 추가 → 검증: 빈 키로 기존 FULL/DELTA/PLAYGROUND 배치 기동 영향 없음 확인
4. **도메인/Repository**: `SigunguCode` 엔티티, `SigunguCodeRepository` + Impl (UPSERT, `code` PK 기준) → 검증: Testcontainers로 UPSERT 동작 확인
5. **UseCase**: `SigunguCodeSyncUseCase` — 페이지네이션 순회, 리 레벨 필터링, 레벨 판별 후 저장 → 검증: 단위 테스트 (2500건/1000페이지사이즈 기준 종료조건 등, playground 때와 동일 패턴)
6. **Orchestrator/SyncJobRunner**: `SYNC_JOB=SIGUNGU_CODE` 분기 추가, `SyncHistory.SyncType`에 `SIGUNGU_CODE` 추가 → 검증: 로컬 1회 실행으로 실데이터 동기화 확인
7. **GitHub Actions 워크플로**: 신규 또는 기존 배치에 편입 — **법정동코드는 행정구역 개편 시에만 바뀌는 정적 데이터**이므로 매일 돌릴 필요 없음. 주 1회 수준으로 충분해 보임 (착수 시 재확인)
8. **테스트**: Kotest + MockK 단위 테스트, Testcontainers 통합 테스트 (playground 패턴 재사용)

---

## 4. 미해결/후속 검토 사항

- 읍면동 레벨 실제 건수 및 동기화 소요 시간 실측 필요 (49,861건 전체를 훑어야 리 레벨 여부 판별 가능 — API가 레벨을 안 주고 코드로만 판별해야 해서 매 건 순회 필요)
- 동기화 주기: 매일 돌릴 필요 없어 보이므로 별도 워크플로 스케줄 결정 필요
- `daycares`의 8.7% 불일치(신설구/구식코드/광주통합 잔존)는 이 작업 범위 밖 — 별도 이슈로 남겨둠
