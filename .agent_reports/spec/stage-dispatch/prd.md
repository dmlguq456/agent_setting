# stage-dispatch — Spec (PRD)

> mode: **library + cli** (하네스 인프라 — 스테이지 분사 계약 문서 + dispatch wrapper·jobs.log·fleet 관제) · 작성 2026-07-10 · v1
> 컴포넌트: `agent_setting` repo 의 **autopilot 파이프 디스패치 토폴로지 개정** — 각 sub-skill 스테이지(code-plan / code-execute / code-test / code-report)를 `standard+` 에서 **기본으로 별개 headless 세션**으로 분사하는 계약. 기존 `spec/prd.md`(Unified Memory System)·`spec/harness-layer-sync/`·`spec/dispatch-profiles/`·`spec/agent-fleet-dashboard/` 와 무관한 독립 청사진. 이 폴더(`spec/stage-dispatch/`)가 자체 SoT.
> 입력(1순위 근거):
> - **사용자 결정 (2026-07-10 확정)**: "스킬 단위의 처리가 분사해서 할 것을 기본 지침으로 했으면 한다. 어차피 산출물 기반 소통인데." — 입도 = sub-skill 스테이지 단위, 적용 = `standard+`, 이는 2026-07-06 depth 재설계 기본값의 명시적 반전.
> - research `.agent_reports/research/cross-platform-agent-frameworks/` — `analysis_summary.md` §4-(8)(fresh-context-per-agent + file-state 지배 관용구), `cards/gsd.md`(fresh-context subagent per stage·`.planning/` file-state·two-stage routing·size-budget), `06_implementation.md`(파일-복제 회피·parity 정직성).
> - 운영 실증 (2026-07-10, 이 결정의 직접 계기): ① in-session Task 서브에이전트 = jobs.log 미등록 → fleet 관제에 스테이지 진행 불가시 ② in-session 서브에이전트는 hook ceremony(가드·spec 게이트) 미수령 ③ owner 단일 세션 = 스테이지 누적 컨텍스트 비대.
> - 현행 계약 실측 (2026-07-10, 본 워크트리): `core/OPERATIONS.md §5.10`·`§5.8`, `core/CONVENTIONS.md §1`·`§2`, `core/WORKFLOW.md §1.1`·`§5`, `core/DESIGN_PRINCIPLES.md §8`, `skills/autopilot-code/references/{dev-pipeline,context-and-guards}.md` + sub-skills, `adapters/claude/bin/dispatch-headless.py`, `adapters/{claude,codex,opencode}` bootstrap §0(C)/AGENTS.md.
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). 지침 파일(core/adapters/skills) 자체는 본 spec 이 수정하지 않는다 — 방향만 확정.

## 0. 한 줄

**autopilot 파이프의 각 sub-skill 스테이지(code-plan·code-execute·code-test·code-report)를 `standard+` 에서 기본으로 별개 headless 세션에 분사하고, 세션 간 소통은 오직 산출물 파일로 한다.** depth-1 owner 는 스테이지 산출물 경로를 계약으로 넘기고 게이트 판단만 자기 컨텍스트에서 쥔 **얇은 conductor** 가 된다. `direct/quick` 은 현행 inline 유지. 이는 2026-07-06 "owner 단일 세션 + in-session 팀" 재설계의 **기본값을 반전**하는 결정이다.

## 0.5 설계 원칙 — 산출물 기반 소통 (file-only handoff) ★ cross-cutting

**스테이지 세션은 대화 컨텍스트를 주고받지 않는다. 입력은 앞 스테이지 산출물 파일 경로 + 자기 sub-skill 계약뿐이고, 출력도 산출물 파일뿐이다. 스테이지의 진실은 파일에만 있다.**

- **왜 (사용자 결정)**: "어차피 산출물 기반 소통인데" — 파이프는 이미 `plan/plan.md`·`checklist.md`·`dev_logs/`·`test_logs/`·`final_report.md` 로 스테이지 상태를 파일에 적재한다(§2.1). 대화 컨텍스트로 상태를 추가 운반하는 것은 이 파일 계약과 중복이고, 그 중복이 owner 컨텍스트 비대(운영 실증 ③)의 원천이다.
- **왜 (research §4-(8))**: "fresh context per agent + file 로 복원" 이 context rot 방지의 **지배적 관용구** — "대부분 DB 없이 git-committable Markdown/JSON 파일(GSD `.planning/`, spec-kit `specs/`, BMAD `_bmad/`, Agent OS `.agent-os/`)로 세션·`/clear` 경계를 넘는다"(`analysis_summary.md` §4-(8)). GSD 는 이를 설계원칙으로 명문화: "모든 heavy work(research/plan/execute)를 fresh 200K subagent 에서 실행, main 세션은 lean(30–40%) 유지 → context rot 방지"(`cards/gsd.md` §4), 상태는 "`.planning/` 의 `STATE.md`·`CONTEXT.md` 등 구조화 산출물이 세션·`/clear` 경계를 넘어 컨텍스트를 복원"(§4). 우리가 새로 만드는 게 아니라 **이미 검증된 관용구를 스테이지 입도로 채택**한다.
- **왜 (core 원칙 §8)**: `DESIGN_PRINCIPLES.md §8`(Performance Preservation)은 이미 "결과 흐름: file 통해 (verdict 만 token)" 를 명문화했다. 본 spec 은 이 원칙의 적용 범위를 _in-session agent→orchestrator_ 에서 _headless 스테이지 세션→conductor_ 로 확장할 뿐이다 — 원칙 신설이 아니라 승격.
- **결정론-first 연결**(§0.5 DESIGN_PRINCIPLES): 산출물 = 유일 인터페이스이면 "무엇이 넘어갔나"가 파일로 결정론적으로 재현·감사 가능하다. 대화 컨텍스트 전달은 재현 불가·drift 원천이므로 금지.
- **제약 (계약의 완결성 의무)**: 산출물이 다음 스테이지에 필요한 컨텍스트를 **완전히** 담아야 한다. 담지 못하면 그것은 스테이지 경계가 잘못됐거나 산출물 스키마가 빈약하다는 신호 — 대화 컨텍스트로 때우지 말고 산출물 계약을 보강한다(§4). 이 의무가 현행 금지 조항의 우려(§2.2 "상태 재발굴")를 규칙으로 흡수한다.

