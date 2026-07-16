---
name: analyze-project
description: "Use when persistent analysis of code, a paper, or a document must be created or refreshed because it is absent, stale, or explicitly requested. Not for read-only project orientation, context recovery, or status reporting."
---

# analyze-project

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-project.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info analyze-project`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Before approval, route from this compact metadata and `core/WORKFLOW.md §0.2`; do not read the full portable source merely to propose the route.
2. Present the five-field confirmation card from `core/WORKFLOW.md §0.4` unless the same route and scope are already approved.
3. After approval, direct/quick acting sessions read `capabilities/analyze-project.md`; at `standard+`, the depth-1 owner reads it and stage workers read only their assigned contracts.
4. Run `adapters/codex/bin/preflight.sh capability-info analyze-project` and obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-project`
- Invocation class: `entry-router`
- Supported modes: `code, paper, doc`
- Argument shape: `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`
- Portable meaning: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery.



## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route analyze-project [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
