---
name: autopilot-apply
description: "Use for autopilot-apply: Apply a cheatsheet draft to the real source artifact and verify the result."
---

# autopilot-apply

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-apply.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-apply`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-apply.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-apply`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-apply`
- Supported modes: `none`
- Argument shape: `\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]`
- Portable meaning: Apply a cheatsheet draft to the real source artifact and verify the result.

## Portable Contract

- Invocation semantics: Autopilot family — the document-side _apply + verify_ arm. Takes a draft-produced cheatsheet (a mutation/edit plan) and applies it to a real working source file _outside_ `<artifact-root>/` (e.g. the user's `main.tex`), under git, with a build/compile verify gate. This is the missing counterpart to autopilot-draft: draft _produces_ the cheatsheet (plan), autopilot-apply _executes_ it on the canonical source and _verifies_ it compiles — mirroring code-execute + code-test on the code side. Default target `latex` (latexmk compile gate + latexdiff rendered-diff review). Never touches the canonical source directly: applies on a git branch (or worktree), each mutation = one commit, hands back via `git merge`. Cheatsheet auto-discovered from `<artifact-root>/documents/*/draft/`. NOT for `<artifact-root>/` markdown artifacts (use autopilot-refine) or codebases (use autopilot-code). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



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
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-apply [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-apply [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
