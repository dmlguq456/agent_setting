---
name: autopilot-lab
description: "Use when needed: Rapid experiment prototyping around training setup and checkpoint evaluation/analysis."
---

# autopilot-lab

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-lab.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-lab`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-lab`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-lab`
- Supported modes: `setup, eval`
- Argument shape: `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`
- Portable meaning: Rapid experiment prototyping around training setup and checkpoint evaluation/analysis.

## Portable Contract

- Invocation semantics: Rapid experiment prototype entrypoint. The user runs heavy training; the lab supports the work before and after it. `setup` prepares an experiment from spec to scaffold and run commands. `eval` analyzes a trained checkpoint through metrics, ablations, paper comparisons, plots, and optional formal reports (prose routes to autopilot-draft; audio/media uses playback HTML). Extension cases use `--parent <slug>` rather than new modes: fine-tuning creates a setup config branch, and reevaluation uses eval. Enforce per-experiment folders, a STORY narrative, and an append-only `_RUNLOG` timeline with pending/completed state and parent links to prevent overwrites and ad hoc loss. Automatically read `experiment_conventions.md` and `similar_models.md` from analyze-project, giving the user's existing layer, prefix, and config patterns priority. Graduate refinement or library work to autopilot-code. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Routing Boundary

Full-run entry is gated by a current hash-bound smoke attestation and detached
resource-run identity. Evaluation reports use one `report_manifest.json`
validated by `tools/report-manifest-verify.py` for Markdown and HTML outputs,
48 kHz/full-band media, summary statistics, hashes, 1:1
audio/waveform/spectrogram/playback sets, and visual evidence. The legacy
figure-semantic verifier remains a compatibility checker, not a second report
manifest.

`autopilot-lab` owns new empirical work: training setup, checkpoint
reevaluation, metric/ablation computation, and experiment figure/media
generation. Under `WORKFLOW §0.2`, a request containing such work keeps
`autopilot-lab` as the primary capability even when phrased as a document
update. `autopilot-refine` corrects existing document surfaces only;
`autopilot-spec` records evaluation-policy or blueprint changes without
executing them; formal prose assembly hands off to `autopilot-draft`; final
routing and registration belong to `autopilot-note`. None of these secondaries
replaces the lab execution, and lab does not absorb their artifact ownership.

## Mode-Specific Semantics

| Mode | Required coverage |
|---|---|
| `setup` | Experiment spec, scaffold, run commands, pending `_RUNLOG` row, birth `run.json`. |
| `eval` | Eval spec, evaluation execution or guidance, metrics and per-array analysis, figures/media, report, `_RUNLOG` completion, lineage finalization. |

### Eval execution topology (`standard+`)

The separable stages of a `standard+` eval are: (1) context and experiment
contract, (2) evaluation harness preparation, (3) checkpoint evaluation run,
(4) metrics and per-array analysis, (5) figures, audio, and playback HTML,
(6) formal report assembly, (7) independent verification, and (8) spec/note
sync. Group stages into workers by file ownership and dependency rather than
opening one session per stage:

| Worker | Owns (write) | Typical stages |
|---|---|---|
| eval worker | eval harness, raw metrics (`metrics.jsonl`, `run.json`), `_RUNLOG` row | 2–4 |
| media worker | `figures/`, audio segments, playback `report/*.html` | 5 |
| report worker | `REPORT.md`, `STORY.md`, `summary.md` | 6 |
| verification worker | read-only checks; verdict artifact only | 7 |
| spec/note sync | `autopilot-spec` update and `autopilot-note`, after results are final | 8 |

The main session or its depth-1 conductor applies the `WORKFLOW §0.3`
pre-execution gate before the checkpoint evaluation run, dispatches workers
under `OPERATIONS §5.10`, and stays in the flow: liveness watching and harvest
are part of the same work, not a fire-and-forget dispatch. Reevaluation always
uses `--parent <slug>` lineage and the append-only `_RUNLOG`. Running a
separable stage inline requires the recorded reason in the experiment
`_RUNLOG` or `_internal/`.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-lab [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
