---
name: autopilot-refine
description: Autopilot family — post-creation iteration pipeline for research and doc artifacts (NOT code). Prompt-driven: target artifact identified via prompt fuzzy match against `.claude_reports/{research,documents}/*`, then auto-discovers the artifact's file structure, plans edits, shows a diff preview in chat, and on user confirm applies edits with versioning + integrated history logging in `pipeline_summary.md` (single source of truth — no separate CHANGELOG). Default `--qa quick` (1-pass review, fastest path); escalate to light/standard/thorough/adversarial for multi-round review, fact-check, or external Codex adversarial pass. Optional `--memo <file>` falls back to file-memo style for deferred reviews.
argument-hint: "\"<prompt>\" [--qa quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--no-fact-check] [--no-style-audit]"
---

> **산출물 폴더 컨벤션**: [SKILL_OUTPUT_CONVENTION.md](../../SKILL_OUTPUT_CONVENTION.md) (3-tier). 버전 스냅샷은 `_internal/versions/v{N}/` (modern, research·doc 공통) 또는 `_v{N}.md` 형제 (legacy doc). 자동 감지.

## Position in autopilot family

`autopilot-refine` is the **post-creation iteration** counterpart to the creation pipelines:
- `autopilot-research` / `autopilot-code` / `autopilot-doc` create artifacts (forward direction).
- `autopilot-refine` reads and updates existing artifacts (reverse direction).

Naming consistency: same `--qa quick|light|standard|thorough|adversarial` flag as the rest of the family, but with `quick` as the **default** (because the skill targets routine, scoped edits — not full re-creation).

## Scope

- **Targets**: `.claude_reports/research/*` and `.claude_reports/documents/*`
- **NOT for**: `.claude_reports/plans/*` (code) — use `/refine-plan`, `/execute-plan`, or `/autopilot-code` instead. Code changes need test-based verification, not diff review.
- Why this skill exists: the existing `refine-doc` / `refine-plan` workflow is file-memo only, which is too heavy for routine prompt-driven edits. `autopilot-refine` is the lightweight default; memo style is reduced to an opt-in fallback.

## --qa <level> (default: quick)

| Level | Behavior |
|---|---|
| **quick** (default) | Single-pass: investigate → **Stage B.5 (factual + style auto-detector, always on)** → diff preview → apply. No internal review loop on proposed changes (no agent invocation). Stage B.5 is cards-grep + regex only — no web fetch, no reviewer subagent. |
| **light** | Adds a 1× quality reviewer (sonnet) pass on the proposed diff before showing it. Catches obvious regressions but stays fast. |
| **standard** | Adds 1× quality reviewer (opus) + 1× fact-checker (sonnet, parallel) on the proposed diff. Verbatim 대조 against in-artifact ground truth — research: `cards/*.md`; doc: `analysis/*.md` + 기존 strategy/draft 본문. 외부 refs PDFs는 재독 안 함. |
| **thorough** | 2× quality reviewers (opus, parallel) + 1× fact-checker. Use for high-stakes refines (final-version paper draft, public-facing report). |
| **adversarial** | `standard` (1× quality opus + 1× fact-checker, parallel) + **Codex external adversarial review** via `Agent(codex-review-team)` on the proposed diff. Use when the artifact will face strong external scrutiny (camera-ready paper, grant submission, public rebuttal) — Codex acts as a hostile reader. Slowest tier. |

