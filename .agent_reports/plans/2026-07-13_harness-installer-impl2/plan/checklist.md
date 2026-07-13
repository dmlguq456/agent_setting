# harness-installer — Cycle 2 Checklist

> plan: `plan.md` · INST-OPEN-1 evidence: `../_internal/hooks_inventory.md`
> Each item's completion criterion is the "Done when" of its Phase in plan.md.

## Phase 1 — `adapters/claude/bin/sync-native-plugin.py` (P0)

- [x] 1.1 Constants + `plugin_json()` / `marketplace_json()` deterministic literals; `HOOK_ADOPT = [git-state-guard.sh, artifact-guard.sh]`. marketplace.json schema verified vs skeleton + Claude docs.
- [x] 1.2 `hooks_json()` literal — 2 hooks on PreToolUse, `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` paths; hooks.json shape verified vs live Claude docs.
- [x] 1.3 `sync()` — plugin.json/marketplace.json write + copytree skills(28)/agents(9) + copy2 hooks(2) + hooks.json; rmtree-then-copy (erase hand-edits); README.md preserved.
- [x] 1.4 `check()` + `check_file()` — byte-equal plugin.json/marketplace.json/hooks.json + per-file skills/agents/hooks vs SoT + excess-file detection; exit 1 on stale.
- [x] 1.5 `main()` — `--check` vs `sync()`; `raise SystemExit(main())`.
- [x] **Done**: sync materializes full plugin tree; re-run byte-identical; `--check` exit 0 clean / exit 1 after touch; writes confined to `adapters/claude/plugin-marketplace/`.

## Phase 2 — `drivers/claude.py` `install --plugin` wrapping (P0)

- [x] 2.1 `_plugin_action(dry_run)` mirror of codex — consts (`_MARKETPLACE_SOURCE_RELPATH=adapters/claude/plugin-marketplace`, `_PLUGIN_SPEC=agent-harness-claude@agent-harness`); `claude plugin marketplace add` + `claude plugin install` (CLI verbs/flags verified live); dry-run / CLI-absent SKIP / timeout / blocked-on-nonzero / registered.
- [x] 2.2 Wire into `install()` — replace SKIP-only block (L41-49); symlink + copy_once projection **still runs** when `plugin=True` (INST-D-5); blocked aggregation covers new action.
- [x] **Done**: `--plugin --dry-run` prints both CLI commands + full projection; CLI-absent real run emits SKIP; symlink projection present in both.

## Phase 3 — `drivers/claude.py` `checks()` + verifier (P0)

- [x] 3.1 `claude.sync-native-plugin` = `check_cmd([... sync-native-plugin.py --check])`.
- [x] 3.2 `claude.plugin-marketplace-source` = `check_file_exists(marketplace.json)`.
- [x] 3.3 CLI-gated registration verify — read-only (`claude plugin ... list`), SKIP when CLI absent, mktemp `CLAUDE_CONFIG_DIR` in tests; verb verified live.
- [x] **Done**: `harness verify claude --json` returns the 3 new checks; read-only; exit 0 clean.

## Phase 4 — `INSTALL_LAYOUT.md` reduction (INST-OPEN-3, P1)

- [x] 4.1 Projection sections — keep copy-once rationale / Windows specifics / Codex-agents-not-plugin-carriable / OpenCode merge+INST-OPEN-4 caveat; replace `ln -sfn` recipe lists with `harness install` reference + contract mapping table.
- [x] 4.2 Migration Order (239-514) — replace manual battery with `harness verify [runtime]` reference; keep exit-code semantics + BLOCKED-on-active-process rule as prose; keep fleet CLI section.
- [x] 4.3 Header note "수동 레시피·검증 → harness install/verify 로 대체됨"; flag editorial polish for code-report.
- [x] **Done**: no runnable `ln -sfn` recipe list / no manual Migration Order battery; all contract facts retained + pointing at harness install/verify.

## Phase 5 — code-test (⚠️ isolation contract — MANDATORY)

- [x] 5.1 All temp-HOME scenarios = single self-contained script under `_internal/test_scripts/*.sh`, one Bash call, env set at top; **no export across Bash boundaries**. (`01_generator_plugin_content.sh`, `02_driver_plugin_wiring_and_verify.sh`, `03_install_layout_and_regression.sh` — each its own single `sh` process / single Bash tool invocation.)
- [x] 5.2 installer/generator commands take explicit mktemp target roots; **no bare `$HOME`**; generator write set confined to marketplace subtree (or confined temp checkout). (script 01 §5 confinement assertion — `git status --porcelain` outside `adapters/claude/plugin-marketplace/`+generator script unchanged.)
- [x] 5.3 Determinism trap in each script: capture sha256 of real `~/.claude/settings.json`, `~/.codex/config.toml`, `~/.config/opencode/opencode.json`, `~/.claude/plugins` before temp-HOME switch; EXIT trap re-asserts byte-unchanged. (all 3 scripts, held on every run.)
- [x] 5.4 Real `claude plugin` CLI tests use mktemp `CLAUDE_CONFIG_DIR` only; gate behind CLI presence (SKIP not fail); never touch real `~/.claude/plugins`. (script 02 §6 — `CLAUDE_CONFIG_DIR` set at script top, before any CLI call including the one nested inside `checks()`; local `claude` CLI present so the integration path ran live, cross-checked `installPath` is not under real `~/.claude/plugins`.)
- [x] 5.5 Graduated levels: syntax (py_compile) → import → smoke (`--check`, `--plugin --dry-run`) → functional (sync→check clean→touch→check fail→regen; verify checks; dry-run commands; CLI-absent SKIP) → (CLI-gated) integration under mktemp CLAUDE_CONFIG_DIR. (script 01: syntax/import/smoke/functional for Phase 1; script 02: syntax/import/smoke/CLI-absent-SKIP/functional/CLI-gated-integration for Phase 2+3; script 03: Phase 4 doc-contract + regression subset.)
- [x] **Done**: all levels pass (53/53 across the 3 scripts); determinism trap held on every run; no write outside mktemp/marketplace subtree (`git status --porcelain` identical to the cycle's expected baseline diff before/after all runs).

> code-execute (this stage) already ran the Phase 1-3 functional/integration
> checks above (incl. CLI-gated mktemp `CLAUDE_CONFIG_DIR` registration) as
> ad-hoc single-self-contained scripts per dev_logs/step_01–03 — Phase 5's
> remaining scope for code-test is authoring these as durable
> `_internal/test_scripts/*.sh` artifacts, not re-discovering the isolation
> contract from scratch.

## Cross-cutting (code-report records; NOT edited here)

- [x] INST-OPEN-1 → 확정 (adopt 2 / defer 3 / exclude rest) — recorded in final_report.md §6; prd edit by main orchestrator autopilot-spec update.
- [x] INST-OPEN-3 → closeable after Phase 4 — recorded in final_report.md §6; prd edit by main orchestrator.
- [x] INST-OPEN-4 → stays OPEN (out of scope, untouched) — recorded in final_report.md §6/§8.
- [x] `INSTALL_LAYOUT.md` (user-read) → editorial-team polish pass done in code-report (250 lines final).
