---
name: autopilot-refine
description: "기존 문서·연구 산출물의 정정·갱신 entry — 버전 snapshot 보존"
argument-hint: "\"<prompt>\" [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]"
metadata:
  group: entry
  fam: doc
  modes: []
  blurb: "기존 문서·연구 산출물의 정정·갱신 entry — 버전 snapshot 보존"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 버전 스냅샷은 `_internal/versions/v{N}/` (modern, research·doc 공통) 또는 `_v{N}.md` 형제 (legacy doc). 자동 감지.

기존 문서·연구 산출물의 정정·갱신 entry. 이 파일은 라우터 — routing 결정(major vs minor, mode form, qa)과 stage 개요만 담고, 세부 orchestration·log 형식·detector·예시는 필요할 때 아래 reference를 읽는다.

## Position in autopilot family

`autopilot-refine` is the **post-creation iteration** counterpart to the creation pipelines:
- `autopilot-research` / `autopilot-code` / `autopilot-draft` create artifacts (forward direction).
- `autopilot-refine` reads and updates existing artifacts (reverse direction).

Naming consistency: same `--intensity direct|quick|standard|strong|thorough|adversarial` and `--qa quick|light|standard|thorough|adversarial` flags as the rest of the family. `intensity` selects the stage graph; `--qa` only scales selected assurance gates. Routine scoped edits default to the quick path unless the request or caller explicitly escalates intensity/QA.

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트는 사용자가 `<artifact-root>/{documents,research}/*` 하위 artifact에 대해 **major-level 변경**을 prompt로 요청할 때만 `/autopilot-refine` slash command 명시 없이도 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke 한다. 기본은 request shape에서 선택된 `intensity`를 따르고, `--qa`는 그 그래프 안의 assurance budget만 조정한다. **minor-level 변경은 직접 Edit + `pipeline_summary.md` 상세 minor log 추가** (refine flow X, 컨펌 자체도 skip — 단순 minor 라 그냥 진행). 누적된 minor는 사용자가 `/audit`을 호출하거나, AUDIT_HINT_THRESHOLD (default 5 minors)를 넘으면 chat alert로 _권장_ 받아 batch 점검한다.

**Scope**: `<artifact-root>/{documents,research}/*` 엄격 한정. project root의 임의 `.md`/`.txt`나 코드 산출물(`<artifact-root>/plans/*`)은 적용 X — 전자는 일반 Edit, 후자는 `/code-refine` 또는 `/autopilot-code`.

### Major vs Minor — 3-criteria 판정

**Major** (하나라도 해당 → autopilot-refine 자동 invoke):

1. **사용자 명시 표현**: "major", "v{N+1}", "/autopilot-refine", "메이저 버전", "전면 재작성", "phase 재시작", "cycle 재진입"
2. **구조적 대규모 변경**: ≥200 줄 영향 / 전체 section rewrite / mutation tier 재분류 batch / strategy↔draft alignment overhaul
3. **외부 검토 직전 ceremony**: 사용자 prompt 본문에 verbatim 으로 "camera-ready 마무리" / "submission 직전 finalize" / "external review 전 마지막" / "grant 제출" / "PR open 직전" 표현이 _직접_ 등장한 경우만. cwd 이름 (예: `..._camera_ready/`) · 메모리 맥락 · 작업 디렉토리 신호로 추론 금지 (응답 원칙 §2 정합)

**Minor** (default — 위 3-criteria 미해당):

- 단일 entry mutation 추가·제거·wording 조정
- cross-ref 한두 줄 추가/수정
- caption / table cell / typo / wording polish
- 사용자가 미리 caption/wording을 본 turn에 명시한 뒤 _그걸 반영해 달라_ 는 요청
- 누락된 reference 1-2건 보강
- figure/asset 경로 정정

→ Claude는 **직접 Edit 도구**로 즉시 적용 + `pipeline_summary.md`에 **상세 minor log entry** 추가. snapshot 생성 **X** (last major snapshot이 audit의 baseline).

> Minor log entry 형식(반드시 준수)·Major 적용 시 동작·Why this split: `references/versioning-and-modes.md`.

### Override 1순위 (자동 룰 무시)

다음 중 하나라도 prompt에 있으면 위 분기 룰을 건너뛴다:

- 다른 qa level 명시 — `standard`/`thorough`/`adversarial` (강제 refine, level 명시)
- "refine 없이 직접 edit" / "Edit으로 처리" / "versioning 없이" / "snapshot 없이" — 강제 minor 경로
- `--review-only` — 검수만, 적용 X
- `/autopilot-refine` slash 명시 invoke — 강제 refine flow (qa level은 따로 명시 안 하면 `quick`)

## Scope

- **Targets**: `<artifact-root>/research/*` and `<artifact-root>/documents/*`
- **NOT for**: `<artifact-root>/plans/*` (code) — use `/code-refine`, `/code-execute`, or `/autopilot-code` instead. Code changes need test-based verification, not diff review.
- Why this skill exists: the existing `draft-refine` / `code-refine` workflow is file-memo only, which is too heavy for routine prompt-driven edits. `autopilot-refine` is the lightweight default; memo style is reduced to an opt-in fallback.

## --qa <level> (assurance budget; graph selected by intensity)

