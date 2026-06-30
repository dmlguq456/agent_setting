---
name: code-report
description: "Use when the user requests code-report: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# code-report

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/code-report.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info code-report`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/code-report.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info code-report`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `code-report`
- Supported modes: `none`
- Argument shape: `<plan name or path>`
- Portable meaning: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다.

## Portable Contract

- Invocation semantics: Generate a detailed change report from plan + dev logs — focuses on key changes, principles, and insights for future reference Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



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


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route code-report [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability code-report [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
