# Autopilot-* Routing Map — Agent-Facing Core

> A compact map for the main agent to route a task request to capabilities and roles. Each adapter maps them to its runtime-native skills, commands, agents, or profiles. Do not force symmetry; separate work according to its nature.
>
> The root `README.md` owns the user-facing meaning map and entry list. `CONVENTIONS.md` owns QA, model, and folder definitions. This document contains routing tables only, avoiding duplicated narrative and invocation examples.

---

## 0. Invariants — One Router and a Hard Order Gate

This is the single routing contract for tracked projects that contain `.agent_reports/spec`, with legacy `.claude_reports` compatibility. Explicit untracked mode is exempt. Read it on demand when the adapter's status or reminder surface indicates tracked routing; hooks expose runtime mode state but do not replace or eagerly inject this contract.

Every task first passes through the work-nature map in §2. Direct work, runtime plugins, and built-in Skills are used only where this router places them. Adapter and runtime projection work also remains core-first: establish the portable invariant in `core/`, read its governing document, then change adapter or generated output. A read marker enforces order but is not a substitute for review.

### 0.1. Read-Only Orientation Before Capability Routing

Before selecting a capability or Skill, distinguish read-only orientation from
work that creates or refreshes a persistent artifact. A request whose desired
outcome is to understand the project, recover prior context, resume from the
current state, or report status is orientation when it does not also ask for a
new analysis or a modification. These examples describe intent; they are not a
keyword classifier.

Read-only orientation invokes no capability and writes no artifact:

1. Use the adapter status surface to determine tracked state and resolve the
   artifact root. Prefer an existing `.agent_reports/`; when it is absent,
   treat an existing legacy `.claude_reports/` as the same project-state
   surface rather than as a lower-value input.
2. Read existing state before a broad source census: relevant
   `pipeline_summary.md` and `pipeline_state.yaml`, the current
   `spec/prd.md`, `experiments/_RUNLOG.md`, and the recent
   `summary.md`, `REPORT.md`, or `STORY.md` files that identify the
   active work. Read only the subset needed to orient.
3. Use memory recall after project artifacts when cross-session continuity
   could materially help. Memory is a continuity and navigation layer: follow
   relevant file or artifact pointers and cross-check their targets. Current
   artifacts and live code override stale memory when they conflict.
4. Inspect raw source and logs only when the existing state leaves a material
   question unanswered.

`analyze-project` becomes eligible only when no usable analysis exists,
existing analysis is demonstrably stale for the requested downstream work, or
the user explicitly asks to create or refresh persistent project analysis.
When analysis already exists, read it before deciding that reanalysis is
needed.

This boundary was strengthened after a 2026-07-14 incident where a context
recovery request in a tracked project was routed to `analyze-project` before
its existing legacy artifact root and memory-linked artifacts were read.

**Hard artifact order:**

```text
[code] research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)
[docs] research / analyze-project(paper or doc) → autopilot-draft → autopilot-refine
```

- **No code without a spec:** if a code request has no `spec/`, run `autopilot-spec` first. A one-off throwaway is the only exception; repeated work graduates to a spec.
- **No spec without prior evidence:** if neither `research/` nor `analysis_project/` grounds the spec, run `autopilot-research` or `analyze-project` first. Enforce this more strongly in unfamiliar domains and for new intent.
- **Mechanical enforcement:** `artifact-guard.sh` blocks only invalid creation order—new spec requires research or analysis, new plan requires spec, and new document requires research or analysis. It does not block edits to existing artifacts or source. Convention plus routing reminders cover those paths. Explicit adapter untracked mode bypasses the gate.

**The owning capability also owns revisions.** `artifact-guard.sh` mechanically enforces creation order, while the routing reminder and convention govern edits. Untracked mode is exempt.

| Artifact | Sole update path | Version location |
|---|---|---|
| `spec/` blueprint | `autopilot-spec` update | `_internal/versions/v{N}/` |
| code work under `plans/` | `autopilot-code` | `plans/<date>_<slug>/` |
| documents | `autopilot-draft` or `autopilot-refine` | `_internal/versions/v{N}/` |
| experiments | `autopilot-lab` | `_RUNLOG.md` |
| DB records with `type=profile` | `analyze-user` or `post-it --scope user` | changelog inside the record body |

