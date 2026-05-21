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

---

## 5. Operational Principles History

> 본 절은 `~/.claude/` 설정의 핵심 운영 원칙들을 commit 흐름 시간순이 아닌 _주제별_로 묶어 정리한 reference. §0~§4 가 _아키텍처 헌법_ (orchestrator / skill / agent 3-tier separation, interface contract, performance preservation) 인 반면, 본 §5 는 _운영 시점에 적용되는 행동 원칙_ — 새 skill·agent 만들 때, 기존 skill 손볼 때, 사용자가 "왜 이렇게 동작하지" 의문이 들 때 검색해서 본다. 시간순 changelog 는 `git log` 로 충분.
>
> 자매 문서:
> - `~/.claude/CONVENTIONS.md` — QA 5 단계·model 표기·폐기 flag·hard invariant·산출물 폴더 컨벤션 (§7)
> - `~/.claude/CLAUDE.md` §1~§5 — 메인 Claude 자체 행동 메타 원칙 (응답 원칙)
> - `~/.claude/notion_guide.md` — Notion MCP 작업 가이드
>
> 본 절은 위 세 문서에 박힌 결정들이 _어떤 incident_ 에서 도입됐는지 묶음별로 보여준다.

### 5.1. Autopilot 정신 — default 는 자동 진행

> family 멤버는 모두 confirm 없이 pipeline 을 끝까지 돌린다. 사용자가 명시할 때만 멈춘다.

- **도입 incident**: `autopilot-refine` 만 default 가 chat-pause + confirm 이라 family 안에서 이름과 동작이 mismatch 였다. commit `782ccf6` (default = 자동 apply) 에서 다른 멤버와 정합 맞춤. 이후 commit `2058325` 에서 사용자가 "스킬 전반에 user-refine 은 요청하지 않으면 안 하는 걸 기본값으로 해. 요즘 계속 멈추더라" 지적 → CLAUDE.md 응답 원칙 §4 신설 (메인 Claude 의 임의 pause flag 추가 금지).
- **적용 범위**: `autopilot-code` / `autopilot-doc` / `autopilot-research` / `autopilot-refine` 전부. 사용자가 직접 typed `--user-refine` / `--confirm` 한 경우에만 멈춘다.
- **Why**: 사용자가 명시 요청을 했는데 메인 Claude 가 "신중을 위해" 라며 추가 confirm 단계를 만들면 작업이 한 turn 만큼 지연되고, "이미 했어?" 같은 follow-up 으로 갈등 비용이 누적된다. high-stakes 일수록 사용자가 _직접_ pause 를 거는 게 자연스럽다.
- **현재 어떻게 강제되나**: 각 skill SKILL.md 의 `--user-refine` / `--confirm` 절에 "Default: false. 메인 Claude MUST NOT add this flag on its own" 명시. CLAUDE.md 응답 원칙 §4 가 메인 Claude 의 args 구성 단계에서 임의 추가 차단. `autopilot-refine` Mode Forms 표 첫 행이 default = 자동 apply 명시 + safety net (snapshot · pipeline_summary history · git diff · Stage B.5 marker) 명시.
- **관련 commit/문서**: `782ccf6` (refine default 자동 apply), `2058325` (`--user-refine` opt-in only 강조), CLAUDE.md §4, `autopilot-refine/SKILL.md` Mode Forms 절.

### 5.2. Implicit input discovery — 외부 flag 폐기, `.claude_reports/*` 자동 발견

> 입력 자료는 사전 분석된 영속 산출물에서 자동 발견한다. 외부 폴더를 가리키는 flag 는 family 전체에서 제거됐다.

