---
name: autopilot-app
description: "앱 개발의 _코드 외 결정·셋업 자리 전반_ — PRD (요구사항·시나리오·API Contract·데이터 모델) + 스택 결정 + scaffolding + skeleton 코드 + 보강 setup (ship 첫 setup·env·domain·migration deploy 안내). analyze-project 의 _신규 의도 → 청사진_ 대칭 자리. 코드 작업 자체는 autopilot-code 가 담당 (apps/<name>/ 컨텍스트 자동 감지)."
argument-hint: "<app description or feature> [--mode init|setup] [--qa quick|light|standard|thorough] [--user-refine]"
---

> 산출물 폴더: `.claude_reports/apps/<app-name>/` (CONVENTIONS.md §5 3-tier).

## Purpose — _코드 외 결정·셋업_ entry

본 skill 은 _코드 작업이 아닌_ 자리 담당:

- **PRD (요구사항·시나리오·API Contract·데이터 모델·화면 흐름)** — 앱 만의 _앞쪽 정의_ 자리
- **스택 결정 + 환경 점검 + scaffolding** — `create-next-app` 등
- **skeleton 코드 생성** — 빈 layout · routing · DB schema 초안 (실제 기능 X)
- **보강 setup** — ship 첫 setup (Vercel 연결·CI/CD·env 가이드·domain) + 운영 중 가끔 보강 (env 변경·migration deploy)

코드 작업 자체 (기능 구현·리팩터링·디버그) 는 `autopilot-code` 가 담당 — `apps/<name>/` 컨텍스트 자동 감지로 _앱 mode_ 활성화. 본 skill 은 _코드 외 자리_ 만.

## 앱 개발 흐름 안에서 본 skill 의 자리

```
1. autopilot-app          ← 본 skill. 초기 기반 (PRD + 스택 + skeleton)
2. autopilot-design       ← 시각 (옵션, UI 있을 시)
3. autopilot-code         ← 본격 개발 (앱 mode 자동, 반복)
4. autopilot-app           ← (필요 시) 보강 setup — ship 첫 setup·env·domain
```

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상.

### Trigger 신호 (자연어 발화 예시)

**초기 기반 mode** (신규 앱):
- "X 앱 만들어줘" / "Y 서비스 만들어줘" / "Z 웹사이트 짜줘"
- "이 앱의 spec 정리해줘" / "PRD 부터"

**보강 setup mode** (이미 있는 앱):
- "이 앱 배포 셋업해줘" / "Vercel 에 올리자" / "CI/CD 잡아줘"
- "env 변경·domain 연결·migration 운영 배포"

### Default 옵션 권장값

- `--mode`: auto-detect — `apps/<name>/pipeline_state.yaml` 부재 → `init`, 존재 → `setup`
- `--qa`: `standard` (global §6 high-stakes 신호 시 thorough 자동 상향)
- `--user-refine`: **off** (사용자 명시 시만 on)

### Override 1순위 — autopilot 우회

