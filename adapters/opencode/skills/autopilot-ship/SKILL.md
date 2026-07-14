---
name: autopilot-ship
description: "Use for autopilot-ship: Prepare application deployment/release setup and a ship checklist."
metadata:
  portable_source: capabilities/autopilot-ship.md
  adapter: opencode
---

# autopilot-ship

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-ship.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-ship`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-ship.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-ship`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-ship`
- Supported modes: `none`
- Argument shape: `<task description (optional)> [--intensity direct|quick|standard|strong|thorough|adversarial]`
- Portable meaning: Prepare application deployment/release setup and a ship checklist.

## Portable Contract

- Invocation semantics: Application deployment-setup entrypoint for projects with an existing `spec/` and substantially complete functionality. Guide the first ship setup, environment, domain, and migration deployment; select hosting (Vercel, Fly, Railway, Cloudflare, or EAS); create CI/CD files, `.env.example`, domain guidance, and a deployment record. The user runs real deployment commands; this skill provides guidance only. Keep it distinct from autopilot-spec's initial spec/skeleton work. It may be rerun for environment changes, added domains, or production migration deployment. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-ship [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
