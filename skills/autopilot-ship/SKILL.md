---
name: autopilot-ship
description: "_앱 배포 셋업_ entry — 이미 `spec/` 가 잡혀 있고 기능 어느 정도 완성된 자리에서 첫 ship setup·env·domain·migration deploy 안내. 호스팅 선정 (Vercel / Fly / Railway / Cloudflare / EAS) + CI/CD 파일 + `.env.example` + 도메인 가이드 + deploy_record. 실제 배포 명령은 사용자 직접 실행 — 본 skill 은 _안내만_. autopilot-spec 의 _초기 spec·skeleton_ 자리와 작업 본질 분리. 재호출 가능 (env 변경·domain 추가·migration 운영 배포 자리)."
argument-hint: "<task description (선택)> [--qa quick|light|standard|thorough]"
metadata:
  group: entry
  fam: app
  modes: []
  blurb: "앱 배포·출시 준비 entry — 빌드·배포 setup 과 ship 체크리스트"
---

> 산출물 폴더: `<artifact-root>/spec/ship.md` 안 누적 ([CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier).

## Purpose — _앱 배포 셋업_ entry

본 skill 은 _작업 본질에 맞는 분리_ 원칙 ([CONVENTIONS §6.3](../../core/CONVENTIONS.md)) 자리:

| 자리 | autopilot-spec | autopilot-code | **autopilot-ship** |
|---|---|---|---|
| 시점 | 초기 (요구사항·기본 틀·skeleton) | 기능 구현 (반복) | **마지막 + 재호출** |
| 목적 | 만들 _것_ 결정 | _작동하게_ | **띄울 _자리_ 결정 + 환경** |
| 사용자 결정 무게 | 🔴 큼 | 🟢 작 (결과만 확인) | 🟡 중 (호스팅·DNS·env) |

## 흐름 안에서 본 skill 의 자리

```
앱 개발:
  autopilot-spec --mode app  (PRD + scaffolding + skeleton)
    → autopilot-design (옵션, UI 사이클)
    → autopilot-code (기능 구현 반복) — 기능 어느 정도 완성
    → autopilot-ship  ← 본 skill. 첫 ship setup·env·domain·migration 안내
       ↻ 재호출 — env 변경·domain 추가·migration 운영 배포 자리
```

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../CLAUDE.md) §0).

### Trigger 신호 (자연어 발화 예시)

- "배포 셋업" / "Vercel 셋업" / "배포 준비"
- "env 변경" / ".env 파일 보강"
- "도메인 연결" / "DNS 안내"
- "migration 운영 배포" / "production DB migration"

### Default 옵션 권장값

- `--qa`: `standard` (default — 호스팅 / CI/CD 파일은 _신중_ 자리)

### Override 1순위 — autopilot 우회

- 실제 배포 명령 실행은 _사용자 직접_ — `vercel deploy --prod` 같은 자리 본 skill 안 X
- `/autopilot-ship <args>` slash 직접 입력 — 컨펌 skip

## Context Auto-Detection

호출 자리에서 `<artifact-root>/spec/pipeline_state.yaml` 자동 검사:

| 감지 | 처리 |
|---|---|
| `spec/ship.md` 부재 | **첫 ship setup** — 호스팅 선정 + CI/CD + env + domain |
| `ship.md` 존재 | **재호출** — 발화 의도 분류 (env / domain / migration) 후 해당 자리만 |

발화 → 자리 자동 분류:

| 발화 | 추론 자리 |
|---|---|
| "배포 셋업" / "Vercel" | 첫 ship setup (전체) |
| "env 변경" / "환경 변수" | env 보강 자리만 |
| "도메인 연결" / "DNS" | domain 자리만 |
| "migration 운영 배포" | DB migration 자리만 (destructive 위험 안내) |

## Language Rule
- Think in English internally. Write user-facing output in Korean.

## Procedure

### Step 1: 현재 상태 점검 (read-only)

- `spec/pipeline_state.yaml` 의 `stack` 검증 (framework / DB)
- `git remote -v` — GitHub 연결 여부
- 기존 `vercel.json` / `.github/workflows/` / `.env.example` 발견 여부
- `git status` — working tree clean 검증

### Step 1.5: 배포 전 게이트 (첫 production deploy 전 권장)

운영 배포 전, 변경 표면에 따라 두 게이트 권고 (사용자가 skip 명시 가능). 둘 다 내장 명령의 온프레미스 흡수:
- **보안** — auth / secret / 외부 입력 / DB migration 을 건드린 변경이면 `Agent(품질관리팀 security-review)` (diff 의 _신규_ high-confidence≥8 취약점만). 🔴 HIGH 잔존 시 배포 보류 권고.
- **동작 확인** — `Agent(품질관리팀 test)` Level 5b _런타임 관찰_ (배포 대상 surface 실제 구동 + 증거 캡처). FAIL 시 배포 보류 권고.

게이트는 _권고_ 이지 차단이 아님 — 실제 배포 명령은 사용자 직접. 결과는 `ship.md` 에 기록.

### Step 2: 자리 분기 (발화 기반)

위 _Context Auto-Detection_ 의 _발화 → 자리_ 표 적용. 발화 모호 시 사용자 컨펌.

### Step 3: 첫 ship setup (가장 흔함)

#### 3-1. 호스팅 선정 — 사용자 컨펌

