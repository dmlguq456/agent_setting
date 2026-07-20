---
name: autopilot-note
description: "Use when existing artifacts must be collected, digested, triaged, or routed into a durable note workflow. Not for storing one scoped memory item or for performing the primary research, code, or document work."
---

# autopilot-note

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-note.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-note`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Before approval, route from this compact metadata and `core/WORKFLOW.md §0.2`; do not read the full portable source merely to propose the route.
2. Present the five-field confirmation card from `core/WORKFLOW.md §0.4` unless the same route and scope are already approved.
3. After approval, direct/quick acting sessions read `capabilities/autopilot-note.md`; at `standard+`, the dispatch-depth-1 owner reads it and stage workers read only their assigned contracts.
4. Run `adapters/codex/bin/preflight.sh capability-info autopilot-note` and obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-note`
- Invocation class: `entry-router`
- Supported modes: `none`
- Argument shape: `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]`
- Portable meaning: Route and note artifacts, producing digests and triage proposals.



## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-note [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-note [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]` and `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
