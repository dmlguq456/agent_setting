---
name: analyze-project
description: "Use when needed: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery."
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

- Invocation semantics: Pre-work analysis capability — analyzes the project's primary materials and writes structured artifacts to `<artifact-root>/analysis_project/`. Invoke it only when no usable project analysis exists, existing analysis is demonstrably stale for the requested downstream work, or the user explicitly requests a persistent analysis document or refresh. A request to understand the current project, recover prior context, resume work, or report status is read-only orientation and is not an `analyze-project` trigger by itself. When analysis already exists, read it before deciding that reanalysis is needed. That orientation starts with one targeted, agent-chosen memory recall; reads a shortened relevant hit in full by record ID; prefers `.agent_reports/` and uses `.claude_reports/` only when the canonical root is absent; then reads the newest report/experiment artifact with its current PRD/spec before primary code or data. Resolve drift as latest spec or user confirmation, durable project fact, latest experiment contract, then legacy document, and report the conflict instead of silently selecting the older value. Three modes are available: code (codebase), paper (academic PDFs), and doc (miscellaneous document materials such as reviewer comments, format templates, samples, and internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit `--mode paper`. Output is the persistent input source for downstream `autopilot-{draft,code,research}` capabilities. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



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

Before invocation, follow `core/WORKFLOW.md §0.1`: run one targeted,
agent-chosen memory recall and read any shortened relevant hit in full by
record ID; prefer `.agent_reports/`, falling back to `.claude_reports/` only
when the canonical root is absent; then inspect the newest report and
experiment artifacts plus current PRD/spec before checking primary code or
data. This order is context recovery, not persistent reanalysis.

For read-only orientation, do not invoke this capability and do not create or
update `analysis_project/`. Follow relevant memory paths and resolve drift with
this precedence: latest specification or user-confirmed decision, durable
project fact, latest experiment contract, then legacy document. Report a
conflict instead of silently combining or selecting the older value.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route analyze-project [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
