# SD-45 risk-focused review

## Verdict

**PASS after review fixes.** This was an independent native Codex fallback review because the registered headless worker path was unavailable. Source files were reviewed read-only; only this report was written.

No unresolved high- or medium-severity SD-45 finding remains in the reviewed diff.

## Resolved findings

### Resolved — stale route source state

Initial review found that `utilities/worker-route-guard.py` verified route integrity but did not compare the route-bound `source_commit` with current `HEAD`. The validator now reports `head`, refuses a mismatch with structured reason `route-source-commit-mismatch`, and has a regression fixture that compiles at commit A, advances to commit B, and confirms refusal.

### Resolved — legacy report-only compatibility

Initial review found that all wrappers treated `--write-scope` alone as route activation and rejected route-less legacy calls. Claude, Codex, and OpenCode now enter route-record enforcement only when route identity metadata is present; `--write-scope` alone retains the low-level report-only compatibility path. Every adapter fixture independently confirms a successful route-less dry run with `--write-scope source/**`.

## Confirmed behavior

- Claude, Codex, and OpenCode wrappers each validate an assigned immutable route before registration/start and export `AGENT_ROUTE_FILE`, `AGENT_ROUTE_ID`, and `AGENT_ROUTE_NODE` to the child.
- The shared validator fails closed on route hash/id, registry digest, assigned node, exact write scope, capability/intensity reselection, tracked evidence shape/satisfaction, workflow-mode mismatch, unsafe merge/rebase/cherry-pick/detached state, and route `source_commit` mismatch.
- Wrapper-resolved canonical artifact root and absolute worktree are compared with the route-bound paths before worker start.
- Route-backed prompts replace rerouting with consume/validate-only instructions. Codex excludes the former positive `preflight.sh route <capability>` bootstrap; Claude/OpenCode explicitly instruct immutable-record consumption and prohibit capability/intensity/topology reselection.
- The sibling fixtures are independent files that invoke their own adapter wrapper. Codex exercises scope refusal, Claude missing tracked evidence, and OpenCode capability reselection; the shared deterministic validator fixture covers hash tamper and source-commit mismatch. No adapter test invokes another adapter's PASS as a proxy.
- Route-less legacy operation remains available, preserving `route_compiler=report-only` and `legacy_low_level_dispatch=true`.

## Advisory

For future hardening, the Claude/OpenCode prompt assertions could exclude a concrete positive route command rather than the current newline-sensitive phrase. This is test precision only; inspection of the generated prompts found no positive rerouting instruction.

## Evidence commands and results

```text
python3 adapters/codex/bin/dispatch-headless.sd45.test.py      # PASS (1)
python3 adapters/claude/bin/dispatch-headless.sd45.test.py     # PASS (1)
python3 adapters/opencode/bin/dispatch-headless.sd45.test.py   # PASS (1)
python3 utilities/worker_route_guard.test.py                    # PASS (3)
```

Additional manual probes:

```text
route compiled at commit A -> commit B -> validate             # BLOCKED: route-source-commit-mismatch
codex route-less dry-run --write-scope source/**                # PASS, legacy path open
claude route-less dry-run --write-scope source/**               # PASS, legacy path open
opencode route-less dry-run --write-scope source/**             # PASS, legacy path open
```

## Scope

Reviewed: the three `dispatch-headless.py` wrappers, Codex/OpenCode `worker-route` preflight projections, Claude `capability-route.py worker-route` bridge, `utilities/worker-route-guard.py`, tracked-evidence validation, and all four focused SD-45/worker-route fixtures. No source changes were made by this review.
