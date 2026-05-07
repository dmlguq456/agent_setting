---
name: refine-doc
description: Reflect user memos/review feedback in a document strategy or draft. Versioned output (`*_v1.md`, `*_v2.md`, ...) with auto-managed CHANGELOG block at top. Mandatory ref-grounding per memo (re-read source; override memo if it conflicts with source).
argument-hint: "<strategy or draft name or path> [--qa quick|light|standard|thorough]"
---

## Document Resolution
Resolve `$ARGUMENTS` to document file paths. Detect whether this is a **strategy** or **draft** refinement:

**Auto-detect document type**:
- If path contains `/draft/` → draft mode (resolve `draft.md` + `draft_ko.md`)
- If path contains `/strategy/` → strategy mode (resolve `strategy.md` + `strategy_ko.md`)
- If path is a directory → default to strategy mode

**Resolution rules** — always resolve BOTH English and Korean files:
1. If it ends with `.md` → use as-is; derive the other file by path swap (`draft.md` ↔ `draft_ko.md`, or `strategy.md` ↔ `strategy_ko.md`)
2. If it's a directory path → append `/strategy/strategy.md` (English) and `/strategy/strategy_ko.md` (Korean)
3. Otherwise, fuzzy search: `ls -d .claude_reports/documents/*$ARGUMENTS* 2>/dev/null`
   - **1 match** → use `{match}/strategy/strategy.md` and `{match}/strategy/strategy_ko.md`
   - **Multiple matches** → ask user
   - **No match** → report error

## Language Rule
- Think and reason in English internally. Write all user-facing output in Korean.

## Pre-Refine: Versioning Setup

Before invoking 연구팀, the orchestrator establishes versioning:

1. **Determine next version number**: scan the doc directory (`{ko_path.parent}`) for existing `*_v*.md` siblings. Find max N from `{ko_path.stem}_v{N}.md`. If none found, current state is implicit v1 — set `next_version = 2`.
2. **Snapshot current state as previous version** (only if `_v1.md` doesn't exist yet, i.e., this is the first refine):
   ```bash
   cp {ko_path} {ko_path.parent}/{ko_path.stem}_v1.md
   cp {en_path} {en_path.parent}/{en_path.stem}_v1.md
   ```
   This preserves the original initial state.
3. **Pass `next_version`, `prev_version`, and version archive paths to 연구팀** in the prompt below.

## Delegate to 연구팀
Invoke the **research-team** (연구팀) agent as a subagent with the following prompt:

```
Refine mode (versioned + ref-grounded). Update an existing document {doc_type} based on user memos and review feedback.

Korean {doc_type} file (current/latest): {ko_path}
English {doc_type} file (current/latest): {en_path}
Previous version archive (immutable): {ko_path.parent}/{ko_path.stem}_v{prev_version}.md (and English equivalent)
Next version: v{next_version}

## Memo Detection
Read the Korean {doc_type} and find all user memos. Memos can appear in any of these formats:
- `<!-- memo: ... -->` (standard memo tag)
- `<!-- ... -->` (HTML comment — treat any HTML comment as a user memo, EXCEPT the CHANGELOG block at top-of-file which is auto-managed)
- `// ...` (inline comment)
- `[memo] ...` (bracketed annotation)
- `(**...**)` (parenthetical note)
- Any other text marked as a user annotation. Do NOT treat the document's original author-written prose as a memo.

## MANDATORY Ref-Grounding Per Memo (CRITICAL — quality requirement)

For EACH memo found, before applying any change:
1. **Identify the relevant source(s)** the memo pertains to:
   - Paper card (`{refs}/cards/*.md`) — for citation, venue, score, NFE, RTF, dataset facts
   - Strategy document (`{artifact_root}/strategy/strategy.md`) — for narrative arc, slide outline alignment
   - Analysis files (`{artifact_root}/analysis/*.md`) — for audience, key messages, visual strategy
   - Reference PDFs (`{refs}/`) — for nuanced claims requiring re-reading the original paper
2. **Re-read the identified source** before applying the change. Do not rely on the memo's claim alone.
3. **Compare memo claim vs source**:
   - If memo agrees with source → apply the change as memo suggests.
   - If memo CONFLICTS with source → **override the memo, keep the original draft text, and document the conflict in changelog**. Do NOT silently propagate user error.
   - If source is ambiguous → apply the change but flag in changelog with `[CAUTION: source ambiguous]`.
4. **Record source verified** in the changelog entry: `[verified cards/2020_Hu_DCCRN.md]` or `[strategy section 4 confirmed]`.

For draft refinement: also cross-check against the strategy document at `{artifact_root}/strategy/` to verify the draft faithfully reflects all strategy points.

## Output Versioning

1. **Write the new content to current files** (`{ko_path}`, `{en_path}`) — these always represent the latest version.
2. **Also write to versioned archive** for permanent record:
   ```
   {ko_path.parent}/{ko_path.stem}_v{next_version}.md
   {en_path.parent}/{en_path.stem}_v{next_version}.md
   ```
   Both copies have identical content (current = latest = v{next_version}).
3. **Remove all memo comments** (HTML comments, `// ...`, `[memo] ...`, etc.) from the new version. EXCEPT preserve/update the CHANGELOG block (see below).

## CHANGELOG Block (auto-managed, top of file)

The very first content of both Korean and English latest files is the CHANGELOG, in this exact format:

```markdown
<!-- CHANGELOG (auto-managed by refine-doc — do NOT edit manually)
v{next_version} ({YYYY-MM-DDTHH:MM}, applied {N} memos / overrode {M} memos):
  - [Slide N | Section X] [verified <source>]: <one-line description of change>
  - [Slide N | Section X] [verified <source>]: <change>
  - [Slide N | Section X] [OVERRIDDEN — memo conflicted with <source>]: <reason>
  ...
{previous CHANGELOG entries preserved verbatim}
-->
```

If no CHANGELOG block exists yet (first refine), create one with:
- v1 entry: `v1 ({creation date or "initial"}): initial draft from autopilot-doc {mode} pipeline`
- v2 entry: this round's changes

If CHANGELOG already exists, prepend the new v{next_version} entry above the existing block content (newest first).

## Other rules
- Do NOT touch the version archive of previous versions (`*_v{prev_version}.md` and earlier) — they are immutable historical record.
- Do NOT skip ref-grounding even if memo seems trivial. Trivial-looking memos can have hidden errors.
- Return which sections were changed, which memos applied vs overridden, and the new version number.
```

Where `{doc_type}` is either "strategy" or "draft" based on auto-detection.

## QA Scaling
Auto-detect from sections changed. Two reviewer roles run **in parallel** at Standard+:
- **Quality reviewer**: narrative arc / cohesion / audience fit / strategy alignment
- **Fact-checker** (NEW): cards/PDFs verbatim 대조, venue/year/metric/lineage/classification 검증

| Level | Condition | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|---|
| **Quick** | (manual via `--qa quick` only — autopilot skips refine entirely in quick mode) | 1× 품질관리팀 (`model: "sonnet"`), spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **Light** | ≤3 sections | 1× 품질관리팀 (`model: "sonnet"`) | _skip_ (quality reviewer covers basic spot-checks) | 2 |
| **Standard** | 4+ sections | 1× 품질관리팀 (default opus) | **1× 품질관리팀 fact-check (`model: "sonnet"`)** | 2 |
| **Thorough** | Major overhaul or new evidence | 2× 품질관리팀 in parallel (opus) | **1× 품질관리팀 fact-check (`model: "sonnet"`)** | 2 |

**Why Sonnet for fact-checker**: card verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 Sonnet으로 충분하고, 비용 효율적이다.

## Post-Refine Review Loop (max 2 rounds; quick = 1 round)
After 연구팀 returns:
1. **Resolve log dir**: artifact root (e.g., `.claude_reports/documents/2026-03-25_foo/`).
   - For strategy refinement: `mkdir -p {log_dir}/strategy_reviews`
   - For draft refinement: `mkdir -p {log_dir}/draft_reviews`
2. **Invoke quality + fact-check reviewers in parallel** (single message with multiple Agent calls per QA Scaling above):

   **Quality reviewer prompt** (opus or sonnet per level):
   ```
   Review changed sections — _quality / cohesion / audience fit_ focus.
   {Doc type}: [path]. Changed: [list]. For rebuttals, verify all reviewer points still addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write to: {log_dir}/{review_subdir}/refine_round_{N}_quality.md.
   Return ONLY path + one-line verdict.
   ```

   **Fact-checker prompt** (sonnet, parallel — Standard/Thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   {Doc type}: [path]. Changed sections: [list].

   For every domain claim in the changed sections (model name / venue / year /
   metric / lineage / classification), open the corresponding ground-truth source
   and verbatim compare against the deliverable:
   - Paper cards: {refs}/cards/*.md
   - Reference PDFs: {refs}/*.pdf (only if cards lack the specific fact)
   - Strategy/analysis: {artifact_root}/strategy|analysis/

   Output a single table (no narrative):
   | Slide/Section | Claim in deliverable | Source (file:line or section) | Match (✅/❌) | Severity (🔴/🟡) |

   Do NOT comment on writing quality, narrative arc, or audience appropriateness
   — that's the quality reviewer's job. Stay narrowly on fact verification.

   Cost-aware mode (sonnet): table-only output, no extended discussion. Limit to
   ~30 most material claims if changed sections exceed 10.

   Write to: {log_dir}/{review_subdir}/refine_round_{N}_factcheck.md.
   Return ONLY path + one-line verdict (e.g., "factcheck.md — 🟢 28/28 claims verified" or
   "factcheck.md — 🔴 3/28 claims fail (Slide N PASE venue, ...)").
   ```

3. **Check verdict (both reviewers):**
   - **No 🔴 from either**: Report to user (both verdicts inline).
   - **qa_level == quick**: After round 1, exit regardless of 🔴. Add 🔴 issues to `## 미해결 이슈`. Report to user.
   - **🔴 from quality reviewer**: Re-invoke 연구팀 with quality findings. Max 2 rounds.
   - **🔴 from fact-checker**: Re-invoke 연구팀 with **mandatory ref-grounding** instruction (re-read the named cards/PDFs). Max 2 rounds.
   - **🔴 from both**: Re-invoke 연구팀 with combined findings. Max 2 rounds.
4. **If 🔴 remain after 2 rounds**: Add to `## 미해결 이슈`, report which sections changed, which issues resolved/unresolved and why. Tag fact-check residuals with `[FACT-RESIDUAL]` for downstream visibility.

## Task
Refine the document at: $ARGUMENTS
