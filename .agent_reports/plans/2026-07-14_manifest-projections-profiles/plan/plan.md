---
status: completed
created: 2026-07-14
spec: .agent_reports/spec/harness-productization/prd.md
intensity: standard
qa: standard
---

# Canonical Manifest, Generated Projections, and Profiles — Phase 2

## Goal

Replace adapter-derived metadata and manual catalog duplication with one
versioned canonical manifest, one deterministic build/check entrypoint, and
three progressive runtime profiles. Keep runtime-specific behavior and
fallbacks adapter-owned, while making metadata drift mechanically impossible.

## Decisions

- Add `harness-manifest.json` as the canonical, stdlib-readable product
  manifest. Keep root `manifest.json` as a generated compatibility view for
  existing consumers.
- The canonical manifest owns capability, role, mode, dependency, pack, and
  profile metadata. Capability procedure bodies and adapter runtime mappings
  remain in their current source files.
- Use `tools/generate.py [--check]` as the only documented build/check entry.
  Existing `sync-native-*` scripts remain internal generator components and
  are not user-facing capabilities.
- Generate catalog tables and capability contract blocks from the manifest.
  Fully generated runtime files are byte-checked; Claude's native Skill bodies
  retain adapter-owned prose while their generated frontmatter is checked.
- Define local-only packs `core`, `software`, `research-writing`, `design`, and
  `operations`. Profiles compose these packs: `starter`, `builder`, `full`.
- Select `builder` as the new activation default after isolated smoke tests.
  Activation records persist the selected profile; legacy Phase 1 activation
  records without a profile continue as `full`.
- Kernel instructions, guards, hook/config surfaces, source-of-truth rules, and
  memory-scout stay active in every profile. Profiles filter discoverable
  capabilities, dependent roles, and mode guides only.

## Implementation

1. Add a strict canonical manifest loader/validator and profile resolver.
2. Refactor manifest/catalog and three runtime native generators to consume
   canonical metadata, with one orchestrating `generate.py` command.
3. Add Claude generated-frontmatter checking without replacing adapter-owned
   Skill procedure bodies.
4. Add `--profile starter|builder|full` to runtime activation, status, refresh,
   doctor, and installer entry parsing; filter runtime discovery entries by the
   resolved profile and preserve profile in activation state.
5. Add isolated-HOME profile tests for all three runtimes, legacy full-state
   compatibility, dependency closure, starter size, deterministic generation,
   stale/manual generated edit rejection, and a representative metadata change.
6. Replace README maintainer sync instructions with profile-oriented install,
   doctor, and golden-task quickstart.

## Verification

- `python3 tools/generate.py --check`
- `python3 -m py_compile tools/*.py tools/install/*.py tools/install/drivers/*.py adapters/*/bin/*.py`
- `sh tools/install/runtime-activation.test.sh`
- `sh tools/install/profile-activation.test.sh`
- `sh tools/check-adaptation-boundary.sh`
- portable guard and skill-conformance suites reported by adapter doctor
- `git diff --check`

## Risks

- `profiles/` already names dispatch model profiles. Product activation
  profiles stay in `harness-manifest.json` and CLI output; no second profile
  directory is introduced.
- Filtering a role too aggressively can leave a capability without its worker.
  Resolver validation closes capability and role dependencies before projection.
- Generated ownership must not overwrite runtime-specific fallback prose.
  Partial-generation boundaries are explicit and checked independently.
- Existing Phase 1 activation state has no profile field. Missing profile is
  interpreted as `full`, while genuinely new activation defaults to `builder`.

## Result

Implemented the manifest, generator, profile activation, native-first README,
and plugin-outside-core verification boundary. The Phase 2 exit gate passed;
the productization spec advanced to v4 with Phase 3 as the next cycle.
