# Capability: autopilot-note

This is the portable capability contract for `autopilot-note`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-note` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | 산출물 라우팅/노트화. digest와 triage 제안을 만든다. |
| Argument shape | `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--qa quick|light|standard|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>] [--no-fact-check]` |

## Invocation Semantics

Autopilot family — periodic + on-demand 산출물 routing pipeline (2-Layer 모델). Scans `<artifact-root>/{research,documents,plans,analysis_project}/` + `experiments/` + `git log` for artifacts changed since last run, then turns each into a **Layer 2 산출물 노트** (`_layer2/notes/<id>.md`) and links it to the user's **Layer 1** board cards. 5-way routing — create L2 note row (auto), link note `card_id` → existing L1 card (auto-PROPOSE as `routing_status: inbox` with `routing_confidence`/`routing_reason`; unattended cron NEVER auto-confirms — user confirms in `/triage`), link `backbone_ids`/`task_ids` → L2 catalog (auto, emerge if needed), propose new L1 card (triage), park as ambient `card_id: null` note (auto fallback). Daily digest accumulates at `<target>/digests/YYYY-MM-DD.md`. Idempotent — same source processed twice never duplicates a note. Default `--qa light` (routine cron). Escalate to standard+ for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 includes Notion mirror (Phase 3, gated).

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-note` currently projects compatibility source `skills/autopilot-note/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-note`. Do not consume `skills/autopilot-note/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-note/SKILL.md` while this capability is being split into portable and adapter-native layers.
