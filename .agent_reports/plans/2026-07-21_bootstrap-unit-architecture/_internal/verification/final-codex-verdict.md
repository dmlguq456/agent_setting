CONFIRMED problems:

- `adapters/claude/skills/code-execute/SKILL.md:67 — active Claude Skill still invokes deleted dev-team — other Claude/plugin Skills likewise reference retired teams and agent-modes, causing runtime lookup failures.`
- `adapters/codex/bin/role-map.sh:92 — role aliases return deleted native-agent paths with available=1 — preflight role planning currently advertises nonexistent plan-team.toml.`
- `profiles/code-execute.yaml:10 — masked profiles expose deleted agents — build-home silently skips the missing target while specialization fragments still require the team.`
- `utilities/capability-route.py:285 — composed routes omit _validate_gate_contracts — a forged completion gate passes composition and verify, contradicting “same validator.”`
- `adapters/codex/bin/dispatch-headless.py:150 — --unit is optional and unbound to the sealed route node — all three wrappers can launch a bare or substituted persona; quick nodes synthesized at capability-route.py:331 contain no unit.`
- `tools/capability_topology.py:121 — reserved-unit roles are unchecked and unit_choices roles are checked only for the primary unit — _kernel/owner accepted fast implementer, and autopilot-refine already admits fast-fact-checker claim-verify under a fast-reviewer choice set.`
- `tools/check-adaptation-boundary.sh:1648 — CI guard still requires all retired team agents — .github/workflows/checks.yml:31 therefore fails on a clean checkout; check-unit-config.py is also unclassified at line 1398.`
- `tools/check-unit-config.py:31 — retired-reference scan covers only root skills/ and capabilities/ — active adapter Skills, profiles, bins, and plugin mirrors escape; the guard reports green despite the breakage above.`
- `tools/check-model-config.py:27 — memory-scout exemption is substring-wide — memory-scout-evil.toml is exempt, not just the exact kernel helper.`

Clean: 43 standard+ topology nodes all carry units; node units are hash-sealed; no depth-3 topology found. Canonical dispatch-node/fallback/capacity paths forward units. Security-review, design-maker/_design-rules, and figure-gen LAW spot-checks retained the named rules. Manifest v3 validation, kernel-only native-agent sync checks, and `tools/generate.py --check` passed.

Temp-directory-dependent tests could not be fully verified under the read-only sandbox. §0.4 user interaction is not provable from repository state.

FIX-NEEDED — biggest risk: active harness consumers still invoke deleted team personas, so production workers can fail or run without their sealed unit behavior.