- 코드 기능 추가·수정·디버그 — `/autopilot-code` 직접 (앱 mode 자동 활성화)
- 디자인만 — `/autopilot-design` 직접
- 작은 작업 (한 파일 수정·rename) — `Agent(개발팀)` 직접
- `/autopilot-app <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- Think in English internally. Write user-facing output in Korean.
- Code identifiers, file paths, technical terms stay in English.

## Argument Parsing

### --mode (auto-detect default)
- `init` — 신규 앱. PRD + 스택 + scaffolding + skeleton 코드. `apps/<name>/pipeline_state.yaml` 부재 자리
- `setup` — 보강. ship 첫 setup / env 변경 / domain 변경 / migration deploy 안내. 이미 `apps/<name>/` 존재 자리

### --qa (review level)
- `quick` / `light` / `standard` (default) / `thorough` — [CONVENTIONS.md §1](../../CONVENTIONS.md) 의 단일 정의

### --user-refine
- On 시: PRD 작성 후 사용자 메모 받고 refine loop (`_internal/refine_v{N}.md` 백업)

## Procedure

### Mode A — `init` (초기 기반)

본 mode 가 _신규 앱_ 의 _앞쪽 정의 + skeleton_ 자리. 다음 5 자리 한 묶음.

#### Step 1: 정보 수집 (read-only, 컨펌 X)

**1-1. App name 추출** — 사용자 발화에서. 모호 시 한 줄 확인.

**1-2. 환경 점검** — `node --version`, `pnpm --version`, `git --version`, (선택) Docker / sqlite3 / gh. 부재 도구 list, 자동 설치 X.

**1-3. 스택 후보 정리** — 사용자 발화·기존 코드·cwd 단서 기반 권장 2-3 안:

| 후보 | 적합 자리 |
|---|---|
| Next.js 15 + Tailwind + Prisma + Turso + pnpm | 웹 앱 default |
| Expo (RN) + Expo Router + tRPC | 모바일 |
| SvelteKit + Drizzle + SQLite | 가벼운 웹 |
| Astro + Tailwind | 정적·콘텐츠 |

발화 신호 없으면 Next.js default. 신호 있으면 신호 기준 1순위.

**1-4. 기존 코드 검사** — `package.json` 발견 시 _기존 프로젝트_ (scaffolding skip + 스택 검증). 부재 시 _신규_.

**1-5. autopilot-research 결과 자동 import** — `.claude_reports/research/` 발견 시 reference 앱 패턴·스택 비교 인용 후보로 정리.

#### Step 2: 한 화면 컨펌

```
=== Phase 0 init 결정 자리 ===
App name:        <name>
환경:            Node ✓ / pnpm ✓ / Docker ✗ (필요 시 안내)
스택 후보:       1. Next.js+Prisma+Turso (default, 웹 앱)
                 2. Expo+tRPC (모바일 신호 있으면)
                 3. SvelteKit+Drizzle (가벼운 자리)
                 → 사용자 발화 분석: "<선택 근거>" → <권장 1안>
프로젝트 모드:    신규 / 기존 (package.json 발견)
research 인용:    .claude_reports/research/X 발견 — N 자리 참조

이대로 진행할까요? (진행 / 수정 — 스택·이름 변경 / 중단)
```

- 진행 → Step 3
- 수정 → 4 정보 갱신 후 다시
- 중단 → 멈춤

#### Step 3: 적용 — 한 묶음 실행

**3-1. 환경 점검 결과** — `00_init/environment_check.md`

**3-2. 스택 결정 기록** — `00_init/stack_decision.md`

**3-3. scaffolding** (신규만) — `create-next-app` 등 실행

**3-4. CLAUDE.md (프로젝트 루트)** — 없으면 신규 작성

**3-5. pipeline_state.yaml 생성**

**3-6. PRD 작성** — `01_spec/PRD.md` 에 다음 구조:

```markdown
# <App Name> PRD

## 피처 목록 (P0 / P1 / P2)
## 사용자 시나리오 (3-5개)
## 비기능 요구 (성능·보안·접근성·모바일)
## 데이터 모델 초안 (entity·관계·migration plan)
## API Contract (백·프론트 공유 — endpoint·body·error·auth)
## 화면 흐름 (UI 있을 시)
```

- 발화 모호 시 한 줄 확인 — _Other_ 가능 명시 (예: "주 사용자는 본인 / 가족 / 일반 / 다른 자리 (직접)?")
- 기획팀 위임 기준 — 피처 ≥5 + 시나리오 ≥5, 비기능 복잡, 데이터 모델 entity ≥4, 사용자 명시. 위임 전 사용자 한 줄 확인

**3-7. skeleton 코드 생성** — PRD 의 데이터 모델 + API Contract 기반:
- `prisma/schema.prisma` 또는 동등 — entity 정의만 (필드 비어 있음 가능)
- 빈 page routes — `app/<route>/page.tsx` 가 _Hello world_ 정도
- 기본 layout
- 실제 기능 (CRUD logic) 은 **autopilot-code 자리**, 본 skill 안 X

#### Step 4: [CONFIRM Gate 0 — refine 진입 가능]

```
초기 기반 완성:
  PRD: ...
  스택: ...
  skeleton: ...

