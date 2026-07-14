## Lifecycle

post-it entries do not accumulate permanently. Every record ends in one of these states:

| State | Meaning | Handling |
|---|---|---|
| **graduated** | Permanently represented in an artifact or structured section: decision → plan, convention → bootstrap/code, user memo → profile section | Expire the working record with `sweep` or `promote`; the artifact is truth and the copy is redundant |
| **stale** | Old `[in-progress]` item or completed hint that no longer applies | Expire with `sweep` or `resolve` |
| **live** | Still valid and present only in a working record | Keep |

- The owning skill performs graduation by writing the durable artifact: autopilot-code updates a plan, autopilot-spec updates a spec, and analyze-user updates a profile. post-it `sweep`/`promote` only expires working records after graduation.
- Handoff continuity and lean storage are paired. Remove graduated and stale items before handoff so the next session receives only current context; this is why `handoff` proposes a sweep first.

## Scope — Project vs User

This skill stores data in two locations selected by `--scope`:

| Scope | Storage | Content | Session loading | Graduation path |
|---|---|---|---|---|
| `project` (default) | cwd-scoped DB working tier via `mem note`/`mem add` | Current-project work, decisions, external resources, and next-session hints | `mem inject` reads DB working records | `sweep` compares them with `plans/`, `documents/`, `spec/`, and git, then expires them |
| `user <aspect>` | Global durable DB profile record through `mem add`, source `user-profile:<stem>`, inside the exact block `## 사용자 수동 메모` | Cross-project patterns, preferences, and domain notes; persistent manual channel between analyze-user runs | `mem inject` reads `type=profile` records | `promote` graduates the item into a structured profile section, then removes it from the manual block |

**Choose scope**:

- Meaningful only in this project → `--scope project`
- Useful across projects → `--scope user <aspect>`
- Ambiguous → `project` by default

**Choose a user-scope aspect**:

| Aspect | Profile record | Example content |
|---|---|---|
| `figure` | `mem profile 01_paper_figure_style` | Visual and figure preferences, such as a fixed Times font |
| `writing` | `mem profile 02_paper_writing_style` | Paper tone and phrasing |
| `presentation` | `mem profile 03_presentation_strategy` | Slide layout and narrative decisions |
| `analysis` | `mem profile 04_analysis_methodology` | Data and experiment-analysis methods |
| `domain` | `mem profile 05_domain_expertise` | Domain terminology and preferred expressions |
| `collab` (default) | `mem profile 06_collaboration_style` | Workflow, feedback, and decision patterns; most common destination |

**Why user-scope notes live inside a profile record's `## 사용자 수동 메모` block rather than a separate file**:

- A user-level note usually maps naturally to one of the six aspects.
- A separate record would split structured analyze-user content from free-form user content and force extra `mem profile` calls by subagents.
- Two regions in one profile record—analyze-user structure plus manual user notes—separate ownership while loading everything with one `mem profile` call.

**Responsibility boundary and graduation with `/analyze-user`**:

- `## 사용자 수동 메모` is user-owned. analyze-user reads it but never edits it silently. After confirmation, `promote` may integrate a memo into a structured section and remove it from the manual block.
- Use `promote`, or an analyze-user startup proposal followed by confirmation, to graduate stable notes. Treat the manual block as a staging sticky note, not an infinite log.
- All other sections are analyze-user-owned. Direct user edits may be overwritten by the next update unless preserved in the record body's `changelog:`.
- **Two-writer contract:** `/post-it promote --scope user` and `analyze-user update` both write the profile record with source `user-profile:<stem>`. This is one logical record with two writers; see the `promote` specification in Step 4.1.

> **Artifact-guard note:** project working records and user-scope profile records are both convention-only, unguarded surfaces in the adapter bootstrap. Writing `--scope user` requires no ceremony. When `promote` changes an analyze-user-owned structured section, preserve the preview → confirm contract.

## DB Working Tier and Automatic Loading

- **Project scope:** write a working record with `python3 <agent-home>/tools/memory/mem.py note "<text>" --type <type>`. When the full form is needed, use `mem add working <type> "<body>" --scope project`, where `<type>` is `thread`, `decision`, `convention`, `reference`, or `hint`. Session injection uses `python3 <agent-home>/tools/memory/mem.py inject --hook`; no file read is required.
- **User scope:** merge-write a profile record with `python3 <agent-home>/tools/memory/mem.py add durable profile <body> --scope global --source user-profile:<stem>`. A subagent loads it with `python3 <agent-home>/tools/memory/mem.py profile <stem>`.
- **Updates:** use `/post-it` or the proactive automatic-recording path. Storage follows the adapter pause/autonomy rule and MEMORY §7 automatic-write invariant; only irreversible pruning/deletion needs confirmation.

## Five Record Types

There is no file format. The five categories are DB working-record `type` values:

| Category | `type` value | Example content | Aging |
|---|---|---|---|
| Conventions | `convention` | Durable conventions such as Notion location or commit-message language | Never age by time; remove only through graduation |
| External Resources | `reference` | External links and paths such as datasets or Overleaf | Never age by time; remove only through graduation |
| Open Threads | `thread` | `[in-progress YYYY-MM-DD]` current work | Time-tiered by date |
| Decisions | `decision` | `YYYY-MM-DD:` decision and rationale | Time-tiered by date |
| Next Session Hints | `hint` | Progress, next action, and cautions for the next session | Refreshed on each handoff |

> **Aging stamp and time tiers for thread/decision/hint:** use the `created` and `expires` columns. `sweep` classifies active (<30d), stale candidate (≥30d), and archive (≥90d). Conventions and references do not age by time; remove them only after graduation.
