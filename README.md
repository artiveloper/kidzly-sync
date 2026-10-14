# kidzly-sync

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql)](https://www.postgresql.org)

공공데이터포털 어린이집/놀이시설 API에서 데이터를 수집하여 PostgreSQL에 동기화하는 CLI 배치입니다.

---

## 배경 & 목적

공공데이터포털(childcare.go.kr)이 제공하는 어린이집 정보 API는 XML 형식으로 응답하며, 전국 시군구 단위로 개별 호출이 필요합니다. 단순 조회 서비스가 매번 외부 API를 직접 호출하면 응답 지연과 API 키 소진 문제가 발생하기 때문에, 별도 동기화 배치를 두어 최신 데이터를 자체 DB에 유지하는 방식을 채택했습니다.

- **전체 동기화**: 주 1회 전국 시군구를 순회하며 어린이집 전량 upsert
- **증분 동기화**: 매일 당월 신규 개원 및 폐지 어린이집만 처리하여 API 호출 최소화
- **놀이시설 동기화**: safemap.go.kr 데이터를 매일 전량 upsert
- **법정동코드 동기화**: 주 1회 odcloud.kr 기준 행정구역 마스터 데이터 최신화
- **동기화 이력 추적**: 실행 결과(처리 건수, 소요 시간, 오류)를 DB에 기록
- **Telegram 알림**: 동기화 완료/실패 시 즉시 알림 발송

원래 Kotlin/Spring Boot로 구현되어 있었으나, 빌드·기동 부담을 줄이기 위해 2026년 하반기에 잡 단위로 Python으로 전환했다. REST 컨트롤러는 운영에서 쓰이지 않아 포팅하지 않고 CLI만 남겼다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 전체 동기화 (`full`) | 전국 어린이집 데이터를 시군구별로 순회하며 전량 upsert |
| 증분 동기화 (`delta`) | 월별 신규 개원/폐지 어린이집만 처리 |
| 놀이시설 동기화 (`playground`) | safemap.go.kr 놀이시설 데이터 전량 upsert |
| 법정동코드 동기화 (`sigungu-code`) | 행정구역 마스터 데이터 최신화 |
| 동기화 이력 관리 | 실행 유형, 처리 건수, 소요 시간, 오류 메시지 기록 |
| 스킵 가드 | 당일 이미 성공했으면 건너뛴다 (`--force`로 강제 재실행) |
| Telegram 알림 | 동기화 성공/실패 결과를 Telegram Bot으로 즉시 알림 |
| 증분 AI 요약 | 증분 동기화 후 신규 어린이집 자동 AI 요약 생성 (Groq·Gemini·Ollama 전환 가능) |

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────┐
│   Presentation (cli.py)                          │  GitHub Actions one-shot 배치 실행
├──────────────────────────────────────────────────┤
│   Application (SyncOrchestrator, UseCase)        │  동기화 오케스트레이션, 스킵 가드, 알림
├──────────────────────────────────────────────────┤
│   Domain (SyncHistory, DomainError, Result)       │  순수 비즈니스 규칙, 도메인 모델
├──────────────────────────────────────────────────┤
│   Infrastructure (ApiClient, Repository)         │  공공 API 호출, psycopg raw SQL
└──────────────────────────────────────────────────┘
```

**데이터 흐름**

```
kidzly-sync <job> [--force] [--year-month YYYY-MM]
        │
   SyncOrchestrator ── 스킵 가드 / SyncHistory 기록 / TelegramNotifier
        │
  FullSyncUseCase / DeltaSyncUseCase / PlaygroundFullSyncUseCase
  / SigunguCodeSyncUseCase / IncrementalDaycaresSummaryUseCase
        │                                        │
  childcare.go.kr / safemap.go.kr          AiSummaryPort
  / odcloud.kr (XML/JSON API)             (Groq / Gemini / Ollama)
        │
  Repository (psycopg3, INSERT ... ON CONFLICT)
        │
  PostgreSQL (daycares, sigungus, sync_histories, playgrounds, sigungu_codes)
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 언어 | Python 3.12+ |
| CLI | `argparse` (`kidzly_sync/cli.py`) |
| 데이터베이스 | PostgreSQL 15+ |
| DB 접근 | psycopg3 (ORM 없음, raw SQL upsert) |
| 마이그레이션 | Alembic |
| 에러 처리 | 자체 `Result`/`Ok`/`Err` (`kidzly_sync/domain/result.py`) |
| HTTP 클라이언트 | httpx |
| 재시도 | tenacity (429 응답 시 1분 대기 후 최대 3회) |
| AI 요약 | Groq API (`openai/gpt-oss-120b`), Gemini 2.0 Flash, Ollama (`qwen3:14b`) — `AI_PROVIDER` env로 전환 |
| 알림 | Telegram Bot API |
| 테스트 | pytest, testcontainers |
| 패키징 | uv + hatchling |

---

## 데이터베이스 스키마

**이 저장소가 kidzly DB 스키마의 단일 소유자다.** kidzly.kr(웹)은 읽기만 하며 스키마를 바꾸지 않는다.

웹이 쓰는 객체(`content_stats`, 조회 인덱스, 필터 옵션 뷰)도 여기서 관리한다.

| 소비자 | 대상 |
|--------|------|
| kidzly-sync | `daycares`, `sigungus`, `sync_histories`, `playgrounds`, `sigungu_codes` |
| kidzly.kr | `content_stats`, `daycares` 조회 인덱스, `daycare_type_names`·`daycare_service_types` 뷰 |

마이그레이션 도구는 **Alembic**이다 (`migrations/versions/`). 과거 Flyway 시절 마이그레이션(`docs/legacy/migration/V1~V20__*.sql`)은 더 이상 실행되지 않지만 운영 히스토리 기록으로 보존한다. 베이스라인 리비전 `0001`이 당시 운영 `schema.sql`(pg_dump)을 통째로 실행해 그 이력을 한 번에 편입했다.

### 변경 절차

1. `migrations/versions/`에 Alembic 리비전 생성 (`uv run --extra migrations alembic revision -m "설명"`), `upgrade()`에 `op.execute()`로 생 SQL을 넣는다.
2. 로컬 검증 — 빈 DB에 `alembic upgrade head`가 처음부터 통과하는지 본다.

   ```bash
   docker run -d --name kidzly-mig-test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=kidzly postgres:16-alpine
   DB_URL="postgresql://postgres:test@localhost:5432/kidzly" uv run --extra migrations alembic upgrade head
   docker rm -f kidzly-mig-test
   ```

3. `db/schema.sql` 재생성 — 손으로 고치지 않는다. 위 컨테이너에서 뽑는다 (`pg_dump --schema-only --no-owner --no-privileges`).
4. 커밋 → **운영 반영**. `db-migrate.yml` 워크플로를 `workflow_dispatch`로 수동 실행한다 (`alembic upgrade head`, `cancel-in-progress: false`).
5. 웹이 읽는 컬럼이 바뀌었으면 kidzly.kr의 `packages/supabase/src/types.ts`를 갱신한다. **마이그레이션이 운영에 적용된 뒤에 웹을 배포한다** — 두 저장소라 배포 순서는 자동으로 보장되지 않는다.

### 좌표 주의

`playgrounds.coord_x/coord_y`는 safemap.go.kr이 주는 **EPSG:3857 Web Mercator**이며 위경도가 아니다.
지도에서 쓸 값은 `latitude`/`longitude` 생성 컬럼이다. 원본에서 DB가 계산하므로 직접 쓸 수 없고,
`coord_x/coord_y`가 갱신되면 자동으로 따라온다.

원본은 **좌표 미입력을 0으로 채워서 준다.** 이를 그대로 변환하면 위경도 `(0, 0)` — 기니만 앞바다 — 이 나오므로
`NULLIF(coord, 0)`으로 결측 처리했다. 즉 **위경도는 NULL일 수 있고**, 소비자는 이를 걸러야 한다. bbox 인덱스도 NULL을 제외한다.

---

## CLI 사용법

```bash
kidzly-sync <job> [--force] [--year-month YYYY-MM]
```

| 잡 | 설명 | 옵션 |
|----|------|------|
| `full` | 전체 어린이집 동기화 | `--force` |
| `delta` | 당월 신규/폐지 어린이집 증분 동기화 | `--force`, `--year-month YYYY-MM` (생략 시 당월) |
| `playground` | 놀이시설 전체 동기화 | `--force` |
| `sigungu-code` | 법정동코드 동기화 | `--force` |

`--force`를 주지 않으면 당일 이미 성공한 잡은 건너뛴다 (cron이 하루 여러 번 재시도하는 구조라서다). 성공 시 exit code `0`, 실패 시 `1`.

---

## 실행 방법

### 사전 요구사항

- Python 3.12+ (uv 권장)
- PostgreSQL 15+
- 공공데이터포털 어린이집 API 키 (4종), safemap.go.kr·odcloud.kr 서비스 키
- Telegram Bot Token & Chat ID
- AI provider 중 하나: Groq API 키 / Gemini API 키 / Ollama 로컬 서버 (`AI_PROVIDER`로 선택)

### 환경변수 설정

```bash
# 데이터베이스 (Spring 시절과 동일한 JDBC URL 형식을 그대로 받아 jdbc: 접두사만 걷어낸다)
DB_URL=jdbc:postgresql://localhost:5432/kidzly
DB_USERNAME=kidzly
DB_PASSWORD=your_password

# 공공데이터 API 키
KIZLE_KEY_SIGUNGU=your_sigungu_api_key    # cpmsapi020
KIZLE_KEY_DETAIL=your_detail_api_key      # cpmsapi030
KIZLE_KEY_NEW=your_new_api_key            # cpmsapi018
KIZLE_KEY_CLOSED=your_closed_api_key      # cpmsapi019
SAFEMAP_SERVICE_KEY=your_safemap_key
LEGAL_DONG_CODE_SERVICE_KEY=your_odcloud_key

# Telegram 알림
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# AI 요약 (AI_PROVIDER 값에 따라 필요한 키만 설정, 기본값 groq)
AI_PROVIDER=groq                      # groq | gemini | ollama
GROQ_API_KEY=your_groq_api_key        # provider=groq 시 필요
GEMINI_API_KEY=your_gemini_api_key    # provider=gemini 시 필요
# provider=ollama 시 별도 키 불필요 (로컬 서버 사용)
```

### 실행

```bash
# 설치
uv sync

# 실행
uv run kidzly-sync full
uv run kidzly-sync delta --year-month 2026-03
uv run kidzly-sync playground
uv run kidzly-sync sigungu-code --force

# 테스트
uv run pytest
uv run pytest -m integration   # Testcontainers 필요

# 마이그레이션
uv run --extra migrations alembic upgrade head
```

운영에서는 GitHub Actions가 각 잡을 스케줄에 따라 `uv run --frozen kidzly-sync <job>`으로 실행한다 (`.github/workflows/sync-*-python.yml`). 시크릿은 Infisical에서 OIDC로 주입한다.

---

## 설계 결정 & 트레이드오프

### ORM 없이 psycopg3 raw SQL
수만 건 단위 upsert가 핵심 작업이라 ORM의 `SELECT` 후 `INSERT/UPDATE` 패턴은 불필요한 조회를 배로 늘린다. `INSERT ... ON CONFLICT DO UPDATE` 네이티브 쿼리를 직접 작성해 단일 라운드트립으로 처리한다.

### 전체 동기화 / 증분 동기화 분리
매일 전국 수만 건을 전량 조회하면 API 키 소진과 외부 API 서버 부하를 유발한다. 주 1회 전체 동기화로 베이스라인을 유지하고, 매일 당월 신규·폐지 어린이집만 처리하는 증분 방식으로 API 호출 횟수를 대폭 줄였다.

### 자체 `Result`(`Ok`/`Err`) 타입
예외(Exception)로 에러를 표현하면 호출 경로 어딘가에서 처리가 누락될 수 있다. `Result[DomainError, A]`를 반환 타입으로 강제해 실패 경로를 명시적으로 다루게 한다. Arrow-kt 같은 외부 라이브러리 의존 없이 `kidzly_sync/domain/result.py`에 직접 구현했다.

### CLI one-shot 배치, REST 서버 없음
Kotlin 시절 REST 컨트롤러(`SyncController`, `AiSummaryController`)는 운영에서 기동되지 않았다 — 실제로는 GitHub Actions cron만 이 배치를 호출했다. 상주 서버를 유지할 이유가 없어 Python 포팅 시 CLI one-shot 실행만 남기고 REST 계층은 포팅하지 않았다.

### 스킵 가드 + cron 재시도
childcare.go.kr/safemap.go.kr이 간헐적으로 러너 IP를 차단해 실패하는 경우가 있다. 하루 한 번만 도는 대신 2시간 간격으로 여러 번 재시도하도록 스케줄을 짜고, 당일 이미 성공한 잡은 `SyncHistory`를 조회해 건너뛴다. 비교·재동기화가 필요할 땐 `--force`로 가드를 무시한다.
