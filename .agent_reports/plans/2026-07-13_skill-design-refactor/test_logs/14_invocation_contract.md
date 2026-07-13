# Invocation contract closure verification

| Check | Result |
|---|---|
| Bash syntax (`check.sh`, g7 root/Claude mirror scripts) | PASS, exit 0 |
| Live `check.sh skills adapters/claude/skills` | PASS, 13 classifications |
| g7 parent-invoked forbidden flip control | PASS — checker returned non-zero as expected |
| g7 user-only missing flag control | PASS — checker returned non-zero as expected |
| g7 user-only correct flag control | PASS — checker returned zero |
| Manifest + Claude native plugin projection | PASS — both `--check` commands exit 0 |
| Skill mirror + sync state | PASS — only `skills/.sync_state.json` differs; recorded sync-skills hash matches live source |
| `git diff --check` | PASS |
| Full drill runner | NOT RUN — Codex `loop-info drill` reports manual-only; static fixture/assert ran directly through verification-runner |
| Portable guards | FAIL outside scope — existing `dispatch-liveness.sh` state-transition/default-parity cases report 5 BAD; invocation checks unaffected |
| Adaptation boundary | FAIL outside scope — existing `INSTALL_LAYOUT.md` drift plus task 5's unprojected `tools/skill-conformance`/missing Claude tool mirror |
| Codex doctor | FAIL because adaptation boundary remains RED; manifest/native skill/plugin/agent/mode/subagent/hook checks are individually OK |

All commands ran through the Codex verification runner and captured their explicit exit status.
