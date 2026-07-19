
## depth-0 fix-forward (round 2, 2026-07-16)

- inline reason (SD-17): retry-execute was blocked by the route source-commit pin +
  denied baseline restore (see pipeline_summary blocker). The remaining fixes were
  three additive micro-edits (symlink projection + guard allowlists, one realpath line,
  one test-fixture reorder) — dispatch overhead clearly exceeds the stage, per the
  §5.10 inline exception. Executed by depth-0 main in the task worktree; commit 81a5cd88.
- contract findings escalated to depth-0 follow-up backlog:
  1. dispatch-node.py does not forward route.dispatch_evidence (v15 absorption item
     not yet at HEAD) — every --start needed manual evidence flags this cycle.
  2. execute-node retry vs source-commit exact pin: a staged pipeline whose mutating
     node commits cannot retry that node without a destructive restore (spec gap;
     candidate SD for stage-dispatch PRD).
