# autopilot-refine

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Autopilot family — **post-creation iteration pipeline for research and document artifacts**, not code. This is branch E for later correction.

- **Prompt-driven:** fuzzy-match target artifacts from prompt keywords against `<artifact-root>/{research,documents}/*`.
- Discover the artifact structure, plan edits, preview the diff, apply after the applicable confirmation policy, snapshot the version, and append integrated history to `pipeline_summary.md`. Do not create a separate CHANGELOG.
- Default to `--intensity quick` for one-pass review. Higher intensities add multiple review rounds, fact checking, and an external adversary. Rigor is derived from intensity under `CONVENTIONS §1.1`; there is no separate `--qa` axis.
- Use optional `--memo <file>` for deferred file-memo reviews.

> Code artifacts are outside this skill. Use `/code-refine` or `/autopilot-code`.

## Invocation

```text
/autopilot-refine "<prompt>" [--intensity quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]
```

## Default invocation rule

Without an explicit slash command, automatically invoke this skill only for a **major-level change** to an artifact under `<artifact-root>/{documents,research}/*`. A change is major when any of these applies:

1. **Explicit user signal:** `major`, `v{N+1}`, `/autopilot-refine`, `전면 재작성`, or `phase 재시작`
2. **Large structural change:** at least 200 affected lines, a whole-section rewrite, or a batch mutation-tier reclassification
3. **Pre-review ceremony:** `camera-ready 마무리`, `submission 직전 finalize`, or `PR open 직전`

Treat every other change as **minor by default**: edit directly and append a detailed minor-log entry to `pipeline_summary.md`. Do not create a snapshot; use the last major snapshot as the audit baseline. At five accumulated minor changes, recommend `/audit` so it can compare both against the last major version and against general principles.

For each minor change:

- Add `| v{N}_M | YYYY-MM-DD | (minor) one-line summary |` to the `## 버전 히스토리` table.
- Add a detailed entry under `## 마이너 변경 로그 (v{N} → next major 누적)` with Trigger, Scope, Rationale, Files touched, Cross-ref, Audit-flag, and Reversibility.

Overrides, highest priority first:

- An explicit `standard`, `thorough`, or `adversarial` level forces the refine pipeline.
- `refine 없이 직접 edit`, `Edit으로 처리`, or `versioning 없이` forces the minor path.
- `--review-only` performs review without application.
- An explicit `/autopilot-refine` invocation forces the refine flow.

## Modes

| Flag | Behavior |
|---|---|
| `"<prompt>"` | Fuzzy-match the artifact from natural language, preview the diff, then apply automatically unless another mode pauses |
| `--memo <file>` | Apply a separate memo file for deferred review |
| `--confirm` | Pause in chat before modification |
| `--review-only` | Inspect only; never apply |

## QA scaling

| Level | Behavior |
|---|---|
| quick (default) | One quality-review pass and automatic application; skip fact-checker and style-audit reviewers |
| light | One fast quality reviewer |
| standard | One deep quality reviewer and one fast fact checker in parallel |
| thorough | Two parallel quality reviewers plus a fact checker |
| adversarial | Thorough plus an external adversary for camera-ready, grant, and similarly high-stakes work |

## Versioning and history

- **Major application:** create `_internal/versions/v{N+1}/`, append integrated history to `pipeline_summary.md`, migrate the active `## 마이너 변경 로그` section verbatim into `### 누적 마이너 변경 사항 (v{N}_1 → v{N}_M)` under the new `## v{N+1} 변경 사항`, and clear the active log. Insert a v{N+1} entry at the top of each affected file's frontmatter `changelog:` array.
- **Minor application:** do not snapshot. Edit directly, append a detailed entry to `## 마이너 변경 로그`, and insert one v{N}_M entry at the top of each affected file's frontmatter `changelog:` array. The last major snapshot remains the audit baseline.

---

*Portable capability contract: `<agent-home>/capabilities/autopilot-refine.md`; shared skill guidance: `<agent-home>/skills/autopilot-refine/SKILL.md`.*
