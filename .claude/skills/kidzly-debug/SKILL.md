---
name: kidzly-debug
description: "kidzly-sync 동기화 문제 디버깅 전문 스킬. API 호출 실패, XML 파싱 에러, DB 저장 오류, Telegram 알림 미발송, AI 요약 실패, 스케줄 미실행, Either Left 에러, ClosedChannelException 등 런타임 오류 디버깅 시 반드시 이 스킬을 사용할 것. '오류', '에러', '실패', '안 됨', '동작 안 함', '버그', '왜', '디버깅', '원인 분석' 언급 시 즉시 트리거."
---

# kidzly-debug Skill

kidzly-sync 런타임 오류와 동기화 문제를 진단하고 근본 원인을 찾는다.

## 데이터 흐름 맵

문제 위치를 특정하려면 먼저 어느 계층에서 발생했는지 파악한다:

```
[SyncJobRunner / REST API 트리거]
    ↓
[SyncOrchestrator] — 전체 동기화 오케스트레이션
    ↓
[FullSyncUseCase / DeltaSyncUseCase] — 비즈니스 로직
    ↓
[ChildcareApiPort → ChildcareApiClient] — 공공 API 호출 (XML)
    ↓
[DaycareRepository → DaycareRepositoryImpl] — Upsert, 배치 저장
    ↓
[PostgreSQL] — daycares, sigungu, sync_histories 테이블
    ↓
[TelegramNotifier] — 완료/실패 알림 발송
```

```
[AiSummaryController / REST API]
    ↓
[DaycareAISummaryUseCase / AllDaycaresAISummaryUseCase / SidoAISummaryUseCase]
    ↓
[AiSummaryPort → GroqApiClient / GeminiApiClient / OllamaApiClient]
```

## 오류 유형별 진단

### 1. 공공 API 호출 실패

**증상**: `ApiCallError`, HTTP 429, 연결 시간 초과, `ClosedChannelException`

**확인 경로**:
- `ChildcareApiClient.kt` — `@Retryable` 설정 확인 (429 → 1분 대기, 최대 3회)
- `application.yml` 또는 환경변수 — API 키 4종 (`KIZLE_KEY_*`) 유효성
- `infrastructure/config/ChildcareApiProperties.kt` — baseUrl, timeout 설정

**주요 원인**:
- API 키 만료 또는 일일 호출 한도 초과
- JDK HttpClient `ClosedChannelException` — 커넥션 풀 재사용 시 발생 (Keep-Alive 만료)
- 시군구 코드 오류 (`arcode` 파라미터 값)

### 2. XML 파싱 실패

**증상**: `ParseError`, `JacksonException`, `MismatchedInputException`

**확인 경로**:
- `infrastructure/api/dto/KizleXmlResponses.kt` — XML 필드 매핑 클래스
- `infrastructure/config/InfrastructureConfig.kt` — `XmlMapper` Bean 설정

**주요 원인**:
- 공공 API 응답 스키마 변경 (필드 추가/삭제)
- 빈 응답 (`resultCode != 00`) 처리 누락

### 3. DB 저장 실패

**증상**: `DataIntegrityViolationException`, Constraint 위반, Flyway 오류

**확인 경로**:
- `DaycareRepositoryImpl.kt` — 네이티브 Upsert 쿼리 (`INSERT ... ON CONFLICT DO UPDATE`)
- `src/main/resources/db/migration/` — 마이그레이션 파일 순서/내용
- 테이블 스키마 (`schema.sql`) vs 엔티티 필드 불일치

**주요 원인**:
- NOT NULL 컬럼에 null 값 전달
- 마이그레이션 파일 버전 충돌 또는 누락
- 배치 처리 중 단일 레코드 오류로 전체 배치 롤백

### 4. AI 요약 실패

**증상**: AI 프로바이더 API 에러, 타임아웃, 빈 응답

**확인 경로**:
- `application.yml` — `ai.provider` 값 (`groq` / `gemini` / `ollama`)
- 해당 프로바이더 API 키 환경변수 (`GROQ_API_KEY`, `GEMINI_API_KEY`)
- `infrastructure/ai/AbstractAiApiClient.kt` — 공통 요청/응답 처리
- `src/main/resources/prompts/daycare-ai-summary.txt` — 프롬프트 내용

**주요 원인**:
- 프로바이더 API 키 미설정 또는 만료
- Ollama 로컬 서버 미실행 (`ollama serve`)
- 프롬프트가 너무 길어 토큰 한도 초과

### 5. Telegram 알림 미발송

**증상**: 동기화 완료되었으나 알림 없음

**확인 경로**:
- `infrastructure/notification/TelegramNotifier.kt`
- 환경변수: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Telegram Bot API 응답 코드

**주요 원인**:
- 환경변수 미설정
- Bot이 채팅에 추가되지 않음 (Chat ID 오류)

### 6. 스케줄 미실행

**증상**: GitHub Actions 배치가 예상 시간에 실행되지 않음

**확인 경로**:
- `presentation/SyncJobRunner.kt` — `SYNC_JOB` 환경변수 분기 로직
- GitHub Actions 워크플로우 파일 (`.github/workflows/`)
- `application-prod.yml` — 스케줄 설정

**주요 원인**:
- `SYNC_JOB` 환경변수 미설정 또는 오타 (`FULL` / `DELTA`)
- GitHub Actions secrets 미설정

## 진단 절차

1. **증상 파악**: 오류 메시지, 발생 계층, 재현 조건 확인
2. **로그 분석**: 스택 트레이스에서 첫 번째 kidzly 패키지 호출 지점 찾기
3. **코드 추적**: 데이터 흐름 맵에서 해당 계층 파일 읽기
4. **근본 원인 식별**: 위 오류 유형 매핑으로 원인 후보 좁히기
5. **수정 제안**: 최소 변경 원칙 (주변 코드 "개선" 금지)
6. **검증 방법 제시**: 수정 후 확인 방법 명시

## 응답 형식

```
## 진단 결과
**발생 계층**: {계층명}
**근본 원인**: {구체적 설명}
**관련 파일**: {파일명:라인}

## 수정 방법
{구체적인 코드 변경 또는 설정 변경}

## 검증 방법
{수정 후 확인 방법}
```