QA 5 단계 정의 + 모델·round 매트릭스는 [`CONVENTIONS.md §1`](../../core/CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용 (proposed diff 에 pre-apply review):

| Level | Behavior on proposed diff |
|---|---|
| **quick** | Investigate → Stage B.5 (factual + style auto-detector, always on) → diff preview → apply. No internal review loop. Stage B.5 는 cards-grep + regex 만. |
| **light** | + 2× fast reviewers (다른 axes) single pass. obvious regression catch. |
| **standard** | + 1× deep reviewer + 2× fast reviewers (다른 axes) + 1× fast fact-checker (parallel, in-artifact ground truth verbatim 대조 — research: `cards/*.md`; doc: `analysis/*.md` + 기존 strategy/draft). round 1. |
| **thorough** | + 2× deep reviewers + 2× fast reviewers (다른 axes) + 1× fast fact-checker, only when the selected graph includes that review point. round 2. high-stakes refine 용. |
| **adversarial** | thorough + 1× external adversary (`codex-review-team` in Claude adapter). camera-ready / grant / public rebuttal 같은 외부 strong scrutiny 자리. |

Pre-apply review 만 — post-apply review 는 본 skill 범위 아님 (`/draft-refine` 사용).

> The two opt-out flags `--no-fact-check` and `--no-style-audit` are **orthogonal to every `--qa` level** — they skip the corresponding Stage B.5 aspect regardless of qa level. These are the _only_ disable mechanism per `feedback_factcheck_principles.md` Principle 0.

> `adversarial` tier의 external adversary propagation 세부: `references/versioning-and-modes.md`.

## Mode Forms (orthogonal to --qa)

| Form | Behavior |
|---|---|
| `autopilot-refine "<prompt>"` | **Default (autopilot 정신)**: investigate → diff preview (chat에 출력만) → **자동 apply** + version + log. MECH/SEM 모두 자동. STRUCT만 halt (사용자에게 heavier flow 권장). 사후 검토는 `git diff` + `_internal/versions/v{prev}/` 스냅샷 + `pipeline_summary.md` history. |
| `autopilot-refine "<prompt>" --confirm` | Diff preview에서 chat-pause + 사용자 confirm 후 apply. _수정 전 검토_ 원할 때 명시. |
| `autopilot-refine "<prompt>" --review-only` | Investigate + diff preview. No edits, no version, no log. _점검만_ 원할 때. |
| `autopilot-refine --memo <file> "<prompt or artifact hint>"` | Read memo file as proposal source. Default 동작과 동일 (자동 apply). `--confirm` 추가 가능. |

> **Target artifact identification**: prompt에 포함된 키워드로 `<artifact-root>/{research,documents}/*` fuzzy match. 매치 1 → 사용. 다수 → 사용자에게 list 보여주고 선택 요청. 0 → "어느 산출물? prompt에 명시 부탁" 안내.

> Default=자동 apply 근거·STRUCT halt escape hatch·tunable constants(`AUDIT_HINT_THRESHOLD`): `references/versioning-and-modes.md`.

## Language Rule

All user-facing output (chat diffs, pipeline_summary entries, reports) in natural **Korean** (no translationese — write Korean natively, don't translate from an English draft).

> `<artifact-root>` 해석: `.agent_reports` 우선, legacy `.claude_reports` 는 이미 존재하고 `.agent_reports` 가 없을 때만 사용. 실제 쉘 명령에서는 `REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports` 로 치환한다.

---

## Process

target 식별(Artifact Resolution) 후 Stage A→E 로 진행. 각 단계 full orchestration 은 `references/process-stages.md`.

- **Artifact Resolution** — prompt 키워드로 `<artifact-root>/{research,documents}/*` fuzzy match, type 감지.
- **Stage A — Auto-discover structure**: artifact root glob, type별(research: `cards/*`; doc: `strategy/`·`draft/`) 구조 파악, grep으로 affected file 좁히기.
- **Stage B — Plan changes**: affected file만 read → per-file change list, 각 change를 MECH/SEM/STRUCT 분류. STRUCT면 halt + heavier flow 권장.
- **Stage B.5 — Factual claim & Style auto-detector**: 모든 change에 항상 실행(quick 포함). cards-grep + regex로 factual claim ground-truth 대조 + style lint → `⚠ Unverified`/`⚠ Style` marker. `--no-fact-check`/`--no-style-audit`로만 개별 opt-out.
- **Stage C — Diff preview (chat)**: 제안 변경을 chat에 출력. default는 출력만 하고 자동 Stage D. `--confirm`은 chat-pause, `--review-only`는 여기서 종료.
- **Stage D — Apply**: version 결정 → pre-edit snapshot → Edit 적용 → `pipeline_summary.md` 5-part update(메타·버전 히스토리·변경 사항·minor log migration·in-file changelog) → report.
- **Stage E — Memo mode (`--memo <file>`)**: 메모 파일을 proposal source로 읽어 Stage B~D 실행.

## Required Reads

- major refine flow 세부(minor log 형식, major apply 동작, --qa adversarial propagation, mode-forms 근거, tunable constants, why-this-split): `references/versioning-and-modes.md`.
- 실제 실행 orchestration(Artifact Resolution + Stage A→E, B.5 detector, diff preview, apply/versioning, memo): `references/process-stages.md`.
- invocation 예시, constraints(빈칸>잘못 채우기 등), when-not-to-use, post-apply checklist: `references/examples-and-constraints.md`.

## Reference Map

- `references/versioning-and-modes.md`: minor log entry 형식, major 적용 동작, why-this-split rationale, --qa adversarial propagation, mode-forms default/STRUCT-halt 근거, tunable constants.
- `references/process-stages.md`: artifact resolution, Stage A/B/B.5/C/D/E full orchestration (factual+style auto-detector, diff preview, apply/versioning, memo mode).
- `references/examples-and-constraints.md`: invocation examples, constraints, when-not-to-use, post-apply checklist.