This document plus the runtime adapter bootstrap is the routing source of truth. Violation signals include ad-hoc artifact edits, code before its gates, or updating an artifact through a capability that does not own it.

## 1. Four Tracks

```text
[research and experiment] research / analyze-project(code) → autopilot-spec ↻ → autopilot-code ↻ → autopilot-lab ↻
[library and CLI]         analyze-project → autopilot-spec ↻ → autopilot-code ↻
[documents]               research / analyze-project(paper or doc) → autopilot-draft → autopilot-refine ↻ → autopilot-apply
[apps]                    autopilot-spec ↻ → autopilot-design → autopilot-code ↻ → autopilot-ship ↻
```

`↻` marks an iteration point. Common post-work capabilities are read-only `audit` and Markdown correction through `autopilot-refine`. Cross-project capabilities are `analyze-user` and `post-it --scope user`.

## 1.1. Pipeline Intensity Routing

Autopilot entrypoints choose `intensity`; verification rigor is derived from it under `CONVENTIONS §1.1`, not from a separate `--qa` axis. Intensity selects the stage graph and dispatch depth, while derived rigor scales plan checks, selected independent review, and final verification.

| Request shape | Default | Routing |
|---|---|---|
| One-off answer, typo, rename, or explicit no-artifact work | `direct` | No plan stage, plan check, or durable plan |
| Small localized tracked change or minor document edit | `quick` | Depth-1 one-shot owner with orient-lite, micro-plan, plan-check-lite, focused verification, and concise report; no depth 2 |
| Routine tracked code, doc, spec, or design work | `standard` | Durable plan/checklist; thin depth-1 conductor dispatches plan, execute, test, and report as separate depth-2 headless stages with file-only handoff, and may open a bounded verifier or planner when separable |
| Important multi-file or risk-bearing work | `strong` | Standard stage dispatch plus one depth-2 check at the riskiest point |
| Complex cross-domain or cross-harness work | `thorough` | Bounded depth-2 perspective and verifier workers |
| High-stakes, irreversible, security, or external-facing work | `adversarial` | Thorough plus an explicit adversary, failure-mode, or security pass |

Only `direct` has no plan. Every other autopilot graph includes a plan check, but independent QA is not repeated after every sub-stage by default. `CONVENTIONS §1` is canonical for the graph.

## 2. Work-Nature Map

| Work | Prior research or analysis | New intent or blueprint | New or existing asset work |
|---|---|---|---|
| Documents: papers, presentations, reports, proposals, rebuttals | academic or market research plus `analyze-project` in paper/doc mode | `autopilot-draft` | `autopilot-refine` |
| Code: libraries, research, apps, CLI, and API | academic or technical research plus `analyze-project(code)` | `autopilot-spec` in app/library/api/cli/research/composite/auto mode | `autopilot-code`, routed by spec mode |
| ML or one-shot experiment prototype | Four code-analysis inputs: experiment conventions, readiness, cleanup, and similar models | No spec for a fast cycle | Iterative `autopilot-lab`, graduating to `autopilot-code` |
| Visual assets and design | — | `autopilot-design` for a new design-first cycle | Substantial direction, token, layout, structure, or built-app design evolution goes through `autopilot-design`, updating the token contract and code from a real render. Only a trivial tweak goes directly through `autopilot-code`. Design tokens are the single contract under `DESIGN_PRINCIPLES §9`. |
| User profile | — | `analyze-user init` | `analyze-user update` |

One-line edits, renames, cleanup, and one-off reviews that need no plan or log may bypass autopilot and use direct editing or the implementation role. Use autopilot only when work needs tracking or accumulated artifacts. `DESIGN_PRINCIPLES §4` and each capability's quick tier define minor versus major.

## 3. `autopilot-spec` Modes

