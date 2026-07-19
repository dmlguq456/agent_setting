# Assignment — conductor r2 (resume): spec-read 게이트 멀티-스펙 인지화

You are the replacement depth-1 capability owner for an in-flight autopilot-code cycle.
The first conductor dispatched the `plan` stage correctly, then violated the SD-14 one-shot
wait contract (ended its turn "waiting for a background notification") and died. You resume
from existing artifacts. Do not restart completed work.

## Read first

Full task spec, route binding, scope, and hard operational constraints (unchanged, still
authoritative):
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/_internal/conductor-prompt.md`

Route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/_internal/route.json`
(rt-603bfc57313d9266). Worktree: `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec`.
Canonical plan root: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/`.

## SD-14 — absolute rule for you

You are a `claude -p` one-shot process: **your OS process terminates the moment your turn
ends.** There are no background notifications for you; anything you leave "waiting in the
background" is orphaned the instant you finish a message.

- After every stage dispatch, poll **in the same turn** with repeated FOREGROUND calls:
  `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent spec-gate-multi-spec --max 600`
  Loop on exit 2 (call it again). Never use run_in_background for waiting. Never end your
  turn while any child row is open.
- Exit 3 → diagnose via `/home/Uihyeop/agent_setting/.dispatch/logs/<slug>.claude.log` (or
  `.codex.log`) tail and the registry row, then harvest or redispatch; still in the same turn.

## Resume state (verify, then act)

1. `plan` node (slug `spec-gate-multi-spec-plan`, pid was 2261671) was dispatched at
   2026-07-16T07:05Z and may be complete or still running when you start.
   - If its row is still open and the process is alive: poll with dispatch-wait as above.
   - When closed/exited: verify `plan/plan.md` (+ `checklist.md`) exist at the canonical plan
     root with sane frontmatter. If complete: append a `done` row for it (append-only registry:
     duplicate the row with status `done`, add `note=harvested-r2`), then write the completion
     marker:
     `python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node plan --evidence <abs path to plan/plan.md>`
   - If the plan worker died without a usable artifact: redispatch node `plan` per the
     mechanics below, then continue normally.
2. Then run Step 2 plan-check (inline, lightweight — standard graph), and continue
   `execute → test → report` exactly per the original prompt.

## Stage dispatch mechanics (r1 lesson baked in)

`utilities/dispatch-node.py` does NOT forward nested-eligibility evidence and the launch
fails closed with `nested-eligibility-evidence-missing` unless you pass it explicitly.
Append these passthrough args after `--` on every dispatch-node call (values are already
recorded in the route's `dispatch_evidence.tuples`):

- claude child (execute, report — and plan redispatch if needed):
  `-- --model-role "<node role>" --parent-harness claude --parent-transport headless --parent-sandbox default --nested-eligibility supported --eligibility-source "depth-0-broker:brk-e1ca7129bef04676aac59547b20e403a+command-check"`
- codex child (test node, prefer codex when `utilities/usage-check.sh` says ok):
  `-- --model-role "deep reviewer" --parent-harness claude --parent-transport headless --parent-sandbox default --nested-eligibility supported --eligibility-source "depth-0-broker:brk-e1ca7129bef04676aac59547b20e403a+headless-check"`

Base call per node (unchanged from the original prompt):

```bash
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/_internal/route.json \
  --node <execute|test|report> --adapter <claude|codex> --action start \
  --slug spec-gate-multi-spec-<stage> --parent spec-gate-multi-spec --qa standard \
  --prompt-text "<stage contract: sub-skill + absolute input paths + output contract + intensity standard + slug>" \
  <passthrough args above>
```

Model roles: execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
After each harvested stage: append its `done` row, write the completion marker, then dispatch
the next node. Completion markers are mandatory before the dependent node starts
(`completion-marker-missing` fails closed).

## Completion

Identical to the original prompt: `pipeline_summary.md` under the §5.8 lock, then exactly:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
