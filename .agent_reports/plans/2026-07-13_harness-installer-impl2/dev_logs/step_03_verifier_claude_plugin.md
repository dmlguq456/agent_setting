# Phase 3 — `drivers/claude.py` `checks()`: plugin verify checks

**File changed**: `tools/install/drivers/claude.py` (`checks()` only; `verifier.py`
core untouched — reused `check_cmd`/`check_file_exists` as the plan requires).

## Implementation (matches plan Step 3.1–3.3)

- **3.1 generator drift**: `verifier.check_cmd("claude.sync-native-plugin",
  ["python3", "adapters/claude/bin/sync-native-plugin.py", "--check"],
  cwd=agent_home)` — read-only subprocess, asserts the plugin content isn't
  stale vs SoT.
- **3.2 marketplace source presence**: `verifier.check_file_exists(
  "claude.plugin-marketplace-source", <resolve_source(_MARKETPLACE_SOURCE_RELPATH)>/
  .claude-plugin/marketplace.json)` — mirrors `codex.plugin-marketplace-source`.
- **3.3 CLI-gated registration check** (`_plugin_registered`, new closure
  inside `checks()`): `shutil.which("claude") is None` → SKIP (`ok:True`,
  detail explains absence — same convention as `_bootstrap_smoke`). If
  present: runs `claude plugin marketplace list --json` (read-only, verified
  live to support `--json` — see dev_logs/step_01), parses JSON, checks an
  entry with `name == "agent-harness"`; if present, runs `claude plugin list
  --json` and checks an entry with `id == "agent-harness-claude@agent-harness"`.
  Any missing → `ok:False` with an actionable detail (which `claude plugin`
  command would fix it); both present → `ok:True`. **Never calls `marketplace
  add`/`plugin install`** — only the two `list --json` read paths.

## Verification (single self-contained scripts, mktemp isolation, real-home
determinism trap on `~/.claude/settings.json` + recursive sha256 of
`~/.claude/plugins/` — same contract as Phase 2)

1. **Clean-tree, mktemp `HOME`, no plugin installed yet**:
   `claude.checks()` returns **23** callables (was 20 pre-Phase-3: +3 new).
   `verifier.run("claude", claude)` executed all 23; the three new IDs are
   present. `claude.sync-native-plugin` → `ok:True` (repo tree is not stale,
   confirms Phase 1's generator + this repo's committed generated output
   agree). `claude.plugin-marketplace-source` → `ok:True` (file exists in
   the repo tree — this check reads the repo, not any runtime home).
   `claude.plugin-registered` → **`ok:False`**, detail `marketplace
   'agent-harness' 미등록 (claude plugin marketplace add 필요)` — correct:
   under a fresh mktemp `HOME` nothing is registered yet, and the check
   truthfully reports that rather than SKIPping (CLI is present, so it
   isn't the CLI-absence SKIP branch — it's read-only real state).
2. **Post-registration, mktemp `HOME` + mktemp `CLAUDE_CONFIG_DIR`**: ran
   `claude.install(plugin=True, dry_run=False)` (registers, per Phase 2)
   then immediately `verifier.run("claude", claude)` in the same script/env
   — `claude.plugin-registered` flips to `ok:True`, detail `OK: marketplace
   'agent-harness' + plugin 'agent-harness-claude@agent-harness' 등록 확인`.
   Determinism trap (settings.json sha256 + recursive plugins-dir sha256)
   held in both scripts; both mktemp dirs removed on exit.

**Not separately re-tested here** (already covered by Phase 2's dev_log):
the CLI-absent SKIP path for `_plugin_registered` — same `shutil.which`
guard pattern as `_plugin_action`/`_bootstrap_smoke`, both already verified
working under a `PATH`-stripped script in Phase 2.

**Done-when (plan Phase 3)**: met — `harness verify claude --json`-equivalent
(`verifier.run`) returns the 3 new checks; all read-only (no `marketplace
add`/`install` ever called from `checks()`); exit/ok 0/True on a clean,
unregistered tree for the two static checks, and the registration check
truthfully reflects live state without mutating anything.
