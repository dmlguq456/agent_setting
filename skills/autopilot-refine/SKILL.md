---
name: autopilot-refine
description: "Autopilot family — post-creation iteration pipeline for research and doc artifacts (NOT code). Prompt-driven: target artifact identified via prompt fuzzy match against `<artifact-root>/{research,documents}/*`, then auto-discovers the artifact's file structure, plans edits, shows a diff preview in chat, and on user confirm applies edits with versioning + integrated history logging in `pipeline_summary.md` (single source of truth — no separate CHANGELOG). Default `--qa quick` (1-pass review, fastest path); escalate to light/standard/thorough/adversarial for multi-round review, fact-check, or external adversary pass. Optional `--memo <file>` falls back to file-memo style for deferred reviews."
argument-hint: "\"<prompt>\" [--qa quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]"
metadata:
  group: entry
  fam: doc
  modes: []
  blurb: "기존 문서·연구 산출물의 정정·갱신 entry — 버전 snapshot 보존"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 버전 스냅샷은 `_internal/versions/v{N}/` (modern, research·doc 공통) 또는 `_v{N}.md` 형제 (legacy doc). 자동 감지.

## Position in autopilot family

`autopilot-refine` is the **post-creation iteration** counterpart to the creation pipelines:
- `autopilot-research` / `autopilot-code` / `autopilot-draft` create artifacts (forward direction).
- `autopilot-refine` reads and updates existing artifacts (reverse direction).

Naming consistency: same `--qa quick|light|standard|thorough|adversarial` flag as the rest of the family. Default `thorough` (2026-05-22 통일 — 모든 autopilot-* default thorough). routine·scoped edits 자리는 `--qa light` / `quick` 명시.

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트는 사용자가 `<artifact-root>/{documents,research}/*` 하위 artifact에 대해 **major-level 변경**을 prompt로 요청할 때만 `/autopilot-refine` slash command 명시 없이도 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke 한다 (`--qa thorough` default). **minor-level 변경은 직접 Edit + `pipeline_summary.md` 상세 minor log 추가** (refine flow X, 컨펌 자체도 skip — 단순 minor 라 그냥 진행). 누적된 minor는 사용자가 `/audit`을 호출하거나, AUDIT_HINT_THRESHOLD (default 5 minors)를 넘으면 chat alert로 _권장_ 받아 batch 점검한다.

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

### Minor log entry 형식 (반드시 준수 — 추적성 핵심)

`pipeline_summary.md`의 (a) 버전 히스토리 표에 1줄 row 추가 + (b) `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션에 상세 block 추가 (newest entry 위쪽).

**(a) 버전 히스토리 row** (기존 표에 append):

```markdown
| v{N}_M | YYYY-MM-DD | (minor) 한 줄 요지 ≤120자 |
```

**(b) 마이너 변경 로그 entry** (없으면 섹션 신규 생성 — 위치: `## 미해결 이슈` 직전 또는 표 직후):

```markdown
### v{N}_M — YYYY-MM-DD HH:MM
- **Trigger**: 사용자 prompt verbatim 한 줄 인용 (≤80자)
- **Scope**: minor (직접 Edit, no snapshot)
- **Rationale**: 왜 minor로 분류했는지 (3-criteria 중 어디에도 해당 안 함 / 단일 entry 단위 / etc.)
- **Files touched**:
  - `relative/path/file1.md` — 무엇을 어떻게 바꿨는지 1-2줄
  - `relative/path/file2.md` — 무엇을 어떻게 바꿨는지 1-2줄
- **Cross-ref / deps**: 다른 mutation·label·downstream artifact와의 의존 (없으면 "—")
- **Audit-flag**: 향후 audit이 점검해야 할 측면 — `facts`/`style`/`structure`/`cross-ref`/`coverage` 중 해당 (none이면 "—")
- **Reversibility**: 이 변경을 되돌리려면 어디를 어떻게 (Edit 위치 + 원본 wording) — 없으면 "git revert 또는 last major snapshot reference"
```

> **Audit-flag**는 핵심 — 누적 minor 점검 시 audit이 각 entry의 audit-flag를 collate해 dual-perspective 첫 번째 pass (vs last major)를 효율적으로 scope.

**(c) 각 affected file frontmatter `changelog:` 1줄 entry** — file의 YAML frontmatter에 `changelog:` array가 정의돼 있으면, 새 version entry를 array 최상단에 insert:

```yaml
changelog:
  - version: v{N}_M
    date: "{YYYY-MM-DDTHH:MM}"
    applied: {count}
    overridden: 0
    entries:
      - |
        [MINOR {scope}] [direct Edit]: {1줄 변경 요약, ≤200자}
  - version: v{N}_{M-1}
    ... (기존 entries 보존)
```

