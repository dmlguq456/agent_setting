# Autopilot Skill/Agent Design Principles

Based on Meta-Framework for Agent & Skill design, adapted to Claude Code environment.

---

## 0. Core Separation (3-Tier)

| Tier | Role | Our System | Anti-Pattern |
|------|------|------------|--------------|
| **Orchestrator** | Deterministic state machine. Routes, gates, commits. | `autopilot-code` SKILL.md | Orchestrator reasoning about code, reading files, synthesizing |
| **Skill** | Expert capability module. Defines WHAT to do and HOW to verify. | `init-plan`, `execute-plan`, `run-test`, etc. | Skill containing orchestration logic (QA loops, retry budgets) |
| **Agent** | Persona with tools. Executes within a skill's scope. | `기획팀`, `품질관리팀`, `개발팀`, etc. | Agent returning verbose results to orchestrator |

---

## 1. Orchestrator Rules (autopilot-code)

### 1.1 Non-Agentic Orchestrator
The orchestrator is a **state machine**, not a reasoning agent. It:
- Parses arguments → determines mode/flags
- Invokes skills in sequence (plan → refine → execute → test → report)
- Checks verdicts (single tokens: ✅/🔴/🟡)
- Gates decisions based on autonomy level
- Commits and reports

It does NOT:
- Read file contents (plans, reviews, logs, test reports)
- Synthesize or summarize subagent work
- Make judgment calls about code quality
- Echo or re-describe what agents returned

### 1.2 Interface Contract
Communication between orchestrator and agents uses a strict protocol:

```
Orchestrator → Agent:  file paths + 1-line task directive
Agent → Orchestrator:  file path + verdict token (one line)
Agent → Agent:         via shared file system (agent B reads file that agent A wrote)
```

The orchestrator NEVER mediates content between agents. It only passes **file paths**.

### 1.3 State Transitions
```
[plan] --verdict→ [refine?] --verdict→ [execute] --verdict→ [test] --verdict→ [report]
         ✅: next              ✅: next            ✅: next           ✅: next
         🔴: re-plan           🔴: re-refine       🔴: rollback       🔴: hotfix
```

Each transition requires only a verdict token, not file content.

---

## 2. Skill Rules (init-plan, execute-plan, run-test, etc.)

### 2.1 Skill = Expert + Verification Loop
Each skill defines:
- **Task agent**: who does the work (기획팀, 개발팀, 테스트팀)
- **Verification agent**: who checks the work (품질관리팀, codex-review-team)
- **Loop contract**: max rounds, escalation rules, pass/fail criteria

### 2.2 Skill Owns Its QA Logic
QA loops (review rounds, fix cycles) belong IN the skill, not in the orchestrator.
The orchestrator only sees the final verdict.

### 2.3 Skill Independence
Skills should work standalone (invokable directly, not only through autopilot-code).
Each skill handles its own:
- File path resolution
- Log directory management
- QA invocation and loop control

---

## 3. Agent Rules (기획팀, 품질관리팀, etc.)

### 3.1 Output Contract (CRITICAL)
Every agent returns EXACTLY:
```
{output_file_path} — {verdict_token}
```
One line. No summary. No explanation. No code snippets.
Full results are written to the output file.

### 3.2 Agent-to-Agent Communication
Agents communicate through FILES, not through the orchestrator:
- Agent A writes `review.md`
- Orchestrator passes `review.md` path to Agent B
- Agent B reads `review.md` directly

### 3.3 Scope of "No Read" Rule
The "no file reading" rule applies ONLY to the **orchestrator** (autopilot-code).
Skills (init-plan, execute-plan, etc.) and their internal agents freely read files.
The orchestrator delegates; skills and agents execute.

### 3.3 Agent Scope
Each agent has a clear boundary:
- 기획팀: reads code, writes plans. Does NOT execute code.
- 개발팀: reads plans, edits code. Does NOT review.
- 품질관리팀: reads code + logs, writes reviews. Does NOT edit code.
- 테스트팀: reads code, runs tests. Does NOT edit code.

---

## 4. Performance Preservation Rules

### 4.1 Efficiency ≠ Cutting Corners
Reducing context waste does NOT mean:
- Fewer QA rounds (quality stays the same)
- Simpler agent prompts (agents still get full context)
- Skipping verification steps

It DOES mean:
- Orchestrator doesn't duplicate agent work
- Results flow through files, not through context
- Verdicts are tokens, not paragraphs

### 4.2 QA Depth Is Non-Negotiable
The adversarial QA pipeline (multiple reviewers × multiple rounds) stays intact.
What changes is HOW results flow — not WHETHER verification happens.
