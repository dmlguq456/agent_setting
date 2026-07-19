# Autopilot-* Routing Map — Agent-Facing Core

> A compact map for the main agent to route a task request to capabilities and roles. Each adapter maps them to its runtime-native skills, commands, agents, or profiles. Do not force symmetry; separate work according to its nature.
>
> The root `README.md` owns the user-facing meaning map and entry list. `CONVENTIONS.md` owns QA, model, and folder definitions. This document contains routing tables only, avoiding duplicated narrative and invocation examples.

---

## 0. Invariants — One Router and the Artifact Order Convention

This is the single routing contract for spec-backed projects that contain `.agent_reports/spec`, with legacy `.claude_reports` compatibility. Read it on demand when the adapter's status or reminder surface indicates routing is due; hooks expose runtime state but do not replace or eagerly inject this contract.

Every task first passes through the work-nature map in §2. Direct work, runtime plugins, and built-in Skills are used only where this router places them. Adapter and runtime projection work also remains core-first: establish the portable invariant in `core/`, read its governing document, then change adapter or generated output. A read marker enforces order but is not a substitute for review.

### 0.1. Read-Only Orientation Before Capability Routing

Before selecting a capability or Skill, distinguish read-only orientation from
work that creates or refreshes a persistent artifact. A request whose desired
outcome is to understand the project, recover prior context, resume from the
current state, or report status is orientation when it does not also ask for a
new analysis or a modification. These examples describe intent; they are not a
keyword classifier.

Read-only orientation invokes no capability and writes no artifact. Recover
context in this order:

1. Choose one targeted memory query from the task and recall it before broad
   discovery. This is an agent judgment for orientation, not a prompt-keyword
   classifier. A shortened, ellipsized, or otherwise insufficient hit is only
   an index: read the full body by record ID before using it as evidence.
2. Use the adapter status surface and `utilities/artifact-root.sh` to resolve
   the project-wide canonical artifact root. In a linked worktree, ignore its
   tracked artifact snapshot and read the primary worktree's canonical root.
   Prefer canonical `.agent_reports/`; only when it is absent, use an existing
   legacy `.claude_reports/`.
3. Read existing state before a broad source census: the newest relevant
   `pipeline_summary.md`, `pipeline_state.yaml`, `summary.md`, `REPORT.md`, or
   `STORY.md`; the latest experiment contract and `experiments/_RUNLOG.md`;
   and the current `spec/prd.md` or task-specific specification. Read only the
   subset needed to orient, and follow any relevant pointers from memory.
4. Inspect primary code, data, and raw logs only when recovered contracts leave
   a material question unanswered or must be checked against live behavior.

Resolve conflicts with this evidence precedence:

```text
latest specification or user-confirmed decision
  > durable project fact
  > latest experiment contract
  > legacy document
```

Live primary behavior is validation evidence, not permission to silently
rewrite an explicit current contract. When a lower-priority source differs,
report the drift and identify both sources; do not merge their meanings or
quietly choose the legacy value.

`analyze-project` becomes eligible only when no usable analysis exists,
existing analysis is demonstrably stale for the requested downstream work, or
the user explicitly asks to create or refresh persistent project analysis.
When analysis already exists, read it before deciding that reanalysis is
needed.

This boundary was strengthened after a 2026-07-14 incident where a context
recovery request in a spec-backed project was routed to `analyze-project` before
its existing legacy artifact root and memory-linked artifacts were read.

**Hard artifact order:**

```text
[code] research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)
[docs] research / analyze-project(paper or doc) → autopilot-draft → autopilot-refine
```

- **No code without a spec:** if a code request has no `spec/`, run `autopilot-spec` first. A one-off throwaway is the only exception; repeated work graduates to a spec.
- **No spec without prior evidence:** if neither `research/` nor `analysis_project/` grounds the spec, run `autopilot-research` or `analyze-project` first. Enforce this more strongly in unfamiliar domains and for new intent.
- **Mechanical enforcement:** `artifact-guard.sh` fail-closes writes outside the canonical artifact root and, for a route-backed write under `spec/`, requires the active route to have declared `spec_touch` with a `spec/` write scope. The artifact-creation order above is convention plus routing reminders, not a mechanical block; it does not block edits to existing artifacts or source either way.

**The owning capability also owns revisions.** The routing reminder and convention govern edits; `artifact-guard.sh` does not track per-artifact edit history.

| Artifact | Sole update path | Version location |
|---|---|---|
| `spec/` blueprint | `autopilot-spec` update | `_internal/versions/v{N}/` |
| code work under `plans/` | `autopilot-code` | `plans/<date>_<slug>/` |
| documents | `autopilot-draft` or `autopilot-refine` | `_internal/versions/v{N}/` |
| experiments | `autopilot-lab` | `_RUNLOG.md` |
| DB records with `type=profile` | `analyze-user` or `post-it --scope user` | changelog inside the record body |