frontmatter `changelog:` 필드 자체가 없는 file은 skip. **이 step은 pipeline_summary 마이너 로그 entry (위 b) 와 중복 layer**지만, in-file frontmatter는 git-tracked file 자체에 남아 `git log {file}` + frontmatter scan만으로 해당 파일의 변경 lineage 추적 가능 — pipeline_summary가 손상되거나 cross-artifact reference 시점에 유용.

### Major 적용 시 동작

`autopilot-refine --qa thorough` (default) 자동 invoke:

1. Stage A-D 정상 흐름 (investigate → diff preview → 자동 apply → snapshot)
2. snapshot: `_internal/versions/v{N+1}/` 생성
3. **누적 minor log migration**: pipeline_summary.md의 `## 마이너 변경 로그 (v{N} → next major)` 섹션 전체를 _verbatim_ 으로 새 major의 `## v{N+1} 변경 사항` 섹션 안 `### 누적 마이너 변경 사항 (v{N}_1 → v{N}_M)` sub-block 으로 migrate. 활성 마이너 로그 섹션 clear (다음 major까지 빈 상태).
4. `## 버전 히스토리` 표에 major row `| **v{N+1}** | ... | (major) ... |` 추가

### Override 1순위 (자동 룰 무시)

다음 중 하나라도 prompt에 있으면 위 분기 룰을 건너뛴다:

- 다른 qa level 명시 — `standard`/`thorough`/`adversarial` (강제 refine, level 명시)
- "refine 없이 직접 edit" / "Edit으로 처리" / "versioning 없이" / "snapshot 없이" — 강제 minor 경로
- `--review-only` — 검수만, 적용 X
- `/autopilot-refine` slash 명시 invoke — 강제 refine flow (qa level은 따로 명시 안 하면 `quick`)

### Why this split

대부분 일상 변경은 entry-level minor — 매 minor마다 refine flow (QA agent invocation + snapshot + version bump)를 묶는 건 cost 대비 가치 낮음. 단 **추적성은 유지**: 모든 minor가 `pipeline_summary.md` minor log에 trigger / files / audit-flag / reversibility까지 기록되므로 last major 이후 변경 이력은 _완전히_ 보존된다. 누적된 minor가 일정 임계치를 넘으면 audit이 **dual-perspective** (vs last major snapshot diff + vs universal principles)로 batch 점검 → fix chain dispatch. major는 _진짜 ceremony 시점_ (외부 검토 직전·구조 재설계·cycle 재진입)에만 refine flow의 ceremony cost를 발생시킨다.

> 본 섹션은 `/sync-skills`가 `<agent-home>/README.md`의 "운영 룰" 섹션으로 자동 반영한다.

## Scope

- **Targets**: `<artifact-root>/research/*` and `<artifact-root>/documents/*`
- **NOT for**: `<artifact-root>/plans/*` (code) — use `/code-refine`, `/code-execute`, or `/autopilot-code` instead. Code changes need test-based verification, not diff review.
- Why this skill exists: the existing `draft-refine` / `code-refine` workflow is file-memo only, which is too heavy for routine prompt-driven edits. `autopilot-refine` is the lightweight default; memo style is reduced to an opt-in fallback.

## --qa <level> (default: thorough)