Higher levels add a pre-apply review pass on the planned diff — they do NOT add post-apply review (that's not what this skill is for; use `/refine-doc` if you want full memo-style review cycles).

> The two opt-out flags `--no-fact-check` and `--no-style-audit` are **orthogonal to every `--qa` level** — they skip the corresponding Stage B.5 aspect regardless of qa level. These are the _only_ disable mechanism per `feedback_factcheck_principles.md` Principle 0.

> **`adversarial` propagation**: at this tier, after the standard reviewers return, spawn `Agent(codex-review-team)` with (a) the proposed diff, (b) the artifact's intent (from `pipeline_summary.md`), and (c) the source ground-truth (research: `cards/*.md`; doc: `analysis/*.md` + existing strategy/draft). Surface Codex findings alongside internal reviewer findings before the user-confirm step. If Codex flags a blocking issue, mark it in the diff preview as `⚠ Codex: <issue>` so the user can decide whether to apply, revise, or abort.

## Mode Forms (orthogonal to --qa)

| Form | Behavior |
|---|---|
| `autopilot-refine "<prompt>"` | **Default**: investigate → diff preview → user confirm → apply + version + log |
| `autopilot-refine "<prompt>" --review-only` | Investigate + diff preview. No edits, no version, no log. |
| `autopilot-refine --memo <file> "<prompt or artifact hint>"` | Read memo file as proposal source (compat with refine-doc memo style). Apply same as default. |

> **Target artifact identification**: prompt에 포함된 키워드로 `.claude_reports/{research,documents}/*` fuzzy match. 매치 1 → 사용. 다수 → 사용자에게 list 보여주고 선택 요청. 0 → "어느 산출물? prompt에 명시 부탁" 안내.

> Auto-apply behavior: if the user explicitly writes "확인 없이 적용" / "자동 적용" / "그대로 적용" in the prompt AND all classified changes are MECH (no SEM/STRUCT), the skill may skip the confirm step and apply directly. Otherwise the default chat-pause-and-confirm always applies. (Translation: the prompt itself is the auto-apply signal — no separate flag.)

### Tunable constants

| Constant | Default | Description |
|---|---|---|
| `AUDIT_HINT_THRESHOLD` | 5 | Number of refine cycles after which Stage D emits a `/audit` recommendation hint. Set to a higher value (e.g., 10) to reduce hint frequency; set to `0` to disable the hint entirely. |

## Artifact Resolution

Extract candidate keywords from the `<prompt>` (skip stop words; pick noun-ish tokens like artifact names, topic names, dates). Run fuzzy match:

```bash
ls -d .claude_reports/research/*<keyword>* .claude_reports/documents/*<keyword>* 2>/dev/null
```

- **1 match** → use as artifact root. Detect type by path prefix.
- **Multiple matches** → list candidates to user, ask which.
- **0 matches** → ask user to clarify the artifact name in the prompt (e.g., "어느 산출물에 대한 작업인가요? prompt에 식별자(`speech-enhancement-trends`, `2026-05-06_se-seminar-tfrestormer` 같은) 포함 부탁").

Detect type by path prefix:
- `.claude_reports/research/*` → **research** type
- `.claude_reports/documents/*` → **doc** type
- 그 외 (e.g., user typed an absolute path that's not a research/documents artifact) → error: "autopilot-refine은 research/documents 산출물 전용".

## Language Rule

Reason internally in English. All user-facing output (chat diffs, pipeline_summary entries, reports) in **Korean**.

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
   - Doc: `/refine-doc <name>` (memo-based deferred) or `/autopilot-doc --from strategy`
   Do NOT proceed with autopilot-refine.

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
   - **Research artifacts** (`.claude_reports/research/{topic}/cards/*.md`): grep the artifact's own `cards/` dir.
   - **Doc artifacts** (`.claude_reports/documents/*/`): grep ALL `.claude_reports/research/*/cards/*.md` files (cross-research lookup) — doc artifacts may reference cards from any research topic. Match by filename token AND by H1 / `## 메타` `**Venue**`/`**arXiv ID**` fields.
4. **case (a) — no cards source available**: if after resolving all the above the candidate file set is _empty_ (0 cards found in any of the above locations; e.g., autopilot-refine invoked from a workspace that has no research artifacts), the detector **skips the factual-claim aspect entirely** (style lint still runs). Stage C diff preview emits one informational line at the top: `ℹ Stage B.5: no cards source available in this workspace — fact-check skipped`. No `⚠ Unverified` markers are emitted. This prevents false-positive marker flooding in non-research workspaces.

For each claim (when cards are available), classify the lookup result:
- **verified** (exact match in cards) — proceed silently.
- **unverified** (no match, or partial match with conflicting venue/year/task) — emit `⚠ Unverified: {claim} — {one-line reason: e.g., "no cards/*.md hit for FRCRN", "cards say IS 2024 but draft says ICASSP 2024"}`.
- **ambiguous** (multiple candidate cards, no single best match) — emit `⚠ Unverified: {claim} — multiple candidates (cards/A.md, cards/B.md); user to pick`.

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

End turn. Wait for user reply.

**Auto-apply (prompt-driven)**: if the prompt contains an explicit auto-apply signal (`자동 적용` / `확인 없이 적용` / `그대로 적용`) AND all classified changes are MECH, skip the chat pause and proceed directly to Stage D. Print a one-line summary instead: `[auto-apply] {N} mech changes 적용 중...`. If any SEM/STRUCT exists, ignore the signal and fall back to chat-pause as usual.

**`--review-only` mode exception**: print Stage C output, then end. No Stage D.

### Stage D — Apply (after user confirms)

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
   - **Legacy** (artifact has `_v{N}.md` siblings already AND no `_internal/` dir) — preserve existing pattern (refine-doc legacy):
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

   These three updates together reproduce the integrated pattern users observe in manually-curated pipeline_summary files (single file = full lifecycle).

5. **Report** to user (≤6 lines):
   ```
   ✓ autopilot-refine 완료 — v{prev} → v{N}
   • Files touched: {count}
   • Snapshot: {_internal/versions/v{prev}/ (modern) or _v{prev}.md (legacy doc)}
   • Updated: {artifact_dir}/pipeline_summary.md (버전 히스토리 + v{N} 변경 사항)
   {if version_count >= AUDIT_HINT_THRESHOLD:}
   ⚠ {version_count} refine cycles accumulated — recommend running an audit:
      /audit {artifact_short_name} --scope facts
      (read-only facts/style/structure check — no edits, 1-2 minutes)
   {endif}
   {if downstream sync needed:}
   ⚠ Downstream sync 필요:
     /autopilot-refine "{dependent_artifact_name} pipeline_summary v{N} 반영"
   ```

### Stage E — Memo mode (`--memo <file>`)

1. Read the memo file. Detect format:
   - **Structured** (per-file proposals like refine-doc memo style) → parse directly into Stage B's change list.
   - **Free-form** (just prose) → treat the body as the prompt, run Stage A-B-C internally.
2. Proceed to Stage D (with `Mode: Memo` recorded in pipeline_summary.md `## v{N} 변경 사항` section).

---

## Constraints

- **빈칸 > 잘못 채우기** — when Stage B.5 flags an `⚠ Unverified` claim and no ground-truth source confirms it within the artifact's `cards/` (or cross-research `.claude_reports/research/*/cards/`), prefer to leave the claim **blank or marked `[?]`** in the new_text rather than filling it from inference. Applies even if the prompt seems to require the claim — emit the marker and let the user decide. Cost of a `[?]` placeholder is small; cost of a hallucinated venue/year/task is high (drift compounds over 20+ refine cycles).
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
- Code artifacts → `/refine-plan`, `/execute-plan`, `/autopilot-code`.
- Whole-axis structural redesign → `/autopilot-research --from analyze` or `/autopilot-doc --from strategy`.
- Pure deferred review (annotate over hours/days) → `/refine-doc` (file-memo) or this skill's `--memo` form.

## Post-Apply Checklist

After successful apply, suggest to user:
1. If `Downstream sync needed: Yes` → run `/autopilot-refine "{dependent_artifact_name} pipeline_summary v{N} 반영"` for each dependent artifact.
2. Optionally `git add -A && git commit -m "autopilot-refine: {prompt summary}"` if artifact is under git.
3. Run `/sync-skills` if this SKILL.md was just updated (rare — only when user iterates on the skill itself).