| Mode | Use | Scaffold: PRD plus skeleton |
|---|---|---|
| `app` | User application such as Next.js or Expo | Component and Deployment diagrams plus application skeleton |
| `library` | Public npm, pip, or crate package | Packaging config and public API skeleton following reference exports |
| `api` | Backend API without UI | Component and Deployment diagrams plus FastAPI or Express router skeleton |
| `cli` | Command-line tool | argparse or typer entry plus command skeleton |
| `research` | Research and reproducibility | train/eval/config and model skeleton plus Phase 1.5 checkpoint preflight |
| composite or `auto` | Multiple aspects or inferred mode | Common contract plus independent sections per selected mode, with confirmation after inference |

Reference priority is internal `similar_models` or `--ref`, then `research/<topic>/code_resources`, then generic scaffolds. Prepend conventions from `analysis_project/code/experiment_conventions.md`; fall back to `mem profile 07_coding_convention`, with project-local conventions winning conflicts.

## 4. Atomic PRD Updates

When a code or intent change affects the spec, update every affected surface in one transaction. `CONVENTIONS §6.3a` is the mapping source of truth.

| Change | Affected surfaces |
|---|---|
| Endpoint, request/response body, or error | API contract, Component, and optionally Sequence |
| DB entity or field | Data model, backend Component, and optionally ER |
| UI flow | UI flow, frontend Component, and optionally Activity |
| External service integration | API auth contract, Deployment, deploy record, and `.env.example` |
| Stack replacement | Stack decision, Component, and Deployment |
| Public API change in a library | Public API, examples, semver impact, and module-dependency Component |
| CLI command or option change | Commands, options, exit codes, README examples, and command-tree Component |

`autopilot-spec refine` identifies the impact list, confirms it, and updates it atomically. If `autopilot-code` detects spec impact, it plans the bundle, confirms, and jumps back to `autopilot-spec`. After the final code report, Step 7 updates `analysis_project`: edit small changes directly or run incremental `/analyze-project --mode code --skip-qa` for large ones.

## 5. Entrypoint-to-Worker Routing

The user supplies one entrypoint; internal routing is automatic. Portable model roles come from `CONVENTIONS §2`.

| Entry | Internal routing |
|---|---|
| `autopilot-research` | Research-survey and fact-check roles plus browser-fetch, PDF-extract, and web-image-search material roles |
| `analyze-project` | One capability analyzing code, paper, or document mode itself |
| `autopilot-spec` | Planning role for PRD, material role for research import, and setup logic for hosting and CI/CD |
| `autopilot-design` | Design maker and critic plus material web-image-search |
| `autopilot-code` | Direct is depth-0 inline. Quick is one depth-1 owner running orient-lite → micro-plan → plan-check-lite → produce → focused verification → concise report. At `standard+`, independently dispatch planning, implementation, code-review/test, and task-aware plan review; visual work uses a design critic, while research and code use research review. |
| `autopilot-code` in app mode | General code flow plus design critique at plan review and after render, DB migration safety, and automatic deploy after an authorized push |
| `autopilot-draft` | Material figure/data/reference work, writing implementation, editorial polish, and research fact-check |
| `autopilot-refine` | Reuse the draft roles plus editorial review |
| `autopilot-lab` | Setup uses research plan review, implementation scaffold, and QA smoke tests. Evaluation uses functional QA, figure generation, and research survey. The actual long-running training run is asynchronous and human-gated through RUNLOG ⏳ rather than a stage-worker dispatch. |
| `analyze-user` | Cross-project material collection plus editorial review |

For every durable stage at `standard+`, use an independent headless session under `OPERATIONS §5.10`; the named team roles run inside that session, and the depth-1 conductor passes only artifact paths. Direct stays depth 0 and quick stays a depth-1 one-shot.

Each entrypoint is an explicit unit of intent. The main agent configures options, summarizes them naturally, and offers the four confirmation outcomes where the capability contract requires them: proceed, revise into v2, back-jump, or stop. Ask when intent is genuinely ambiguous rather than guessing. The runtime adapter bootstrap owns concrete invocation syntax.

## 6. Artifact Folders

Code uses sibling `spec/` and `plans/` buckets.

