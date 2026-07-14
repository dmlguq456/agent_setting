---
name: analyze-project
description: "Use for analyze-project: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery."
---

# analyze-project

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-project.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info analyze-project`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/analyze-project.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info analyze-project`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-project`
- Supported modes: `code, paper, doc`
- Argument shape: `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`
- Portable meaning: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery.

## Portable Contract

- Invocation semantics: Pre-work analysis capability — analyzes the project's primary materials and writes structured artifacts to `<artifact-root>/analysis_project/`. Invoke it only when no usable project analysis exists, existing analysis is demonstrably stale for the requested downstream work, or the user explicitly requests a persistent analysis document or refresh. A request to understand the current project, recover prior context, resume work, or report status is read-only orientation and is not an `analyze-project` trigger by itself. When analysis already exists, read it before deciding that reanalysis is needed. Three modes are available: code (codebase), paper (academic PDFs), and doc (miscellaneous document materials such as reviewer comments, format templates, samples, and internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit `--mode paper`. Output is the persistent input source for downstream `autopilot-{draft,code,research}` capabilities. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Routing Boundary

Before invocation, follow `core/WORKFLOW.md §0.1`: resolve the existing
artifact root through the adapter status surface and inspect current summaries,
state, spec, run logs, and relevant prior analysis. Existing
`.claude_reports/` is the legacy form of the same project-state surface when
`.agent_reports/` is absent.

For read-only orientation, do not invoke this capability and do not create or
update `analysis_project/`. Memory recall may supplement continuity after the
artifact read, but relevant memory paths must be followed and checked against
the current artifact or live code before reporting project state.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route analyze-project [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
