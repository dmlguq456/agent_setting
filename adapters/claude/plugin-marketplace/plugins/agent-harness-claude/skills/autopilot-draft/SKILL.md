---
name: autopilot-draft
description: "Use when starting a document draft (paper/slides/prose). 문서 초안 파이프 entry — paper(LaTeX)·슬라이드·prose 세 출력 형태"
argument-hint: "<task description> [--mode paper|presentation|doc] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]"
metadata:
  group: entry
  fam: doc
  modes: [paper, presentation, doc]
  blurb: "문서 초안 파이프 entry — paper(LaTeX)·슬라이드·prose 세 출력 형태"
---

# autopilot-draft

문서 초안 파이프 entry. paper(LaTeX)·slide·prose 세 출력 형태를 `analyze → strategy → strategy-refine → draft → draft-refine → finalize` 흐름으로 닫는다. 이 파일은 라우터와 stage 개요만 담고, 세부 절차는 필요할 때 아래 reference를 읽는다.

## First Principle — draft 의 산출물은 "최종 문서" 가 아니다

autopilot-draft 의 산출물은 _최종 문서 그 자체_ 가 아니라, 사용자가 canonical source (`main.tex` 등) 에 적용할 **cheatsheet (mutation/edit plan) 의 draft** 다. **모든 mode 공통** — 여기서 'draft' 는 _백지 본문/문서 작성_ 이 아니라 _적용할 수정안(plan)의 초안_ 이다.

- **`autopilot-apply` 가 별도로 존재하는 이유** — cheatsheet 를 실제 소스에 paste·적용·compile 검증한다. draft 가 곧 최종 산출물이라면 apply 는 존재 이유가 없다.
- **`draft-refine` / `autopilot-refine`** 은 _최종 문서_ 가 아니라 _이 cheatsheet draft_ 를 다듬는다.
- **code 가족 대응** — draft ≈ `code-plan`(plan 생성), apply ≈ `code-execute`(소스 반영). draft 는 _plan 단계_ 지 실행 단계가 아니다.

> 이 원칙은 2026-05-21 mode 6→3 collapse (`ff0319b`) + conventions 분리 (`04c1b83`) 다이어트 때 표면에서 사라져 반복 오해를 유발했다. 축소·정리 시에도 본 블록은 _표면에 유지_ 한다.

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). reviewer 로그는 `_internal/strategy_reviews/`·`_internal/draft_reviews/`. 버전 스냅샷은 `_internal/versions/v{N}/strategy/`, `v{N}/draft/`.

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

**paper 모드** (LaTeX 학술 본문):
- "X 논문 본문 작성해줘" / "ICML camera-ready 마무리" / "major revision 작성"
- "thesis chapter 초안" / "book chapter"
- "paste-ready cheatsheet" (LaTeX)

**presentation 모드** (slide markdown):
- "발표 자료 만들어줘" / "PPT 작성" / "슬라이드 markdown"
- "세미나 자료" / "강의 자료"
- (PPTX 변환은 PowerPoint 수동 — autopilot 은 markdown 까지만)

**doc 모드** (Word/HWP/markdown prose):
- "보고서 써줘" / "제안서 작성" / "분기 보고"
- "rebuttal 응답 써줘" / "OpenReview 응답"
- "peer review 작성" / "tech blog" / "메모"

### Default 옵션 권장값 (컨펌 시 메인 에이전트가 제안)

- `--mode`: 발화 신호로 paper/presentation/doc 자동 추론
- `--intensity`: default 는 thorough-tier rigor 를 주는 수준 (검증 rigor 는 별도 `--qa` 축이 아니라 intensity 에서 파생 — CONVENTIONS §1.1). high-stakes 신호(신중히·camera-ready·submission 직전) 시 intensity 를 adversarial 로 상향.
- `--user-refine`: **off** (글로벌 §2 준수)
- `--no-clarify`: off (default — Step 0 Scope Clarification 보존)

### Override 1순위 — autopilot 우회