| 스택 | 권장 호스팅 |
|---|---|
| Next.js | Vercel |
| Next.js + heavy backend | Fly.io |
| 정적 사이트 | Cloudflare Pages |
| 컨테이너 | Railway |
| Mobile (Expo) | EAS Build |

다른 자리 (Astro / SvelteKit / Remix 등) — Vercel 또는 Cloudflare Pages.

#### 3-2. `.env.example`

실제 값 없음, 키만. 사용자가 dashboard 에서 직접 실제 값 입력.

#### 3-3. CI/CD 셋업

`.github/workflows/deploy.yml` 생성 (사용자 컨펌 후). 보통:
- Push to main → 자동 deploy (Vercel / Cloudflare 의 GitHub integration 사용 시 _생성 불필요_)
- 별도 cluster (Fly / Railway) 자리만 explicit workflow 자료 필요

#### 3-4. 도메인 (옵션)

DNS 는 사용자가 domain registrar dashboard 에서 직접 설정 (본 skill 은 레코드 안내만).

#### 3-5. 배포 명령 안내

```
vercel login
vercel link
vercel deploy --prod
```

또는 호스팅 별 명령. **배포 명령은 사용자가 직접 실행** (본 skill 은 명령 안내만).

#### 3-6. `spec/ship.md` 작성

```markdown
---
changelog:
  - date: <YYYY-MM-DD>
    type: initial
    notes: "<첫 setup 요약 — 호스팅·CI/CD·env keys·domain>"
---

# Ship Record — <name>

- 호스팅: <Vercel / Fly / ...>
- DB host: <Turso / Supabase / Neon / 등>
- Domain: <(if any) example.com>
- env vars (이름만): VAR_1 / VAR_2 / ...
- Deploy command: <vercel deploy --prod / fly deploy / ...>
- CI/CD: <GitHub Actions workflow path / Vercel auto>

## Notes
<배포 자리 특이사항·외부 service 연결 자리·재호출 시 점검할 자리>

## 변경 이력
- <YYYY-MM-DD>: initial setup
```

### Step 4: 재호출 자리 (단일 파일 누적 — refine v{N+1} 자리 아님)

`ship.md` 는 **단일 파일** — 재호출 시 _frontmatter `changelog:` 배열 append_ + _## 변경 이력_ 절 append. _이전 버전 스냅샷 X_ (배포 자료 자리는 _현재 자료_ 가 source of truth, 과거 자리는 git log 가 단일 source).

| 자리 | 처리 | ship.md 갱신 |
|---|---|---|
| env 변경 | `.env.example` 보강 + 사용자에 dashboard 안내 | env vars 자리 갱신 + changelog `{type: env, notes: "VAR_X 추가"}` |
| 도메인 추가 | DNS 안내 | Domain 자리 갱신 + changelog `{type: domain}` |
| migration 운영 배포 | destructive 안내 (`prisma migrate deploy` 같은 명령은 사용자 직접) + rollback 가능 자리 안내 | Notes 자리에 migration 자국 + changelog `{type: migration}` |

### Step 5: [CONFIRM Gate]

```
=== Ship 자리 ===
대상: spec/
자리: <첫 setup / env 보강 / domain / migration>
주요 결정: <3-5 bullet>

(진행 / 수정 / 중단)
```

## Forbidden Zones (명시 요청 없이 X)

- 실제 배포 명령 (`vercel deploy` / `fly deploy` 등) — 안내만
- 결제 정보·credit card 등록
- DNS 직접 변경
- 도메인 구매
- 환경변수 _실제 값_ 입력 (사용자 dashboard 직접)
- production DB migration 자동 실행

## CONFIRM Gate 응답 분기 (모든 Gate 공통)

| 응답 | 처리 |
|---|---|
| **진행** | 다음 단계 또는 종료 |
| **수정** | 현 단계 refine v{N+1} (`_internal/refine_v{N}.md` 백업) |
| **back-jump** | 이전 단계 재실행 |
| **중단** | 멈춤 |

## Return Format

```
spec/ship.md -- ✅ ship setup 완료
다음 — push 후 자동 deploy (Vercel/Cloudflare 자리) 또는 사용자 직접 명령
```

## Examples

### 예시 1 — 첫 Vercel 셋업

```
/autopilot-ship "가사관리앱 배포 셋업"
→ spec/가사관리/ 발견, ship.md 부재 → 첫 ship setup
→ stack: Next.js + Prisma + Turso 인지 → Vercel 권장
→ .env.example 키 list (DATABASE_URL / NEXT_PUBLIC_X / ...)
→ vercel.json (선택) + GitHub Actions deploy.yml
→ 배포 명령 안내: vercel login / link / deploy --prod
→ spec/가사관리/ship.md 작성
```

### 예시 2 — 환경 변수 변경 (재호출)

```
/autopilot-ship "STRIPE_KEY 환경 변수 추가"
→ ship.md 존재 → 재호출 자리
→ .env.example 에 STRIPE_KEY 키 추가
→ ship.md env vars 자리 갱신
→ 사용자 안내: Vercel dashboard 에서 실제 값 입력
```

### 예시 3 — 도메인 연결 (재호출)

```
/autopilot-ship "homemanager.app 도메인 연결"
→ DNS A 레코드 / CNAME 안내
→ Vercel dashboard 에서 domain 추가 안내
→ ship.md Domain 자리 갱신
```

## Task
$ARGUMENTS
