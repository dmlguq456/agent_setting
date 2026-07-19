# metrics — 2026-07-16_dispatch-defaults-config

Route `rt-20f4481665281810`, dispatch contract v3, launch_authority=conductor.
This cycle dogfoods the cross-harness defaults it implements (SD-66), so each
harness choice is recorded with its reason.

## Stage dispatch ledger

| stage | harness | model role | reason for harness | outcome |
|---|---|---|---|---|
| plan | codex | deep maker | SD-22 stage affinity: GPT-family deep-maker affinity; `usage-check.sh` reported `codex ok` | PASS (`plan.md`) |
| execute | claude | fast implementer | repo-idiom-dense multi-file edit; maker family = claude; `claude ok` | PASS (`dev_logs/implementation.md`), commits `efeab72e`, `7697c3b6` |
| test | codex | deep reviewer | diverse checker — deliberately a different family from the maker (claude) so the verifier is independent; `codex ok` | **FAIL** (`test_logs/verification.md`) |
| execute (retry r1) | claude | fast implementer | same as execute | **BLOCKED at launch** — route guard `route-source-commit-mismatch` |
| report | — | — | not dispatched: `code-test` gate not met | not run |

The diverse-checker placement paid for itself: the codex verifier caught an
adapter-projection regression that the claude implementer's own dev log claimed
was covered, plus a fixture-isolation gap in the implementer's own tests.

## Usage / eligibility probes (all conductor-level, from the task worktree)

| time (UTC) | probe | result |
|---|---|---|
| 12:38:01 | `nested-headless --child-harness codex` | `status=supported`, `probe_source=direct-auth+headless-check` |
| 12:48:56 | `nested-headless --child-harness claude` | `status=supported`, `probe_source=direct-command-check` |
| 13:50:11 | `nested-headless --child-harness codex` | `status=supported`, `probe_source=direct-auth+headless-check` |
| 12:36 / 13:50 | `usage-check.sh` | `claude ok`, `codex ok`, `bias auto` — no harness avoided for limits |

## Contract-mechanics findings measured this cycle

1. **`dispatch-node.py` does not forward route evidence** (contradicts the assignment's
   premise). A plain `--action start` failed with
   `DispatchContractError: nested-eligibility-evidence-missing (detail=eligibility_source)`.
   The conductor had to supplement `--parent-harness/--parent-transport/--parent-sandbox/
   --launch-authority/--nested-eligibility/--eligibility-source` by hand — i.e. the exact
   SD-48 situation item (C) documents. Every dispatch in this cycle used that supplementation.
   The v15 "record path auto-passes evidence" assumption is FALSE at this HEAD.
2. **`execute` is not retryable in place** — see `pipeline_summary.md` §Blocker.
3. **The nested-headless probe returns `unsupported` from inside a codex sandbox.** The
   test stage's own probe returned `failure_class=auth-unavailable, status=unsupported`
   while three conductor-level probes on the same worktree returned `supported`. The
   sandbox (`codex exec --sandbox workspace-write`) cannot see host codex auth state.
   This is an environment artifact, not a regression, and not the SD-66 change's doing.
