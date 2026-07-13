# dispatch-routing-policy-v7 implementation plan

Date: 2026-07-13  
Stage: depth-2 `code-plan` under `dispatch-routing-impl`  
Scope: durable plan only; no source changes in this stage.

## Significance and graph

`SPEC-SIGNIFICANT`: PRD v7 changes portable dispatch priority, model-family/role ownership, adapter runtime probes, and Fleet attribution. Use the `standard` graph; this is `code-plan`, followed by `code-execute -> code-test -> code-report`. Only execute mutates source.

## Locked requirements

- SD-21: standard+ depth-1 conductor=`orchestrator` with high/deep reasoning; fast orchestration is mechanical-only.
- SD-22 priority: `explicit choice > hard eligibility > stage affinity > maker/checker family diversity > capacity/cost/latency`. Planning/architecture/decomposition=`deep maker` with GPT/Codex affinity, not a hard pin. Core owns family/role; adapters own exact model/reasoning and proof.
- SD-23: deterministic read-only `utilities/dispatch-route.sh` consumes `usage-check.sh`, reports selection/rejections/fallback/trace, and never launches/registers/mutates. Claude/Codex initially supported; OpenCode honest `unknown`.
- SD-24: env-marked Codex headless process child-hidden while jobs.log remains; non-code jobs never fuzzy-match code stages; genuine code stages remain.

## Evidence/current state

