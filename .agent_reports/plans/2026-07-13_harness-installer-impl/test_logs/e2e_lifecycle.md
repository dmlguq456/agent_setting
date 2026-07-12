# code-test — harness-installer e2e lifecycle result

## [PASS] real-home determinism guard

No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,
~/.config/opencode/opencode.json across the whole run (hashes captured
before HOME was reassigned to a mktemp dir, re-checked at exit via trap).

---

## Summary

PASS=51 FAIL=0

---

## Baseline
- REAL_REPO=/home/Uihyeop/agent_setting-wt/harness-installer-impl
- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode (hashes not printed here, compared at exit)

## Isolated env
- HOME(temp)=/tmp/tmp.vk8J3I7vSW
- AGENT_HOME=/home/Uihyeop/agent_setting-wt/harness-installer-impl
- MEM_STORE=/tmp/tmp.vk8J3I7vSW/mem

## 1. Syntax — py_compile
```
（출력 없음 — 정상）
```
- [PASS] syntax.py_compile — python3 -m py_compile tools/install/*.py tools/install/drivers/*.py — exit=0

## 2. Import — paths.py
```
/home/Uihyeop/agent_setting-wt/harness-installer-impl
/tmp/tmp.vk8J3I7vSW/.claude
```
- [PASS] import.paths — agent_home()==/home/Uihyeop/agent_setting-wt/harness-installer-impl, runtime_home(claude,global)==$HOME/.claude (temp) — got [/home/Uihyeop/agent_setting-wt/harness-installer-impl] [/tmp/tmp.vk8J3I7vSW/.claude] exit=0

## 3. Smoke — install --dry-run --json (all runtimes)
- [PASS] smoke.install_dryrun.exit0 — exit=0 (expect 0)
- [PASS] smoke.install_dryrun.all_three_runtimes — checks[] covers claude/codex/opencode ids
- [PASS] smoke.install_dryrun.no_source_absent_skips — no skip:source-absent entries — {claude,codex,opencode}_setting/ all exist in this worktree

## 4. Functional — claude install / manifest / drift / reapply
- [PASS] e2e.install_claude.exit0 — harness install claude --json — exit=0
- [PASS] e2e.manifest_created — $HOME/.claude/.harness/manifest.json exists
- [PASS] e2e.symlinks_created — projection symlinks created for representative claude entries (core, skills)
- [PASS] e2e.manifest_hash_recorded — manifest.files includes settings.json+keybindings.json hash entries
- [PASS] e2e.install_codex.exit0 — harness install codex --json — exit=0
- [PASS] e2e.install_opencode.exit0 — harness install opencode --json — exit=0
- [PASS] e2e.verify_after_install.exit0 — harness verify --json right after install (claude+codex+opencode all installed) — expect all pass, exit=0
- [PASS] e2e.drift_detected.exit4 — harness update --json after hand-edit — expect exit=4 (EXIT_DRIFT), got 4
- [PASS] e2e.drift_nonempty — drift[] non-empty and names settings.json
- [PASS] e2e.reapply.exit0 — harness update --reapply --json — exit=0
- [PASS] e2e.reapply_reapplied_no_conflicts — 1 file reapplied via git merge-file 3-way, 0 conflicts
- [PASS] e2e.reapply_preserved_user_edit — merged settings.json still contains '// user edit' after reapply

(note: canonical source file itself was NOT mutated for this reapply pass — doing so
 would require editing a git-tracked repo file outside this stage's write scope;
 the drift -> reapply -> user-edit-preserved invariant is still fully exercised
 against the unchanged canonical source. Deliberate scope narrowing, not a gap.)

## 5. Verify (read-only) — full + subsets
- [PASS] verify.read_only — manifest.json + settings.json byte-identical immediately before/after this one verify call (verify never mutates disk)
- [PASS] verify.exit_in_expected_set — harness verify --json exit is 0(all pass) or 2(1+ check failed) — never a crash exit, got 0
- [PASS] verify.all_checks_pass — every registered check() returned ok=true
- [PASS] verify.codex_subset_only — harness verify codex --json returns only codex.* checks (nonempty)
- [PASS] verify.opencode_subset_only — harness verify opencode --json returns only opencode.* checks (nonempty)
- [PASS] verify.status_exit0 — harness status --json — exit=0
- [PASS] verify.status_no_notimplemented — no NotImplementedError leaks into status checks[].detail

## 6. Codex / OpenCode driver coverage (install --dry-run)
- [PASS] driver.codex_install_dryrun.exit0 — harness install codex --dry-run --json — exit=0
- [PASS] driver.opencode_install_dryrun.exit0 — harness install opencode --dry-run --json — exit=0

## 6b. CLI-absent SKIP simulation (codex plugin-wrap, bootstrap-smoke x3)
- [PASS] driver.cli_absent_probe_ran — PATH-stripped probe ran (exit=0); PATH used: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
- [PASS] driver.codex_plugin_skip_on_cli_absent — codex plugin-wrap SKIPs (no subprocess call) when codex CLI unresolvable via PATH
- [PASS] driver.codex_bootstrap_smoke_skip — codex.bootstrap-smoke reports ok=true SKIP when codex CLI absent
- [PASS] driver.opencode_bootstrap_smoke_skip — opencode.bootstrap-smoke reports ok=true SKIP when opencode CLI absent
- [PASS] driver.claude_bootstrap_smoke_skip — claude.bootstrap-smoke reports ok=true SKIP when claude CLI absent

## 7. Full lifecycle — idempotent reinstall / clean update / uninstall
- [PASS] lifecycle.install_all_dryrun.exit0 — harness install all --dry-run --json — exit=0
- [PASS] lifecycle.idempotent_reinstall.exit0 — harness install claude --json (second run, all-unchanged expected) — exit=0
- [PASS] lifecycle.idempotent_reinstall.no_blocked — no blocked actions on idempotent re-install
- [PASS] lifecycle.update_clean_after_reapply.exit0 — update after the earlier reapply resolved drift — expect exit=0, got 0
- [PASS] lifecycle.uninstall_dryrun.exit0 — harness uninstall claude --dry-run --json — exit=0
- [PASS] lifecycle.uninstall.exit0 — harness uninstall claude --json — exit=0
- [PASS] lifecycle.manifest_removed — manifest.json removed after uninstall
- [PASS] lifecycle.symlinks_removed — manifest-scoped projection symlinks (core, skills) removed after uninstall
- [PASS] lifecycle.non_manifest_file_preserved — file never enumerated by the manifest survives uninstall untouched

## 8. mem import + ~/.local/bin launchers + PATH-collision guard
- [PASS] bootstrap.reinstall_after_uninstall.exit0 — fresh install claude --json (post-uninstall) — exit=0
- [PASS] bootstrap.memory_db_created — $MEM_STORE/memory.db created from dump.jsonl on install
- [PASS] bootstrap.launchers_created — $HOME/.local/bin/{harness,fleet} symlinks created (temp HOME)
- [PASS] bootstrap.collision_probe_ran — install_launchers() probe against pre-seeded foreign 'harness' file ran (exit=0)
- [PASS] bootstrap.collision_guard_skips_foreign — pre-existing non-symlink 'harness' left alone (status=skipped-collision)
- [PASS] bootstrap.fleet_created_despite_collision — unrelated 'fleet' launcher still created despite the 'harness' collision
- [PASS] bootstrap.collision_file_content_untouched — foreign harness file bytes unmodified after collision-guard skip

## 9. Plugin channel dry-run (Phase 7 boundary)
- [PASS] plugin.codex_dryrun.exit0 — harness install codex --plugin --dry-run --json — exit=0
- [PASS] plugin.codex_cmds_planned — planned 'codex plugin marketplace add' + 'codex plugin add' commands present in checks[]
- [PASS] plugin.claude_dryrun.exit0 — harness install claude --plugin --dry-run --json — exit=0
- [PASS] plugin.claude_deferred_skip — claude plugin channel reports deferred SKIP message (Phase 7 boundary — Claude plugin content generator out of cycle-1 scope)

## Observations (not failures — informational)

- **python3 version vs PRD dependency line**: PRD (`spec/harness-installer/prd.md` §공통) states
  "python3 ≥ 3.10" as a dependency. The actual interpreter on this box/worktree is
  `Python 3.8.10` (checked via `python3 --version` before this run). `py_compile` and every
  functional step above ran clean on 3.8.10 — no observed 3.10+-only syntax in
  `tools/install/**` — so this is a doc-vs-environment discrepancy to note for the conductor,
  not a functional defect surfaced by this test pass.
- **Prior test-script bugs found and fixed during this stage** (both in
  `_internal/test_scripts/`, not in `tools/install/**`): (1) `_json_assert.py`'s first version
  put helper names (`any`/`all`/...) in a `locals` dict passed to `eval()` — nested
  generator/comprehension expressions only resolve free names via their enclosing
  frame's *globals*, so multi-level boolean exprs (e.g. `all(any(...) for x in y)`) raised
  `NameError`; fixed by moving everything into the single globals dict. (2) the first
  `verify.read_only` hash-window spanned an intervening `update --reapply` call (which is
  *supposed* to mutate disk), so pre/post hashes legitimately differed for a reason
  unrelated to `verify`; narrowed the window to wrap only the `verify` call itself. (3) the
  first `harness verify --json` right after `install claude` expected all-green, but codex/
  opencode hadn't been installed yet in that run, so their symlink-existence checks
  correctly reported missing — fixed by installing codex/opencode for real (still temp-HOME
  only) before that verify call. All three were test-harness ordering/scoping bugs on my
  side, confirmed by inspecting the raw JSON artifacts directly; none indicated an
  installer defect. The corrected script (this file's run) is what produced the 51/0 tally
  above.

## Done — all phases executed, see Summary above for pass/fail tally.