- 한 단락 다듬기 / 표기 통일 / 판교체 정리 — `Agent(편집팀)` 직접 호출
- 구조 점검 / drift 점검 — `/audit`
- 작은 minor-level 수정 — `/autopilot-refine` 자동 라우팅 분기 (직접 Edit 경로)
- `/autopilot-draft <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

## Language Rule
- Write user-facing output in Korean. (Material analysis results and pipeline_summary.md are written directly in the artifacts — no separate user output needed for those steps.)

> `<artifact-root>` 해석·치환(`.agent_reports` 우선, legacy `.claude_reports` fallback): [CONVENTIONS §5.1](../../core/CONVENTIONS.md#51-workspace-assumption-전제).

## Argument Shape

`<task description> [--mode paper|presentation|doc] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`

Defaults (full parsing rules → `references/invocation-and-args.md`):

- `--mode`: 생략 시 발화 신호로 paper/presentation/doc auto-infer, 실패 시 doc. form-first 3-mode (doc 안의 rebuttal·review·report·proposal genre 는 task description 자연어로 분기).
- 검증 rigor: 별도 `--qa` 축이 아니라 선택된 `--intensity` 에서 파생된다 (CONVENTIONS §1.1). high-stakes 신호(신중히·camera-ready·submission 직전) 시 intensity 를 adversarial 로 상향.
- `--user-refine`: 사용자가 명시적으로 pause 를 요청한 경우만 (orchestrator 가 자의로 추가 X).
- `--no-clarify`: Step 0 Scope Clarification skip.
- `--from <stage>`: 기존 artifact 폴더 path 또는 fuzzy short-name 을 positional 로 받아 해당 stage 에서 재개 — `pipeline_state.yaml` 에서 mode/intensity/discovered_inputs/user_refine 복원, CLI flag 우선.
- mode·flag 제거 후 남는 텍스트가 task description. Input 은 `<artifact-root>/{analysis_project,research}/` 에서 implicit 자동 발견 (`--refs` flag 없음).

## Pipeline Overview

산출물: `<artifact-root>/documents/{YYYY-MM-DD}_{short-name}/` (Artifact Structure·Input Sources 규약 → `references/invocation-and-args.md`).

| Stage (`--from`) | Step | 역할 | 상세 reference |
|---|---|---|---|
| (pre) | Pre-flight Validation | mode·input·format-spec 검증, 실패 시 mkdir/sub-skill 전에 abort | `references/pipeline-steps.md` |
| — | Step 0: Scope Clarification | 모호 query 2-4 문항 사전 조율 (`--no-clarify` skip) | `references/pipeline-steps.md` |
| `analyze` | Step 1: Material Analysis | refs inventory + mode 별 분석 (`analysis/`) | `references/pipeline-steps.md` |
| `strategy` | Step 2: draft-strategy | strategy 생성 + `## Style Guide` 보증 | `references/pipeline-steps.md` |
| `strategy-refine` | Step 3: Strategy Review | 연구팀 review + fact-check + (memo 시) draft-refine | `references/review-and-qa.md` |
| `draft` | Step 4: Draft Generation | figure discovery/extraction + 연구팀 draft + KO mirror | `references/pipeline-steps.md` |
| — | Step 4b: factual detector | orchestrator-side 사실 스캔 (all qa 실행) | `references/pipeline-steps.md` |
| `draft-refine` | Step 5: Draft Review | 연구팀 review + fact-check + (memo 시) draft-refine | `references/review-and-qa.md` |
| — | Step 5.5: Editorial polish | 편집팀 모드 B 다듬기 (standard+ 한정) | `references/pipeline-steps.md` |
| `finalize` | Step 6: Pipeline Summary | `pipeline_summary.md` 작성 + 사용자 보고 | `references/summary-and-safety.md` |

> Step 4.1 의 연구팀 draft 프롬프트 안에 **Tone Propagation · Mode-Specific Conventions & Draft Structure · Quality Requirements** 가 임베드돼 있다 (`references/pipeline-steps.md`). mode 별 conventions 원본은 이 skill 폴더의 `conventions/{common,paper,presentation,doc}.md` 4 파일이 single source.

## Safety Essentials

전문은 `references/summary-and-safety.md` (## Safety Rules). 핵심:

- citation·데이터·결과를 날조하지 않는다 — `{discovered_inputs}` 에 실재하는 자료만 인용. 불확실·placeholder 는 `[TODO: ...]` 표기.
- draft 는 사용자 편집용 working first draft 이지 최종 문서가 아니다 (First Principle: cheatsheet/mutation plan 의 초안).
- `doc` + **rebuttal-response 의도**: 모든 reviewer point 에 응답 (누락 = critical error). rebuttal sub-type 은 Step 1 까지 format spec/task description 에서 도출.
- `doc` + **peer review 작성 의도**: 점수는 paper 근거 필수, format spec 도 필수 (pre-flight abort).
- **presentation mode**: 실제 figure/이미지 자동 삽입 X — `**시각자료**:` 블록에 구체 서술, PPTX 변환은 PowerPoint 수동.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/invocation-and-args.md` | 인자 해석·default·`--from` 재개·input/output 구조 자리 | Argument Parsing 전문(mode/auto-inference/input discovery/intensity-derived rigor/`--user-refine`/`--from`/format spec resolution), Decision Defaults 표, `pipeline_state.yaml` 스키마, Input Sources Convention, Artifact Structure |
| `references/pipeline-steps.md` | Pre-flight·Step 0·1·2·4·4b·5.5 orchestration 실행 시 (필수) | Pre-flight~Step 2, Step 4(4.0a figure discovery / 4.0b on-demand extraction / 4.0b-quality 해상도·crop 정책 / 4.0c path convention / 4.1 연구팀 draft[Tone·Conventions·Quality 임베드] / 4-KO mirror), Step 4b factual detector, Step 5.5 editorial polish |
| `references/review-and-qa.md` | Step 3(strategy review)·Step 5(draft review) 시 | intensity-derived rigor 별 reviewer 수·axis 분해(A domain/content · B methodology/writing · C style · D cross-ref+coverage)·quality reviewer·fact-checker 프롬프트 |
| `references/summary-and-safety.md` | Step 6 summary·terminal 보고 시 | Step 6 Pipeline Summary 템플릿(Process Log/Artifacts/Decision Points 포함) + Safety Rules 전문 |

## Task
$ARGUMENTS
