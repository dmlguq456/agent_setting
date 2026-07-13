---
name: autopilot-note
description: "Use for autopilot-note: 산출물 라우팅/노트화. digest와 triage 제안을 만든다."
metadata:
  portable_source: capabilities/autopilot-note.md
  adapter: opencode
---

# autopilot-note

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-note.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-note`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-note`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-note`
- Supported modes: `none`
- Argument shape: `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]`
- Portable meaning: 산출물 라우팅/노트화. digest와 triage 제안을 만든다.

## Portable Contract

- Invocation semantics: Autopilot family — periodic + on-demand 산출물 routing pipeline (2-Layer 모델). Scans `<artifact-root>/{research,documents,plans,analysis_project}/` + `experiments/` + `git log` for artifacts changed since last run, then turns each into a **Layer 2 산출물 노트** under `<agent-notes-root>/_layer2/notes/<id>.md` and links it to the user's **Layer 1** board cards under `<agent-notes-root>/cards/`. 5-way routing — create L2 note row (auto), link note `card_id` → existing L1 card (auto-PROPOSE as `routing_status: inbox` with `routing_confidence`/`routing_reason`; unattended cron NEVER auto-confirms — user confirms in `/triage`), link `backbone_ids`/`task_ids` → L2 catalog (auto, emerge if needed), propose new L1 card (triage), park as ambient `card_id: null` note (auto fallback). Daily digest accumulates at `<agent-notes-root>/digests/YYYY-MM-DD.md`. Idempotent — same source processed twice never duplicates a note. Routine cron defaults to `quick` intensity and its derived verification rigor. Escalate intensity to `standard+` for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 includes Notion mirror (Phase 3, gated). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-note [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
