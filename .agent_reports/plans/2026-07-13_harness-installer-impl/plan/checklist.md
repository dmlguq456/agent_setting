Safety commit: 24e229572920eea602410774464280447e75a3a8

Phase 0: manifest schema + layout constants (foundation)
  [x] Step 0.1: tools/install/paths.py (new) — agent_home()/runtime_home()/harness_state_dir()/resolve_source()/source_exists()
  [x] Step 0.2: tools/install/manifest.py — module docstring documents manifest JSON schema (no logic yet)

Phase 1: projector.py — INSTALL_LAYOUT symlink recipe (P0.1) [depends on Phase 0]
  [x] Step 1.1: tools/install/projector.py — per-runtime projection tables as data (claude/codex/opencode)
  [x] Step 1.2: tools/install/projector.py — plan(runtimes, scope="global") resolves via paths.py

Phase 2: manifest.py — hash-manifest / drift / reapply (P0.3) [depends on Phase 0]
  [x] Step 2.1: manifest.py — helpers (_sha256, _manifest_path/_pristine_path/_backup_path, _safe_relpath, _load/_write_manifest)
  [x] Step 2.2: manifest.py — record(runtime, files, scope, version)
  [x] Step 2.3: manifest.py — check_drift(runtimes, scope)
  [x] Step 2.4: manifest.py — reapply(runtimes, scope, sources=None) via git merge-file

Phase 3: drivers/{claude,codex,opencode}.py — install()/status()/checks() (P0.4) [depends on Phase 1]
  [ ] Step 3.1: drivers/claude.py — install/status/checks (delegates to install-windows.sh on Windows)
  [ ] Step 3.2: drivers/codex.py — install/status/checks (symlinks + optional --generate)
  [ ] Step 3.3: drivers/opencode.py — install/status/checks (opencode.json non-destructive merge)

Phase 4: verifier.py real check lists (P0.2) [depends on Phase 3]
  [ ] Step 4.1: verifier.py / checks_common.py — shared check helpers (check_symlink, check_cmd, check_file_exists)
  [ ] Step 4.2: drivers/claude.py checks() — symlink existence + build-manifest --check + compile smoke + bootstrap smoke (CLI-gated)
  [ ] Step 4.3: drivers/codex.py checks() — symlink existence + sync-native --check x4 + preflight smoke + bootstrap smoke (CLI-gated)
  [ ] Step 4.4: drivers/opencode.py checks() — symlink existence + sync-native --check x3 + preflight smoke + drift-watch sentinel + bootstrap smoke (CLI-gated)

Phase 5: installer.py wiring — cmd_* real behavior (P0 integration) [depends on 1,2,3]
  [ ] Step 5.1: installer.py cmd_install — driver.install() real call, SKIP/BLOCKED surfacing
  [ ] Step 5.2: installer.py cmd_status — driver.status() real call
  [ ] Step 5.3: installer.py cmd_update — remove reapply-gated drift computation; always compute drift; --reapply path
  [ ] Step 5.4: installer.py cmd_uninstall — manifest-scoped removal

Phase 6: mem import + ~/.local/bin launcher symlinks (P0.5) [independent, parallel with 1-4]
  [ ] Step 6.1: bootstrap.py (new) or cmd_install hook — mem import when DB absent
  [ ] Step 6.2: bootstrap.py — ~/.local/bin/{harness,fleet} launcher symlinks + PATH-collision guard

Phase 7: P1 — plugin channel wrapping (BOUNDARY — Codex in-cycle, Claude deferred)
  [ ] Step 7.1: drivers/codex.py — plugin=True wraps `codex plugin marketplace add` + `codex plugin add` (CLI-gated); drivers/claude.py plugin=True emits deferred SKIP
