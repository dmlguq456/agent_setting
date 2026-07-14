---
description: "Run the portable autopilot-ship capability through the OpenCode adapter. Meaning: Prepare application deployment/release setup and a ship checklist."
---

Use the OpenCode adapter realization of portable capability `autopilot-ship`.
This is adapter-owned output generated from `capabilities/autopilot-ship.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-ship.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-ship` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-ship [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description (optional)> [--intensity direct|quick|standard|strong|thorough|adversarial]`.

Portable contract excerpt:

- Invocation semantics: Application deployment-setup entrypoint for projects with an existing `spec/` and substantially complete functionality. Guide the first ship setup, environment, domain, and migration deployment; select hosting (Vercel, Fly, Railway, Cloudflare, or EAS); create CI/CD files, `.env.example`, domain guidance, and a deployment record. The user runs real deployment commands; this skill provides guidance only. Keep it distinct from autopilot-spec's initial spec/skeleton work. It may be rerun for environment changes, added domains, or production migration deployment. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
