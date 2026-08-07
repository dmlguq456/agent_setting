---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: post-it
description: "Use when the acting agent needs to store, retrieve, resolve, hand off, or promote a scoped working-memory item in support of current work. Not for primary task routing, broad artifact triage, or replacing the capability that owns the current work."
argument-hint: "[show] | add <category> <text> | resolve <hint> | decide <text> | handoff [--no-confirm] | sweep [--no-confirm] | promote [<hint>] [--scope project|user [<aspect>]]"
metadata:
  group: ops
  fam: ops
  invocation_class: model-support
  modes: []
  blurb: "Store project/cross-project notes and handoffs in working memory."
  use_when: "Use when the acting agent needs to store, retrieve, resolve, hand off, or promote a scoped working-memory item in support of current work."
  not_for: "Not for primary task routing, broad artifact triage, or replacing the capability that owns the current work."
---

# post-it

## Purpose

Maintain a user-controlled working-memory surface distinct from automatic project memory under `<agent-home>/projects/*/memory/`. The primary mutation path is an explicit `post-it` action. The acting agent may also record a note when the proactive-nudge contract in [references/nudge-and-boundaries.md](references/nudge-and-boundaries.md) clearly applies; this is a judgment based on task relevance, not a fixed language signal.

Treat a post-it as temporary. Durable truth belongs in source artifacts such as `plans/`, `documents/`, `spec/`, code, git history, and structured profile records. Use post-its only to bridge work that still needs to remain salient across sessions, then remove or promote them when their information graduates.

## Invariants

- The user should not need to inspect post-it records line by line. Keeping the store lean and pruning graduated records are agent responsibilities.
- During automatic nudges, remove only clearly graduated or stale records and report one concise summary; keep ambiguous records.
- Ask only whether an action should be stored when confirmation is required. Show line-level sweep previews only for an explicit `post-it sweep` request.
- Every entry eventually graduates or expires; do not build a permanent unstructured archive.

## Unified Store

Post-its use the project-scoped working tier in the unified [memory store](../../tools/memory/README.md), backed by `memory.db` in SQLite WAL mode.

- write working records with `mem note` or `mem add`
- search with `mem recall`
- manage working lifecycle with `mem lifecycle`
- inject the working tier with `python3 <agent-home>/tools/memory/mem.py inject --hook` when the active session contract explicitly calls for it

Post-it sweep and store expiration are related but distinct. Post-it flags at least 30-day stale and 90-day archive candidates for human review, while the store may automatically expire working records according to configured `WORKING_TTL_DAYS` (currently 21 days in this contract).

## Quick Contract

This file routes actions; load the references for lifecycle and mutation details.

- **Scopes**: `project` is the cwd-scoped DB working tier. `user <aspect>` writes the exact compatibility section `## 사용자 수동 메모` in a profile record. Read `references/lifecycle-and-scope.md` for scope and aspect selection.
- **Lifecycle**: every record is live, graduated, or stale. Read `references/lifecycle-and-scope.md` for the five-category taxonomy and aging rules.
- **Actions**: `show`, `add`, `resolve`, `decide`, `sweep`, `promote`, and `handoff`. Read `references/sub-actions.md` for procedures and confirmation policy.
- **Writing**: keep one dense line per bullet under the style contract in `references/nudge-and-boundaries.md`.

Memory retrieval, promotion, and cleanup remain context-sensitive decisions within those data and lifecycle contracts. Do not invent deterministic recall phrases or infer user-profile truth from language alone.

## Reference Index

| File | Load when | Contents |
|---|---|---|
| `references/lifecycle-and-scope.md` | Every invocation | Live/graduated/stale lifecycle; project versus user scope; aspect selection; `analyze-user` separation; two-writer contract; artifact guard; DB commands; five-category taxonomy and aging |
| `references/sub-actions.md` | Running any mutation action | Complete show, add, resolve, decide, sweep, promote, and handoff procedures; read-modify-write rules; confirmation table |
| `references/nudge-and-boundaries.md` | Considering automatic recording or writing a record | Proactive-nudge judgment, auto-memory boundary, exclusions, and concise writing style |

## Language Rule

Use the conversation language for user-facing summaries unless an explicit audience language overrides it. Preserve working-record bodies in the user's original language; mixed-language content is valid. Keep commands, profile stems, IDs, categories, paths, and the exact compatibility heading unchanged.

## Task

Parse `$ARG`:

- empty or `show` → preview cwd-scoped DB working records; when empty, explain the `post-it add` form
- `add <category> <text>` → write a working record with `mem note`
- `resolve <hint>` → fuzzy-resolve the advisory thread record
- `decide <text>` → write a decision record
- `sweep [--no-confirm] [--scope ...]` → compare artifacts and records, then graduate, flag stale, or expire according to the selected policy
- `promote [<hint>] [--scope user [<aspect>]]` → promote a user note into the structured profile section through read-modify-write
- `handoff [--no-confirm]` → prepare the sweep proposal, session summary, and hint record
- with `--scope user [<aspect>]` → target `mem profile <stem>` and `mem add ... --source user-profile:<stem>`; write the profile record directly under its two-writer contract
- otherwise → show concise usage guidance
