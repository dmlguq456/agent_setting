# Implementation log

## Root-cause closure

The dispatch adapter had one overloaded `mode` value for two independent axes:
capability behavior and worker persona. Because the validator only checked the
`family/mode` shape, a depth-1 owner could be bootstrapped as `plan/plan-author`.

## Changes

- Added `utilities/dispatch_mode_contract.py` as the shared parser and tuple
  validator for canonical and legacy arguments.
- Updated Claude, Codex, and OpenCode dispatch wrappers to persist
  `capability_mode` and `worker_mode` separately and reject ambiguity before any
  prompt, registry row, or child spawn.
- Made the portable `unit` the authoritative worker persona. An owner is exactly
  `_kernel/owner` with no worker mode; a non-owner compatibility worker mode must
  equal its non-reserved unit.
- Updated route/node and fallback writers so depth-1 owners emit only capability
  mode while depth-2 stages preserve their worker unit once.
- Updated Fleet collection, model, rendering, and Claude mirror. Clean owners show
  capability mode only; inconsistent legacy owner slash-mode rows surface `mode!`.
- Retained legacy `--mode` parsing for old callers and rows without allowing new
  writers to serialize another overloaded `mode=` field.

## Integration

Implementation commit `89b59d72` was fast-forwarded to `main`, pushed to origin,
and its isolated source worktree was removed through checked cleanup.
