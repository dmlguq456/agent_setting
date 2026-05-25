---
name: app-build
description: Implementation phase — reads PRD + design tokens, drafts an implementation plan, then dispatches to 개발팀 backend / frontend modes (parallel when independent).
argument-hint: "<app name or path>"
---

## Language Rule
- Korean output, English code identifiers.

## App Resolution

1. `$ARG` 가 폴더 경로면 그것 사용
2. fuzzy search `.claude_reports/apps/*$ARG*`
3. 단일 매치 → 사용. 다중 → "어느 앱?" 확인

## Pre-Check

- `01_spec/PRD.md` 존재 확인 → 부재 시 "먼저 `/app-spec` 실행 필요"
- `02_design/` 디렉토리 확인 → UI 가 있고 design phase skip 됐으면 사용자에 경고

## Procedure

### Step 1: PRD + Design Read

- `01_spec/PRD.md` Read — 피처·시나리오 파악
- `02_design/` 있으면 디자인 토큰·컴포넌트 spec Read

### Step 2: Implementation plan 작성

짧은 plan (5-15줄) 을 `03_build/plan.md` 에:

```markdown
# Build Plan for <feature>

## Backend
- API route `POST /api/tasks` — 새 task 생성
- Prisma schema 변경 — `Task` 모델 추가
- Server action `createTask` — zod 검증

## Frontend
- 페이지 `app/tasks/page.tsx` — list view
- 컴포넌트 `task-form.tsx` — 입력 폼
- 컴포넌트 `task-row.tsx` — 한 row

## API contract
- `Task = { id: string, title: string, ... }` — 공유 type
```

### Step 3: 사용자 confirm

plan 보여주고 "이대로 진행할까요?" 확인.

`--user-refine` 또는 plan 이 비교적 큰 경우 (10줄+) 에 명시. 작은 plan 은 skip 가능 (사용자 fast path 선호 시).

### Step 4: 병렬 실행 (의존성 없는 경우)

```
Agent(개발팀, mode=backend, "<backend spec from plan>")
Agent(개발팀, mode=frontend, "<frontend spec from plan>")
```

병렬 실행 — 둘이 _API contract_ 공유:
- backend 의 type 정의가 먼저 commit 되면 frontend 가 import 가능
- frontend 가 placeholder 로 시작 후 backend type 도착 시 swap

### Step 5: 순차 실행 (의존성 있는 경우)

backend 가 _DB schema 변경_ + type 새로 정의 → 먼저:

```
1. Agent(개발팀, mode=backend, "...")     # 완료 대기
2. Agent(개발팀, mode=frontend, "...")    # backend 결과 type 사용
```

### Step 6: Step log 작성

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

### Step 7: build_log.md 갱신

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

- `.claude_reports/apps/<name>/03_build/plan.md` — implementation plan
- `.claude_reports/apps/<name>/03_build/build_log.md` — phase 요약
- `.claude_reports/apps/<name>/03_build/_internal/step_logs/step_*.md`

## Return Format

```
.claude_reports/apps/<name>/03_build/ -- ✅ build completed (N steps, K files changed)
```

실패 시:
```
.claude_reports/apps/<name>/03_build/ -- ❌ build failed at step N: <reason>
```

## Update agent memory

- 자주 등장하는 API contract 패턴
- 백엔드 / 프론트엔드 병렬 vs 순차 판단 기준 누적
- 사용자 선호 (Prisma vs Drizzle, server action vs API route 등)
