# Operations — Git, Worktree, Dispatch, and Push (canonical)

> Split from `CONVENTIONS.md` on 2026-06-23 when front- and back-half contracts were separated. Git operations—locks, preflight, worktree dispatch, and `<agent-home>` pushes—differ from artifact conventions and therefore live here. Preserve section numbers and headings because Skills, drills, and hooks link to anchors such as `OPERATIONS.md#59-…`. This is the single source for git operations.

## §5.8. Pipeline Lock — Guarding a Shared Artifact Root Across Worktrees

Every project has one canonical artifact root—`.agent_reports`, with legacy
`.claude_reports` compatibility—resolved by
`utilities/artifact-root.sh <cwd>`. Linked task worktrees are source-only:
their tracked artifact snapshots are read-only, while all workers share the
primary checkout's canonical root through `AGENT_ARTIFACT_ROOT`. Simultaneous
writes to shared `spec/prd.md`, `pipeline_state.yaml`,
`pipeline_summary.md`, or the `_internal/versions/v{N}/` chain can lose updates
or allocate the same version twice. `plans/<cycle>/` is path-separated by
cycle and does not require this lock.

- **Lock file:** `<artifact-root>/.pipeline-lock`, visible to all worktrees. The holder keeps an OS advisory lock for the full transaction, so process exit releases ownership without a stale-age override.
- **Protected scope:** the complete spec transaction is one atomic sequence while the lock is held: re-read latest state → allocate and create the next `_internal/versions/v{N}/` snapshot → update `prd.md` → update `pipeline_state.yaml` → update `pipeline_summary.md`. Reads outside a transaction and path-separated plan writes do not lock.
- **Route declaration:** a route that can touch any `spec/**` path declares `spec_touch=true`. Before lock acquisition the conductor runs §5.9 git-state checks. Missing declaration or a route/node scope mismatch is a structured failure tied to the route id.
- **Contention:** a nonblocking acquisition first reports `BLOCKED`, then waits. After acquiring it re-reads the latest spec and version chain and enters the next version. It never retries a previously computed `v{N}` and never overwrites an existing snapshot.

Acquire immediately before `autopilot-spec` Step 3 or update mode, `autopilot-code` state/summary writes, or a spec-drift update. The helper holds the lock around the supplied transaction command and exports `AGENT_SPEC_NEXT_VERSION` only after the latest version is re-read under lock:

```bash
REPORTS_DIR=$("${AGENT_HOME:-$HOME/agent_setting}/utilities/artifact-root.sh" "$PWD") || exit
python3 "${AGENT_HOME:-$HOME/agent_setting}/utilities/spec-transaction.py" run \
  --artifact-root "$REPORTS_DIR" --worktree "$(pwd -P)" \
  --route "$ROUTE_RECORD" --node "$ROUTE_NODE" --wait-timeout 600 -- \
  sh ./the-owning-capability-transaction.sh
```

Exit 3 means the bounded wait expired; report the current owner and leave every spec surface unchanged. Do not delete the lock or reuse the version number.

The helper releases automatically after normal completion, interruption, or error. The transaction command must fail before its first canonical write if all four output paths cannot be completed.

For a read-only check before touching the spec:

```bash
REPORTS_DIR=$("${AGENT_HOME:-$HOME/agent_setting}/utilities/artifact-root.sh" "$PWD") || exit
[ -f "$REPORTS_DIR/.pipeline-lock" ] && cat "$REPORTS_DIR/.pipeline-lock" || echo "no active edit"
```

In a single-checkout environment the same helper and sequence still apply.
With linked worktrees, the canonical resolver makes one lock visible without
replacing a tracked directory with a symlink.

### §5.9. Git Working-State Preflight

The §5.8 lock protects only artifact writes. It does not detect an active merge or rebase, dirty files, detached HEAD, or the same branch in another worktree. A code-mutating capability, canonically `autopilot-code`, checks once before editing and again before every commit or write-back.

