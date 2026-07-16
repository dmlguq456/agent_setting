# Code-test semantic review — entry Skill layer

## Verdict

**FAIL.** The compact-router structure and byte budgets are correct, and the
owner prose was moved losslessly, but the moved owner documents do not resolve
their references from the new directory. The adaptation inventory also rejects
the two new canonical tools. These are new regressions and block route
completion.

## Findings

### 1. P0 — all moved owner-reference paths are interpreted from the wrong directory

The owner body is copied unchanged by
`tools/sync-entry-skill-layer.py:65-70`. Moving it from
`skills/<entry>/SKILL.md` to
`skills/<entry>/references/owner-execution.md` adds one directory level, but
the generator performs no path rewrite. The new test checks only owner-file
existence and router wording (`tools/entry-skill-layer.test.py:23-30`); it never
resolves links or anchors.

An independent resolver derived exactly 13 entry routers from the manifest and
checked canonical, Claude-native, and Claude-plugin owner documents. It found
345 reference occurrences and 345 missing targets. Representative evidence:

- `skills/analyze-project/references/owner-execution.md:27` resolves
  `../../core/CONVENTIONS.md` as nonexistent `skills/core/CONVENTIONS.md`;
- `skills/analyze-project/references/owner-execution.md:83` resolves
  `references/mode-code.md` as nonexistent
  `references/references/mode-code.md`;
- `skills/autopilot-design/references/owner-execution.md:119` resolves
  `../../roles/modes/design/_design_rules.md` under nonexistent
  `skills/roles/`;
- `skills/autopilot-spec/references/owner-execution.md:44` resolves
  `../autopilot-ship/SKILL.md` inside `skills/autopilot-spec/` rather than the
  sibling Skill.

Because the path fails before fragment lookup, the associated Markdown anchors
also cannot resolve. Claude-native and plugin copies reproduce the same broken
text.

Smallest correction: make the canonical owner-reference content location-aware
before mirroring. References to another file in the same `references/`
directory should drop the `references/` prefix; root-relative portable links
need one additional `..` on the canonical tree, while Claude projections need
an explicit `<agent-home>`/adapter-safe form where byte-identical relative paths
cannot resolve. Cross-Skill links need the extra parent step. Add a deterministic
path-and-anchor resolver over all 13 entries and all three owner trees to
`tools/entry-skill-layer.test.py`.

### 2. P0 — the draft-strategy authority backlink still targets the compact router

`skills/draft-strategy/references/delegate-prompt.md:162` names
`<agent-home>/adapters/claude/skills/autopilot-draft/SKILL.md` as the authority
for the paper paste-ready contract. That file is now intentionally only the
compact router and contains no such procedure. The generated Claude mirror has
the same stale backlink.

Smallest correction: point the backlink to the post-approval owner/reference
file that actually owns the cited section, then include this cross-reference in
the new link/anchor gate.

### 3. P1 — adaptation and footprint gates were not extended for the new layer

`tools/generate.py:18-20` registers the new
`tools/sync-entry-skill-layer.py`, and `tools/entry-skill-layer.test.py` is also
new, but the adaptation boundary has no projected/deferred decision for either.
The bounded boundary check reports:

- no projection decision for both files (twice across the boundary passes);
- missing `adapters/claude/tools/entry-skill-layer.test.py`;
- missing `adapters/claude/tools/sync-entry-skill-layer.py`.

These failures are caused by files introduced in this diff and are not part of
the planning baseline.

The strict footprint command passes, but `tools/context-footprint.py:21-24`
still defines only bootstrap, worker-bootstrap, and metadata budgets. It neither
derives the 13 entry routers nor emits/enforces max and aggregate entry-body
bytes for canonical, Claude, Codex, OpenCode, and plugin surfaces as required by
the approved plan. The standalone entry test cannot substitute for the required
static-footprint surface/baseline.

Smallest correction: classify both new tools in the adaptation inventory (use
the canonical-only/deferred class if projection is intentionally unnecessary,
otherwise add the required Claude projections), then extend
`context-footprint.py` and its checked baseline with the exact 13-entry max and
aggregate surfaces.

## Passing semantic checks

- Exactly 13 primary entry routers are manifest-derived; parent-invoked and
  model-support capabilities are excluded.
- All four Skill trees retain concrete manifest `Use when` and `Not for`
  boundaries and fit the 4,096/53,248-byte budgets.
- Canonical/Claude compact routers separate pre-approval routing from
  post-approval owner loading; Codex and OpenCode remain native compact
  projections and do not preload portable procedure detail.
- Starting-commit owner prose is lossless for all 13 entries after ignoring two
  leading blank lines only. The defect is path semantics, not missing prose.
- Root/Claude/plugin freshness is accepted by `tools/generate.py --check`;
  native Codex/OpenCode boundaries pass conformance.
- Runtime support/fallback, local projection, and physical masking remain
  distinct in the changed text. No token, billing, cost-savings, or ROI claim
  was introduced.
- Worker-bootstrap v5 files and hashes are unchanged; measured kernel and typed
  combinations remain 1,571 and 1,862–2,028 bytes.
- No tracked primary-checkout, fleet, dispatch, worker-bootstrap, worker-type,
  or runtime-bin behavior is changed by the task diff.

## Baseline classification and handoff

`tools/generated-projections.test.sh` stops at
`legacy artifact root was not selected for orientation`. The planning evidence
already classifies this as an unrelated existing baseline, so it is recorded
but is not the reason for FAIL. The broken moved references and adaptation
inventory failures are new and independently sufficient to fail the stage.

Recommended next action: return to `code-execute`/`code-refine` for the three
small corrections above, then rerun the full matrix and verify that the
mutation-based projection test restores the original source diff.
