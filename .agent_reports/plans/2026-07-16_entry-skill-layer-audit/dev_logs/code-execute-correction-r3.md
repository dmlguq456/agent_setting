# Code-execute correction pass — entry Skill layer

Date: 2026-07-16  
Stage: `code-execute` correction pass  
Worktree: `/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit`

## Corrections

1. Updated `tools/sync-entry-skill-layer.py` so moved owner content keeps a
   one-level reference layout: adjacent reference paths are normalized, sibling
   Skill links gain one parent, and portable-root links use the runtime-stable
   `<agent-home>` form. Canonical, Claude-native, and Claude-plugin copies now
   resolve from their actual owner-document locations.
2. Extended `tools/entry-skill-layer.test.py` with deterministic link and
   anchor resolution across all 13 manifest-derived owner documents on the
   canonical, Claude-native, and Claude-plugin trees.
3. Retargeted the draft-strategy paste-ready authority backlink to the
   post-approval `autopilot-draft` owner-contract section and refreshed its
   Claude/plugin mirrors.
4. Classified `sync-entry-skill-layer.py` and `entry-skill-layer.test.py` as
   portable canonical-only/deferred tool helpers in the adaptation inventory
   and adaptation-boundary decision lists.
5. Added strict manifest-derived 13-entry aggregate/max UTF-8-byte surfaces
   for canonical, Claude, Claude plugin, Codex, and OpenCode trees, with exact
   baseline values. Static bytes remain input-size measurements only; no token,
   billing, cost, or savings claim was added.

## Generation and verification

All generated outputs were refreshed through `PYTHONDONTWRITEBYTECODE=1
python3 tools/generate.py`.

| Command | Result |
|---|---|
| `python3 tools/entry-skill-layer.test.py` | PASS — 13 routers and 3 owner trees resolve links/anchors |
| `python3 tools/context-footprint.py --root . --skip-runtime --skip-hooks --timeout 30 --strict` | PASS — exact totals/maxima; no warnings |
| `python3 tools/generate.py --check` | PASS — 12 projection groups current |
| `sh tools/check-adaptation-boundary.sh` | PASS (existing documented portable-reference warning only) |
| `bash tools/skill-conformance/check.sh` | PASS |
| `sh tools/routing-contract.test.sh` | PASS |
| `python3 tools/capability_topology.test.py` | PASS — 8 tests |
| `git diff --check 23c86beaa613571a583f65e869da6b72013a2ad4` | PASS |

## QA/runtime notes

`preflight.sh qa-policy thorough code` required thorough assurance and reported
the depth-2 fallback: no additional independent reviewer was dispatched. This
stage corrected the independent code-test findings inline and made no commit or
push. Worker-bootstrap and worker-type files were not changed.
