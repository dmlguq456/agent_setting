# Conventions — Family-Wide Operational Rules

> This is the single source of truth for operational rules and definitions across the autopilot family. `DESIGN_PRINCIPLES.md` owns architectural design such as orchestrator, Skill, and agent separation; this document owns QA definitions, portable model roles, artifact conventions, and family-wide flags.
>
> Runtime adapter bootstraps list this file as a source of truth. The main agent reads it when QA, model-role, artifact, or family-wide flag work needs the definitions.
>
> `tools/build-manifest.py --check` and adapter `sync-native-* --check` verify manifests and projections; `tools/check-adaptation-boundary.sh` verifies adapter boundaries; `tools/skill-conformance/check.sh` verifies quantitative Skill rules; and `harness verify` checks installed surfaces. Human review owns semantic prose consistency.

---

## §1. Pipeline Intensity, Stage Graph, and Assurance (canonical)

Pipeline intensity controls which orchestration shape an autopilot entry uses. Verification rigor—how much assurance selected checks receive—is derived from the same intensity through §1.1 rather than selected as a separate axis. There is no user-facing `--qa` selector to reconcile with the pipeline graph.

| Stage | Meaning | Typical realization |
|---|---|---|
| `intake` | Parse request, mode, constraints, risk, and intensity | Route/capability preflight, spec significance, target selection |
| `orient` | Gather only the context needed for the selected intensity | Read spec, source, or material artifacts; `orient-lite` for quick |
| `plan` | Choose the work path before production | Absent for direct, inline micro-plan for quick, durable plan for standard+ |
| `plan-check` | Check that the plan can safely feed production | Required for quick+; depth scales with intensity |
| `produce` | Create or modify the artifact | Code, draft, report, design, spec, or note |
| `verify` | Run a concrete checker | Tests, visual harness, claim verification, compile, consistency, or drift check |
| `synth` | Merge independent perspectives into one path | Only when perspective workers ran |
| `report` | Return outcome, evidence, artifact paths, and remaining risk | Summary, handoff, or user-facing report |

| Intensity | Stage graph | Plan and check policy | Dispatch | Assurance |
|---|---|---|---|---|
| `direct` | `intake → produce → sanity/report` | No plan, plan check, or durable plan; final sanity only | Inline | none/light |
| `quick` | `intake → orient-lite → micro-plan → plan-check-lite → produce → verify-lite → report` | One depth-1 session; 3–4 focused plan questions and one concrete sanity check | One-shot owner; no depth 2 | quick |
| `standard` | `intake → orient → owner-plan → plan-check → optional verifier/planner → synth → produce → verify → report` | Durable plan where the capability owns a work cycle; bounded review for separable work | Thin conductor dispatches each durable stage as depth 2 with file-only handoff | standard |
| `strong` | Standard plus a risk-focused check and optional fix loop | One independent review at the riskiest point | Stage dispatch plus one bounded risk worker | standard/thorough |
| `thorough` | Owner plan, multiple bounded perspectives, synthesis, production, and verification | Deeper plan review and bounded alternatives | Depth-1 owner opens bounded depth-2 perspectives | thorough |
| `adversarial` | Thorough plus adversarial planning and failure-mode/security verification | Explicit contradiction or hostile pass | Bounded adversary/verifier workers | adversarial |

Stage-local gates stay cheap and ask only whether output can feed the next stage. An independent QA pass uses another role, model, or harness and runs only where the selected intensity calls for it. Final verification remains capability-specific. Every non-direct graph includes at least a small plan check because a bad plan corrupts every downstream stage.

Depth 0 is the user-facing main session. Depth 1 owns the whole capability pipeline and returns only synthesis. At standard+, it is a thin conductor; quick uses a one-shot owner. Depth 2 serves read-only review helpers and independently dispatched pipeline stages with disjoint writes. Direct stays inline, quick opens no depth 2, and depth 3 or greater is forbidden. Stage sessions use in-session teams for any internal parallelism.

### §1.1. Verification Rigor Tiers

Rigor is an assurance budget inside the graph selected by intensity. It does not create stages, choose topology, or grant depth 2. Reviewer counts are upper bounds for a selected pass rather than automatic fan-out after every stage.

