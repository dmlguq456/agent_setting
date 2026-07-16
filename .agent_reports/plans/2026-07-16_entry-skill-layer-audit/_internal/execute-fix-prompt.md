# Assigned code-execute correction pass

Correct the independent code-test failures in the existing uncommitted diff.
Work only in `/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit`; keep the
primary checkout untouched. Read:

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/_internal/test_reviews/code-test.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/test_logs/verification-matrix.md`
- the approved plan/checklist and current source diff.

Implement all three required correction groups:

1. Make all moved owner-execution links and anchors resolve correctly on the
   canonical, Claude-native, and Claude-plugin trees without semantic loss.
   Preserve one-level references; no nested reference directories.
2. Retarget the draft-strategy backlink to the actual post-approval owner
   contract/section.
3. Add adaptation classification/projection decisions for both new tools and
   extend the canonical strict context-footprint surface/baseline with exact
   manifest-derived 13-entry totals/maxima across active/plugin trees.

Extend `tools/entry-skill-layer.test.py` with a deterministic path-and-anchor
resolver covering every moved owner tree. Keep static bytes as input size only;
make no token/cost-savings claim. Run preflight before every edit, refresh all
generated outputs through `tools/generate.py`, run the focused failing checks,
and write a canonical correction log under `dev_logs/`. Do not commit or push.
