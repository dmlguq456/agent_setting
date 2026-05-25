---
name: app-init
description: App project initial setup — environment check, stack selection, directory scaffolding, pipeline_state.yaml creation. First phase of autopilot-app (only on cold start).
argument-hint: "<app description>"
---

## Language Rule
- Korean output, English code identifiers.

## Pre-Check

Check if `.claude_reports/apps/<inferred-name>/` already exists:
- 존재 + `pipeline_state.yaml` 있음 → "이미 init 완료된 앱이 있습니다. 새로 시작하려면 폴더 삭제 후 재실행." 안내 후 중단
- 부재 → 계속

## Procedure

### Step 1: App name 결정
사용자 입력에서 추출 (예: "home-os 의 task 페이지 추가" → app name = `home-os`). 모호 시 한 줄 확인.

### Step 2: 환경 점검

`.claude_reports/apps/<name>/00_init/environment_check.md` 에 결과 작성:

```bash
node --version       # ≥ 20 권장
pnpm --version       # 또는 npm/yarn/bun
git --version
```

추가 도구 (사용자 스택에 따라 선택):
- Docker (containerized backend 면)
- PostgreSQL CLI 또는 sqlite3
- gh (GitHub CLI — deploy phase 에서 활용)

부재 시 사용자에 안내. **자동 설치 X** — "이 명령을 실행하면 됩니다, 진행할까요?" 형태.

### Step 3: 스택 선정

`stack_decision.md` 에 결정 기록.

기본 권장 (home-os 가 이 패턴 — 사용자 친숙):
```
Framework: Next.js 15 (App Router)
Styling:   Tailwind + shadcn/ui
DB:        Prisma + Turso (libSQL)
Auth:      next-auth 또는 lucia
Forms:     server actions + zod
Package:   pnpm
```

사용자가 다른 스택 원하면 그것 사용 (Expo, Remix, SvelteKit, Astro 등). 한 줄 확인.

### Step 4: 디렉토리 scaffolding

**신규 프로젝트**:
- 사용자 confirm 후 `npx create-next-app@latest <name>` 등 실행
- 또는 사용자가 직접 init 하도록 명령만 안내

**기존 프로젝트** (사용자가 _이미 있는_ 코드베이스에서 호출):
- 스택 검증만 (`package.json` 읽어서 일치하는지)
- scaffolding skip

### Step 5: CLAUDE.md (프로젝트 루트) 작성

프로젝트 루트에 `CLAUDE.md` 없으면 신규 작성. 있으면 _업데이트 권장_ 만 안내 (덮어쓰기 X).

```markdown
# <App Name>

## Stack
- Framework: ...
- DB: ...

## 주요 명령어
- 개발: `pnpm dev`
- 빌드: `pnpm build`
- 테스트: `pnpm test`

## 컨벤션
- (initial — 사용자가 채워 나감)
```

### Step 6: pipeline_state.yaml 생성

`.claude_reports/apps/<name>/pipeline_state.yaml`:

```yaml
app_name: <name>
created: <YYYY-MM-DD>
current_cycle: 1
stack:
  framework: <chosen>
  db: <chosen>
  ...
phases:
  init: done
  spec: pending
  design: pending
  build: pending
  qa: pending
  ship: pending
  iterate: pending
last_updated: <timestamp>
```

## Output

- `.claude_reports/apps/<name>/00_init/environment_check.md`
- `.claude_reports/apps/<name>/00_init/stack_decision.md`
- `.claude_reports/apps/<name>/pipeline_state.yaml`
- 프로젝트 루트의 `CLAUDE.md` (없을 시 신규 생성)

## Return Format

```
.claude_reports/apps/<name>/00_init/ -- ✅ init completed (stack: <framework>+<db>)
```

## Update agent memory

- 사용자가 자주 선택하는 스택 조합
- 환경 점검 시 자주 부재한 도구
- 사용자가 디폴트에서 자주 바꾸는 결정
