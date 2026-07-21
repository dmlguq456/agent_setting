# Dispatch surface terminology v20 — pipeline summary

Status: complete — merged, integrated, pushed, and task worktree removed.

The task restarted from clean `origin/main`; deleted candidate/remediation code
was not restored. See `plan.md` and `checklist.md`.

The implementation now separates dispatch depth, transport, execution surface,
registration, and fallback hop in topology, route, registry, completion, Fleet,
wrapper, generated Skill/mode, and drill surfaces. Quick is one checked
registered-headless dispatch-depth-1 owner; direct is inline; every standard+
route carries checked headless tuples and the ordered four-hop fallback.

The first independent read-only audit reported 20 findings. All were addressed:
immutable attempt replay and exact tuple checks; strict native evidence;
schema-v2 completion history/link proof; serialized per-node completion;
terminal-row fail-closed behavior; exact repair/harvest/cleanup; current-only
Fleet authority; complete bare-depth rejection; corrected canonical prose,
hook CLI, loop projection, mode projection, and g9/g10/g11 drill fixtures.

The final independent audit reported no critical finding and identified two
high, four medium, and two low residuals. All were closed: cleanup candidate
authorization now requires a valid current attempt; standard+ documentation and
the reminder use route-bound `dispatch-node.py` plus captured exact attempt
completion; Fleet validates marker axes; registry repair pins the canonical
marker; Codex harvest is idempotent with no live row; loop writers use current
worker identity; completion replay cannot regress the latest pointer; and the
g9/g10/g11 drills assert attempt and fallback evidence.

Current verification evidence:

- focused route/contract/completion/fallback/topology/registry/worker suites pass;
- Codex, Claude, and OpenCode SD-45 and SD-15 wrapper suites pass;
- exact harvest and guarded cleanup regressions pass;
- Fleet: 733 tests pass;
- generated projections, routing contract, and adaptation boundary pass;
- portable guards: 355 pass, 0 fail;
- `git diff --check` passes.

Integration:

- implementation commit: `4e2f8f7a`;
- merge commit: `781581bc`;
- `origin/main` pushed through `781581bc`;
- integrated tree matched the verified branch tree and repeated key utility,
  concurrency, Fleet 733, generated projection, routing, and adaptation checks;
- registered open jobs and orphaned conductor jobs: 0;
- cleanup check passed and removed the task worktree while preserving the branch.
