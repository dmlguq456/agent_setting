# Verification evidence

- Baseline reproduction: BC-shaped exact reconcile evidence returned `failed` before the edit.
- Focused Fleet route/gate/process/context: **131/131 PASS**.
- Final full canonical Fleet suite: **886/886 PASS**.
- Integrated `main` full Fleet suite: **886/886 PASS**.
- Generated projections: `tools/generate.py --check` PASS.
- Python compile, `git diff --check`, and canonical/Claude mirror byte comparisons: PASS.
- Adaptation boundary: PASS; the existing non-failing portable-reference warning remains.
- Acceptance probe: marker absent → `reconciling`, `frame …gate 1m`, done=0; marker present →
  `done`, `frame ✓1m`, done=1; generic stale → `failed`.