```bash
# Run before code edits and every commit. On STOP, halt and report.
GD=$(git rev-parse --git-dir 2>/dev/null) || { echo "OK non-git"; return 0 2>/dev/null||exit 0; }
op=; [ -f "$GD/MERGE_HEAD" ] && op=merge
{ [ -d "$GD/rebase-merge" ] || [ -d "$GD/rebase-apply" ]; } && op=rebase
[ -f "$GD/CHERRY_PICK_HEAD" ] && op=cherry-pick
br=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo DETACHED)
head=$(git rev-parse --short HEAD 2>/dev/null)
ahead_behind=$(git rev-list --left-right --count @{u}...HEAD 2>/dev/null)
elsewhere=$(git worktree list --porcelain 2>/dev/null | awk -v b="$br" '/^worktree /{w=$2} /^branch /{if($2=="refs/heads/"b && w!=ENVIRON["PWD"]) print w}')
def=$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'); def=${def:-main}
git fetch -q origin "$def" 2>/dev/null
merged_in=$( [ "$br" != DETACHED ] && [ "$br" != "$def" ] && [ "$(git rev-list --count origin/$def..HEAD 2>/dev/null)" = 0 ] && echo yes )
if [ -n "$op" ];        then echo "STOP: $op is in progress; resolve it or abort explicitly before continuing"; fi
if [ "$br" = DETACHED ];then echo "STOP: detached HEAD($head); check out a branch before risking a lost commit"; fi
[ -n "$elsewhere" ] && echo "WARN: branch '$br' is also checked out at $elsewhere"
[ "${ahead_behind%%	*}" -gt 0 ] 2>/dev/null && echo "WARN: upstream is ${ahead_behind%%	*} commits ahead; integrate before continuing"
[ -n "$merged_in" ] && echo "DONE-BRANCH: '$br' is zero commits ahead of origin/$def; start new work from the latest base: git switch -c <new-slug> origin/$def"
echo "state: branch=$br head=$head base=$def dirty=$(git status --porcelain 2>/dev/null|wc -l|tr -d ' ')"
```

- **STOP:** halt edits and commits during merge, rebase, cherry-pick, or detached HEAD and ask for handling. Never auto-abort or force-checkout. `hooks/git-state-guard.sh` hard-denies Edit and Write calls during an operation, including direct paths outside ceremony. `$GITDIR/CLAUDE_MERGE_EDIT_OK` is allowed only when the user explicitly requests conflict resolution; an agent must not invent that permission.
- **WARN:** report one line for the same branch in another worktree, upstream movement, or pre-existing session-independent dirt, then decide how to proceed.
- **DONE-BRANCH:** after a branch is merged into base it is finished. At a new work cycle, a non-base branch that is zero commits ahead and is not a just-created branch for this task must be replaced with `git fetch origin && git switch -c <slug> origin/$def`. This applies to direct edits too; uncommitted work on a dead branch is already drift.
- **Periodic recheck:** remember the entry `head`. Before each commit, stop if `head` changed underneath the session or a new `MERGE_HEAD` appeared. Non-git and single-checkout paths pass harmlessly.

### §5.10. Work Isolation and Parallel Dispatch

Adapter and projection changes follow the same core-first order as other portable work: establish and read the governing `core/` contract before adapter edits. Read and write markers enforce that gate but do not replace review.

Actual edits, tests, and QA run in isolated worktrees while the main session handles triage, dispatch, harvest, and reporting. The depth model prevents both an oversized main context and a monolithic worker that cannot use cross-harness perspectives:

- **depth 0:** user-facing main or orchestrator;
- **depth 1:** capability owner responsible for the entire pipeline;
- **depth 2:** bounded planning, verification, perspective, adversarial, or pipeline-stage worker opened by a `standard+` owner;
- `direct` runs inline, `quick` uses one depth-1 one-shot worker, and depth 3 or greater is forbidden.

The portable role for a `standard+` depth-1 owner is `deep orchestrator`. The retained `orchestrator` role is balanced mechanical coordination of already decided commands, paths, and states; they are not aliases.

