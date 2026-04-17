# kidzly-sync

[![Kotlin](https://img.shields.io/badge/Kotlin-2.x-7F52FF?logo=kotlin)](https://kotlinlang.org)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.4-6DB33F?logo=springboot)](https://spring.io/projects/spring-boot)
[![JVM](https://img.shields.io/badge/JVM-21-007396?logo=openjdk)](https://openjdk.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql)](https://www.postgresql.org)

공공데이터포털 어린이집 API에서 데이터를 수집하여 PostgreSQL에 동기화하는 배치 서비스입니다.

---

## 배경 & 목적

공공데이터포털(childcare.go.kr)이 제공하는 어린이집 정보 API는 XML 형식으로 응답하며, 전국 시군구 단위로 개별 호출이 필요합니다. 단순 조회 서비스가 매번 외부 API를 직접 호출하면 응답 지연과 API 키 소진 문제가 발생하기 때문에, 별도 동기화 서비스를 두어 최신 데이터를 자체 DB에 유지하는 방식을 채택했습니다.

- **전체 동기화**: 주 1회 전국 17개 시도 × 전체 시군구를 순회하며 전량 upsert
- **증분 동기화**: 매일 당월 신규 개원 및 폐지 어린이집만 처리하여 API 호출 최소화
- **동기화 이력 추적**: 실행 결과(처리 건수, 소요 시간, 오류)를 DB에 기록
- **Telegram 알림**: 동기화 완료/실패 시 즉시 알림 발송

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 전체 동기화 (Full Sync) | 전국 어린이집 데이터를 시군구별로 순회하며 전량 upsert |
| 증분 동기화 (Delta Sync) | 월별 신규 개원/폐지 어린이집만 처리 |
| 시군구 동기화 | 행정구역 마스터 데이터 최신화 |
| 수동 트리거 API | REST API를 통한 즉시 동기화 실행 |
| 자동 스케줄링 | 매주 일요일 03:00 전체 / 매일 02:00 증분 |
| 동기화 이력 관리 | 실행 유형, 처리 건수, 소요 시간, 오류 메시지 기록 |
| Telegram 알림 | 동기화 성공/실패 결과를 Telegram Bot으로 즉시 알림 |

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────┐
│   Presentation (SyncController, SyncScheduler)   │  REST API, Cron 트리거
├──────────────────────────────────────────────────┤
│   Application (SyncOrchestrator, UseCase)        │  동기화 오케스트레이션, 트랜잭션
├──────────────────────────────────────────────────┤
│   Domain (Daycare, SyncHistory, DomainError)     │  순수 비즈니스 규칙, 도메인 모델
├──────────────────────────────────────────────────┤
│   Infrastructure (ApiClient, Repository)         │  공공데이터 API 호출, JPA 구현체
└──────────────────────────────────────────────────┘
```

**데이터 흐름**

```
[Scheduler / REST API]
        │
   SyncOrchestrator  ─────────────────────────────┐
        │                                         │
  FullSyncUseCase / DeltaSyncUseCase        TelegramNotifier
        │                                   (성공/실패 알림)
  ChildcareApiPort
        │
  childcare.go.kr (XML API)
        │
  DaycareRepository
        │
  PostgreSQL (daycares, sigungu, sync_histories)
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 언어 | Kotlin 2.x (K2 컴파일러) |
| 프레임워크 | Spring Boot 3.4, Spring MVC |
| 동시성 | JVM 21 Virtual Threads (Project Loom) |
| 데이터베이스 | PostgreSQL 15+ |
| ORM / 마이그레이션 | JPA / Hibernate, Flyway |
| 에러 처리 | Arrow-kt `Either<DomainError, A>` |
| XML 파싱 | Jackson Dataformat XML |
| 재시도 | Spring Retry (429 응답 시 1분 대기 후 최대 3회) |
| 알림 | Telegram Bot API |
| 테스트 | Kotest, MockK |
| 빌드 | Gradle 8.x (Kotlin DSL) |

---

## API 명세

모든 엔드포인트는 `POST` 메서드를 사용합니다.

| 엔드포인트 | 파라미터 | 설명 |
|------------|----------|------|
| `POST /api/v1/sync/full` | — | 전체 동기화 (백그라운드 실행) |
| `POST /api/v1/sync/delta` | `yearMonth` (선택, 예: `2026-03`) | 증분 동기화 (기본: 당월) |
| `POST /api/v1/sync/sigungu` | `sidoname` (선택, 예: `서울특별시`) | 시군구 동기화 (생략 시 전체) |
| `POST /api/v1/sync/daycare-detail` | `arcode` (필수, 예: `11010`) | 특정 시군구 어린이집 상세 동기화 |
| `POST /api/v1/sync/new-daycare` | `yearMonth` (선택) | 월별 신규 어린이집 동기화 |
| `POST /api/v1/sync/closed-daycare` | `yearMonth` (선택) | 월별 폐지 어린이집 처리 |

**응답 형식**

```json
{
  "success": true,
  "data": "전체 동기화가 백그라운드에서 시작되었습니다.",
  "error": null
}
```

---

## 실행 방법

### 사전 요구사항

- JDK 21+
- PostgreSQL 15+
- 공공데이터포털 어린이집 API 키 (4종)
- Telegram Bot Token & Chat ID

### 환경변수 설정

```bash
# 데이터베이스
DB_URL=jdbc:postgresql://localhost:5432/kidzly
DB_USERNAME=kidzly
DB_PASSWORD=your_password

# 공공데이터 API 키
KIZLE_KEY_SIGUNGU=your_sigungu_api_key    # cpmsapi020
KIZLE_KEY_DETAIL=your_detail_api_key      # cpmsapi030
KIZLE_KEY_NEW=your_new_api_key            # cpmsapi018
KIZLE_KEY_CLOSED=your_closed_api_key      # cpmsapi019

# Telegram 알림
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 실행

```bash
# 빌드
./gradlew build

# 실행
./gradlew bootRun

# 테스트
./gradlew test
```

---

## 설계 결정 & 트레이드오프

### Virtual Threads 선택
공공 API 호출은 전형적인 I/O 바운드 작업입니다. 전국 시군구 수백 개를 순회하는 동안 대부분의 시간이 네트워크 대기에 소비됩니다. JVM 21의 Virtual Threads를 활용하면 플랫폼 스레드를 블로킹하지 않아 전체 처리량을 높일 수 있습니다. 수동 트리거 API에서도 `Thread.ofVirtual().start { }` 로 즉시 응답을 반환하면서 동기화를 백그라운드에서 실행합니다.

### Arrow-kt `Either` 도입
예외(Exception)로 에러를 표현하면 호출 경로 어딘가에서 처리가 누락될 수 있습니다. `Either<DomainError, A>`를 반환 타입으로 강제하면 컴파일 타임에 실패 경로 처리를 강제할 수 있습니다. `ApiCallError`, `ParseError`, `NetworkError` 등 도메인 에러를 sealed class로 명시하여 어떤 에러가 발생 가능한지 코드에서 직접 확인할 수 있습니다.

### 전체 동기화 / 증분 동기화 분리
매일 전국 수만 건을 전량 조회하면 API 키 소진과 외부 API 서버 부하를 유발합니다. 주 1회 전체 동기화로 베이스라인을 유지하고, 매일 당월 신규·폐지 어린이집만 처리하는 증분 방식으로 API 호출 횟수를 대폭 줄였습니다.

### Native Upsert (`INSERT ... ON CONFLICT DO UPDATE`)
JPA의 `save()`는 ID 존재 여부 확인을 위해 `SELECT` 후 `INSERT/UPDATE`를 수행합니다. 수만 건을 처리할 때 이 방식은 SELECT 쿼리가 배로 발생합니다. 네이티브 쿼리로 단일 `INSERT ... ON CONFLICT DO UPDATE`를 실행하여 불필요한 조회를 제거하고, `hibernate.jdbc.batch_size=500` 설정으로 배치 단위 처리합니다.