## 1. 배경 — 사용자 결정 + 운영 실증 + research 종합

사용자 문제의식: **파이프의 스킬 단위 처리를 분사하는 것을 기본 지침으로.** 근거는 "어차피 산출물 기반 소통"이라는 관찰 — 스테이지가 이미 파일로 상태를 넘기므로 세션을 쪼개도 잃을 게 없고, 오히려 관제·격리·컨텍스트에서 이득이라는 판단.

이 결정의 직접 계기 = 2026-07-10 운영에서 드러난 세 실증:

| # | 현행 in-session 팀 모델의 실측 문제 | 근거 |
|---|---|---|
| ① | **fleet 관제 불가시** — in-session Task 서브에이전트(기획팀/개발팀/품질관리팀)는 `.dispatch/jobs.log` 에 등록되지 않아, fleet 대시보드에 스테이지별 진행·liveness 가 뜨지 않는다. owner 세션 한 줄만 보인다. | OPERATIONS §5.10 job 레지스트리 계약(분사만 등록) + 운영 실측 |
| ② | **hook ceremony 미수령** — in-session nested subagent 는 "hook 발화·skill·worktree·jobs.log·statusline 풀 ceremony 격리를 못 받음"(adapter bootstrap §0(C) 명문). 즉 스테이지가 artifact-guard·spec-read 게이트·mode 신호를 온전히 통과하지 않는다. | `adapters/claude/CLAUDE.md §0(C)` |
| ③ | **owner 컨텍스트 비대** — owner 단일 세션이 plan→execute→test→report 를 통째로 들고 가면 각 스테이지 산출물 본문이 대화에 누적되어 컨텍스트가 부풀고, 2026-07-06 재설계가 막으려던 바로 그 팽창이 스테이지 누적으로 재발한다. | OPERATIONS §5.10 재설계 narrative + DESIGN_PRINCIPLES §8 |

research 종합: 거의 모든 multi-agent 프레임워크가 "fresh-context per agent + file-state" 로 세션 경계를 넘는다(§4-(8)). GSD 는 phase loop(Discuss→Plan→Execute→Verify→Ship)를 milestone 당 반복하며 각 heavy work 를 fresh subagent 로 돌리고 상태는 `.planning/` 파일이 복원한다(`cards/gsd.md` §4·§5). Superpowers 는 7단계 순차 gate 를 "design doc / plan / git worktree 로 분산"한다(`analysis_summary.md` §2). 즉 **"스테이지 = fresh 세션"과 "file 기반 handoff"는 각각 널리 실증**됐고, 이 둘의 결합이 §4-(8)이 말하는 지배 관용구다. 우리의 스테이지 입도 분사는 이 관용구를 우리 파이프에 이식하는 것.

## 2. 현행 계약 실측 (2026-07-10, 본 워크트리)

### 2.1 스테이지 파이프는 이미 파일로 상태를 넘긴다 (분사의 전제가 이미 성립)

`standard+` dev 파이프의 스테이지·산출물(전부 `<artifact-root>/plans/<date>_<slug>/` 하위):

| Stage(skill) | 읽는 입력 산출물 | 쓰는 출력 산출물 |
|---|---|---|
| **code-plan** | task 설명(args), 기존 `plans/` 조회 | `plan/plan.md`(영문 primary)·`plan/plan_ko.md`(한국어 mirror), `_internal/plan_reviews/round_{N}.md` |
| **code-execute** | `plan/plan.md` | `plan/checklist.md`(`Safety commit:` 헤더 + Phase/Step 상태), `dev_logs/step_*.md`, `_internal/dev_reviews/phase_{NN}.md`, plan frontmatter `status` |
| **code-test** | `plan/plan.md` verification 섹션 + `plan/checklist.md` | `test_logs/test_report.md`(Level N), `_internal/test_reviews/` |
| **code-report** | plan·checklist·dev_logs·test_logs·`_internal/*_reviews/`·`pipeline_summary.md` | `final_report.md`, `analysis_project/code/*.md` 보강 |

⇒ 스테이지 인터페이스는 **이미 파일**이다. 세션을 쪼개도 잃는 것은 대화 컨텍스트뿐이고, 그건 §0.5 대로 잃어도 되는(오히려 잃어야 하는) 것.

### 2.2 현행 dispatch 모델 = in-session 팀 + **스테이지 분사 명시 금지**

