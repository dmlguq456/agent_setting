# Main integration hardening

## Findings closed

1. Accounting aggregates accepted unknown top-level keys. The store now enforces
   the exact fixed schema plus timestamp, sample, byte, and monotonic-counter
   identities, so poisoned content fields reset fail-open instead of persisting.
2. A failed private receipt write suppressed an otherwise valid Phase 1
   directive, and a missing lifecycle receipt discarded canonical delivered
   stdout. Receipt/accounting infrastructure is now observational only: actual
   canonical stdout owns contribution bytes, while unavailable receipt samples
   remain `null`; accounting exceptions cannot change output.
3. Malformed transition state looked like missing state and could re-emit. It now
   degrades to `unknown`/zero contribution without overwriting the damaged file.
4. A complete-looking `status=invalid` arm and extra schema fields could enter a
   triplet. Declaration/result schemas are now exact, every invalid arm is
   excluded, tokenizer provenance must be non-empty when present, and the
   control arm remains exactly zero.
5. The newly added accounting portable-guard capture now uses the invocation's
   unique `$TMP`, matching the runtime-projection collision fix.

## Focused evidence

- Phase 2 focused suite: 20 tests passed.
- Phase 3 focused suite: 9 tests passed.
- Frozen `offline-forecast-v1` code hash updated to
  `a674cc885fec256d111b684a6b998a3b44e6ff1b5ef3f555fa65a39fd3d8ceb9`.
- Canonical/Claude mirror files were copied and byte-compared.

Independent review then found five additional gaps: duplicate workload sample
inflation, spawn-error accounting loss, raw CLI session id output, impossible
directive accounting/provenance, and a spec-extra aggregate field. All were
fixed and covered by regressions. Final evidence is Phase 2 21, Phase 3 10,
Fleet 221, portable 344/0, adaptation/boundary/manifest/doctor/diff/production
absence pass, and independent re-review PASS.

Production dynamic activation, runtime config, model/effort, intensity,
dispatch/depth, QA, input pruning, RL/online fitting, and adoption state remain
unchanged. Integration is ready; real Phase 3 evidence is still pending.