Official currentness (2026-07-13): OpenAI [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) supports bounded delegation, favors read-heavy parallel work, warns about write conflicts/token cost, and recommends capable/high-reasoning settings for demanding agents. OpenAI [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) defines `codex exec`, explicit sandboxing, and `--ephemeral`. OpenAI [Models](https://developers.openai.com/api/docs/models) recommends GPT-5.6 Sol for complex reasoning/coding (exact API ID `gpt-5.6-sol`, alias `gpt-5.6`), but API docs do not prove Codex runtime/account acceptance. Anthropic's [CLI reference](https://code.claude.com/docs/en/cli-reference) documents Claude `-p`, model alias/full ID, and effort; exact acceptance still needs a probe.

Local checks: Codex 0.144.1, Claude Code 2.1.207, OpenCode 1.17.13; Codex subagent/headless checks pass. Runtime links/hook trust exist, but runtime projection bootstrap discovery returned `codex-debug-failed exit=1`, so full discoverability is unproven. Codex role defaults are stale (`gpt-5.5` deep, `gpt-5.4-mini` fast, conductor fast/medium); Claude embeds a separate map and maps conductor sonnet/medium; OpenCode invents `runtime-default`. `usage-check.sh` already emits conservative status+bias. Fleet procscan directly recognizes only Claude children; Codex uses later cwd reconciliation. `live_stage()` always searches `plans/`, permitting non-code false stages.

## Implementation

### 1. Core-first portable contract

Files: `core/CONVENTIONS.md`, `core/OPERATIONS.md`, `core/ADAPTATION.md`; only necessary cross-references in `core/WORKFLOW.md` and `core/DESIGN_PRINCIPLES.md`.

- Define portable families (`gpt`, `claude`, `unknown`) separately from exact IDs.
- Set conductor/deep-maker roles and mechanical-only downshift boundary.
- Add the exact five-step priority, hard-eligibility inputs, checker maker-family input, and `usage-check ok` caveat.
- Specify stable trace/rejection/fallback/unknown and read-only invariants.
- Preserve direct/quick/standard+ topology, depth, and write ownership.

### 2. Read-only selector

Files: new `utilities/dispatch-route.sh` and `utilities/dispatch-route.test.sh`; reuse `usage-check.sh`.

- Inputs: stage, capability, intensity, optional QA, repeatable required surfaces, explicit harness/family/role/model, maker family, jobs path, adapter probe results. Conflicts exit 64.
- Build candidates only from adapter outputs; eliminate runtime/tool/account/exact-model/limit failures before ranking.
- Invoke `usage-check.sh --harness all --jobs ...` once. `limited` rejects; `unknown` stays uncertainty.
- Apply priority lexicographically; capacity bias is final tie-break only.
- Stable `key=value` output: status, adapter, family, role, exact_model_id, reasoning, trace.N, rejected.N, fallback.N, unknown.
- Hermetic tests checksum jobs/worktree before/after, fixture probes, and forbid eval, launches, registry/cache/worktree writes.

### 3. Exact adapter mapping/probes

Files: consistent adapter helper (`adapters/{claude,codex,opencode}/bin/model-map.sh`), `preflight.sh model-info`, adapter docs, and all dispatch wrappers.

- Claude: standard+ conductor/deep maker use high/deep candidates. Live acceptance: minimal no-tool `claude -p --no-session-persistence --permission-mode plan --max-turns 1 --model <candidate> --effort <level>`. Alias is discovery only.
- Codex: deep roles/conductor prefer adapter candidate `gpt-5.6-sol`/high; lighter mechanical work uses an eligible fast candidate. Probe using minimal `codex exec --ephemeral --sandbox read-only --model <exact> -c model_reasoning_effort=...`; rejection is traced and falls back cleanly.
- OpenCode: `status/family/exact_model_id=unknown` with reason until supported inventory/acceptance exists; do not copy other mappings.
- Make all three `dispatch-headless.py` wrappers consume the adapter mapper, eliminating duplicated dictionaries. Explicit choice remains first but cannot bypass eligibility silently.
- Keep live probes opt-in/quota-sensitive; hermetic tests use fixtures.

### 4. Adapter/projection wiring

Files: adapter bootstrap/ADAPTATION/README, `tools/check-adaptation-boundary.sh`, `INSTALL_LAYOUT.md` if required, selective utility projections.

- Project route/usage helpers and tests through adapter utility directories only after documenting status; OpenCode selector support still returns model unknown.
- Extend dynamic utility allow/defer census and preflight help/output. Separate runtime support, adapter realization, parity.
- Source order: shared/core -> adapter helper -> projection checks. Never hand-edit generated Codex skills/plugin or OpenCode commands.
- If portable capability sources change, run supported Codex/OpenCode sync scripts and `--check`; otherwise prove generated output unchanged.

### 5. Fleet procscan hotfix

Files: `tools/fleet/collectors/procscan.py`, `collectors/__init__.py`, focused Fleet tests, and wrapper env assembly.

- Add stable cross-runtime `AGENT_DISPATCH_CHILD=1` in each wrapper. Procscan reuses its single env read and identifies Codex children by this marker, never argv/PPID/cwd guesses.
- Preserve Claude marker, memory/app-server logic, Windows fail-open. Unreadable env means visible/not-proven-child.
- Keep cwd/jobs reconciliation only as documented legacy fallback with parent protection.
- Hermetic ps/cwd/env/tty test asserts Codex Session child-hidden while registry row/liveness remains rendered.

### 6. Metadata-exact Fleet stages

File: `tools/fleet/collectors/dispatch.py` plus collector/render tests.

- Central resolver maps explicit code worker roles to plan/exec/test/report. Only explicit code capabilities (`autopilot-code`, `code-*`) may derive progress from plan artifacts.
- Gate `_find_plan_dir`, `_plan_qa`, and `live_stage` at every caller, including working registry and tokenless enrichment.
- Preserve exact/fuzzy recovery for genuine legacy code rows. Add non-code path/slug containing `plans` with nearby code artifacts and assert no plan/test/spec:test; add positive code-plan/code-test fixtures.

## Verification matrix

```sh
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- bash utilities/usage-check.test.sh
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- bash utilities/dispatch-route.test.sh
adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- python3 -m unittest discover -s tools/fleet/tests -v
adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- bash hooks/portable-guards.test.sh
adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- bash tools/check-adaptation-boundary.sh
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/codex/bin/sync-native-agents.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/codex/bin/sync-native-skills.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/codex/bin/sync-native-plugin.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/codex/bin/sync-native-modes.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/opencode/bin/sync-native-agents.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/opencode/bin/sync-native-skills.py --check
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- adapters/opencode/bin/sync-native-commands.py --check
adapters/codex/bin/preflight.sh doctor
adapters/codex/bin/preflight.sh doctor --runtime
adapters/codex/bin/preflight.sh runtime-projection --require-hook-trust
git diff --check
```

Selector tests cover explicit choice, hard rejection, GPT/Codex plan affinity, cross-family checker, limited failover, unknown usage, bias final tie, OpenCode unknown, stable traces, no mutation. Fleet tests cover all SD-24 bullets. Separately run accepted+invalid live probes for Claude/Codex if quota permits; otherwise record unknown/limited and prove hermetic fallback. Do not auto-run drill; report `preflight.sh loop-info drill` as optional later E2E.

## Risks/safeguards

- Catalog/entitlement drift: adapter-owned exact candidates, immediate probe, clean fallback; aliases are not proof.
- Probe quota: minimal ephemeral/non-persistent opt-in prompts; selector caches nothing.
- Mapping drift: selector and wrappers share adapter mapper output.
- `usage-check ok` is not availability; probe failure rejects.
- Unreadable `/proc/.../environ`: fail open and retain registry fallback; never infer by substring/PPID.
- Keep fuzzy matching for explicit legacy code only to avoid regression.
- Report runtime bootstrap discovery failure until runtime doctor is clean.
- Core markers initially targeted a read-only install; `AGENT_HOME=$PWD` created all 10 worktree markers. Downstream writes keep that root.

Completion requires a deterministic change+regression for SD-21~24 and a report separating runtime support, adapter realization, parity, projection sync, and live-probe gaps. Commit/push/merge/cleanup remain with the main orchestrator.
