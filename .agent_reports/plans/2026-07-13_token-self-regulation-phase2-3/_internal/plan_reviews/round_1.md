# Plan Review — Round 1 (inline fallback)

## QA limitation

- Thorough code policy reports up to 2 deep + 2 fast reviewers, no fact checker/external adversary, max 2 rounds.
- Both reviewer roles resolve, but this worker is depth 2. Any separate reviewer/headless child is forbidden depth 3, so none ran.
- This is structured inline plan-check fallback, **not independent QA**.

## Review axes

### Requirements completeness — PASS after correction

Every Phase 2 schema/counter/bound and Phase 3 feature/pairing/bootstrap/gate maps to a file owner and test. Fixtures are explicitly non-evidence; adoption stays pending.

### Production preservation — PASS with lock

Accounting authority must be the lifecycle parent, not child helper: only parent knows whether output was delivered or timed out. Child writes a transient receipt; parent records once. This prevents timeout miss/double count and preserves exact stdout.

### Privacy/concurrency/fail-open — PASS with lock

Aggregate permits digest/fixed counters/timestamps/directive IDs only. One bounded directory lock serializes update+prune; atomic replace prevents partial files. Tests must inspect serialized content and failure paths, not only field definitions.

### Experiment/statistics — PASS with locks

- Candidate is a separate module/CLI, absent from production imports.
- Unknown means no early emission but retains static-equivalent transition.
- Latch tests cover early target, later observed duplicate, and below-threshold reopen.
- Pairing is exact one-of-each arm, fixed reason priority, no imputation.
- Both quality LCBs use >=-0.02; both observed-delta LCBs use >0; workload-paired 10,000 seed 20260713.
- Canonical ordering/float/JSON and repeated output bytes are tested.

### Adapter/scope — PASS

Core changes first. Claude gets required Fleet mirror/portable isolated CLI but no hook activation. Codex gets allowlisted isolated CLI plus Phase 2 hook accounting. OpenCode is explicitly deferred without symlink/parity claim. Runtime config remains untouched. Current worker writes plan artifacts only.

## Findings incorporated

1. Single parent accounting authority plus private receipt.
2. Fixed zero-reason precedence including degradation versus timeout/error.
3. Precise valid/decreasing/unavailable sample behavior.
4. Production import negative scan and forbidden-file list.
5. Both static/control comparisons and deterministic lower-bound requirement.
6. Official current docs/local runtime/projection evidence and strict-probe limitation.
7. Fixture non-evidence assertion across implementation/test/handoff.

## Residual verification risks

- Timeout after receipt but before stdout: classify actual delivered contribution as empty/timeout exactly once.
- Lock must be bounded/stale-safe without deleting live lock; temp/locks excluded from bounds.
- Freeze hashes only after final candidate/fixture bytes, then lock via tests.
- Document/pin bootstrap lower-quantile indexing and float serialization.
- Regenerate manifest only with builder after projection changes.

## Verdict

**PASS WITH INLINE QA FALLBACK.** Ready for code-execute; no independent-review claim permitted.
