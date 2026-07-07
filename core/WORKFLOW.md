# Autopilot-* 라우팅 맵 (agent-facing core)

> 메인 에이전트가 _작업 발화 → capability·role 라우팅_ 을 결정할 때 보는 압축 맵. Claude Code 에서는 capability=skill, role=agent 로 어댑팅된다. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙.
>
> 역할 분담: 사용자 향 의미 지도·entry list 는 [`README.md`](../README.md). 정의(QA·model·폴더 컨벤션)는 [`CONVENTIONS.md`](CONVENTIONS.md). 본 문서는 _라우팅 표_ 만 — narrative·호출 예시·비개발자 설명은 중복 회피로 제거(필요 시 README).

---

## 0. 불변식 — 단일 라우터 + 하드 순서 게이트 (우회 불가)

> **본 문서 = 📌tracked 모드 계약.** tracked 프로젝트(`.agent_reports`/`spec` 보유, legacy `.claude_reports` 호환)에서 _반드시 지킬 것_ 의 단일 출처. untracked(adapter toggle surface)면 면제. **읽는 방식 = 지침 기반 on-demand**: adapter status/reminder surface 가 제공하는 `workflow-guard-hook` 모드 신호(📌 따름 / ⚡ 면제)가 anchor 이고, tracked 라우팅이 필요한 자리에서 본 문서를 Read 한다 (hook 주입·eager 로드 아님 — user_profile 과 같은 lazy·이식 가능 패턴). hook 은 instruction 이 못 보는 _런타임 모드_ 만 전달.

본 문서가 **모든 작업 흐름의 단일 라우터**. 모든 발화는 §2 작업-본질 매핑을 먼저 거치고, 직접 처리·플러그인(codex)·빌트인 스킬도 WORKFLOW 가 배치하는 자리에서만 쓴다.

**(a) 하드 순서 게이트** — 산출물은 한 방향으로만, 앞 단계 산출물 없이 다음 단계 진입 금지:

```
[코드]  research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)
[문서]  research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine
```

- **spec 없이 코드 X**: 코드 요청인데 `spec/` 없으면 autopilot-spec 먼저 (throwaway 1 회성만 예외, 반복 시 spec 승격).
- **사전 산출물 없이 spec X**: spec 근거(`research/` 또는 `analysis_project/`) 없으면 autopilot-research/analyze-project 먼저. 낯선 영역·신규 의도일수록 강제.
- **harness 강제**: `artifact-guard.sh` 는 _신규 산출물 생성 순서_ 만 기계 차단 — 신규 spec ← research/analyze, 신규 plan ← spec, 신규 문서 ← research/analyze. 기존 편집·소스 코드는 비차단 (convention + workflow-guard-hook 라우팅 reminder). Adapter untracked toggle 로 우회.

**(b) 동일 스킬 수정 = 버전 트래킹** (convention — `hooks/artifact-guard.sh` 는 _신규 산출물 생성 순서_ 만 기계 강제하고 기존 산출물 _편집_ 은 막지 않는다; 소유 스킬 경유는 `workflow-guard-hook` 라우팅 reminder + 관행. Adapter untracked toggle 면제). 각 산출물은 _그것을 만든 스킬로만_ 수정:

| 산출물 | 유일 수정 경로 | 버전 자리 |
|---|---|---|
| `spec/` 청사진 | autopilot-spec update | `_internal/versions/v{N}/` |
| `plans/` 코드 | autopilot-code | `plans/<date>_<slug>/` |
| `documents/` 문서 | autopilot-draft/refine | `_internal/versions/v{N}/` |
| `experiments/` 실험 | autopilot-lab | `_RUNLOG.md` |
| DB `type=profile` 레코드 | analyze-user / post-it --scope user | 레코드 body 내 changelog |

