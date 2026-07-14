## Pipeline: Mode debug

### Step 1: Diagnose the Root Cause

The main agent performs diagnosis directly; do not delegate it.

1. Parse error type, message, traceback, and affected location. Run `git log --oneline -10` and `git diff HEAD~3`; inspect relevant config and checkpoint files.
2. Follow the call stack and read the affected source and its callers.
3. Classify the cause as code logic, environment, data, or interaction between otherwise valid components.
4. Report a localized diagnosis with error, location, root cause, impact, and proposed fix.
5. If one cause is clear, continue automatically. If several remain plausible, list them and ask which to investigate. This is the only debug-mode pause.

### Step 2: Create a Minimal Fix Plan

Invoke `code-plan` with:

```text
Fix: {root cause summary}

Error: {error message}
Location: {file:line}
Root cause: {diagnosis from Step 1}
Proposed fix: {fix approach}

Scope: Minimal — fix the root cause only. Do not refactor or improve surrounding code.
```

Use `<artifact-root>/plans/{YYYY-MM-DD}_fix_{short-error-name}/`.

### Step 3: Check the Fix Plan

- Skip research-team review by default; debugging should stay minimal.
- Run a focused plan-check only when selected risk or assurance requires it.
- Apply one bounded correction for blocking issues; do not reopen a multi-round review loop.

### Step 4: Execute

Invoke `code-execute` with the fix-plan path. If status is `failed`, report and stop.

### Step 5: Verify and Reproduce

Invoke `code-test`, then reproduce the original scenario:

- rerun the user's failing command when provided;
- for training, run one or two short epochs;
- for inference, run an inference test.

If verification fails or the original error persists:

1. Read `Safety commit: {hash}` from `plan/checklist.md` and restore only changed paths with `git checkout <safety-commit> -- <changed paths>`.
2. Write `pipeline_summary.md` with `status: unresolved` before user output.
3. Report the diagnosis, attempted fix, why it failed, and manual investigation steps.

### Step 6: Report

Invoke `code-report`, then write the debug pipeline summary before any user-facing terminal report. This applies to fixed, partial, unresolved, and stopped states.

## Pipeline: Mode audit

Audit mode inspects an existing codebase or application broadly and applies verified low-risk corrections. It differs from dev, which creates requested features, debug, which diagnoses one error, and the separate artifact `/audit` Skill, which lints plans, documents, and research artifacts.

Preserved multilingual user-input examples include `"전수 점검해서 더 효율적·효과적인 동작/UI 까지 컨펌없이 고쳐"` and `"병렬 검토 많이 돌려"`.

The main agent orchestrates; reviewers and fixers fan out. Write findings, triage, fixes, and flags under `plans/<date>_audit/`.

### Step 1: Read-Only Review Fan-Out

Run multiple parallel reviewers by area and axis; requests for broad or numerous review may justify 10–16 or more workers.

- UI, responsiveness, accessibility, and visual quality → native `디자인팀`, render-aware.
- Code, behavior, performance, consistency, and data layer → native `품질관리팀` in code-review mode.
- Each reviewer reads code and renders when possible, then writes findings shaped as `{title, severity, category, files, proposed_fix, risk(low|med|high), confidence}`.
- Reviewers never edit. Report only source-backed findings and omit unsupported guesses.

### Step 2: Triage

Merge duplicates and drop low-value, overbroad, ambiguous, or `confidence < 0.6` findings.

- **autofix:** low risk with a clear correction, such as token consistency, wording, accessibility attributes, or simple duplication. Group by nonoverlapping files.
- **flagged:** medium or high risk involving behavior, architecture, schema, data, or judgment. Report without automatic correction.

### Step 3: Correct Low-Risk Clusters

Create every correction worktree from current main HEAD:

```bash
git worktree add <repo>-wt/audit-<key> -b <branch> main
```

Do not use a workflow helper that may branch from a stale base. The 2026-06-15 incident created a worktree 32 commits behind main and produced a merge reverting more than 5,000 lines. Review isolation is harmless; correction bases must be explicit and current.

Link required local dependencies such as `node_modules`, `.cache`, `<artifact-root>`, and `.env.local`, then dispatch one headless correction per cluster. Each fixer stays within its cluster, respects token contracts, and verifies with `tsc --noEmit`, a full `next build` when applicable, and native `디자인팀` verifier evidence for UI changes at light, dark, and mobile-390 views. Commit but do not merge.

### Step 4: Harvest and Report

The main orchestrator reviews real diffs, merges verified nonoverlapping branches sequentially, reruns the full build, and reports flagged items for user judgment or a later dev/debug cycle. Record finding, autofix, flagged, and dropped counts in `pipeline_summary.md`.

### Audit Discipline

- Do not request confirmation per low-risk correction, but never merge without verification.
- Review is read-only; correction bases are current HEAD; only the orchestrator merges.
- The user decides flagged medium- and high-risk changes.