**Main-session role contract.** The depth-0 main session is the context owner, router, orchestrator, and final integrator — not the default executor of every stage. It directly owns: memory and existing artifact-root recovery (`.agent_reports/`, legacy `.claude_reports/`); user-intent and artifact-state reconstruction; primary/secondary capability selection under `WORKFLOW §0.2`; spec, guard, worktree, and currentness checks; work decomposition and write-ownership decisions; worker dispatch with registration, liveness watching, and harvest; cross-stage conflict and semantic decisions; final consistency integration of metrics, documents, and notes; and the user-facing response. At `standard+`, when a stage is separable, main does not take on inline: long experiment or evaluation execution, repeated checkpoint inference, bulk figure/media generation, report HTML assembly, mechanical document synchronization, independent verification/QA, or implementation work with a clear file boundary against other stages.

**Main/worker bootstrap boundary.** Every registered headless dispatch and repo-owned background model caller exports `AGENT_SESSION_ROLE=worker` before launch. Legacy adapter markers remain worker evidence and fail closed. Workers retain deterministic safety, scope, routing, handoff, liveness, and verification guards, but they do not inherit main-only automatic model lifecycle: memory injection, briefing, turn-nudge/distill, SessionEnd sync/curation, Fleet title summarization, token-budget context, or interactive-pane publication. Explicit worker bootstrap commands such as `status`, `prompt-signal`, `mode`, capability/mode checks, and agent-chosen `recall` remain available. A worker never manufactures a main session, and its shutdown never launches a curator. This boundary applies equally to depth 1, depth 2, loop/drill invocations, title/distill workers, and runtime-native subagents; depth and role are separate from capability ownership.

**Inline exceptions.** Main or a depth-1 owner may run such work inline only when at least one holds: the work is `direct`/`quick` scale; file or state boundaries make it genuinely non-separable; the worker runtime or headless dispatch is unsupported; hook trust or worktree safety checks fail; the work is tightly coupled to external GPU or process state a worker cannot reach; the user explicitly requires main-session execution; or the stage is so small that dispatch overhead clearly exceeds it. Running `standard+` separable work inline without recording the concrete reason — in `plans/<slug>/_internal/metrics.md` for code cycles, or the experiment `_RUNLOG`/`_internal` for lab cycles — is a contract violation; this generalizes SD-17 beyond code stages.

**Delegation surfaces are distinct.** A *native sub-agent* is runtime-internal delegation (the Claude Code Agent tool; Codex `multi_agent`/`spawn_agent` custom agents). A *registered headless worker session* is a separately launched process (`claude -p`, `codex exec`) governed by this section's worktree, slug, capability/mode/QA, model-role, `jobs.log`, and liveness contract. A restriction on one surface must not be silently extended to the other: "do not use sub-agents" — whether from the user or from runtime policy — restricts native delegation and leaves registered headless dispatch governed by this section, unless the user names both surfaces or a runtime/system policy verifiably restricts both. Claiming both are restricted requires current official documentation plus the adapter's local runtime check (for Codex, `subagent-info --check` and `headless --check`); only then fall back inline with the reason recorded as above. Added after a 2026-07-14 incident where a native sub-agent restriction was over-read as a ban on all headless worker dispatch and a full evaluation pipeline ran inline in the main session.

| Scale | Handling |
|---|---|
| One-off typo, one line, or `direct` work | Work directly in the main working tree |
| Small work routed to `quick` because atomic-direct predicates are incomplete and no promotion signal is present | Depth-1 one-shot worker in an isolated worktree |
| Work promoted to `standard+` by durable scope, shared-contract, resource, resume, verifier, or separability signals | Use a worktree and task branch from the latest base. Features, new modules, and multi-file edits always use a branch; ambiguity resolves toward a branch. Separable multi-file or feature work at `standard+` must use headless dispatch. Team delegation and inline micro-stages are limited to `quick` and genuinely microscopic stages. |
| A new independent request while work is active | Dispatch immediately to a new worktree; do not wait for the first job |

