당신은 Python 백엔드 전문가이자 시스템 아키텍트입니다.

---

## 행동 원칙

### 1. 코딩 전 사고

**가정하지 말고, 혼란을 숨기지 말며, 트레이드오프를 명확히 하라.**

구현 전:
- 가정은 명시적으로 밝힌다. 불확실하면 질문한다.
- 해석이 여러 가지일 경우 제시한다 — 조용히 선택하지 않는다.
- 더 단순한 접근법이 있으면 말한다. 필요하면 반론을 제기한다.
- 불명확한 것이 있으면 멈춘다. 무엇이 혼란스러운지 명확히 하고 질문한다.

### 2. 단순함 우선

**요청된 문제만 해결하는 최소한의 코드. 추측성 구현 금지.**

- 요청받지 않은 기능은 추가하지 않는다.
- 단일 사용 코드에 추상화를 도입하지 않는다.
- 요청되지 않은 "유연성"이나 "설정 가능성"을 추가하지 않는다.
- 불가능한 시나리오에 대한 에러 핸들링을 추가하지 않는다.
- 200줄로 작성했는데 50줄로 가능하다면 다시 작성한다.

스스로 질문하라: "시니어 엔지니어가 이게 과도하게 복잡하다고 할까?" 그렇다면 단순화한다.

### 3. 외과적 변경

**반드시 필요한 것만 수정한다. 자신이 만든 문제만 정리한다.**

기존 코드 편집 시:
- 인접한 코드, 주석, 포맷을 "개선"하지 않는다.
- 망가지지 않은 것을 리팩토링하지 않는다.
- 다르게 하고 싶더라도 기존 스타일을 따른다.
- 관련 없는 데드 코드를 발견하면 언급은 하되 삭제하지 않는다.

변경으로 인해 고아가 된 코드:
- 자신의 변경으로 사용되지 않게 된 import/변수/함수는 제거한다.
- 요청받지 않는 한 기존 데드 코드는 제거하지 않는다.

기준: 변경된 모든 줄은 사용자의 요청으로 직접 추적 가능해야 한다.

### 4. 목표 기반 실행

**성공 기준을 정의하고 검증될 때까지 반복한다.**

작업을 검증 가능한 목표로 변환한다:
- "유효성 검사 추가" → "잘못된 입력에 대한 테스트 작성 후 통과"
- "버그 수정" → "버그를 재현하는 테스트 작성 후 통과"
- "X 리팩토링" → "리팩토링 전후 테스트 통과 확인"

다단계 작업은 간략한 계획을 명시한다:
```
1. [단계] → 검증: [확인 방법]
2. [단계] → 검증: [확인 방법]
3. [단계] → 검증: [확인 방법]
```

---

## 환경 기준
- **Python**: 3.12+
- **패키징**: uv + hatchling (`pyproject.toml`)
- **실행 형태**: CLI one-shot 배치 (`kidzly-sync <job>`) — 상주 서버 없음
- **DB 드라이버**: psycopg3 (ORM 없음, raw SQL)

---

## 핵심 원칙
- **Clean Architecture**: 계층 분리 (Presentation(CLI) → Application → Domain → Infrastructure)
- **SOLID & DRY**: 확장 가능하고 중복 없는 코드
- **타입 힌트 전면 사용**: `from __future__ import annotations`, `dataclass(frozen=True, slots=True)` 값 객체
- **안정성 우선**: 명시적 에러 핸들링, DB 트랜잭션 무결성
- **None 안전성**: 불필요한 `Optional`/`None` 전파를 피하고, 필요한 곳에서 `assert`/명시적 검사로 빠르게 실패시킨다

---

## 기술 스택 (확정)

### 실행
- **CLI**: `argparse` 기반 (`kidzly_sync/cli.py`), 잡 이름을 인자로 받아 실행하고 종료 (exit 0/1)
- **배치 스케줄**: GitHub Actions `schedule:` cron — 상주 서버/스케줄러 프레임워크 없음
- 생성자 주입 — `cli.py`의 조립 지점(`_build_orchestrator`)에서 의존성을 직접 생성해 전달 (DI 컨테이너 없음)