현행 autopilot-code 는 각 sub-skill 을 **owner 세션에서 Skill tool 로 인라인 호출**하고, 각 sub-skill 이 다시 **in-session Task subagent** 로 위임한다:

- `dev-pipeline.md:2`: "You (the main Claude) orchestrate by invoking each skill directly via the Skill tool."
- Step 1/3/4/5: "invoke Skill: `code-plan`/`code-execute`/`code-test`/`code-report` …"
- sub-skill 내부: code-plan→"Invoke the **plan-team** (기획팀) agent as a subagent", code-execute→"Delegate implementation to the dev-team (개발팀) agent", code-test→"Invoke the **품질관리팀** agent in **test mode**", code-report→"Invoke the **qa-team** (품질관리팀) agent as fast writer".

그리고 **스테이지 단위 headless 분사를 명시적으로 금지**한다 (drill 재발 방지 항목, `context-and-guards.md:51`):

> "worktree 확보 _즉시_ 그 안으로 `claude -p` 헤드리스 분사 — plan 호출부터 report 까지 **통째로 한 세션**. … 파이프 스테이지(code-plan·refine·execute)를 main 과 헤드리스로 **쪼개면 헤드리스가 상태 재발굴 + 연속성 상실 = worst of both — 금지.**"

adapter bootstrap §0(C) 도 동형: "풀 ceremony 가 필요하면 worktree 안 `claude -p` headless 분사, 이때 … **분사는 main 전용·깊이 1**".

**본 spec 이 반전하는 정확한 지점**: 위 금지 조항(전체 1세션 강제 + 스테이지 분리 금지)과 "스테이지 = 인라인 Skill" 계약. 반전의 정당성 = §0.5(산출물이 상태를 완전히 담으면 "상태 재발굴"은 파일 로드 비용으로 수렴, "연속성 상실"은 발생하지 않음 — 연속성의 매체가 대화가 아니라 파일이므로). 단 현행 우려는 실재하므로 §4 계약 완결성 의무 + §8 마이크로-스테이지 inline 경계로 규칙화해 흡수한다.

### 2.3 depth 모델 (현행) — 반전이 depth 예산 안에 든다

`OPERATIONS.md §5.10`·`CONVENTIONS.md §1`: depth 0 = 사용자-facing main, depth 1 = capability owner worker(autopilot-code 전체 파이프), depth 2 = `standard+` owner 가 여는 bounded sub-worker(planner/verifier/adversary). **depth 3+ 금지.** 현행 depth-2 는 _리뷰 보조 역할_ 이고 파이프 스테이지 자체는 depth-1 세션 안 in-session 팀이 실행.

⇒ 본 spec 은 **depth-2 의 용도를 리뷰 보조 → 파이프 스테이지 자체**로 확장한다. depth 예산은 그대로: main(0) → conductor(1) → 스테이지 세션(2). 스테이지 세션은 depth-3 headless 를 열지 않고 내부는 in-session 팀만 → depth ≤ 2 불변 유지.

### 2.4 dispatch wrapper 는 이미 스테이지 분사를 받을 수 있다 (증분 확인)

`adapters/claude/bin/dispatch-headless.py` 실측 — 현행 계약이 이미 스테이지 분사의 골격을 지원:

- 인자: `--depth {1,2}`, `--parent <slug>`, `--worker-role <자유문자열>`, `--owner <capability>`, `--capability/--mode/--qa/--intensity`, model 선택(`--model-role | --model+--effort | --inherit-model-settings` 셋 중 필수).
- 게이트: `depth==2` 인데 `--parent` 없으면 `missing-dispatch-parent`(64), `depth==2` + intensity ∈ {direct,quick} → `invalid-depth-two-intensity`(64), `depth 3+` 불가.
- jobs.log: launch _전_ append, `fcntl.flock` 로 `{jobs}.lock` 직렬화, pipe = `capability=…,mode=…,qa=…,intensity=…,depth=…,harness=claude` + 조건부 `parent=/worker_role=/owner=/model_*`.
- depth contract 를 자식 프롬프트에 주입: "depth 1 … should open bounded depth-2 sub-workers for separable standard+ work; … depth 3+ is forbidden."

⇒ **wrapper 는 스테이지 분사를 위해 재작성이 필요없다.** depth=2 + parent=owner-slug + worker_role=<sub-skill> 로 이미 호출 가능. 필요한 것은 (a) conductor 가 이 호출을 스테이지마다 도는 오케스트레이션 계약(문서) (b) 편의를 위한 stage-dispatch helper 판단(§9·§12) 뿐 — 신규 시스템 아님.

## 3. 기본 토폴로지 — 얇은 conductor + 스테이지 headless 세션 (채택)

> **SD-1**: depth-1 owner(autopilot-code)는 **얇은 conductor**. 실작업(plan 작성·구현·검증·보고)은 sub-skill 별 depth-2 headless 세션. conductor 는 스테이지 산출물 경로를 다음 스테이지에 계약으로 넘기고, **게이트 판단(plan-check verdict·CONFIRM 자리·retry 분기)만** 자기 컨텍스트에서 쥔다.

