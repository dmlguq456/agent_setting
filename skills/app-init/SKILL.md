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

cold start 자리라 _작은 컨펌 5 자리 분산_ 대신 _2 컨펌 묶음_ 으로 운영. 사용자 인지 부담 적게.

### Step 1: 정보 수집 (read-only — 컨펌 X)

다음 4 정보를 한 번에 모음:

**1-1. App name 추출** — 사용자 입력에서 추출 (예: "home-os 의 task 페이지 추가" → `home-os`). 모호하면 한 줄 확인.

**1-2. 환경 점검** — 부재 도구 list 작성, 자동 설치 X:

```bash
node --version       # ≥ 20 권장
pnpm --version       # 또는 npm/yarn/bun
git --version
```

추가 도구 (선택): Docker / PostgreSQL CLI / sqlite3 / gh (GitHub CLI).

**1-3. 스택 후보 정리** — 사용자 발화·기존 코드·cwd 의 단서 (예: `package.json` 의 framework, 사용자 발화 안 "Expo" / "FastAPI" 등 신호) 분석. 단서 기반 _권장 2-3 안_ 제시. 단일 home-os 패턴 강제 X.

기본 후보 (사용자 신호 없을 때):
| 후보 | 적합 자리 | 메모 |
|---|---|---|
| Next.js 15 + Tailwind + Prisma + Turso + pnpm | 웹 앱 default — home-os 패턴, 사용자 친숙 | full-stack, server actions, edge runtime |
| Expo (RN) + Expo Router + tRPC | 모바일 앱 자리 | iOS / Android 공통, EAS Build |
| SvelteKit + Drizzle + SQLite | 가벼운 웹 + 빠른 개발 | Next.js 보다 적은 boilerplate |
| Astro + Tailwind | 정적 / 콘텐츠 중심 | 블로그·랜딩 페이지 |

사용자 발화 신호 (모바일 / 정적 / 가벼운 / API only 등) 가 _없는_ 경우만 Next.js home-os default. 신호 있으면 신호 기준 후보 1순위.

**1-4. 기존 코드 검사** — `package.json` 발견 시 _기존 프로젝트_ 모드 (scaffolding skip + 스택 검증). 부재 시 _신규_ 모드.

### Step 2: 한 화면 컨펌 — 4 정보 확정

수집한 4 정보를 한 화면으로 사용자에 보여줌:

```
=== Phase 0 init 결정 자리 ===
App name:    <name>
환경:        Node ✓ / pnpm ✓ / Docker ✗ (필요 시 안내)
스택 후보:   1. Next.js+Prisma+Turso (default, 웹 앱)
             2. Expo+tRPC (모바일 신호 있으면)
             3. SvelteKit+Drizzle (가벼운 자리)
             → 사용자 발화 분석: "<선택 근거>" → <권장 1안>
프로젝트 모드: 신규 / 기존 (package.json 발견)

이대로 진행할까요? (진행 / 수정 — 스택·이름 변경 / 중단)
```

사용자 응답:
- **진행** → Step 3 자동 실행
- **수정** ("Expo 로 가자" / "이름 X 로" 등) → 4 정보 갱신 후 다시 보여줌
- **중단** → 멈춤

### Step 3: 적용 (한 묶음 실행 — 컨펌 X, Step 2 가 일괄 컨펌)

**3-1. 환경 점검 결과 기록** — `00_init/environment_check.md` 작성.

**3-2. 스택 결정 기록** — `00_init/stack_decision.md` 작성:
```
Framework: <chosen>
Styling:   <chosen>
DB:        <chosen>
Auth:      <chosen>
Forms:     <chosen>
Package:   <chosen>
```

**3-3. 디렉토리 scaffolding** (신규 프로젝트만):
- `npx create-next-app@latest <name>` 등 실행 (Step 2 의 일괄 컨펌이 본 자리 포함)
- 기존 프로젝트면 skip + `package.json` 의 스택 검증만

**3-4. CLAUDE.md (프로젝트 루트)** — 없으면 신규 작성. 있으면 _업데이트 권장_ 만 안내 (덮어쓰기 X).

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

**3-5. pipeline_state.yaml 생성**

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
