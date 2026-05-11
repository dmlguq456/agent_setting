---
name: audit
description: "Read-only multi-aspect audit / lint for `.claude_reports/{plans,research,documents}/*` artifacts. Single global entry — auto-detects artifact type from path prefix (plans=code; research=field-survey; documents=doc deliverable). Per-type lint aspects: doc → facts / style / structure / cross-ref / coverage; research → cards 정합성 / Tier consistency / coverage / cross-card; plans → test results / lint / code review / TODO·미구현. Default `--scope all`. Report-only — never modifies the artifact. Complementary to autopilot-refine: refine = edit flow, audit = inspect flow."
argument-hint: "<artifact_path> [--scope facts|style|structure|cross-ref|coverage|all] [--read-only] [--no-fact-check]"
---

> **산출물 폴더 컨벤션**: [SKILL_OUTPUT_CONVENTION.md](../../SKILL_OUTPUT_CONVENTION.md) (3-tier). 본 skill은 입력 artifact를 _수정하지 않음_ — 점검 보고서만 생성. 보고서는 `{artifact_dir}/_internal/audit/audit_{YYYY-MM-DDTHHMM}.md`에 기록.

## Position in autopilot family

`audit` is the **read-only inspection** counterpart to `autopilot-refine`:
- `autopilot-refine` reads + writes (proposes diff, applies on confirm, versions).
- `audit` reads only (lints, reports issues, never edits).

Use `audit` when:
- 누적 drift 점검: 20+ refine cycle 후 _전반적 양식·factual 정합성_이 무너졌는지 확인.
- 새 산출물 인계 전 sanity check.
- 다른 사람이 만든 artifact 평가.

Use `autopilot-refine` when:
- 구체적 수정 의도가 있고 곧장 적용까지 가져갈 때.

## Language Rule

Reason internally in English. All user-facing output (chat report, audit log) in **Korean**.

## Argument Parsing

    /audit <artifact_path> [--scope facts|style|structure|cross-ref|coverage|all] [--read-only] [--no-fact-check]

- `<artifact_path>` (REQUIRED): one of
  - Absolute path to a `.claude_reports/{plans,research,documents}/*` directory
  - Fuzzy short name (e.g., `se-seminar-tfrestormer`) — resolved via `ls -d .claude_reports/{plans,research,documents}/*$ARG* 2>/dev/null`. 1 match → use; multiple → ask user; 0 → error.