(진행 — autopilot-design 또는 autopilot-code / 수정 — PRD refine v2 / 중단)
```

`--user-refine` on 또는 사용자 _수정_ 발화 시 PRD refine loop (`_internal/refine_v{N}.md`).

### Mode B — `setup` (보강 setup)

이미 `apps/<name>/` 있고 _기능 구현 끝_ 또는 _운영 중_. 다음 자리:

#### Step 1: 현재 상태 점검
- `pipeline_state.yaml` 의 stack·환경 검증
- `git remote -v` (GitHub 연결 여부)
- 기존 `vercel.json`·`.github/workflows/`·`.env.example` 발견 여부
- `phases.qa` 상태 — `done` 자리만 ship 진행 (`failed` 면 거부)
- git working tree 검증 — 더러우면 commit 권고 후 중단

#### Step 2: 사용자 발화 분류 — 어떤 setup?

| 발화 신호 | 처리 |
|---|---|
| "배포 셋업" / "Vercel 에 올려" | **ship 첫 setup** (provider·CI/CD·env·domain) |
| "env 변경" / "API 키 갱신" | env 보강 |
| "도메인 연결" | DNS 안내 |
| "migration 운영 배포" | DB migration deploy 안내 (destructive 위험 강조) |

#### Step 3: ship 첫 setup (가장 흔함)

**3-1. 호스팅 선정** — 사용자 confirm:

| 스택 | 권장 | 이유 |
|---|---|---|
| Next.js | Vercel | 공식, edge runtime, zero-config |
| Next.js + heavy backend | Fly.io | full Node.js, region |
| 정적 | Cloudflare Pages | 빠름, free tier |
| 컨테이너 | Railway | 간편, DB 함께 |
| Mobile (Expo) | EAS Build | RN 공식 |

**3-2. 환경변수 정리** — `.env.example` 작성 (실제 값 없음, 키만)

**3-3. CI/CD 셋업** — `.github/workflows/deploy.yml` 생성 (사용자 confirm 후)

**3-4. 도메인** (옵션) — DNS 안내. 자동 변경 X.

**3-5. 배포 명령 안내** — `vercel login` / `vercel link` / 환경변수 dashboard 입력 / `vercel deploy --prod`. **사용자 직접 실행** (Claude 자동 실행 X).

**3-6. `05_ship/deploy_record.md` 작성** — provider·CI/CD·env 키 list·첫 배포 기록

#### Step 4: 기타 보강 setup

- env 변경 — `.env.example` 업데이트 + dashboard 안내
- domain — DNS 안내
- migration deploy — `prisma migrate deploy` 명령 안내 + destructive 위험 표시 + 사용자 직접 실행

## Forbidden Zones (명시 요청 없이 X)

- 실제 배포 명령 (`vercel deploy`, `fly deploy` 등) — 안내만
- 결제 정보·credit card 등록
- DNS 직접 변경
- 도메인 구매
- 환경변수 _실제 값_ 입력 (사용자 dashboard 직접)
- production DB migration 자동 실행 (destructive 위험)

## CONFIRM Gate 응답 분기 (모든 Gate 공통)

| 응답 | 처리 |
|---|---|
| **진행** | 다음 단계 또는 종료 |
| **수정** | 현 단계 refine v2 작성 (`_internal/refine_v{N}.md` 백업) |
| **back-jump** | (init mode 에서) PRD 수정 후 skeleton 재생성. (setup mode 에서) 단계 재선택 |
| **중단** | pipeline 멈춤, `pipeline_state.yaml` 상태 보존 |

발화가 모호하면 옵션 다시 물음 (임의 추측 X).

## Pipeline state 관리

`apps/<app-name>/pipeline_state.yaml`:

```yaml
app_name: <name>
created: <date>
stack:
  framework: <chosen>
  db: <chosen>
phases:
  init: done       # autopilot-app init mode 완료
  design: pending  # autopilot-design 진행 시 done
  dev: in_progress # autopilot-code 가 앱 mode 로 누적 — 각 dev 호출이 누적
  ship_setup: pending  # autopilot-app setup mode 의 ship 첫 setup
last_updated: <timestamp>
```

autopilot-code 가 _앱 mode_ 로 호출될 때마다 `phases.dev: in_progress` 갱신 + 자체 dev log 누적 (`apps/<name>/dev_log/` 또는 동등 자리).

## Return Format

```
.claude_reports/apps/<app-name>/ -- ✅ {mode} completed (PRD / skeleton / ship setup)
```

다음 단계 안내:
- init 완료 → "디자인 사이클 (autopilot-design) 또는 첫 기능 구현 (autopilot-code)"
- setup 완료 → "이후 push 만으로 자동 deploy"

## Update memory

- 사용자가 자주 만나는 phase 게이트 보강
- 스택 선호·QA 강도 default
- ship setup 자주 만나는 함정
- migration deploy 사용자 처리 패턴
