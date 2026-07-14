---
description: "Run the portable post-it capability through the OpenCode adapter. Meaning: Store project/cross-project notes and handoffs in working memory."
---

Use the OpenCode adapter realization of portable capability `post-it`.
This is adapter-owned output generated from `capabilities/post-it.md`, not a runtime-specific command copy.

1. Read `capabilities/post-it.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info post-it` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability post-it [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[show]|add <category> <text>|resolve <hint>|decide <text>|handoff [--no-confirm]|sweep [--no-confirm]|promote [<hint>] [--scope project|user [<aspect>]]`.

Portable contract excerpt:

- Invocation semantics: Manually-controlled working-memory layer, two scopes. `--scope project` (default): `mem note`/`mem add` (working tier, per-cwd) — thread/decision/convention/reference records in DB. `--scope user <aspect>`: `mem add` (durable, global, profile-adjacent) — splices a note into the `## 사용자 수동 메모` block of the profile record (`source user-profile:<stem>`), shared with analyze-user. All entries are designed to graduate (into artifacts/profiles) or expire — `sweep` flags stale working records; `promote` graduates user notes into the profile record. DB working tier is injected at session start by `mem inject` (not a file read). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
