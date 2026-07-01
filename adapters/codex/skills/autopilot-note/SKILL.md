---
name: autopilot-note
description: "Use when the user requests autopilot-note: 산출물 라우팅/노트화. digest와 triage 제안을 만든다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-note

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-note.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-note`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-note`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-note`
- Supported modes: `none`
- Argument shape: `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--qa quick|light|standard|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>] [--no-fact-check]`
- Portable meaning: 산출물 라우팅/노트화. digest와 triage 제안을 만든다.

## Portable Contract

- Invocation semantics: Autopilot family — periodic + on-demand 산출물 routing pipeline (2-Layer 모델). Scans `<artifact-root>/{research,documents,plans,analysis_project}/` + `experiments/` + `git log` for artifacts changed since last run, then turns each into a **Layer 2 산출물 노트** under `<agent-notes-root>/_layer2/notes/<id>.md` and links it to the user's **Layer 1** board cards under `<agent-notes-root>/cards/`. 5-way routing — create L2 note row (auto), link note `card_id` → existing L1 card (auto-PROPOSE as `routing_status: inbox` with `routing_confidence`/`routing_reason`; unattended cron NEVER auto-confirms — user confirms in `/triage`), link `backbone_ids`/`task_ids` → L2 catalog (auto, emerge if needed), propose new L1 card (triage), park as ambient `card_id: null` note (auto fallback). Daily digest accumulates at `<agent-notes-root>/digests/YYYY-MM-DD.md`. Idempotent — same source processed twice never duplicates a note. Default `--qa light` (routine cron). Escalate to standard+ for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 includes Notion mirror (Phase 3, gated). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

The capability has two output surfaces: `<artifact-root>/notes/<date>/` for the
run log/reviewer artifacts, and `<agent-notes-root>/` for the cross-project board
state. The latter is mutable continuity state, not harness source. Adapter
defaults for resolving `<agent-notes-root>` belong in adapter-native files.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-note [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-note [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