| Rigor | Derived from | Plan check | Selected independent pass | Final verification | Retry budget |
|---|---|---|---|---|---|
| `quick` | `quick` | Self-check or 3–4 focused questions | None by default | One concrete sanity check | None automatically |
| `light`/none | `direct` | Focused self-check if present | At most one fast reviewer at an already selected review point | Focused command, render, or source check | One pass |
| `standard` | `standard`, `strong` | Lightweight independent review where planning exists | One bounded depth-2 point for separable work | Normal capability verification; source check when relevant | At most one correction |
| `thorough` | `thorough` | Deeper or multi-axis review | Additional bounded perspectives | Broader evidence and adequacy review | Up to two corrections |
| `adversarial` | `adversarial` | Hostile owner-plan critique | Thorough plus explicit external adversary, security, contradiction, or failure-mode pass | Verification plus adversarial evidence | Two corrections plus one adversary pass |

Track rules:

- Code has no fact-checker; ground truth is code, tests, runtime behavior, API/CLI surface, and selected security review.
- Document, research, refinement, and note tracks fact-check only when claims, citations, cards, or external truth are in scope.
- Design, apply, and ship require executable render, build, compile, or deployment evidence; reviewer prose never substitutes for it.
- Spec review checks coherence and downstream API/data/UI impact; factual citations may additionally require source checking.

Intensity resolves in this order: explicit `--intensity`, capability default, then request shape in `WORKFLOW §1.1`. Rigor then maps deterministically: direct to none/light, quick to quick, standard or strong to standard, thorough to thorough, and adversarial to adversarial.

An external adversary is required only when an adversarial graph actually selects that pass. The adapter must prove that a different reviewer, engine, or harness ran. If an explicitly requested adversarial pass is unavailable, fail loudly; if routing auto-escalated, fall back to thorough and report it. Runtime wrapper names are not portable semantics.

`--no-fact-check` and `--no-style-audit` remain orthogonal and appear only on capabilities that expose those checks. `code-plan` realizes durable plan and plan-check for standard+; quick keeps an inline micro-plan. `code-refine` corrects an existing durable plan and is not automatic in quick. `code-test` scales concrete verification with rigor. `code-report` reports and synthesizes without adding QA.

### §1.2. Token and Context Pressure

The portable invariant is **token pressure ⊥ intensity**. Pressure is an observed response-shaping signal, not a pipeline selector or assurance budget. It may shorten user-facing explanation and defer unrequested optional extras, but never changes graph, depth, dispatch, model role, reasoning effort, plan check, reviewer budget, verification, retry contract, or definition of done.

Portable telemetry distinguishes active context, cumulative session counters, and a response-policy score. Never reuse a generic adapter field with different runtime meaning. Unknown, stale, malformed, unsupported, or decreasing counters fail open to the selected pipeline and report degraded availability. Forks and subagents have separate denominators.

Pressure cannot reduce validation, tests, error and data-loss handling, security, auth, permissions, accessibility, spec and plan gates, sandbox and approval, git/write/hook/liveness guards, required tools, or input context. Automatic pruning stays off. An adapter may inject a compact output directive only on a verified pressure-band transition; normal, unknown, unsupported, native-owned, and repeated bands inject zero bytes. Runtime-owned budget config is read-only unless the user explicitly chooses a separately verified native opt-in.

## §2. Portable Model Roles

Shared contracts use model roles rather than concrete model names. Vendor-specific models are adapter implementation values.

| Role | Meaning | Typical use |
|---|---|---|
| `fast reviewer` | Low-cost, low-latency broad review with known ground truth or surface-heavy checks | quick/light QA, style, coverage, cross-reference, verbatim matching |
| `deep reviewer` | High-reasoning domain and methodology judgment | methodology, safety/security, architecture risk, standard+ quality review |
| `fast fact-checker` | Narrow comparison of claims against source artifacts with limited creativity | citation, venue, year, metric, lineage, table values |
| `fast writer` | Low-cost assembly of verified artifacts into a user-facing summary | Final report and short synthesis |
| `deep maker` | Generation requiring aesthetic, strategic, architectural, or domain judgment | Planning, research synthesis, visual design, editorial rewrite |
| `deep orchestrator` | High-judgment conductor for stage gates, failover, and evidence synthesis | Standard+ depth-1 capability owner |
| `external adversary` | Hostile review through an independent engine or runtime | Adversarial verification |
| `orchestrator` | Balanced mechanical coordination of already decided calls, paths, and states | Wrappers, dispatch mechanics, report assembly |

### §2.1. Dispatch Routing