- **도입 incident**: `--refs <folder>` / `--format-ref <path>` 같은 flag 가 매번 path 를 외워야 하고, 같은 자료를 여러 skill 이 다시 읽어 비용도 컸다. commit `444616a` (analyze-project positional optional — cwd 자동 발견), `d8f42cd` (autopilot-doc `--format-ref` 제거), `215fc23` (stale `--format-ref` / `{refs_folder}` legacy 일괄 cleanup) 으로 단계적 정착.
- **적용 범위**: `analyze-project` / `autopilot-doc` / `autopilot-research` / `autopilot-refine` / `init-doc-strategy`. `--refs` 는 2026-05-08 폐기, `--format-ref` 는 2026-05-12 폐기 (CONVENTIONS.md §3 Removed Flags).
- **Why**: 사용자가 자료를 _프로젝트 dir 안에 두고_ `cd` 후 호출하는 워크플로우가 90%+ 케이스를 차지한다. 외부 폴더 지정은 rare case 인데 그것을 위해 모든 호출에 flag 를 강제하는 건 인지 비용 과부하. 더 큰 가치 — `analyze-project` 산출물이 _영속 자산_ 이 되어 후속 autopilot-* skill 이 implicit 으로 활용하면 분석 비용이 중복되지 않는다.
- **현재 어떻게 강제되나**: `analyze-project/SKILL.md` Workspace assumption 절 + 모든 mode 의 positional optional 명시. `autopilot-doc/SKILL.md` Input Discovery 절이 `analysis_project/{paper,doc}` / `research/{topic}` fuzzy match. CONVENTIONS.md §3 Removed Flags 표 + §5 hard invariant 5 (사용 예시로 잔존 시 drift). sync-skills 가 cross-doc grep 으로 자동 검사.
- **관련 commit/문서**: `444616a`, `d8f42cd`, `215fc23`, CONVENTIONS.md §3, CLAUDE.md "Workspace assumption" 절.

### 5.3. 3-tier 산출물 컨벤션 (T1/T2/T3) — `_internal/` 로 audit 흔적 격리

> artifact 폴더 root 에는 사용자가 보는 entry/main 산출물만 둔다. review log / 스냅샷 / raw scan 은 `_internal/` 아래로 격리.

- **도입 incident**: 초기에는 review log, version 스냅샷, raw search 결과가 artifact root 에 같이 있어 "어떤 파일이 중요한지" 한눈에 안 들어왔다. commit `50e595e` 가 `SKILL_OUTPUT_CONVENTION.md` single source 신설 + 모든 skill SKILL.md path 를 일괄 마이그레이션. 2026-05-21 본 컨벤션이 단독 파일에서 CONVENTIONS.md §7 으로 흡수됨 (자매 단일 source 통합).
- **적용 범위**: `autopilot-research` / `autopilot-doc` / `autopilot-code` / `autopilot-refine` / `analyze-project` / `refine-doc` / `init-plan` / `run-test` 등 산출물을 만드는 모든 skill. CLAUDE.md "산출물 위치" 표가 단일 출처.
- **Why**: artifact root 정돈이 사용자 신뢰의 첫 화면. _내가 한 작업 결과_ 와 _도구가 audit 용으로 만든 부산물_ 을 구분 못 하면 산출물 navigation 비용이 폭증한다. T3 격리 후 root 만 보면 결정·draft 가 보이고, 의심이 들 때만 `_internal/` 안을 본다.
- **현재 어떻게 강제되나**: 각 skill SKILL.md 상단 callout "산출물 폴더 컨벤션: CONVENTIONS.md §7 (3-tier T1/T2/T3)" 1 줄로 명시. `audit` skill 의 documents aspect "structure" 가 T1/T2/T3 layout 위반을 lint. autopilot-refine snapshot 은 modern (`_internal/versions/v{N}/`) vs legacy (`_v{N}.md` 형제) auto-detect.
- **관련 commit/문서**: `50e595e`, CONVENTIONS.md §7 본문, `audit/SKILL.md` documents aspect "structure".

### 5.4. Natural-integration rule — 본문 mutation 은 sentence 통합, paste 가 아닌

> reviewer 의견 → 본문 수정으로 옮길 때, paste-ready 표·enumeration 을 통째로 박지 말고 1~2 문장 in-line rewrite 로 자연스럽게 녹인다. 안 되면 drop 또는 Appendix.

