# Autopilot-* 라우팅 맵 (Claude-facing)

> 메인 Claude 가 _작업 발화 → skill·sub-agent 라우팅_ 을 결정할 때 보는 압축 맵. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙.
>
> 역할 분담: 사용자 향 의미 지도·entry list 는 [`README.md`](README.md). 정의(QA·model·폴더 컨벤션)는 [`CONVENTIONS.md`](CONVENTIONS.md). 본 문서는 _라우팅 표_ 만 — narrative·호출 예시·비개발자 설명은 중복 회피로 제거(필요 시 README).
> 마지막 정돈: 2026-05-31 (Claude-facing 라우팅 코어로 압축).

---

## 0. 불변식 — 단일 라우터 + 하드 순서 게이트 (우회 불가)

본 문서가 **모든 작업 흐름의 단일 라우터**. 모든 발화는 §2 작업-본질 매핑을 먼저 거치고, 직접 처리·플러그인(codex)·빌트인 스킬도 WORKFLOW 가 배치하는 자리에서만 쓴다.

**(a) 하드 순서 게이트** — 산출물은 한 방향으로만, 앞 단계 산출물 없이 다음 단계 진입 금지:

```
[코드]  research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)
[문서]  research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine
```

- **spec 없이 코드 X**: 코드 요청인데 `spec/` 없으면 autopilot-spec 먼저 (throwaway 1 회성만 예외, 반복 시 spec 승격).
- **사전 산출물 없이 spec X**: spec 근거(`research/` 또는 `analysis_project/`) 없으면 autopilot-research/analyze-project 먼저. 낯선 영역·신규 의도일수록 강제.
- **harness 강제**: `artifact-guard.sh` 가 체인을 기계 차단 — `spec/` 있는 프로젝트는 코드 편집 = `plans/` plan 전제, spec·문서(documents) 작성 = research/analyze 전제. 작은 변경도 `autopilot-code --qa quick` 트레일. spec 없는 프로젝트는 코드 자유 (자동 scope). `/track` 우회.

**(b) 동일 스킬 수정 = 버전 트래킹** (`hooks/artifact-guard.sh` 가 기계 강제 — 추적 산출물 직접 Edit 차단, `.untracked` touch 로만 해제). 각 산출물은 _그것을 만든 스킬로만_ 수정:

| 산출물 | 유일 수정 경로 | 버전 자리 |
|---|---|---|
| `spec/` 청사진 | autopilot-spec update | `_internal/versions/v{N}/` |
| `plans/` 코드 | autopilot-code | `plans/<date>_<slug>/` |
| `documents/` 문서 | autopilot-draft/refine | `_internal/versions/v{N}/` |
| `experiments/` 실험 | autopilot-lab | `_RUNLOG.md` |
| `user_profile/` 프로필 | analyze-user / post-it --scope user | `_internal/versions/` |

> 단일 출처 = 글로벌 `CLAUDE.md` §0. 본 §0 은 그 라우팅 불변식의 WORKFLOW 측 거울. 위반 신호: ad-hoc Edit 으로 산출물 직접 수정 / 게이트 건너뛰고 코드부터 / 산출물 만든 스킬 외 경로로 수정.

## 1. 한 화면 청사진 — 4 트랙

```
[연구·실험]   research / analyze-project(code) → autopilot-spec ↻ → autopilot-code ↻ → autopilot-lab ↻
[라이브러리·CLI]  analyze-project → autopilot-spec ↻ → autopilot-code ↻
[문서]        research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine ↻ → autopilot-apply
[앱]          autopilot-spec ↻ → autopilot-design → autopilot-code ↻(앱 mode 자동) → autopilot-ship ↻
```

`↻` = 반복 자리. 사후 공통: `audit`(읽기 전용 점검) · `autopilot-refine`(markdown 정정). cross-project: `analyze-user` · `post-it --scope user`.

## 2. 작업 본질 매핑 (발화 → skill)

