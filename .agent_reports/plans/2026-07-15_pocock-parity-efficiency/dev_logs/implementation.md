# Implementation log

## Portable contract

- Made `core/`, `capabilities/`, and `roles/` the explicit semantic parent of Claude, Codex, and OpenCode sibling adapters.
- Defined shared completion as partial until every applicable adapter realization, fallback, active discovery surface, and footprint is verified.
- Added fixed-input-first budgets: 16,384-byte bootstrap, 7,000-character active Skill metadata, zero-byte ordinary hooks, 240-byte maximum verified pressure transition, and 5% baseline growth rejection.
- Kept production savings claims gated on at least 30 paired real sessions with input, cache creation, output, and billable cost separated.

## Adapter realization

- Replaced the three large bootstraps with compact routers that retain source order, hard invariants, runtime commands, dispatch, memory/context, and response policy while moving detailed edge cases behind adapter docs and command help.
- Extended Skill conformance from the Claude trees to the portable 27-capability domain across Claude, Codex, and OpenCode native projections.
- Generated Pocock-compatible `Use when needed:` descriptions for Codex/OpenCode without increasing metadata; regenerated native and plugin projections.
- Updated the existing Codex plugin through the cachebuster flow and kept its generator version deterministic.

## Measurement and guards

- Upgraded `context-footprint --strict` to measure bootstrap bytes, normalized metadata regression, concrete active runtime paths, duplicate discovery, hook emissions, and a checked baseline.
- Kept path-neutral baseline values separate from concrete runtime-path budgets so checkout location is not mistaken for source growth.
- Added sibling/context invariants to the adaptation boundary and changed the bootstrap negative fixture to the 16 KiB ceiling.
- Official runtime evidence supports the chosen progressive-disclosure shape: Codex initially loads only Skill name/description/path with an 8,000-character safety budget, Claude preloads Skill metadata and loads bodies on demand, and OpenCode loads Skill bodies through its native Skill tool on demand.

## Execution topology

- Codex headless could not use the isolated worktree because the installed projection pointed to the primary checkout.
- The OpenCode depth-1 owner repeated a fixture under the dispatch-injected canonical artifact root and made no implementation progress; it was terminated and harvested.
- The core/bootstrap/guard refactor was completed inline under the recorded boundary-coupled fallback. No worker output is counted as implementation or savings evidence.

## Integration and activation

- Merged the portable-first implementation into the primary checkout and activated the same common `builder` profile for Claude, Codex, and OpenCode.
- Replaced the Codex legacy all-projection doctor assumption with profile-aware validation backed by the portable runtime activation record.
- Added bounded detection and transactional cleanup for stale harness-owned native links outside the selected profile. A regression test proves that a legacy harness link is removed while a user-owned agent file is preserved.
- Migrated the pre-existing Codex whole-directory mode link to profile-owned per-file links once; subsequent activation is handled by the common profile transaction.
