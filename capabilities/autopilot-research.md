# Capability: autopilot-research

This is the portable capability contract for `autopilot-research`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-research` |
| Group | `entry` |
| Supported modes | `academic, technology, market` |
| Portable meaning | 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다. |
| Argument shape | `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]` |

## Invocation Semantics

Research survey pipeline — _세 family 의 공통 사전_ entry. academic (논문 survey·trend·필드 정리) / technology (라이브러리·프로젝트·스택·코드 baseline 비교) / market (시장·경쟁·reference 앱·UX 패턴) 3 mode. 다운스트림 매핑: academic → autopilot-draft (paper/presentation) + autopilot-code (academic baseline 코드) | technology → autopilot-code (라이브러리·연구 baseline 위) + autopilot-spec (스택·reference 패턴) | market → autopilot-draft (proposal/report) + autopilot-spec (reference 앱 UX). Field intelligence only — 실제 문서·코드·앱 생성은 다운스트림 skill 이 담당.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.

Research work writes to `<artifact-root>/research/<topic>/`.

Required public artifacts:

- `pipeline_state.yaml`: query, mode, depth, intensity, QA override, resume stage, and artifact path;
- `pipeline_summary.md`: source coverage, findings, QA result, and downstream recommendations;
- report chapters at the research root, named by mode;
- `cards/` for paper/project/company/source cards when the mode produces cards;
- `analysis_summary.md` when the analyze stage produces cross-source synthesis.

Internal artifacts belong under `_internal/`, including raw search metadata, source JSON, browser extracts, reference-chaining logs, code search notes, review records, and retry scratch files.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Minimum role mapping:

- source search and retrieval: research/material role;
- analysis and synthesis: research role;
- fact/citation verification: QA or research-review role;
- editorial cleanup of final chapters: editorial role when available;
- downstream handoff: planning role for spec/code/draft routing.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. QA level is an assurance override for plan-check, selected independent reviews, and final verify; it does not name a model or choose the stage graph.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

Additional research-entry gates:

- ask one scope-clarification round when the query is too broad, too short, or matches multiple modes, unless `--no-clarify` or resume mode is active;
- keep raw source metadata in `_internal/`; public reports should cite or summarize, not expose noisy scrape output;
- stop with a failed `pipeline_summary.md` when search returns no useful sources;
- for `standard` and above, verify card-level facts such as title, venue, year, citation, metric, and quoted claims against sources;
- for `adversarial`, run an independent contradiction/claim check before finalizing public-facing reports;
- do not create code, specs, apps, or prose deliverables directly; hand off to downstream capabilities after field intelligence is complete.

## Portable Procedure

1. Parse query, mode, depth, intensity, QA override, optional `--from`, and skip flags.
2. Resolve or create `<artifact-root>/research/<topic>/`; if resuming, read `pipeline_state.yaml`.
3. Infer mode when omitted and ask scope clarification when required.
4. Build search queries, including 2-3 synonym or alternate-phrase expansions.
5. Search mode-appropriate sources and write raw metadata under `_internal/`.
6. Analyze results into cards, chaining/code/source summaries, and `analysis_summary.md` as applicable.
7. Generate mode-specific report chapters.
8. Run QA verification according to level.
9. Update `pipeline_state.yaml` after each completed stage and finish with `pipeline_summary.md`.

## Mode-Specific Semantics

| Mode | Search/source emphasis | Public report set |
|---|---|---|
| `academic` | Papers, citation graphs, datasets, baselines, implementations, model resources. | briefing, landscape, core papers, baselines, technical deep dive, datasets, implementation, resources, reading guide. |
| `technology` | Standards, vendor docs, technical whitepapers, OSS implementations, deployment constraints. | briefing, landscape, standards/specs, vendor comparison, technical deep dive, deployment, implementation, resources. |
| `market` | Analyst/news/company/investor sources, product positioning, adoption and business signals. | briefing, market overview, key players, trends, opportunities. |

Mode inference should report its basis. If multiple modes match, resolve via clarification unless the user explicitly supplied `--mode`.

## Downstream Handoff

Field intelligence ends with recommendations for downstream work:

- `academic`: hand off to `autopilot-draft` for papers/presentations or `autopilot-code` for baseline implementation;
- `technology`: hand off to `autopilot-spec` for stack/reference decisions or `autopilot-code` for implementation on a selected baseline;
- `market`: hand off to `autopilot-draft` for business/report writing or `autopilot-spec` for reference-app/UX decisions.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-research/SKILL.md` and `skills/autopilot-research/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-research/SKILL.md`, while `skills/autopilot-research/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-research`. Use `adapters/codex/skills/autopilot-research/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/autopilot-research/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/autopilot-research/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-research`. Use `adapters/opencode/skills/autopilot-research/SKILL.md` and `adapters/opencode/commands/autopilot-research.md` as native OpenCode projections; do not consume `skills/autopilot-research/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-research/SKILL.md` and `adapters/claude/skills/autopilot-research/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-research/SKILL.md`, while `skills/autopilot-research/SKILL.md` remains the compatibility reference kept for parity/drift checks.
