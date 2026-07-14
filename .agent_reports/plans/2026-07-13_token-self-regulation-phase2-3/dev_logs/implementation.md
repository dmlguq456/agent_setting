# Token Self-Regulation Phase 2/3 — Implementation Log

## Verdict

`READY_FOR_CODE_TEST`

This is implementation evidence only. It is not independent QA, full verification, real experiment evidence, or an adoption decision.

## Decisions

1. Kept the Phase 1 directive strings in one canonical `directive_id -> text` map and preserved their exact inserted UTF-8 sequences (tight 154 bytes, critical 165 bytes; stdout transport newline excluded).
2. Kept transition state and accounting separate. The helper writes a transient content-free receipt; the UserPromptSubmit parent is the sole accounting authority after observing delivered stdout, timeout, nonzero status, and receipt validity.
3. Stored only fixed counters/IDs and sha256 session digest in `${XDG_STATE_HOME}/agent-harness/token-budget/accounting/`; no raw session id, prompt, response, transcript, directive body, tokenizer estimate, savings, billing, cost, or ROI field is persisted.
4. Kept `offline-forecast-v1` in `tools/fleet/token_experiment.py` plus an explicit isolated CLI. Production utility, lifecycle, preflight, and hooks.json contain no candidate import/activation/config path.
5. Recomputed `config_fingerprint` from every workload pairing field, used strict complete triplets and fixed exclusion priority, and froze bootstrap to 10,000 resamples / seed 20260713.
6. Mirrored complete `tools/fleet/` into the required Claude mirror, projected the isolated CLI only for Claude/Codex, and explicitly deferred OpenCode Phase 2 automation/Phase 3 CLI.

## Changed files

Portable/core:

- `core/CONVENTIONS.md`
- `core/ADAPTATION_INVENTORY.md`
- `tools/fleet/token_budget.py`
- `tools/fleet/token_accounting.py` (new)
- `tools/fleet/token_experiment.py` (new)
- `tools/fleet/tests/test_token_budget.py`
- `tools/fleet/tests/test_token_experiment.py` (new)
- `tools/fleet/tests/fixtures/token_experiment/manifest.json` (new)
- `tools/fleet/tests/fixtures/token_experiment/replay.json` (new)
- `tools/fleet/tests/fixtures/token_experiment/replay_expected.json` (new)
- `utilities/token-budget.py`
- `utilities/token-budget-experiment.py` (new)
- `hooks/portable-guards.test.sh`
- `tools/check-adaptation-boundary.sh`

Codex/OpenCode realization:

- `adapters/codex/hooks/userprompt-lifecycle.py`
- `adapters/codex/bin/preflight.sh`
- `adapters/codex/AGENTS.md`
- `adapters/codex/README.md`
- `adapters/codex/ADAPTATION.md`
- `adapters/codex/utilities/token-budget-experiment.py` (new symlink)
- `adapters/opencode/AGENTS.md`
- `adapters/opencode/README.md`
- `adapters/opencode/ADAPTATION.md`

Claude mirror/projection:

- `adapters/claude/tools/fleet/token_budget.py`
- `adapters/claude/tools/fleet/token_accounting.py` (new mirror)
- `adapters/claude/tools/fleet/token_experiment.py` (new mirror)
- `adapters/claude/tools/fleet/tests/test_token_budget.py`
- `adapters/claude/tools/fleet/tests/test_token_experiment.py` (new mirror)
- `adapters/claude/tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json}` (new mirrors)
- `adapters/claude/utilities/token-budget-experiment.py` (new symlink)

Implementation artifacts:

- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/checklist.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/dev_logs/implementation.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/dev_reviews/implementation_review.md`

`python3 tools/build-manifest.py` was run as required; its generated output was byte-identical, so `manifest.json` has no final diff.

## Guard/tool fallback record

- The native `apply_patch` tool was twice rejected because the Codex PreToolUse bridge could not infer the patch target, including a relative-path retry. After the explicit per-file `preflight.sh write ... codex-headless` gates, edits used the shell `apply_patch` executable. No redirect/`sed -i`/Python file-write fallback was used.
- After core-first source edits, adapter symlink/mirror mutation was correctly blocked until the changed core documents were re-read and marked with `preflight.sh read`; the marker was refreshed before continuing.
- Current Codex official manual was refreshed through the OpenAI docs helper (`/tmp/openai-docs-cache/codex-manual.md`), confirming concurrent matching hooks, UserPromptSubmit input/additionalContext, and rollout_budget under-development/off-by-default. Local `codex-cli 0.144.3` reports hooks/multi_agent stable and rollout_budget/runtime_metrics/token_budget disabled under development.
- Component PRD read marking succeeded in this worker. No unsupported Codex runtime tool contract blocked implementation. Thorough independent reviewers were not launched because this depth-2 worker cannot dispatch depth 3; inline review is explicitly labeled fallback.

## Focused implementation sanity

- `preflight.sh verification-runner --timeout 120 -- python3 -m unittest -v tools.fleet.tests.test_token_budget tools.fleet.tests.test_token_experiment` — exit 0, 24 tests.
- `preflight.sh verification-runner --timeout 60 -- sh -n tools/check-adaptation-boundary.sh` — exit 0.
- `preflight.sh verification-runner --timeout 60 -- sh -n hooks/portable-guards.test.sh` — exit 0.
- `preflight.sh verification-runner --timeout 60 -- python3 -c <AST parse>` over the Phase 2/3 modules, CLIs, lifecycle, and focused tests — exit 0.
- Mirror byte comparison for every non-`__pycache__` `tools/fleet/` file — `mirror_drift=none`.
- Explicit production-source scan currently returns no forbidden `offline-forecast-v1|token_experiment|production_dynamic_enabled` match.

Earlier focused runs (15 Phase 0–2 tests and 8 Phase 3 tests) also passed before the combined run. These are implementation sanity checks, not the code-test evidence set.
An intermediate combined run after adding declaration-derived config fingerprints exposed one exclusion-fixture precedence mismatch (`pairing_fingerprint_mismatch` correctly outranked a mutated rubric hash); the fixture was narrowed to a reviewer-id mismatch and the final 24-test combined run passed.

## Remaining code-test obligations

- Run the plan's AST, focused Phase 2/3, full Fleet discovery, portable guards, adaptation guard/boundary, manifest check, doctor, diff check, and explicit production-absence commands through the verification runner.
- Exercise installed-fixture lifecycle accounting for normal/transition/same-band/timeout/error and prove diagnostics never enter hook output.
- Reconfirm all store bounds/concurrency/fail-open cases, exclusion enums, n/strata, safety/required/hard regression, both quality LCBs, both observed-delta LCBs, deterministic bytes, verdict cap, adoption pending, and production false.
- Apply the thorough QA policy's selected independent reviewer pass in code-test if runtime depth/worker ownership permits; otherwise report inline fallback without claiming independence.
- Main orchestrator alone harvests/merges/pushes, refreshes installed runtime projection/trust, and cleans the worktree.