**Token-pressure non-interference:** token or context pressure cannot downshift this table, remove a required stage or depth, skip liveness and registry handling, or weaken worktree, write, spec, sandbox, approval, safety, validation, security, or accessibility guards. Unknown or exceeded budgets preserve the pipeline and surface degraded availability. Only unrequested optional exploration and user-facing verbosity may shrink.

Dispatch rules:

1. **Overlap triage:** if a new request is likely to touch the same files as an active job, queue it behind that job on the same branch. Otherwise it may run in parallel.
2. **Execution and naming:** create the worktree with `git worktree add <path> -b <slug> origin/<base>` using §5.9 base selection. The sole canonical path is the sibling directory `<repo>-wt/<slug>`, such as `Foo-wt/<slug>` for `Foo`; do not invent `<repo>_worktrees/`. `worktree-path-guard` hard-enforces this naming for `git worktree add`, while untracked mode, non-add subcommands, and non-git contexts fail open.
   - **Source-only worktree:** immediately resolve the primary checkout's
     canonical artifact root. Dispatch wrappers inject it as
     `AGENT_ARTIFACT_ROOT`, include it in prompt/registry metadata, and open
     only that external path through runtime-native scoped access (Claude/Codex
     `--add-dir`; OpenCode exact `permission.external_directory` rule).
     Writes to the task worktree's `.agent_reports/**` or
     `.claude_reports/**` snapshot fail closed.
   - **Light team delegation:** open a team agent in the background and name the work root in its prompt. The main session opens QA against that same path. Use only for small, fast iterations.
   - **Quick one-shot:** open one depth-1 owner. Its micro-stages stay inline inside that worker, it opens no depth-2 fan-out, and any mutating quick job uses an isolated worktree.
   - **Full headless ceremony:** launch an adapter-specific headless main in the worktree. It acts as a complete main for that runtime, including team roles, hooks or preflight, and plan artifacts. The adapter owns noninteractive tool and permission setup and documents its cost realization. The top-level dispatch is a depth-1 capability owner that returns only synthesis to main.
   - At `standard+`, the depth-1 owner is a thin conductor. It dispatches `code-plan`, `code-execute`, `code-test`, and `code-report` as separate depth-2 headless sessions, reads verdict and status metadata rather than stage bodies, and passes context only through files. Before any stage, it verifies that the artifact root and `spec/` exist or that `/track` has explicitly selected untracked mode.
   - **Separability under SD-17:** dispatch is mandatory when the stage output contract is complete and its edit surface is not boundary-coupled through shared semantic anchors or sequential boundary assertions. A non-separable stage may run inline only if the reason is recorded in `plans/<slug>/_internal/metrics.md`; missing evidence is a contract violation. Parallelize separable census or independent file groups in-session. Self-modification of dispatch infrastructure additionally requires the orchestrator opt-out `STAGE_DISPATCH_INLINE_OK`.
   - Depth-2 review helpers are read-only by default. Standard usually opens one verifier or planner; strong adds one worker at the riskiest point; thorough and adversarial expand across perspectives. Stage-worker write ownership is disjoint: `code-plan` owns `plans/<slug>/plan/` and `_internal/plan_reviews/`; `code-execute` alone mutates source and owns checklist, dev logs, dev reviews, and plan status; `code-test` owns test logs and reviews while source stays read-only; `code-report` owns `final_report.md`, `analysis_project/code/`, and the locked pipeline summary.
   - The default concurrency cap is five. Count `Σ(active conductors + active stage workers per conductor) ≤ 5`; each stage pipeline is sequential, and in-session implementation-team workers do not count. Queue dispatches that would exceed the cap.
   - Every dispatch prompt exposes capability, mode, QA, intensity, depth, parent slug, parent session ID, worker role, and owner so the adapter UI and registry can identify it.
   - The parent orchestrator chooses a portable model role or a concrete runtime model and effort for each job, or explicitly inherits settings. Wrappers reflect the choice and must not silently pick a default or inherit the interactive model. The orchestrator also chooses the harness.
   - **Cross-harness routing under SD-16:** before dispatch, query each harness through `utilities/usage-check.sh`, which reports `ok`, `limited(reset)`, or `unknown`. Avoid a limited harness, distribute when both are available, place work by runtime strengths, and prefer a checker from a different model family than the maker. Initial weighting is limit avoidance, then task fit, then distribution. `HARNESS_CAPACITY_BIAS` may provide an explicit preference; otherwise remain neutral `auto`. Never hardcode a durable claim that one vendor has more capacity. Current interactive `/usage` and `/status` commands are not headless usage APIs, so the helper conservatively derives limits from `jobs.log` death markers; `ok` means no known block, not guaranteed capacity.
   - **Nested child-spawn eligibility under SD-48:** root headless readiness, native-subagent readiness, and a conductor's ability to launch a registered depth-2 child are separate runtime surfaces. Before compiling a route with depth-2 nodes, bind checked evidence for `(parent_harness,parent_transport,parent_sandbox,child_harness,launch_authority)`. Only `supported` is eligible; `unknown` and `unsupported` fail closed. Logical ownership remains `depth=2,parent=<conductor>` even when a prebound depth-0 `ancestor-broker` performs the OS launch. The current Codex `headless/workspace-write -> codex` conductor tuple is `unsupported(network-operation-not-permitted)` until a newer checked probe supersedes that evidence.
   - **Checked fallback chain under SD-50:** a standard+ stage evaluates `same-harness-headless -> cross-harness-headless -> native-subagent -> inline` in that order. Every headless hop must carry the same route id/node, write scope, completion gate, logical parent, and checked tuple evidence. A conductor-local network failure cannot be retried without changed eligibility evidence and cannot skip directly to inline; use an eligible cross-harness tuple or the prebound ancestor broker first. Native and inline degradation must record the skipped candidates, failure classes, registry attempt ids, and assurance compensation without claiming Fleet parity.
   - **Immediate limit-death handling under SD-15:** wrappers watch briefly after launch. If a child exits immediately on session, usage, or authentication limits, mark its row `done` with `note=dead-<reason>` and, when available, `reset=<time>`. Liveness also recognizes anchored short CLI error lines at the end of logs, but a fresh completion or activity transcript wins over a report that merely discusses limits. Wrappers do not retry; the orchestrator chooses redispatch or failover.
   - **Canonical global attempt registry under SD-49:** depth 0 resolves `<agent-home>/.dispatch/jobs.log` once (or an explicit root fixture path) and passes it immutably as `AGENT_DISPATCH_JOBS` to every descendant and launch broker. For a nested launch, `--jobs` may only repeat that inherited absolute path; a cycle-local override is non-authoritative and fails closed. Every actual start writes a global row before spawn and gives it a stable `attempt_id` plus `launch_authority`, `fallback_ordinal`, route id/node, tuple evidence, and logical parent. A global open/lock failure returns `global-registry-unwritable` with zero children and no local-only row. Optional cycle-local files are audit mirrors, never authority. Existing local-only rows are reconciled by attempt identity (or the legacy route/node/parent/slug key) idempotently while preserving timestamp, status, and failure note. The six tab-separated row fields remain `<ISO-time>`, status, repo, worktree, slug, and pipe; status words remain only `open`, `running`, and `done`.
   - **Fleet notice:** after starting background work, tell the user once that Fleet is the live cross-harness dashboard for stage and liveness status. Its quality depends on complete argv and registry metadata; do not repeat the notice when the user already has Fleet open.
   - **Stealth-death guard:** never wait indefinitely on completion notifications. Use the adapter liveness wrapper: Codex `adapters/codex/bin/preflight.sh liveness [jobs.log]`, OpenCode `adapters/opencode/bin/preflight.sh liveness [jobs.log]`, or Claude/shared `utilities/dispatch-liveness.sh [jobs.log]`. They report `ALIVE`, `SUSPECT`, `DEAD`, or `EXITED`; exit 3 means at least one suspicious or unharvested job. Diagnose through transcript and dispatch-log tails, then harvest or redispatch. Exact recorded `pid` plus `/proc/<pid>/cmdline` is the strongest signal. Transcript or DB mtime is a fallback only because workers sharing a worktree can make each other's directories look fresh; path-based `pgrep` is rejected as false-positive prone.
   - **One-shot wait contract under SD-14:** a headless main, including a conductor, exits when its turn ends. A conductor therefore must not end a turn waiting for a notification after dispatching a stage. It polls within the same turn through `utilities/dispatch-wait.sh`, then harvests. Enforcement combines injected wrapper guidance and the deterministic wait helper. A Claude Stop-hook gate remains disabled because it does not fire reliably under `claude -p` and can corrupt result output.