This document plus the runtime adapter bootstrap is the routing source of truth. Violation signals include ad-hoc artifact edits, code before its gates, or updating an artifact through a capability that does not own it.

### 0.2. Semantic Primary Routing

Choose the primary capability from the core new work the request performs, not
from the artifact the user names or the surface verb such as "update", "fix",
or "정리". A request that ends in "update the report" still has its primary
decided by what must newly happen before any report can change.

Precedence, highest first:

1. New empirical work — training, checkpoint reevaluation or analysis,
   metric or ablation computation, plot/figure generation, or audio/media
   artifact generation — makes `autopilot-lab` the primary capability
   (`eval` for checkpoint-centered work, `setup` for new training).
2. With no new empirical work, correcting only the wording, structure, or
   errors of an existing document makes `autopilot-refine` the primary.
3. A change to requirements, evaluation policy, or any blueprint surface adds
   `autopilot-spec` update as a secondary spec-sync step; it never replaces
   the execution primary.
4. Formal report prose assembly routes through `autopilot-draft` or the owning
   capability's draft handoff as a secondary step.
5. Final artifact routing and note registration is `autopilot-note`, always
   secondary and last.
6. A secondary capability must never substitute for the primary execution
   capability, and the primary never absorbs a secondary's artifact ownership.

| Request shape | Primary | Secondary |
|---|---|---|
| "Reevaluate the model on a new test set and update the report" | `autopilot-lab --mode eval` | refine/draft document pass; `autopilot-spec` on policy change; `autopilot-note` |
| "Fix only the typos and sentences in REPORT.md" | `autopilot-refine` | — |
| "Change the evaluation mixing policy to unscaled and reevaluate" | `autopilot-lab --mode eval` | `autopilot-spec` update; neither replaces the other |

Added after a 2026-07-14 incident where a checkpoint reevaluation with report
regeneration was routed to `autopilot-refine` as primary from its surface
artifact and the entire evaluation ran inline in the main session.

### 0.3. Pre-Execution Gate for Long-Running Work

Before starting a long-running command, GPU or checkpoint evaluation, bulk
figure/media generation, or a full report regeneration, the main session
answers this gate; it does not enter long-running execution inline without it:

1. What is the semantic primary capability under §0.2?
2. Does the work create new empirical output?
3. Is the intensity `standard+`?
4. Are two or more separable stages present under `OPERATIONS §5.10`
   separability?
5. If main intends to run anything inline, which recorded exception applies?
6. Have native sub-agent limits and headless worker limits been checked as
   separate surfaces (`OPERATIONS §5.10` delegation surfaces)?
7. Does the plan preserve existing experiment lineage and the append-only
   `_RUNLOG`?

A gate answer that selects dispatch follows `OPERATIONS §5.10` registry and
liveness rules; an inline answer for `standard+` separable work requires the
recorded reason.

### 0.4. Primary Entry Confirmation

For material work, the main agent proposes the route and the user confirms the
intent before capability execution begins. The agent fills every field from
the request and recovered context; the user reviews a completed proposal rather
than recalling capability names, invocation syntax, or pipeline options.

Render labels in the user's communication language while preserving these five
fields and this order. In Korean, the canonical card is:

```text
[실행 확인]

작업: <무엇을 어떤 결과로 만들지>
이유: <현재 배경과 작업이 필요한 이유>
경로: <primary entry capability> · <mode/intensity> — <선택 이유>
범위: <포함 범위와 중요한 제외 대상>
완료: <산출물과 검증 기준>

→ 진행 / 수정: <틀린 부분> / 중단
```

Keep each value to one line. Do not include alternative menus, internal
sub-Skills, or extended reasoning. The card applies when any of these observable
conditions holds:

1. source, document, configuration, or a durable artifact will be created or
   changed;
2. two or more of research, analysis, implementation, or verification are
   needed;
3. the work requires a test, build, deploy, external-system mutation, or
   separate correctness evidence; or
4. a spec-backed project will create or update a capability-owned artifact.

Read-only orientation, status reporting, explanations, and simple factual
answers are exempt. `direct` is an explicit route shown in the card with its
reason, not a silent no-route decision. A current or immediately preceding user
instruction that already approves the same route and scope satisfies the gate;
do not repeat the card. After approval, capability-owned stages, validation,
records, commits, dispatch, and handoffs proceed without further confirmation.
Reconfirm only a material change to the primary capability, scope, completion
criterion, destructive risk, or touched external system.

Before approval, choose from compact manifest routing metadata and §0.2; do not
load the full entry Skill body or its references merely to propose a route. At
`standard+`, the depth-1 owner reads the selected capability contract and each
depth-2 worker reads only its stage contract. `direct` or `quick` acting
sessions read the detail they need after approval. If a runtime automatically
injects a selected Skill body into main, do not duplicate that read; record the
runtime limitation rather than claiming total-token savings.

