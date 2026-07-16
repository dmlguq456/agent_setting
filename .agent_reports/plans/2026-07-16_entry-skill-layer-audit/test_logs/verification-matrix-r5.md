# Entry Skill Layer — code-test retry r5 verification matrix

Verdict: **PASS**. This registered test worker was independent of execute; it
made no unsupported claim that the optional 2-deep/2-fast upper bound ran.
The source status remained stable at 110 rows with SHA-256
`334571c60e7355b098a40b61a5e875a69d2cc7dce3220a3d1ecaa328d5fa122f`.

| Surface | Result |
|---|---|
| Exact owner/topology sets | PASS: exactly 13 invocation-class entry routers have self-targeting owner rows; topology remains exactly the ten group-entry capabilities |
| Portable layering | PASS: design principles and capability catalog define router → owner → assigned-stage separation and exclude parent/model-support candidates |
| `tools/generate.py --check` | PASS |
| Two-run generation determinism | PASS; matching tree hash `bf85cc9d1a114654553546fdfbccde47289818d3c14c3d7a2d8a5d2833c4cc14` |
| Skill conformance / entry-layer gate | PASS |
| Routing / topology / strict footprint | PASS |
| Adaptation boundary | PASS with the documented 91-reference warning |
| Python and shell syntax / diff hygiene | PASS |
| Owner-body losslessness | PASS: 12 exact; autopilot-draft insertion-only +14 lines; 39 projected owner documents identical by tree |
| Owner/delegate paths and anchors | PASS across canonical, Claude-native, and Claude-plugin trees |
| Worker-bootstrap v5 and deny zones | PASS; unchanged bytes/hashes and no protected source changes |
| Primary checkout | PASS: no tracked or staged source changes; canonical cycle artifacts only |
| Generated projections, current | Known baseline failure: `legacy artifact root was not selected for orientation` |
| Generated projections, starting commit | Identical first failure and message; unchanged unrelated baseline |

Exact router footprints remained 13 entries per surface: canonical/Claude/
Claude-plugin 26,825 total and 2,217 max; Codex 35,173/2,843; OpenCode
33,717/2,731. All 65 descriptions matched manifest routing metadata. Static
bytes are input-size evidence only; no masking, token, billing, cost, savings,
or ROI inference is made.
