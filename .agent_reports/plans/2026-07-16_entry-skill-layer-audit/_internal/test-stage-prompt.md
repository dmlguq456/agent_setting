# Assigned code-test stage

Independently verify the uncommitted entry-skill-layer refactor in
`/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit` at thorough code rigor.
Treat source as read-only. Write test evidence only under
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/test_logs`
and `_internal/test_reviews`.

Inputs:

- Plan/checklist and plan review under the canonical cycle root.
- Execute evidence: `dev_logs/step_02_entry_skill_layer.md`.
- Task spec: `/home/Uihyeop/agent_setting/.agent_reports/spec/skill-design-refactor/prd.md`.
- Starting commit: `23c86beaa613571a583f65e869da6b72013a2ad4`.
- Current source diff in the task worktree.

Run the required generated, conformance, routing, projection, adaptation,
static-footprint, and diff checks with repository verification wrappers and
bounded timeouts. Compare unrelated failures to the planning baseline.

Perform semantic review beyond command exit codes:

- exactly 13 primary entry routers, excluding parent-invoked/model-support;
- concrete manifest `Use when`/`Not for` boundaries on all four Skill trees;
- pre-approval router vs post-approval owner separation;
- lossless moved owner procedures relative to the starting commit, allowing
  only required path rewrites;
- every moved reference and Markdown anchor resolves from its new directory,
  especially existing `references/...`, `../../core/...`, and the
  draft-strategy backlink;
- Claude/root/plugin parity and Codex/OpenCode native projection boundaries;
- official runtime support, local projection, and physical masking claims stay
  distinct; no token/cost-savings claim;
- worker-bootstrap v5 files/hashes and 1,571 / 1,862-2,028 byte measurements
  remain unchanged;
- no primary-checkout source, fleet-usage, or dispatch behavior is changed.

If any issue is found, write a precise FAIL report with file/line evidence and
the smallest correction recommendation. Do not modify source. If all gates
pass, write a PASS report sufficient for route completion.
