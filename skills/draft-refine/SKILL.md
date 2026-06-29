---
name: draft-refine
description: Reflect user memos/review feedback in a document strategy or draft. Snapshots prior version under `_internal/versions/v{N}/` (modern; per CONVENTIONS.md §5) or `_v{N}.md` siblings (legacy). Auto-managed `changelog:` array inside YAML frontmatter (NOT a top-of-file HTML comment — that breaks markdown preview when frontmatter is also present). Mandatory ref-grounding per memo (re-read source; override memo if it conflicts with source).
argument-hint: "<strategy or draft name or path> [--qa quick|light|standard|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "초안 정련·다듬기 sub-skill — 편집팀 검수 경유"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 본 skill은 review 로그를 `_internal/strategy_reviews/` 또는 `_internal/draft_reviews/`에 기록. 버전 스냅샷은 modern artifact면 `_internal/versions/v{N}/`, legacy artifact면 `_v{N}.md` 형제 (자동 감지).

## Document Resolution
Resolve `$ARGUMENTS` to document file paths. Detect whether this is a **strategy** or **draft** refinement:

**Auto-detect document type**:
- If path contains `/draft/` → draft mode (resolve `draft.md` + `draft_ko.md`)
- If path contains `/strategy/` → strategy mode (resolve `strategy.md` + `strategy_ko.md`)
- If path is a directory → default to strategy mode

**Resolution rules** — always resolve BOTH English and Korean files:
1. If it ends with `.md` → use as-is; derive the other file by path swap (`draft.md` ↔ `draft_ko.md`, or `strategy.md` ↔ `strategy_ko.md`)
2. If it's a directory path → append `/strategy/strategy.md` (English) and `/strategy/strategy_ko.md` (Korean)
3. Otherwise, fuzzy search: `ls -d <artifact-root>/documents/*$ARGUMENTS* 2>/dev/null`
   - **1 match** → use `{match}/strategy/strategy.md` and `{match}/strategy/strategy_ko.md`
   - **Multiple matches** → ask user
   - **No match** → report error

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Pre-Refine: Versioning Setup

Before invoking 연구팀, the orchestrator establishes versioning. Snapshots go to `{artifact_root}/_internal/versions/v{N}/<relative-path>` (per [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3)). The legacy `_v{N}.md` sibling pattern is **deprecated** for new artifacts.

1. **Determine next version number**:
   - **Modern** (`{artifact_root}/_internal/` exists): scan `_internal/versions/` for `v{N}` subdirs. Find max N. If none → `next_version = 2`.
   - **Legacy** (artifact has `*_v{N}.md` siblings AND no `_internal/`): scan for `{ko_path.stem}_v{N}.md` siblings. Find max N. If none → `next_version = 2`.
   - **New**: if neither exists, treat as modern, `next_version = 2`. mkdir -p `_internal/versions/`.

2. **Snapshot current state as previous version** (skip if a snapshot for `prev_version` already exists):
   - **Modern**:
     ```bash
     mkdir -p {artifact_root}/_internal/versions/v{prev_version}/{ko_relative_subdir}
     cp {ko_path} {artifact_root}/_internal/versions/v{prev_version}/{ko_relative_subdir}/{ko_filename}
     cp {en_path} {artifact_root}/_internal/versions/v{prev_version}/{en_relative_subdir}/{en_filename}
     ```
     where `{ko_relative_subdir}` is e.g. `strategy/` or `draft/`.
   - **Legacy**:
     ```bash
     cp {ko_path} {ko_path.parent}/{ko_path.stem}_v{prev_version}.md
     cp {en_path} {en_path.parent}/{en_path.stem}_v{prev_version}.md
     ```
3. **Pass `next_version`, `prev_version`, convention mode, and snapshot paths to 연구팀** in the prompt below.

## Delegate to 연구팀
Invoke the **research-team** (연구팀) agent as a subagent with the following prompt:

```
Refine mode (versioned + ref-grounded). Update an existing document {doc_type} based on user memos and review feedback.

Korean {doc_type} file (current/latest): {ko_path}
English {doc_type} file (current/latest): {en_path}
Previous version archive (immutable, already created by Pre-Refine setup):
- Modern: `{artifact_root}/_internal/versions/v{prev_version}/{relative-subdir}/{filename}` (where `{relative-subdir}` is `strategy/` or `draft/`)
- Legacy: `{ko_path.parent}/{ko_path.stem}_v{prev_version}.md` (and English equivalent — only if artifact already used `_v{N}.md` siblings AND lacks `_internal/`)
Convention mode: {modern | legacy}
Next version: v{next_version}

## Memo Detection
Read the Korean {doc_type} and find all user memos. Memos can appear in any of these formats:
- `<!-- memo: ... -->` (standard memo tag)
- `<!-- ... -->` (HTML comment — treat any HTML comment as a user memo, EXCEPT a **legacy** `<!-- CHANGELOG (auto-managed by draft-refine ... -->` block at top-of-file. Such legacy blocks are NOT memos; they must be **migrated** into the frontmatter `changelog:` array and then deleted from the body (see "Changelog (frontmatter `changelog:` array)" below).
- `// ...` (inline comment)
- `[memo] ...` (bracketed annotation)
- `(**...**)` (parenthetical note)
- Any other text marked as a user annotation. Do NOT treat the document's original author-written prose as a memo.

## MANDATORY Ref-Grounding Per Memo (CRITICAL — quality requirement)

For EACH memo found, before applying any change:
1. **Identify the relevant source(s)** the memo pertains to:
   - Paper analyses (`<artifact-root>/analysis_project/paper/*.md`) — for citation, venue, score, NFE, RTF, dataset facts (single source of truth, produced by `/analyze-project --mode paper`)
   - Strategy document (`{artifact_root}/strategy/strategy.md`) — for narrative arc, slide outline alignment
   - Analysis files (`{artifact_root}/analysis/*.md`) — for audience, key messages, visual strategy
   - Original PDFs (in user's source folder if available) — only for nuanced claims requiring re-reading; paper analyses are preferred
2. **Re-read the identified source** before applying the change. Do not rely on the memo's claim alone.
3. **Compare memo claim vs source**:
   - If memo agrees with source → apply the change as memo suggests.
   - If memo CONFLICTS with source → **override the memo, keep the original draft text, and document the conflict in changelog**. Do NOT silently propagate user error.
   - If source is ambiguous → apply the change but flag in changelog with `[CAUTION: source ambiguous]`.
4. **Record source verified** in the changelog entry: `[verified cards/2020_Hu_DCCRN.md]` or `[strategy section 4 confirmed]`.

For draft refinement: also cross-check against the strategy document at `{artifact_root}/strategy/` to verify the draft faithfully reflects all strategy points.

## Output Versioning

1. **Write the new content to current files** (`{ko_path}`, `{en_path}`) — these always represent the latest version.
2. The pre-edit snapshot is already written by the Pre-Refine setup step (see "Pre-Refine: Versioning Setup" above) — to either `_internal/versions/v{prev_version}/...` (modern) or `{file}_v{prev_version}.md` (legacy). No additional snapshot needed at output time.
3. **Remove all memo comments** (HTML comments, `// ...`, `[memo] ...`, etc.) from the new version. EXCEPT preserve/update the frontmatter `changelog:` array (see below).

## Changelog (frontmatter `changelog:` array — NEVER an HTML comment)

The changelog is stored as a **YAML array** inside the file's frontmatter, NOT as a top-of-file `<!-- CHANGELOG -->` HTML comment.

**Why this form is mandatory** (do not regress to the HTML-comment form):
- A `<!-- ... -->` block placed above the frontmatter pushes `---` off line 1. Markdown previewers (VS Code, GitHub, Obsidian, Jupyter) require frontmatter to start at line 1; otherwise they render `---` as horizontal rules and YAML keys as plain prose, breaking preview.
- YAML arrays are structured data, parseable by tools (audit, downstream scripts).
- The frontmatter is hidden by previewers; the body renders cleanly.

### File-level invariant

The file MUST begin with `---` on line 1. Nothing — no HTML comment, no blank line, no prose — may precede the frontmatter open delimiter.

### Format

```yaml
---
{existing domain keys preserved verbatim: type, venue, status, date, tone, ...}
changelog:
  - version: v{next_version}
    date: "{YYYY-MM-DDTHH:MM}"
    applied: {N}
    overridden: {M}
    entries:
      - |
        [Slide N | Section X] [verified <source>]: <one-line description of change>
      - |
        [Slide N | Section X] [verified <source>]: <change>
      - |
        [Slide N | Section X] [OVERRIDDEN — memo conflicted with <source>]: <reason>
  - version: v{next_version - 1}
    date: "{YYYY-MM-DD or YYYY-MM-DDTHH:MM}"
    {applied/overridden/note as recorded previously}
    entries:
      - |
        {previous entry preserved verbatim}
---
```

### Rules

1. **Placement**: `changelog:` is the **last** key in the frontmatter (after `type`, `venue`, `status`, `date`, `tone`, etc.), so domain keys stay readable at the top.
2. **Order**: Newest version first. Prepend the new `version: v{next_version}` block above the existing entries.
3. **Block scalars (`|`) for entries**: Each entry uses a YAML literal block scalar so backticks, backslashes, colons, brackets, and emoji inside the change description need NO escaping. Indent each entry's content one level under the `|`.
4. **First refine (no prior changelog)**: create the `changelog:` key with both:
   - v1 entry — `version: v1`, `date: "{creation date from existing frontmatter, or the literal string \"initial\" if unknown}"`, `note: "initial draft from autopilot-draft {mode} pipeline"`, no `entries:` required.
   - v2 entry — this round's changes (above v1).
5. **No frontmatter at all (rare)**: create a minimal frontmatter block at the very top of the file with at least `changelog:` (and any other keys you can derive from the document).
6. **Legacy migration (required on first encounter)**: if the file has a `<!-- CHANGELOG (auto-managed by draft-refine ... -->` HTML block (above or below the frontmatter), convert each `vN (date, applied X / overrode Y): ...` line into a frontmatter array entry **in the same refine pass** and **delete the HTML block** (including its surrounding blank lines). After migration the file must begin with `---` on line 1. This migration applies to BOTH `{ko_path}` and `{en_path}`.

### Worked example

Before (legacy, broken preview):

```markdown
<!-- CHANGELOG (auto-managed by draft-refine — do NOT edit manually)
v2 (2026-05-14T14:00, applied 22 memos / overrode 0 memos):
  - [M25 QUALITY 🔴] [verified .bib L366]: `\citep{defossez2023}` → `\citep{defossez2023high}`
v1 (2026-05-14, initial draft from autopilot-draft paper pipeline): camera-ready cheatsheet ...
-->

---
type: paper
status: draft
date: 2026-05-14
---

# Camera-Ready Cheatsheet ...
```

After (frontmatter array, preview-safe):

```markdown
---
type: paper
status: draft
date: 2026-05-14
changelog:
  - version: v2
    date: "2026-05-14T14:00"
    applied: 22
    overridden: 0
    entries:
      - |
        [M25 QUALITY 🔴] [verified .bib L366]: `\citep{defossez2023}` → `\citep{defossez2023high}`
  - version: v1
    date: "2026-05-14"
    note: "initial draft from autopilot-draft paper pipeline"
    entries:
      - |
        camera-ready cheatsheet ...
---

# Camera-Ready Cheatsheet ...
```

## Other rules
- Do NOT touch the version archive of previous versions (`*_v{prev_version}.md` and earlier) — they are immutable historical record.
- Apply ref-grounding to every memo, even trivial-looking ones (they can carry hidden errors).
- **Paragraph Cohesion Pre-Check (mandatory for every memo that rewrites paste-ready content — all modes)** (cross-ref `draft-strategy/SKILL.md` § _Paragraph Cohesion Pre-Check_ for the full 4-step spec; single source of truth there):
  Before applying any memo that adds or rewrites a paste-ready block (LaTeX / markdown / slide / table), run the 4-step pre-check on the **target paragraph as a whole**: (1) is the substance already stated? (2) does the new sentence break the paragraph axis (motivation → design → formalization, claim → evidence → caveat, etc.)? (3) is this substance already canonical at another §-level / slide-level site? (4) classify the edit as EDIT (in-line) / REPLACE / INSERT / DROP — prefer EDIT/REPLACE over INSERT for cohesion. **When refining an existing mutation that fails this check** (e.g., a trailing INSERT whose content overlaps a prior sentence, or a cross-ref that restates substance already covered elsewhere), the correct refine action is to **rewrite the mutation as EDIT / REPLACE / DROP**, not polish the existing INSERT further.
- **Paper mode — Natural-integration rule** (cross-ref `draft-strategy/SKILL.md` paper mode for full spec; single source of truth there):
  When a memo asks to **add a new mutation from a reviewer concern or rebuttal material**, apply the same gating question as draft-strategy: *"Can this be naturally integrated as a 1-2 sentence inline rewrite that flows with the surrounding paragraphs?"* YES → inline rewrite mutation (M15-style: subsection-head opening + body-paragraph touch-up + Figure cascade; numbers/hyperparameters stay in body or Appendix). NO → reject and inform the user — rebuttal-format artifacts (model-comparison tables, structured Q&A blocks, point-by-point enumerations) must not become paper-body mutations even if the reviewer "strongly recommended integration."
  - When **refining an existing mutation**, re-evaluate it against the same rule. If a previously-drafted mutation fails the natural-integration test (e.g., a standalone `\begin{table}` lifted from rebuttal materials with no embedding paragraph rewrite), the correct refine action is **drop the mutation entry**, not polish it further.
- Return which sections were changed, which memos applied vs overridden, and the new version number.
```

Where `{doc_type}` is either "strategy" or "draft" based on auto-detection.

## QA Scaling
Auto-detect from sections changed. Two reviewer roles run **in parallel** at Standard+:
- **Quality reviewer** (품질관리팀): narrative arc / cohesion / audience fit / strategy alignment
- **Fact-checker** (연구팀 subrole): cards/PDFs verbatim 대조, venue/year/metric/lineage/classification 검증. classification 8-row table 의 canonical 정의는 [`research-team.md`](../../agents/research-team.md) L258-300 single source.

| Level | Condition | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|---|
| **Quick** | (manual via `--qa quick` only — autopilot skips refine entirely in quick mode) | 1× fast reviewer, spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **Light** | ≤3 sections | 1× fast reviewer | _skip_ (quality reviewer covers basic spot-checks) | 2 |
| **Standard** | 4+ sections | 1× deep reviewer | **1× fast fact-checker** | 2 |
| **Thorough** | Major overhaul or new evidence | 2× deep reviewers in parallel | **1× fast fact-checker** | 2 |
| **Adversarial** | external-review-imminent (camera-ready / submission), or manual via `--qa adversarial` | 2× deep reviewers in parallel + 1× external adversary (`codex-review-team` in Claude adapter) | **1× fast fact-checker** | 2 + external 1 |

**Why fast fact-checker**: card verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 fast role 로 충분하고, 비용 효율적이다.

## Post-Refine Review Loop (max 2 rounds; quick = 1 round)
After 연구팀 returns:
1. **Resolve log dir**: artifact root (e.g., `<artifact-root>/documents/2026-03-25_foo/`).
   - For strategy refinement: `mkdir -p {log_dir}/_internal/strategy_reviews`
   - For draft refinement: `mkdir -p {log_dir}/_internal/draft_reviews`
2. **Invoke quality + fact-check reviewers in parallel** (single message with multiple Agent calls per QA Scaling above):

   **Quality reviewer prompt** (deep or fast reviewer per level):
   ```
   Review changed sections — _quality / cohesion / audience fit_ focus.
   {Doc type}: [path]. Changed: [list]. For rebuttals, verify all reviewer points still addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write to: {log_dir}/{review_subdir}/refine_round_{N}_quality.md.
   Return ONLY path + one-line verdict.
   ```

   **Fact-checker prompt** (fast fact-checker, parallel — Standard/Thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   {Doc type}: [path]. Changed sections: [list].

   For every domain claim in the changed sections (model name / venue / year /
   metric / lineage / classification), open the corresponding ground-truth source
   and verbatim compare against the deliverable:
   - Paper analyses: `<artifact-root>/analysis_project/paper/*.md` (single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if paper analyses lack the specific fact
   - Strategy/analysis: {artifact_root}/strategy|analysis/

   Output a single table (no narrative):
   | Slide/Section | Claim in deliverable | Source (file:line or section) | Match (✅/❌) | Severity (🔴/🟡) |

   Do NOT comment on writing quality, narrative arc, or audience appropriateness
   — that's the quality reviewer's job. Stay narrowly on fact verification.

   Fast fact-checker mode: table-only output, no extended discussion. Limit to
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
