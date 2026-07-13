# code-test verdict — dispatch-routing-policy-v7 (SD-21~24)

Stage: depth-2 `code-test` (independent, cross-family) under `dispatch-routing-impl`.
Date: 2026-07-13. Source **not** modified; read-only verification only.

## Verdict

**PASS with findings.** Every required verification command ran through
`adapters/codex/bin/preflight.sh verification-runner`. All change-owned suites are green.
All red suites were root-caused to (a) this worker's own dispatch-env contamination or
(b) pre-existing failures on files this diff does not touch — none are regressions of
SD-21~24. Two implementation-quality findings and one test-adequacy gap are recorded below.

## Verification matrix (command → exit → log)

| # | Command (via verification-runner unless noted) | exit | result | log |
|---|---|---|---|---|
| 01 | `bash utilities/dispatch-route.test.sh` | 0 | PASS | 01 |
| 02 | `bash utilities/usage-check.test.sh` | 0 | PASS | 02 |
| 03 | `python3 -m unittest discover -s tools/fleet/tests` | 0 | PASS 162/162 | 03 |
| 04 | `… -s adapters/claude/tools/fleet/tests` (mirror) | 0 | PASS 162/162 | 04 |
| —  | Fleet mirror byte parity (changed files diff) | 0 | IDENTICAL | (inline) |
| 05 | `bash hooks/portable-guards.test.sh` (raw, in-dispatch) | 1 | PASS=319 FAIL=10 → all env/pre-existing | 05 |
| 05b| same, dispatch-env stripped | 1 | PASS=323 FAIL=6 → all pre-existing (unchanged files) | 05b |
| 06 | `bash tools/check-adaptation-boundary.sh` | 1 | 19 FAIL, all pre-existing Claude-mirror gaps | 06 |
| 07 | `adapters/codex/bin/sync-native-agents.py --check` | 0 | PASS | 07 |
| 08 | `adapters/codex/bin/sync-native-skills.py --check` | 0 | PASS | 08 |
| 09 | `adapters/codex/bin/sync-native-plugin.py --check` | 0 | PASS | 09 |
| 10 | `adapters/codex/bin/sync-native-modes.py --check` | 0 | PASS | 10 |
| 11 | `adapters/opencode/bin/sync-native-agents.py --check` | 0 | PASS | 11 |
| 12 | `adapters/opencode/bin/sync-native-skills.py --check` | 0 | PASS | 12 |
| 13 | `adapters/opencode/bin/sync-native-commands.py --check` | 0 | PASS | 13 |
| 14 | `git diff --check` | 0 | PASS (no whitespace errs) | 14 |
| 15 | `preflight.sh doctor` | 1 | fails only on adaptation-boundary (pre-existing) | 15 |
| 16 | `preflight.sh doctor --runtime` | 1 | runtime-projection:ok; fails only on adaptation-boundary | 16 |
| 17 | `preflight.sh runtime-projection --require-hook-trust` | 0 | PASS (bootstrap:ok, plugin:ok, all agent-links ok) | 17 |
| 18 | functional: model-map role probes | 0 | PASS | 18 |
| 19 | functional: selector role/affinity/override probes | 0 | PASS (except SD-22 finding) | 19 |
| 20 | functional: SD-23 limited failover + no-mutation | 0 | PASS | 20 |

## Failure root-cause classification (no SD-21~24 regressions)

### portable-guards: 10 → 6 after stripping this worker's env
- **4 register/harvest failures (codex+opencode) = env contamination, NOT a defect.**
  This worker runs as a depth-2 headless child, so `AGENT_DISPATCH_PARENT_SESSION_ID`
  (and siblings) are in its env and get inherited by the child dispatch wrappers the test
  launches. That injects a `parent_sid=…` segment into the jobs.log line, so the test's
  exact-line `grep` misses. Proof: re-running register under `env -i` produces the exact
  expected line (MATCH); re-running the whole suite with the dispatch vars unset drops
  FAIL 10→6 and removes exactly these 4. The harvest wrapper isn't even touched by the diff.
- **6 remaining, all on files this diff does NOT modify:**
  - 4× `dispatch-liveness.sh` ALIVE/SUSPECT — the `.sh` variant; the identical `.py`
    transition tests PASS. Pre-existing `.sh`/`.py` parity quirk in this sandbox
    (transcript-root/mtime resolution), unrelated to the change.
  - 2× `codex doctor --runtime` / `--runtime-strict` — both run with `AGENT_HOME=$ROOT`
    and fail because `doctor` bundles `adaptation-boundary:failed` (see below);
    `check=runtime-projection:ok` in both. Pre-existing.

### check-adaptation-boundary: 19 FAIL — all pre-existing Claude-mirror gaps
Every FAIL is a missing `adapters/claude/…` mirror path: `tools/install/*` (10),
`loops/drill/cases_growing/g_stage_dispatch/*` (5), `tools/memory/mem_cluster_j.test.sh`,
plus parents. The portable counterparts (`tools/install`, `loops/drill/.../g_stage_dispatch`,
`tools/memory/mem_cluster_j.test.sh`) exist; this diff never touches those paths
(`git status` clean for them). **The diff's OWN new boundary checks pass** — no FAIL
mentions `dispatch-route` or `model-map`; the new `dispatch-route.sh` utility projection
(codex/opencode symlink allowlist + PROJECTED/DEFERRED census) validates cleanly. Matches
the code-execute dev-log note verbatim.

