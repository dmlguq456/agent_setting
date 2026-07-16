# Pipeline dispatch metrics and exceptions

- Route: `rt-598d435deeb0cb81`; thorough staged graph.
- Broker status: live, ancestor-broker same-harness tuple supported.
- Plan attempt r2 crossed its read-only source boundary during negative-test
  discovery and was terminated; cleanup restored the worktree to clean.
- Plan attempt r3 produced complete plan/checklist/plan-check artifacts, but
  its workspace-write sandbox could not write the primary-checkout spec marker
  and did not emit the final handoff. The owner validated the artifacts and
  completed the route node using the plan-check evidence.
- Execute attempt r2 produced the source diff and focused checks, then returned
  `BLOCKED` for the same marker limitation. The owner wrote the canonical dev
  log and continued to independent `code-test`; no Fleet-parity claim is made
  for the owner-side artifact recovery.
- Fallback trace: same-harness broker ran; cross-harness was not available in
  the immutable route; native-subagent/inline fallback was limited to artifact
  recovery after the registered worker had already produced the stage body.
- Assurance compensation: independent registered `code-test`, full generated
  and conformance checks, semantic moved-body comparison, link/anchor scan,
  baseline comparison, and post-integration verification remain mandatory.
- Test retry r3 independently reduced the remaining defect to one stale
  draft-strategy fragment. Re-dispatching the already-completed immutable
  execute node through `dispatch-chain` reached the checked native/inline
  fallback (`ancestor-broker` exit 1; direct conductor disabled), so the owner
  applied the narrow correction inline and recorded its complete stage body in
  `dev_logs/code-execute-correction-r4.md`. A fresh registered independent test
  retry remains mandatory before the test node can complete.
- Test retry r4 closed the backlink defect and found an exact-set generator
  predicate error plus two omitted portable alignment statements. Because the
  immutable execute node was already completed, the owner again used the
  recorded inline correction fallback; `dev_logs/code-execute-correction-r5.md`
  contains the complete stage body. A registered independent r5 test retry is
  required for route-node completion.
