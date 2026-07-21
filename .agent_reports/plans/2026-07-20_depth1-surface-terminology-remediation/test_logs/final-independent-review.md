verdict: FAIL

# Final independent review — depth-1 surface terminology remediation

Date: 2026-07-20  
Reviewed committed range: `6f3007b1c65acca02d0348605e9cc32d46c595c4...36a8e849e8fde9c41f115b49f3a7b0fb8d67f117`  
Additional review scope: the complete current unstaged remediation diff  
Approved scope: retain and repair the intent of `7094c92b` + `c95ed391`; exclude `6b3a34bc`

## Gate result

FAIL. The bounded fix round closes the Claude native-surface mismatch, removes null standard+ completion axes, repairs the observed wrapper/drill CLI names, and supplies substantive acceptance evidence. It does not meet the final gate because completion-marker idempotency can retain stale attempt/surface evidence across a retry, and active normative/wrapper/Fleet prose still contains ambiguous bare dispatch-depth language that the new conformance test does not detect.

Thorough/code QA policy was applied: `assurance_scope=plan-check:selected-independent-pass:final-verify`, `quality_reviewers=2x-deep-reviewers+2x-fast-reviewers`, `independent_delegation_policy=claim-only-if-separate-codex-agent-headless-or-external-pass-ran`. This artifact is the separately dispatched independent final review; no additional reviewer identity is claimed.

## Findings

### Major 1 — same-digest standard+ retry can publish stale attempt and execution-surface axes

- `utilities/capability-route.py:385-394` hashes only the evidence body and returns the existing canonical marker whenever that digest matches. It does not compare the newly validated `attempt_id`, `transport`, `execution_surface`, `registered_worker`, or `fallback_hop`.
- `utilities/capability-route.py:489-494` validates the current attempt, calls the digest-only marker writer, and immediately returns for unregistered native/inline completions. Therefore an unregistered retry gets no separate attempt linkage and receives the prior marker unchanged.
- `utilities/dispatch_completion_marker.test.py:321-346` exercises same-evidence idempotency only with the same attempt ID and same inline axes. There is no same-artifact retry that changes attempt ID or fallback surface.

Reproduction against the accepted standard+ route, using one unchanged evidence file first as registered headless and then as inline fallback:

```text
{"canonical": {"attempt_id": "att-retry-one", "surface": "registered-headless"}, "first": {"attempt_id": "att-retry-one", "surface": "registered-headless"}, "second_returned": {"attempt_id": "att-retry-one", "surface": "registered-headless"}}
```

The second completion supplied `attempt_id=att-retry-two`, `execution_surface=inline`, `registered_worker=0`, and `fallback_hop=inline`, but the canonical and returned marker still claim the first registered-headless attempt. This violates SD-74's requirement that a fallback retain logical dispatch depth without being mislabeled as registered dispatch, and defeats the plan's exact-attempt-evidence completion binding.

Required fix: make marker idempotency include the exact attempt identity and all attempt axes, or create a new history/canonical marker whenever those axes differ even if the evidence digest is unchanged. Add registered-headless → native/inline and native/inline → registered-headless same-artifact retry fixtures.

### Moderate 2 — current qualified-terminology propagation and its conformance check remain incomplete

The governing plan requires current normative prose and generated projections to say “dispatch depth” or use `dispatch_depth`. Active current surfaces still use ambiguous bare `depth` for dispatch topology:

- `core/OPERATIONS.md:127` says dispatch prompts expose “QA, intensity, depth, parent ...”.
- `adapters/codex/AGENTS.md:89` repeats “QA, intensity, depth, parent ...”.
- `adapters/codex/bin/capability-map.sh:78` and `adapters/opencode/bin/capability-map.sh:63` advertise an “intensity/depth dispatch contract”.
- All three wrappers retain “callers gate on depth/action” at `adapters/claude/bin/dispatch-headless.py:722`, `adapters/codex/bin/dispatch-headless.py:1028`, and `adapters/opencode/bin/dispatch-headless.py:764`.
- Fleet's current registry/parser prose still says `depth/parent/intensity` at `tools/fleet/collectors/dispatch.py:77`, and current rendering prose says “Every depth fans out” at `tools/fleet/render.py:1020` (with byte-identical Claude mirrors).

The new terminology check at `utilities/dispatch_v20.test.py:225-243` matches only bare `depth` immediately followed by `0`–`3`; it cannot catch any of the active examples above. Its explicit safety assertions at `:245-277` cover `--depth`, the Claude surface token, and two corrupted `find` spellings, but not the stated repository-wide normative-prose rule.

Required fix: qualify these dispatch-topology references while preserving unrelated concepts such as review depth, search depth, native-subagent nesting depth, display-indent locals, and Unix `find -maxdepth`; extend conformance with semantic/contextual fixtures for both required replacements and protected unrelated meanings.

## Prior finding closure