The default role for a standard+ conductor is `deep orchestrator`. Do not alias the retained balanced `orchestrator` to it. Dispatch selection order is explicit choice, hard eligibility, stage affinity, maker/checker family diversity, then capacity, cost, and latency. Portable core records only `gpt`, `claude`, or `unknown` family plus a role. Planning, architecture, and decomposition use `deep maker` and prefer eligible GPT-family affinity without hard pinning. Adapters own exact model IDs, reasoning profiles, runtime probes, and eligibility. Reviewers prefer a different family from makers where available.

`utilities/dispatch-route.sh` is read-only and emits stable key/value trace, rejected, fallback, and unknown records. It does not register, launch, or mutate caches or worktrees. Without an adapter probe, OpenCode remains `unknown` rather than guessed.

### §2.2. Adapter Mapping

Every adapter maps portable roles to concrete runtime models, tools, and prompt profiles as a quality-reproduction contract. Main or the parent orchestrator explicitly chooses a role or concrete model/effort for every dispatched job; wrappers do not silently choose a default. Update and read core before changing adapter maps or generated agents.

### §2.3. Role Operation Matrix

| Role family | Portable role | Operation |
|---|---|---|
| `plan-team` | deep maker | Planning and architecture |
| `qa-team` | variable reviewer/verifier | Rigor-selected plan, test, code, and security checks; test owns final evidence and security review owns adversarial code checks |
| `research-team` | variable research reviewer | Deep maker/reviewer by default; fast fact-checker or reviewer for narrow/light work |
| `material-team` | deep maker plus fast tool workers | Fast browser/PDF/image collection; deep figure and data synthesis |
| `dev-team` | fast implementer by default | Routine implementation; escalate complex API or library design to deep maker |
| `design-team` | deep maker plus fast verifier | Deep maker, nuance-dependent critic, and fast mechanical verifier |
| `editorial-team` | deep editor/maker plus fast reviewer | Translation and polish use deep editorial judgment; review uses fast reviewer |
| external review wrapper | external adversary orchestrator | Independent engine performs review; wrapper only invokes and summarizes |

For standard+ code stage dispatch, choose explicitly: code-plan uses deep maker; code-execute uses fast implementer unless complexity warrants deep maker; code-test uses the variable reviewer/verifier budget derived from intensity; and code-report uses fast writer.

---

## §3. Hard Cross-Document Invariants

1. Intensity selects graph and depth; §1.1 derives assurance from intensity. There is no user-facing `--qa` axis, and rigor alone cannot open depth 2 or a full pipeline.
2. Quick means one-session micro-plan, plan-check-lite, and verify-lite. Requiring a durable plan, repeated QA, or parallel reviewer fan-out for every small task is drift.
3. Adversarial means thorough plus a selected external adversary, failure-mode, security, or claim-verification pass. `standard + external/Codex` is not the definition.
4. Code has no fact-checker.
5. Do not hardcode code-test to thorough or parallel QA on every call; scale final verification from intensity-derived rigor.
6. `--no-fact-check` and `--no-style-audit` must not leak to unrelated capabilities.
7. An external review wrapper is not the reviewer; separate the independent engine from the mechanical orchestrator.
8. New or strengthened instructions, rules, and hooks preserve why, including the motivating incident and date, inline or in the commit message. Drills are the strongest executable preservation of intent.
9. Never reduce a semantic requirement to token or regex rules without verifying that meaning is preserved; see `DESIGN_PRINCIPLES §0.7`.
10. Token pressure is orthogonal to intensity and cannot reduce graph, depth, dispatch, model role, assurance, required guards, or input context.

Token-budget accounting is observation, not attribution. Hook invocations,
zero/emission outcomes, exact inserted-directive UTF-8 bytes, and monotonic
exact-session runtime counter deltas remain separate fields; none may be named
or derived as savings, billing cost, or ROI. Directive token counts remain
unknown unless an exact tokenizer for the actual payload is recorded with
runtime/model/version provenance. Accounting state must be content-free,
hashed by session, atomically updated under a bounded lock, bounded to 8 KiB per
file / 256 files / 2 MiB total with oldest-first aggregate pruning, and always
fail open without changing hook output. L2 diagnostics are on-demand only.

Dynamic token-pressure policy is an isolated experiment surface. Production
reinjection remains the static transition-only policy; production hooks and
runtime config must not import, activate, or fit an offline candidate. Paired
control/static/dynamic evaluation keeps input, model effort, intensity,
dispatch/depth, QA, required checks, and safety gates identical, performs no
input pruning or online/RL fitting, and may return at most
`eligible_for_user_review`. Adoption requires explicit user review and a later
spec/code cycle.