- **도입 incident**: 2026-05-19 ICML camera-ready 사이클에서 reviewer 의견을 자동으로 paper-body mutation 으로 변환했는데, model-by-model comparison 표 (`tab:arch_compare`) 가 본문에 통째로 박혀 사용자가 거부 ("rebuttal 자료를 본문에 그대로 가져다 붙이지 말고 자연스럽게 문장으로 녹여 넣어라"). commit `bf8d565` 에서 5-rule 패턴 (별도 paragraph block 회피 · Figure cascade · 실험 수치 verbatim 제거 · opening + 본론 통합 · rebuttal 표 drop) 을 SKILL.md 에 박음. 후속 2026-05-20 M8/M9 incident 에서 4-step Paragraph Cohesion Pre-Check 추가.
- **적용 범위**: `init-doc-strategy` paper mode + `autopilot-doc` paper mode (Step 4.1 mutation 생성). 모든 mode 의 paste-ready block 작성 전 4-step pre-check (substance 중복 · paragraph axis · cross-section redundancy · EDIT/REPLACE/INSERT/DROP 선택).
- **Why**: reviewer 응답 format 과 paper-body flow 는 _다른 장르_ 다. 기계적 변환은 camera-ready 가독성을 깨고, 사용자에게는 "이걸 그대로 붙이라고?" 라는 즉각 거부 반응을 일으킨다. 4-step pre-check 가 mechanical INSERT 를 사전 차단.
- **현재 어떻게 강제되나**: `init-doc-strategy/SKILL.md` "Paragraph Cohesion Pre-Check" 절 + paper mode "Natural-integration rule" 본문. `autopilot-doc/SKILL.md` Step 4.1 paper 절의 Hard-fail rejection signals (a/b/c) — 셋 중 하나라도 보이면 mutation 작성 거부. 메모리 `feedback_paper_body_rewrite_pattern.md` + `feedback_paragraph_cohesion_pre_check.md` 자동 로드.
- **관련 commit/문서**: `bf8d565`, memory `feedback_paper_body_rewrite_pattern.md`, memory `feedback_paragraph_cohesion_pre_check.md`, `init-doc-strategy/SKILL.md` paper mode.

### 5.5. Minor vs Major 분리 + dual-perspective audit

> 일상 변경은 직접 Edit + pipeline_summary 상세 minor log. major-level (구조 재설계·외부 검토 직전 ceremony) 일 때만 autopilot-refine 호출. 누적 minor 는 audit 이 두 관점 (vs last major snapshot + vs universal principles) 으로 batch 점검.

- **도입 incident**: `autopilot-refine` 의 Default Invocation Rule 초기 안 (commit `b61191f`) 은 doc/research 산출물에 대한 모든 자연어 수정 prompt 를 자동 invoke 대상으로 봤는데, 매 minor 마다 QA agent + snapshot + version bump 의 ceremony cost 가 컸다. commit `56708c4` 에서 3-criteria (사용자 명시 · 구조적 ≥200 줄 · 외부 검토 직전 ceremony) 로 _major-level_ 만 자동 invoke 좁히고, audit 에 dual-perspective 추가.
- **적용 범위**: `autopilot-refine` (major 전용 자동 routing), `audit` (doc/research 의 dual-perspective P1/P2), 메인 Claude (minor 직접 Edit + `pipeline_summary.md` minor log).
- **Why**: 대부분 변경은 단일 entry mutation · caption · cross-ref 조정 같은 minor. 매번 refine ceremony 묶는 건 cost 대비 가치 낮음. 그러나 _추적성_ 유지 → minor log 에 Trigger / Files / Audit-flag / Reversibility 모두 박혀, audit 이 누적 minor 를 last major snapshot 과 cross-correlate 해서 "최근 도입된 issue (fix 우선순위 高)" vs "기존 잔존 issue" 분류 가능.
- **현재 어떻게 강제되나**: `autopilot-refine/SKILL.md` "Default Invocation Rule" 절 (3-criteria 표 + Override 1순위 표). CLAUDE.md 도메인 트리거 표 row 2 (major 만 자동 invoke). `audit/SKILL.md` "Dual-perspective audit" 절 + Stage B.5 minor log baseline ingestion. AUDIT_HINT_THRESHOLD = 5 minors 도달 시 chat alert.
- **관련 commit/문서**: `b61191f`, `56708c4`, `autopilot-refine/SKILL.md` Default Invocation Rule 절, `audit/SKILL.md` Dual-perspective 절.

