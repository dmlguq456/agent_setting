# Phase 1 — `adapters/claude/bin/sync-native-plugin.py` (Claude plugin content generator)

**New file**: `adapters/claude/bin/sync-native-plugin.py` (mirrors
`adapters/codex/bin/sync-native-plugin.py`, extended per
`_internal/hooks_inventory.md` note — skills + agents + hooks + hooks.json,
not skills-only).

## Runtime-currentness check (before finalizing schemas)

Local `claude` CLI is present (`claude 2.1.207`) — verified live instead of
assuming from the Codex analogue:

- `claude plugin marketplace add <source>` — non-interactive, no `--json`
  output flag exists for this subcommand (`claude plugin marketplace add
  --help`). Empirically confirmed under a mktemp `CLAUDE_CONFIG_DIR`:
  `Adding marketplace…✔ Successfully added marketplace: agent-harness
  (declared in user settings)`, exit 0.
- `claude plugin install <plugin>` (alias `i`) — non-interactive, `-s/--scope
  <user|project|local>` (default `user`), `--config` for userConfig; no
  `--json` flag either (`claude plugin install --help`). So neither wrapped
  command gets a `--json` flag (unlike the Codex analogue, which does) —
  command arrays built without it.
- Read-only queries **do** support `--json`: `claude plugin marketplace list
  --json` and `claude plugin list [--available] --json`. Used
  `marketplace list --json` for the Phase 3 registration check.
- `CLAUDE_CONFIG_DIR` env var empirically confirmed to redirect Claude's
  entire config root (verified: `CLAUDE_CONFIG_DIR=<mktemp> claude plugin
  marketplace list --json` created `<mktemp>/.claude.json` +
  `<mktemp>/backups/`, real `~/.claude` untouched) — this is the isolation
  primitive Phase 5's test scripts must use.
- `claude plugin marketplace add <local-repo-path>` against the on-disk
  skeleton succeeded end-to-end under the mktemp config dir and the
  subsequent `marketplace list --json` reflected it
  (`source: "directory"`, `path: <repo>/adapters/claude/plugin-marketplace`).
- Fetched current official docs (`code.claude.com/docs/en/plugins-reference`,
  `.../plugin-marketplaces`) via WebFetch to pin two schema details that the
  plan flagged as a runtime-currentness risk:
  1. **`hooks/hooks.json` is wrapped under a top-level `"hooks"` key**
     (`{"hooks": {"PreToolUse": [...]}}`), NOT the flat
     `{"PreToolUse": [...]}` shape `adapters/claude/settings.json` uses.
     Docs example: `{"hooks": {"PostToolUse": [{"matcher": "Write|Edit",
     "hooks": [{"type": "command", "command":
     "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh"}]}]}}`.
  2. **`marketplace.json` plugin `source` accepts a bare relative-path
     string** for local directories (`"source": "./plugins/<name>"`),
     which is exactly the shape the existing skeleton
     `marketplace.json`/plan already used — confirmed correct, no change
     needed there. Paths resolve relative to the marketplace root (the dir
     containing `.claude-plugin/`).

## Implementation (matches plan Steps 1.1–1.5)

- Constants: `ROOT = parents[3]`, `ADAPTER`, `PLUGIN_NAME =
  "agent-harness-claude"`, `MARKETPLACE_ROOT`, `MARKETPLACE`, `PLUGIN_ROOT`,
  `SKILLS`, `AGENTS`, `HOOKS_SOURCE = ROOT/"hooks"` (repo-root hooks/, not
  `adapters/claude/hooks/` — that dir doesn't exist as a source; hooks live
  at repo root and are only *referenced* from `adapters/claude/settings.json`).
  `HOOK_ADOPT = ["git-state-guard.sh", "artifact-guard.sh"]` per
  `_internal/hooks_inventory.md`'s conclusion.
- `plugin_json()`/`marketplace_json()` reproduce the existing skeleton files
  byte-for-byte (verified via `--check` after first `sync()` — zero diff).
- `hooks_json()` — registers both adopted hooks on `PreToolUse`, matcher
  and shell (`sh`/`bash`) copied verbatim from
  `adapters/claude/settings.json`'s own registration of these two hooks
  (`git-state-guard.sh`: `Edit|Write|MultiEdit|NotebookEdit`, `sh`;
  `artifact-guard.sh`: `Edit|Write|MultiEdit`, `bash`), command path rebased
  to `${CLAUDE_PLUGIN_ROOT}/hooks/<name>`.
- `sync()` — guards on `SKILLS`/`AGENTS` existing, writes plugin.json +
  marketplace.json, then rmtree-then-copytree for `skills/` (28 dirs) and
  `agents/` (9 files), then rmtree-then-mkdir+copy2 for `hooks/` (2 files)
  + `hooks.json` write. README.md at plugin root is never touched (not in
  any rmtree'd subtree).
- `check()`/`check_file()` — byte-compare plugin.json/marketplace.json/
  hooks.json against their literals; per-file byte-compare for each
  `skills/*/SKILL.md`, `agents/*.md`, and the 2 adopted hook scripts;
  excess-file detection walks each generated subtree and flags anything not
  in the expected set (covers stray hand-edits and SoT deletions across all
  three content trees — plan's "do not over-mirror Codex" risk item).
- **Deviation from plan draft**: initial `json.dumps(...)` calls used the
  default `ensure_ascii=True`, which `—`-escaped the em dash in the
  description strings and produced a spurious byte-diff against the
  existing skeleton files (git showed them as modified after first `sync()`
  even though content was semantically identical). Fixed by adding
  `ensure_ascii=False` to every `json.dumps` call (both `write_json()` and
  the three `check_file()` comparisons in `check()`) — now byte-identical
  to the pre-existing skeleton, confirmed via `git diff` showing no changes
  to `plugin.json`/`marketplace.json` after `sync()`.

## Verification

- `python3 -m py_compile adapters/claude/bin/sync-native-plugin.py` — OK.
- `--check` before first `sync()`: exit 1, lists all 42 expected-but-missing
  paths (plugin.json content mismatch, marketplace.json content mismatch,
  hooks.json, 28 skills, 9 agents, 2 hooks).
- `sync()`: materializes the full tree; `--check` immediately after: exit 0.
- Idempotency: sha256 of every file under
  `plugins/agent-harness-claude/` before/after a second `sync()` run —
  identical (`diff` empty).
- Drift detection: appended a line to
  `skills/audit/SKILL.md` (generated copy) → `--check` exit 1, flags exactly
  that one file; re-ran `sync()` → `--check` exit 0 again.
- Write-set confinement: `git status --porcelain` after all runs shows only
  changes under `adapters/claude/bin/sync-native-plugin.py` (new file) and
  `adapters/claude/plugin-marketplace/**` — nothing outside that subtree.
- `git diff --stat` on the two originally-skeleton JSON files shows zero
  diff post-fix (byte-identical to what was already committed).

**Done-when (plan Phase 1)**: met — full tree materializes; re-run
byte-identical; `--check` exit 0 clean / exit 1 after touch; writes confined
to `adapters/claude/plugin-marketplace/`.
