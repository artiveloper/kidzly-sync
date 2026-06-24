---
name: kidzly-migration
description: "kidzly-sync Flyway DB 마이그레이션 파일 작성 전문 스킬. 테이블 생성, 컬럼 추가/변경/삭제, 인덱스 추가, 컬럼 타입 변경, 코멘트 추가 등 스키마 변경 작업 시 반드시 이 스킬을 사용할 것. '컬럼 추가', '테이블 만들어줘', '스키마 변경', '마이그레이션 작성', 'Flyway', 'DDL' 언급 시 즉시 트리거. JPA 엔티티 수정이 필요한 경우도 함께 처리."
---

# kidzly-migration Skill

kidzly-sync 프로젝트의 Flyway 마이그레이션 파일을 작성한다. 기존 마이그레이션 버전을 확인하고 올바른 번호의 SQL 파일을 생성한다.

## 실행 절차

### Step 1: 현재 버전 확인

`src/main/resources/db/migration/` 디렉토리를 읽어 가장 높은 버전 번호를 확인한다.

현재 파일 패턴: `V{N}__{description}.sql`
현재 최고 버전: V12 (`V12__add_ai_analysis_column.sql`)

신규 파일: `V{현재최고+1}__{snake_case_description}.sql`

### Step 2: 스키마 변경 내용 파악

사용자 요청에서 다음을 파악한다:
- 대상 테이블 (`daycares`, `sync_histories`, `sigungus`, 신규 테이블)
- 변경 유형 (CREATE TABLE, ADD COLUMN, ALTER COLUMN, ADD INDEX, ADD COMMENT 등)
- 데이터 타입 및 제약 조건 (NOT NULL, DEFAULT, UNIQUE 등)
- 기존 데이터 영향 (운영 중 무중단 적용 가능 여부)

### Step 3: SQL 작성 원칙

**안전한 변경 (무중단 적용 가능):**
- `ALTER TABLE ... ADD COLUMN` — DEFAULT 값 포함 권장
- `CREATE INDEX CONCURRENTLY` — 잠금 없이 인덱스 생성
- `ADD COMMENT ON ...`

**주의가 필요한 변경:**
- `ALTER TABLE ... ALTER COLUMN TYPE` — 기존 데이터 타입 호환성 확인
- `ALTER TABLE ... ADD COLUMN ... NOT NULL` — 기존 행에 DEFAULT 값 필수
- `DROP COLUMN` — 먼저 JPA 엔티티에서 제거 후 마이그레이션 실행

**금지:**
- `DROP TABLE` (사용자가 명시적으로 요청하더라도 한 번 더 확인)
- 데이터 손실이 발생하는 변경을 경고 없이 실행

### Step 4: SQL 파일 생성

```sql
-- V{N}__{description}.sql
-- 작성 일시: {YYYY-MM-DD}
-- 변경 내용: {한 줄 요약}

{DDL 구문}
```

PostgreSQL 문법을 사용한다 (프로젝트 DB: PostgreSQL 15+).

### Step 5: JPA 엔티티 수정 (필요 시)

스키마 변경이 JPA 엔티티와 연관된 경우:
- `src/main/kotlin/kr/kidzly/sync/domain/entity/` 경로의 해당 엔티티 파일 수정
- 기존 엔티티 참조: `Daycare.kt`, `Sigungu.kt`, `SyncHistory.kt`
- 컬럼 추가 시: `@Column` 어노테이션 및 필드 추가
- Nullable 여부: DB NOT NULL → `val field: Type`, Nullable → `val field: Type?`

## 자주 사용하는 패턴

### 컬럼 추가
```sql
ALTER TABLE daycares ADD COLUMN IF NOT EXISTS {column_name} {type} DEFAULT {default_val};
COMMENT ON COLUMN daycares.{column_name} IS '{설명}';
```

### 인덱스 추가
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table}_{columns} ON {table}({columns});
```

### 신규 테이블
```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    id BIGSERIAL PRIMARY KEY,
    -- 필드들
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE {table_name} IS '{테이블 설명}';
```

## 완료 후 체크

- [ ] 파일명 버전 번호가 현재 최고 버전 + 1인지
- [ ] `IF NOT EXISTS` / `IF EXISTS` 안전 구문 사용했는지
- [ ] NOT NULL 컬럼에 DEFAULT 값 또는 기존 데이터 업데이트 구문이 있는지
- [ ] JPA 엔티티 수정이 필요한 경우 함께 처리했는지
- [ ] PostgreSQL 문법인지 (MySQL 문법 혼용 주의)