| 작업 종류 | 사전 (조사·분석) | 신규 의도·청사진 | 자산 작업 (신규·기존) |
|---|---|---|---|
| **문서** (paper / 발표 / 보고서 / proposal / rebuttal) | research(academic·market) + analyze-project(paper·doc) | `autopilot-draft` | `autopilot-refine` |
| **코드** (라이브러리·연구·앱·CLI·API 모두) | research(academic·tech) + analyze-project(code) | **`autopilot-spec`** (mode app/library/api/cli/research/복합/auto) | **`autopilot-code`** (spec mode 별 분기 자동) |
| **실험 prototype** (ML / one-shot) | analyze-project(code) 의 4 종 자료(experiment_conventions·readiness·cleanup·similar_models) | — (spec 없이 빠른 cycle) | **`autopilot-lab`** (반복; 졸업 자리 autopilot-code) |
| **시각 자산** | — | `autopilot-design` (신규 사이클) | `autopilot-design` 재호출 |
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

**Scaffold ref 우선순위**: 내부(similar_models·`--ref`) → 외부(research/{topic}/code_resources) → generic. **컨벤션 prepend**: `analysis_project/code/experiment_conventions.md`(1순위) → `user_profile/07_coding_convention.md`(2순위, 충돌 시 per-project 우선).

## 4. PRD 묶음 갱신 — spec drift 차단

코드·의도 변경이 spec 영향 자리면 _영향 받는 모든 자리 한 트랜잭션_ 갱신. 매핑 single source = [`CONVENTIONS.md §6.3a`](CONVENTIONS.md).

| 변경 | 영향 자리 |
|---|---|
| endpoint·body·error | api_contract + Component (+옵션 Sequence) |
| DB entity·필드 | data_model + Component(backend) (+옵션 ER) |
| UI flow | ui_flow + Component(frontend) (+옵션 Activity) |
| 외부 service 통합 | api_contract(auth) + Deployment + deploy_record + .env.example |
| 스택 교체 | stack_decision + Component + Deployment |

**호출 자리**: autopilot-spec refine(의도 변경) → 영향 list → confirm → 일괄 / autopilot-code 가 spec 영향 감지 → 묶음 plan → confirm → autopilot-spec back-jump. **analysis_project 자동 갱신**: autopilot-code final-report 후 Step 7 — 작은 변경은 직접 Edit, 큰 변경은 `/analyze-project --mode code --skip-qa` incremental 자동.

## 5. entry → 서브에이전트 분기 (autopilot-* 내부 라우팅)

사용자는 entry 한 줄만 — 내부 분기는 자동. (model 표기 = CONVENTIONS §2)

| entry | 내부 분기 |
|---|---|
| **autopilot-research** | 연구팀 research-survey + 자료팀 browser-fetch/pdf-extract/web-image-search + 연구팀 fact-check |
| **analyze-project** | 단일 skill — code/paper/doc mode 자체 분석 |
| **autopilot-spec** | 기획팀(PRD 위임) + 자료팀(research import) / setup: 호스팅·CI/CD logic |
| **autopilot-design** | 디자인팀 maker + 디자인팀 critic + 자료팀 web-image-search |
| **autopilot-code** (일반) | 기획팀(plan) + 개발팀(execute) + 품질관리팀 code-review·test + 연구팀 plan-review |
| **autopilot-code** (앱 mode) | 위 + **디자인팀 critic**(UI 변경 자리 자동) + DB migration 안전 logic + push 자동 deploy |
| **autopilot-draft** | 자료팀(figure·data·reference) + 개발팀(writing) + 편집팀 polish + 연구팀 fact-check |
| **autopilot-refine** | autopilot-draft 와 동일 재활용 + 편집팀 review |
| **analyze-user** | 자료팀(cross-project 수집) + 편집팀 review |

**사용자 주도성**: 각 entry = 명시 의도 단위. 메인 Claude 가 옵션 자동 구성 + 자연어 요약 컨펌 → CONFIRM Gate 4 갈래(진행 / 수정-refine v2 / back-jump / 중단). 발화 모호 시 재질문(임의 추측 X). 호출 패턴 상세 = [`CLAUDE.md §0`](CLAUDE.md).

## 6. 산출물 폴더 — 코드 = `spec/` + `plans/` 형제 2-bucket