| Kind | Folder |
|---|---|
| Code blueprint | `spec/`: current `prd.md`, `stack.md`, optional `design/`, `ship.md`, `pipeline_state.yaml`, and prior specs under `_internal/versions/v{N}/` |
| Code work | `plans/<date>_<slug>/`: plans, dev logs, test logs, and `_internal`, regardless of whether a spec exists |
| Experiment prototype | `experiments/<date>_<slug>/` plus `experiments/_RUNLOG.md` |
| Document | `documents/<date>_<name>/` |
| Prior research and analysis | `research/<topic>/` and `analysis_project/<mode>/` |

Numeric prefixes such as `00_`, `01_`, `02_`, and `05_` are retired. Use plain names inside `spec/`, separating user-facing files from machine-oriented `_internal/`. `autopilot-spec refine` snapshots prior `prd.md` versions automatically, following the document-track versioning principle. See `CONVENTIONS §§5 and 6.5`.

## 6.1. Cross-Project Continuity Layer

`<agent-notes-root>` is separate from each project's artifact root. The artifact root holds research, spec, plans, documents, and experiments for one project; the notes root reads across projects and presents Layer 1 and Layer 2 continuity state.

| Layer | Owner | Example | Update path |
|---|---|---|---|
| `<artifact-root>/notes/<date>/` | `autopilot-note` | Scan/routing and reviewer logs for this run | Capability artifact rules |
| `<agent-notes-root>/_layer2/notes/` | Agent | Readable note row derived from one artifact | `autopilot-note` or board-approved migration |
| `<agent-notes-root>/_layer2/{backbones,tasks,papers}/` | Agent | Reusable-axis, task, and paper catalogs | `autopilot-note` emergence or board-approved edit |
| `<agent-notes-root>/cards/` | User | Layer 1 task and project cards | Worklog-board UI or direct user edit |
| `<agent-notes-root>/_triage`, `_feedback`, `_change_review` | User-agent queue | New-card proposals, feedback, and code-change review | Worklog-board UI plus `autopilot-note --feedback` |
| `<agent-notes-root>/digests`, `oncall`, `study`, `manual` | Loops and operators | Digests, reports, proposals, and manuals | Loop or board UI |

`_layer2/`, the three queues, and the local board DB are mutable runtime or user state and must not be committed to the harness repository. They may live in a separate notes repository, still independent of harness core and adapters. `<worklog-board-app>` displays this root and processes approval or review. Changes to the app belong to `autopilot-code` in the app repository; harness migration must not move or delete board data.

## 7. Routing Changes After the Initial Build

In a spec-backed project, a later fix or feature—especially in a new session—must not start with an ad-hoc edit. Follow understand existing artifacts → analyze → spec → implementation.

0. **Understand existing artifacts first:** follow the read-only orientation order in §0.1 before editing or choosing a capability, then read `spec/prd.md`, `pipeline_state.yaml`, and recent `plans/*`. Reading `prd.md` is a hard gate in a spec-backed cwd. Adapter-native markers and gates deny entry to spec-changing capabilities when it has not been read in the current session or changed since the read.
1. **Refresh analysis when needed:** if `analysis_project/code/` is stale or the domain is unfamiliar, run incremental `analyze-project --mode code` first.
2. **Require a spec:** when absent, route to `autopilot-spec` before development. A single throwaway is the only exception, and repetition should graduate to a spec.
3. **Check spec drift before code:** compare the request with `spec/prd.md`. A route, schema/entity, UI-flow, external integration, migration, or existing code drift is spec-significant and routes through `autopilot-spec` update with a snapshot under `_internal/versions/v{N}/`. Proceed autonomously and report when drift is clear; ask when it is genuinely ambiguous. Record “no spec impact” for within-spec implementation details. `autopilot-code` repeats this verdict in preflight Step 0 as a backstop.
4. **Run `autopilot-code`:** intensity selects the graph. Direct performs inline production plus sanity/report. Quick uses one depth-1 session for micro-plan, plan-check-lite, focused verification, and report with no depth 2. Only `standard+` creates a durable `plans/<date>_<slug>/` cycle. Derived rigor never creates a separate plan cycle by itself.

These rules close three gaps: a broken trail caused by over-creating plans for quick work, spec drift that bypasses versioned spec update, and blind editing in a new session. Both `autopilot-spec` and `autopilot-code` are iterable; post-build change is another invocation of the same capability, not a new workflow family.
