# test log — code-test (SD-68)

route: rt-d57cbb149952fd3d · tree under test: HEAD `9130c437` (base `ecd3acd8`)
stage harness: codex (deep reviewer) — **artifact persist BLOCKED** by the codex
spec-read/Read-tool marker gate; verification itself completed. Per the route
binding ("아티팩트 영속화 실패 시 로그에서 salvage해 test_logs/에 영속화") the
conductor salvaged the codex verdict AND independently re-ran the full suite +
baseline classification + a live acceptance smoke in the task worktree. Results
below are the conductor's authoritative re-verification (they supersede the
partial codex stdout salvage, and agree with it).

## Gate verdict: PASS

All spec acceptance ①~⑤ pass; zero new regressions introduced by the SD-68 diff.
The only failing suites (sd45 ×3) fail **identically at baseline `ecd3acd8`** and
are therefore pre-existing / environment-dependent, not SD-68 regressions.

## Suite results (task worktree only)

| Suite | Result |
|---|---|
| `utilities/capability_route.test.py` | **18 passed** (OK) — acceptance ①②③ + old-route backcompat + forged-vocab reject + absent-config + corrupt fail-loud |
| `utilities/dispatch_node.test.py` | **20 passed** (OK) — acceptance ④⑤ |
| `utilities/dispatch_contract.test.py` | **10 passed** (OK) — regression |
| `utilities/worker_route_guard.test.py` | **13 passed** (OK) — regression |
| `adapters/claude/bin/dispatch-headless.sd45.test.py` | 8 pass / **1 fail** (`test_route_consumer_and_missing_evidence_refusal`, exit 73) — **pre-existing** |
| `adapters/codex/bin/dispatch-headless.sd45.test.py` | 8 pass / **1 fail** (same test) — **pre-existing** |
| `adapters/opencode/bin/dispatch-headless.sd45.test.py` | 8 pass / **1 fail** (same test) — **pre-existing** |
| `adapters/claude/bin/dispatch-headless.sd15.test.sh` | PASS |
| `adapters/codex/bin/dispatch-headless.sd15.test.sh` | PASS |
| `adapters/opencode/bin/dispatch-headless.sd15.test.sh` | PASS |
| `utilities/dispatch-route.test.sh` | PASS — selector 1단계 의미 불변 회귀 |

### Baseline classification of the sd45 failure (regression-0 proof)

Ran all three sd45 suites in a detached worktree at `ecd3acd8` (pre-SD-68):
each fails with the identical `test_route_consumer_and_missing_evidence_refusal`
(exit 73, empty stderr — a wrapper-subprocess/env fixture issue, not touched by
this diff). Since baseline == SD-68 tree for these three, the SD-68 change adds
**no new regression**. (Note: the execute dev log under-reported this as
"claude only"; the codex test worker and this re-run both confirm all three fail
identically, and all three are pre-existing. The execute log's separate sd15
"4 governor-denied failures" were environment-specific model-worker-governor caps
and PASS under the lighter concurrent load at test time.)

## Live acceptance smoke (direct compile_route / verify_route, task worktree)

- **① depth-2 vocab stamp**: compiled standard route depth-2 nodes =
  `plan=unspecified, execute=codex, test=diverse, report=claude` — all within the
  valid vocabulary `{claude,codex,opencode,diverse,unspecified}`. These match the
  SD-66 §13.8.1 initial config snapshot. `dispatch_defaults_digest` present
  (`sha256:b3e8dd08…`) and **distinct from `registry_digest`** (topology pin
  uncontaminated — §13.9.2 separation intent).
- **② seal proven**: changing a config value (`report: claude → codex`) changes
  `route_hash` (and the report node's stamped affinity `claude → codex`). A
  **comment-only** config edit leaves `route_hash` UNCHANGED — validating the
  plan's normalized-parse digest decision (raw-byte digest would have churned).
- **③ no post-compile reload**: a route stamped under config A `verify_route`s
  successfully even after the env points to config B — verify checks only the
  hash seal, never reloads the config.
- **absent config**: `dispatch_defaults_digest = None` and every depth-2 node
  stamped `unspecified`.
- **④ / ⑤** covered by `dispatch_node.test.py` (argv carries `--harness-affinity`
  when the node has it, absent otherwise; explicit `--adapter ≠ affinity` launches
  without any gate/comparison — soft).

## Housekeeping

- Baseline detached worktree (`/tmp/sd68-base`) removed; the codex worker's
  `.sd68-baseline/` copy inside the task worktree removed; `adapters/**/__pycache__`
  cleaned. `git status` clean (only the two SD-68 commits over `ecd3acd8`).
- No source commits made by the test stage.