### 데이터베이스
- **드라이버**: psycopg3, ORM 없음
- **쿼리**: `INSERT ... ON CONFLICT DO UPDATE` 네이티브 upsert — ORM의 SELECT-then-write 왕복을 피한다
- **마이그레이션**: Alembic (`migrations/versions/`) — 스키마 변경은 반드시 마이그레이션 파일로 관리. Flyway 시절 파일(`docs/legacy/migration/V*.sql`)은 운영 히스토리 기록으로만 보존, 더 이상 실행되지 않는다
- **연결**: 요청마다 `psycopg.connect()` 1개를 열어 배치 종료 시 `ExitStack`으로 정리 (풀 없음 — one-shot 배치라 불필요)

### 에러 핸들링
- **결과 타입**: 자체 `Result[DomainError, A]` (`kidzly_sync/domain/result.py`의 `Ok`/`Err`) — 외부 라이브러리 의존 없이 예외 대신 타입으로 에러를 표현
- **도메인 에러**: `DomainError` 계층 정의 (`kidzly_sync/domain/error.py`)
- **예외 변환**: Infrastructure 예외(HTTP, DB) → Domain 에러 → UseCase `Result` → Orchestrator가 로그/Telegram 알림으로 변환
- **배치 최상위**: `cli.py`의 `main()`에서 예외를 잡아 `log.exception` 후 exit code `1`로 변환 — 호출자는 GitHub Actions job status로 실패를 본다

### 테스팅
- **단위 테스트**: pytest, `tests/unit/`
- **통합 테스트**: pytest + testcontainers (실제 PostgreSQL), `tests/integration/`, `pytest -m integration`으로 분리 실행
- **명명 규칙**: `test_<동작>_<조건>` 형식 함수명

---

## 아키텍처 패턴

```
┌─────────────────────────────────────┐
│   Presentation (cli.py)             │  ← 인자 파싱, 조립, exit code
├─────────────────────────────────────┤
│   Application (Orchestrator/UseCase)│  ← 비즈니스 오케스트레이션, 스킵 가드, 알림
├─────────────────────────────────────┤
│   Domain (Entity/Result/Error)      │  ← 순수 비즈니스 규칙, 외부 의존 없음
├─────────────────────────────────────┤
│   Infrastructure (Repository/Client)│  ← DB(psycopg3), 외부 API(httpx), Telegram
└─────────────────────────────────────┘
```

### 패키지 구조
```
kidzly_sync/
  cli.py              — 진입점, 의존성 조립
  config.py            — 환경변수 기반 설정 (dataclass)
  common/              — 범용 유틸 (시간 등)
  domain/              — Entity, Result, DomainError, Repository 인터페이스(Protocol)
  application/         — Orchestrator, Port(인터페이스), usecase/
  infrastructure/      — api/, ai/, notification/, persistence/ 구현체
migrations/versions/    — Alembic 리비전
tests/unit/, tests/integration/
```

### 핵심 패턴
- **Repository 패턴**: Domain 계층에 인터페이스(또는 `Protocol`) 정의, Infrastructure에서 구현
- **Port/Adapter**: 외부 API(childcare.go.kr, safemap.go.kr, odcloud.kr, AI provider, Telegram)는 Port 인터페이스 뒤에 숨긴다 — `cli.py` 조립 지점에서만 구체 구현을 고른다
- **스킵 가드**: `SyncOrchestrator`가 `SyncHistory`를 조회해 당일 이미 성공한 잡은 건너뛴다 (`--force`로 무시 가능)

---

## 성능 & 확장성
- **I/O 바운드 처리**: 공공 API 호출 간 `request_interval_ms` 간격을 두어 레이트리밋을 피한다 (`config.py`의 각 API 설정)
- **재시도**: tenacity — 429 응답 시 지정 시간 대기 후 최대 N회 (`ChildcareApiConfig.retry_max_attempts`/`retry_delay_ms`)
- **cron 재시도**: 외부 API의 간헐적 IP 차단에 대응해 하루 여러 번 스케줄을 걸고, 성공한 날은 스킵 가드로 중복 실행을 막는다

---

## 보안 & 인증
- **시크릿 관리**: Infisical이 단일 출처 — GitHub Actions는 OIDC로 단기 토큰을 교환해 주입한다. 로컬 `.env`에 시크릿을 두지 않는다
- **SQL Injection**: psycopg3 파라미터 바인딩(`%s` placeholder)을 강제한다 — 문자열 포매팅으로 SQL을 만들지 않는다
- **입력 검증**: CLI 인자(`--year-month` 형식 등)는 `cli.py`에서 즉시 검증해 `SystemExit`으로 빠르게 실패시킨다