> 단일 출처 = 본 `WORKFLOW.md` + runtime adapter bootstrap. Claude Code adapter 에서는 `adapters/claude/CLAUDE.md` §0 이 이 라우팅 불변식을 세션 부트스트랩으로 싣는다. 위반 신호: ad-hoc Edit 으로 산출물 직접 수정 / 게이트 건너뛰고 코드부터 / 산출물 만든 스킬 외 경로로 수정.

## 1. 한 화면 청사진 — 4 트랙

```
[연구·실험]   research / analyze-project(code) → autopilot-spec ↻ → autopilot-code ↻ → autopilot-lab ↻
[라이브러리·CLI]  analyze-project → autopilot-spec ↻ → autopilot-code ↻
[문서]        research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine ↻ → autopilot-apply
[앱]          autopilot-spec ↻ → autopilot-design → autopilot-code ↻(앱 mode 자동) → autopilot-ship ↻
```

`↻` = 반복 자리. 사후 공통: `audit`(읽기 전용 점검) · `autopilot-refine`(markdown 정정). cross-project: `analyze-user` · `post-it --scope user`.

## 1.1 Pipeline intensity routing

Autopilot entrypoints choose `intensity` before `--qa`. Intensity selects the stage graph and dispatch depth; `--qa` only overrides assurance rigor inside `plan-check`, selected independent review, and final `verify`.

| Request shape | Default intensity | Routing note |
|---|---|---|
| one-off answer, typo, rename, explicit no-artifact work | `direct` | no plan stage, no plan-check, no durable plan artifact |
| small localized tracked change or doc minor | `quick` | inline micro-plan plus small plan-check; no depth dispatch |
| routine tracked code/doc/spec/design work | `standard` | durable plan/checklist when the capability owns a work cycle |
| important multi-file or risk-bearing work | `strong` | one independent review at the riskiest point, not every stage |
| complex cross-domain or cross-harness work | `thorough` | depth-1 owner may open bounded depth-2 perspective/verifier workers |
| high-stakes, irreversible, security, or external-facing work | `adversarial` | thorough plus explicit adversary/failure-mode/security pass |

Direct work is the only graph with no plan. Every non-`direct` autopilot graph has a `plan-check`, but repeated independent QA after every sub-stage is not the default. See `CONVENTIONS.md §1` for the canonical stage graph.

## 2. 작업 본질 매핑 (발화 → skill)

| 작업 종류 | 사전 (조사·분석) | 신규 의도·청사진 | 자산 작업 (신규·기존) |
|---|---|---|---|
| **문서** (paper / 발표 / 보고서 / proposal / rebuttal) | research(academic·market) + analyze-project(paper·doc) | `autopilot-draft` | `autopilot-refine` |
| **코드** (라이브러리·연구·앱·CLI·API 모두) | research(academic·tech) + analyze-project(code) | **`autopilot-spec`** (mode app/library/api/cli/research/복합/auto) | **`autopilot-code`** (spec mode 별 분기 자동) |
| **실험 prototype** (ML / one-shot) | analyze-project(code) 의 4 종 자료(experiment_conventions·readiness·cleanup·similar_models) | — (spec 없이 빠른 cycle) | **`autopilot-lab`** (반복; 졸업 자리 autopilot-code) |
| **시각 자산 / 디자인** | — | `autopilot-design` (신규 사이클·design-first) | _substantial 시각 결정_(방향·토큰·새 레이아웃·구조)·빌트앱 디자인 진화 → **`autopilot-design`** (실제 앱 렌더 → 토큰 계약 갱신, code 적용). _trivial tweak_(한 끗)만 `autopilot-code` 직접. 토큰=design 단일 계약 ([DESIGN_PRINCIPLES §9](DESIGN_PRINCIPLES.md)) |
| **사용자 프로필** | — | `analyze-user` init | `analyze-user` update |

**직접 처리 경계** — plan/log 안 남는 단발 작업(한 줄 수정·rename·cleanup·단발 리뷰)은 autopilot 우회: `Agent(개발팀)` / 직접 Edit. 추적 필요·산출물 누적 자리만 autopilot. minor vs major 판정은 [`DESIGN_PRINCIPLES.md §4`](DESIGN_PRINCIPLES.md) + 각 skill `--qa quick` tier.