### 5.6. QA 5단계 single-source-of-truth → CONVENTIONS.md

> QA level (quick / light / standard / thorough / adversarial) 정의는 한 곳에만 박힌다. 다른 skill SKILL.md 는 본 정의를 참조만 한다.

- **도입 incident**: 분산 정의 시기에 "adversarial = standard + Codex" 오정의가 한동안 잔존 (실제는 `thorough + Codex`). commit `1d37674` 가 QA_LEVELS.md 신설로 single source 만들고, `6ed1d2e` 가 sync-skills 안으로 이동, 최종 `f3ceda0` 에서 CONVENTIONS.md (CLAUDE.md "Source of Truth" 등재) 로 옮겨 자동 로드.
- **적용 범위**: 모든 `--qa` flag 를 받는 skill (autopilot-code / autopilot-doc / autopilot-research / autopilot-refine / init-plan / refine-plan / execute-plan / run-test / init-doc-strategy / refine-doc) 및 audit 의 `--no-fact-check` / `--no-style-audit` opt-out.
- **Why**: 같은 level 이 skill 마다 다른 의미면 사용자 신뢰가 깨진다. canonical wording 한 곳 + sync-skills 가 cross-doc grep 으로 drift 점검 + `--auto-fix` 로 propagation 까지 — drift 가 발생해도 자동 복구.
- **현재 어떻게 강제되나**: CONVENTIONS.md §1 QA Levels (5단계 + Skill 별 사용 매트릭스 + opt-out flag 정책). §5 Hard Cross-Doc Invariants 1~9 — sync-skills `--check` 가 자동 검사. canonical wording 위반 시 `--auto-fix` 로 propagate.
- **관련 commit/문서**: `1d37674`, `6ed1d2e`, `f3ceda0`, CONVENTIONS.md §1·§5, `a95b1f9` (adversarial 오정의 fix).

### 5.7. 응답 원칙 §1~§5 — 메인 Claude 의 메타 행동 규칙

> _작업 결과물 정책_ 과 별개로, 메인 Claude 응답 자체에 강제되는 다섯 가지 메타 원칙: 판교체 회피 · 출력 자제 · 동사 약속어 self-check · pause flag 비자동 · 질문 후 자율 진행.

- **도입 incident**: §1 (판교체 — 2026-05-21 한국어 가독성 불만), §2 (출력 자제 — `d10b58d` "concise core, details on follow-up"), §3 (동사 약속어 self-check — 2026-05-19 사용자가 "진행할게요" 한 뒤 tool call 없이 turn 종료한 패턴 지적, `bf8d565`), §4 (pause flag 비자동 — 2026-05-21 "스킬 전반 user-refine 안 하는 게 기본", `2058325`), §5 (질문 후 자율 진행). commit `9d258b5` 에서 §2 의 부작용 (행동까지 빠지는 패턴) 을 §3 self-check 로 보강.
- **적용 범위**: 메인 Claude 의 _모든 응답_. skill / agent 산출물의 내용 정책과 layer 가 다르다 (산출물 정책은 SKILL.md / agent.md / 메모리에).
- **Why**: 산출물 품질만 좋고 응답 자체에서 사용자가 짜증나는 패턴 (장황한 판교체 · 동사 약속 후 tool call 없이 종료 · 임의 pause · 같은 질문 반복) 이 누적되면 신뢰가 깨진다. 다섯 원칙은 사용자가 _개별 지적할 때마다_ 메인 Claude 가 자가 점검하도록 만든 self-audit checklist.
- **현재 어떻게 강제되나**: CLAUDE.md 응답 원칙 §1~§5 본문 (각 원칙별 wording + 한국어로 쓸 어휘 / 영어로 둘 어휘 분류 표). 메모리 `feedback_korean_readability_policy.md`, `feedback_verbal_action_mismatch.md` 자동 로드. CLAUDE.md 운영 정책 (e) — 응답 원칙 추가·변경 시 본 파일을 먼저 수정한 뒤 propagate.
- **관련 commit/문서**: `d10b58d`, `bf8d565`, `9d258b5`, `51bcf0b`, `568e152`, `2058325`, `3f5a48c`, memory `feedback_*.md`.

