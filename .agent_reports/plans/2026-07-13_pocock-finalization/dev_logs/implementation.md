# Implementation log — Pocock finalization

## Baseline

- Started from `016a883` (`origin/main`), where the 14-capability `--qa` cleanup was already merged.
- Worked in branch/worktree `pocock-finalize` / `/home/Uihyeop/agent_setting-wt/pocock-finalize`.
- Headless dispatch preflight failed only on installed Codex `hooks.json` projection trust/identity, so the documented manual current-session fallback was used.

## Changes

1. Added an English `Use when…` first sentence to `autopilot-ship` while preserving the Korean blurb.
2. Classified all 13 entry routers and all 13 parent-invoked pipeline skills in `invocation-policy.tsv`.
3. Replaced the two P8-targeted anti-pattern negations in `design-components` with positive executable outcomes.
4. Added a Claude concrete projection for `tools/skill-conformance/{check.sh,scan.sh,invocation-policy.tsv}`.
5. Classified `skill-conformance` as deferred for Codex/OpenCode selective tool projections and documented why in `core/ADAPTATION_INVENTORY.md`.
6. Regenerated the Claude native plugin and manifest; refreshed the two changed skill hashes in `skills/.sync_state.json`.
7. Synchronized the original cycle state/checklist/summary from partial/RED to Pocock-scope done/GREEN.

## Design decisions

- The repository contract continues to encode the English trigger in `description`; current Claude documentation also exposes `when_to_use`, but adopting that new field would be a separate schema/design change rather than this closure.
- P8 changes were deliberately limited to the two negations named by the audit evidence. Safety and destructive-action guardrails were preserved.
- A full adaptation-boundary cleanup was not expanded into this cycle: after the focused fix, only unrelated `INSTALL_LAYOUT.md` parity failures remain.
