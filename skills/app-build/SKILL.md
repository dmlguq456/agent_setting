---
name: app-build
description: "[DEPRECATED — autopilot-code 의 _앱 mode_ 가 본 역할 대체. 신규 호출 X. 이미 진행 중인 작업 자리에서만 참고]. 과거: Implementation phase — PRD + design tokens 읽고 implementation plan 작성 후 개발팀 backend/frontend mode 병렬 호출. 현재: 동일 작업이 `/autopilot-code` 호출 시 _앱 컨텍스트 자동 감지_ (specs/<name>/ 발견) 로 처리됨."
argument-hint: "<app name or path>  # DEPRECATED — /autopilot-code 사용"
---

> **DEPRECATED (2026-05-25)** — 본 sub-skill 의 _구현 자리_ 는 **autopilot-code 의 앱 mode** 가 대체. 사용자는 `/autopilot-code "기능 추가"` 자연어 발화로 호출, autopilot-code 가 `specs/<name>/` 컨텍스트 발견 시 자동 활성화. 본 파일은 _레거시 참조_ 용 — 새 호출 X.

## Language Rule
- Korean output, English code identifiers.

## App Resolution

1. `$ARG` 가 폴더 경로면 그것 사용
2. fuzzy search `.claude_reports/specs/*$ARG*`
3. 단일 매치 → 사용. 다중 → "어느 앱?" 확인

## Pre-Check

- `01_spec/PRD.md` 존재 확인 → 부재 시 "먼저 `/app-spec` 실행 필요"
- `02_design/` 디렉토리 확인 → UI 가 있고 design phase skip 됐으면 사용자에 경고

## Procedure

### Step 1: PRD + Design Read

- `01_spec/PRD.md` Read — 피처·시나리오 파악 + **API Contract 섹션** (spec 단계의 단일 source of truth) + **데이터 모델 초안 + migration plan** (있으면)
- `02_design/` 있으면 디자인 토큰·컴포넌트 spec Read

> spec 안 API Contract 가 _build phase 의 입력_. build 안에서 contract 임의 변경 X — 변경 필요 시 spec 으로 back-jump (autopilot-spec `--from spec`).

### Step 2: Implementation plan 작성

짧은 plan (5-15줄) 을 `03_build/plan.md` 에 — spec 의 API Contract 를 그대로 인용 + 구현 매핑:

```markdown
# Build Plan for <feature>

## API Contract (from 01_spec/PRD.md §API Contract)
- `Task = { id, userId, title, completed, createdAt, updatedAt }`
- `POST /api/tasks` / `GET /api/tasks` / `PATCH /api/tasks/:id` / `DELETE /api/tasks/:id`

## Backend
- `prisma/schema.prisma` — Task 모델 추가 (spec 의 데이터 모델 초안 그대로)
- API routes 또는 Server actions — contract 따라 구현
- zod 검증 — contract 의 body shape 그대로

## Frontend
- 페이지 `app/tasks/page.tsx` — list view (GET /api/tasks)
- 컴포넌트 `task-form.tsx` — 입력 폼 (POST /api/tasks)
- 컴포넌트 `task-row.tsx` — 한 row (PATCH / DELETE)

## DB Migration (cycle 2+ 또는 destructive 변경 시)
- 변경 종류: <add column / drop column / type change / index>
- 영향: production 운영 중 row 처리 방법 (backfill / nullable / drop)
- 명령: `pnpm prisma migrate dev --name <slug>` (dev), `pnpm prisma migrate deploy` (prod)
- _자동 실행 X_ — 사용자 confirm 후 실행
```

### Step 3: 사용자 confirm

plan 보여주고 "이대로 진행할까요?" 확인.

`--user-refine` 또는 plan 이 비교적 큰 경우 (10줄+) 에 명시. 작은 plan 은 skip 가능 (사용자 fast path 선호 시).

### Step 4: DB Migration (schema 변경 있을 시 — Step 5 _전_)

`prisma/schema.prisma` 등 schema 파일 변경 감지 시 _backend 구현 전에_ migration 단계 분리:

```bash
# 1. schema diff 보여줌 (사용자 검토 자리)
git diff prisma/schema.prisma

# 2. migration 명령 안내 (자동 실행 X)
#    dev: 새 migration 파일 생성 + DB 적용
$ pnpm prisma migrate dev --name <slug>

#    prod (cycle 2+ 운영 중): destructive 변경이면 한 번 더 확인
$ pnpm prisma migrate deploy
```

**destructive 변경 (column drop / type change / NOT NULL 추가) 시**:
- 사용자에 _migration plan_ 보여줌 (spec 에서 결정한 backfill / nullable 처리)
- 자동 실행 절대 X — 사용자가 명령 직접 실행
- migration 파일 생성 후 step log 에 _backfill SQL_ 또는 _수동 데이터 정리 명령_ 안내

### Step 5: 병렬 실행 (contract 안정 + schema migration 완료 시)

```
Agent(개발팀, mode=backend, "<backend spec from plan + API contract>")
Agent(개발팀, mode=frontend, "<frontend spec from plan + API contract>")
```

병렬 실행 — 둘이 spec 의 _API Contract_ 를 입력으로 공유:
- backend 가 contract 의 type / endpoint 구현
- frontend 가 같은 contract 의 type import 후 호출

### Step 6: 순차 실행 (contract 변경 또는 type 새로 정의 시)

backend 가 _새 type 정의 + contract 확장_ 필요한 자리:

```
1. Agent(개발팀, mode=backend, "...")     # contract 의 shared type 먼저 commit
2. Agent(개발팀, mode=frontend, "...")    # backend type import
```

contract _변경_ 자체가 필요한 자리 — 본 build phase 진행 _안 함_. spec 으로 back-jump.

### Step 7: Step log 작성

`03_build/_internal/step_logs/step_{NN}_{name}.md` 에 각 단계 상세:

```markdown
## step_01_backend_task_api
**모드**: backend (개발팀)
**시간**: <timestamp>

### 변경 사항
- `prisma/schema.prisma` — Task 모델 추가
- `app/actions.ts` — createTask server action 추가
- ...

### 검증
- `pnpm tsc --noEmit` 통과
- 로컬 테스트: ...
```

### Step 8: build_log.md 갱신

`03_build/build_log.md` 에 phase 요약:

```markdown
# Build Log

## Steps
- step_01: backend task API ✅
- step_02: frontend task page ✅
- ...

## API contract
- `Task`: { id, title, completed, createdAt }

## 다음 단계
- QA phase
```

## Pipeline state 업데이트

`pipeline_state.yaml` 의 `phases.build` 을 `done` 으로.

## Output

- `.claude_reports/specs/<name>/03_build/plan.md` — implementation plan
- `.claude_reports/specs/<name>/03_build/build_log.md` — phase 요약
- `.claude_reports/specs/<name>/03_build/_internal/step_logs/step_*.md`

## Return Format

```
.claude_reports/specs/<name>/03_build/ -- ✅ build completed (N steps, K files changed)
```

실패 시:
```
.claude_reports/specs/<name>/03_build/ -- ❌ build failed at step N: <reason>
```

## Update agent memory

- 자주 등장하는 API contract 패턴
- 백엔드 / 프론트엔드 병렬 vs 순차 판단 기준 누적
- 사용자 선호 (Prisma vs Drizzle, server action vs API route 등)