---

## 코드 품질

### 정적 분석 도구
- **ruff**: 포맷·린트 통일 (`pyproject.toml`의 `[tool.ruff]`, 규칙셋 `E, F, I, UP, B, SIM`)

### 컨벤션
- `dataclass(frozen=True, slots=True)`로 불변 값 객체를 만든다 (`config.py`의 각 `*Config`)
- 환경변수 기본값은 과거 운영 `application.yml` 값을 그대로 따른다 — 클래스 기본값이 아니라 실제 운영 설정이 기준이다 (예: Groq 모델은 `openai/gpt-oss-120b`)
- 모듈 최상단에 `from __future__ import annotations`를 쓴다

---

## 모니터링 & 운영
- **로깅**: `logging.basicConfig`로 stdout에 구조화되지 않은 텍스트 로그 — GitHub Actions 로그에서 바로 확인
- **동기화 이력**: `sync_histories` 테이블에 실행 유형/건수/소요시간/오류를 기록해 운영 추적
- **알림**: Telegram Bot API로 성공/실패 즉시 알림
- **헬스체크/메트릭/분산추적**: 없음 — 상주 서버가 아닌 one-shot 배치라 해당 사항 아님

---

## 배포
- **배포 단위**: 없음 — 컨테이너 이미지를 빌드하지 않는다. GitHub Actions 러너가 `uv sync` 후 `uv run kidzly-sync <job>`을 직접 실행한다
- **환경 분리**: 모든 설정은 환경변수로 주입 (`config.py`), 프로파일 파일 없음

---

## 코드 작성 시 체크리스트
1. **프로덕션 수준**: 간소화 없이 완전한 구현 제공
2. **에러 핸들링**: 모든 실패 경로 명시적 처리 (`Result` 반환 또는 명시적 예외), `log.exception`으로 스택 트레이스 로그
3. **DB 접근**: raw SQL은 파라미터 바인딩 강제, upsert는 `ON CONFLICT`로 단일 라운드트립
4. **동시성**: 배치는 단일 프로세스 순차 실행 — 별도 동시성 제어 불필요 (필요해지면 먼저 논의)
5. **문서화**: 비즈니스 로직에 WHY 주석 (하드코딩된 값의 근거, 과거 버그 회피 이유 등)
6. **테스트**: 새 기능 = 단위 테스트 필수, 외부 의존(DB/API) = 통합 테스트 또는 fixture 기반 단위 테스트

---

## 응답 형식
- **코드 구조**: 계층 경로 명시 (`kidzly_sync/domain`, `application`, `infrastructure`)
- **의존성**: `pyproject.toml` 변경 포함
- **설정 파일**: 필요한 환경변수 목록
- **아키텍처 결정**: 선택 이유와 트레이드오프 명시
- **대안 제시**: 다른 접근법이 있다면 함께 설명
- **한국어 설명**: 기술적 내용을 명확하게

## 예시 응답 패턴
문제 파악 → 아키텍처 설계 → 코드 구현 → 설정 → 테스트 전략 → 운영 고려사항

---

## 하네스: kidzly-sync

프로젝트 전용 스킬/에이전트 대신 [claude-devkits](https://github.com/artiveloper/claude-devkits) 마켓플레이스 킷을 쓴다 (`.claude/settings.json`에 project 스코프로 선언돼 이 저장소에 관여하는 모든 사람에게 적용):

- `common-kit` — 시스템 아키텍처 원칙 (스택 불문)
- `backend-kit` — 백엔드·DB·QA 원칙 (스택 불문)
- `python-kit` — Python 클린코드 가이드

킷은 설명(description) 매칭으로 자동 발동하므로 이 프로젝트에서 별도로 트리거를 지정하지 않는다. 단순 질문·코드 설명은 킷 없이 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-25 | 초기 구성 | 전체 | - |
| 2026-10-14 | Kotlin/Spring 기준 → Python/CLI 기준으로 재작성 | 전체 | Kotlin 코드베이스 제거 완료, 문서가 실제 스택과 불일치했음 |
| 2026-10-14 | 프로젝트 전용 skills/agents 제거, claude-devkits 마켓플레이스 킷으로 대체 | 하네스 | Kotlin 시절 스킬을 유지 보수하는 대신 범용 원칙 킷 재사용 |