When adding an invariant, add its mechanically expressible portion to deterministic tooling or regression tests. Human source review owns semantic and wording consistency.

## §4. Cross-Document Verification Ownership

- Manifest, name, and path drift: `python3 tools/build-manifest.py --check`
- Runtime-native projections: each adapter's `sync-native-* --check`
- Canonical-to-adapter boundary: `tools/check-adaptation-boundary.sh`
- Skill structure and invocation: `tools/skill-conformance/check.sh`
- Installed runtime surface: `harness verify`
- Value proposition, information order, and semantic equivalence: human review; no automatic prose fix

## §5. Skill Output Convention — T1/T2/T3

Every autopilot capability and `analyze-project` follows this artifact structure. Existing artifacts keep their legacy flat layout; new invocations use this convention.

### §5.1. Workspace Assumption

Skills run from the project root. Prefer `.agent_reports/`; use `.claude_reports/` only when it already exists and the new root does not. Shell examples resolve `REPORTS_DIR` accordingly. `analyze-project` reads the current directory, `autopilot-code` mutates code there, and draft/research/refine discover persistent inputs below the artifact root. Cross-project work changes cwd and uses another session.

Artifact directories are normally gitignored. Add `.agent_reports/` to `.gitignore` on first creation in a tracked repository; treat legacy `.claude_reports/` similarly. The exception is `<agent-home>`, where artifact history is itself a repository asset and is committed, while transient locks and untracked markers remain ignored.

Inputs come from persistent project artifacts. External raw material is first normalized through `analyze-project --mode paper|doc`; the family has no flag for arbitrary external artifact directories.

### §5.2. Tier Definitions

| Tier | Meaning | Location |
|---|---|---|
| **T1 primary** | Core index and deliverable that users routinely see | Artifact directory root |
| **T2 secondary** | Chapters, strategy, analysis, logs, and supporting assets read as needed | Named subdirectories |
| **T3 tertiary** | Reviews, raw metadata, and version snapshots rarely read directly | `_internal/` |

The underscore keeps internal data visible but de-emphasized; a dot directory would hide it too strongly.

### §5.3. Standard Shape

```text
<artifact-dir>/
├── pipeline_summary.md
├── <T1 deliverables>
├── <T2 subdirectories>
└── _internal/
    ├── <capability-specific review directories>
    ├── <raw metadata>
    └── versions/v{N}/<changed files>
```

### §5.4. Capability Mappings

#### §5.4.1. Research

`<artifact-root>/research/<topic>/` contains T1 `pipeline_summary.md`, `pipeline_state.yaml`, `00_briefing.md`, and numerically ordered report chapters; T2 `analysis_summary.md`, `cards/`, `code_resources/`, and `figures/`; and T3 search results, batches, access classification, chaining, code search, prefetch, reviews, and versions under `_internal/`. Keep chapters at root because numeric prefixes already group them.

#### §5.4.2. Documents

`<artifact-root>/documents/<date>_<name>/` contains T1 pipeline state and the latest `draft/`; T2 latest `strategy/`, `analysis/`, and `assets/`; and T3 metadata, strategy/draft reviews, audits, discarded variants, and snapshots under `_internal/versions/v{N}/`. Retire sibling `_v{N}.md` files for new output but preserve them in legacy artifacts.

#### §5.4.3. Code Track — Flat `spec/` Plus Repeated `plans/`

One repository normally has one flat `spec/`. Only a monorepo with independently delivered components and separate PRDs uses `spec/<component>/` and `plans/<component>/<cycle>/`.

```text
spec/
├── prd.md
├── ship.md
├── stack.md
├── design/
├── pipeline_state.yaml
└── _internal/versions/v{N}/prd.md

plans/<date>_<slug>/
├── pipeline_summary.md
├── plan/                 # plan.md, optional localized variant, checklist.md
├── dev_logs/
├── test_logs/
└── _internal/            # plan, dev, and test reviews
```

`prd.md` is always current. A major `autopilot-spec refine` snapshots it before overwrite; minor edits append to pipeline history, and five accumulated minors trigger an audit alert. Code history uses git rather than `autopilot-refine` by default.

#### §5.4.4. Project Analysis

`analysis_project/code/` and `analysis_project/paper/` are flat and cumulative per project. `analysis_project/doc/<name>/` is per task because document inputs vary by reviewer, template, patent, or other source set. Each mode keeps user-facing overview and analysis at T1/T2 and raw scans or QA under `_internal/`.

