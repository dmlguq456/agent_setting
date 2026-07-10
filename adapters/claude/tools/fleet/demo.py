"""Synthetic fixture for rendering checks (`fleet.py --demo` or FLEET_DEMO=1).

Covers all three harnesses, every liveness state, tracked/untracked gate, git branch, nested
dispatch under a parent, depth-2 subdispatch, an orphan, a loop, varied models/effort — so the render layer can be
exercised without waiting for real live processes. Merged INTO live data by fleet.py's --demo
path. gate/branch are set explicitly here (fake cwds are not real repos).
"""
import time

from .model import Session, DispatchJob


def collect(harness_filter=None):
    S, J = Session, DispatchJob
    sessions = [
        # --- project 'demo-app' (tracked) ---
        S(harness="claude", pid=90001, cwd="/home/demo/demo-app", session_id="demo-claude-1",
          slug="demo-app-a7", model="Opus 4.8 (1M context)", effort="xhigh",
          ctx_pct=45, rl_5h=33, rl_7d=12, rl_ms=[["fable", 57]], cost=12.30, elapsed_min=95,
          status="busy", gate="tracked", branch="main", liveness="working"),
        S(harness="codex", pid=90002, cwd="/home/demo/demo-app", session_id="demo-codex-1",
          slug="demo-app", model="gpt-5.5", effort="high",
          ctx_pct=72, rl_5h=94, rl_7d=53, elapsed_min=41,
          gate="tracked", branch="feat/streaming", liveness="idle"),
        # --- project 'demo-lib' (untracked session in a tracked repo) ---
        S(harness="opencode", pid=90003, cwd="/home/demo/demo-lib", session_id="demo-oc-1",
          slug="witty-orchid", model="deepseek-v4-pro", effort="high",
          ctx_pct=8, cost=0.05, elapsed_min=16,
          gate="untracked", branch="wip/experiment", liveness="idle"),
        S(harness="claude", pid=90004, cwd="/home/demo/demo-lib", session_id="demo-claude-2",
          slug="demo-lib-f0", model="Sonnet 5", effort="medium",
          ctx_pct=88, rl_5h=20, rl_7d=40, cost=3.10, elapsed_min=3000,
          gate="tracked", branch="fix/bug-4821", liveness="stale"),
        # --- project 'demo-svc' (opencode, low effort, untracked) ---
        S(harness="opencode", pid=90005, cwd="/home/demo/demo-svc", session_id="demo-oc-2",
          slug="brave-comet", model="glm-5.2", effort="low",
          ctx_pct=31, cost=0.42, elapsed_min=200,
          gate="untracked", branch="main", liveness="working"),
        # detached tmux session (no client attached) — idle but backgrounded, shown with ◌ not ○
        S(harness="claude", pid=90006, cwd="/home/demo/demo-app", session_id="demo-claude-3",
          slug="demo-app-detach", model="Opus 4.8", effort="high", detached=True,
          ctx_pct=62, rl_5h=40, rl_7d=22, cost=8.40, elapsed_min=720,
          gate="tracked", branch="fix/night-run", liveness="idle"),
        # --- project 'demo-cool' (cooling) — no active work, last transcript write ~92min ago; the
        # idle session lingers (within the 48h live window) so the group isn't folded, and the
        # directory header shows a grey ○ ring + time-since-done ("완료 직후 식는 중").
        S(harness="claude", pid=90007, cwd="/home/demo/demo-cool", session_id="demo-claude-cool",
          slug="demo-cool-shipped", model="Opus 4.8", effort="high",
          ctx_pct=18, rl_5h=25, rl_7d=15, cost=4.20, elapsed_min=160,
          gate="tracked", branch="feat/shipped", liveness="idle",
          mtime=time.time() - 92 * 60),
    ]
    jobs = [
        # nested under the demo-app claude parent (demo-claude-1)
        J(key="code", stage="exec", mode="dev", qa="adversarial", qa_source="argv", harness="claude",
          model="Opus 4.8 (1M context)", elapsed_min=22, slug="demo-feat-x",
          cwd="/home/demo/demo-app-wt/feat-x", parent_sid="demo-claude-1", parent_cwd="/home/demo/demo-app", is_child=True,
          branch="feat-x", liveness="working", depth=1, intensity="adversarial",
          worker_role="capability-owner", capability_owner="autopilot-code"),
        # depth-2 workers owned by the autopilot-code capability worker above
        J(key="plan", stage="done", mode="review", qa="adversarial", qa_source="jobslog", harness="codex",
          model="gpt-5.5", elapsed_min=6, slug="demo-feat-x-plan-alt",
          cwd="/home/demo/demo-app-wt/feat-x-plan-alt", parent_slug="demo-feat-x", is_child=True,
          branch="feat-x-plan-alt", liveness="idle", depth=2, intensity="adversarial",
          worker_role="planner", capability_owner="autopilot-code"),
        J(key="test", stage="test", mode="verify", qa="adversarial", qa_source="jobslog", harness="opencode",
          model="glm-5.2", elapsed_min=4, slug="demo-feat-x-verifier",
          cwd="/home/demo/demo-app-wt/feat-x-verifier", parent_slug="demo-feat-x", is_child=True,
          branch="feat-x-verifier", liveness="working", depth=2, intensity="adversarial",
          worker_role="verifier", capability_owner="autopilot-code"),
        J(key="review", stage="test", mode="debug", qa="quick", qa_source="jobslog", harness="codex",
          model="gpt-5.5", elapsed_min=8, slug="demo-review",
          cwd="/home/demo/demo-app-wt/review", parent_sid="demo-claude-1", parent_cwd="/home/demo/demo-app", is_child=True,
          branch="review", liveness="working", depth=1),
        # drill launched by a Codex parent from a throwaway /tmp fixture, with depth-2
        # cross-harness checks. It should render under the parent, not as a /tmp project.
        J(key="drill", stage="run", mode="loop/drill", qa="quick", qa_source="jobslog", harness="codex",
          model="gpt-5.5", elapsed_min=3, slug="drill-g6-worktree",
          cwd="/tmp/drill-g6_worktree_dispatch-abcd/repo", parent_sid="demo-codex-1",
          parent_cwd="/home/demo/demo-app", is_child=True, branch="main", liveness="working",
          depth=1, intensity="quick", worker_role="g6_worktree_dispatch", capability_owner="drill"),
        J(key="drill", stage="review", mode="loop/drill-verify", qa="quick", qa_source="jobslog", harness="claude",
          model="Sonnet 5", elapsed_min=2, slug="drill-g6-claude-verify",
          cwd="/tmp/drill-g6_worktree_dispatch-verify/repo", parent_slug="drill-g6-worktree",
          parent_cwd="/home/demo/demo-app", is_child=True, liveness="idle", depth=2,
          intensity="quick", worker_role="verifier", capability_owner="drill"),
        J(key="drill", stage="review", mode="loop/drill-verify", qa="quick", qa_source="jobslog", harness="opencode",
          model="glm-5.2", elapsed_min=1, slug="drill-g6-opencode-verify",
          cwd="/tmp/drill-g6_worktree_dispatch-verify2/repo", parent_slug="drill-g6-worktree",
          parent_cwd="/home/demo/demo-app", is_child=True, liveness="working", depth=2,
          intensity="quick", worker_role="verifier", capability_owner="drill"),
        # nested under demo-svc opencode parent
        J(key="spec", stage="design", mode="dev", qa="thorough", qa_source="plan", harness="opencode",
          model="glm-5.2", elapsed_min=5, slug="demo-spec",
          cwd="/home/demo/demo-svc-wt/spec", parent_sid="demo-oc-2", parent_cwd="/home/demo/demo-svc", is_child=True,
          branch="spec", liveness="working"),
        # orphan (parent not on screen) — stale, in demo-lib
        J(key="debug", stage="running", mode="debug", qa="thorough", qa_source="jobslog",
          harness="codex", elapsed_min=290 * 60, slug="demo-orphan",
          cwd="/home/demo/demo-lib-wt/orphan", parent_sid="demo-dead", parent_cwd="/home/demo/demo-lib", is_child=True,
          branch="orphan", liveness="stale"),
        # loop
        J(key="oncall", elapsed_min=12, slug="oncall", cwd="", parent_sid=None, liveness="working"),
    ]
    if harness_filter:
        sessions = [s for s in sessions if s.harness in harness_filter]
    return sessions, jobs
