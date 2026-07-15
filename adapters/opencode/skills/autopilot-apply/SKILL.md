---
name: autopilot-apply
description: "Use when needed: Apply a cheatsheet draft to the real source artifact and verify the result."
metadata:
  portable_source: capabilities/autopilot-apply.md
  adapter: opencode
---

# autopilot-apply

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-apply.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-apply`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-apply.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-apply`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-apply`
- Supported modes: `none`
- Argument shape: `"<cheatsheet hint / task>" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]`
- Portable meaning: Apply a cheatsheet draft to the real source artifact and verify the result.

## Portable Contract

- Invocation semantics: Autopilot family — the document-side _apply + verify_ arm. Takes a draft-produced cheatsheet (a mutation/edit plan) and applies it to a real working source file _outside_ `<artifact-root>/` (e.g. the user's `main.tex`), under git, with a build/compile verify gate. This is the missing counterpart to autopilot-draft: draft _produces_ the cheatsheet (plan), autopilot-apply _executes_ it on the canonical source and _verifies_ it compiles — mirroring code-execute + code-test on the code side. Default target `latex` (latexmk compile gate + latexdiff rendered-diff review). Never touches the canonical source directly: applies on a git branch (or worktree), each mutation = one commit, hands back via `git merge`. Cheatsheet auto-discovered from `<artifact-root>/documents/*/draft/`. NOT for `<artifact-root>/` markdown artifacts (use autopilot-refine) or codebases (use autopilot-code). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-apply [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
