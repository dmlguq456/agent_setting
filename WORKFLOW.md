# Autopilot-* 라우팅 맵 (Claude-facing)

> 메인 Claude 가 _작업 발화 → skill·sub-agent 라우팅_ 을 결정할 때 보는 압축 맵. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙.
>
> 역할 분담: 사용자 향 의미 지도·entry list 는 [`README.md`](README.md). 정의(QA·model·폴더 컨벤션)는 [`CONVENTIONS.md`](CONVENTIONS.md). 본 문서는 _라우팅 표_ 만 — narrative·호출 예시·비개발자 설명은 중복 회피로 제거(필요 시 README).
> 마지막 정돈: 2026-05-31 (Claude-facing 라우팅 코어로 압축).

---

## 1. 한 화면 청사진 — 4 트랙

```
[연구·실험]   research / analyze-project(code) → autopilot-spec ↻ → autopilot-code ↻ → autopilot-lab ↻
[라이브러리·CLI]  analyze-project → autopilot-spec ↻ → autopilot-code ↻
[문서]        research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine ↻ → autopilot-apply
[앱]          autopilot-spec ↻ → autopilot-design → autopilot-code ↻(앱 mode 자동) → autopilot-ship ↻
```

`↻` = 반복 자리. 사후 공통: `audit`(읽기 전용 점검) · `autopilot-refine`(markdown 정정). cross-project: `analyze-user` · `memo --scope user`.

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

**사용자 주도성**: 각 entry = 명시 의도 단위. 메인 Claude 가 옵션 자동 구성 + 자연어 요약 컨펌 → CONFIRM Gate 4 갈래(진행 / 수정-refine v2 / back-jump / 중단). 발화 모호 시 재질문(임의 추측 X). 호출 패턴 상세 = [`CLAUDE.md §6`](CLAUDE.md).

## 6. 산출물 폴더 — 코드 = `spec/` + `plans/` 형제 2-bucket

| 종류 | 폴더 |
|---|---|
| 코드 청사진 | `spec/<project>/` — `prd.md`(항상 최신 T1)·`stack.md`·`design/`(자산 시)·`ship.md`·`pipeline_state.yaml`·`_internal/versions/v{N}/`(구 spec) |
| 코드 작업 | `plans/<project>/<date>_<slug>/` — plan·dev_logs·test_logs·_internal (spec 유무 무관, spec 과 같은 `<project>` 이름) |
| 실험 prototype | `experiments/{date}_{slug}/` + `experiments/_RUNLOG.md` |
| 문서 | `documents/<date>_<name>/` |
| 사전 조사·분석 | `research/<topic>/` · `analysis_project/<mode>/` |

숫자 prefix(00_/01_/02_/05_) 폐지 — `spec/<project>/` 안 평이한 이름·user-facing(위) vs `_internal/`(기계) 2분. spec versioning = doc 트랙 동일 원리 (autopilot-spec refine 이 `_internal/versions/v{N}/prd.md` 자동 snapshot). 상세 = [`CONVENTIONS.md §5·§6.5`](CONVENTIONS.md).

## 7. 사후 수정 라우팅 — spec-backed 프로젝트

초기 빌드 후 수정·기능 요청 (특히 새 세션). cwd 에 `.claude_reports/spec/<project>/` 있으면 ad-hoc 직접 Edit 금지 — **순서 원칙 analyze → spec → dev** 를 지킨다 (CLAUDE.md §9 imperative).

0. **(필요 시) analyze 갱신** — `analysis_project/code/` 가 stale 하거나 낯선 영역이면 `analyze-project --mode code` (incremental) 먼저. _순서상 analyze 가 spec·dev 앞._
1. **spec 존재 확인** — 없으면 `autopilot-spec` 먼저 유도 (**spec → dev 하드 원칙**; throwaway 1 회성만 예외, 반복 시 spec 승격 권장).
2. **spec-drift 사전 체크 (code 경유 _전_, 최우선 · 자율)** — `spec/<project>/prd.md` 대조해 _update 여부를 스스로 판단·실행_:
   - spec-significant (route / schema·entity / UI-flow / 외부 연동 / 마이그레이션) **또는 코드 기존 drift** → **`autopilot-spec` refine 자동 실행** (iterable — `prd.md` 최신화 + `_internal/versions/v{N}/prd.md` 스냅샷). autopilot 정신 — 사용자 gating X, 실행 후 한 줄 보고.
   - within-spec (구현 디테일) → _"spec 영향 없음"_ 확인.
3. **`autopilot-code` 경유** (작은 건 `--qa quick`) → `plans/<project>/<date>_<slug>/` 트레일 + §4 spec-sync 자동. trivial (typo·포맷, 2 에서 spec 무관 확정) 만 직접 Edit + 한 줄 로그.

> 핵심: ① 트레일 단절 (작업 항상 `plans/<project>/`) ② spec drift (2 에서 자율 갱신) ③ 새 세션 맹목 (도메인 트리거 cwd 감지) 셋을 닫는다. autopilot-spec·autopilot-code 둘 다 iterable — 사후 수정은 _재호출_ 이지 새 사이클이 아니다.
