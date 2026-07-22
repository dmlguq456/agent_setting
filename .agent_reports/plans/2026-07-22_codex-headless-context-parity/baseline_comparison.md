---
status: active
created: 2026-07-22
starting_commit: 8db730a48ca82ec23a9cd1a39fb65dd507e1be5a
---

# Registered-headless handoff baseline

## Scope and evidence rule

This baseline compares local harness behavior, not vendor-runtime behavior. The
evidence is therefore the checked-in wrappers, exact-attempt fixtures, and local
deterministic tests. No official runtime-documentation claim is needed for the
proposed harness changes. If implementation later depends on a new claim about
`codex exec --json` or `claude -p`, that claim must be separately verified from
current official documentation and kept distinct from this local comparison.

The relevant project-analysis directory was inspected first. Its current files
cover the harness installer and Skill audits, not registered-headless handoff,
so no reusable module map existed for this task.

## Comparable information classes

| Information class | Parent may receive | Must remain isolated |
|---|---|---|
| Worker transcript | Exact attempt log path and typed state | Tool output, intermediate agent messages, reasoning, and arbitrary transcript text |
| Launch receipt | Attempt/route identity, PID/lifecycle, log path, safe terminal-envelope fields when already terminal | Attempt-log body |
| Wait/liveness | `ALIVE`, `COMPLETED`, `EXITED`, `SUSPECT`, or `DEAD`; exact attempt identity; typed verdict/reason | Transcript excerpts and artifact body |
| Harvest | Registry metadata plus validated three-line handoff envelope and artifact readability | Raw JSONL/plain-text log body |
| Terminal handoff | `artifact`, `verdict`, and `blocker` from the final exact envelope | Earlier agent messages and command output |
| Artifact reading | A validated path under the canonical artifact root; the next stage reads the file directly | Artifact body copied into conductor output |

## Measured Claude sibling baseline

The local Claude wrapper redirects `claude -p` stdout/stderr to the exact attempt
log (`adapters/claude/bin/dispatch-headless.py:410-429`) and emits a metadata-only
receipt (`:1129-1189`). A deterministic fake-CLI fixture was run in
`foreground-scoped` mode for all three worker verdicts.

| Fixture | Wrapper exit | `worker_exit` | `worker_failure` | Current row | Raw marker in receipt | Handoff in receipt | Raw marker and handoff in log |
|---|---:|---:|---|---|---|---|---|
| `PASS` | 0 | 0 | `-` | `open` | no | no | yes |
| `FAIL` | 0 | 0 | `-` | `open` | no | no | yes |
| `BLOCKED` | 0 | 0 | `-` | `open` | no | no | yes |

This establishes the useful Claude baseline: worker content is a log-only data
plane, while the parent sees a receipt. It also shows that byte-for-byte parity
with Claude is not the target: the Claude receipt does not interpret textual
`FAIL`/`BLOCKED` handoffs when the CLI exits zero. Codex should preserve the
isolation property while using its structured exact-attempt JSONL to provide a
safer typed control plane.

The checked-in Claude deterministic suites produced:

- `python3 adapters/claude/bin/dispatch-headless.sd45.test.py`: 14 tests, PASS.
- `bash adapters/claude/bin/dispatch-headless.sd15.test.sh`: expected fixture
  failure in this per-call PID namespace because detached launch is rejected as
  `nested-sandbox-lifetime`.
- `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 bash adapters/claude/bin/dispatch-headless.sd15.test.sh`:
  PASS. The explicit override is fixture-only and confirms the intended SD-15
  cases without weakening the production namespace guard.

## Measured current Codex behavior

`utilities/codex_dispatch_terminal.py:16-115` already parses an exact final
three-line agent message before `turn.completed`. Handcrafted exact-attempt JSONL
fixtures containing a raw command-output sentinel were run through the parser,
Codex liveness, shared wait, and Codex harvest.

| Fixture | Parser result | Codex liveness | Shared wait has typed verdict | Harvest has handoff | Raw sentinel in liveness/wait/harvest |
|---|---|---|---|---|---|
| `PASS` | valid `PASS` | generic `EXITED` | no | no | no / no / no |
| `FAIL` | valid `FAIL` | typed `EXITED ... dead-worker-fail` | no | no | no / no / no |
| `BLOCKED` | valid `BLOCKED` | typed `EXITED ... dead-worker-blocked` | no | no | no / no / no |