### §5.5. Legacy Compatibility

For a new or empty directory, create the modern layout. On re-entry, the presence of `_internal/` selects modern behavior; otherwise main-level review directories or sibling `_v{N}.md` files select legacy behavior. Preserve the detected shape. Migrate only on an explicit user request through a one-off helper.

### §5.6. Authoring `SKILL.md`

This section applies to orchestrator-level capabilities that create artifact directories, not sub-capabilities operating inside them.

- Express output locations through tiers and convention-relative directories rather than brittle absolute paths.
- Include one pointer to this section.
- Use exactly one `## Reference Index` table with file, load timing, and obligation columns. Do not split required reads from a reference map or weaken a mandatory resource into a filename-only pointer.

### §5.6a. Quantitative Skill-Design Rules

| Rule | Requirement | Scan columns |
|---|---|---|
| `SKILL.md` body | Under 500 lines | `body_lines`, `line_ok` |
| `references/` | One level, no nested directories | `ref_dir`, `ref_depth_ok` |
| Invocation frontmatter | Manual-only uses `disable-model-invocation: true`; parent/pipeline or subagent-preloaded Skills remain model-invoked; entry routers remain model-invoked and include an English “Use when” trigger | `disable_model`, `invocation`, `use_when` |

`tools/skill-conformance/check.sh` compares scanner output with the invocation registry and must pass before merge. `disable-model-invocation: true` is a hard boundary that also blocks programmatic Skill calls and subagent preload, not a recommendation-strength knob. `user-invocable: false` controls menu exposure separately. `tools/skill-conformance/invocation-policy.tsv` is the deterministic registry; the 13 current parent-invoked sub-Skills must remain model-invoked. `DESIGN_PRINCIPLES §10` owns the qualitative design tenets.

### §5.7. Backward-Compatible Detection

```bash
test -d "<artifact-dir>/_internal" && CONVENTION=modern || CONVENTION=legacy
if [[ $CONVENTION == legacy ]]; then
  REVIEWS_DIR="<artifact-dir>/strategy_reviews"
  VERSIONS_PATTERN="_v{N}.md sibling"
else
  REVIEWS_DIR="<artifact-dir>/_internal/reviews"
  VERSIONS_PATTERN="_internal/versions/v{N}/"
fi
```

Always create `_internal/` for a new artifact, even when empty, to mark modern layout.

## §5.8–§5.11. Operations

Pipeline lock, git preflight, worktree dispatch, and `<agent-home>` push policy moved to `OPERATIONS.md` on 2026-06-23 with numbering preserved.

## §6. Autopilot Flow Matrix

`WORKFLOW.md` owns detailed routing. This section preserves family-wide operational boundaries.

### §6.1. Work-Nature Matrix

| Work | Prior research/analysis | New intent | Asset work |
|---|---|---|---|
| Documents | `autopilot-research` plus paper/doc analysis | `autopilot-draft` | `autopilot-refine` |
| Code in any product shape | Research plus code analysis | `autopilot-spec` with PRD, architecture, and skeleton | `autopilot-code` adds logic over the scaffold |
| One-shot ML prototype | Code-analysis experiment inputs plus prior RUNLOG | No spec for the fast cycle | Iterative `autopilot-lab`, graduating to code |
| Visual design | — | `autopilot-design` | Repeat design cycles |
| User profile | — | `analyze-user --mode init` | `analyze-user --mode update` |

Project experiment conventions are the first source for coding behavior; `mem profile 07_coding_convention` is the cross-project fallback.

### §6.2. Common Invocation Shapes

```text
# Research and experiment
autopilot-research? → analyze-project(code)? → autopilot-spec(research/cli) → autopilot-code → autopilot-lab ↻

# Library and CLI productization
analyze-project → autopilot-spec(library/cli) → autopilot-code ↻

# Documents
autopilot-research? → analyze-project(paper/doc)? → autopilot-draft → autopilot-refine ↻

# Apps
autopilot-research? → analyze-project(code)? → autopilot-spec(app) → autopilot-design? → autopilot-code ↻ → autopilot-ship
```

### §6.3. Separation by Work Nature

Draft and refinement are separate because refinement may compare across prior documents. New and existing code share one implementation flow because only code state changes. Spec and code remain separate because product decisions and skeleton generation differ from logic implementation, while app/library/api/cli/research remain modes of the same spec capability.

