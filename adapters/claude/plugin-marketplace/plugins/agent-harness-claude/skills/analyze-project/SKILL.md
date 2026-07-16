---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: analyze-project
description: "Use when persistent analysis of code, a paper, or a document must be created or refreshed because it is absent, stale, or explicitly requested. Not for read-only project orientation, context recovery, or status reporting."
argument-hint: "[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]"
metadata:
  group: pre
  fam: pre
  invocation_class: entry-router
  modes: ["code", "paper", "doc"]
  blurb: "Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery."
  use_when: "Use when persistent analysis of code, a paper, or a document must be created or refreshed because it is absent, stale, or explicitly requested."
  not_for: "Not for read-only project orientation, context recovery, or status reporting."
---

# analyze-project

This is a compact pre-approval entry router. Its manifest-owned frontmatter is
the authoritative discovery metadata; it intentionally contains no execution
procedure.

## Pre-approval boundary

Use only this router, `harness-manifest.json`, and `core/WORKFLOW.md §0.2` to
propose a route. Present the one-time confirmation in `core/WORKFLOW.md §0.4`
unless the same route and scope are already approved. Do not load references
before approval.

## Post-approval owner contract

After approval, direct/quick sessions and the `standard+` depth-1 owner load
`capabilities/analyze-project.md`, then use the Reference Index below. Assigned
stage workers load only their assigned stage contracts.

## Reference Index

| File | Load when | Obligation |
|---|---|---|
| [`references/owner-execution.md`](references/owner-execution.md) | After approval, by the selected direct/quick session or depth-1 owner | Read the complete execution procedure before material work. This is the router's only post-approval reference edge. |

## Guard pointer

Follow the portable artifact, worktree, role, and verification guards in the
selected owner contract. Runtime projections must report unsupported mechanics
and must not claim physical instruction masking, token, billing, or cost
savings without verified evidence.
