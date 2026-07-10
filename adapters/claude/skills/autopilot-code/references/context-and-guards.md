> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). 코드 작업 산출물은 spec 유무와 무관하게 기본적으로 `<artifact-root>/plans/<date>_<slug>/` (청사진은 `spec/`, 작업은 `plans/` — 1 repo = 1 spec, 형제 bucket; [CONVENTIONS §5.4.3](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3)). 단 `intensity=direct` 는 plan stage/plan artifact 없음, `quick` 은 inline micro-plan + plan-check-lite 가 기본이며 durable plan 은 adapter/repo 정책상 필요할 때만 남긴다. `standard+` work cycle 에서 plan/ + checklist는 T1 (root). dev_logs/, test_logs/는 T2 (root). reviewer 로그(plan_reviews, dev_reviews, test_reviews)는 모두 `_internal/` 하위. (모노레포 예외만 `spec/<component>/`·`plans/<component>/`.)
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

> **Intake 게이트** (dev mode, 새·미명세 작업만): 입력이 비가역 결정 커버리지에 미달이면 [CONVENTIONS.md §6.6](../../core/CONVENTIONS.md#66-autopilot-intake-gate) 1라운드 질문 먼저. 질문 뱅크는 spec 분기 따름(app→앱 행, library/cli→라이브러리·CLI 행 — code 트랙 자체 행 없음). debug·기존 spec 따라가는 자리·재개(--from)는 skip (이미 명시됨, 별도 flag 불요).

**0a. git working-state 게이트 ([OPERATIONS.md §5.9](../../core/OPERATIONS.md#59-git-working-state-preflight-worktreemerge-가드-canonical))** — spec 트리아지 _전_, 코드 편집 _전_ 실행. merge/rebase/cherry-pick 진행 중·detached HEAD = **STOP**(사용자 보고, 자동 abort 금지), 다른 worktree 동일 브랜치·upstream 앞섬·세션 무관 dirty = **WARN**. 진입 시 `HEAD` 기억 → **각 commit/write-back 직전 재실행**(주기적 체크)해 HEAD 가 바뀌었거나 새 `MERGE_HEAD` 생겼으면 STOP. 여러 worktree·브랜치+merge 자리에서 §5.8 산출물 lock 이 못 잡는 _실제 repo 상태_ 를 닫는 가드. 비-git·단일 체크아웃은 무해 통과.

> **DONE-BRANCH → 새 브랜치 (이 cycle 이 새 작업일 때)**: §5.9 게이트가 `DONE-BRANCH`(현재 브랜치가 base 에 ahead 0 = 머지 완료된 끝난 브랜치) 를 내면, 이 plan 의 slug(`plans/<date>_<slug>/` 와 동일)로 **base 최신에서 새 브랜치를 판 뒤** 코드 작업 진행 — `git fetch origin && git switch -c <slug> origin/<base>` (worktree 안전: base 를 체크아웃 안 해 main worktree 와 비충돌). 현재 브랜치가 이미 이번 작업용 빈 브랜치면 그대로 사용. 죽은(머지된) 브랜치 위에 새 작업을 쌓지 않게 하는 자리 — worktree+merge 워크플로우의 핵심 누락. 한 줄 보고 후 진행.

> **규모 분기 ([OPERATIONS.md §5.10](../../core/OPERATIONS.md#510-작업-격리병렬-디스패치-worktree-정책-canonical))**: 두 축으로 게이트 — 어느 하나라도 본작업이면 worktree.
> - **변경 종류 (qa 레벨 무관, adapter worktree policy (Claude Code: [CLAUDE.md §0(C)](../../adapters/claude/CLAUDE.md))·drill g3)**: 기능 추가·모듈 신설·다파일 변경은 **규모·qa 판단 없이 무조건 worktree+작업 브랜치**. main 트리 직접은 typo·1줄급 자잘한 단발만 (qa quick 이어도 다파일이면 worktree — "quick 이니 main" 우회 금지).
> - **실행 메커니즘 (반쪽 적용 금지 — drill 신설 자리)**: worktree 를 _파 두기만_ 하고 main(depth 0)에서 autopilot-code 를 in-process(Skill)로 돌리지 않는다. worktree 확보 _즉시_ 그 안으로 **`claude -p` 헤드리스 분사 (§5.10 풀 ceremony)** — main 은 _정찰(분사 대상 결정)·분사·수확_ 만 (§5.10 "조정만 main"). 파이프를 **main(depth 0)과 헤드리스로 쪼개는 것은 여전히 금지** (상태 재발굴 + 연속성 상실 = worst of both). 단 가벼운 정찰(파일 나열·diff 범위)로 _무엇을 분사할지 결정_ 하는 건 main 정상.
> - **스테이지 분사 (2026-07-10 stage-dispatch 반전 — `standard+` 기본 권장)**: 위 헤드리스 세션(depth-1 conductor) _안_ 에서는 반대로, 각 sub-skill 스테이지(code-plan·refine·execute·test·report)를 **depth-2 headless 세션으로 분사하는 것이 `standard+` 기본**이다. 과거 "스테이지를 쪼개면 상태 재발굴·연속성 상실 = 금지" 우려는 **산출물 기반 소통**으로 해소됐다 — 스테이지 인터페이스는 이미 파일(`plan.md`·`checklist.md`·`dev_logs/`·`test_logs/`·`final_report.md`, §2.1 계약)이므로 "재발굴"은 파일 로드 비용으로 수렴하고, 연속성의 매체가 대화가 아니라 파일이라 "연속성 상실"이 발생하지 않는다 (OPERATIONS §5.10 ③④, DESIGN_PRINCIPLES §8, spec/stage-dispatch SD-1·SD-2). conductor 는 스테이지 산출물 _본문_ 을 안 읽고 verdict/status·게이트 분기만 쥔다. 계약 완결성 의무: 산출물이 다음 스테이지 컨텍스트를 완전히 담아야 하며, 못 담으면 대화로 때우지 말고 산출물 스키마를 보강한다. **경계**: 산출물을 새로 쓰지 않거나 한 줄 verdict 만 내는 마이크로-스테이지(plan-check self-check 등)와 `direct/quick` 파이프 전체는 **inline 유지** — 분사 오버헤드가 실작업보다 크면 손해(손익 임계는 SD-OPEN-1 pilot 계측).
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

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

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
- `--intensity`: 발화 risk/범위로 추론 (`direct|quick|standard|strong|thorough|adversarial`). stage graph 선택자.
- `--qa`: assurance override. 기본은 선택된 intensity를 따른다 (`quick`→quick, `standard|strong`→standard, `thorough`→thorough, `adversarial`→adversarial). debug는 보통 `standard` 이상으로 충분하며, 명시 adversarial만 상향.
- `--from`: 자동 추론 (`pipeline_state.yaml` 발견 시 마지막 성공 stage 다음부터)
- `--user-refine`: **off** (글로벌 §2 — "사용자 검토 끼워" / "memo 추가하게 멈춰줘" 같은 명시 신호 있을 때만 켬)

### Override 1순위 — autopilot 우회

- 작은 작업 (한 줄 수정·rename·cleanup) — `Agent(개발팀)` 직접 호출 또는 직접 Edit
- 단발성 코드 리뷰 — `Agent(품질관리팀)` 직접 호출
- `/autopilot-code <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `<agent-home>/README.md` 운영 룰 안내로 자동 반영.
