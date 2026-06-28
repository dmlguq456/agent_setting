---
name: autopilot-code
description: "_코드 작업 일반_ entry — 라이브러리·연구 코드·앱 모두 커버. 신규·기존 코드 무관 (cwd 자동 감지). dev (기능 추가·신규) / debug (진단·수정) 두 mode. spec/ 컨텍스트 발견 시 spec 자동 Read + spec mode 별 분기: app mode → 디자인팀 critic + DB migration 안전 + push 자동 deploy. library mode → 공개 API 일관성 점검. cli mode → 명령·옵션 일관성. research mode → 재현성·configs·metric 검증. 코드 외 결정 (PRD·스택·skeleton·ship setup) 은 autopilot-spec 영역."
argument-hint: "--mode dev|debug <task/plan/error description> [--from <step>] [--qa quick|light|standard|thorough|adversarial] [--user-refine]"
metadata:
  group: entry
  fam: code
  modes: [dev, debug, audit]
  blurb: "코드 작업 일반 entry — 라이브러리·연구·앱 모두 커버, spec 컨텍스트 자동 감지"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). 코드 작업 산출물은 spec 유무와 무관하게 **항상** `<artifact-root>/plans/<date>_<slug>/` (청사진은 `spec/`, 작업은 `plans/` — 1 repo = 1 spec, 형제 bucket; [CONVENTIONS §5.4.3](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3)). plan/ + checklist는 T1 (root). dev_logs/, test_logs/는 T2 (root). reviewer 로그(plan_reviews, dev_reviews, test_reviews)는 모두 `_internal/` 하위. (모노레포 예외만 `spec/<component>/`·`plans/<component>/`.)
> `<artifact-root>` 해석: `.agent_reports` 우선, legacy `.claude_reports` 는 이미 존재하고 `.agent_reports` 가 없을 때만 사용. 실제 쉘 명령에서는 `REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports` 로 치환한다.

## Context Auto-Detection (spec mode 자동 분기 + 자료 자동 read)

본 skill 은 호출 자리에서 _cwd / 산출물 폴더 / spec 파일_ 검사 + 다음 자료 자동 read:

| 자료 | 자리 | 우선순위 |
|---|---|---|
| `mem profile 07_coding_convention` (`python3 <agent-home>/tools/memory/mem.py profile 07_coding_convention`) | 사용자 cross-project 컨벤션 | 2순위 (default·fallback) |
| `<artifact-root>/analysis_project/code/experiment_conventions.md` | per-project 컨벤션 | **1순위** — 코드 수정 4 원칙의 source. 충돌 시 per-project 우선 |
| `<artifact-root>/spec/prd.md` (있으면) | spec 청사진 | spec mode 별 추가 logic 활성화 |
| `<artifact-root>/spec/design/05_handoff/handoff.md` + `design/02_tokens/tokens.md` + `design/design_state.yaml` (app mode·design 산출 있으면) | 디자인 토큰·컴포넌트 인계 + 토큰 버전 | **app mode 1순위** — UI 구현은 이 토큰(`tokens_path`)·컴포넌트 위에서. 디자인팀 critic 의 _비교 기준_ 도 이 handoff. design 없으면 skip |
| `<artifact-root>/analysis_project/code/` 4 종 실험 자료 (`experiment_readiness`·`cleanup_candidates`·`similar_models`) | _실험 ready 정돈_ 자리 input | autopilot-code "실험 ready 정돈" 발화 시 자동 read |

### 1단계 — spec 존재 여부

| 감지 조건 | 처리 |
|---|---|
| `<artifact-root>/spec/pipeline_state.yaml` 존재 | spec 자동 Read + 그 안 `mode` 배열 따라 _추가 logic_ 활성화 |
| 부재 (spec 없이 호출) | 일반 mode — 표준 dev/debug. cwd 단서 (`package.json` framework·`argparse` 등) 만 보고 _경량 추론_ |

> **산출 경로는 spec 유무와 무관하게 항상 `plans/<date>_<slug>/`.** spec 의 `pipeline_state.yaml` 감지는 _spec mode 별 추가 logic_ (app/library/api/cli/research) 을 활성화할 뿐, OUTPUT PATH 를 가르지 않음.

spec 발견 시 사용자에 명시 보고 — _"spec 발견 (spec/, mode: [library, cli, research]). 그 청사진 따라 진행. 산출 plans/."_

### 2단계 — spec mode 별 추가 logic

spec 의 `mode` 배열 (단일 또는 복수) 에 따라 자동 활성화:

| mode | 추가 logic |
|---|---|
| **app** | (1) UI 변경 자리 디자인팀 critic 자동 호출 (2) DB migration destructive 자리 명령 안내·자동 실행 X (3) push 후 CI/CD 자동 deploy 인지 (4) **토큰 = design 계약 (DESIGN_PRINCIPLES §9)** — code 는 design 소유 토큰(globals.css `@theme`/tokens.css)을 _참조·사용만_, 인라인 hex·px 로 재정의·즉흥변경 X. _substantial 시각 결정_(방향·토큰·새 레이아웃·구조)은 코드에서 즉흥 말고 **autopilot-design 으로 리드**(실제 앱 렌더 → 결정 → 토큰 계약 갱신) 후 본 skill 이 적용. trivial tweak(한 끗)만 직접 |
| **library** | (1) 공개 API 변경 자리 _semver 영향 분석_ (2) export 일관성 점검 (3) 사용 예시 갱신 권장 |
| **api** | (1) endpoint·body·error 일관성 (spec contract 와) (2) auth 변경 자리 보안 검토 (3) rate limiting 변경 자리 마이그레이션 안내 |
| **cli** | (1) 명령·옵션 일관성 (spec 과) (2) input/output 형식 점검 (3) exit code 일관성 |
| **research** | (1) entry point (train·eval) 변경 자리 _재현 명령_ 갱신 권장 (2) configs 변경 자리 spec 동기화 (3) 예상 metric 검증 가능 자리 자동 |

복수 mode 시 _해당하는 logic 모두_ 활성화.

### Pre-flight (필수 Step 0): git-state + spec-significance — 코드 손대기 _전_, verdict 보고 강제

