# Implementation evidence

- Added exact F-41 reconciliation evidence recognition in `tools/fleet/route.py`.
- Preserved active, marker, explicit-failure, generic stale/dead, clean-done, and pending
  boundaries while selecting the canonical/newest retry for reconciliation.
- Added yellow `…` breadcrumb/detail and `…gate` process labels in `tools/fleet/render.py`.
- Added parallel aggregation precedence `failed > active > reconciling`.
- Added positive, negative, marker-transition, retry-order, progress, JSON, render, width, and
  process-card regressions; synchronized the canonical Claude Fleet mirror byte-for-byte.
- No live jobs registry, completion marker, or BC_ResNet_tf artifact was mutated.
