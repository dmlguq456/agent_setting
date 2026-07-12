# Execute Log

- Updated core SoT for quick depth-1 one-shot semantics and preserved depth-2 prohibition.
- Updated capability contracts, adapter bootstraps, and dispatch prompts for Codex/OpenCode/Claude mirror.
- Added Fleet quick depth1 `quick/exec` breadcrumb rendering and tests for quick depth2 rejection.
- Regenerated Codex/OpenCode native skill/plugin/command projections from the updated portable specs.
- Verification passed for `python3 tools/fleet/tests/test_dispatch.py`, `python3 tools/fleet/tests/test_mirror_parity.py`, `python3 adapters/codex/bin/sync-native-skills.py --check`, `python3 adapters/codex/bin/sync-native-plugin.py --check`, `python3 adapters/opencode/bin/sync-native-skills.py --check`, `python3 adapters/opencode/bin/sync-native-commands.py --check`, and `git diff --check`.
- `hooks/portable-guards.test.sh` still reports unrelated existing BAD cases outside the quick depth1/2 contract path; the new quick depth1 and quick depth2 wrapper checks pass when run directly.