QA 5 단계 정의 + 모델·round 매트릭스는 [`CONVENTIONS.md §1`](../../core/CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용 (proposed diff 에 pre-apply review):

| Level | Behavior on proposed diff |
|---|---|
| **quick** | Investigate → Stage B.5 (factual + style auto-detector, always on) → diff preview → apply. No internal review loop. Stage B.5 는 cards-grep + regex 만. |
| **light** | + 2× fast reviewers (다른 axes) single pass. obvious regression catch. |
| **standard** | + 1× deep reviewer + 2× fast reviewers (다른 axes) + 1× fast fact-checker (parallel, in-artifact ground truth verbatim 대조 — research: `cards/*.md`; doc: `analysis/*.md` + 기존 strategy/draft). round 1. |
| **thorough** (default) | + 2× deep reviewers + 2× fast reviewers (다른 axes) + 1× fast fact-checker. round 2. high-stakes refine 용. |
| **adversarial** | thorough + 1× external adversary (`codex-review-team` in Claude adapter). camera-ready / grant / public rebuttal 같은 외부 strong scrutiny 자리. |

Pre-apply review 만 — post-apply review 는 본 skill 범위 아님 (`/draft-refine` 사용).

> The two opt-out flags `--no-fact-check` and `--no-style-audit` are **orthogonal to every `--qa` level** — they skip the corresponding Stage B.5 aspect regardless of qa level. These are the _only_ disable mechanism per `feedback_factcheck_principles.md` Principle 0.

> **`adversarial` propagation**: at this tier, after the thorough reviewers return, spawn external adversary (`Agent(codex-review-team)` in Claude adapter) with (a) the proposed diff, (b) the artifact's intent (from `pipeline_summary.md`), and (c) the source ground-truth (research: `cards/*.md`; doc: `analysis/*.md` + existing strategy/draft). Surface external findings alongside internal reviewer findings before the user-confirm step. If the external adversary flags a blocking issue, mark it in the diff preview as `⚠ External: <issue>` so the user can decide whether to apply, revise, or abort.

## Mode Forms (orthogonal to --qa)

| Form | Behavior |
|---|---|
| `autopilot-refine "<prompt>"` | **Default (autopilot 정신)**: investigate → diff preview (chat에 출력만) → **자동 apply** + version + log. MECH/SEM 모두 자동. STRUCT만 halt (사용자에게 heavier flow 권장). 사후 검토는 `git diff` + `_internal/versions/v{prev}/` 스냅샷 + `pipeline_summary.md` history. |
| `autopilot-refine "<prompt>" --confirm` | Diff preview에서 chat-pause + 사용자 confirm 후 apply. _수정 전 검토_ 원할 때 명시. |
| `autopilot-refine "<prompt>" --review-only` | Investigate + diff preview. No edits, no version, no log. _점검만_ 원할 때. |
| `autopilot-refine --memo <file> "<prompt or artifact hint>"` | Read memo file as proposal source. Default 동작과 동일 (자동 apply). `--confirm` 추가 가능. |

> **Target artifact identification**: prompt에 포함된 키워드로 `<artifact-root>/{research,documents}/*` fuzzy match. 매치 1 → 사용. 다수 → 사용자에게 list 보여주고 선택 요청. 0 → "어느 산출물? prompt에 명시 부탁" 안내.

> **Default = 자동 apply 근거**: family 다른 멤버(`autopilot-research/code/doc`)는 모두 confirm 없이 pipeline 끝까지 실행 — autopilot 정신. refine만 default가 confirm이면 이름과 mismatch. Safety net: (a) `_internal/versions/v{prev}/` 스냅샷, (b) `pipeline_summary.md` 통합 history, (c) `git diff` 즉시 검토, (d) Stage B.5 `⚠ Unverified/Style` marker가 본문에 박혀 사후 git diff에서 식별 가능, (e) audit auto-fix chain dispatch와 정합.

> **STRUCT halt (escape hatch)**: 변경이 5+ files / 전체 section rewrite / autopilot pipeline 재실행 필요로 분류되면 _자동 apply 안 함_. halt + 사용자에게 heavier flow 권장 (`/autopilot-research --from analyze` 또는 `/autopilot-draft --from strategy`). 이건 default 변경 후에도 유지.

### Tunable constants

| Constant | Default | Description |
|---|---|---|
| `AUDIT_HINT_THRESHOLD` | 5 | Number of refine cycles after which Stage D emits a `/audit` recommendation hint. Set to a higher value (e.g., 10) to reduce hint frequency; set to `0` to disable the hint entirely. |

## Artifact Resolution

Extract candidate keywords from the `<prompt>` (skip stop words; pick noun-ish tokens like artifact names, topic names, dates). Run fuzzy match:

```bash
ls -d <artifact-root>/research/*<keyword>* <artifact-root>/documents/*<keyword>* 2>/dev/null
```

- **1 match** → use as artifact root. Detect type by path prefix.
- **Multiple matches** → list candidates to user, ask which.
- **0 matches** → ask user to clarify the artifact name in the prompt (e.g., "어느 산출물에 대한 작업인가요? prompt에 식별자(`speech-enhancement-trends`, `2026-05-06_se-seminar-tfrestormer` 같은) 포함 부탁"). adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) — ScheduleWakeup 10분 동시 호출, 답 없으면 가장 최근 수정된 artifact 로 자율 진행.

