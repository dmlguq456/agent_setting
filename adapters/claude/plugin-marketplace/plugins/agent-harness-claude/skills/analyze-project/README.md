# analyze-project

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Analyze a codebase or source collection and write structured documentation under `<artifact-root>/analysis_project/{code,paper,doc}/`. This is an **upfront preparation Skill** for autopilot pipelines.

- `--mode code` — map codebase modules and interfaces.
- `--mode paper` — produce cards and an overview from academic PDFs.
- `--mode doc` — classify reviewer comments, format templates, past samples, and mixed document sources.

## Invocation

```text
/analyze-project [--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]
```

- If `--mode` is omitted, detect code or document mode; paper mode must be explicit.
- `--skip-qa` skips Phase 5 QA verification.
- Remaining text after flag removal is the target directory or scope.

## Language

- Follow an explicit artifact or audience language for `<artifact-root>/analysis_project/`; otherwise use the user's communication language.
- User-facing explanations follow the same contract and should read naturally rather than as literal translations.

## Code Mode

### Phase 1: Codebase Analysis

Resolve scope as follows:

- Directory argument → read recursively.
- Keyword argument → map it to modules through the project instruction file's structure section, then read those modules.
- Empty argument → use the project structure section when present; otherwise inspect repository entry points and obvious source directories such as `src/` and `lib/`.

Identify each file or module's role and interface, data flow, dependencies, design intent, and core algorithms.

### Phase 2: Documentation

Write role-separated Markdown files under `<artifact-root>/analysis_project/code/`. Avoid one monolithic document. Focus on code-level detail, use the selected artifact language, and end every document with:

```markdown
## Interface Reference

| Class/Function | File | Signature | Called by |
|---|---|---|---|
| `ClassName` | file.py:L | `(arg1, ...) → return` | `caller.func` |
```

Include every public class, key function, and function with cross-module callers.

### Phase 3: Project Instruction File

Keep code detail out of the project instruction file. Add only the analysis-document list and coverage table, behavioral rules, a project-structure tree, and execution examples. Preserve and merge existing rules.

### Phase 4: Coverage

Confirm that every code file in major module directories is covered by at least one analysis document.

### Phase 5: QA Verification

Unless `--skip-qa` is set, invoke the **qa-team** in code-review mode to compare Interface Reference entries with live source.

- Scope: documents updated in this run.
- Minimum: two entries per file, checking signature, path, and line number.
- Portable role: light QA with a fast reviewer; Claude adapter mapping: sonnet.

## Paper Mode

Read owned or reference PDFs and produce per-paper cards plus `<artifact-root>/analysis_project/paper/00_overview_and_constraints.md`. Delegate analysis to the **research-team**. These artifacts become implicit inputs to autopilot-draft, autopilot-code, and autopilot-research.

## Document Mode

Classify reviewer comments, templates, samples, and mixed document sources under `<artifact-root>/analysis_project/doc/{name}/{reviewers,formats,samples,misc}/`. This is the format-spec discovery source for autopilot-draft.

---
*Portable capability contract: `<agent-home>/capabilities/analyze-project.md`; shared skill guidance: `<agent-home>/skills/analyze-project/SKILL.md`.*
