# Execution Checklist — dispatch-profiles

Safety commit: 513474b
Plan: plan/plan.md · qa_level: standard

## Phase 0 — profiles/ scaffolding
- [x] 0.1 `profiles/README.md` (catalog + DP-3 exception note + L0/L1/L2 summary)
- [x] 0.2 `profiles/templates/bootstrap-claude.md` (L0 stub, no L1)
- [x] 0.3 `profiles/templates/bootstrap-codex.md` (L0 stub, no L1)
- [x] 0.4 `profiles/lab-runner.yaml` (spec §3 example)
- [x] 0.5 `profiles/fragments/lab-runner.md` (L2 example)

## Phase 1 — build-home.py
- [x] 1.1 NEW `tools/profile/build-home.py` (marker-walk AGENT_HOME, YAML validate, symlink farm, --check, exit 0/1/2)
- [x] 1.2 MIRROR `adapters/claude/tools/profile/build-home.py` (byte-identical, +x)

## Phase 2 — Claude dispatch wrapper
- [x] 2.1 NEW `adapters/claude/bin/dispatch-headless.py` (--profile, CLAUDE_CONFIG_DIR attach, gate exit 3, pipe+=profile=, +x)

## Phase 3 — Codex dispatch wrapper --profile
- [x] 3.1 EDIT `adapters/codex/bin/dispatch-headless.py` (--profile, CODEX_HOME attach, build-home --check gate after check_runtime_projection, pipe+=profile=; preserve all L599-630 literals)

## Phase 4 — liveness
- [x] 4.1 EDIT `utilities/dispatch-liveness.sh` (parse profile= → homes/<slug>.<name>/projects/<enc>)
- [x] 4.2 MIRROR `adapters/claude/utilities/dispatch-liveness.sh`

## Phase 5 — fleet
- [x] 5.1 EDIT `tools/fleet/model.py` (DispatchJob.profile)
- [x] 5.2 EDIT `tools/fleet/collectors/dispatch.py` (_parse_pipe→4-tuple all 3 returns, mode/profile backfill)
- [x] 5.3 EDIT `tools/fleet/collectors/dispatch.py` (_job_liveness profile-aware, spec §7 scan root)
- [x] 5.4 EDIT `tools/fleet/render.py` (_mq_tag profile segment)
- [x] 5.5 MIRROR `adapters/claude/tools/fleet/{model.py,collectors/dispatch.py,render.py}`

## Phase 6 — codex harvest cleanup
- [x] 6.1 EDIT `adapters/codex/bin/dispatch-harvest.py` (--keep-home, rmtree home on --mark-done; preserve flock/registry_lock literals)

## Completion gates (all pass before commit)
- [x] `bash tools/check-adaptation-boundary.sh`
- [x] `bash adapters/claude/tools/check-adaptation-boundary.sh`
- [x] `bash hooks/portable-guards.test.sh`
- [x] `bash adapters/claude/hooks/portable-guards.test.sh`
- [x] `python3 tools/build-manifest.py --check`
- [x] build-home smoke (see plan Verification §6)