Detect type by path prefix:
- `<artifact-root>/research/*` → **research** type
- `<artifact-root>/documents/*` → **doc** type
- 그 외 (e.g., user typed an absolute path that's not a research/documents artifact) → error: "autopilot-refine은 research/documents 산출물 전용".

## Language Rule

All user-facing output (chat diffs, pipeline_summary entries, reports) in natural **Korean** (no translationese — write Korean natively, don't translate from an English draft).

> `<artifact-root>` 해석: `.agent_reports` 우선, legacy `.claude_reports` 는 이미 존재하고 `.agent_reports` 가 없을 때만 사용. 실제 쉘 명령에서는 `REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports` 로 치환한다.

---

## Process

### Stage A — Auto-discover structure

1. List `*.md` files at artifact root and one level deep (Glob `{root}/*.md` + `{root}/*/*.md`).
2. **Research** type:
   - Note `cards/*.md` as primary source. Don't read all upfront.
   - Read `pipeline_summary.md` if exists for context (1 file, small).
3. **Doc** type:
   - Identify `strategy/` and `draft/` subdirs and ko/en pairs (e.g., `strategy/strategy.md` ↔ `strategy/strategy_ko.md`).
   - Read `pipeline_summary.md` if exists.
4. Use grep with prompt keywords to identify likely-affected files. Don't read files that grep doesn't hit.

### Stage B — Plan changes

1. Read only the affected files identified in A.
2. For research taxonomy/definition/coverage prompts, also re-read relevant `cards/*.md` (primary source) — top-level files can drift over multi-edit cycles.
3. Build a per-file change list. Each change = `(file, line_range, old_text, new_text, classification, reason)`.
4. Classify each change:
   - **MECH** — count update, exact-string rename, table relabel, redundant-row merge with no info loss, label normalization.
   - **SEM** — wording shift, scope decision, non-trivial reframe, judgment call.
   - **STRUCT** — touches 5+ files OR rewrites whole sections OR requires re-running an autopilot pipeline.
5. **If STRUCT detected** → halt before Stage C. Recommend the user run a heavier flow:
   - Research: `/autopilot-research --from analyze` (full re-analysis)
   - Doc: `/autopilot-draft --from strategy` (full strategy/draft rebuild) or `/autopilot-refine "<artifact>" --memo <file>` (deferred memo style, this skill's `--memo` form)
   Do NOT proceed with the current autopilot-refine call.

### Stage B.5 — Factual claim & Style auto-detector (always runs, even in quick)

Runs after Stage B's per-file change list is built but BEFORE Stage C diff preview. The two detectors below execute on every proposed change regardless of `--qa` level — they are cards-grep / regex only, no web fetch, so cost is negligible. Their findings become markers in Stage C, not auto-rejections.

**Pre-check (flag-based opt-out, orthogonal to `--qa`)** — before either detector runs, inspect the original invocation argv:
- If `--no-fact-check` is present → **skip the factual claim detector entirely** (including the section-heading context cross-check). Emit one informational line at the top of Stage C diff preview: `ℹ Stage B.5 factual aspect: skipped via --no-fact-check flag (memory feedback_factcheck_principles 정책에 따른 명시적 opt-out)`. Style lint still runs.
- If `--no-style-audit` is present → **skip the style lint** only. Emit: `ℹ Stage B.5 style aspect: skipped via --no-style-audit flag`. Factual detector still runs.
- If both flags are present → both detectors skipped; both informational lines emitted.

These two flags are the _only_ mechanism by which the principles in `feedback_factcheck_principles.md` may be disabled (see Memory Principle 0). Ad-hoc prompt instructions like "Stage B.5 is noisy, disable it" must not be honored — emit the Principle 0 reminder line and proceed with detection anyway.

**1. Factual claim detector** — regex-scan each `new_text` for patterns matching factual claims that must be ground-truthed:
- Model names (camelCase / hyphenated / acronym-style, e.g., `FRCRN`, `TF-Locoformer`, `MP-SENet`, `IF-CorrNet`)
- Venue tags (e.g., `IS 2024`, `T-ASLP 2023`, `ICASSP 2025`, `Interspeech`, `NeurIPS`, `ICML`)
- Year + author patterns (`Luo 2017`, `[Wang et al., 2024]`)
- Task-category sentences (e.g., "denoising", "dereverberation", "general restoration", "universal SE", "BWE", "GSR")
- arXiv IDs (`\d{4}\.\d{4,5}`)

For each detected claim, look up ground truth. **Lookup source resolution (in priority order)**:
1. **case (c) — explicit `cards_source` override**: if the artifact's `pipeline_summary.md` frontmatter or `strategy.md` body contains a `cards_source: <path>` key, use _that path_ as the primary lookup root (resolved relative to cwd or absolute).
2. **case (b) — self-contained `cards/` inside the artifact**: if `{artifact_dir}/cards/*.md` exists (rare; some doc artifacts are self-contained), include it in the lookup set.
3. **Default**:
   - **Research artifacts** (`<artifact-root>/research/{topic}/cards/*.md`): grep the artifact's own `cards/` dir.
   - **Doc artifacts** (`<artifact-root>/documents/*/`): grep ALL `<artifact-root>/research/*/cards/*.md` files (cross-research lookup) — doc artifacts may reference cards from any research topic. Match by filename token AND by H1 / `## 메타` `**Venue**`/`**arXiv ID**` fields.
4. **case (a) — no cards source available**: if after resolving all the above the candidate file set is _empty_ (0 cards found in any of the above locations; e.g., autopilot-refine invoked from a workspace that has no research artifacts), the detector **skips the factual-claim aspect entirely** (style lint still runs). Stage C diff preview emits one informational line at the top: `ℹ Stage B.5: no cards source available in this workspace — fact-check skipped`. No `⚠ Unverified` markers are emitted. This prevents false-positive marker flooding in non-research workspaces.

For each claim (when cards are available), classify the lookup result per the _single-source classification table_ — **`adapters/claude/agents/research-team.md` _Fact-checker subrole_ 절** 의 8-row 표 (cards-verbatim / cards-name-only / external-marker / external-reverified / conflict / no-match / ambiguous / circular-ref). Stage B.5 본문은 orchestrator-side detector 이므로 _emit wording_ 만 본 절에 명시 (classification 정의 자체는 agent 본문이 single source — 향후 변경 시 agent 본문 한 곳만 갱신):

- **cards-verbatim ✅** — classify silently verified.
- **cards-name-only 🟡** — emit `⚠ Unverified (name-only match): {claim} — cards/{file}.md contains the name but no verbatim venue/metric. External reverify required (WebSearch/WebFetch)`.
- **external-marker 🟡** — emit `⚠ Unverified (external marker): {claim} — explicit external-estimation marker present. External reverify required`.
- **conflict 🔴** — emit `⚠ Unverified: {claim} — cards say {X} but new_text says {Y} (cards/{file}.md)`.
- **no-match 🔴** — emit `⚠ Unverified: {claim} — no cards/*.md hit`.
- **ambiguous 🟡** — emit `⚠ Unverified: {claim} — multiple candidates (cards/A.md, cards/B.md); user to pick`.

**Anti-pattern (circular reference) — explicitly FORBIDDEN**: do NOT treat the artifact's own `strategy/*.md` (especially its `## Style Guide` venue mapping table) as ground truth when verifying its `draft/*.md` claims, or vice versa. Both strategy and draft must be verified against `cards/*.md` _directly_. If a fact-checker is found comparing draft↔strategy and reporting ✅ on the basis of mutual agreement, mark as 🔴 architecture violation. (Incident reference: 2026-05-12 TF-Locoformer `IS 2024` → actually `IWAENC 2024` — strategy fact-checker passed on name-only match, draft fact-checker passed on strategy mirror, error survived two layers.)

**Section-heading context cross-check (MANDATORY)** — pure name matching alone lets WPE-class misclassifications (a classical method placed inside a "deep learning dereverb" table) pass through. For each detected claim, additionally:

1. Extract tokens from the _nearest enclosing section heading_ (H1-H3) in the target file (e.g., `## 딥러닝 dereverberation 모델` → `[딥러닝, dereverberation]`).
2. Extract tokens from the matched card's `## 분류` section (or equivalent label section) (e.g., `**방법론**: classical / statistical signal processing` → `[classical, statistical]`).
3. Check for _conceptual conflict_ between the two token sets using a predefined conflict-pair dictionary:
   - `{딥러닝, deep learning, neural, DNN}` ↔ `{classical, statistical, signal processing, non-learning}`
   - `{denoising, noise reduction}` ↔ `{dereverberation, reverb}` ↔ `{BWE, bandwidth extension}` ↔ `{GSR, general restoration, universal SE}`
   - `{single-task, sub-task}` ↔ `{universal, multi-task, GSR}`
4. On conflict (e.g., H1=딥러닝 but card=classical; H1=GSR timeline but card=BWE only), emit `⚠ Unverified: {claim} — section context "{heading tokens}" conflicts with card classification "{card tokens}" (card path: cards/{file}.md)`.

Without this cross-check, putting FRCRN in a dereverberation section, WPE in a deep-learning table, or AP-BWE in a GSR timeline would all pass the detector. The conflict-pair dictionary is hardcoded in v1; v2 enhancement can auto-derive pairs from cards' `## 분류` labels (domain-agnostic).

**2. Style lint** — compare `new_text` against immediate surrounding context (±10 lines in the target file):
- Citation format consistency (e.g., bullet list using `IS 2024` style vs new change using `Interspeech 2024` style → flag)
- Year/venue ordering inconsistency (e.g., surrounding uses `IS 2024 / arXiv:2402.XXXXX`, new uses `arXiv:2402.XXXXX (IS 2024)` → flag)
- Bullet depth jump (e.g., surrounding uses 2-level, new introduces 4-level → flag)
- Speaker note numbering style (e.g., `1. / 2. / 3.` vs `- / - / -` → flag)
- Figure caption template mismatch (if doc artifact has a recurring `**Figure N**: caption` pattern)

Emit `⚠ Style: {issue} — {1-line description of mismatch}` per finding.

**Skipped detection** is fine — both detectors are best-effort. False negatives are acceptable; false positives are harmless markers (user can override at Stage C).

### Stage C — Diff preview (chat)

Output to chat in this format:

```
**Quick refine — {artifact 한줄 식별}**

Prompt: "{prompt verbatim, ≤200자 trim}"

제안 변경 ({MECH 개수} mech / {SEM 개수} sem) — ⚠ {unverified 개수} unverified / {style 개수} style:

📄 `{relative path}` ({n} changes)
   Line {a}-{b}  [MECH|SEM]
     - {old_text 발췌, ≤80자}
     + {new_text 발췌, ≤80자}
     사유: {1줄}
     ⚠ Unverified: {claim} — {reason}    (Stage B.5 finding, if any)
     ⚠ Style: {issue} — {description}    (Stage B.5 finding, if any)

   Line {c}-{d}  [...]
     ...

📄 `{relative path 2}` ({n} changes)
   ...

(필요 시) 의도적으로 건드리지 않은 부분:
- `{path}:{line}` — {역사적 인용·논문 제목 등 사유}

다음: 적용 여부?
  - "yes" / "all" → 모두 적용
  - "1,3" → 해당 번호만
  - "skip 2" → 2번 제외
  - "skip-unverified" → ⚠ Unverified marker가 붙은 모든 변경 자동 제외
  - "edit 4: <new>" → 4번 텍스트 교체 후 적용
  - "no" / "stop" → 중단
```

**Default behavior — 자동 진행 (autopilot 정신)**: Stage C diff preview를 chat에 _출력만_ 하고, _자동으로_ Stage D 진행. Print one-line summary: `[auto-apply] {N_MECH} mech + {N_SEM} sem changes 적용 중... (STRUCT 0건)`. 사용자 _수정 가능_은 사후 `git diff` + 스냅샷에서.

**STRUCT halt 예외**: 변경 중 하나라도 STRUCT (5+ files / 전체 section rewrite)이면 _자동 apply 하지 않음_ — halt + heavier flow 권장 후 종료. (Stage B에서 이미 STRUCT detected halt 적용; 여기는 잔여 안전망.)

**`--confirm` mode (사용자 명시 시)**: Stage C diff 끝에 다음 instruction 추가 출력하고 chat-pause:
```
다음: 적용 여부?
  - "yes" / "all" → 모두 적용
  - "1,3" → 해당 번호만
  - "skip 2" → 2번 제외
  - "skip-unverified" → ⚠ Unverified marker가 붙은 모든 변경 자동 제외
  - "edit 4: <new>" → 4번 텍스트 교체 후 적용
  - "no" / "stop" → 중단
```
End turn. Wait for user reply. adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) — ScheduleWakeup 15분 동시 호출, 답 없으면 "yes / all" 추천 방향 (default auto-apply 패턴) 으로 자율 진행.

**`--review-only` mode**: print Stage C output, then end. No Stage D.

### Stage D — Apply

Parse the user's reply, then:

1. **Determine version**:
   - Read `{artifact_dir}/pipeline_summary.md`; find the highest `**v{N}**` row in the `## 버전 히스토리` table (or `**Latest version**` line).
   - If no version markers exist (artifact was never refined) → current state is implicit v1; next version = v2.
   - Else → next version = max + 1.

2. **Snapshot pre-edit state** (only files about to change). Detect convention from artifact:
   - **Modern** (`{artifact_dir}/_internal/` exists OR artifact is new) — use `_internal/versions/v{N}/`:
     ```
     {artifact_dir}/_internal/versions/v{prev}/{relative-path}
     ```
     - Research: e.g. `_internal/versions/v1/01_landscape.md`, `_internal/versions/v1/cards/2024_*.md`
     - Doc: e.g. `_internal/versions/v1/strategy/strategy.md`, `_internal/versions/v1/strategy/strategy_ko.md`, `_internal/versions/v1/draft/draft_ko.md`
     - `mkdir -p` parent dirs as needed.
   - **Legacy** (artifact has `_v{N}.md` siblings already AND no `_internal/` dir) — preserve existing pattern (draft-refine legacy):
     ```
     {file_dir}/{stem}_v{prev}.{ext}
     ```
     - e.g. `strategy/strategy_v3.md`
   - If a snapshot for the same prev version already exists, do NOT overwrite (don't double-snap).
   - On first apply to a fully-new artifact (no `_internal/`, no `_v{N}.md`): create `_internal/` dir and use modern pattern.

3. **Apply edits** via the Edit tool. Exact-string match. Never use `replace_all` unless explicitly stated in a proposal.

3b. **Inline memo cleanup (memo mode 전용)**: 메모 mode (`--memo <file>` 또는 inline `<!-- memo: ... -->` 소스)에서 모든 메모가 반영된 경우, _draft 안의 inline 메모도 함께 삭제_. 메모는 사용자의 _임시 review notes_이고 반영 후에는 stale이므로 _기본 삭제_가 정합. 예외: (a) 사용자가 _보존_ 명시 / (b) 메모 안에 _작업 외 메타 제안_이 있고 사용자에게 미해결로 알릴 가치 있는 경우 — 이 두 경우만 메모 보존하고, 다른 경우는 모두 메모 + 주변 빈 줄까지 함께 제거 (구분자 `---`는 보존).

4. **Update `pipeline_summary.md`** (single source of truth — no separate CHANGELOG):

   The artifact's `pipeline_summary.md` was created by the original autopilot-{research,doc} run. autopilot-refine accumulates version history into the same file rather than spawning a sibling log. Three places to touch:

   **(a) Top-level metadata** — update or add lines (idempotent):
   ```
   - **Latest version**: **v{N}** ({YYYY-MM-DD} — {prompt 한줄 요약 ≤60자})
   - **Status**: ✅ done (v{N}, 사용자 후속 검토 대기)
   ```
   If `**Latest version**` line doesn't exist (artifact was never refined), insert it just below the existing `**Date**` / `**Mode**` / `**Status**` block.

   **(b) `## 버전 히스토리` table** — insert NEW row at top of the table body:
   ```
   ## 버전 히스토리

   | 버전 | 일시 | 핵심 변경 |
   |---|---|---|
   | **v{N}** | {YYYY-MM-DD} | **{prompt 요약 + 핵심 변경 압축, ≤120자}** |
   | v{N-1} | ... | ... (기존 행 보존) |
   | v1 | ... | autopilot-{research,doc,...} 초기 생성 |
   ```
   If the section doesn't exist yet (this is the first refine), CREATE it right after the metadata block. The first row should be the initial creation: `| v1 | {creation date from frontmatter} | autopilot-{mode} 초기 생성 |`. Then the new v{N} row above it.

   **(c) `## v{N} 변경 사항` section** — append at end of file (or before `## 미해결 이슈` if exists):
   ```
   ## v{N} 변경 사항

   - **Mode**: {Quick chat-loop | Quick auto-applied | Memo}
   - **Prompt**: "{prompt verbatim, ≤200자 trim}"
   - **Reason**: {1-2줄}
   - **Files touched**:
     - `{path}:{line}` — {짧은 설명}
     - `{path}:{line}` — {짧은 설명}
   - **Skipped** (if any):
     - `{path}` — {SKIP 사유}
   - **Snapshot**: `_internal/versions/v{prev}/` (modern, both types) | `{stem}_v{prev}.md` (legacy doc)
   - **Downstream sync needed**: {Yes / No}
     - If Yes: `{dependent_artifact_path}` — {왜 영향받는지}
   ```

   **(d) Migrate accumulated minor log** — autopilot-refine은 Default Invocation Rule에 따라 **major-level**에만 invoke되므로, 본 stage가 도달했다는 것은 v{N-1}_1 ~ v{N-1}_M 누적 minor가 있을 수 있다는 뜻. `pipeline_summary.md`의 `## 마이너 변경 로그 (v{N-1} → next major 누적)` 섹션이 존재하면:

   1. 섹션 본문 전체를 _verbatim_ 으로 cut.
   2. 새 `## v{N} 변경 사항` 섹션의 끝에 다음 sub-block으로 paste:
      ```markdown
      ### 누적 마이너 변경 사항 (v{N-1}_1 → v{N-1}_M, audit consumed)
      
      {migrated minor log entries verbatim, newest-first 순서 유지}
      ```
   3. 활성 `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션을 _빈 상태_ 로 초기화 (헤더만 남기고 entries 제거):
      ```markdown
      ## 마이너 변경 로그 (v{N} → next major 누적)

      _(empty — 다음 minor에서 첫 entry 추가됨)_
      ```

   audit이 fix dispatch 후 major bump한 경우엔 audit log가 이미 누적분을 검토했으므로 위 sub-block 헤더에 ` — audit consumed` 마커 추가. audit 없이 사용자 직접 major refine한 경우엔 마커 생략 (단, audit 권장 alert를 Stage 5 report에 surface).

   **(e) Update in-file `changelog:` frontmatter** — 각 affected file의 YAML frontmatter에 `changelog:` array 필드가 정의돼 있으면, 새 version entry를 array 최상단(newest-first)에 insert. pipeline_summary.md의 메타 history (4(a)-4(d))와 _중복 layer_ 지만, in-file frontmatter는 _파일 자체의 git-tracked history_라 별도 보존 가치 있음 (특히 `git log {file}` + frontmatter scan만으로 해당 파일의 변경 lineage 추적 가능).

   형식 (`draft-refine` 컨벤션 mirror):

   ```yaml
   changelog:
     - version: v{N}
       date: "{YYYY-MM-DDTHH:MM}"
       applied: {count}
       overridden: 0
       entries:
         - |
           [{TYPE} {scope}] [verified {source}]: {1-2 line description per fix block, ≤300자}
         - |
           ...
     - version: v{N-1}
       ... (기존 entries 보존 — 절대 삭제 X)
   ```

   - `{TYPE}`: `STYLE`/`STRUCT`/`FACT`/`MEMO` 등 변경 성격. `{scope}`: section anchor or mutation ID.
   - `{verified source}`: ground-truth (cards / baseline file / 사용자 직접 지시 등).
   - `frontmatter changelog:` 필드 자체가 없는 file은 skip (e.g., research artifact의 일부 chapters).
   - 신규 file (changelog 처음 만드는 경우)이면 array 신설 + 직전 version (v{N-1}) 도 `{date: ..., note: "<creation date>의 pipeline 생성"}` 형식으로 1줄 add.

   These five updates together reproduce the integrated pattern users observe in manually-curated pipeline_summary files + per-file changelog (single file = full lifecycle, plus minor log migration trail, plus per-file changelog mirror).

5. **Report** to user (≤6 lines):
   ```
   ✓ autopilot-refine 완료 — v{prev} → v{N}
   • 수정 파일: {count}개
   • 스냅샷: {_internal/versions/v{prev}/ (modern) or _v{prev}.md (legacy doc)}
   • 갱신: {artifact_dir}/pipeline_summary.md (버전 히스토리 + v{N} 변경 사항)
   {if version_count >= AUDIT_HINT_THRESHOLD:}
   ⚠ refine cycle {version_count}회 누적 — audit 권장:
      /audit {artifact_short_name}
      (auto-scope: artifact 특성으로 aspect 자동 선택. 점검만 하려면 --report-only)
   {endif}
   {if downstream sync needed:}
   ⚠ 후속 동기화 필요:
     /autopilot-refine "{dependent_artifact_name} pipeline_summary v{N} 반영"
   ```

### Stage E — Memo mode (`--memo <file>`)

1. Read the memo file. Detect format:
   - **Structured** (per-file proposals like draft-refine memo style) → parse directly into Stage B's change list.
   - **Free-form** (just prose) → treat the body as the prompt, run Stage A-B-C internally.
2. Proceed to Stage D (with `Mode: Memo` recorded in pipeline_summary.md `## v{N} 변경 사항` section).

---

## Constraints

- **빈칸 > 잘못 채우기** — when Stage B.5 flags an `⚠ Unverified` claim and no ground-truth source confirms it within the artifact's `cards/` (or cross-research `<artifact-root>/research/*/cards/`), prefer to leave the claim **blank or marked `[?]`** in the new_text rather than filling it from inference. Applies even if the prompt seems to require the claim — emit the marker and let the user decide. Cost of a `[?]` placeholder is small; cost of a hallucinated venue/year/task is high (drift compounds over 20+ refine cycles).
- **No silent additions** — Stage D applies only what was shown in Stage C diff (or auto-mode summary). If a new issue is discovered during apply, abort that single edit and note it in the v{N} 변경 사항 section's `Skipped` list, but do NOT propose new edits beyond the original list.
- **Versioning is mandatory** when applying — every apply increments version + creates snapshot. Only `--review-only` skips this (because it doesn't apply).
- **Cards = primary source for research** — for taxonomy/definition/coverage prompts, always re-read `cards/*.md` and cite in reasoning.
- **Don't auto-rename historical citations** — paper titles, baseline names as published, specific challenge names. List these in Stage C as "intentionally untouched" if relevant.
- **Cross-artifact ripple is announced, not auto-propagated** — if a research change affects a downstream doc artifact, surface this in the v{N} 변경 사항 section's `Downstream sync needed` field. The user invokes `/autopilot-refine` again on the doc; this skill never auto-cascades.
- **STRUCT escape hatch** — if changes look structural, halt with a recommendation; don't try to handle structural rewrites in this skill.

---

## Examples

```
# Default — chat-loop with diff preview. Artifact inferred from prompt.
/autopilot-refine "speech-enhancement-trends에서 General Restoration과 Universal SE를 task family로 통합"
# (skill fuzzy-matches "speech-enhancement-trends" → research artifact, shows diff, ends turn)
# user replies: "all"
# → applies, snapshots to _internal/versions/v1/, updates pipeline_summary.md with v2 row + 변경 사항 section

# Auto-apply via prompt signal (no separate flag)
/autopilot-refine "speech-enhancement-trends Year×Paradigm heatmap의 2026년 칸 채우기. 확인 없이 자동 적용."

# Review only — no edits (artifact 식별자는 prompt에 포함)
/autopilot-refine "speech-enhancement-trends에서 최신 카드 5편이 분류표에 누락됐는지 검토" --review-only

# Memo mode — fall back to file-memo for deferred review
/autopilot-refine --memo .../review_memo.md "2026-05-06_se-seminar-tfrestormer 메모 반영"

# Doc artifact (auto-detected from prompt keyword)
/autopilot-refine "se-seminar-tfrestormer draft Slide 4 task family 표를 4행으로 변경"

# Higher QA — pre-apply reviewer pass
/autopilot-refine "se-seminar-tfrestormer 결론 챕터 wording 다듬기" --qa standard
```

## When NOT to use

- Single-file typo / cosmetic edit → just `Edit`.
- Code artifacts → `/code-refine`, `/code-execute`, `/autopilot-code`.
- Whole-axis structural redesign → `/autopilot-research --from analyze` or `/autopilot-draft --from strategy`.
- Pure deferred review (annotate over hours/days) → this skill's `--memo <file>` form (file-memo). `/draft-refine` 는 autopilot-draft 내부 sub-skill 이라 사용자 직접 호출 X.

## Post-Apply Checklist

After successful apply, suggest to user:
1. If `Downstream sync needed: Yes` → run `/autopilot-refine "{dependent_artifact_name} pipeline_summary v{N} 반영"` for each dependent artifact.
2. Optionally `git add -A && git commit -m "autopilot-refine: {prompt summary}"` if artifact is under git.
3. Run `/sync-skills` if this SKILL.md was just updated (rare — only when user iterates on the skill itself).
