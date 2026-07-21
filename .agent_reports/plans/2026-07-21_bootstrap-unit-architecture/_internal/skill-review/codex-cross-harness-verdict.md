- `utilities/worker_bootstrap.py:116-128; adapters/codex/bin/dispatch-headless.py:486-495; adapters/codex/skills/code-plan/SKILL.md:34-58` — “~80% scaffolded” is overstated — 30/38 nodes fall back to the entry capability because no matching sub-capability exists; even mapped Codex stage Skills contain little executable procedure. The portable unit catalog is substantially missing.

- `adapters/codex/agents/{plan,qa,dev,research,design,material,editorial}-team.toml:1-30; adapters/codex/README.md:218-221` — “team reification is Claude-adapter-only” is false — Codex projects these labels as real native custom subagents, selected through `role-map.sh:36-100`.

- `capabilities/topologies.json:46-48; tools/capability_topology.py:198-202; adapters/codex/bin/preflight.sh:260-280` — “report-only means the legacy path is authoritative” is unproven — the pin is real and test-locked, but `legacy_low_level_dispatch` has no consumer, while preflight actively exposes route compilation and node dispatch. Promotion is not a safe flag flip because rollout semantics are internally contradictory.

- `tools/capability_topology.py:36-44; harness-manifest.json:14-78` — entry coverage is overstated — exact topology coverage includes only `group == entry`; `analyze-project`, `analyze-user`, and `audit` are also `entry-router` Skills but have no recipes.

- `capabilities/topologies.json:188-194` — “one blob per capability×mode” overstates explosion — 22 mode keys collapse into 11 recipes; code, draft, research, and spec already share graphs across modes.

- synthesis §breaks(B) — the literal “40+ `Agent(subagent_type=...)`” count is not verified — canonical Claude Skills contain 16 exact literals (18 `subagent_type` lines). Broader team-invocation prose is pervasive, so the architectural problem remains.

Independently CONFIRMED: 11 fully inlined recipes/38 nodes, no `$ref` or unit library; only 8/38 gates match 13 sub-Skills; two duplicated fallback arrays; unknown capability/mode hard-fails; route nodes are deep-copied at `capability-route.py:304`, sealed at `:342`, and verified at `:352`; no classification fallback exists.

CODEX-SIDE: node → `dispatch-node.py` → Codex headless wrapper → assigned Skill is hash-bound and routing-free. The direction holds conceptually, but Codex also needs team de-reification and real unit contracts.

SOUND-BUT-HARD — biggest risk: inventing portable executable unit contracts without weakening the route seal, artifact gates, or depth-2 ceiling.