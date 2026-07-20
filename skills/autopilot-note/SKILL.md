---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: autopilot-note
description: "Use when existing artifacts must be collected, digested, triaged, or routed into a durable note workflow. Not for storing one scoped memory item or for performing the primary research, code, or document work."
argument-hint: "[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]"
metadata:
  group: entry
  fam: ops
  invocation_class: entry-router
  modes: []
  blurb: "Route and note artifacts, producing digests and triage proposals."
  use_when: "Use when existing artifacts must be collected, digested, triaged, or routed into a durable note workflow."
  not_for: "Not for storing one scoped memory item or for performing the primary research, code, or document work."
---

# autopilot-note

This is a compact pre-approval entry router. Its manifest-owned frontmatter is
the authoritative discovery metadata; it intentionally contains no execution
procedure.

## Pre-approval boundary

Use only this router, `harness-manifest.json`, and `core/WORKFLOW.md §0.2` to
propose a route. Present the one-time confirmation in `core/WORKFLOW.md §0.4`
unless the same route and scope are already approved. Do not load references
before approval.

## Post-approval owner contract

After approval, direct/quick sessions and the `standard+` dispatch-depth-1 owner load
`capabilities/autopilot-note.md`, then use the Reference Index below. Assigned
stage workers load only their assigned stage contracts.

## Reference Index

| File | Load when | Obligation |
|---|---|---|
| [`references/owner-execution.md`](references/owner-execution.md) | After approval, by the selected direct/quick session or dispatch-depth-1 owner | Read the complete execution procedure before material work. This is the router's only post-approval reference edge. |

## Guard pointer

Follow the portable artifact, worktree, role, and verification guards in the
selected owner contract. Runtime projections must report unsupported mechanics
and must not claim physical instruction masking, token, billing, or cost
savings without verified evidence.