- **conductor 가 쥐는 것 (얇음의 정의)**: (a) 현재 사이클 slug·산출물 루트 경로 (b) 각 스테이지 verdict/status(plan frontmatter `status`, `test_report.md` Level 결과) (c) 게이트 분기 결정(진행/refine/back-jump/중단, retry). **스테이지 산출물 _본문_ 은 읽지 않는다** — verdict/status 만 파일에서 읽어 판단(DESIGN_PRINCIPLES §8 "verdict 만 token").
- **스테이지 세션이 쥐는 것**: 자기 sub-skill 계약 + 입력 산출물 경로. 내부는 현행 그대로 in-session 팀(기획팀/개발팀/품질관리팀)으로 실행 — 스테이지 세션 안에서는 아무것도 안 바뀐다.
- **왜 conductor 가 depth-1 인가**: 스테이지를 depth-2(parent=conductor)로 두려면 parent 가 depth-1 이어야 한다(§2.4 wrapper 게이트). 따라서 main(0)이 autopilot-code conductor 를 depth-1 로 분사(현행 "풀 ceremony" 자리)하고, conductor 가 스테이지를 depth-2 로 분사. main 은 정찰·conductor 분사·수확만(현행 §5.10 역할 불변).
- **conductor 도 얇으므로 main 부담 0 유지**: 재설계가 노린 "main lean"은 그대로 — 오히려 conductor 자신도 스테이지 본문을 안 읽어 lean 을 한 겹 더 얻는다.

## 4. 인터페이스 = 산출물 파일만 (채택)

> **SD-2**: 스테이지 세션은 (a) 입력 산출물 경로 (b) 자기 sub-skill 계약만 받고, 출력도 산출물 파일(§2.1 표). **세션 간 대화 컨텍스트 전달 금지** — §0.5 "산출물 기반 소통"의 명문화.

- **분사 프롬프트 계약**: conductor 가 스테이지를 분사할 때 프롬프트에 넣는 것 = {sub-skill 이름, 입력 산출물 절대경로, 출력 산출물 계약(어디에 무엇을 쓸지), qa/intensity, slug}. plan 본문·앞 스테이지 대화 요약을 프롬프트에 복사하지 않는다 — 스테이지가 파일을 직접 읽는다.
- **계약 완결성 의무(§0.5)**: 산출물이 다음 스테이지 입력으로 완전해야 한다. 예 — code-execute 는 `plan/plan.md` 만으로 구현 가능해야 하고(현행 이미 성립, §2.1), code-test 는 `plan.md` verification 섹션 + `checklist.md` 만으로 검증 가능해야 한다. 불완전하면 산출물 스키마를 보강(구현 phase 에서 sub-skill 계약 갱신), 대화로 때우지 않는다.
- **retry 의 파일 의미론**: 현행 test 실패 시 `plan/plan_ko.md` 에 `<!-- memo: [테스트 실패] … -->` 주입 + checklist 리셋 후 재진입. 이 memo-주입이 곧 파일 기반 handoff — conductor 는 test verdict(fail)만 보고 code-refine/code-plan 스테이지를 재분사하며, 실패 상세는 `test_logs/`·memo 가 운반. 스테이지 재분사는 **기존 산출물 재사용**(SD-6)으로 처음부터 다시 하지 않는다.

## 5. 레지스트리·관제 (채택)

> **SD-3**: 스테이지 세션은 `.dispatch/jobs.log` 에 `depth=2, parent=<conductor-slug>, worker_role=<sub-skill>, owner=autopilot-code` 로 등록 → fleet 에 **스테이지별 row**. stealth-death 가드는 conductor 책임.

- **row 형식**(OPERATIONS §5.10 하드 계약 준수): status 어휘 `open`/`running`→`done`, pipe metadata 쉼표 구분·공백 없음. 예: `capability=code-execute,mode=dev,qa=standard,intensity=standard,depth=2,harness=claude,parent=<conductor-slug>,parent_sid=<sid>,worker_role=code-execute,owner=autopilot-code`.
- **worker_role = sub-skill 이름**: `code-plan`/`code-execute`/`code-test`/`code-report`(+phase 분할 시 `code-execute:phase-A` 류 접미). wrapper 는 worker_role 을 자유문자열로 받으므로(§2.4) enum 확장 불요 — 다만 fleet collector 가 스테이지 row 를 사람이 읽는 라벨로 표시하도록 관제 표면(§9 fleet)에서 인지.
- **관제 이득(운영 실증 ① 해소)**: 이제 fleet 에 plan→execute→test→report 각 row 가 뜨고 liveness·stage 진행이 라이브로 보인다. 분사 직후 fleet 한 줄 안내(§5.10)는 conductor 가 첫 스테이지 분사 시 1회.
- **stealth-death 가드(§5.10 필수)**: conductor 는 각 스테이지 세션 대기 자리에서 완료 알림만 믿지 말고 `utilities/dispatch-liveness.sh` 로 transcript-mtime liveness 점검(SUSPECT/DEAD → 진단→수확/재분사). 스테이지 세션이 여럿이므로 이 가드가 더 중요.
- **hook ceremony 수령(운영 실증 ② 해소)**: 스테이지가 독립 headless 세션이므로 artifact-guard·spec-read·mode 신호 등 풀 ceremony 를 정상 통과(§0(C)가 in-session 에 불가라던 바로 그 격리를 획득).

## 6. depth-2 계약 개정 — 스테이지-워커 클래스 (채택)

