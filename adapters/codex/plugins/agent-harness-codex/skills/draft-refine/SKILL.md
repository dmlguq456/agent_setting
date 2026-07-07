---
name: draft-refine
description: "Use for draft-refine: 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다."
---

# draft-refine

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/draft-refine.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info draft-refine`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/draft-refine.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info draft-refine`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `draft-refine`
- Supported modes: `none`
- Argument shape: `<strategy or draft name or path> [--qa quick|light|standard|thorough|adversarial]`
- Portable meaning: 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다.

## Portable Contract

- Invocation semantics: Reflect user memos/review feedback in a document strategy or draft. Snapshots prior version under `_internal/versions/v{N}/` (modern; per CONVENTIONS.md §5) or `_v{N}.md` siblings (legacy). Auto-managed `changelog:` array inside YAML frontmatter (NOT a top-of-file HTML comment — that breaks markdown preview when frontmatter is also present). Mandatory ref-grounding per memo (re-read source; override memo if it conflicts with source). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



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
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route draft-refine [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability draft-refine [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
