---
name: kidzly-feature
description: "kidzly-sync 새 기능 개발을 위한 에이전트 팀 오케스트레이터. 새 동기화 기능, API 엔드포인트, UseCase, AI 프로바이더 통합, Port 인터페이스 추가 등 코드 구현이 필요한 모든 작업에 반드시 이 스킬을 사용할 것. '구현해줘', '추가해줘', '만들어줘', '기능 개발', 'feature 추가' 요청 시 즉시 트리거. 후속 작업: 결과 수정, 다시 구현, 이전 결과 보완, 테스트만 다시, 특정 계층만 수정 요청 시에도 이 스킬을 사용."
---

# kidzly-feature Orchestrator

kidzly-sync의 새 기능 개발 워크플로우를 조율한다. architect → implementer → tester 파이프라인으로 Clean Architecture를 보장한 코드를 생성한다.

## 실행 모드: 에이전트 팀 (파이프라인 패턴)

## 에이전트 구성

| 팀원 | 에이전트 타입 | 역할 | 출력 |
|------|-------------|------|------|
| kidzly-architect | Plan | 아키텍처 설계, UseCase/Port 인터페이스 정의 | `_workspace/01_arch_design.md` |
| kidzly-implementer | general-purpose | Kotlin 코드 구현 (4계층) | `src/` 파일들, `_workspace/02_impl_notes.md` |
| kidzly-tester | general-purpose | Kotest 테스트 작성 + 코드 리뷰 | `src/test/` 파일들, `_workspace/03_test_review.md` |

## 워크플로우

### Phase 0: 컨텍스트 확인

`_workspace/` 디렉토리 존재 여부를 확인하여 실행 모드를 결정한다:

- **`_workspace/` 미존재** → 초기 실행. Phase 1로 진행
- **`_workspace/` 존재 + 사용자가 부분 수정 요청** → 부분 재실행. 해당 에이전트만 재호출하고 기존 산출물 중 수정 대상만 덮어쓴다
- **`_workspace/` 존재 + 새 기능 요청** → 새 실행. 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동한 후 Phase 1 진행

부분 재실행 예시:
- "테스트만 다시 작성해줘" → kidzly-tester만 재호출, `_workspace/02_impl_notes.md` 경로를 프롬프트에 포함
- "아키텍처 수정해줘" → kidzly-architect 재호출 후 implementer, tester 순서로 이어서 실행

### Phase 1: 준비

1. 사용자 요구사항을 분석하여 `_workspace/00_requirements.md` 작성:
   - 기능 요약 (한 줄)
   - 영향받는 계층 (domain / application / infrastructure / presentation)
   - 외부 의존 여부 (새 API, DB 스키마 변경, 새 설정 필요 여부)
   - 성공 기준 (검증 방법)
2. `_workspace/` 디렉토리 생성 (또는 새 실행의 경우 기존 이동 후 재생성)

### Phase 2: 팀 구성

```
TeamCreate(
  team_name: "kidzly-dev-team",
  members: [
    {
      name: "kidzly-architect",
      agent_type: "Plan",
      model: "opus",
      prompt: "당신은 kidzly-architect입니다. `.claude/agents/kidzly-architect.md`를 읽어 역할을 파악하세요. 요구사항: `_workspace/00_requirements.md` 읽기. 작업: 아키텍처 설계 후 `_workspace/01_arch_design.md` 저장. 완료 후 TaskUpdate로 '아키텍처 설계' 태스크를 completed로 변경하고, kidzly-implementer에게 SendMessage로 설계 완료를 알리세요."
    },
    {
      name: "kidzly-implementer",
      agent_type: "general-purpose",
      model: "opus",
      prompt: "당신은 kidzly-implementer입니다. `.claude/agents/kidzly-implementer.md`를 읽어 역할을 파악하세요. kidzly-architect의 SendMessage를 기다렸다가 `_workspace/01_arch_design.md`를 읽고 Kotlin 코드를 구현하세요. 완료 후 TaskUpdate로 '코드 구현' 태스크를 completed로 변경하고, kidzly-tester에게 SendMessage로 변경 파일 목록과 함께 구현 완료를 알리세요."
    },
    {
      name: "kidzly-tester",
      agent_type: "general-purpose",
      model: "opus",
      prompt: "당신은 kidzly-tester입니다. `.claude/agents/kidzly-tester.md`를 읽어 역할을 파악하세요. kidzly-implementer의 SendMessage를 기다렸다가 변경된 소스 파일과 `_workspace/02_impl_notes.md`를 읽고 Kotest 테스트를 작성하고 코드 리뷰를 수행하세요. 완료 후 TaskUpdate로 '테스트 및 리뷰' 태스크를 completed로 변경하고, 오케스트레이터(리더)에게 SendMessage로 이슈 건수와 함께 완료를 알리세요."
    }
  ]
)
```

