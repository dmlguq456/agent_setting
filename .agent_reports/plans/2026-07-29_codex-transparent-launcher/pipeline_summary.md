# Pipeline summary

## Result

Implemented installer-owned transparent managed entry for ordinary interactive
Codex launches and replaced Claude's recurring model-visible owner monitoring
with one native async exact-attempt wake.

## Delivered

- GitHub runtime activation and Codex plugin installation now create or repair a
  manifest-backed `~/.local/bin/codex` launcher.
- Interactive `codex`, `resume`, and `fork` enter the checked managed App Server
  gateway; headless and administrative subcommands reach the preserved real CLI.
- Update repairs wrapper or moved real-CLI bindings. Uninstall restores the
  recorded previous command binding and prior Codex-home mode.
- Private `CODEX_HOME` projections no longer mutate or depend on the global CLI
  ingress unless `HARNESS_BIN_DIR` is explicitly supplied.
- Claude arms `dispatch-owner-rewake.py` only from one successful exact owner
  start in the same session, waits outside the model, and emits one bounded
  harvest receipt without Background Bash, Monitor, liveness, or re-arm loops.

## Verification

- Launcher installer tests: 7 passed.
- Launcher runtime tests: 6 passed.
- Claude re-wake tests: 6 passed on canonical and adapter projection.
- Codex managed entry/dispatch and Claude supervisor suites: passed.
- Runtime activation and release lifecycle suites: passed.
- Generation, adaptation boundary, utility census, syntax, and diff checks:
  passed.
- Portable guards: 393 passed; 2 unrelated existing failures remained in Codex
  custom-agent TOML discovery and context-footprint baseline checks.

## Local projection

The local Codex launcher is installed and healthy against Codex CLI 0.146.0.
The Claude hook was merged through the runtime activator's normal backup-aware
settings merger; a new Claude session is required to load it. A full source
reactivation remains blocked by the pre-existing absolute symlink under
`.core-grounding`, which this cycle intentionally did not modify.