3. **Merge and cleanup belong to main or the orchestrator:** merge only after an explicit user signal or while harvesting a background job that main dispatched. Do not self-merge the current turn's substantive branch; finish with the branch and a concise report while preserving main unless the user has already authorized integration. Review `git diff main...<branch>`, skip regressions or duplicated work, resolve conflicts by interpreting both intents rather than choosing a side automatically, stop when ambiguity would revert an established result, and verify the integrated build. “Merge everything” means merge all valid work selectively, not blindly accept every diff.
   - After merge, integrated verification, and a successful push of the
     integration ref, main automatically runs
     `utilities/worktree-cleanup.py --check --worktree <path>` and then the
     same command with `--apply` when eligible. The state machine blocks the
     primary worktree, dirty/untracked state, Git operations, locks, unmerged
     HEADs, an integration ref not synchronized with its upstream, and active
     exact job PIDs or process cwd. It never uses `--force`, and the branch is
     retained as a rollback point.
   - Cleanup does not copy or harvest agent artifacts: workers wrote them to
     the canonical root from the start. A stale matching open registry row is
     reconciled to `done,note=cleanup-merged` only after every other safety
     gate passes. `--all-eligible` considers only worktrees referenced by the
     selected jobs registry; `git worktree lock` is an explicit keep veto.
   - Runtime lifecycle events such as Claude `SessionEnd`, Codex `Stop`, or
     OpenCode `session.idle` do not prove merge/push completion and must never
     perform destructive cleanup. They may expose diagnostics only.