> **SD-4**: 현행 "depth-2 worker 기본 read-only, 구현 worker 만 제한 write"(§5.10 ④)를 **스테이지-워커 클래스별 write 소유**로 재정의. depth 3+ 금지 유지 — 스테이지 세션은 또 headless 를 열지 않고 내부는 in-session 팀만.

현행 depth-2 는 리뷰 보조라 read-only 기본이 맞았다. 스테이지 세션은 파이프의 실작업이므로 write 소유를 클래스로 정의:

| 스테이지-워커 클래스 | write 소유 범위 | 근거 |
|---|---|---|
| **code-plan** | `plans/<slug>/plan/` (plan.md·plan_ko.md) + `_internal/plan_reviews/` | plan 산출물만 |
| **code-execute** | **소스 코드 write 소유** + `plans/<slug>/{plan/checklist.md,dev_logs/,_internal/dev_reviews/}` + plan frontmatter status | 유일한 소스 mutation 스테이지 |
| **code-test** | `plans/<slug>/{test_logs/,_internal/test_reviews/}` (소스 read-only) | 검증은 관찰, 소스 불변 |
| **code-report** | `plans/<slug>/final_report.md` + `analysis_project/code/*.md` + `pipeline_summary.md`(lock 경유) | 보고·이력 |

- **read-only 기본의 예외로서 스테이지 write 를 명시**: depth-2 리뷰 워커(planner/verifier/adversary)는 여전히 read-only 기본. 스테이지-워커는 위 표의 클래스 write 만 소유 — 클래스 밖 write 는 계약 위반.
- **소스 mutation = code-execute 단일**: 여러 스테이지가 동시에 소스를 쓰지 않는다. execute 만 소스 소유이므로 스테이지 간 소스 경합 없음. plan/test/report 는 `plans/<slug>/` 하위 경로-분리라 상호 비경합(§8 lock 참조).
- **depth 3+ 금지 유지**: 스테이지 세션(depth 2)은 dispatch-headless.py 를 재호출하지 않는다(wrapper 가 depth 3 자체를 막음, §2.4). 내부 병렬(예: execute 의 독립 step 병렬 개발팀)은 in-session Task 팀으로 — depth 로 세지 않음.

## 7. 모델 라우팅 (채택)

> **SD-5**: 스테이지별 model role 은 CONVENTIONS §2 매핑을 conductor 가 스테이지 분사 시 **명시**(§5.10 ⑦ 그대로 — wrapper 는 기본 모델 암묵 선택 금지).

CONVENTIONS §2.3 role 매트릭스 → 스테이지 매핑:

| 스테이지 | portable model role | 근거 |
|---|---|---|
| code-plan | **deep maker** (기획팀) | §2.3 기획팀 = deep maker |
| code-execute | **fast implementer** default, 복잡 설계 시 deep maker 상향 | §2.3 개발팀 = fast implementer default |
| code-test | **variable reviewer/verifier** (품질관리팀) — qa/intensity 가 fast/deep 결정 | §2.3 품질관리팀 가변 |
| code-report | **fast writer** (품질관리팀 report) | §2.3 / §2.1 fast writer |

- conductor 는 스테이지마다 `--model-role <role>` 또는 concrete `--model+--effort` 를 명시. dispatch-headless.py `role_map`: deep maker→(opus,high), fast implementer→(sonnet,medium), fast writer→(sonnet,low) 등(§2.4 실측)이 재현.
- **작업 난이도별 상향은 conductor 판단**(§5.10 ⑦): 어려운 plan·복잡 API 는 conductor 가 deep maker/opus 로 상향, 단순 스테이지는 하향. wrapper 가 임의 기본 선택하거나 interactive session model 암묵 상속 금지.

## 8. 비용·안전 가드레일 (채택)

> **SD-6**: 동시 상한 5 안 동시성 계산 / 마이크로-스테이지 inline 경계 / 스테이지 실패 재시도·재개 의미론 / §5.8 lock 범위를 명문화.

- **동시 상한 5 안 동시성**(§5.10 ⑤): 스테이지 파이프는 **순차**(plan→execute→test→report)라 한 conductor 는 보통 동시 1 스테이지만 점유 — conductor(1) + 활성 스테이지(1) = 2. 여러 요청을 병렬 처리하면 conductor 가 여럿이 되므로 상한 계산은 **`Σ(활성 conductor + 각 conductor 의 활성 스테이지)` ≤ 5**. code-execute 내부 병렬 개발팀은 in-session(depth 미증가)이라 상한에 안 셈. 초과 예상 시 conductor 는 스테이지 분사를 큐잉(다음 스테이지는 앞 스테이지 done 후이므로 자연 직렬).
- **마이크로-스테이지 inline 경계**(현행 우려 §2.2 흡수): 분사 오버헤드(세션 startup·산출물 로드)가 스테이지 실작업보다 크면 분사가 손해다. **경계 규칙**: 산출물을 새로 쓰지 않거나 한 줄 verdict 만 내는 스테이지(예: plan-check self-check, `direct/quick` 파이프 전체, ≤3 step plan 의 통합 리뷰)는 **inline 유지**. 산출물을 실제로 생성·mutation 하는 스테이지(plan 작성·execute·test·report)만 분사. 정확한 손익 임계(어느 크기부터 분사가 이득인가)는 **pilot 계측으로 캘리브레이트**(§12, SD-OPEN-1) — research 도 per-stage dispatch 비용을 수치화하지 않았으므로(digest 주의) 추측하지 말고 측정.
- **실패·재개 의미론(기존 산출물 재사용)**: 스테이지 실패 시 conductor 는 `--from <stage>` 로 **그 스테이지만 재분사**, 앞 스테이지 산출물은 재사용(재생성 금지). test 실패 retry 는 §4 memo-주입 경로(최대 1회 pipeline-level retry, `qa=quick` 은 retry 없음 — 현행 유지). 스테이지 세션이 hang/crash(§5 stealth-death)면 conductor 가 진단 후 동일 스테이지 재분사 — 부분 산출물이 있으면 이어쓰기, 없으면 처음부터 그 스테이지만.
- **§5.8 pipeline lock 범위**: lock 은 `spec/prd.md`·`spec/pipeline_state.yaml`·`spec/pipeline_summary.md` _공유 단일파일 쓰기_ 만 보호. 스테이지 산출물은 전부 `plans/<slug>/` 경로-분리라 **비경합 → lock 불요**. 예외 = **code-report 가 `pipeline_summary.md`(공유 단일파일)를 쓰는 자리만 lock acquire**(현행 code-report 계약과 동일). 즉 스테이지 분사가 lock 경합을 새로 만들지 않는다.