> **Intake 게이트** (dev mode, 새·미명세 작업만): 입력이 비가역 결정 커버리지에 미달이면 [CONVENTIONS.md §6.6](../../CONVENTIONS.md#66-autopilot-intake-gate) 1라운드 질문 먼저. 질문 뱅크는 spec 분기 따름(app→앱 행, library/cli→라이브러리·CLI 행 — code 트랙 자체 행 없음). debug·기존 spec 따라가는 자리·재개(--from)는 skip (이미 명시됨, 별도 flag 불요).

**0a. git working-state 게이트 ([OPERATIONS.md §5.9](../../OPERATIONS.md#59-git-working-state-preflight-worktreemerge-가드-canonical))** — spec 트리아지 _전_, 코드 편집 _전_ 실행. merge/rebase/cherry-pick 진행 중·detached HEAD = **STOP**(사용자 보고, 자동 abort 금지), 다른 worktree 동일 브랜치·upstream 앞섬·세션 무관 dirty = **WARN**. 진입 시 `HEAD` 기억 → **각 commit/write-back 직전 재실행**(주기적 체크)해 HEAD 가 바뀌었거나 새 `MERGE_HEAD` 생겼으면 STOP. 여러 worktree·브랜치+merge 자리에서 §5.8 산출물 lock 이 못 잡는 _실제 repo 상태_ 를 닫는 가드. 비-git·단일 체크아웃은 무해 통과.

> **DONE-BRANCH → 새 브랜치 (이 cycle 이 새 작업일 때)**: §5.9 게이트가 `DONE-BRANCH`(현재 브랜치가 base 에 ahead 0 = 머지 완료된 끝난 브랜치) 를 내면, 이 plan 의 slug(`plans/<date>_<slug>/` 와 동일)로 **base 최신에서 새 브랜치를 판 뒤** 코드 작업 진행 — `git fetch origin && git switch -c <slug> origin/<base>` (worktree 안전: base 를 체크아웃 안 해 main worktree 와 비충돌). 현재 브랜치가 이미 이번 작업용 빈 브랜치면 그대로 사용. 죽은(머지된) 브랜치 위에 새 작업을 쌓지 않게 하는 자리 — worktree+merge 워크플로우의 핵심 누락. 한 줄 보고 후 진행.

> **규모 분기 ([OPERATIONS.md §5.10](../../OPERATIONS.md#510-작업-격리병렬-디스패치-worktree-정책-canonical))**: 두 축으로 게이트 — 어느 하나라도 본작업이면 worktree.
> - **변경 종류 (qa 레벨 무관, adapter worktree policy (Claude Code: [CLAUDE.md §0(C)](../../CLAUDE.md))·drill g3)**: 기능 추가·모듈 신설·다파일 변경은 **규모·qa 판단 없이 무조건 worktree+작업 브랜치**. main 트리 직접은 typo·1줄급 자잘한 단발만 (qa quick 이어도 다파일이면 worktree — "quick 이니 main" 우회 금지).
> - **실행 메커니즘 (반쪽 적용 금지 — drill 신설 자리)**: worktree 를 _파 두기만_ 하고 main 에서 autopilot-code 를 in-process(Skill)로 돌리지 않는다. worktree 확보 _즉시_ 그 안으로 **`claude -p` 헤드리스 분사 (§5.10 풀 ceremony) — plan 호출부터 report 까지 통째로 한 세션**. main 은 _정찰(분사 대상 결정)·분사·수확_ 만 (§5.10:389 "조정만 main"). 파이프 스테이지(code-plan·refine·execute)를 main 과 헤드리스로 **쪼개면 헤드리스가 상태 재발굴 + 연속성 상실 = worst of both** — 금지. 단 가벼운 정찰(파일 나열·diff 범위)로 _무엇을 분사할지 결정_ 하는 건 main 정상.
>
> quick 급 _단발_(typo·1줄)만 현재 트리 직접. 작업 진행 중 새 독립 요청이 오면 §5.10 디스패치 규칙 (파일 겹침 triage → 병렬 worktree 분사 / 겹치면 큐잉, merge 는 사용자).

**0b. spec-significance 트리아지** — spec/ 존재 시, _어떤_ 코드 요청이든 plan 전에 **이 게이트를 먼저 통과하고 한 줄 verdict 를 반드시 출력**한다. WORKFLOW §7-3 의 spec-drift 사전 체크를 _메인 에이전트의 라우팅 판단_ (잘 건너뜀) 이 아니라 _본 skill 의 강제 첫 단계_ 로 내재화 — "그냥 code 로 진입" 으로 스킵 못 하게.

1. 요청 + `spec/prd.md` (+ 해당 시 `api_contract.md`·`data_model.md`·`ui_flow.md`) 대조.
2. 분류:
   - **spec-significant** — route 추가/변경 · schema·entity 필드 · UI-flow · 외부 service 통합 · stack·migration · 기존 코드가 이미 spec 과 drift. → **`autopilot-spec` update 먼저** (prd.md 최신화 + `_internal/versions/v{N}/` 스냅샷) → _갱신된 spec_ 에 맞춰 코드 진행. drift 명확하면 자율 진행 + 한 줄 보고, **_애매하면 사용자 확인_**.
   - **within-spec** — 구현 디테일 (버그 수정·리팩터·내부 로직). → 그대로 코드 진행.
3. **verdict 한 줄 필수** (plan/dev_logs 에도 기록 — 이 줄 없이 코드 plan 진입 X):
   ```
   spec-significance: within-spec (구현 디테일 — spec 영향 없음)
   ```
   ```
   spec-significance: SPEC-SIGNIFICANT (data_model: Task.category) → autopilot-spec update 먼저
   ```

> 이 Step 0 (요청이 spec 을 바꾸나) → 아래 _역방향 drift 체크_ (spec 이 코드보다 최신인가) → 작업 중 _Spec 영향 변경 감지_ (코드가 spec 을 건드렸나) 셋이 spec↔code 동기화를 앞·뒤 양방향으로 닫는다.

### 진입 시 spec/design 갱신 역방향 체크 (코드 작업 _시작 전_)

spec·design 산출물이 _직전 코드 작업 사이클 이후_ 갱신됐는지 먼저 확인 — 갱신분을 못 보고 stale 한 토큰·계약 위에 작업하는 것 차단 (코드→spec 감지의 대칭):

| 비교 | 판정 |
|---|---|
| `spec/pipeline_state.yaml` 의 `last_updated` vs 최근 `plans/<date>_*/` 작업 날짜 | prd 가 더 최신 → 갱신된 `prd.md` re-read 후 작업 |
| `design/design_state.yaml` 의 `tokens_version`·`tokens_updated` vs 코드가 반영한 토큰 버전 (직전 plan log 기록) | 토큰이 더 최신 → 최신 `tokens.md`·`tokens.css` re-read, `design_summary.md` 의 변경 entry 확인 |

갱신 감지 시 사용자에 알림 후 진행:
```
=== spec/design 갱신 감지 (역방향 drift) ===
spec 이 직전 작업(plans/2026-05-20_*) 이후 갱신됨:
  - tokens v2 → v3 (2026-06-01, design_summary.md: brand-500 #F97316→#EA580C "대비 강화")
  - prd.md (2026-05-30)
갱신분 반영해 진행합니다. (무시하려면 알려주세요)
```
app mode 에서 `design_summary.md` 의 최근 토큰 변경이 코드에 미반영이면 _묶음 반영 plan_ 제시 (아래 "Spec 영향 변경 감지" 의 역방향). 현재 작업이 반영한 토큰 버전은 plan/dev_logs 에 기록해 다음 사이클의 anchor 로 남긴다.

### 경량 추론 (spec 부재 시)

spec 없이 호출된 자리에서도 cwd 단서로 _경량 mode 추정_:
- `package.json` 의 UI framework → 앱 자리 (일부 logic 적용)
- `package.json` 의 `bin` 필드 / argparse → CLI 자리
- `configs/*.yaml` + ipynb → research 자리

다만 spec 부재 시 _경량 추론_ — _전체 logic_ 은 spec 있을 때만. 사용자가 _완전한 mode 분기 원하면_ `/autopilot-spec` 으로 spec 먼저 만들기 권장.

> autopilot-spec 과의 경계: PRD·스택·skeleton·ship setup·env·domain·migration 운영 배포 _안내_ 는 **autopilot-spec 영역**. 본 skill 은 _코드 변경 자체_ 만 담당.

### Spec 영향 변경 감지 → 묶음 갱신 알림

코드 변경이 _spec 자리 영향_ 자리 (예: 새 API endpoint·entity 필드 변경·외부 service 통합) 발생 시 autopilot-code 가 _영향 받는 PRD 자리 자동 list_ → 사용자에 _묶음 갱신 plan_ 보여줌 → confirm 받고 autopilot-spec back-jump 호출 (또는 사용자가 _나중에_ 결정).

| 코드 변경 종류 | 영향 받는 spec 자리 |
|---|---|
| 새 API endpoint · body · error 변경 | `api_contract.md` + Component diagram + (옵션) Sequence diagram |
| `prisma/schema.prisma` 등 entity·필드 변경 | `data_model.md` + (옵션) ER diagram + Component diagram |
| 새 page route · UI flow 변경 | `ui_flow.md` + (옵션) Activity diagram + Component diagram |
| 새 외부 service SDK 통합 (`stripe`·`@clerk/nextjs` 등) | `api_contract.md` (auth) + Deployment diagram + `deploy_record.md` + `.env.example` |
| 스택 의존성 큰 변경 (DB 교체·framework 업그레이드) | `stack_decision.md` + Component diagram + Deployment diagram |
| state 모델 추가 (order / payment lifecycle 등) | `data_model.md` + (옵션) State diagram |

**알림 형태**:
```
=== Spec 영향 변경 감지 ===
변경: prisma/schema.prisma 의 Task 모델에 category 필드 추가

영향 받는 spec 자리 (묶음 갱신 권장):
  - spec/data_model.md (entity 필드 추가)
  - spec/api_contract.md (Task type 의 category 필드)
  
어떻게 진행할까요?
  (a) 지금 autopilot-spec 호출로 묶음 갱신 (back-jump)
  (b) 코드 작업 먼저 끝낸 후 나중에 (현재 변경은 dev_logs/ 에 기록)
  (c) 무시 — spec 갱신 안 함 (drift 받아들임)
```

자동 갱신은 _autopilot-spec back-jump_ 통해서만 — 본 skill 안에서 직접 spec 갱신 X (역할 경계 보존).

### 실험 ready 정리 자리 (autopilot-lab 사전 단계)

연구·실험 코드에서 _실험 시작 전 정돈_ 자리. autopilot-lab 진입 전 코드베이스를 _실험 적절한 상태_ 로 정돈하는 사전 작업. 별도 mode 가 _아니라_ dev mode 의 한 갈래로 처리 — 사용자가 _cleanup + refactor + ready 정리_ 같이 자연어로 발화하면 본 skill 이 통합 처리.

#### 자동 input

`<artifact-root>/analysis_project/code/` 에 있으면 자동 read:
- **`cleanup_candidates.md`** — unused / dead branch / 주석 자국 list (제거 후보)
- **`experiment_readiness.md`** — model 분리·train/eval 분리·seed·config 메커니즘 checklist (정리 후보)
- **`experiment_conventions.md`** — 사용자 코드베이스의 preferred layer / config / prefix 패턴 (정돈 시 1순위 준수)

#### 발화 trigger 신호

- "실험 ready 상태로 정리" / "lab 시작 전 정돈"
- "unused 코드 제거" / "main.py 를 train.py / eval.py 분리"
- "model 폴더 분리" / "config 메커니즘 통일"

본 발화 인지 시 메인 에이전트가 cleanup_candidates / experiment_readiness 를 자동 input 으로 본 skill 호출. code-plan 자리에서 _cleanup + refactor + ready 정돈_ 한 묶음 plan 생성.

#### 자리 흐름

```
analyze-project --mode code → cleanup_candidates.md / experiment_readiness.md 추출
   ↓
autopilot-code "실험 ready 정돈" (본 skill) — cleanup + refactor + ready 한 묶음
   ↓
analyze-project --mode code 재실행 (옵션 — readiness 재점검)
   ↓
autopilot-lab "X 실험" — Step 0 에서 readiness ✓ 확인 후 진행
```

본 자리에서 _experiment_conventions.md 의 preferred layer / config / prefix 패턴_ 을 code-plan / code-execute 단계 입력으로 자동 prepend — 정돈 결과가 사용자 코드베이스 컨벤션과 어긋나지 않게.

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../CLAUDE.md) §0). 메인 에이전트가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

**dev 모드**:
- "X 기능 만들어줘" / "Y 추가해줘" / "Z 구현해줘"
- "이 모듈 리팩토링" (단, 한두 줄 rename 은 `Agent(개발팀)` 우회)
- 기존 plan 폴더 발견 + 재개 신호 ("이어서 진행", "다음 stage 부터")

**debug 모드**:
- "이 에러 디버그해봐" / "X 가 안 돌아" / "왜 안 되지"
- 에러 로그 / traceback 첨부
- 테스트 fail 보고서 첨부

### Default 옵션 권장값 (컨펌 시 메인 에이전트가 제안)

- `--mode`: 발화 신호로 dev/debug 자동 추론. cwd 가 plan 폴더 + 최근 dev_logs/ 있으면 dev 우세, 에러 로그·traceback 있으면 debug 우세.
- `--qa`: dev=thorough, debug=standard (default — global §6 high-stakes 신호 시 adversarial 자동 상향)
- `--from`: 자동 추론 (`pipeline_state.yaml` 발견 시 마지막 성공 stage 다음부터)
- `--user-refine`: **off** (글로벌 §2 — "사용자 검토 끼워" / "memo 추가하게 멈춰줘" 같은 명시 신호 있을 때만 켬)

### Override 1순위 — autopilot 우회

- 작은 작업 (한 줄 수정·rename·cleanup) — `Agent(개발팀)` 직접 호출 또는 직접 Edit
- 단발성 코드 리뷰 — `Agent(품질관리팀)` 직접 호출
- `/autopilot-code <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `<agent-home>/README.md` 운영 룰 안내로 자동 반영.

## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing

### --mode (REQUIRED)
- `--mode dev` — development pipeline (default if omitted)
- `--mode debug` — debug pipeline for runtime error diagnosis and fix
- `--mode audit` — 코드베이스/앱 전수 자체점검 → 병렬 리뷰 fan-out → 트리아지 → 저위험 자동수정(검증) + 위험건 플래그. 상세 = "Pipeline: Mode audit".
- If omitted: treat as `--mode dev` and warn: "모드가 지정되지 않았습니다. dev 모드로 기본 설정합니다."
- If invalid value: report error and stop.

### --from <step> (mode-specific)
- dev: plan|refine|execute|test|report (5 points)
  - **stage ↔ step 매핑**: `plan` = Step 1 (code-plan) / `refine` = Step 2 (code-refine + 연구팀 memos) / `execute` = Step 3 (code-execute) / `test` = Step 4 (code-test) / `report` = Step 5 (code-report)
- debug: not supported — always starts from diagnosis
- If --from is used with debug mode: warn "debug 모드에서는 --from이 지원되지 않습니다. 진단부터 시작합니다." and ignore.

### --qa <level>

QA 5 단계 정의 + 모델·round 매트릭스는 [`CONVENTIONS.md §1`](../../CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용:

- Supported: `quick` / `light` / `standard` / `thorough` (default) / `adversarial`
- **security-review (code 트랙의 보안 축 — fact-check 부재 대체)**: auth / crypto·secrets / external input / api_contract / deserialization 을 건드리는 변경이 `adversarial` 이면 `Agent(품질관리팀 security-review)` 를 code QA 에 parallel 추가 — diff 의 _신규_ high-confidence(≥8) 취약점만. (내장 `/security-review` 온프레미스 — `agent-modes/qa/security-review.md`.)
- **behavioral test (app/cli/api/library mode)**: code-test(품질관리팀 test)가 Level 5b _런타임 관찰_(실제 앱·CLI·API·라이브러리 구동 + 증거 캡처)을 자동 포함 — 단순 ML 학습 코드는 Level 1-5 로 충분. (내장 `/verify`·`/run` 온프레미스.)
- Mode-specific:
  - dev: 5 levels 모두 accept. default `thorough`.
  - debug: `adversarial` 받으면 `thorough` 로 downgrade + warn. default `standard` (빠른 root-cause 우선).
- 유효하지 않은 값 → `standard` fallback + warn ("유효하지 않은 QA level '{value}'. standard 로 기본 설정합니다.")
- Auto-detect: omitted 시 각 sub-skill 이 scope 기반 추정
- **Propagation**: `--qa <level>` 를 code-plan / code-refine 에 flag 로 전달. code-execute / code-test / code-report 는 plan frontmatter `qa_level: <level>` 로
- **Mid-pipeline switching**: Step 2+ 에서 `--qa` 명시 시 plan frontmatter 갱신. 명시 안 하면 frontmatter 값 보존 (없으면 `thorough`)
- **`quick` interactions**: `--user-refine` silently ignored (refine skip). `--from refine` 으로 재개 시 frontmatter `qa_level == quick` 이면 abort ("qa_level=quick 에서는 refine 단계가 skip 됩니다. --qa <level> 을 다른 값으로 명시해 재개하세요.")
- **`quick` = 소규모 잡일 경량 tier**: 데이터 split·포맷 변환·log 파싱·metric 재계산 같은 _로그는 남기되 deep review 불필요_ 한 작업의 자리. plan + execute + **test(forced thorough — 유지)** 는 돌되 plan-review·code-report·test-retry 는 skip. `plans/{date}_{slug}/` 에 plan + pipeline_summary + test 결과가 남아 DB-harvest 가능. _직접 처리(로그 0)_ 와 _dev/debug(full ceremony)_ 사이의 경량 자리. (test gate 는 quick 에서도 살아 있어 fast implementer execute 가 무검증 통과하지 않음.)

### --user-refine (boolean flag — opt-in only)

**Default: false. The orchestrator (메인 에이전트) MUST NOT add this flag on its own — it is set only when the user typed `--user-refine` (or an explicit Korean equivalent like "사용자 검토 끼워" / "memo 추가하게 멈춰줘") in the original prompt.**
When present, the orchestrator **pauses** at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before code-refine runs.

- Applies to: **dev mode only** (Step 2 plan refine, and the failure-loop refine after test failure).
- Debug mode: 연구팀 review skipped → flag ignored with one-line warning.

**Pause behavior** (dev mode):
1. After 연구팀 writes memos at Step 2 (or after failure memos are written in the test-failure retry loop), do NOT invoke code-refine.
2. Update plan frontmatter: `user_refine: true`, `paused_at_stage: refine`.
3. Print to user (Korean) the memo file path and the resume command:
   ```
   연구팀 메모가 {ko_plan_path}에 기록되었습니다.
   직접 메모를 추가한 뒤 다음 명령으로 재개하세요:
       /autopilot-code --mode dev --from refine <plan-name>
   ```
4. Exit. Do NOT write pipeline_summary.md (pipeline is paused, not terminated).

**Resume behavior**: When invoked with `--from refine`, the orchestrator skips Step 1 and goes directly to Step 2's code-refine invocation, then continues normally.

**Persistence**: `user_refine: <true|false>` lives in the English plan's YAML frontmatter (same place as `qa_level`). On `--from` resume, if `--user-refine` is not re-specified, preserve the frontmatter value.

When `--from` is used together with `--user-refine` (dev only), `--from refine` is the natural resume point after a user-refine pause.

The remaining text (after removing flags) is the task description, plan name, or error description (depending on mode).

**When starting from Step 2+** (dev mode), the argument must be a plan name (not a task description). Use the Plan Resolution section below to locate the plan folder.

## Decision Defaults (no autonomy gating)

The pipeline runs with sane defaults and only pauses on genuinely ambiguous or destructive situations. There is no autonomy-level dial.

| Decision Point | Default Behavior |
|---|---|
| Test failure (after code-test internal hotfix loop) | Auto-retry once (mode dev). |
| Pipeline-level catastrophic failure (plan status = failed) | Stop and report; no retry. |
| Final retry failure | Auto-stop, write pipeline_summary(failed), report. |
| Research team adds many memos | Auto-refine (or pause if `--user-refine` is set). |
| code-plan: existing plan with status `active` | **Always ask** — no safe default; user must choose resume vs. create new. |
| code-plan: existing plan with status `done` / `failed` | Auto-create a new plan (note the previous one for reference). |
| code-plan: existing plan with status `partial` | Auto-create a new plan covering the failed steps (read `failed_steps` from frontmatter). |
| debug: confirm diagnosis before fix | Auto-proceed unless root cause is ambiguous. |
| debug: ambiguous root cause (multiple possible) | **Always ask** — list candidates, ask which to investigate first. |
| debug: fix verification failed | Auto-rollback + report. |
| debug: environment issue (not code bug) | Auto-report env-fix steps; do not modify code. |

**Logging**: When the pipeline pauses (active-plan ambiguity, ambiguous root cause, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search (project-keyed — search across all projects): `ls -d <artifact-root>/plans/*/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

## Pipeline: Mode dev
You (the main Claude) orchestrate by invoking each skill directly via the Skill tool. All tasks go through the full pipeline. Step 2 (plan review as user proxy) uses a **task-aware expert** — UI/visual → `디자인팀`, 그 외 → `연구팀`; Step 6 (meta-report) = 연구팀.

> **자료팀 위임 (옵션)** — task 가 _결과 시각화·실험 log plot·result table 정리_ 같은 분석 자료를 요구하면 code-execute / code-report 단계 안에서 `Agent(자료팀, "<spec>")` 직접 호출. _훈련·실험 실행_ 자체는 autopilot-code 본 영역, 결과의 _후처리·시각화_ 만 자료팀 영역. 자료팀이 figure / 스크립트 / 표 한 묶음 생성 후 dev_logs/ 의 해당 step 안에 결과 자산 경로 박음.

### Step 1: code-plan
Invoke Skill: `code-plan` with the task description as args.
Wait for completion before proceeding.

### Step 2: code-refine (plan-review proxy — task-aware: 연구팀 / UI는 디자인팀)
**`--qa quick` short-circuit**: if `qa_level == quick`, skip the entire plan-review + code-refine invocation. Log to pipeline_summary Decision Points: `Step 2 | refine skipped (qa=quick) | auto | proceed to Step 3`. Proceed directly to Step 3.

Otherwise:
1. Resolve plan paths from code-plan output: `en_plan_path`, `ko_plan_path`, `log_dir`.
2. **Detect task type** before invoking 연구팀 (this hint provides the type-specific lens — see `agents/research-team.md` Role 1 Step 3 table):
   - Read the plan's "## Change Plan" target files. If any target is under `<agent-home>/skills/*` / `<agent-home>/agents/*` / `<agent-home>/README.md` / `<agent-home>/skills/.sync_state.json` → `task_type=meta-skill`.
   - If targets are under `~/.claude/settings.json` / `keybindings.json` / hooks → `task_type=infra/config`.
   - If targets are project source code (`.py`, `.cpp`, etc.) → `task_type=paper-driven code`.
   - If targets are under `<artifact-root>/documents/*` → `task_type=paper-driven doc`.
   - If targets are under `<artifact-root>/research/*` → `task_type=research artifact`.
   - If targets are **UI/visual** (`*.css` / `globals.css` / `styles/` / 앱 컴포넌트 `*.tsx`·`*.jsx` 의 _시각·레이아웃·디자인 토큰_ 변경) → `task_type=ui/visual`.
   - Mixed → `task_type=mixed`.

   > **plan-review proxy = task-aware (DESIGN_PRINCIPLES §9).** `task_type=ui/visual` 이면 아래 연구팀 호출을 **`Agent(디자인팀)` plan-review** 로 _대체_ — plan + 디자인 계약(`spec/design/05_handoff/handoff.md`·토큰)을 읽고 _계획된 접근_ 을 6축(위계·정렬·a11y·반응형·UX·톤) + **토큰 계약 준수** + slop 으로 리뷰 (render 전이라 _no-render plan-review_ 모드; 정의 = `agent-modes/design/critic.md`). 메모는 동일하게 `_internal/plan_reviews/design_review.md` → code-refine. UI 가 paper-driven 로직과 섞인 `mixed` 면 디자인팀 + 연구팀 둘 다 parallel. 그 외 task_type 은 연구팀(아래).

   **By `qa_level`** (reviewer 수·model 매트릭스는 [CONVENTIONS.md §1.1](../../CONVENTIONS.md#11-5단계-공통-정의) 단일 source — 본 sub-skill 은 그 spec 을 instance·axis 분담으로 풀어씀):
   - **quick / light** — 1× / 2× fast reviewer single pass, all task-type axes 단일 prompt 로:
     ```
     Invoke 연구팀: "Review this plan as user proxy. **Task type: {task_type}** — apply ALL Role 1 Step 3 axes for this task type (no Focus axis). Korean plan: {ko_plan_path}. English plan: {en_plan_path}. Review log: {log_dir}/_internal/plan_reviews/research_review.md. Weight task-type-specific axes heavily (for meta-skill: family-level naming conflict + cross-skill scope overlap + sync-skills downstream + frontmatter validity)."
     ```
   - **standard / thorough / adversarial** — **axis-decomposed parallel 연구팀**: dispatch N parallel instances (standard = 1× deep reviewer + 2× fast reviewers, thorough/adversarial = 2× deep reviewers + 2× fast reviewers). 각 invocation 에 `Focus axis: <axis_name>` 포함해 single lens 로 제한. axis list 와 task-type 별 axis 매핑은 `agents/research-team.md` Role 1 _Multi-axis parallel mode_ 표 single source. deep reviewer instance 는 _깊이 axis_ (correctness / methodology / domain), fast reviewer instance 는 _coverage axis_ (completeness / style / cross-ref / test gap). 각 instance 는 `[<axis_name>]` prefix 메모 + separate review log (`{log_dir}/_internal/plan_reviews/research_review_<axis_name>.md`) 작성. 모든 parallel 완료 후 메모 merge + dedup → code-refine. adversarial 은 추가로 `Agent(codex-review-team)` external adversary review parallel.
   - **Why decomposition at standard+**: 단일 instance 가 많은 axis 를 다루면 주의가 분산. parallel decomposition 으로 각 instance 가 좁게 집중해 사용자가 직접 잡아낼 만한 자리 (naming conflict / test coverage gap / style drift) 전부 커버.
3. If memos added:
   - **`--user-refine` pause**: if the flag is set (CLI or plan frontmatter), update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command, and exit. Do NOT invoke code-refine.
   - Otherwise: invoke Skill `code-refine` with the Korean plan path.
4. If no memos: skip to Step 3.

### Step 3: code-execute
Invoke Skill: `code-execute` with the plan name/path as args.
Wait for completion before proceeding.

#### Status Check (between Step 3 and Step 4)
After code-execute completes, read the English plan's frontmatter `status` field:
- `done` → proceed to Step 4.
- `partial` → proceed to Step 4 (test what succeeded).
- `failed` → code-execute already rolled back source code. **STOP the pipeline.** Write pipeline_summary.md (status: failed) FIRST, then report failure to the user with the checklist summary. Do NOT proceed to code-test or code-report.

### Step 4: code-test
Invoke Skill: `code-test` with the plan name/path as args.
Wait for completion before proceeding.

## Retry Budget (Total)
- code-test internal hotfix loop: max 2 attempts per test run
- Mode dev retry loop: max 1 pipeline-level retry
- Total theoretical maximum: 2 (first code-test) + 2 (second code-test after retry) = 4 hotfix attempts
- At each code-test invocation, the hotfix counter resets.

#### Test Failure → Retry Loop (max 1 pipeline-level retry; quick = no retry)
**`--qa quick` short-circuit**: if `qa_level == quick` and code-test reports failure, do NOT retry. Skip the retry loop below and go directly to Step 5 (code-report) with status reflecting the test failure. Log to pipeline_summary Decision Points: `Step 4 | test failure, no retry (qa=quick) | auto | proceed to code-report`.

Otherwise (qa_level != quick), if code-test reports failure (after its internal hotfix loop of 2 attempts), auto-retry once:

1. **Collect failure context**: Note the test failure verdict from code-test's return. Failure details are in `test_logs/test_report.md` and `_internal/test_reviews/` — these will be consumed by code-refine's agent, not by the orchestrator.

2. **Rollback source code only** (preserve plan/log files):
   - Read Safety commit hash from `plan/checklist.md` header: `Safety commit: {hash}`
   - Run: `git checkout <safety-commit> -- <changed paths>` (NOT `<artifact-root>/`)
   - Verify with `git status`

3. **Write failure memos into Korean plan**: Append `<!-- memo: [테스트 실패] code-test 실패. 상세: test_logs/test_report.md, _internal/test_reviews/. 대안 필요. -->` at relevant steps in `plan/plan_ko.md`.

4. **Reset checklist**: Reset all step marks in `plan/checklist.md` to `[ ]`.

5. **Loop back to Step 2**:
   - **`--user-refine` pause**: if the flag is set, update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command (`/autopilot-code --mode dev --from refine <plan>`), and exit. The user can review the failure memos plus add their own before re-resuming.
   - Otherwise: invoke Skill `code-refine` with the plan path (QA review loop runs as usual, max 3 rounds).

6. **Re-execute**: Invoke Skill: `code-execute` with the same plan path.

7. **Re-test**: If plan status is not `failed`, invoke Skill: `code-test`.
   - **Pass** → continue to Step 5 (code-report).
   - **Fail again** → rollback, **STOP**. Write pipeline_summary.md (status: failed, note both attempts) FIRST, then report to user. Do NOT proceed to code-report.

### Step 5: code-report
Invoke Skill: `code-report` with the plan name/path as args.

### Step 6: Pipeline Summary Report
> **동시성 가드 (공유 `<artifact-root>`)**: `pipeline_summary.md`·`pipeline_state.yaml` 등 `spec/` 공유 단일파일 쓰기 _직전_ **OPERATIONS.md §5.8** `.pipeline-lock` 획득, 쓰기 직후 해제(짧게 보유). spec-drift 로 prd.md 갱신(§ "Spec 영향 변경 감지" → autopilot-spec update) 시도 lock 경유(해당 skill 이 자체 획득). `plans/<cycle>/` 쓰기는 경로 분리라 비-lock. BLOCKED(`exit 3`) 면 쓰기 멈추고 사용자 보고.

Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=dev)** (see below).
Then report to the user: pipeline_summary.md path + 2-3 line verdict.

### Step 7: analysis_project/code/ 영향 자리 자동 update (혼합 분기)

코드 변경 후 `<artifact-root>/analysis_project/code/` 자료가 _drift_ 빠지지 않게 — autopilot-code 가 _final-report 직후_ 영향 범위 검사 + 분기.

#### 7-1. 영향 범위 검사

`dev_logs/` 또는 `git diff <safety-commit>..HEAD --name-only` 으로 변경 파일 list 추출. 다음 분류:

| 변경 종류 | 분기 |
|---|---|
| 한 module 안 함수·class·signature·rename / 한 줄 자리 수정 / 작은 logic 추가 | **(A) 직접 Edit** — autopilot-code 가 `analysis_project/code/<module>.md` 의 _interface_reference_ 표 / docstring 자리 직접 Edit (별도 skill 호출 X) |
| 새 module 추가 / 새 모델 폴더 추가 / module 삭제·rename / cleanup 큰 자리 / config 메커니즘 변경 / preferred layer 변경 / train·eval 분리 / seed·reproducibility 자리 변경 | **(B) analyze-project 자동 호출** — `/analyze-project --mode code` invoke (incremental 자동 — `_last_run.yaml` 발견 시 변경 자리만 재분석, `--skip-qa` 가벼움) |

판단 — _변경 파일 N 자리_ + _영향 받는 산출물 자리 종류_:
- 변경 파일 ≤ 3 + 한 module 안 + interface_reference 만 영향 → (A)
- 변경 파일 ≥ 4 또는 module 추가/삭제 또는 4 종 실험 자료 영향 → (B)
- 애매한 자리 → (B) 안전 default

#### 7-2. (A) 직접 Edit 대상

| 산출물 자리 | autopilot-code 가 직접 update |
|---|---|
| `analysis_project/code/<module>.md` 의 _interface_reference_ 표 | 변경 함수·class 한 행 추가·수정·제거 (Called by 컬럼 포함) |
| `analysis_project/code/<module>.md` 의 _Role / 본문_ | signature 변경 자리만 한 줄 정도 — 큰 본문 재작성 자리는 (B) |

#### 7-3. (B) analyze-project 자동 호출

```bash
/analyze-project --mode code --skip-qa
# default incremental — _last_run.yaml 발견 시 변경 파일만 재분석
# --skip-qa — autopilot-code 의 final-report 가 이미 검증된 자리, 추가 QA cost 절감
```

호출 결과:
- 변경 module 분석 .md update
- 4 종 실험 자료 영향 자리 update
- `_last_run.yaml` 갱신
- 사용자에게 _한 줄 보고_ — "analysis_project/code/ 자료 N 자리 자동 갱신"

#### 7-4. 사용자 skip 옵션

사용자 발화 `"분석 자료 update skip"` / `"--no-analyze-update"` 명시 시 본 Step 7 skip.

#### 7-5. mode debug 자리

debug 의 _수정 자리_ 도 동일 logic 적용 (Step 6 후) — 보통 _작은 변경_ 자리라 (A) 직접 Edit 우세.

## Pipeline: Mode debug

### Step 1: Diagnose — trace root cause
Do NOT delegate this step. You (the main Claude) perform the diagnosis directly.

1. **Parse the error & check runtime context**: Extract error type, message, traceback, affected file/line. Run `git log --oneline -10` and `git diff HEAD~3`; check config/checkpoint files if relevant.
2. **Read the relevant code**: Follow the call stack or error location. Read the source files.
3. **Identify root cause**: Determine whether the issue is in:
   - Code logic (bug introduced by recent changes)
   - Environment (missing files, wrong config state, missing dependencies)
   - Data (corrupted checkpoint, wrong format, missing keys)
   - Interaction (code is correct individually but breaks when combined)
4. **Report diagnosis to user** in Korean:
   ```
   ## 진단 결과
   - **에러**: {error type and message}
   - **위치**: {file:line}
   - **근본 원인**: {root cause explanation}
   - **영향 범위**: {what else might be affected}
   - **수정 방향**: {proposed fix approach}
   ```
5. **Diagnosis confirmation**:
   - If the root cause is **unambiguous** (single clearly-identified cause): auto-proceed to fix plan.
   - If the root cause is **ambiguous** (multiple plausible causes): list the candidates and ask the user which to investigate first before creating the fix plan. This is the only debug-mode pause point.

### Step 2: Create fix plan
Invoke Skill: `code-plan` with a fix task description:
```
Fix: {root cause summary}

Error: {error message}
Location: {file:line}
Root cause: {diagnosis from Step 1}
Proposed fix: {fix approach}

Scope: Minimal — fix the root cause only. Do not refactor or improve surrounding code.
```

The plan folder will be: `<artifact-root>/plans/{YYYY-MM-DD}_fix_{short-error-name}/`

### Step 3: Review fix plan (QA only, skip research-team)
- Skip 연구팀 review — debugging fixes should be fast.
- QA review still runs via code-plan's built-in Post-Plan Review Loop.
- If QA has 🔴 issues, let the review loop resolve them (max 3 rounds as usual).

### Step 4: Execute fix
Invoke Skill: `code-execute` with the fix plan path.
- Status check: if `failed`, report to user and stop.

### Step 5: Verify fix
Invoke Skill: `code-test` with the fix plan path.

**Additional verification**: After code-test passes, reproduce the original error scenario:
- If the user provided a specific command that triggered the error, re-run it.
- If the error was during training, run a short training session (1-2 epochs).
- If the error was during inference, run an inference test.
- Report whether the original error is resolved.

If tests fail or the original error persists, auto-rollback and then proceed to reporting.

On rollback path:
1. **Rollback**: Determine changed paths from checklist or git diff. Read the Safety commit hash from the fix plan's `plan/checklist.md` header line: `Safety commit: {hash}`. Run `git checkout <safety-commit> -- <changed paths>`
2. **Write pipeline_summary.md (status: unresolved)** BEFORE reporting to the user. See Step 6 for the format.
3. **Report to user** with:
   - Original diagnosis
   - What was attempted
   - Why it didn't work
   - Suggested manual investigation steps

### Step 6: Report
Invoke Skill: `code-report` with the fix plan path.

**pipeline_summary.md must be written BEFORE reporting to the user, regardless of success/failure path.** This is the first action upon reaching any terminal state (fixed, partial, unresolved, or stop). On failure path (Step 5 rollback), pipeline_summary.md is written as part of that failure path — do NOT skip it.

Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=debug)** (see below).
Report to user: summary + verdict.

## Pipeline: Mode audit

_코드베이스/앱 "전수 자체점검 + 자율 수정"_ 자리. 발화 예: "전수 점검해서 더 효율적·효과적인 동작/UI 까지 컨펌없이 고쳐", "병렬 검토 많이 돌려". dev=새 기능 / debug=에러 진단 과 구분 — audit = _있는 것 전반을 훑어 개선_.

> **audit mode vs 빌트인 `audit` 스킬**: 본 mode = _소스 코드·UI·동작_ 점검+수정. 빌트인 `audit` 스킬 = `<artifact-root>/{plans,documents,research}` _산출물_ 린트 (대상 다름). 앱 점검은 본 mode.

오케스트레이션은 main, 리뷰·수정은 fan-out. 산출물 `plans/<date>_audit/` (findings·triage·fixes·flagged).

### Step 1: Review fan-out (병렬, 읽기전용)
`Workflow` 로 다수 병렬 리뷰어 — _영역 × 차원_. 규모는 요청에 맞춤 ("많이/전수" → 10~16+).
- UI·시각·반응형·a11y → `agentType: 디자인팀` (render-aware). 코드·동작·perf·일관성·데이터레이어 → `agentType: 품질관리팀` (code-review).
- 각 리뷰어: 코드 직접 읽고(+가능 시 렌더) 구조화 finding — `{title, severity, category, files, proposed_fix, risk(low/med/high), confidence}`. **읽기전용 — finding 만 작성.** 코드로 확인한 것만 보고 (모호하면 제외).

### Step 2: Triage (1 에이전트)
중복 병합, 저가치·과도·모호·confidence<0.6 드롭. 남은 것 분류:
- **autofix** — `risk=low` + 개선 명확 (토큰·문구·일관성·a11y 속성·단순 중복 추출 등). **파일 겹침 없는 클러스터로** 묶음 (병렬 수정 충돌 방지).
- **flagged** — `risk med/high` (동작 변경·구조·스키마·데이터·판단 필요) → 자동수정 말고 보고.

### Step 3: Fix (autofix 클러스터)
**⚠️ worktree 는 _현재 main(HEAD)_ 에서 판다** — `git worktree add <repo>-wt/audit-<key> -b <branch> main`. **`Workflow` 의 `isolation:'worktree'` 를 자율수정 fan-out 에 쓰지 말 것** (실측 2026-06-15: isolation worktree 가 32커밋 뒤 stale base 로 잡혀 머지 시 그간 작업을 revert — 5000줄+ 삭제 diff. review/triage 는 isolation 무방, _수정_ 만 명시 current-main worktree 로). 심링크(node_modules·.cache·<artifact-root>·.env.local) 후 클러스터별 헤드리스 `claude -p "/autopilot-code …"` 분사(또는 팀 위임).
- 각 fixer: 그 클러스터만 적용 (scope creep 금지·토큰 계약 준수) → **검증: `tsc --noEmit` 0 + full `next build`(DB 있어야 page-data 통과 → `.cache` 심링크 필수) + UI 변경은 디자인팀 verifier 실화면(light/dark/mobile390)** → 커밋. merge 안 함.

### Step 4: Harvest + Report
오케스트레이터(main)가 검증된 fix 브랜치를 **순차 머지** (§5.10 — 클러스터 비겹침이라 충돌 0, diff 실내용 확인 후) → `:3020` 등 full build 재확인. flagged 는 묶어 보고 (사용자 결정 또는 후속 dev/debug cycle). pipeline_summary 에 findings·autofix·flagged·dropped 수 기록.

### audit mode 규율
- 자율 (per-fix 컨펌 X) 이되 **검증 게이트 필수** — 미검증 머지 금지. risky 는 _자동수정 말고 flag_.
- 리뷰 = 읽기전용. 수정 base = 현재 HEAD (stale 금지). 머지 = 오케스트레이터. 사용자는 flagged 결정만.

## Pipeline Summary Template (all modes)

**Write `{log_dir}/pipeline_summary.md` as the FIRST action on reaching any terminal state** (success, partial, failed, stop) — before reporting to the user, on all paths.

This is a process log and artifact index — NOT a change analysis (that's code-report's job).

Populate the Decision Points table from in-memory decision records. If none: `| - | No gated decisions triggered | - | - |`.

```markdown
# {mode_title}: {task_or_error_name}

- **Date**: {YYYY-MM-DD}
- **Status**: done / partial / failed{debug: " / unresolved"}
{mode_specific_fields}
- **User-Refine**: {true | false}

## Process Log
| Step | Skill/Action | Result | Notes |
|---|---|---|---|
{mode_specific_rows}

## Artifacts
{mode_specific_artifacts}

## Decision Points
| Step | Decision | User Response | Action Taken |
|---|---|---|---|
```

### Mode-specific fields

| Field | dev | debug |
|---|---|---|
| Title prefix | "Pipeline Summary" | "Debug Pipeline Summary" |
| Extra header fields | `Plan: {en_plan_path}` | `Error: {msg}` + `Root Cause: {diagnosis}` + `Fix Plan: {path}` + `Attempts: {N}` |
| Process Log rows | Steps 1-5 + 4R (retry: refine→execute→test) | Steps 1-6 (Step 1=Diagnosis, no row for Step 3) |
| Artifacts | plan/ (T1), dev_logs/ (T2), test_logs/ (T2), _internal/{plan_reviews,dev_reviews,test_reviews}/ (T3), final_report | same minus research artifacts |

## Safety Rules

### Common (all modes)
- If execution fails catastrophically (plan status = `failed`), stop and report to user immediately.
- Always verify — testing 은 모든 path 에서 실행.
- 각 skill 의 QA loop 는 그 skill 이 자체 처리 (orchestrator 는 위임).

### Mode dev
(No additional mode-specific rules beyond common.)

### Mode debug
- **Minimal scope**: Fix the bug only. Do not refactor, improve, or clean up surrounding code.
- **Preserve existing behavior**: The fix should not change behavior for cases that were already working.
- If the root cause is ambiguous (multiple possible causes), list them and ask the user which to investigate first — this is the only debug-mode pause point.
- If the root cause is an environment issue (not a code bug), auto-report env fix steps; do not modify code.
