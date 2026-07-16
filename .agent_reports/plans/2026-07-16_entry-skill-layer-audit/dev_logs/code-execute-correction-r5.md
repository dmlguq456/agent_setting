# Code-execute correction r5

Verdict: PASS

The r4 independent review found one exact-set projection defect and two
omitted portable alignment statements. The capability contract generator now
derives the owner-status row from invocation class independently of capability
group, so all and only the 13 manifest `entry-router` contracts declare their
post-approval owner. Execution topology remains group-specific.

`core/DESIGN_PRINCIPLES.md` and `capabilities/README.md` now define the compact
pre-approval router, post-approval capability owner, and assigned-stage
contract boundary, including exclusion of parent-invoked/model-support Skills
from primary routing. The entry-layer gate asserts the exact 13 owner-row set,
targets, and both portable documentation anchors.

Generated outputs were refreshed. Entry-layer, generation, conformance,
routing, strict footprint, adaptation, topology, and diff checks all pass.
No commit or push was performed in this correction stage.