### doctor / doctor --runtime
Both fail *only* on the pre-existing `adaptation-boundary:failed`. Notably
`doctor --runtime` now reports `check=runtime-projection:ok` and the strict
`runtime-projection --require-hook-trust` gate is fully green — i.e. the plan's
"runtime bootstrap discovery returned codex-debug-failed" concern no longer reproduces
under hook trust.

## Functional SD verification (evidence in logs 18–20)

- **SD-21 conductor=deep**: `model-map.sh orchestrator` → codex `gpt-5.6-sol`/high,
  claude `opus`/high. Fast tiers → `gpt-5.4-mini`/medium, `sonnet`/medium. ✓
- **SD-22 Sol pin + affinity**: deep maker → `gpt-5.6-sol`; selector `--stage
  plan|architecture` → adapter=codex, family=gpt, role=deep maker (affinity, not hard pin —
  explicit `--adapter` overrides it). ✓
- **Mapping honesty**: claude emits real `opus`/`sonnet`; opencode emits
  `status/family/exact_model_id=unknown` + reason, never fabricates. ✓
- **SD-23 explicit-cannot-silently-bypass**: explicit `--adapter claude` while claude is
  `limited(reset)` → traced `rejected.1=claude:usage-limited(...)` +
  `fallback.1=codex:known-limit-on-claude`, final adapter=codex. Eligibility is a hard gate
  that cannot be bypassed silently. ✓
- **SD-23 no mutation**: jobs.log sha256 unchanged before/after; unknown role/args → exit 64;
  missing `--stage` → exit 64. ✓
- **SD-24 env-marked child hiding**: procscan hides only `AGENT_DISPATCH_CHILD=1`; unreadable
  environ fails open. `test_codex_dispatch_child_marker_hides_only_marked_child` PASS; all
  three wrappers export the marker. ✓
- **SD-24 non-code stage regression guard**: `test_non_code_plans_path_never_derives_stage`
  PASS (a non-code `plans`-adjacent path returns fallback, no plan/test/spec stage);
  `test_code_worker_derives_stage_from_artifacts` PASS. ✓
- **quick preservation**: `codex/opencode dispatch wrapper accepts quick depth-1 / rejects
  quick depth-2` all PASS. ✓

## Findings (implementation-quality; not blockers)

### F1 (medium) — SD-22 checker family-diversity is not implemented in the selector
`utilities/dispatch-route.sh` accepts `--maker-family` and echoes it in `trace.2`, but the
selection logic never consumes it. For any checker/review stage (`affinity=diverse`) with no
explicit `--adapter`, it unconditionally falls to `claude`:
`[ "$affinity" = codex ] && choose=codex || choose=claude`.
- Repro: `dispatch-route.sh --stage code-review --maker-family claude` → `adapter=claude,
  family=claude` — the checker lands in the **same** family as the maker, contradicting the
  priority `… > maker/checker family diversity > …` and CONVENTIONS "reviewer는 가능한 경우
  maker와 다른 family를 선호".
- Suggested fix: in the `diverse` branch, prefer the family ≠ `maker_family`
  (e.g. `maker_family=claude → choose=codex`; `maker_family=gpt → choose=claude`),
  still subordinate to explicit choice and hard eligibility, then emit a trace token.

### F2 (low) — dropped portable roles + lost normalization in the shared model-map
The new `adapters/{claude,codex}/bin/model-map.sh` only knows deep maker/reviewer,
orchestrator, fast implementer/reviewer/writer. It drops `fast fact-checker` and
`external adversary orchestrator`, which are documented portable roles (core/CONVENTIONS.md,
core/ADAPTATION.md, adapters/claude/ADAPTATION.md → sonnet). The claude wrapper's old inline
`role_map` also normalized case/hyphens; model-map.sh requires an exact spelling.
- Impact: `dispatch-headless.py --model-role "fast fact-checker"` (or the adversary role, or
  a hyphen/case variant) now exits 64. Likely **unreachable** in practice — those roles are
  in-session Agent subagents, not headless pipeline stages — but it is a capability narrowing
  and a mapping-table drift (ADAPTATION lists them; the wrapper can no longer produce them).
- Suggested fix: either add the two roles (→ sonnet / gpt fast) to model-map.sh, or document
  in ADAPTATION that these roles are in-session only and not headless-dispatchable.

### F3 (test-adequacy) — selector test covers 3 of ~10 claimed scenarios
`utilities/dispatch-route.test.sh` has 3 assertions (plan→codex, plan→gpt, opencode→unknown)
+ a checksum no-mutation check. The plan's verification matrix claims coverage of "explicit
choice, hard rejection, cross-family checker, limited failover, unknown usage, bias final
tie, stable traces, no launch". Limited-failover, explicit-override, cross-family-checker
(the F1 path), and stable-trace assertions are absent. Adding them would have caught F1.

## Boundaries
No commit / push / merge / worktree cleanup performed. No depth-3 dispatch. No live
quota-consuming Claude/Codex model probes were run (opt-in; selector caches nothing) — the
adapter probe syntax is present in `model-map.sh` output and hermetic fixtures exercise the
fallback. `preflight.sh loop-info drill` E2E deliberately not auto-run.
