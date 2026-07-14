# Final verification evidence

All commands ran through the Codex verification runner in the isolated
`release-installer-auto-update` worktree.

| Gate | Result |
|---|---|
| `tools/install/release-lifecycle.test.sh` | PASS — clone-free real archive, all-runtime packaged activation/doctor, checksum, traversal, symlink/hardlink/special-file rejection, pin, scheduler ownership/env, pointer repair, state/lock symlink rejection, profile and state rollback |
| `tools/install/runtime-activation.test.sh` | PASS |
| `tools/install/profile-activation.test.sh` | PASS |
| `tools/install/extension-lifecycle.test.sh` | PASS |
| `python3 tools/generate.py --check` | PASS |
| `tools/generated-projections.test.sh` | PASS |
| `tools/skill-conformance/check.sh` | PASS |
| `tools/check-adaptation-boundary.sh` | PASS |
| `adapters/codex/bin/preflight.sh doctor` | PASS |
| actual HEAD release build ×2 + SHA-256 + safe extraction | PASS — byte-identical archives; report roots excluded; required installer files present |

Additional checks: Python compile, POSIX shell syntax, README links, workflow
YAML/permissions/action SHA, deterministic release archive, and
`git diff --check` all passed.

Independent read-only security review: final HIGH/MEDIUM findings = 0. The
review's remaining LOW suggestions were also closed by hardlink/state-lock
fixtures, required release-file validation, typed state validation, and broader
release workflow gates.