## 9. 영향 표면 목록 (구현 phase 에서 갱신 — 현행 문구 → 개정 방향)

> **SD-7**: 아래 표가 구현(autopilot-code) 시 묶음 갱신할 자리. 각 surface = {현행 문구, 개정 방향}. 실제 문구 편집은 소유 스킬(core-first) 경유 별도 — 본 spec 은 방향만 확정.

| # | Surface | 현행 문구(요지) | 개정 방향 |
|---|---|---|---|
| 1 | `OPERATIONS.md §5.10 ③`(depth 모델 narrative) | "depth 2 는 `standard+` owner-worker pipeline 의 기본 도구 … 단일 역할 worker(verifier/planner/…)" | depth-2 용도에 **파이프 스테이지 워커 클래스** 추가(리뷰 보조와 병기). 스테이지 = 기본 분사(`standard+`) 명문화. |
| 2 | `OPERATIONS.md §5.10 ④`(depth-2 write 계약) | "depth 2 worker 는 기본 read-only, 구현 worker 만 제한 write" | **스테이지-워커 클래스별 write 소유**(§6 표)로 재정의. 리뷰 워커 read-only 기본은 유지. |
| 3 | `WORKFLOW.md §1.1`(intensity routing 표) | `standard`: "depth-1 owner should open bounded depth-2 verifier/planner work" | `standard+` 행에 "**스테이지 분사 기본**(plan/execute/test/report 각 headless)" 추가. `direct/quick` = inline 명시(현행 유지). |
| 4 | `WORKFLOW.md §5`(entry→서브에이전트 분기) | "autopilot-code: 기획팀(plan)+개발팀(execute)+품질관리팀 … (in-session)" | 각 스테이지가 **headless 세션(내부에 그 팀)** 임을 명시 — 팀은 스테이지 세션 _안_ 에서 실행. |
| 5 | `CONVENTIONS.md §1`(stage graph Dispatch policy 열) | `standard`: "depth-1 owner with bounded depth-2 sub-workers when useful" | Dispatch policy 에 **스테이지 = depth-2 headless 기본**(standard+) 반영. depth 계약(§1 line 46)에 스테이지-워커 클래스 추가. |
| 6 | `DESIGN_PRINCIPLES.md §8`(Performance Preservation) | "결과 흐름: file 통해 (verdict 만 token)" | 적용 범위를 **headless 스테이지 세션→conductor** 까지 확장 명시(원칙 승격, §0.5). 2026-07-06 재설계 기본값 반전을 이력에 기록. |
| 7 | `skills/autopilot-code/references/context-and-guards.md:51` | "파이프 스테이지를 헤드리스로 쪼개면 worst of both — **금지**" | **금지 해제 → 기본 권장**으로 반전. "산출물이 상태를 완전히 담으므로 재발굴=파일로드, 연속성=파일 매체"로 우려 해소 근거 병기(§2.2·§0.5). |
| 8 | `skills/autopilot-code/references/dev-pipeline.md`(Step 1/3/4/5) | "invoke Skill: `code-plan/…` (인라인)" | `standard+`: "**dispatch-headless 로 스테이지 분사**(depth=2,parent=conductor,worker_role=<skill>)" / `direct/quick`: 인라인 유지. |
| 9 | sub-skills(code-plan/execute/test/report) SKILL.md | "orchestrator 가 Skill 로 호출 … in-session 팀 위임" | 스테이지가 **독립 세션 진입점**으로도 동작하도록 입력=산출물 경로 계약 명문화(§4 완결성). 팀 위임은 세션 _안_ 그대로. |
| 10 | `adapters/claude/CLAUDE.md §0(C)` | "분사는 main 전용·깊이 1" / "in-session nested 는 ceremony 격리 못 받음" | "**conductor(depth-1)가 스테이지를 depth-2 로 분사**" 추가 — 깊이 1 전용 문구를 깊이 2 스테이지까지 확장. ceremony 격리 문구는 유지(오히려 분사 정당화). |
| 11 | `adapters/codex/AGENTS.md` · `adapters/opencode/AGENTS.md`(동형) | headless dispatch 계약 "depth 1, or depth 2 by depth-1 owner under standard+" | 동일 개정 — 스테이지 분사를 depth-2 정규 용법으로 병기. 3어댑터 parity 유지(codex/opencode preflight dispatch 도 이미 depth=2/parent 지원). |
| 12 | `adapters/claude/bin/dispatch-headless.py`(+codex/opencode preflight dispatch) | depth=2/parent/worker_role 이미 지원(§2.4) | **재작성 불요**. 판단: (a) conductor 편의용 **stage-dispatch helper**(스테이지 순서·경로 계약을 캡슐화) 신설 여부 (b) worker_role 표준값 문서화. helper 는 pilot 후 필요성 판정. |
| 13 | fleet 관제(`tools/fleet`) | in-session 서브에이전트 미표시 | 스테이지 row(worker_role 라벨)를 사람이 읽는 stage 진행으로 표시(§5). collector 는 이미 `open|running` 파싱 — 표시 라벨만. |
| 14 | drill 케이스 | 스테이지 분사 회귀 없음 | **스테이지 분사 회귀 케이스 신설**(Phase 2): fleet 에 스테이지 row 뜨는지·산출물 정상·depth≤2 강제. |

