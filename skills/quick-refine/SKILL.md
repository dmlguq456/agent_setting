---
name: quick-refine
description: Prompt-driven artifact refinement for research and doc artifacts (NOT code). Auto-discovers the artifact's file structure, plans edits from a one-line prompt, shows a diff preview in chat, and on user confirm applies edits with versioning + CHANGELOG logging. Optional `--memo <file>` falls back to file-memo style for deferred reviews. Lightweight by default; memo path is opt-in.
argument-hint: "<artifact_dir_or_topic> \"<prompt>\" [--auto | --review-only | --memo <file>]"
---

## Scope

- **Targets**: `.claude_reports/research/*` and `.claude_reports/documents/*`
- **NOT for**: `.claude_reports/plans/*` (code) — use `/refine-plan`, `/execute-plan`, or `/autopilot-code` instead. Code changes need test-based verification, not diff review.
- Why this skill exists: the existing `refine-doc` / `refine-plan` workflow is file-memo only, which is too heavy for routine prompt-driven edits. `quick-refine` is the lightweight default; memo style is reduced to an opt-in fallback.

## Argument Forms

| Form | Behavior |
|---|---|
| `quick-refine <a> "<p>"` | **Default**: investigate → diff preview → user confirm → apply + version + log |
| `quick-refine <a> "<p>" --auto` | Auto-apply MECH changes; pause only on SEM. Skips confirmation when all proposals are mechanical. |
| `quick-refine <a> "<p>" --review-only` | Investigate + diff preview. No edits, no version, no log. |
| `quick-refine <a> --memo <file>` | Read memo file as proposal source (compat with refine-doc memo style). Apply same as default. |

## Artifact Resolution

1. If `<arg>` is a path that exists → use as-is. Detect type by path:
   - `.claude_reports/research/*` → **research**
   - `.claude_reports/documents/*` → **doc**
2. Else fuzzy search both:
   ```bash
   ls -d .claude_reports/research/*<arg>* .claude_reports/documents/*<arg>* 2>/dev/null
   ```
   - 1 match → use it. Multiple → list, ask user. 0 → error.

## Language Rule

Reason internally in English. All user-facing output (chat diffs, CHANGELOG entries, reports) in **Korean**.

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
   Do NOT proceed with quick-refine.

### Stage C — Diff preview (chat)

Output to chat in this format:

```
**Quick refine — {artifact 한줄 식별}**

Prompt: "{prompt verbatim, ≤200자 trim}"

제안 변경 ({MECH 개수} mech / {SEM 개수} sem):

📄 `{relative path}` ({n} changes)
   Line {a}-{b}  [MECH|SEM]
     - {old_text 발췌, ≤80자}
     + {new_text 발췌, ≤80자}
     사유: {1줄}

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
  - "edit 4: <new>" → 4번 텍스트 교체 후 적용
  - "no" / "stop" → 중단
```

End turn. Wait for user reply.

**`--auto` mode exception**: if all proposals are MECH, skip Stage C output and proceed directly to Stage D. Print a one-line summary instead: `[auto] {N} mech changes 적용 중...`. SEM 항목이 하나라도 있으면 chat 출력 + pause로 fallback.

**`--review-only` mode exception**: print Stage C output, then end. No Stage D.

### Stage D — Apply (after user confirms)

Parse the user's reply, then:

1. **Determine version**:
   - Read `{artifact_dir}/CHANGELOG.md` if exists; find the highest `## v{N}` heading.
   - If no CHANGELOG → current state is implicit v1; next version = v2.
   - Else → next version = max + 1.