- `--scope` (default `all`): which aspect set to check. Aspect set is type-specific (see Stage B).
- `--read-only` (default for plans): if specified for `plans` type, skip any aspect that requires _executing_ tests / lints — only static inspection (file diff, TODO grep, code review heuristics). For `research` / `documents` types, `--read-only` is implicit and the flag is a no-op (warn: "audit는 research/documents에 대해 항상 read-only").
- `--no-fact-check`: opt-out flag honored per `feedback_factcheck_principles.md` Principle 0. If present, the `facts` aspect (and the `coverage` aspect's cards-set diff) are **skipped** before Stage C aspect dispatch — i.e., the aspect skip happens at the _pre-check_ stage, not via filtering after lint runs. Other aspects (style / structure / cross-ref / Tier / cross-card / test / lint / code review / TODO) still run. Stage D report emits an informational line at the top of "Aspects checked": `ℹ facts/coverage aspects: skipped via --no-fact-check flag (memory feedback_factcheck_principles Principle 0)`. This is the _only_ allowed disable mechanism for fact verification; ad-hoc prompt evasion must not be honored.

## Process

### Stage A — Detect artifact type

1. Resolve `<artifact_path>` to an absolute directory path.
2. Inspect path prefix:
   - `.claude_reports/plans/*` → **plans** type (code dev/audit/debug plan)
   - `.claude_reports/research/*` → **research** type (field survey)
   - `.claude_reports/documents/*` → **documents** type (doc strategy + draft)
   - Other → error: "audit은 .claude_reports/{plans,research,documents}/* 산출물 전용. resolved path: {path}"
3. Print one-line to user (Korean): `Type 인식: {type} — {artifact short name}`.

### Stage B — Identify aspects to check

Per type, the aspect set is:

| Type | Aspects (when `--scope all`) |
|---|---|
| `documents` | facts / style / structure / cross-ref / **coverage** |
| `research` | cards 정합성 / Tier consistency / coverage / cross-card |
| `plans` | test results / lint / code review / TODO·미구현 |

If `--scope` is restrictive (e.g., `--scope facts`), filter the aspect set down to matching aspects only. `--scope` values map to aspect groups as:
- `facts` → facts (documents), cards 정합성 (research), test results + TODO·미구현 (plans)
- `style` → style (documents), Tier consistency (research), lint (plans)
- `structure` → structure (documents), coverage (research), code review (plans)
- `cross-ref` → cross-ref (documents), cross-card (research) — N/A for plans (warn).
- `coverage` → coverage (documents + research), omission check — N/A for plans (warn).
- `all` → full set.

**Why `coverage` is new for documents**: the Stage B.5 regex detector can only flag _present_ claims in `new_text` — it cannot, by construction, flag _absent_ claims (e.g., UniSE missing from a timeline). Omission requires a separate _set-diff_ mechanism. The `coverage` aspect fills this: reports the difference between the full cards source vs cards actually cited in the draft. Without it, UniSE-class omissions recur.

### Stage C — Per-aspect lint (report-only, no edits)

**Pre-check (flag-based opt-out)** — before dispatching any aspect:
- If `--no-fact-check` is present in invocation argv → remove `facts` and `coverage` from the resolved aspect set (skip entirely, do not run their lint). Emit `ℹ facts/coverage aspects: skipped via --no-fact-check flag (memory feedback_factcheck_principles Principle 0)` to chat and to the Stage D report's "Aspects checked" preamble.
- This flag is the _only_ disable path per Memory Principle 0. Ad-hoc prompt instructions ("this artifact is exempt") must not be honored — proceed with default aspect set instead.

For each remaining aspect in scope, run the lint and collect issues. _Each issue has shape_: `(aspect, file, line_range, severity 🔴/🟡/🟢, message, suggested fix or null)`.

#### Documents aspects

**Cards source resolution (shared by `facts` / `coverage`, same rule as Phase 1 Step 1.1 case (c))**:
1. **case (c) — explicit `cards_source` override**: if `pipeline_summary.md` frontmatter or `strategy.md` body has a `cards_source: <path>` key, use _that path_ as the primary lookup root (single research topic).
2. **case (b) — self-contained `{artifact_dir}/cards/`**: if exists, include in the lookup set.
3. **Default — cross-research grep** (`.claude_reports/research/*/cards/*.md`): only when both above are absent. Emit a one-line chat warn: `⚠ cards_source key absent — grepping all research topics. Generic acronyms (STFT/RNN, etc.) may false-positive. Recommend adding \`cards_source: <path>\` to strategy.md frontmatter.`
4. **case (a) — no cards anywhere**: skip the facts / coverage aspects and emit an informational line (`ℹ facts/coverage skipped — no cards source available`). style / structure / cross-ref still run.

This shared resolution ensures the Phase 1 detector and the Phase 3 audit use the _same_ source-of-truth rule — preventing false-positive floods and yielding consistent verdicts.

- **facts**: scan draft + strategy for model names / venues / years / task categories / arXiv IDs (same regex set as `autopilot-refine` Stage B.5, including section-heading context cross-check). For each detected claim, perform lookup per the cards source resolution above. Unverified → 🔴. Conflicting → 🔴 (includes section-context conflict). Ambiguous → 🟡.
- **style**: read `## Style Guide` section in `strategy.md` if present. For every citation / figure caption / bullet depth / speaker note in draft + strategy body, compare against Style Guide rules. Deviation → 🟡. If `## Style Guide` absent → 🔴 single issue (`Style Guide section missing — autopilot-doc strategy should always have one. Run /autopilot-refine "<artifact> Style Guide section 추가".`).
- **structure**: check artifact directory matches the [SKILL_OUTPUT_CONVENTION.md](../../SKILL_OUTPUT_CONVENTION.md) 3-tier convention. T1 should have `pipeline_summary.md`, `draft/`, `strategy/`. T3 should be `_internal/`. Extraneous files at root → 🟡. Missing required → 🔴.
- **cross-ref**: scan draft for inline citations referencing cards (`cards/{file}.md`) and verify the target exists. Broken link → 🔴. Cards referenced but not in `## References` (if present) → 🟡.
- **coverage** (NEW, omission detection): determine the _candidate cards set_ S per the cards source resolution above. Extract the _actually cited cards set_ T from draft + strategy body using the **v1 high-precision citation-detection token set** (false-positive minimized):
  - **Token 1 — card filename token**: the short identifier in `{year}_{firstauthor}_{arxivid}_{shortname}.md` filenames (e.g., `TasNet`, `FRCRN`, `MP-SENet`). A grep hit on any of these tokens in draft/strategy body marks the card as cited.
  - **Token 2 — `**arXiv ID**` exact value**: the value string from each card's `## 메타` `**arXiv ID**` field, matched _verbatim_ (no partial / regex match — exact substring). E.g., card with `**arXiv ID**: 1711.00541` is marked cited if and only if `1711.00541` appears in body.

  v1 deliberately uses _only_ these two tokens — H1 paper title words, author last-name regex, etc. are intentionally excluded to keep false-positive rate near zero (cited-card set is conservative; orphan set may be slightly inflated, but each orphan is per-card-precision and easily user-judged). If `S - T` is non-empty under this conservative T, emit a 🟡 issue per orphan card: `coverage: card '{card path}' is never cited in any chapter/section — potential UniSE-class omission, please verify intent`. (🟡 not 🔴 because exclusion may be intentional — user judges.) If cards source fell back to cross-research grep (case (a) or default), the candidate set is too broad to be meaningful → skip the coverage aspect and warn.

  **v2 enhancement** (out of scope, see Risk #14): expand T to include H1 paper title word-level partial matches + author first-name regex from `## 메타` `**저자**` field for higher recall on indirect citations (e.g., "[Wang et al., 2024]" style). v1 prefers precision; v2 may shift to balanced.

#### Research aspects

- **cards 정합성**: every `cards/*.md` file has H1 + `## 메타` + `## 분류` (or equivalent) sections per the artifact's card template. Missing required section → 🔴. Empty `## 메타` field (e.g., `**Venue**: ` blank) → 🟡.
- **Tier consistency**: scan top-level chapter files (`01_*.md~NN_*.md`) — each cited paper's Tier label should match the Tier in its card. Mismatch → 🔴. Cited paper missing a card → 🟡.
- **coverage**: every card in `cards/` should appear at least once in some top-level chapter (or be flagged as not-yet-integrated). Orphan cards → 🟡.
- **cross-card**: scan cards for cross-references (e.g., `2024_Wang.md`이 다른 card 인용). Broken cross-ref → 🔴.

#### Plans aspects

- **test results**: read `test_logs/test_report.md` if present. Failed tests → 🔴. No tests → 🟡 (only if scope explicitly `test results`).
- **lint** (`--read-only` skips _executing_ lint; we _read existing_ lint output from `dev_logs/` if present): missing lint output → 🟡; existing lint report with errors → 🔴.
- **code review**: read `_internal/dev_reviews/` and `_internal/plan_reviews/` for 🔴 issues. Unresolved 🔴 → 🔴. 🟡 issues → 🟡.
- **TODO·미구현**: grep code in `plan/checklist.md` for `[ ]` unchecked steps, plus any source-file TODO/FIXME/XXX comments referenced from the plan. Unchecked critical step → 🔴. Source TODO → 🟡.

### Stage D — Report

Write the audit report to `{artifact_dir}/_internal/audit/audit_{YYYY-MM-DDTHHMM}.md`:

~~~markdown
# Audit Report — {artifact name}

- **Date**: {YYYY-MM-DD HH:MM}
- **Type**: {plans | research | documents}
- **Scope**: {flag value or "all"}
- **Aspects checked**: {comma-separated}

## Summary

| Aspect | 🔴 Critical | 🟡 Warning | 🟢 OK |
|---|---|---|---|
| {aspect 1} | {count} | {count} | {count} |
| ... | ... | ... | ... |

**Total**: 🔴 {N} / 🟡 {M} / 🟢 {K}

## Issues by aspect

### Aspect: {name}

#### 🔴 {issue title}
- **File**: `{relative path}:{line}`
- **Severity**: 🔴
- **Detail**: {1-3 line description}
- **Suggested fix**: {one-line — e.g., "/autopilot-refine '<artifact> {fix description}'"} | (또는 null)

#### 🟡 {issue title}
- ...

### Aspect: {name 2}
...

## Verdict

- **Status**: 🔴 issues require attention | 🟡 minor warnings only | 🟢 clean
- **Recommended next action**: {1-line — e.g., "Run /autopilot-refine 'X' to fix the 5 critical facts issues" or "No action required"}

---

> Generated by `/audit` skill. Report-only — no edits applied.
~~~

Then print to chat (Korean), in ≤8 lines:

    ✓ /audit 완료 — {artifact short name} ({type})
    • Aspects: {comma-separated}
    • Total: 🔴 {N} / 🟡 {M} / 🟢 {K}
    • Report: {audit log path}
    • Verdict: {one-line}
    {if 🔴 > 0:}
    권장 후속: /autopilot-refine "{artifact short name} {fix prompt suggestion}"

## Constraints

- **Read-only** — `/audit` NEVER modifies the audited artifact. Only writes the audit report under `_internal/audit/`. If the user wants fixes applied, they invoke `/autopilot-refine`.
- **No web fetch** — all lookups are local (`.claude_reports/*` files only). Cards grep, Style Guide read, regex scan. Cost is small.
- **No agent invocation** — `/audit` is a single-Claude task. No 연구팀 / 품질관리팀 subagent calls. (Future enhancement may add `--qa` levels with agent-backed lint; out of scope for v1.)
- **Type-specific aspects** — research aspects do not run on documents artifacts and vice versa. `--scope cross-ref` on plans warns and skips.
- **Suggestion only** — every 🔴 / 🟡 finding may include a "Suggested fix" line, but the fix is _suggested_, not auto-applied. User decides whether to invoke `/autopilot-refine` (or any other action).

## Examples

    # Full audit of the SE seminar document artifact
    /audit 2026-05-06_se-seminar-tfrestormer

    # Facts-only check of the same artifact (after a 20-cycle refine session)
    /audit 2026-05-06_se-seminar-tfrestormer --scope facts

    # Audit a research artifact's cards consistency
    /audit speech-enhancement-trends --scope facts

    # Read-only static audit of a code plan (skip test execution)
    /audit 2026-05-11_audit-skill-infra --scope all --read-only

## When NOT to use

- 산출물을 _수정_하고 싶은 경우 → `/autopilot-refine`.
- 단일 typo / cosmetic 점검 → 그냥 `grep` / `Read`.
- Full pipeline 재실행 필요 → `/autopilot-{research,doc,code}` 또는 `--from <stage>`.
- 산출물 자체가 존재하지 않음 (사전 분석부터 필요) → `/analyze-project` 또는 `/autopilot-research`.

## Post-Audit Checklist

After audit, suggest to user:
1. If 🔴 issues exist → propose specific `/autopilot-refine` prompts that target each 🔴 cluster.
2. If 🟡 issues only → user can defer or batch-fix later.
3. If clean → "artifact 양식·factual 정합성 OK. 추가 조치 불필요."