1. **Claude native fallback surface and shared validation — CLOSED.** `utilities/stage-dispatch-fallback.py:168-214` validates proof rows through `validate_attempt_metadata` and applies the explicit Codex/Claude surface map; `:729-740` emits `claude-subagent` for Claude. `utilities/stage_dispatch_fallback.test.py:114-130` exercises both `codex-native-subagent` and `claude-subagent`.
2. **Null standard+ completion axes — PARTIALLY CLOSED, NOT FULLY CLOSED.** Missing axes now fail before write and every fresh marker has non-null axes, but Major 1 shows a later exact attempt can inherit stale, incorrect non-null axes.
3. **Wrapper/drill/prose qualified terminology — NOT CLOSED.** Removed `--depth` wrapper/drill invocations and the previously cited bare metadata line are repaired, but Moderate 2 remains and the conformance check is weaker than the plan.
4. **Acceptance summary and expanded v20 matrix — CLOSED.** `route-acceptance/summary.md` is substantive and records fresh route IDs/hashes, zero-emission cases, standard+ completion/fallback evidence, logs, and preservation results. `utilities/dispatch_v20.test.py` now contains eight substantive wrapper/compile/registry/conformance cases and passes 8/8.

Therefore not all four prior findings are closed.

## Confirmed properties

- Quick compilation produces exactly one dispatch-depth-1 registered-headless owner with no child node and fails `quick-headless-unavailable` before route/row/spawn emission when checked eligibility is absent or unsupported.
- The wrappers reject unbound quick attempts, quick dispatch-depth-2 children, unknown execution surfaces, and unknown fallback hops; a second live quick claim does not append another row, and exhausted candidates fail `quick-registered-headless-exhausted`.
- Route/topology fields use `dispatch_depth`, `owner_dispatch_depth`, and `max_dispatch_depth`. Codex native `agents.max_depth` remains a separate runtime-native nesting concept.
- Current attempt rows carry schema v2 and the closed transport/surface/fallback vocabularies. Legacy rows remain diagnostic/read-only. Wrapper, registry, Fleet, and shared-validator suites pass.
- Direct acceptance remains dispatch-depth-0 inline/unregistered with no jobs row. Standard+ keeps owner/stage dispatch depth 1/2 and the four-hop order `same-harness-headless → cross-harness-headless → native-subagent → inline`.
- Canonical Fleet collector/model/control/render/route files are byte-identical to their Claude mirrors.
- `tools/generate.py --check`, `tools/sync-entry-skill-layer.py --check`, routing contract, and adaptation-boundary checks pass when run without ignored bytecode-cache contamination.
- Unix `find -maxdepth`/`-mindepth` options remain intact; no `-max_dispatch_depth`, `mindispatch`, `maxdispatch`, double-qualified field, or unrelated CLI-option corruption was found.
- `6b3a34bc320fc5d89c1b254e0314cf33aabc5824` is not an ancestor of HEAD, and no co-primary/multi-capability composition change appears in the reviewed retained diff. The two approved source commits were intentionally applied without preserving ancestry and consolidated into the task commit, as required by the plan.

## Exact verification commands

Scope, diff, and acceptance:

```text
git status --short
git log --oneline --decorate --graph 6f3007b1..HEAD
git diff --stat 6f3007b1...HEAD
git diff --stat
git diff --name-status 6f3007b1...HEAD
git diff --name-status
git diff --check
git diff --cached --check
git merge-base --is-ancestor 7094c92b HEAD
git merge-base --is-ancestor c95ed391 HEAD
git merge-base --is-ancestor 6b3a34bc HEAD
git diff 6f3007b1...HEAD -- core/WORKFLOW.md capabilities/autopilot-spec.md | rg -n 'co-primary|multi-capability|composition|capability DAG|envelope' || true
python3 utilities/capability-route.py verify --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/test_logs/route-acceptance/direct.json --cwd /home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated
python3 utilities/capability-route.py verify --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/test_logs/route-acceptance/quick.json --cwd /home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated
python3 utilities/capability-route.py verify --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/test_logs/route-acceptance/standard-plus.json --cwd /home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated
```

Results: all three fresh routes verify with the IDs and hashes recorded in `summary.md`; excluded commit status is non-ancestor as required. `7094c92b` and `c95ed391` are also non-ancestors because the approved plan required `cherry-pick --no-commit` followed by one consolidated task commit; their scoped intent is present in the reviewed diff.

Required aggregate suite, run through the checked verification runner:

```text
PYTHONDONTWRITEBYTECODE=1 adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- zsh -c '
set -e
python3 tools/capability_topology.test.py
python3 utilities/capability_route.test.py
python3 utilities/dispatch_contract.test.py
python3 utilities/dispatch_node.test.py
python3 utilities/dispatch_registry.test.py
python3 utilities/dispatch_completion_marker.test.py
python3 utilities/dispatch_progress.test.py
python3 utilities/worker_route_guard.test.py
python3 utilities/stage_dispatch_fallback.test.py
python3 utilities/stage_dispatch_capacity.test.py
python3 utilities/worker_bootstrap.test.py
python3 utilities/worker_dispatch_prompt.test.py
python3 adapters/claude/bin/dispatch-headless.sd45.test.py
python3 adapters/codex/bin/dispatch-headless.sd45.test.py
python3 adapters/opencode/bin/dispatch-headless.sd45.test.py
bash adapters/claude/bin/dispatch-headless.sd15.test.sh
bash adapters/codex/bin/dispatch-headless.sd15.test.sh
bash adapters/opencode/bin/dispatch-headless.sd15.test.sh
python3 utilities/dispatch_v20.test.py
python3 -m unittest discover -s tools/fleet/tests -p "test_*.py"
sh tools/routing-contract.test.sh
python3 tools/generate.py --check
python3 tools/sync-entry-skill-layer.py --check
sh tools/check-adaptation-boundary.sh
bash hooks/portable-guards.test.sh
git diff --check
'
```

