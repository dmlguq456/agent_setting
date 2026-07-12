---
name: autopilot-research
description: "Use for autopilot-research: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다."
---

# autopilot-research

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-research.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-research`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-research`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-research`
- Supported modes: `academic, technology, market`
- Argument shape: `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`
- Portable meaning: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다.

## Portable Contract

- Invocation semantics: Research survey pipeline — _세 family 의 공통 사전_ entry. academic (논문 survey·trend·필드 정리) / technology (라이브러리·프로젝트·스택·코드 baseline 비교) / market (시장·경쟁·reference 앱·UX 패턴) 3 mode. 다운스트림 매핑: academic → autopilot-draft (paper/presentation) + autopilot-code (academic baseline 코드) | technology → autopilot-code (라이브러리·연구 baseline 위) + autopilot-spec (스택·reference 패턴) | market → autopilot-draft (proposal/report) + autopilot-spec (reference 앱 UX). Field intelligence only — 실제 문서·코드·앱 생성은 다운스트림 skill 이 담당. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

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


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-research [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-research [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
