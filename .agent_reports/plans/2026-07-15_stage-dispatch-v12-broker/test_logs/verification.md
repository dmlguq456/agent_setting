# Verification evidence

## Target

- Plan: `plans/2026-07-15_stage-dispatch-v12-broker/plan.md`
- Source commit: `8897bf76`
- Integrated main commit: `70bac6ef`
- Verification mode: QA/test through the Codex adapter-owned `verification-runner`

## Graduated levels

1. Syntax/import — PASS
   - Python compile/import coverage for broker, route, fallback, contract, eligibility, and three dispatch wrappers.
   - `sh -n` for modified preflight surfaces.
2. Smoke/protocol — PASS
   - `python3 utilities/dispatch_broker.test.py -v`: 10/10.
   - Includes Claude→Claude, Claude→Codex, Codex→Claude, Codex→Codex; missing/stale/tampered binding; concurrent/sequential duplicate; claim-crash and post-registry crash recovery.
3. Functional — PASS
   - fallback 3/3, capability route 10/10, dispatch contract 5/5, worker route guard 3/3, spec transaction 2/2.
   - sibling adapter v11 1/1; Claude/Codex/OpenCode SD-45 3/3; three SD-15 conformance suites PASS.
4. Integration — PASS
   - `dispatch-route.test.sh`, `dispatch-concurrency.test.sh`, `dispatch-liveness.test.sh`, `dispatch-wait.test.sh`, artifact-root tests, topology tests, and manifest check.
   - `tools/check-adaptation-boundary.sh`: PASS.
   - `hooks/portable-guards.test.sh`: `PASS=359 FAIL=0`.
5. Behavioral runtime observation — PASS
   - Unix-socket request/response observed through a broker process distinct from the caller.
   - Global rows retained exact logical parent/depth and target harness for all four placements.
   - Claim crash resumed one unregistered attempt; post-registry crash returned the same attempt without a second row/launch.
6. Integrated-tree verification — PASS
   - Broker 10/10, fallback 3/3, route 10/10, manifest up to date, adaptation boundary PASS.
   - Installed Codex runtime projection check: `status=ok` with hook trust and active profile wiring intact.

## Failures found and closed

- Projection census initially lacked the two new utilities; fixed by explicit Codex/OpenCode deferred classification and Claude utility projection.
- Legacy concurrency fixture omitted v11 registry/eligibility evidence; fixture corrected and 3-worker parallel liveness/wait passed.
- Intentional bootstrap contract growth exceeded the old context baseline; baseline rebound to the reviewed current surfaces.
- OpenCode quick fixture lacked the already-required `parent_cwd` field; expected row corrected.

## Verdict

PASS — SD-51~53 implementation and the required four-placement compatibility matrix are verified; no known v12 regression remains. No independent QA reviewer is claimed.
