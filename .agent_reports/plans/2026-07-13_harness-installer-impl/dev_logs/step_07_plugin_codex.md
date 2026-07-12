# Step 7.1 — codex plugin channel wrapping (P1, in-cycle per plan boundary)

Implemented directly by the orchestrator (not delegated) given the ongoing
real-HOME incident this session — kept the change small and self-verified
with the dry-run path only, to avoid any further risk of a real-CLI
side effect during verification.

**File changed**: `tools/install/drivers/codex.py`

- Added `_plugin_action(dry_run)`: wraps `codex plugin marketplace add
  <codex_setting/codex-plugin-marketplace> --json` then `codex plugin add
  agent-harness-codex@agent-harness --json` (exact two commands from
  INSTALL_LAYOUT.md Migration Order lines 353-357). CLI-gated via
  `shutil.which("codex")` — absent → `status: "skipped"` SKIP marker, no
  subprocess call. `dry_run=True` → `status: "planned"`, reports the two
  commands as text, never executes them. On real (non-dry-run, CLI present)
  invocation: runs both commands in sequence; any non-zero exit or missing
  binary → `status: "blocked"` (folds into the driver's existing
  `blocked = any(status=="blocked")` aggregation from the Phase 3+4 fix);
  both succeeding → `status: "registered"`.
- `install()`'s `plugin=True` branch now calls `_plugin_action(dry_run)`
  instead of the old unconditional SKIP stub — symlink projection above it
  is untouched and still runs unconditionally (INST-D-5 preserved).
- Added one verify check, `codex.plugin-marketplace-source`
  (`verifier.check_file_exists`), confirming
  `codex_setting/codex-plugin-marketplace/.agents/plugins/marketplace.json`
  exists — i.e. "the plugin marketplace resolves", per Phase 7's done-when.
  (Path corrected after an initial guess at a bare `marketplace.json` failed
  — the real file lives at `.agents/plugins/marketplace.json` under the
  marketplace dir, confirmed via `find`.)
- `drivers/claude.py`'s `plugin=True` path is unchanged from Phase 3 — it
  still emits the deferred SKIP
  (`"SKIP(claude): plugin channel — deferred to next cycle (Phase 7 boundary)"`)
  per the plan's explicit cycle-1 boundary (Claude plugin content generator +
  `install --plugin` wrapping both deferred to a future cycle).

**Verification** (dry-run only, no real subprocess executed — deliberate,
given the session's active real-HOME incident):
- `codex.install(scope='global', plugin=True, dry_run=True)` under a temp
  HOME: plugin action reports `status: "planned"` with both exact command
  lines in `detail`; symlink actions (54) still present/planned alongside it
  (INST-D-5 not violated); temp HOME left empty after the call.
- `codex.checks()` — 63 callables now (was 62), all still constructible;
  the new `codex.plugin-marketplace-source` check runs read-only and
  returns `ok: True` against the real repo tree (source file genuinely
  exists — this check reads repo-tracked files only, not any runtime home).
- The CLI-present execution branch (`shutil.which("codex")` truthy →
  actually calling `codex plugin marketplace add`/`plugin add`) was
  **reviewed statically only, not executed** in this session — running it
  for real would register the marketplace/plugin against whatever
  `CODEX_HOME` the process inherits, and given this session's real-HOME
  incident I chose not to risk that without an explicit temp-`CODEX_HOME`
  harness around it. A future cycle's `code-test` pass (or a careful
  temp-`CODEX_HOME`-scoped single-Bash-call test) should exercise the real
  execution branch before this ships.

**Deferred (per plan's own Phase 7 boundary, not attempted)**: Claude plugin
content generator (materializing `adapters/claude/plugin-marketplace/plugins/
agent-harness-claude/` from SoT) and Claude `install --plugin` CLI wrapping —
both explicitly out of cycle-1 scope per plan.md's Phase 7 section.