## 10. 기각·비채택 (근거와 함께)

| 항목 | 판정 | 근거 |
|---|---|---|
| **owner 단일 세션 + in-session 팀 유지**(2026-07-06 기본값) | **반전(비채택)** | 운영 실증 ①②③(관제 불가시·ceremony 미수령·컨텍스트 비대). 단 `direct/quick` 은 이 모델 유지(분사 오버헤드가 이득 초과). |
| **스테이지 세션도 depth-3 headless 를 열기** | **기각** | depth 3+ 금지 불변(§2.3·§6). 스테이지 내부 병렬은 in-session 팀으로 충분. wrapper 가 depth 3 자체를 차단. |
| **대화 컨텍스트 요약을 프롬프트로 운반**(하이브리드) | **기각** | §0.5 산출물 기반 소통 위반 — 재현 불가·drift 원천. 산출물 불완전은 스키마 보강으로 해결(§4). |
| **모든 intensity 에서 스테이지 분사** | **범위 한정** | `direct/quick` 은 inline — 마이크로 작업에 분사 오버헤드는 손해(§8). 적용은 `standard+` 만(사용자 결정). |
| **per-stage dispatch 비용을 spec 에서 수치 단정** | **미결로 이관** | research 가 per-stage dispatch cost 를 수치화 안 함(digest 주의). 손익 임계는 pilot 계측(SD-OPEN-1) — 추측 금지. |

## 11. Module 구조 (확정 — 코드 생성은 autopilot-code)

```
adapters/claude/bin/dispatch-headless.py   # (증분/무변) depth=2·parent·worker_role 이미 지원 — helper 신설은 pilot 후 판정
adapters/{codex,opencode}/bin/preflight.sh # (증분/무변) dispatch 서브커맨드 동형 — parity 문구만 개정
skills/autopilot-code/references/
  dev-pipeline.md            # 스테이지 = standard+ 분사 / direct·quick 인라인 (§9-8)
  context-and-guards.md      # 스테이지 분사 금지 → 기본 권장 반전 (§9-7)
skills/{code-plan,code-execute,code-test,code-report}/SKILL.md
                             # 독립 세션 진입점 계약(입력=산출물 경로) 명문화 (§9-9)
core/OPERATIONS.md §5.10     # depth-2 스테이지-워커 클래스 + write 소유 (§9-1,2)
core/WORKFLOW.md §1.1·§5     # 스테이지 분사 기본 반영 (§9-3,4)
core/CONVENTIONS.md §1       # Dispatch policy·depth 계약 (§9-5)
core/DESIGN_PRINCIPLES.md §8 # 산출물 기반 소통 승격·재설계 반전 이력 (§9-6)
adapters/{claude,codex,opencode} bootstrap §0(C)   # 깊이 1 전용 → 스테이지 depth-2 확장 (§9-10,11)
tools/fleet                  # 스테이지 row 표시 라벨 (§9-13)
loops/drill                  # 스테이지 분사 회귀 케이스 (§9-14, Phase 2)
```

- 신규 코드 최소화 — wrapper 재작성 없음(§2.4). 대부분 계약 문서(core·bootstrap·SKILL) 개정 + 얇은 conductor 오케스트레이션 문구 + (판정 시) stage-dispatch helper.
- 지침 파일 문구 변경은 소유 스킬(core-first) 경유 별도 — 본 spec 은 _구조_ 만 확정.

## 12. Next — 구현 phase 분할 (autopilot-code, 본 v1 입력)

`/autopilot-code --mode dev "stage-dispatch 구현"` (worktree 브랜치).

### Phase 1 — 계약 문서 + wrapper 증분 + autopilot-code pilot (저위험, 검증 우선)
1. **계약 문서 개정** — core(OPERATIONS §5.10 ③④·CONVENTIONS §1·WORKFLOW §1.1·§5·DESIGN_PRINCIPLES §8) + adapter bootstrap §0(C) 3어댑터 동형(§9-1~6,10,11). context-and-guards.md:51 금지 반전(§9-7).
2. **dev-pipeline.md + sub-skills 계약** — 스테이지 분사 오케스트레이션(§9-8,9): conductor 가 스테이지마다 dispatch-headless(depth=2,parent,worker_role) 호출, 입력=산출물 경로.
3. **wrapper 증분** — 재작성 불요 확인 + (필요 판정 시) stage-dispatch helper. worker_role 표준값 문서화(§9-12).
4. **autopilot-code pilot** — code track 한 실제 작업을 스테이지 분사로 1회 완주.

