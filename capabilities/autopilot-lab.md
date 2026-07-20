# Capability: autopilot-lab

This is the portable capability contract for `autopilot-lab`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `autopilot-lab` |
| Group | `entry` |
| Supported modes | `setup, eval` |
| Portable meaning | Rapid experiment prototyping around training setup and checkpoint evaluation/analysis. |
| Argument shape | `<task description> [--mode setup\|eval\|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct\|quick\|standard\|strong\|thorough\|adversarial] [--report] [--from spec\|scaffold\|run\|eval\|summary]` |
| Execution topology | `staged+resource`; registry `capabilities/topologies.json` |
| Entry load phase | `post-approval`; owner contract `capabilities/autopilot-lab.md` |

## Invocation Semantics

Rapid experiment prototype entrypoint. The user runs heavy training; the lab
supports the work before and after it. `setup` prepares an experiment from spec
to scaffold and run commands. `eval` analyzes a trained checkpoint through
metrics, ablations, paper comparisons, plots, and optional formal reports
(prose routes to autopilot-draft; audio/media uses playback HTML). Extension
cases use `--parent <slug>` rather than new modes: fine-tuning creates a setup
config branch, and reevaluation uses eval. Enforce per-experiment folders, a
STORY narrative, and an append-only `_RUNLOG` timeline with pending/completed
state and parent links to prevent overwrites and ad hoc loss. Automatically read
`experiment_conventions.md` and `similar_models.md` from analyze-project, giving
the user's existing layer, prefix, and config patterns priority. Graduate
refinement or library work to autopilot-code.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is one registered-headless dispatch-depth-1 one-shot owner with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

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

The main session or its dispatch-depth-1 conductor applies the `WORKFLOW §0.3`
pre-execution gate before the checkpoint evaluation run, dispatches workers
under `OPERATIONS §5.10`, and stays in the flow: liveness watching and harvest
are part of the same work, not a fire-and-forget dispatch. Reevaluation always
uses `--parent <slug>` lineage and the append-only `_RUNLOG`. Running a
separable stage inline requires the recorded reason in the experiment
`_RUNLOG` or `_internal/`.

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

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-lab/SKILL.md` and `skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/codex/skills/autopilot-lab/SKILL.md` as the native Codex Skill projection; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/opencode/skills/autopilot-lab/SKILL.md` and `adapters/opencode/commands/autopilot-lab.md` as native OpenCode projections; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-lab/SKILL.md` and `adapters/claude/skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks.