### 5.8. 편집팀 / 판교체 정책 — 한국어 산출물 전담 에이전트

> 한국어 산출물의 표기 일관성은 편집팀 (opus) 에이전트가 책임진다. 영문 → 국문 번역 / 이미 한국어인데 어색한 문서 다듬기 / 점검만 세 모드.

- **도입 incident**: 2026-05-21 사용자가 cheatsheet v3 사이클에서 한국어 가독성 불만 표현 ("paste-ready block 은 dependency 해소 후 verification gate 를 통과한다" 같은 판교체). 근본 원인은 영문으로 내부 작업 후 마지막 sonnet 1:1 번역으로 국문 산출물을 만드는 패턴. commit `3f5a48c` 가 본 에이전트 신설 + 모든 한국어 산출물 단계의 호출 자리를 sonnet 1:1 번역 → 편집팀 모드 A 호출로 swap.
- **적용 범위**: `autopilot-doc` Step 4-KO (draft 국문 mirror), `autopilot-research` Step 4a-KO (research 보고서 국문 mirror), `init-doc-strategy` / `init-plan` 의 Korean Version Generation. 사용자 직접 호출 ("한국어 다듬어줘" / "판교체 정리해줘" 트리거).
- **Why**: 판교체는 사용자가 영어를 못 읽어서가 아니라 _같은 개념을 다른 표기로 쓰는 일관성 부재_ 와 _한국어로 자연스럽게 쓸 수 있는데 영어를 끌어다 쓰는 허세_ 때문에 거슬린다. 1:1 번역은 영어 어순을 그대로 끌어와서 이 패턴을 양산한다. 전담 에이전트가 _한 절 단위로 의미 파악 후 한국어 문장을 처음부터 새로 작성_ 하는 방식으로 끊는다.
- **현재 어떻게 강제되나**: `agents/editorial-team.md` 본문 (영어로 둘 어휘 / 정착 외래어 / 한국어로 쓸 어휘 매핑 표 + 호흡 규칙 + 거부 패턴 5). `autopilot-doc/SKILL.md` Step 4-KO 절 명시. CLAUDE.md 응답 원칙 §1 이 본 정책을 메인 Claude 응답에도 강제.
- **관련 commit/문서**: `3f5a48c`, `agents/editorial-team.md` 본문, memory `feedback_korean_readability_policy.md`, memory `reference_editorial_team_agent.md`.

### 5.9. 사용자 통제 메모리 (notes) vs 자동 메모리 분리

> per-project 메모는 두 layer 분리: 사용자가 `/notes` 명령으로만 갱신하는 `.claude_reports/NOTES.md` (1 파일 5 카테고리) + Claude 가 자동 누적하는 `~/.claude/projects/*/memory/` (feedback_*.md).