**pilot 성공 기준(계측)**:
- fleet 에 code-plan·code-execute·code-test·code-report **스테이지별 row** 가 뜨고 liveness 가 보인다(운영 실증 ① 해소 증명).
- 각 스테이지 산출물이 §2.1 표대로 정상 생성되고, 스테이지가 앞 산출물만으로(대화 전달 0) 완주(§0.5·§4 완결성 증명).
- depth ≤ 2 강제 확인(스테이지가 depth-3 안 염), §5.8 lock 경합 미발생.
- **토큰/시간 비교 계측** — 동일 작업 in-session(현행) vs 스테이지 분사의 conductor 컨텍스트 크기·총 토큰·wall-clock. 마이크로-스테이지 inline 경계 임계(SD-OPEN-1) 캘리브레이트 데이터.

### Phase 2 — 나머지 autopilot-* 확산 + drill 회귀
5. **확산** — autopilot-draft/research/design 등 다른 autopilot-* 파이프에 스테이지 분사 적용(pilot 성공 기준 통과 후). 각 파이프의 스테이지-워커 클래스·산출물 계약 매핑.
6. **fleet 표시** — 스테이지 row 라벨(§9-13).
7. **drill 케이스** — 스테이지 분사 회귀(§9-14): fleet row·산출물·depth≤2·lock 미경합 자동 검증.

## 13. 결정 목록

- **SD-1**: depth-1 owner = 얇은 conductor, 스테이지(plan/execute/test/report) = depth-2 headless 세션. conductor 는 verdict/게이트만, 스테이지 본문 미독. (§3, 사용자 결정·§5.10 depth)
- **SD-2**: 인터페이스 = 산출물 파일만. 세션 간 대화 컨텍스트 전달 금지. 계약 완결성 의무. (§4·§0.5, 사용자 결정·research §4-(8)·DESIGN_PRINCIPLES §8)
- **SD-3**: 스테이지 세션 = jobs.log `depth=2,parent=<conductor>,worker_role=<sub-skill>,owner=autopilot-code` 등록 → fleet 스테이지 row. stealth-death 가드는 conductor 책임. (§5, §5.10 레지스트리·운영 실증 ①②)
- **SD-4**: depth-2 write 계약을 스테이지-워커 클래스별 소유로 재정의(plan=plan폴더·execute=소스+dev로그·test=test로그·report=report+analysis). depth 3+ 금지 유지. (§6, §5.10 ④ 개정)
- **SD-5**: 스테이지 model role 은 conductor 가 CONVENTIONS §2 매핑으로 명시(wrapper 암묵 선택 금지). (§7, §5.10 ⑦·§2.3)
- **SD-6**: 동시 상한 5 = Σ(conductor+활성 스테이지). 마이크로-스테이지 inline. 실패=스테이지만 재분사(산출물 재사용). lock 은 report 의 pipeline_summary 쓰기만. (§8, §5.10 ⑤·§5.8)
- **SD-7**: 영향 표면 14곳(§9 표) — core·bootstrap·SKILL·wrapper·fleet·drill. 문구 편집은 소유 스킬(core-first) 별도. (§9·§11)
- **SD-8**: 적용 = `standard+` 기본. `direct/quick` = 현행 inline 유지. 2026-07-06 "owner 단일 세션" 기본값의 명시적 반전. (§0·§10, 사용자 결정)
- **SD-9**: wrapper 재작성 불요 — depth=2/parent/worker_role 이미 지원. helper 신설은 pilot 후 판정. (§2.4·§11·§9-12)
- **SD-OPEN-1**(미결 — pilot 계측): 마이크로-스테이지 inline 의 정확한 손익 임계(어느 스테이지 크기부터 분사가 이득). research 가 per-stage cost 미수치화 → 추측 금지, Phase 1 pilot 토큰/시간 계측으로 확정. (§8·§12)

## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간(코드로 강제)**: depth ≤ 2(wrapper 게이트)·jobs.log row 형식·스테이지-워커 write 클래스·lock 범위·model role 명시 — 전부 결정론 가드/wrapper(§2.4). "산출물 기반 소통"의 완결성은 파일 존재로 결정론적 감사.
- **의미 판단 구간(사람/LLM)**: (1) 마이크로-스테이지 inline 경계 임계 — pilot 계측 후 판정(SD-OPEN-1). (2) 스테이지 실패 시 재분사 vs 이어쓰기 판단 — conductor 의 부분 산출물 해석. (3) 산출물 계약이 "완전한가"의 판정 — 스테이지가 대화 없이 완주 가능한지.
- **충돌**: 없음 — 반전의 핵심 우려(현행 "상태 재발굴·연속성 상실")를 §0.5 계약 완결성 의무 + §8 inline 경계로 규칙화해 흡수했다. 우려를 사람 vigilance 로 남기지 않고 "산출물이 상태를 완전히 담는가"라는 검증 가능한 규칙으로 전환한 것이 이 경계 존중. per-stage cost 는 추측으로 규칙화하지 않고 pilot 계측(SD-OPEN-1)으로 미룬 것도 의미↔규칙 경계 존중.