### §6.3a. Atomic PRD Updates

Update every affected textual contract and architecture diagram in one transaction.

| Change | Bundle |
|---|---|
| API endpoint, body, or error | API contract, Component, optional Sequence |
| DB entity or field | Data model, backend Component, optional ER |
| UI flow | UI flow, frontend Component, optional Activity |
| External service | Auth contract, Deployment, deploy record, `.env.example` |
| Stack replacement | Stack decision, Component, Deployment |
| State model | Data model, optional State |
| Public library API | Public API, examples, compatibility and semver, module Component |
| CLI command or option | Command, option, exit code, README example, command-tree Component |

App and API modes include Component and Deployment by default. Library Component is optional. ER, Sequence, Activity, State, and Class appear only for complexity or explicit request.

### §6.4. Context Auto-Detection

Code, spec, lab, research, and design inspect their state file to distinguish new work from re-entry, classify the requested stage from the prompt, and present one concise confirmation surface where the capability contract requires it. Each capability's `Context Auto-Detection` section is the source for its stage names. Draft and refine remain separate work types rather than automatic stages of one capability.

### §6.4-staleness. Analysis Refresh

After code changes, `autopilot-code` Step 7 directly updates a small one-module or signature change in `analysis_project/code/`. New modules, model directories, cleanup, or experiment-input changes invoke incremental `/analyze-project --mode code --skip-qa`. Incremental analysis reads `_last_run.yaml` and reanalyzes changed files by default; `--full` redoes everything. Explicit `--no-analyze-update` skips the step.

### §6.4-legacy. Code Context

When `spec/pipeline_state.yaml` exists, read it and activate every applicable app, library, API, CLI, or research mode rule. Without it, infer only lightweight context from cwd signals. App adds design critique, guarded migrations, and deployment awareness; library adds semver/export/example checks; API adds contract and auth security checks; CLI adds command/I/O/exit-code checks; research adds reproducibility and expected-metric checks.

### §6.5. Output Locations

| Capability | Output |
|---|---|
| research | `research/<topic>/` |
| project analysis | `analysis_project/{code,paper,doc}/` |
| spec | `spec/` |
| ship | `spec/ship.md` plus runtime source config at project root |
| standalone design | `designs/<name>/` decision record; live app file is the sole token contract |
| spec-owned design | `spec/design/` decision record |
| code | `plans/<date>_<slug>/` |
| lab | `experiments/<date>_<slug>/` plus `_RUNLOG.md` |
| draft | `documents/<date>_<name>/` |
| refine | Target artifact plus `_internal/versions/v{N}/` |
| note | Run logs in artifact root plus routed cards, digests, and triage under the configured notes target |
| apply | Real source outside artifact root; git branch and commit provide versions, with apply logs under the cheatsheet artifact |

### §6.6. Autopilot Intake Gate

Immediately after entry, if irreversible choices are genuinely under-specified, ask one structured round before production. This is semantic agent judgment, not a keyword or hard-hook classifier.

The round:

1. provides enumerated options for each question;
2. always permits free-form input or proceeding with a recommended default;
3. runs once at entry and never repeatedly;
4. covers only expensive-to-change choices such as stack, public API, deployment target, tone, or brand—not reversible implementation details.

Question banks:

| Track | High-cost choices |
|---|---|
| Documents | Audience, length/page limit, paper/slide/prose form, tone, deadline and constraints |
| Research | Depth, citation/year cutoff, domain boundary, comparison priority, decision purpose |
| App spec | Stack, auth model, persistence, deployment target, core entities |
| Library/CLI spec | Public exports, semver policy, command/options, runtime/package manager, compatibility |
| Design | Visual direction, target device, design-system availability, brand constraints, standalone versus project output |

Code uses the bank for its spec mode. Skip automatically when adapter-native arguments already specify the choice, the user already said it, explicit untracked/throwaway mode applies, or a state file captures it on re-entry. `--no-clarify` exists only for draft and research.

If a non-blocking intake question receives no answer, proceed with the recommended default and report one line. Runtime adapters may provide a scheduled wake-up for a genuinely long wait, but ordinary unanswered intake does not pause the pipeline.

Draft Step 0 and research Step 1.5 are the existing track-specific instances. Spec, code, and design use this common gate.

## §7. Memory

Unified memory moved to `MEMORY.md` on 2026-06-23 with §7 numbering preserved. That file is the single source.