2. **Snapshot pre-edit state** (only files about to change):
   - **Research** type: copy current file to `{artifact_dir}/versions/v{prev}/{relative-path}`
     - e.g., `.claude_reports/research/topic/versions/v1/01_landscape.md`
     - `mkdir -p` parent dirs as needed.
   - **Doc** type: copy current file to `{file_dir}/{stem}_v{prev}.{ext}` (refine-doc convention, backward compatible)
     - e.g., `.../strategy/strategy_v1.md`
   - If a snapshot for the same prev version already exists, do NOT overwrite (don't double-snap).

3. **Apply edits** via the Edit tool. Exact-string match. Never use `replace_all` unless explicitly stated in a proposal.

4. **Append to CHANGELOG**:
   - Path: `{artifact_dir}/CHANGELOG.md`
   - Create with header `# Quick-Refine CHANGELOG\n` if absent.
   - Insert NEW entry at top (newest first), below the header:
     ```
     ## v{N} — {YYYY-MM-DD HH:MM} — {prompt 요약 ≤80자}
     - Mode: {Quick chat-loop | Quick auto | Memo}
     - Prompt: "{prompt verbatim, ≤200자 trim}"
     - Reason: {1-2줄}
     - Files touched:
       - `{path}:{line}` — {짧은 설명}
       - `{path}:{line}` — {짧은 설명}
     - Skipped (if any):
       - `{path}` — {SKIP 사유}
     - Snapshot: `versions/v{prev}/` (research) | `{stem}_v{prev}.md` (doc)
     - Downstream sync needed: {Yes / No}
       - If Yes: `{dependent_artifact_path}` — {왜 영향받는지}
     ```

5. **Report** to user (≤6 lines):
   ```
   ✓ Quick refine 완료 — v{prev} → v{N}
   • Files touched: {count}
   • Snapshot: {versions/v{prev}/ or _v{prev}.md}
   • CHANGELOG: {artifact_dir}/CHANGELOG.md
   {if downstream sync needed:}
   ⚠ Downstream sync 필요:
     /quick-refine {dependent_path} "CHANGELOG v{N} 반영"
   ```

### Stage E — Memo mode (`--memo <file>`)

1. Read the memo file. Detect format:
   - **Structured** (per-file proposals like refine-doc memo style) → parse directly into Stage B's change list.
   - **Free-form** (just prose) → treat the body as the prompt, run Stage A-B-C internally.
2. Proceed to Stage D (with `Mode: Memo` in CHANGELOG).

---

## Constraints

- **No silent additions** — Stage D applies only what was shown in Stage C diff (or auto-mode summary). If a new issue is discovered during apply, abort that single edit and note it in CHANGELOG's `Skipped` section, but do NOT propose new edits beyond the original list.
- **Versioning is mandatory** when applying — every apply increments version + creates snapshot. Only `--review-only` skips this (because it doesn't apply).
- **Cards = primary source for research** — for taxonomy/definition/coverage prompts, always re-read `cards/*.md` and cite in reasoning.
- **Don't auto-rename historical citations** — paper titles, baseline names as published, specific challenge names. List these in Stage C as "intentionally untouched" if relevant.
- **Cross-artifact ripple is announced, not auto-propagated** — if a research change affects a downstream doc artifact, surface this in CHANGELOG's `Downstream sync needed` field. The user invokes `/quick-refine` again on the doc; this skill never auto-cascades.
- **STRUCT escape hatch** — if changes look structural, halt with a recommendation; don't try to handle structural rewrites in this skill.

---

## Examples

```
# Default — chat-loop with diff preview
/quick-refine speech-enhancement-trends "General Restoration과 Universal SE는 혼용 개념이라 task family를 통합"
# (skill discovers files, shows diff, ends turn)
# user replies: "all"
# → applies, snapshots to versions/v1/, writes CHANGELOG v2 entry

# Auto mode — mechanical changes apply without confirm
/quick-refine speech-enhancement-trends "Year×Paradigm heatmap의 2026년 칸 채우기" --auto

# Review only — no edits
/quick-refine speech-enhancement-trends "최신 카드 5편이 분류표에 누락됐는지 검토" --review-only

# Memo mode — fall back to file-memo for deferred review
/quick-refine 2026-05-06_se-seminar-tfrestormer --memo .../review_memo.md

# Doc artifact (auto-detected from path)
/quick-refine 2026-05-06_se-seminar-tfrestormer "Slide 4 task family 표를 4행으로 변경"
```

## When NOT to use

- Single-file typo / cosmetic edit → just `Edit`.
- Code artifacts → `/refine-plan`, `/execute-plan`, `/autopilot-code`.
- Whole-axis structural redesign → `/autopilot-research --from analyze` or `/autopilot-doc --from strategy`.
- Pure deferred review (annotate over hours/days) → `/refine-doc` (file-memo) or this skill's `--memo` form.

## Post-Apply Checklist

After successful apply, suggest to user:
1. If `Downstream sync needed: Yes` → run `/quick-refine <downstream> "CHANGELOG v{N} 반영"` for each dependent artifact.
2. Optionally `git add -A && git commit -m "quick-refine: {prompt summary}"` if artifact is under git.
3. Run `/sync-skills` if this SKILL.md was just updated (rare — only when user iterates on the skill itself).
