# Phase 2 — `drivers/claude.py`: `install --plugin` Claude wrapping

**File changed**: `tools/install/drivers/claude.py`

## Implementation (matches plan Step 2.1–2.2)

- Added module constants: `_MARKETPLACE_SOURCE_RELPATH =
  "adapters/claude/plugin-marketplace"`, `_MARKETPLACE_NAME = "agent-harness"`,
  `_PLUGIN_SPEC = "agent-harness-claude@agent-harness"`.
- Added `_plugin_action(dry_run)`, mirroring `drivers/codex.py._plugin_action`
  (L33-86 there): `marketplace_cmd = ["claude", "plugin", "marketplace",
  "add", marketplace_source]`, `plugin_cmd = ["claude", "plugin", "install",
  _PLUGIN_SPEC]`. `dry_run` → `status:"planned"` with both command strings in
  `detail`, no subprocess. `shutil.which("claude") is None` → `status:
  "skipped"` SKIP. Runs marketplace add then plugin install in sequence
  (`timeout=60`, `capture_output=True`); non-zero exit / `FileNotFoundError`
  / `TimeoutExpired` at either step → `status:"blocked"`; both succeeding →
  `status:"registered"`.
- **Deviation from the Codex analogue (deliberate, per Step 2.1's
  runtime-currentness note)**: neither `marketplace_cmd` nor `plugin_cmd`
  carries a `--json` flag. Verified live: `claude plugin marketplace add
  --help` and `claude plugin install --help` — neither subcommand exposes a
  `--json` output flag (only `claude plugin marketplace list --json` and
  `claude plugin list --json`, the read-only query commands, support it).
  Both mutating commands are already non-interactive by default (no
  confirmation prompt observed in the live test below), so no flag was
  needed for the non-interactive contract itself.
- Replaced the old unconditional SKIP block (`plugin=True` → `SKIP(claude):
  plugin channel — deferred to next cycle`) in `install()` with `if plugin:
  actions.append(_plugin_action(dry_run))`.
- **INST-D-5 parity preserved by construction**: the plugin action is
  appended to `actions` alongside — not instead of — the symlink/copy_once
  loop that follows; nothing in the symlink loop was touched. Confirmed
  empirically below (17 symlink/copy_once actions present in the same
  `dry_run=True, plugin=True` call that also returns the plugin action).
- `blocked = any(a.get("status") == "blocked" for a in actions)` (unchanged
  in this file) already covers the new action since it's a plain dict in
  the same `actions` list.

## Verification (single self-contained scripts per Phase-5-style isolation
contract — mktemp `HOME`/`CLAUDE_CONFIG_DIR` set at top of one Bash call,
determinism trap on EXIT, no cross-call `export`)

1. **Dry-run, mktemp `HOME`**: `claude.install(scope="global", plugin=True,
   dry_run=True)` → plugin action `status:"planned"`, detail contains both
   exact command lines (`claude plugin marketplace add
   <repo>/adapters/claude/plugin-marketplace ; claude plugin install
   agent-harness-claude@agent-harness`); 17 symlink/copy_once actions also
   present in the same result; `blocked: False`. Trap: real
   `~/.claude/settings.json` sha256 unchanged after.
2. **CLI-absent SKIP, mktemp `HOME` + `claude` stripped from `PATH`** (only
   the directory containing the `claude` binary removed, coreutils kept for
   the trap): `claude.install(..., plugin=True, dry_run=False)` → plugin
   action `status:"skipped"`, detail `SKIP(claude): plugin channel wrapping
   — claude CLI absent`. No subprocess invoked (would have raised/hung
   otherwise since `claude` isn't resolvable). Trap held.
3. **Real CLI, mktemp `HOME` + mktemp `CLAUDE_CONFIG_DIR`**: `claude.install(
   ..., plugin=True, dry_run=False)` with `claude` CLI present on `PATH` →
   plugin action `status:"registered"`, detail `marketplace + plugin
   install OK: agent-harness-claude@agent-harness`. Cross-checked via direct
   read-only `claude plugin marketplace list --json` (shows `agent-harness`
   pointing at the repo's `adapters/claude/plugin-marketplace`) and `claude
   plugin list --json` (shows `agent-harness-claude@agent-harness`,
   `enabled: true`, `installPath` under the mktemp `CLAUDE_CONFIG_DIR`'s
   `plugins/cache/`, not under real `~/.claude/plugins`). Trap: real
   `~/.claude/settings.json` sha256 **and** a full recursive sha256 listing
   of real `~/.claude/plugins/` (if present) both unchanged after — held.

All three scripts ran as a single Bash invocation each (env exported at the
top, `trap ... EXIT` inline in the same call) — no attempt to carry `export`
across separate Bash calls (cycle-1 incident class, plan Phase 5 §1).

**Done-when (plan Phase 2)**: met — `--plugin --dry-run` prints both CLI
commands + full projection plan; CLI-absent real run emits SKIP; symlink
projection present in both; real CLI path registers end-to-end under
isolated `CLAUDE_CONFIG_DIR` without touching the real `~/.claude`.