| 종류 | 폴더 |
|---|---|
| 코드 청사진 | `spec/` — `prd.md`(항상 최신 T1)·`stack.md`·`design/`(자산 시)·`ship.md`·`pipeline_state.yaml`·`_internal/versions/v{N}/`(구 spec) |
| 코드 작업 | `plans/<date>_<slug>/` — plan·dev_logs·test_logs·_internal (spec 유무 무관) |
| 실험 prototype | `experiments/{date}_{slug}/` + `experiments/_RUNLOG.md` |
| 문서 | `documents/<date>_<name>/` |
| 사전 조사·분석 | `research/<topic>/` · `analysis_project/<mode>/` |

숫자 prefix(00_/01_/02_/05_) 폐지 — `spec/` 안 평이한 이름·user-facing(위) vs `_internal/`(기계) 2분. spec versioning = doc 트랙 동일 원리 (autopilot-spec refine 이 `_internal/versions/v{N}/prd.md` 자동 snapshot). 상세 = [`CONVENTIONS.md §5·§6.5`](CONVENTIONS.md).

## 7. 사후 수정 라우팅 — spec-backed 프로젝트

초기 빌드 후 수정·기능 요청 (특히 새 세션). cwd 에 `.claude_reports/spec/` 있으면 ad-hoc 직접 Edit 금지 — **순서 원칙 (기존 산출물 파악) → analyze → spec → dev** 를 지킨다 (CLAUDE.md §0 imperative).

> 본 §7 의 단일 출처는 글로벌 [`CLAUDE.md`](CLAUDE.md) §0. `settings.json` 의 SessionStart hook (`utilities/spec-guard-hook.sh`) 이 cwd·상위의 `spec/pipeline_state.yaml` (모노레포는 `spec/*/`) 을 감지하면 본 §7 을 `additionalContext` 로 주입한다.

0. **기존 `.claude_reports/` 산출물 파악 (1 순위, 특히 새 세션)** — 손대기 전 `spec/prd.md` · `pipeline_state.yaml` · 최근 `plans/*` 를 _필요에 따라_ 먼저 읽어 프로젝트 상태·진행 자리를 잡는다. 맥락 모른 채 작업 X.
1. **(필요 시) analyze 갱신** — `analysis_project/code/` 가 stale 하거나 낯선 영역이면 `analyze-project --mode code` (incremental) 먼저.
2. **spec 존재 확인** — 없으면 `autopilot-spec` 먼저 유도 (**spec → dev 하드 원칙**; throwaway 1 회성만 예외, 반복 시 spec 승격 권장).
3. **spec-drift 사전 체크 (code 경유 _전_, 최우선)** — `spec/prd.md` 대조:
   - spec-significant (route / schema·entity / UI-flow / 외부 연동 / 마이그레이션) **또는 코드 기존 drift** → **`autopilot-spec` update 모드** (prd.md 최신화 + `_internal/versions/v{N}/prd.md` 스냅샷). drift 가 _명확_ 하면 자율 진행 후 한 줄 보고, **_애매_ 하면 사용자에 확인.**
   - within-spec (구현 디테일) → _"spec 영향 없음"_ 확인.
   > 이 체크는 `autopilot-code` 의 **pre-flight Step 0** 로 절차화 — 라우팅에서 빠뜨려도 code 스킬 진입 시 verdict 보고로 다시 걸린다.
4. **`autopilot-code` 경유** — 작은 자연어 요청도 `--qa quick` (모든 모드 공통 경량 tier) 로 산출물 남기며 진행 → `plans/<date>_<slug>/` (매 사이클 새 plan). 생성 순서·코드←plan 은 artifact-guard hook 이 강제하나, _기존 산출물 편집_ 은 convention (소유 스킬 권장; hook 비차단 — §0(b)). code←plan 은 "플랜 1개 이상 존재" floor 라, _변경마다 fresh plan_ 은 본 skill 행동이 담당.

> 핵심: ① 트레일 단절 (거의 모든 요청 quick-pipe → `plans/`) ② spec drift (spec 변경은 항상 autopilot-spec update + versioning) ③ 새 세션 맹목 (진입 시 기존 산출물 파악 1 순위 + 도메인 트리거) 셋을 닫는다. autopilot-spec·autopilot-code 둘 다 iterable — 사후 수정은 _재호출_ 이지 새 사이클이 아니다.