## 3. autopilot-spec mode 5종

| mode | 자리 | scaffold (mode 통일: PRD + skeleton) |
|---|---|---|
| **app** | 사용자 앱 (Next.js/Expo) | + Component·Deployment diagram + create-next-app skeleton |
| **library** | 공개 패키지 (npm·pip·crate) | + pyproject/setup + 공개 API skeleton (ref repo export 구조) |
| **api** | 백엔드 API (UI 없음) | + Component·Deployment diagram + FastAPI/Express router skeleton |
| **cli** | 명령줄 도구 | + argparse/typer entry + 명령 skeleton |
| **research** | 연구·재현성 | + train.py/eval.py/config + model skeleton + **Phase 1.5 ckpt 사전 동작 점검** |
| **복합 / auto** | 다측면 / 자동 추론 | 공통 + mode 별 독립 섹션 / 추론 후 컨펌 |

**Scaffold ref 우선순위**: 내부(similar_models·`--ref`) → 외부(research/{topic}/code_resources) → generic. **컨벤션 prepend**: `analysis_project/code/experiment_conventions.md`(1순위) → `mem profile 07_coding_convention`(2순위, 충돌 시 per-project 우선).

## 4. PRD 묶음 갱신 — spec drift 차단

코드·의도 변경이 spec 영향 자리면 _영향 받는 모든 자리 한 트랜잭션_ 갱신. 매핑 single source = [`CONVENTIONS.md §6.3a`](CONVENTIONS.md).

| 변경 | 영향 자리 |
|---|---|
| endpoint·body·error | api_contract + Component (+옵션 Sequence) |
| DB entity·필드 | data_model + Component(backend) (+옵션 ER) |
| UI flow | ui_flow + Component(frontend) (+옵션 Activity) |
| 외부 service 통합 | api_contract(auth) + Deployment + deploy_record + .env.example |
| 스택 교체 | stack_decision + Component + Deployment |
| 공개 API 변경 [library] | 공개 API + 사용 예시 + semver 영향 + Component(module dep) |
| CLI 명령·옵션 변경 [cli] | 명령·옵션·exit code + README 예시 + Component(명령 트리) |

**호출 자리**: autopilot-spec refine(의도 변경) → 영향 list → confirm → 일괄 / autopilot-code 가 spec 영향 감지 → 묶음 plan → confirm → autopilot-spec back-jump. **analysis_project 자동 갱신**: autopilot-code final-report 후 Step 7 — 작은 변경은 직접 Edit, 큰 변경은 `/analyze-project --mode code --skip-qa` incremental 자동.

## 5. entry → 서브에이전트 분기 (autopilot-* 내부 라우팅)

사용자는 entry 한 줄만 — 내부 분기는 자동. (model 표기 = CONVENTIONS §2)

| entry | 내부 분기 |
|---|---|
| **autopilot-research** | 연구팀 research-survey + 자료팀 browser-fetch/pdf-extract/web-image-search + 연구팀 fact-check |
| **analyze-project** | 단일 skill — code/paper/doc mode 자체 분석 |
| **autopilot-spec** | 기획팀(PRD 위임) + 자료팀(research import) / setup: 호스팅·CI/CD logic |
| **autopilot-design** | 디자인팀 maker + 디자인팀 critic + 자료팀 web-image-search |
| **autopilot-code** (일반) | 기획팀(plan) + 개발팀(execute) + 품질관리팀 code-review·test + **task-aware plan-review** (UI/visual → 디자인팀 critic / research·code → 연구팀) |
| **autopilot-code** (앱 mode) | 위 + **디자인팀 critic 2자리** (plan 단계 _plan-review_ + render 후 결과 critic) + DB migration 안전 logic + push 자동 deploy |
| **autopilot-draft** | 자료팀(figure·data·reference) + 개발팀(writing) + 편집팀 polish + 연구팀 fact-check |
| **autopilot-refine** | autopilot-draft 와 동일 재활용 + 편집팀 review |
| **analyze-user** | 자료팀(cross-project 수집) + 편집팀 review |