```
TaskCreate(tasks: [
  {
    title: "아키텍처 설계",
    description: "_workspace/00_requirements.md 기반으로 도메인 모델, UseCase 시그니처, Port 인터페이스를 설계하고 _workspace/01_arch_design.md를 생성한다",
    assignee: "kidzly-architect"
  },
  {
    title: "코드 구현",
    description: "_workspace/01_arch_design.md 기반으로 4계층 Kotlin 코드를 작성한다",
    assignee: "kidzly-implementer",
    depends_on: ["아키텍처 설계"]
  },
  {
    title: "테스트 및 리뷰",
    description: "구현된 코드에 대해 Kotest 테스트를 작성하고 코드 리뷰를 수행한다",
    assignee: "kidzly-tester",
    depends_on: ["코드 구현"]
  }
])
```

### Phase 3: 파이프라인 실행

**실행 흐름**: architect 설계 → implementer 구현 → tester 테스트/리뷰

팀원들은 SendMessage로 순서대로 작업을 넘긴다. 리더는 진행 상황을 TaskGet으로 모니터링한다.

**팀원 간 통신 규칙:**
- kidzly-architect: 설계 완료 후 kidzly-implementer에게 SendMessage
- kidzly-implementer: 구현 완료 후 kidzly-tester에게 파일 목록 포함하여 SendMessage
- kidzly-tester: 완료 후 오케스트레이터(리더)에게 이슈 요약 SendMessage

**리더 개입 기준:**
- 팀원이 30분 이상 유휴 상태 → SendMessage로 상태 확인
- HIGH 이슈 에스컬레이션 수신 → 사용자에게 보고 후 지시 대기
- 설계 대안 선택 요청 → 사용자에게 확인 후 architect에게 결정 전달

### Phase 4: 결과 수집

kidzly-tester의 완료 보고 수신 후:

1. `_workspace/03_test_review.md` 읽기 — 이슈 목록 확인
2. 생성된 파일 목록 정리 (소스 파일 + 테스트 파일)
3. 사용자에게 최종 보고:
   ```
   ## 구현 완료
   **기능**: {기능명}
   
   **생성/수정 파일:**
   - src/main/kotlin/...
   - src/test/kotlin/...
   
   **리뷰 결과**: 이슈 {N}건 (HIGH: {X}, MEDIUM: {Y}, LOW: {Z})
   **주요 이슈**: (있는 경우)
   **Flyway 마이그레이션**: (필요한 경우 파일명)
   ```
4. HIGH 이슈가 있으면 수정 여부를 사용자에게 확인

### Phase 5: 정리

1. 팀원들에게 종료 SendMessage 발송
2. `TeamDelete(team_name: "kidzly-dev-team")`
3. `_workspace/` 보존 (삭제하지 않음 — 부분 재실행 및 감사 추적용)

## 데이터 흐름

```
사용자 요청
    ↓
_workspace/00_requirements.md
    ↓
kidzly-architect → _workspace/01_arch_design.md
    ↓ (SendMessage)
kidzly-implementer → src/main/kotlin/... + _workspace/02_impl_notes.md
    ↓ (SendMessage)
kidzly-tester → src/test/kotlin/... + _workspace/03_test_review.md
    ↓ (SendMessage)
오케스트레이터 → 최종 보고
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 팀원 1명 실패 | 리더가 감지 → SendMessage로 상태 확인 → 재시작 또는 대체 |
| HIGH 이슈 에스컬레이션 | 사용자에게 보고 후 계속/중단 선택 |
| 설계 대안 선택 요청 | 사용자에게 옵션 제시 후 architect에게 결정 전달 |
| 타임아웃 | 현재까지 완료된 Phase 산출물 보존, 미완료 팀원 종료 |
| 기존 코드 충돌 | implementer가 오케스트레이터에 보고 → 사용자 지시 대기 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "월별 어린이집 통계 집계 UseCase 추가해줘"
2. Phase 0: `_workspace/` 없음 → 초기 실행
3. Phase 1: `00_requirements.md` 생성 (application 계층 영향, DB 조회 추가)
4. Phase 2: 팀 3명 + 태스크 3개 생성
5. Phase 3: architect 설계(Port 불필요, Repository 메서드 추가) → implementer 구현 → tester 테스트 작성
6. Phase 4: "이슈 0건, 생성 파일 4개" 보고
7. Phase 5: 팀 정리

### 에러 흐름
1. Phase 3에서 architect가 "기존 엔티티 수정 vs 신규 엔티티 생성" 대안 에스컬레이션
2. 리더가 사용자에게 "기존 `Daycare` 엔티티에 컬럼 추가 vs 신규 `DaycareStats` 엔티티 생성" 선택 요청
3. 사용자가 "기존 엔티티 수정"으로 결정
4. 리더가 architect에게 결정 전달 → 파이프라인 재개
5. implementer 구현 중 HIGH 이슈(Either Left 미처리) 발견 → tester가 implementer에게 수정 요청
6. implementer 수정 후 재통보 → tester 재검토 후 최종 완료 보고
