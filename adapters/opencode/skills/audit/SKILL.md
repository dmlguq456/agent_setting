---
name: audit
description: "Use for audit: Read-oriented post-run inspection for artifact drift, inconsistency, and omissions."
metadata:
  portable_source: capabilities/audit.md
  adapter: opencode
---

# audit

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/audit.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info audit`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/audit.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info audit`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `audit`
- Supported modes: `none`
- Argument shape: `<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]`
- Portable meaning: Read-oriented post-run inspection for artifact drift, inconsistency, and omissions.

## Portable Contract

- Invocation semantics: Read-only multi-aspect audit/lint for `<artifact-root>/{plans,research,documents}/*` artifacts. A single global entry auto-detects artifact type from the path prefix (`plans`=code, `research`=field survey, `documents`=document deliverable). Per-type aspects: documents use facts/style/structure/cross-reference/coverage; research uses card integrity/tier consistency/coverage/cross-card checks; plans use test results, lint, code review, TODOs, and unimplemented work. `--scope auto` selects from artifact characteristics by default; an explicit user scope overrides it. Report only—never modify the artifact. This complements autopilot-refine: refine edits, while audit inspects. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability audit [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
