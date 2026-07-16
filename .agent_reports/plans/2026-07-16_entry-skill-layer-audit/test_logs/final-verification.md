# Entry Skill Layer — Final Verification

Date: 2026-07-16
Source commit: `22b9fe1b`
Verdict: **PASS**

| Check | Result | Evidence |
|---|---|---|
| `python3 tools/generate.py --check` | PASS | manifest current; 12 core projection groups current |
| `python3 tools/entry-skill-layer.test.py` | PASS | 13 entries on canonical, Claude, Claude plugin, Codex, OpenCode; one owner edge; links resolve |
| `bash tools/skill-conformance/check.sh` | PASS | 27 invocation classifications and all runtime trees conform |
| `sh tools/routing-contract.test.sh` | PASS | semantic primary routing, five-field gate, stage boundaries pass |
| strict `tools/context-footprint.py` | PASS | canonical/Claude/plugin 29,828 total, 2,448 max; no warnings |
| `python3 tools/capability_topology.test.py` | PASS | 8 tests |
| `sh tools/check-adaptation-boundary.sh` | PASS | documented warning: 91 concrete Claude/model references |
| `sh tools/generated-projections.test.sh` | PASS | two-run determinism, stale-edit rejection, 13-entry gate, 29 figure tests |
| Python/shell syntax + `git diff --check` | PASS | no syntax or whitespace error |
| Codex runtime projection strict check | PASS | profile builder, native discovery, hook trust `ok`, `session_end=stop-alias` |
| Codex/OpenCode `capability-info` | PASS | native Skill 13/13 for each adapter |
| independent read-only final review | PASS | initial CommonMark finding fixed; final findings none |
| protected worker-bootstrap/runtime surfaces | PASS | unchanged from `23c86bea` |

## Baseline-only incompatibilities

- `skill-creator/scripts/quick_validate.py` rejects existing `argument-hint`
  frontmatter in both `23c86bea` and the final tree.
- Earlier isolated `/tmp` archive projection runs fail identically on base and
  current artifact-root orientation; the canonical linked-worktree run passes.
