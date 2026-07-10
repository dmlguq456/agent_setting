---
name: stage-dispatch-phase2
slug: 2026-07-10_stage-dispatch-phase2
status: planned
mode: dev
intensity: strong
qa: standard
spec: .agent_reports/spec/stage-dispatch/prd.md
spec_scope: "§12 Phase 2 (v2) + §8.5 + §9 surfaces 8·8b·9b·9c·9d·10·11·14 (SD-10~14 · SD-OPEN-2)"
created: 2026-07-10
owner: autopilot-code
excluded_paths: ["loops/**", "tools/fleet/**"]
---

# Plan — stage-dispatch Phase 2 (배선 완성 + 확산 + drill 회귀)

> **Blueprint SoT**: `.agent_reports/spec/stage-dispatch/prd.md` — §12 Phase 2, §8.5 (SD-10~14), §9 surface table, §13/§14 decision list. This plan implements Phase 2 only; Phase 1 (§9 surfaces 1–7, 8-partial, 9, 10, 11 core reversal) is already merged (5b7cf33) and verified via pilot.
>
> **Excluded — never edit (other-session-owned)**: `loops/**` (drill runner) and `tools/fleet/**`. The drill regression case is authored as a **handoff artifact under this plan directory** (Phase I), not written into `loops/`.
>
> **core-first**: core doc edits (Phase B) precede all derived adapter/skill/wrapper edits. Verify with the anchors quoted per step; the live file is truth — re-read and match exact current wording before editing (Phase-1 already updated most core surfaces, so several §9-listed "current wordings" are stale; each step below flags where current text already reflects stage-dispatch).

## Orientation — what Phase 1 already did (do NOT re-do)

Empirically re-verified 2026-07-10 in this worktree (core-docs research pass):

- `core/OPERATIONS.md §5.10` line 94 already carries the thin-conductor stage-dispatch narrative (③), the class-scoped depth-2 write ownership (④), the `Σ(conductor+active stage) ≤ 5` concurrency rule (⑤), and the explicit-model-role rule (⑦). Line 98 carries the stealth-death liveness guard.
- `core/CONVENTIONS.md §1` line 34 (stage graph Dispatch policy) and line 46 (Depth contract, two depth-2 uses incl. stage-workers) already reflect stage dispatch.
- `core/WORKFLOW.md §1.1` line 57 already says the standard depth-1 owner is a thin conductor dispatching each stage.
- `core/DESIGN_PRINCIPLES.md §8` line 226 already records the SD-1/SD-2 promotion; line 254 change-history entry present.
- `adapters/{claude,codex,opencode}` bootstrap §0(C)/AGENTS.md already carry the conductor→stage depth-2 language (claude CLAUDE.md §0(C); codex AGENTS.md line 69; opencode AGENTS.md line 60).
- `skills/autopilot-code/references/context-and-guards.md` line 52 already reverses the "금지" to "기본 권장".
- `dispatch-headless.py` already supports `--depth 2 --parent --worker-role --owner --profile`, gates depth≥3, and injects a depth-2 stage-worker `depth_note` for `code-*` roles (lines 159–186).

