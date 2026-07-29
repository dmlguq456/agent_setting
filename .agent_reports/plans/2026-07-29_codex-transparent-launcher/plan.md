# Codex transparent managed launcher

## Objective

Make the GitHub release installer and the Codex plugin-channel installer install
a reversible `codex` launcher so interactive `codex`, `resume`, and `fork`
sessions automatically use the checked App Server gateway. Preserve the real
Codex CLI for `exec`, `review`, `plugin`, `update`, and every other
non-interactive or administrative subcommand. Replace Claude's model-driven
recurring owner monitor with one runtime-owned exact-attempt wake receipt.

## Classification

- Primary: `autopilot-code/dev`
- Secondary: `autopilot-spec/update`
- Intensity: `direct`, executed inline under
  `dispatch-infrastructure-self-modification`
- Spec significance: SPEC-SIGNIFICANT — production rollout changes from manual
  canary entry to installer-owned transparent entry
- Governing contracts: `core/OPERATIONS.md`, `core/HOOKS.md`

The registered completion path being repaired cannot safely own this cycle.
The current interactive parent is precisely the unmanaged surface that the
existing gate rejects, so implementation and verification stay in this session
with the exception recorded in `_internal/metrics.md`.

The existing stage-dispatch PRD and pipeline files were already modified by
other work before this cycle. They are not overwritten; the latest explicit
user decision is reflected in the clean core contract and source implementation.

## Work

1. Promote checked launcher-managed Codex entry from manual canary use to an
   installer-owned, reversible runtime surface in core.
2. Add an argument-routing launcher that manages only interactive surfaces and
   invokes the preserved real Codex binary for all other commands.
3. Add guarded installer ownership for the `codex` shim, original-command
   metadata, secure runtime state, update repair, and uninstall restoration.
4. Cover command classification, recursion avoidance, install/update repair,
   collision refusal, and restoration with focused regressions.
5. Synchronize Codex adapter documentation and run the focused plus portable
   verification suites.
6. Add a Claude `PostToolUse(Bash)` `asyncRewake` bridge that arms only from a
   successful same-session owner start and explicitly forbids recurring
   Background Bash/Monitor/dispatch-wait re-arms.

## Completion

- A clean test home can install the Codex runtime and invoke plain `codex`
  through `codex-managed-entry.py` without hand-written managed-entry flags.
- `codex exec`, plugin/update/admin commands reach the preserved real binary.
- Reinstall/update is idempotent and uninstall restores the original command.
- Unsafe foreign command collisions and unsafe runtime permissions fail closed.
- Focused installer/launcher tests and relevant adapter boundary checks pass.
- Claude owner completion emits one exact-attempt wake and ordinary Bash calls
  remain no-ops.
