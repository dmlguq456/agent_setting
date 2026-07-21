architecture-spec.md:12-13,27-46,62 — native projection cardinality is undefined — current generators emit one fixed-model agent per manifest role (`sync-native-agents.py:273-280`), while each role aggregates many mode-units (`harness-manifest.json:574-713`). The spec defines neither unit→team aggregation nor per-mode model selection; emitting one native agent per unit changes behavior.

architecture-spec.md:33-37; current-state-map.md:102-107 — `write_scope` is wrongly unit-owned — dispatch scope is route/node-specific, while native permissions are agent-specific. Unifying them covertly merges lifecycle policy and leaves conflicting authorities.

architecture-spec.md:61,108,120-122 — “capability LAST” is not executable — Phase 1 makes runtime `compose()` consume units, but `node.unit` arrives only in Phase 4 because role+kind is non-unique. Today `render_worker_bootstrap()` receives only worker type (`worker_bootstrap.py:95-103`).

architecture-spec.md:94 — cross-validator is incomplete — it checks existence and role equality, but not `capability.requires.units` membership or `node.kind` compatibility with unit `worker_type`; a wrongly wired same-role unit passes.

architecture-spec.md:100-103 — Phase 0 cannot be behavior-neutral — primary/plugin `qa-team.md:5` select different models. Single-sourcing necessarily changes one surface; byte identity to both baselines is impossible.

architecture-spec.md:105-110; current-state-map.md:58-59 — QA is not the “most mechanical” pilot — the phase includes MODERATE+ security-review and HIGH ml-debug while simultaneously introducing schema, runtime composition, and guards.

architecture-spec.md:108,137 — hot-path safety is asserted, not designed — no runtime unit encoding, generated artifact, import boundary, or dependency test preserves today’s stdlib-only bootstrap.

architecture-spec.md:98 — reversibility is unproven — no reverse projection can recreate both already-divergent persona trees; only VCS rollback is apparent.

Genuinely clean: Decision 11 preserves dispatch syntax/lifecycle; branch preservation, capability/unit separation, security silence nuance, family floors, and dual 48-kHz gate placement match the investigation.

FIX-NEEDED — biggest risk: the missing mode-unit-to-native-team aggregation and model contract.