- **도입 incident**: commit `60f141a` 가 `/notes` skill 신설. 자동 메모리가 모든 feedback 을 누적하다 보니 사용자가 _명시적으로 박아두고 싶은_ 정보 (코딩 컨벤션 · 외부 자원 link · 미해결 thread · 다음 세션 hint) 가 noise 에 묻혀 보였다.
- **적용 범위**: `/notes` skill 의 5 카테고리 (conventions / external resources / open threads / decisions / next session hints). CLAUDE.md 도메인 트리거 표 row 4 — 세션 시작 시 `cwd/.claude_reports/NOTES.md` 가 있으면 메인 Claude 가 즉시 Read.
- **Why**: _자동 메모리는 Claude 가 결정_, _사용자 메모리는 사용자가 결정_ — 둘이 섞이면 둘 다 신뢰 깎인다. 사용자가 "이건 절대 잊지 마" 라고 박은 정보는 자동 누적과 별개로 독립 layer 에 둬야 우선순위가 명확하다.
- **현재 어떻게 강제되나**: `skills/notes/SKILL.md` 의 5 카테고리 정의 + 갱신은 항상 `/notes` 명령으로 (Claude 자동 X). CLAUDE.md 도메인 트리거 표 row 4 가 자동 로드 동작 명시. 자동 메모리 `~/.claude/projects/*/memory/` 는 별개 layer 유지.
- **관련 commit/문서**: `60f141a`, `skills/notes/SKILL.md`, CLAUDE.md 도메인 트리거 표.

### 5.10. Presentation = figure-centric, text minimal

> PPT slide capacity (16:9) 는 markdown draft 가 시사하는 것보다 작다. figure 가 slide 면적의 절반 이상을 차지하고, 본문 bullet 은 1~2 키워드 수준으로 한 줄에 맞춘다. 긴 정당화는 speaker note 또는 backup slide.

- **도입 incident**: 여러 사이클에서 markdown draft 의 풍부한 bullet 이 PPT 로 옮겨질 때 figure 자리를 침범. commit `1a7ac0e` (PRESENTATION_FIGURE_CONVENTIONS.md 신설) → `3178321` (slim down) → `5028ce5` (audio-specific knowledge drop) → `fbe7d15` (§0 slide-volume limit 명시) 단계적 정착.
- **적용 범위**: `autopilot-doc` presentation mode (Step 4.0a/b/c 의 figure discovery / extraction / path convention 포함). PPT 자체는 PowerPoint 에서 사용자 수동 (pandoc 자동 변환은 신뢰성 낮아 family 에서 제외).
- **Why**: 슬라이드는 _청중이 한눈에 보는 것_, markdown 본문은 _발표자가 읽는 것_ — 두 매체가 다르다. text-heavy bullet 은 발표 동안 청중 인지를 분산시키고, figure 가 작아져서 메시지 전달력이 떨어진다. figure-centric default 가 PPT 의 본질에 맞는다.
- **현재 어떻게 강제되나**: `autopilot-doc/SKILL.md` Step 4.0a-c (multi-source figure discovery + on-demand extraction + path convention). `PRESENTATION_FIGURE_CONVENTIONS.md` §0 slide-volume limit + figure-centric default + 고해상도 정책 (DPI 600-800 caption-aware crop). Step 4.0b-quality 표가 모든 PDF 기반 figure / table 추출에 강제 적용.
- **관련 commit/문서**: `1a7ac0e`, `3178321`, `5028ce5`, `fbe7d15`, `7888284`, `PRESENTATION_FIGURE_CONVENTIONS.md` 본문.

### 5.11. 미반영 후보 (다음 review 후보)

향후 본 §5 에 추가 검토 후보 — 아직 별도 묶음으로 격상 안 됨:

- **Codex / external review 통합** — commit `95e75e7` (adversarial QA + Codex review agent 도입), `29886b1` (autopilot-refine 에 `--qa adversarial` tier 추가). 현 §5.6 (QA 5단계) 에 흡수돼 있지만, _external scrutiny 에 대비하는 메커니즘_ 자체로 별도 묶음 신설 vs §5.6 안 subsection 검토 필요.
- **Audit auto-fix chain** — commit `28b46be` (fact-check / audit 인프라 구축), `5de964c` (`--scope auto` artifact 특성 기반 자동 판단). §5.5 (Minor vs Major + audit) 에 부분 포함이지만, _audit 결과를 사용자가 무시하는 실패 모드를 forcing function 으로 차단_ 한다는 자체 가치 — §5.5 본문에 _Stage E auto-fix chain_ 한 단락 추가 권장.