**What is missing (this plan's actual work)** — the "half-wiring" (§8.5.1) and the new SD-11/12/13/14 mechanisms:
1. `dev-pipeline.md` Step 1~7 **body** is still `invoke Skill: code-<stage>` imperative (dual signal); the front-matter contract block has an unbounded `e.g.` escape hatch (SD-10).
2. `SKILL.md` Stage Graph table has no dispatch-mode annotation (SD-10b).
3. No SD-11 reminder hook; no SD-14b Stop gate; no `dispatch-wait.sh`; wrapper `depth_note` for depth-1 lacks the one-shot wait contract; registry gap (SD-14b②) unfixed; conductor cannot see its own slug.
4. No stage-worker profile fragments (SD-12).
5. No SD-13 spec-precondition wording in the conductor contract.
6. Diffusion to draft/research/spec/design/lab pipes not done (WORKFLOW §5 rows + each pipe's stage-dispatch contract).
7. No stage-dispatch drill case definition.

---

## Phase A — SD-14b① prerequisite: empirically verify `-p` mode Stop hook fires (gating probe, no source edit)

> **Why first**: SD-14b (conductor Stop gate) is only valid if a `claude -p` one-shot session actually fires the `Stop` hook at turn end. The spec (§8.5.7, §12-0) makes this an explicit precondition: **if Stop does not fire, hold the Stop gate** and ship only SD-14 (a) depth_note + (c) dispatch-wait. This phase produces the verdict that branches Phase E hook B.

### Step A1 — Probe `Stop` firing under `claude -p`
- **Action** (scratch, no repo mutation): create a throwaway config home with a `Stop` hook that appends a sentinel line to a temp file, then run a trivial `claude -p` turn against it.
  - Concretely:
    ```bash
    T=$(mktemp -d)
    mkdir -p "$T/home/hooks"
    cat > "$T/home/hooks/stop-probe.sh" <<'EOF'
    #!/bin/sh
    echo "STOP_FIRED $(date -u +%FT%TZ)" >> "$STOP_PROBE_OUT"
    exit 0
    EOF
    chmod +x "$T/home/hooks/stop-probe.sh"
    cat > "$T/home/settings.json" <<EOF
    { "hooks": { "Stop": [ { "matcher": "*", "hooks": [ { "type": "command", "command": "sh \"$T/home/hooks/stop-probe.sh\"", "timeout": 10 } ] } ] } }
    EOF
    STOP_PROBE_OUT="$T/fired.log" CLAUDE_CONFIG_DIR="$T/home" claude -p "say ok" >/dev/null 2>&1 || true
    echo "--- probe result ---"; cat "$T/fired.log" 2>/dev/null || echo "(Stop did NOT fire)"
    ```
  - Note env var name: the wrapper marks child sessions with `CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH` (dispatch-headless.py lines 384–386). The probe does not need these; it only decides whether `Stop` fires **at all** in `-p` mode.
- **Record**: write the outcome to `_internal/dev_reviews/phaseA_stop_probe.md` (execute stage) and surface it in `test_logs/` + `final_report.md`.
- **Branch (decision recorded in checklist Decision Points)**:
  - **Fires** → Phase E installs hook B (conductor Stop gate) + settings registration + conformance test.
  - **Does NOT fire** → Phase E **skips** hook B registration entirely; instead adds a short note in the Stop-hook script header (kept on disk, un-registered) and records "Stop gate held: `-p` Stop unfired (probe <date>)" in `final_report.md`. SD-14 still ships via (a) depth_note wait contract + (c) `dispatch-wait.sh`. **This is a hard branch — do not register a hook that never fires.**

### Step A2 — Runtime-currentness check (bounded)
- Per the global Runtime-currentness gate, before finalizing the Stop-hook decision, do a quick sanity check of current Claude Code hook docs for `Stop` behavior under `-p`/headless (WebFetch/WebSearch, ≤2 queries). If official docs contradict the probe, prefer the probe (empirical) but note the discrepancy in `final_report.md`. Do not block on this — the probe is authoritative for the branch.

---

## Phase B — Core doc increments (core-first; edit these before any derived file)

> All four core files already carry the Phase-1 stage-dispatch language. Phase 2 adds only: **SD-14 one-shot wait contract** + **SD-13 spec precondition** (OPERATIONS), **diffusion rows + new lab row** (WORKFLOW §5), a **capability-neutral diffusion clarifier** (CONVENTIONS §1), and a **light SD-14 determinism note** (DESIGN_PRINCIPLES §8/§0.7). Keep edits minimal and additive — do not rewrite existing sentences that already work.

### Step B1 — `core/OPERATIONS.md §5.10`: SD-14 one-shot wait contract + SD-13 spec precondition
- **File**: `core/OPERATIONS.md`. Target the §5.10 "풀 ceremony (headless 분사)" bullet at **line 94** and the stealth-death guard at **line 98** (re-locate by content — line numbers may drift).
- **Current (line 98, verbatim head)**: `**stealth-death 가드 (분사 후 대기 자리 — 필수, §0.5 결정론)**: ⚠️ hung/crash 한 adapter-specific headless main 은 _exit 를 안 해 완료 알림이 영영 안 올 수 있다_ …` (continues with the ALIVE/SUSPECT/DEAD liveness-command contract).
- **Edit direction (SD-14, additive)**: immediately after the stealth-death guard sentence, add a **one-shot wait contract** clause (new, distinct from stealth-death):
  > **one-shot 대기 계약 (§8.5.7 SD-14)**: adapter headless main(conductor 포함)은 **one-shot 프로세스** — turn 종료 = 프로세스 종료다. background 완료 알림은 그 프로세스가 살아 있을 때만 유효하므로, conductor 는 스테이지 분사 후 **Monitor·완료 알림 대기로 turn 을 끝내지 않는다**; 같은 turn 안에서 `utilities/dispatch-wait.sh`(dispatch-liveness 재사용) 반복 호출로 스테이지 종료를 폴링한 뒤 수확한다. 대기 계약의 결정론 강제는 (a) wrapper depth_note 주입 + (b) conductor Stop hook 게이트(open 자식 row 시 차단, `-p` Stop 발화 검증 전제) + (c) `dispatch-wait` 헬퍼 3층.
- **Edit direction (SD-13, additive)**: in the ③ conductor narrative (line 94), add one clause on spec precondition:
  > **spec 전제 선보장 (§8.5.4 SD-13)**: conductor 는 스테이지 분사 _전_ 대상 repo 의 spec 전제(artifact root 존재 + `spec/` 존재 또는 `/track` untracked)를 선확인한다 — 스테이지 세션은 풀 ceremony(artifact-guard 생성-순서 게이트 포함)를 받으므로, 전제 미충족을 스테이지 안에서 차단으로 발견하면 재분사 비용, conductor 게이트에서 잡으면 무료.
- **Verify**: `grep -n "one-shot 대기 계약\|spec 전제 선보장" core/OPERATIONS.md` returns both; `grep -c "stealth-death" core/OPERATIONS.md` unchanged (no duplication of existing guard).

### Step B2 — `core/WORKFLOW.md §5`: diffusion rows + new autopilot-lab row
- **File**: `core/WORKFLOW.md` §5 table (header line 105, rows lines 111–119).
- **Current** (autopilot-code row 115 already reflects stage dispatch; the diffusion targets do NOT):
  - `111 autopilot-research`: `연구팀 research-survey + 자료팀 … + 연구팀 fact-check`
  - `113 autopilot-spec`: `기획팀(PRD 위임) + 자료팀(research import) / setup: 호스팅·CI/CD logic`
  - `114 autopilot-design`: `디자인팀 maker + 디자인팀 critic + 자료팀 web-image-search`
  - `117 autopilot-draft`: `자료팀(…) + 개발팀(writing) + 편집팀 polish + 연구팀 fact-check`
  - `118 autopilot-refine`: `autopilot-draft 와 동일 재활용 + 편집팀 review`
  - **autopilot-lab row does not exist** in §5.
- **Edit direction**: append to each of rows 111/113/114/117/118 a short clause mirroring row 115's pattern:
  > `` `standard+` 에선 각 durable 스테이지가 **독립 headless 세션**(OPERATIONS §5.10 ③④)이고 위 팀은 그 스테이지 세션 _안_ 에서 실행 — depth-1 conductor 는 산출물 경로만 넘긴다. `direct/quick` 은 inline. ``
  - Per-pipe stage-worker class = the §6-homolog table each pipe carries (Phase H). Keep the WORKFLOW row clause generic; the concrete stage→class map lives in each pipe's reference doc (Phase H) to avoid duplicating the mapping in two places.
- **New row (autopilot-lab)**: insert a new row after 118 (or grouped with research/experiment entries):
  > `| **autopilot-lab** | (setup) 연구팀 plan-review + 개발팀 new-lib scaffold + 테스트팀 smoke / (eval) 테스트팀 functional + 자료팀 figure-gen + 연구팀 research-survey. `standard+` setup/eval 스테이지는 독립 headless 세션(OPERATIONS §5.10 ③④), 팀은 세션 _안_. `direct/quick`·단발 실험 run 은 inline |`
- **Verify**: `grep -n "autopilot-lab" core/WORKFLOW.md` shows the new §5 row; each diffusion row now contains "독립 headless 세션".

### Step B3 — `core/CONVENTIONS.md §1`: capability-neutral diffusion clarifier (light)
- **File**: `core/CONVENTIONS.md §1`, Depth contract at **line 46** (already lists stage-workers with `code-plan/execute/test/report`).
- **Current (line 46, relevant clause)**: `(b) **pipeline stage-workers** — the conductor dispatches each sub-skill stage (e.g. code-plan/execute/test/report) as its own depth-2 headless session …`
- **Edit direction (additive, one clause)**: generalize the parenthetical so the stage-worker class is not read as code-only:
  > `… each sub-skill stage (code-* for autopilot-code; the homologous stage set for autopilot-draft/research/spec/design/lab — see each pipe's stage-worker table) as its own depth-2 headless session …`
- The stage-graph Dispatch-policy column (line 34) is intensity-keyed and capability-neutral — **no edit needed** (it already applies to every `standard+` pipe). Confirm and note in dev_logs that no change was required there.
- **Verify**: `grep -n "homologous stage set" core/CONVENTIONS.md` returns the clause.

### Step B4 — `core/DESIGN_PRINCIPLES.md`: SD-14 determinism note (light)
- **File**: `core/DESIGN_PRINCIPLES.md`. §8 line 226 already records SD-1/SD-2. §0.7 (lines 39–61) is the semantic↔rule boundary section.
- **Edit direction (§8, one appended sentence to the existing 226 note)**:
  > 대기·수확도 이 결정론 흐름의 일부다 (SD-14): conductor 의 스테이지 대기는 완료 알림 신뢰가 아니라 `dispatch-wait`(liveness 재사용) 폴링 + Stop hook 게이트로 결정론화되고, 죽은 스테이지 해석만 conductor 의미 판단으로 남는다.
- **Edit direction (§0.7 coverage, optional — only if it reads naturally)**: mirror PRD §14 v2 additions in one clause — SD-11 이 deny 아닌 reminder 로 시작(intensity 를 hook 이 결정론적으로 알 수 없는 구간 존중), SD-14b 피드백이 "대기 강제"가 아니라 liveness 진단→행동 분기. If §0.7's existing enumerated list has a natural insertion point, add; otherwise skip and leave the PRD §14 as the SoT (do not force).
- **Verify**: `grep -n "SD-14" core/DESIGN_PRINCIPLES.md`.

---

## Phase C — SD-14 wrapper increments + `dispatch-wait.sh` helper

> **Re-measure first (§8.5.7 note)**: another session may have already patched the `AGENT_HOME` registry gap. Before editing, re-read `dispatch-headless.py` `resolve_agent_home()` (line 269–273) and `utilities/agent-home.sh`; only apply the fix if the gap still exists. Confirmed present at plan time: `resolve_agent_home()` falls back to `ROOT` (= `parents[3]` = worktree) while `agent-home.sh` falls back to `$HOME/agent_setting`.

### Step C1 — Fix SD-14b② registry gap in `dispatch-headless.py`
- **File**: `adapters/claude/bin/dispatch-headless.py`, function `resolve_agent_home()` (lines 269–273):
  ```python
  def resolve_agent_home() -> Path:
      env_home = os.environ.get("AGENT_HOME")
      if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
          return Path(env_home)
      return ROOT
  ```
- **Problem**: when `AGENT_HOME` is unset, the wrapper writes `jobs.log` under `ROOT/.dispatch` (worktree), but `utilities/dispatch-liveness.sh` (and the future Stop hook + `dispatch-wait.sh`) resolve the registry via `agent-home.sh` → `$HOME/agent_setting/.dispatch`. Different registries → the Stop gate/liveness never see the rows the wrapper wrote.
- **Edit direction**: after the `AGENT_HOME` check, fall back to the **same chain as `agent-home.sh`** (`CLAUDE_HOME` → `$HOME/agent_setting` if it has `core/CORE.md` → `$HOME/.claude` if it has `core/CORE.md`), and only then to `ROOT`:
  ```python
  def resolve_agent_home() -> Path:
      def _valid(p):
          return p and (Path(p) / "core" / "CORE.md").is_file()
      for cand in (os.environ.get("AGENT_HOME"),
                   os.environ.get("CLAUDE_HOME"),
                   str(Path.home() / "agent_setting"),
                   str(Path.home() / ".claude")):
          if _valid(cand):
              return Path(cand)
      return ROOT
  ```
  Rationale: mirrors `agent-home.sh` preference order so writer (wrapper) and readers (liveness/Stop/dispatch-wait) agree on one registry. Keep `ROOT` as last resort so an isolated worktree with no installed home still works.
- **Verify**: `AGENT_HOME= CLAUDE_HOME= python3 adapters/claude/bin/dispatch-headless.py --dry-run --worktree "$PWD" --slug t --capability code-plan --mode dev --qa standard --depth 1 --model-role "deep maker" | grep job_registry` prints a path equal to `"$(utilities/agent-home.sh)/.dispatch/jobs.log"`. Cross-check with `utilities/dispatch-liveness.sh` reading the same file.

### Step C2 — Inject `AGENT_DISPATCH_SELF_SLUG` into the child env (needed by the Stop gate)
- **File**: `adapters/claude/bin/dispatch-headless.py`, the `action == "start"` env block (lines 383–393).
- **Problem**: the child session receives `AGENT_DISPATCH_PARENT_SLUG` (its parent) but **not its own slug**. The conductor Stop gate must identify "open jobs whose `parent=` equals *my own* slug" — impossible without the self slug.
- **Edit direction**: add `env["AGENT_DISPATCH_SELF_SLUG"] = args.slug` to the `env.update({...})` dict.
- **Verify**: dry-run print already lists `slug=`; add a one-line assertion in dev_logs that the start env now carries `AGENT_DISPATCH_SELF_SLUG`. (Behavior test deferred to the drill case, Phase I.)

### Step C3 — Add SD-14 one-shot wait contract to the depth-1 `depth_note`
- **File**: `adapters/claude/bin/dispatch-headless.py`, `dispatch_prompt()` depth-1 `else` branch (lines 178–186), current:
  ```
  "Depth contract: depth 1 is a capability-owner worker. It should open bounded depth-2 sub-workers for separable standard+ work; for standard+ pipelines it acts as a thin conductor that dispatches each stage (code-plan/execute/test/report) as its own depth-2 session with file-only handoff. thorough/adversarial expands review to multi-axis or adversary workers. Direct/quick stay inline unless explicitly escalated; depth 3+ is forbidden.\n"
  ```
- **Edit direction**: append the one-shot wait clause to this depth-1 note (only depth-1 — stage-workers depth-2 do not wait on children):
  > ` You are a one-shot process: ending your turn ends the process, and background completion notifications never arrive after that. After dispatching a stage, do NOT end the turn on a Monitor/notification wait — poll within the same turn using utilities/dispatch-wait.sh (which reuses dispatch-liveness) until the stage row leaves 'open', then harvest its artifact verdict and dispatch the next stage. On SUSPECT/DEAD, diagnose and re-dispatch rather than waiting.`
- **Verify**: `python3 adapters/claude/bin/dispatch-headless.py --dry-run --worktree "$PWD" --slug t --capability autopilot-code --mode dev --qa standard --depth 1 --model-role "orchestrator" | grep -c "one-shot"` — but note dry-run prints command not prompt; instead assert on the generated `*.prompt.txt` via `--register` into a temp `--jobs`/`--log-dir`, then `grep "one-shot process" <log-dir>/t.claude.prompt.txt`.

### Step C4 — New helper `utilities/dispatch-wait.sh`
- **File (new)**: `utilities/dispatch-wait.sh` (repo-root utilities, mirrored to `adapters/claude/utilities/` if that mirror convention holds — check: `dispatch-liveness.sh` exists in both `utilities/` and `adapters/claude/utilities/`; replicate the same dual placement, or a symlink, matching the existing pattern).
- **Contract** (reuse `dispatch-liveness.sh`, do not reimplement liveness):
  - Usage: `dispatch-wait.sh [--parent <self-slug>] [--jobs <path>] [--interval <s>] [--max <s>]`.
  - Resolves registry the same way liveness does (`AGENT_HOME` → `agent-home.sh`), so it matches C1.
  - Loops (bounded, per-call `--max` ≤ 600s to respect a single Bash timeout): each iteration
    1. count `open` rows in jobs.log with `parent=<self-slug>` (if `--parent` given) — if zero → `exit 0` (all children done → harvest).
    2. else run `dispatch-liveness.sh <jobs>`; if it exits 3 (SUSPECT/DEAD) → print the offending rows and `exit 3` (caller diagnoses/re-dispatches, does not keep waiting).
    3. else `sleep <interval>` (default 20s) and repeat until `--max`; on timeout `exit 2` (caller re-invokes — repeated-call form, so the conductor's next Bash call continues the poll).
  - Exit codes: `0` = target children done (harvest), `2` = still alive, poll again (re-call), `3` = SUSPECT/DEAD (diagnose). Print a one-line status each iteration.
  - POSIX sh, `set -uo pipefail`, source `agent-home.sh` like liveness; **no background processes, no nohup** (§ stage-worker duty — synchronous only).
- **Verify**: `sh utilities/dispatch-wait.sh --jobs /nonexistent --parent x` → exits 0 with "(no open children)"; construct a temp jobs.log with one `open` row whose parent matches and a fresh fake transcript → exits 2 (alive); with a stale/absent transcript → exits 3. Add these to a small `utilities/dispatch-wait.test.sh` mirroring `dispatch-liveness.test.sh` (conformance layer, per HOOKS.md — deterministic, not drill).

---

## Phase D — SD-12 stage-worker profiles (fragments + declarations)

> Model: `profiles/lab-runner.yaml` + `profiles/fragments/lab-runner.md`. Loader = `tools/profile/build-home.py`: yaml requires `name/description/harness`, `model_role` **XOR** `model`, `fragments:` list of repo-relative paths that must exist, `expose:` with only `{skills,agents,triggers}`. Bootstrap = plain concat of `templates/bootstrap-<harness>.md` + fragments in order.

### Step D1 — Create 4 fragment files `profiles/fragments/code-{plan,execute,test,report}.md`
- Each = a minimal L2 role fragment, heading `## L2 — code-<stage> specialization`, containing only that stage's contract: (i) its sub-skill role + the in-session team it delegates to (기획팀 / 개발팀 / 품질관리팀 test / 품질관리팀 report), (ii) its input-artifact paths and output-artifact write class (§6 / OPERATIONS §5.10 ④), (iii) file-only handoff + "read inputs from files, never prior-stage conversation", (iv) "no re-dispatch (depth-1 forbidden from here); internal parallelism = in-session teams". Model each closely on `fragments/lab-runner.md`'s four subsections (specialization / discipline / convention / stay-in-lane).
  - **code-plan**: writes `plans/<slug>/plan/{plan.md,plan_ko.md}` + `_internal/plan_reviews/`; reads task + prior `plans/`. Delegates to 기획팀.
  - **code-execute**: writes source + `plans/<slug>/{checklist.md,dev_logs/,_internal/dev_reviews/}` + plan frontmatter `status`; reads `plan/plan.md`. Delegates to 개발팀. Note: **only stage that mutates source**.
  - **code-test**: writes `plans/<slug>/{test_logs/,_internal/test_reviews/}` (source read-only); reads `plan.md` verification section + `checklist.md`. Delegates to 품질관리팀 test mode.
  - **code-report**: writes `final_report.md` + `analysis_project/code/*` + `pipeline_summary.md` (via §5.8 lock); reads plan/checklist/dev_logs/test_logs/_reviews. Delegates to 품질관리팀 fast writer.
- Keep each ≤ ~30 lines — the point is a *minimal* bootstrap vs full CLAUDE.md (SD-12 token saving).

### Step D2 — Create 4 declarations `profiles/code-{plan,execute,test,report}.yaml`
- Each mirrors `lab-runner.yaml`:
  - `name: code-<stage>`; `description:` one line (routing label for main).
  - `harness: claude`.
  - `model_role:` per CONVENTIONS §2.3 / SD-5: code-plan=`deep maker`, code-execute=`fast implementer`, code-test=`fast reviewer` (variable — the conductor may override to deep at strong+; the profile default is fast), code-report=`fast writer`. (Use `model_role`, not concrete `model` — portable boundary.)
  - `fragments: [profiles/fragments/code-<stage>.md]`.
  - `expose:` minimal — `skills: [code-<stage>, autopilot-code, post-it]` (+ `analyze-project` for code-report's analysis_project update), `agents:` the one team it uses (`plan-team`/`dev-team`/`qa-team`), `triggers: []`.
- **Note on model override**: the profile's `model_role` is the *default*; the conductor's `dispatch-headless.py --model-role <role>` on the dispatch line still governs (SD-5 explicit selection). Document in the fragment that the profile default may be overridden per-dispatch.

### Step D3 — Register in `profiles/README.md` catalog + validate
- Add 4 rows to the `profiles/README.md` catalog table (name + one-line description) so main can route by name.
- **Verify**: for each stage, `python3 tools/profile/build-home.py code-<stage> --check` exits 0 (declaration/template/fragment exist + deterministic reassembly). Fix any XOR/field/path errors the checker reports.

### Step D4 — Instrumentation hook for SD-12/SD-OPEN-1 (measurement, not gating)
- The conductor's dispatch line (Phase F) passes `--profile code-<stage>`; the jobs.log row then carries `profile=code-<stage>` (wrapper already appends it, line 261–262). No code change needed to *record* the profile. For token/time comparison, Phase J defines the instrumentation log format; here just ensure the profiles are wired so full-bootstrap-vs-minimal-profile can be compared later.

---

## Phase E — Hooks: SD-11 reminder (soft) + SD-14b Stop gate (gated by Phase A)

> HOOKS.md contract: a hook's **output shape** belongs in the **conformance** layer (`hooks/portable-guards.test.sh`), never drill; only agent **behavior** goes to drill (Phase I). Register new hooks in the HOOKS.md Invariant Catalog. Both hooks here are **never-block-on-error** (fail-open) except the Stop gate's intentional deterministic block.

### Step E1 — `hooks/stage-dispatch-reminder.sh` (SD-11, soft / non-deny)
- **File (new)**: `hooks/stage-dispatch-reminder.sh`. Pattern: `PreToolUse(Skill)` matcher, but **emit `additionalContext` (non-deny)** like `spec-sync-nudge.sh`, not a `deny` like `worktree-path-guard.sh`. Parse `tool_input.skill` like `spec-skill-gate.sh` does.
- **Fire condition (all must hold, else clean `exit 0`)**:
  - env `CLAUDE_CODE_CHILD_SESSION=1` **and** `AGENT_DISPATCH_DEPTH=1` (this is a conductor, not main, not a depth-2 stage session), **and**
  - `AGENT_DISPATCH_INTENSITY` ∈ {`standard`,`strong`,`thorough`,`adversarial`} (not `direct`/`quick` — those legitimately run inline; this is why deny is wrong and reminder is right, §8.5.2), **and**
  - the invoked `skill` ∈ {`code-plan`,`code-execute`,`code-test`,`code-report`}.
  - Recursion guard: `[ "${MEM_DISTILL:-}" = "1" ]` → drain stdin, `exit 0` (mirror the memory hooks).
- **Emitted `additionalContext`** (reminder, not block):
  > `📌 stage-dispatch: 이 세션은 depth-1 conductor(intensity=<..>)입니다. code-<stage> 를 in-session Skill 로 직접 부르는 대신 dispatch-headless.py --depth 2 --parent $AGENT_DISPATCH_SELF_SLUG --worker-role code-<stage> 로 스테이지를 분사하고 dispatch-wait 로 수확하세요 (dev-pipeline Step 1~7). in-session Skill 은 direct/quick 또는 headless-불가 런타임 fallback 자리에서만.`
- **Why soft (do not deny)**: the hook cannot deterministically know whether this is a legitimate headless-unavailable-runtime fallback; deny risks false positives. Deny escalation is deferred pending drill/instrumentation (§8.5.2, §14-(4)).
- **Register**: `adapters/claude/settings.json` `PreToolUse` array, new entry `{ "matcher": "Skill", "hooks": [ { "type":"command", "command":"sh \"$HOME/.claude/hooks/stage-dispatch-reminder.sh\"", "timeout":10 } ] }` (co-exists with the existing `spec-skill-gate.sh` Skill matcher).
- **CLI mode**: support `--skill/--cwd/--session/--depth/--intensity` like the other guards for the conformance test.
- **Conformance test** (`hooks/portable-guards.test.sh`): add cases — (i) conductor+standard+code-plan → emits additionalContext; (ii) direct/quick → no-op; (iii) depth-2 stage session → no-op; (iv) non-code skill → no-op; (v) main (no child env) → no-op.

### Step E2 — `hooks/conductor-stop-gate.sh` (SD-14b) — **conditional on Phase A verdict**
- **Only if Phase A Step A1 shows `Stop` fires under `-p`.** If it does not fire: create the script on disk (for future use) with a header note "UNREGISTERED: `-p` Stop unfired as of <date> probe — see final_report" but **do not add it to settings.json**; record the hold in `final_report.md`. Skip the rest of this step's registration + the conformance firing test (keep only the CLI unit test).
- **File (new)**: `hooks/conductor-stop-gate.sh`. `Stop` matcher.
- **Fire condition**: env `CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH=1` (conductor) + `AGENT_DISPATCH_SELF_SLUG` set (from C2). Else clean `exit 0`. Recursion/loop guard: respect `stop_hook_active` in the Stop payload — if already active, `exit 0` (no infinite block). Memory-distill guard as above.
- **Logic**:
  1. Resolve jobs.log via `agent-home.sh` (same registry as C1/liveness).
  2. Count `open` rows where `parent=$AGENT_DISPATCH_SELF_SLUG`. If zero → `exit 0` (conductor may finish).
  3. If ≥1 open child: run `utilities/dispatch-liveness.sh <jobs>`:
     - **ALIVE** (exit 0, no SUSPECT) → **block Stop** with action feedback: "열린 스테이지 자식 N개가 아직 실행 중 — turn 을 끝내지 말고 dispatch-wait 로 폴링 후 수확하세요." (deterministic block: emit the Stop-hook deny/continue JSON per Claude's Stop hook schema — `{"decision":"block","reason":"..."}` or the current `hookSpecificOutput` equivalent; confirm exact schema against live docs in Phase A Step A2.)
     - **SUSPECT/DEAD** (exit 3) → **do not force waiting** (avoid the inverse hang where a dead stage traps the conductor forever): block with **action** feedback = "스테이지 자식이 SUSPECT/DEAD — 대기 금지. transcript tail·dispatch 로그로 진단 → 수확 또는 재분사 → jobs.log row 정리 후 종료." (§8.5.7, §14-(5): feedback is a liveness→action branch, not "keep waiting".)
- **Register** (only on Phase A fires): `adapters/claude/settings.json` `Stop` array, new entry alongside the existing `herdr-agent-state.sh idle` Stop hook.
- **CLI mode + conformance test**: `--self-slug/--jobs/--stop-active` flags; conformance cases — no open children → exit 0; open+alive → block; open+dead → block-with-diagnose; stop_hook_active → exit 0; non-conductor env → exit 0. (These are deterministic output-shape assertions → conformance, per HOOKS.md.)

### Step E3 — HOOKS.md Invariant Catalog + settings parity
- Add both hooks to `core/HOOKS.md` Invariant Catalog (name, event, invariant, fail-open note; Stop gate marked "conditional on `-p` Stop firing").
- **Parity note**: codex/opencode adapters have their own hook bridges. SD-11/SD-14b are Claude-first; add a one-line parity note in the codex/opencode `AGENTS.md` dispatch section (Phase G) that the conductor one-shot wait contract applies there too via their `preflight.sh liveness` (they already document liveness-while-waiting). Do **not** port the Claude hook scripts to other adapters in this phase (out of scope; note as follow-up).

---

## Phase F — SD-10: `dev-pipeline.md` dispatch-first rewrite + `SKILL.md` Stage Graph

> This is Phase 2 **priority 0**. References the mechanisms from Phases C–E (dispatch-wait, profiles, hooks) — those must exist first so the rewritten commands are runnable/verifiable.

### Step F1 — Rewrite `dev-pipeline.md` Step 1~7 to dispatch-first imperative
- **File**: `skills/autopilot-code/references/dev-pipeline.md`.
- **Remove the unbounded escape hatch** (line 4 contract block, current): `When still orchestrating in-session (e.g. `--intensity` downgraded, or a runtime without headless dispatch), invoke each stage via the Skill tool as written below …`
  - Replace the `e.g.`-led open list with a **closed two-condition fallback**: `The in-session Skill path is a fallback used only when [a] intensity is direct/quick (micro-stages, no dispatch) or [b] the runtime has no headless dispatch (codex/opencode preflight reports unavailable). In all other standard+ cases, dispatch is mandatory, not optional.`
- **Rewrite each `standard+` stage step (1,3,4,5 + retry loop 6/7) body** from `invoke Skill: code-<stage>` to dispatch-first. Template for Step 1 (apply homologously to 3/4/5 and the retry re-execute/re-test):
  - **Step 1 (code-plan)** new body:
    > For `standard+`, dispatch code-plan as its own depth-2 session (do not invoke it in-session). First ensure the SD-13 spec precondition (artifact root + `spec/` present, or `/track`). Then:
    > ```
    > REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
    > python3 <agent-home>/adapters/claude/bin/dispatch-headless.py --start \
    >   --worktree "$PWD" --slug <cycle-slug> \
    >   --capability code-plan --mode dev --qa <qa> --intensity <intensity> \
    >   --depth 2 --parent <cycle-slug> --worker-role code-plan --owner autopilot-code \
    >   --model-role "deep maker" --profile code-plan \
    >   --prompt-text "<sub-skill contract + input artifact abs paths + output contract + slug>"
    > ```
    > Then poll+harvest in the same turn (one-shot wait contract, SD-14):
    > ```
    > sh <agent-home>/utilities/dispatch-wait.sh --parent <cycle-slug>   # exit 0=done, 2=re-call, 3=diagnose
    > ```
    > Loop the dispatch-wait call until exit 0, then read only the plan frontmatter `status` + plan paths (verdict/status, not the plan body) to drive Step 2. On exit 3, diagnose via dispatch-liveness + transcript tail → re-dispatch that stage (reuse existing artifacts, SD-6). **The dispatch prompt carries input artifact paths only — never the plan body or prior-stage conversation.**
  - **Step 3 (code-execute)**: same shape, `--worker-role code-execute --model-role "fast implementer" --profile code-execute`; input = `plan/plan.md` path; conductor reads plan frontmatter `status` after harvest (existing Status Check between Step 3/4 stays — it now reads the file, not an in-session return).
  - **Step 4 (code-test)**: `--worker-role code-test --model-role "fast reviewer" --profile code-test`; input = `plan.md` verification + `checklist.md`; conductor reads `test_logs/test_report.md` Level verdict.
  - **Step 5 (code-report)**: `--worker-role code-report --model-role "fast writer" --profile code-report`.
  - **Retry loop (6/7)**: the memo-injection + checklist reset + re-dispatch of code-refine/code-execute/code-test all stay, but re-execute/re-test become **re-dispatch** commands (same template) rather than `invoke Skill`. The conductor's rollback (`git checkout <safety-commit>`) stays conductor-side (it reads the Safety commit from `checklist.md` — a file read, fine for the thin conductor).
- **Keep the fallback body**: under each stage step, keep a short "[direct/quick] or [headless-unavailable runtime] fallback: invoke Skill: code-<stage>" line so the two-condition fallback is concrete.
- **plan-check (Step 2) stays inline** (micro-stage, one-line verdict) per SD-6 micro-stage boundary — annotate it explicitly as an inline micro-stage, not a dispatched stage.
- **Verify**: `grep -n "e.g." skills/autopilot-code/references/dev-pipeline.md` no longer matches the escape-hatch line; `grep -c "dispatch-headless.py" dev-pipeline.md` ≥ 4 (one per durable stage); each stage step contains `dispatch-wait`.

### Step F2 — `SKILL.md` Stage Graph table: dispatch-mode annotation
- **File**: `skills/autopilot-code/SKILL.md`, Stage Graph table (lines 45–51).
- **Edit direction**: add to the `standard`/`strong`/`thorough` rows (the `standard+` band) an at-a-glance dispatch marker in the Graph or a new inline note — e.g. append to the `standard` Graph cell: `(각 스테이지 = depth-2 headless 분사, file-only handoff)`. Simplest: add one sentence under the table: `**`standard+` dispatch**: 각 durable 스테이지(code-plan/execute/test/report)는 depth-2 headless 세션으로 분사된다 (dev-pipeline Step 1~7; direct/quick·plan-check 마이크로-스테이지는 inline).`
- **Verify**: `grep -n "depth-2 headless" skills/autopilot-code/SKILL.md` returns the annotation.

---

## Phase G — Adapter bootstrap parity increment (SD-14 one-shot + diffusion note)

> Surfaces §9-10/11. The conductor→stage depth-2 language is already present (Phase 1). Phase 2 adds only the **SD-14 one-shot wait** clause and a pointer that diffusion applies to all `standard+` pipes.

### Step G1 — `adapters/claude/CLAUDE.md §0(C)`
- Already states "conductor(depth-1)는 … 각 스테이지를 depth-2 headless 세션으로 분사". Append one clause to the stealth-death sentence: `conductor 는 one-shot 프로세스이므로 스테이지 분사 후 알림 대기로 turn 을 끝내지 말고 dispatch-wait 로 같은 turn 폴링·수확한다 (SD-14).` **core-first note**: this adapter bootstrap is generated/derived — confirm the equivalent lives in `core/OPERATIONS.md §5.10` (Step B1) first; the CLAUDE.md clause is a pointer, not the SoT.
- **Verify**: `grep -n "one-shot" adapters/claude/CLAUDE.md`.

### Step G2 — `adapters/codex/AGENTS.md` (line 69) + `adapters/opencode/AGENTS.md` (line 60)
- Both already carry "Depth-2 has two regular uses … pipeline stage-workers … conductor dispatches each sub-skill stage". Append one sentence: `The depth-1 conductor is a one-shot process — after dispatching a stage it must not end the turn on a notification wait; it polls the registered stage with `preflight.sh liveness` in the same turn and harvests, re-dispatching on SUSPECT/DEAD (SD-14 parity).`
- Keep 3-adapter parity: identical clause wording (adjusted for each adapter's `preflight.sh` path).
- **Verify**: `grep -n "one-shot process" adapters/codex/AGENTS.md adapters/opencode/AGENTS.md`.

---

## Phase H — Diffusion: stage-dispatch contract into draft/research/spec/design/lab pipes

> WORKFLOW §5 rows (Phase B2) are the routing half; this phase adds the operational half — a **§6-homolog stage-worker table** + a short stage-dispatch contract block in each pipe's reference doc, mirroring what `dev-pipeline.md` line 4 does for autopilot-code. Each table maps: stage → in-session team (unchanged, runs inside the stage session) → input artifacts → output artifacts → write class.

> **Scope discipline**: diffusion = adding the **dispatch contract + stage-worker class table** to each pipe's existing pipeline doc. Do **not** rewrite each pipe's step bodies to imperative dispatch commands (that is a large per-pipe effort like SD-10; Phase 2 scope for diffusion is the *contract + mapping*, with a note that per-pipe body rewrite is follow-up). This keeps Phase 2 bounded and matches the spec's "확산 = 스테이지 분사 계약 적용 + §6 동형 표" (§12-1) rather than a full 5-pipe SD-10.

### Step H1 — autopilot-draft
- **File**: `skills/autopilot-draft/references/pipeline-steps.md`. Add a top contract block + table. Durable `standard+` stage-workers (from research): draft-strategy (Skill), Step 4.1 Draft Generation (연구팀), Step 5.5 polish (편집팀). Materials/analysis steps that write durable artifacts (Step 1 material analysis, Step 4.0 figure extraction via 자료팀) are candidate stages; pure orchestrator/regex steps (Step 4b detector) stay inline (micro-stage). Map input/output per the research table (draft.md, strategy.md, figure_index.md).

### Step H2 — autopilot-research
- **Files**: `skills/autopilot-research/references/pipeline-search-analysis.md` + `report-generation.md`. Stage-workers: Step 2 search (연구팀), Step 3b skimming (연구팀 batch), Step 3e compile (연구팀), Step 4a report (연구팀), Step 4b QA (연구팀/codex-review-team). Materials (자료팀 browser-fetch/web-image) are sub-delegations inside stages. Note the depth-gated steps (2e/3c) as conditional stages.

### Step H3 — autopilot-spec
- **Files**: `skills/autopilot-spec/references/prd-authoring.md` + `scaffolding.md`. Most spec steps are orchestrator-direct (PRD authoring) — these are **not** natural dispatch stages (they write `spec/prd.md` directly and are the conductor's own judgment surface). The clear stage-worker is **Phase 2 scaffold (개발팀 new-lib)** — a separable, artifact-producing stage. Map scaffold as the primary dispatchable stage; annotate PRD authoring as conductor-inline. This asymmetry is worth stating explicitly (not every pipe has 4 symmetric stages).

### Step H4 — autopilot-design
- **File**: `skills/autopilot-design/SKILL.md` (no `references/` dir — pipeline is in SKILL.md body). Stages already map cleanly to sub-skills (design-init/refs/tokens/components/review/handoff), each already delegating to 디자인팀 modes. Add the stage-dispatch contract: `standard+` design phases dispatch as depth-2 sessions; note that design phases have `[CONFIRM Gate]`s — the conductor holds the gate verdict between dispatched phases (file: `design_state.yaml` phase status).

### Step H5 — autopilot-lab
- **Files**: `skills/autopilot-lab/references/setup-procedure.md` + `eval-procedure.md`. Stage-workers: setup S1 spec (연구팀 plan-review), S2 scaffold (개발팀 new-lib), eval E2 (테스트팀), E3-2 plot (자료팀), E3-3 compare (연구팀). **Important lab nuance**: the actual experiment *run* is often long/async and human-gated (RUNLOG ⏳) — these are **not** dispatched stages (they wait on real training); only the scaffold/eval/report stages dispatch. State this explicitly. (This is also why `lab-runner.yaml` profile already exists — the run segment has its own profile; the stage-dispatch contract composes with it.)

### Step H6 — §6-homolog table consistency
- Each pipe's added table must use the same columns as OPERATIONS §5.10 ④ / spec §6: `stage | in-session team | input artifacts | output artifacts | write class`. Cross-check that no pipe claims two stages mutate the same shared file without a lock (mirror the code-report `pipeline_summary.md` lock exception). **Verify**: each of the 5 pipe docs now contains a "stage-worker" table and a "file-only handoff" clause; `grep -rl "stage-worker\|스테이지-워커" skills/autopilot-{draft,research,spec,design,lab}` lists all five.

---

## Phase I — Drill regression case **definition** (handoff artifact; NOT written into loops/**)

> **Hard constraint**: `loops/**` is other-session-owned and must not be edited. Deliver the case as a **handoff artifact under this plan directory**, with the exact 4-file contents ready for the loops-owning session to drop into `loops/drill/cases_growing/`.

### Step I1 — Author the case definition artifact
- **Dir (new, under plan)**: `.agent_reports/plans/2026-07-10_stage-dispatch-phase2/drill_case_stage_dispatch/` containing:
  - `README.md` — install instructions: "copy into `loops/drill/cases_growing/g_stage_dispatch/`; growing tier (2 consecutive PASS → promote to `cases/`); AXIS=git (jobs.log inspection); expensive (spawns headless stages) — matches g6 discipline."
  - `prompt.md` — a single-line user utterance that triggers a `standard+` multi-file dev task in a fixture repo **that already has `spec/`** (so SD-13 precondition holds), given only the skill docs (no dispatch spoon-feeding in the prompt) — this is the §8.5.5 doc-efficacy test.
  - `config` — `MAX_TURNS=120 TIMEOUT=2400 AXIS=git` (larger than g6 — full stage pipeline).
  - `fixture.sh` — build a throwaway repo with `.agent_reports/spec/prd.md` + `pipeline_state.yaml` + a couple of source files; record `main` sha to `.pre/`.
  - `assert.sh` — hard assertions = **forbidden results only** (per drill discipline): main ref unchanged (no direct main commit); no depth-3 rows in jobs.log (`depth=3` must be absent); stage rows must not show source writes from non-execute workers. Soft `WARN:` (turn-cap tolerant) = presence of `depth=2` stage rows with `parent=<cycle-slug>` + `worker_role=code-plan|code-execute|code-test|code-report`; stage artifacts present (`plan/plan.md`, `checklist.md`, `test_logs/`); `pipeline_summary.md` lock not contended. **Doc-efficacy WARN**: at least one `dispatch-headless.py ... --depth 2 --worker-role code-*` invocation trace in `.dispatch/` — i.e. dispatch happened from the docs alone.
- Model `fixture.sh`/`assert.sh` on `g6_worktree_dispatch` (jobs.log grep pattern already established there). Reuse its `.pre/main_sha` idiom.

### Step I2 — Handoff note
- In `final_report.md`, add a "drill handoff" line: the case is authored under the plan dir; the loops-owning session installs it. Do **not** touch `loops/`. (Optionally `post-it` a handoff memo for that session — Phase J.)

---

## Phase J — Instrumentation + SD-OPEN observations (measurement only; no threshold decisions)

### Step J1 — Instrumentation log format (SD-OPEN-1 accumulation + SD-12 token/time)
- Define (in `final_report.md` and a small `plans/<slug>/instrumentation.md`) the columns to record per stage-dispatch run: stage, `profile=` (full-bootstrap vs `code-<stage>` minimal), model_role, wall-clock (start→done via jobs.log ts), conductor context size proxy. **Do not set the micro-stage inline threshold** — accumulate only (SD-OPEN-1, §12-5). Add the Phase-1 pilot sample (plan 218s/execute 255s/test 46s/report 28s) as the first row for continuity.

### Step J2 — SD-OPEN-2 curator observation
- Record whether each stage session fires the SessionEnd mem curator (distiller). The distiller is gated by `MEM_DISTILL_ENABLE=1` (settings env). Instrumentation = note in `instrumentation.md` "curator fired: yes/no" per stage session, and whether any duplicate `mem add` resulted. **Observation only** — no intervention this phase (§8.5.6, §13 SD-OPEN-2). Cross-check: the reminder/Stop hooks already guard `MEM_DISTILL=1` recursion, so hook firing during a distiller sub-session is suppressed.

### Step J3 — Cross-doc sync + post-it handoff
- After edits, sync the correspondence artifacts (part of the change, no separate confirm): `pipeline_summary.md` Decision Points; and a `post-it` handoff memo noting (a) the drill case awaiting install in `loops/`, (b) the SD-14b Stop-gate branch outcome (registered / held), (c) the SD-11 deny-escalation still deferred. Update the spec only if an implementation choice drifted from the blueprint (spec-significance) — otherwise leave prd.md untouched (this plan implements, does not re-spec).

---

## Verification summary (code-test consumes this)

Level-graded (CONVENTIONS test taxonomy):
- **Syntax/lint**: `python3 -c "import ast,sys; ast.parse(open('adapters/claude/bin/dispatch-headless.py').read())"`; `sh -n` on every new/edited `.sh` (`dispatch-wait.sh`, `stage-dispatch-reminder.sh`, `conductor-stop-gate.sh`); `python3 -m json.tool adapters/claude/settings.json`.
- **Import/smoke**: `python3 adapters/claude/bin/dispatch-headless.py --dry-run …` (C1 registry parity; C3 prompt one-shot clause via --register temp); `python3 tools/profile/build-home.py code-<stage> --check` × 4 (D3).
- **Conformance**: `sh hooks/portable-guards.test.sh` (E1/E2 output-shape cases added); `sh utilities/dispatch-wait.test.sh` (C4); `sh utilities/dispatch-liveness.test.sh` (unchanged, regression). If a repo-wide conformance runner exists (`hooks/portable-guards.test.sh` + `tools/check-adaptation-boundary.sh`), run it.
- **Functional**: dispatch-wait exit-code matrix (0/2/3) against a temp jobs.log; SD-11 reminder emits additionalContext for conductor+standard+code-plan and no-ops for direct/quick / depth-2 / non-code / main.
- **Doc-efficacy (deferred to drill, Phase I)**: conductor dispatches stages from `dev-pipeline.md`/`SKILL.md` alone — this is agent-behavior, so it lives in the drill case, not a deterministic test.
- **Grep assertions**: per-step `grep` checks listed above (escape-hatch removed; `dispatch-headless.py` in ≥4 stage steps; `one-shot` in wrapper prompt + OPERATIONS + CLAUDE.md; diffusion clause in 5 pipe docs + WORKFLOW §5 rows incl. new lab row).
- **No-regression guards**: `git grep -n "loops/" plans/<slug>` shows the plan never edits `loops/**`; confirm no writes under `tools/fleet/**`.

## Phase ordering & dependencies (for code-execute)

```
A (probe, gates E2)
└─ B (core docs, core-first)
   └─ C (wrapper+dispatch-wait)          ┐
   └─ D (profiles)                       ├─ mechanisms; F references them
   └─ E (hooks; E2 gated by A)           ┘
      └─ F (SD-10 dev-pipeline+SKILL, priority 0, references C/D/E)
         └─ G (adapter parity), H (diffusion), I (drill artifact), J (instrumentation)
```
- Safe commit per phase (checklist `Safety commit:` header). Source mutation is confined to Phases C (wrapper), D (profiles — data), E (hooks), and the new `dispatch-wait.sh` — plus doc edits elsewhere. No two phases mutate the same file.
- If Phase A blocks (probe inconclusive), proceed with all phases; only E2 registration is held — the pipeline still completes (SD-14 a+c ship regardless).

## Risks / open items surfaced for the conductor
- **SD-14b schema**: exact Claude `Stop` hook block-JSON shape must be confirmed against live docs (Phase A Step A2) before E2 registration — the plan uses `{"decision":"block","reason":...}` as the likely shape but flags it for verification.
- **Diffusion depth**: Phase H delivers contract + mapping tables, not full per-pipe imperative rewrites (bounded scope per §12-1). Per-pipe SD-10-style body rewrites are noted as follow-up, not Phase 2.
- **loops/** and **tools/fleet/**: untouched by design; drill case is a handoff artifact only.