**사용자 주도성**: 각 entry = 명시 의도 단위. 메인 에이전트가 옵션 자동 구성 + 자연어 요약 컨펌 → CONFIRM Gate 4 갈래(진행 / 수정-refine v2 / back-jump / 중단). 발화 모호 시 재질문(임의 추측 X). 호출 패턴 상세 = runtime adapter bootstrap (Claude Code: [`adapters/claude/CLAUDE.md §0`](../adapters/claude/CLAUDE.md)).

## 6. 산출물 폴더 — 코드 = `spec/` + `plans/` 형제 2-bucket

| 종류 | 폴더 |
|---|---|
| 코드 청사진 | `spec/` — `prd.md`(항상 최신 T1)·`stack.md`·`design/`(자산 시)·`ship.md`·`pipeline_state.yaml`·`_internal/versions/v{N}/`(구 spec) |
| 코드 작업 | `plans/<date>_<slug>/` — plan·dev_logs·test_logs·_internal (spec 유무 무관) |
| 실험 prototype | `experiments/{date}_{slug}/` + `experiments/_RUNLOG.md` |
| 문서 | `documents/<date>_<name>/` |
| 사전 조사·분석 | `research/<topic>/` · `analysis_project/<mode>/` |

숫자 prefix(00_/01_/02_/05_) 폐지 — `spec/` 안 평이한 이름·user-facing(위) vs `_internal/`(기계) 2분. spec versioning = doc 트랙 동일 원리 (autopilot-spec refine 이 `_internal/versions/v{N}/prd.md` 자동 snapshot). 상세 = [`CONVENTIONS.md §5·§6.5`](CONVENTIONS.md).

## 6.1. Cross-Project Continuity Layer — `<agent-notes-root>`

`<agent-notes-root>` 는 프로젝트별 `<artifact-root>` 와 다른 계층이다. artifact root 는 한 프로젝트 안의 research/spec/plans/documents/experiments 를 담고, notes root 는 여러 프로젝트 산출물을 읽어 L1/L2 상태판으로 연결한다.

| 계층 | 주인 | 예시 | 변경 경로 |
|---|---|---|---|
| `<artifact-root>/notes/<date>/` | autopilot-note | 이번 실행의 scan/routing log, reviewer log | capability 산출물 — artifact root 규칙 |
| `<agent-notes-root>/_layer2/notes/` | agent | 산출물 1개를 읽기 좋은 note row 로 노트화 | `autopilot-note` 또는 board-approved migration |
| `<agent-notes-root>/_layer2/{backbones,tasks,papers}/` | agent | 재사용 축/과제/논문 카탈로그 | `autopilot-note` emerge 또는 board-approved edit |
| `<agent-notes-root>/cards/` | user | L1 task/project 카드 | worklog-board UI 또는 사용자 직접 편집 |
| `<agent-notes-root>/_triage`, `_feedback`, `_change_review` | user+agent queue | 신규 카드 제안, 사용자 피드백, 코드 변경 검토 | worklog-board UI + `autopilot-note --feedback` |
| `<agent-notes-root>/digests`, `oncall`, `study`, `manual` | loop/operator docs | 일지, 당직 보고, 연수 제안, 매뉴얼 | loop 또는 board UI |

**판정**: `_layer2/`, `_triage/`, `_feedback/`, `_change_review/`, local board DB 는 mutable runtime/user state 이다. 하네스 repo 에 커밋하지 않는다. 별도 notes repo 로 versioning 할 수는 있지만, 그 경우도 하네스 core/adapters 와 독립된 데이터 repo 로 취급한다.

