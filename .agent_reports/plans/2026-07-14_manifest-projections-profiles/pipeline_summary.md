# Manifest and profiles Phase 2 pipeline summary

Status: implementation, deterministic QA, and independent review complete;
git handoff pending.

Branch: `manifest-profiles-phase2`, based on `runtime-activation-phase1`.

The active cycle replaces adapter-derived metadata with a canonical product
manifest, consolidates generated projection checks behind one internal command,
and adds progressive runtime activation profiles without weakening kernel guards.

Delivered:

- strict `harness-manifest.json` schema and dependency/profile resolver;
- one `tools/generate.py [--check]` path for core generated projections;
- real starter/builder/full discovery filtering across three runtimes;
- builder default plus legacy-full state compatibility;
- native-first README and marketplace bundles outside core checks;
- spec v4 / Phase 2 complete handoff to Phase 3.
