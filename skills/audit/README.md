# audit

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Perform a read-oriented, multi-aspect audit of `<artifact-root>/{plans,research,documents}/*`. One entry point detects artifact type from its path:

- **documents:** facts, style, structure, cross-reference, and coverage;
- **research:** card integrity, Tier consistency, coverage, and cross-card references;
- **plans:** test results, lint, code review, incomplete work, and semantic-deterministic consistency.

Document and research audits use two perspectives:

- **P1 — change from the last major baseline:** compare the `pipeline_summary.md` `## 마이너 변경 로그` section and the newest `_internal/versions/v{N}/` snapshot to detect accumulated drift.
- **P2 — universal principles:** inspect current artifact consistency aspect by aspect.
- Cross-correlate P2 `file:line` findings with P1 `Files touched` entries to distinguish recently introduced issues from older residue.

Default scope is `auto`. The audit itself never edits the artifact. By default it may dispatch the appropriate corrective workflow after reporting; `--report-only` disables that dispatch.

## Cadence

- Explicit `/audit <artifact>` → run immediately.
- At `AUDIT_HINT_THRESHOLD`, default five minor changes since the last major snapshot → recommend audit after autopilot-refine or a direct edit; do not run automatically.
- A corrective chain may also dispatch audit from autopilot-refine or autopilot-code.

## Invocation

```text
/audit <artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]
```

- `<artifact_path>`: an artifact under `<artifact-root>/{documents,research,plans}/{name}` or a unique fuzzy name.
- `--scope`: explicit aspect override. `auto` selects aspects from artifact mode, history, and status.
- `--read-only`: for code plans, do not execute tests; inspect existing evidence only.
- `--report-only`: write the report without corrective dispatch.
- `--no-fact-check`: disable fact and coverage checks.

## Corrective Dispatch

When findings exist and `--report-only` is absent:

- documents and research → `autopilot-refine`;
- plans → `autopilot-code --mode dev`.

## Output

Append reports under `_internal/audit/{YYYY-MM-DD}_{aspect}.md` in the audited artifact.

---
*Portable capability contract: `<agent-home>/capabilities/audit.md`; shared skill guidance: `<agent-home>/skills/audit/SKILL.md`.*