`<worklog-board-app>` 는 이 notes root 를 보여주고 승인/검토를 처리하는 구현체다. 앱 코드 변경은 그 앱 repo 의 `autopilot-code` 대상이며, 하네스 migration 은 board data 를 이동/삭제하지 않는다.

## 7. 사후 수정 라우팅 — spec-backed 프로젝트

초기 빌드 후 수정·기능 요청 (특히 새 세션). cwd 에 artifact root 의 `spec/` 이 있으면 ad-hoc 직접 Edit 금지 — **순서 원칙 (기존 산출물 파악) → analyze → spec → dev** 를 지킨다 (adapter bootstrap imperative).

> 본 §7 은 _지침_ 으로 적재된다 — adapter bootstrap 이 세션 시작 또는 해당 도메인 트리거에서 WORKFLOW.md 를 Read 한다. Claude Code adapter 에서는 `adapters/claude/CLAUDE.md` §0(A)가 spec-backed 사후 수정 트리거를 가리킨다. `workflow-guard-hook` 은 매 프롬프트에 모드 신호(📌tracked 따름 / ⚡untracked 면제)만 띄운다(런타임 flag 상태). 규칙 본문의 단일 출처는 본 §0/§7.

0. **기존 artifact root (`.agent_reports/`, legacy `.claude_reports/`) 산출물 파악 (1 순위, 특히 새 세션)** — 손대기 전 `spec/prd.md` · `pipeline_state.yaml` · 최근 `plans/*` 를 먼저 읽어 프로젝트 상태·진행 자리를 잡는다. 맥락 모른 채 작업 X. **spec-backed cwd 에선 `prd.md` Read 가 _필수 게이트_** — `spec-skill-gate`/`spec-read-marker` 가 이번 세션 prd.md 미Read(또는 Read 후 prd 갱신) 시 `autopilot-code`/`autopilot-spec` 등 spec-changing capability 진입을 hard DENY 한다 (선택 아님; Claude 는 settings hook, Codex 는 preflight wrapper, [README](../README.md) 'hard 차단 셋' 중 하나).
1. **(필요 시) analyze 갱신** — `analysis_project/code/` 가 stale 하거나 낯선 영역이면 `analyze-project --mode code` (incremental) 먼저.
2. **spec 존재 확인** — 없으면 `autopilot-spec` 먼저 유도 (**spec → dev 하드 원칙**; throwaway 1 회성만 예외, 반복 시 spec 승격 권장).
3. **spec-drift 사전 체크 (code 경유 _전_, 최우선)** — `spec/prd.md` 대조:
   - spec-significant (route / schema·entity / UI-flow / 외부 연동 / 마이그레이션) **또는 코드 기존 drift** → **`autopilot-spec` update 모드** (prd.md 최신화 + `_internal/versions/v{N}/prd.md` 스냅샷). drift 가 _명확_ 하면 자율 진행 후 한 줄 보고, **_애매_ 하면 사용자에 확인.**
   - within-spec (구현 디테일) → _"spec 영향 없음"_ 확인.
   > 이 체크는 `autopilot-code` 의 **pre-flight Step 0** 로 절차화 — 라우팅에서 빠뜨려도 code 스킬 진입 시 verdict 보고로 다시 걸린다.
4. **`autopilot-code` 경유** — stage graph는 `--intensity`가 선택한다. `direct`는 plan 없이 produce+sanity/report, `quick`은 inline micro-plan+plan-check-lite+verify-lite, `standard+`만 `plans/<date>_<slug>/` durable cycle을 만든다. `--qa`는 assurance override일 뿐 새 plan cycle을 강제하지 않는다.

> 핵심: ① 트레일 단절 (거의 모든 요청 quick-pipe → `plans/`) ② spec drift (spec 변경은 항상 autopilot-spec update + versioning) ③ 새 세션 맹목 (진입 시 기존 산출물 파악 1 순위 + 도메인 트리거) 셋을 닫는다. autopilot-spec·autopilot-code 둘 다 iterable — 사후 수정은 _재호출_ 이지 새 사이클이 아니다.