All three liveness and wait cases returned exit 3, and harvest returned exit 0.
The raw transcript is already isolated. The genuine gaps are information loss
and inconsistent use of the existing safe parser:

1. A valid `PASS` terminal handoff is ignored by Codex liveness and becomes a
   generic dead-PID `EXITED` result (`adapters/codex/bin/dispatch-liveness.py:324-369`).
2. `utilities/dispatch-wait.sh` calls the shared shell liveness surface, which
   does not parse the exact Codex terminal envelope; all three verdicts are
   reduced to generic terminal/death output.
3. Codex harvest is registry-only and emits no terminal handoff
   (`adapters/codex/bin/dispatch-harvest.py:39-55,118-200`), so a parent must
   inspect the raw JSONL to recover `artifact` and `blocker`.
4. The parser returns only valid-or-`None`; it cannot distinguish no terminal
   event from `turn.completed` plus a malformed/missing envelope, and it does
   not validate a non-`-` artifact path against the canonical artifact root.
5. Existing tests cover parser verdict classification and blocked sandbox
   closure, but do not prove end-to-end parent-output non-leakage across launch,
   wait/liveness, and harvest.

## Existing contracts that are already correct

- Both wrappers redirect child stdout/stderr to attempt logs and emit receipts.
- Codex foreground launch parses `turn.completed` and closes exact `FAIL` or
  `BLOCKED` attempts (`adapters/codex/bin/dispatch-headless.py:1431-1455`).
- `PASS` does not close a routed row; the hash-bound completion marker remains
  the success authority.
- Shared wait retains exit 0/2/3 semantics and bounded same-turn polling.
- Registry rows, exact attempt IDs, Fleet inputs, fallback ordinals, liveness
  PID/heartbeat evidence, raw debugging logs, and failure typing already exist.

These are preservation constraints, not redesign targets.

## Initial design choice

Keep the attempt log as the private/raw data plane and introduce one normalized,
exact-attempt terminal-inspection result as the parent control plane. Reuse that
result in the Codex launch receipt, both liveness surfaces, and Codex harvest.

- A normal success path exposes only typed envelope fields and an artifact path;
  it never emits a transcript excerpt or artifact body.
- Failure diagnostics remain off by default. An explicit failure-only option may
  emit one clearly labeled, newline/control-escaped excerpt from a structured
  failed command/error event, capped at 512 UTF-8 bytes. It must never select an
  agent message and must never emit an excerpt for `PASS`.
- A non-`-` artifact path is resolved and checked for containment beneath the
  row's canonical `artifact_root` before it is advertised as readable. Whether
  `artifact: -` is allowed remains the existing worker/completion-gate decision;
  the parser must not invent a new materiality policy.
- A parsed `PASS` is an observation used for `COMPLETED/harvest required`; it is
  not a completion marker and cannot close or advance a routed node.

## Test evidence captured on 2026-07-22

- Codex SD-45: 16 tests PASS.
- Codex SD-15: PASS.
- `utilities/codex_dispatch_terminal.test.py`: 4 tests PASS.
- `utilities/dispatch_harvest.test.py`: 3 tests PASS.
- `utilities/dispatch-wait.test.sh`: PASS.
- `utilities/dispatch-liveness.test.sh`: PASS.

The worktree was clean at the assigned starting commit before artifact creation.
The required spec content was read, but `preflight.sh read ... codex-headless`
could not write its marker because the dispatched sandbox mounted
`/home/Uihyeop/agent_setting/.spec-grounding` read-only. This planning stage did
not edit spec or source. The execute owner must rerun the governing read/write
guards in its own approved write scope before source edits.

Artifact schema/required-marker validation and `git diff --check` passed, and
the worktree remained clean. A heartbeat attempted after artifact publication
with `phase=test` was rejected as `progress-phase-regression` (`artifact->test`);
the same validation evidence was then recorded successfully at the current
`phase=artifact`, `kind=test` as sequence 7. This sequencing warning changed no
artifact, registry, or source state.