4. **Shared artifacts:** route writes to shared artifact-root files through the §5.8 lock. `plans/<slug>/` remains path-separated and noncontending.
5. **Context:** when coordination records pressure the main context, propose a post-it handoff under the global continuity rule.

### §5.11. Commit and Push Policy for `<agent-home>`

After validating changes to instructions, rules, hooks, preflight, or runtime status surfaces under `<agent-home>`, commit and push them in the same turn without a separate user signal. This policy was ratified on 2026-06-12. A work repository's push is separate and remains subject to its deployment gate.

---
# Governed workers and detached resources

All repo-launched model-backed workers pass through `utilities/model-worker-governor.py`, which applies a global cap, per-class caps, rolling start budget, kill switch, and PID/starttime stale-lease cleanup. Its shared state lives under the canonical artifact root so the main checkout and linked workers use one writable governor. Admission checks do not consume the rolling start budget, and a launched worker inherits the same governor root before it can dispatch a child. This does not modify runtime-owned native subagent limits.

Registered model-backed jobs remain owned by the dispatching session even when the runtime launcher uses a background OS process. The main or depth-1 conductor launches, polls, harvests, and integrates the job in the same task flow; an absent OS parent does not grant an independent lifecycle or permit the orchestrator to end early. Only long-running non-model resource jobs use the independent `utilities/resource-runner.py` lifecycle. Reattachment and signals for those resource jobs require PID, process start time, process group, command identity, absolute cwd, log, and run-registry identity rather than PID alone.