Entry routers therefore have two deterministic load phases: manifest-owned
metadata before approval, then the selected portable owner contract after
approval. A router may expose one direct owner-reference index, but no
pre-approval reference may contain execution procedure. The confirmation is
one-time for an unchanged approved route and scope.

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
| Small localized change that misses at least one atomic-direct predicate and has no promotion signal | `quick` | Depth-1 one-shot owner with orient-lite, micro-plan, plan-check-lite, focused verification, and concise report; no depth 2 |
| Work with a promotion signal or separable durable stages | `standard` | Durable plan/checklist; thin depth-1 conductor dispatches capability-defined stages with file-only handoff and may open a bounded verifier or planner when separable |
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

One-line edits, renames, cleanup, and one-off reviews that need no plan or log may bypass autopilot and use direct editing or the implementation role. Use autopilot only when work needs tracking or accumulated artifacts. `DESIGN_PRINCIPLES §4` and each capability's quick tier define minor versus major. When one request spans several rows of this map, resolve the primary with the §0.2 semantic precedence.

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

The main agent proposes one primary entrypoint under §0.2, the user confirms it
under §0.4, and internal routing is automatic. Portable model roles come from
`CONVENTIONS §2`.

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
| `autopilot-lab` | Setup uses research plan review, implementation scaffold, and QA smoke tests. Evaluation uses functional QA, figure generation, and research survey; at `standard+`, checkpoint evaluation, media generation, report assembly, and independent verification dispatch as stage workers under the eval execution topology in `capabilities/autopilot-lab.md`. The actual long-running training run is asynchronous and human-gated through RUNLOG ⏳ rather than a stage-worker dispatch. |
| `analyze-user` | Cross-project material collection plus editorial review |

For every durable stage at `standard+`, use an independent headless session under `OPERATIONS §5.10`; the named team roles run inside that session, and the depth-1 conductor passes only artifact paths. Direct stays depth 0 and quick stays a depth-1 one-shot.

Each entrypoint is an explicit unit of intent. The §0.4 confirmation is the
single top-level route handshake. Capability-local review controls such as
revise into v2, back-jump, `--confirm`, or `--user-refine` remain opt-in and do
not repeat that handshake. Ask a separate question only when intent is genuinely
ambiguous after presenting the completed proposal. The runtime adapter bootstrap
owns concrete invocation syntax.

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

0. **Understand existing artifacts first:** follow the read-only orientation order in §0.1 before editing or choosing a capability, then read `spec/prd.md`, `pipeline_state.yaml`, and recent `plans/*`. Reading the spec that governs the declared work scope — root `prd.md` or the relevant `spec/<slug>/prd.md` — is a hard gate in a spec-backed cwd; which candidate governs remains agent judgment, recorded via route-record `spec_read.source`. Adapter-native markers and gates deny entry to spec-changing capabilities when a current spec of this project has not been read in the current session or has changed since the read.
1. **Refresh analysis when needed:** if `analysis_project/code/` is stale or the domain is unfamiliar, run incremental `analyze-project --mode code` first.
2. **Require a spec:** when absent, route to `autopilot-spec` before development. A single throwaway is the only exception, and repetition should graduate to a spec.
3. **Check spec drift before code:** compare the request with `spec/prd.md`. A route, schema/entity, UI-flow, external integration, migration, or existing code drift is spec-significant and routes through `autopilot-spec` update with a snapshot under `_internal/versions/v{N}/`. Proceed autonomously and report when drift is clear; ask when it is genuinely ambiguous. Record “no spec impact” for within-spec implementation details. `autopilot-code` repeats this verdict in preflight Step 0 as a backstop.
4. **Run `autopilot-code`:** intensity selects the graph. Direct performs inline production plus sanity/report. Quick uses one depth-1 session for micro-plan, plan-check-lite, focused verification, and report with no depth 2. Only `standard+` creates a durable `plans/<date>_<slug>/` cycle. Derived rigor never creates a separate plan cycle by itself.

These rules close three gaps: a broken trail caused by over-creating plans for quick work, spec drift that bypasses versioned spec update, and blind editing in a new session. Both `autopilot-spec` and `autopilot-code` are iterable; post-build change is another invocation of the same capability, not a new workflow family.
# Capability route topology

Every entry capability resolves through `capabilities/topologies.json`, the machine-readable execution-topology source. Intensity, topology class, worker kind, transport, DAG nodes, write scopes, promotion signals, and completion gates remain separate axes. `utilities/capability-route.py` compiles an immutable route bound to the registry digest, source commit, physical absolute working directory, artifact root, and transport evidence. Adapters may project compact summaries and pointers, but must not copy the graph into bootstrap or Skill metadata.