Results before the aggregate stopped: all focused suites PASS; completion 11/11, fallback 11/11, v20 8/8, Fleet 728/728, routing contract PASS, generation and entry-skill checks PASS. The in-worktree adaptation check then failed only because preceding subprocess tests created ignored `adapters/{codex,opencode}/bin/__pycache__` files. The same committed+unstaged diff passed adaptation-boundary from a clean temporary clone:

```text
review_tmp=$(mktemp -d /tmp/surface-review.XXXXXX)
git clone -q --shared . "$review_tmp"
git diff --binary | git -C "$review_tmp" apply -
PYTHONDONTWRITEBYTECODE=1 sh "$review_tmp/tools/check-adaptation-boundary.sh"
```

Result: `OK: adaptation boundary checks passed`, with the existing non-fatal warning about 110 documented concrete Claude/model references.

The portable guard suite was also run separately:

```text
PYTHONDONTWRITEBYTECODE=1 adapters/codex/bin/preflight.sh verification-runner --timeout 300 -- bash hooks/portable-guards.test.sh
```

Result: `PASS=350 FAIL=5`. Two default-registry failures were caused by this worker's inherited `AGENT_DISPATCH_JOBS`; one start failure explicitly reported the expected sandbox `nested-sandbox-lifetime` restriction; two `doctor --runtime*` failures depend on current runtime projection/native CLI state. These five are recorded as environment/runtime-contract warnings, not used to establish the source FAIL above. The remediation-specific quick, wrapper, stage-dispatch, liveness, projection-generation, and terminology-adjacent assertions inside the suite passed.

Parity and mechanical-safety scans:

```text
cmp -s tools/fleet/collectors/dispatch.py adapters/claude/tools/fleet/collectors/dispatch.py
cmp -s tools/fleet/model.py adapters/claude/tools/fleet/model.py
cmp -s tools/fleet/control.py adapters/claude/tools/fleet/control.py
cmp -s tools/fleet/render.py adapters/claude/tools/fleet/render.py
cmp -s tools/fleet/route.py adapters/claude/tools/fleet/route.py
rg -n 'find[[:space:]].*(-maxdepth|-mindepth)' adapters core capabilities roles skills hooks utilities tools loops
rg -n 'find[[:space:]].*(dispatch-depth|max-dispatch-depth)|-(max|min)dispatch|--dispatch-depth' adapters core capabilities roles skills hooks utilities tools loops --glob '*.sh' --glob '*.md' --glob '*.py'
rg -n --fixed-strings -- '--depth' core capabilities roles skills adapters hooks utilities tools loops || true
rg -n '(maxdepth|mindepth|tree depth|search depth|analysis depth|recursion depth|nesting depth|execution_surface|fallback_hop|registered_worker)' <reviewed diff/current roots>
```

All Fleet comparisons return zero and protected Unix `find` options are unchanged. The final targeted bare-depth scan exposed Moderate 2.

Completion retry reproduction:

```text
python3 -c 'import importlib.util,json,pathlib,tempfile; p=pathlib.Path("utilities/capability-route.py"); s=importlib.util.spec_from_file_location("r",p); r=importlib.util.module_from_spec(s); s.loader.exec_module(r); route=json.load(open("/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/test_logs/route-acceptance/standard-plus.json")); node=next(n for n in route["nodes"] if n["id"]=="plan"); td=tempfile.TemporaryDirectory(); out=pathlib.Path(td.name); r.completion_dir=lambda _rid: out/"markers"; evidence=pathlib.Path("/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/test_logs/route-acceptance/summary.md"); first={"transport":"headless","execution_surface":"registered-headless","registered_worker":"1","fallback_hop":"same-harness-headless"}; second={"transport":"interactive","execution_surface":"inline","registered_worker":"0","fallback_hop":"inline"}; m1,_=r.complete_node(route,node,"plan",evidence,attempt_id="att-retry-one",explicit_attempt_metadata=first); m2,_=r.complete_node(route,node,"plan",evidence,attempt_id="att-retry-two",explicit_attempt_metadata=second); print(json.dumps({"first":{"attempt_id":m1["attempt_id"],"surface":m1["execution_surface"]},"second_returned":{"attempt_id":m2["attempt_id"],"surface":m2["execution_surface"]},"canonical":{"attempt_id":json.load(open(out/"markers"/"plan.json"))["attempt_id"],"surface":json.load(open(out/"markers"/"plan.json"))["execution_surface"]}},sort_keys=True)); td.cleanup()'
```

No source, generated projection, test, or canonical specification was edited by this review. Only this canonical review artifact was replaced.
