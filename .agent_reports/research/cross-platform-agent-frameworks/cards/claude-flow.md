# claude-flow (ruvnet) — 기술 심층 카드

> 정체성 주의: `ruvnet/claude-flow` 저장소는 현재 `ruvnet/ruflo` 로 리브랜드/이전됐고, 문서/README 상의 제품명은 대부분 **Ruflo v3.x** 다. 다만 **npm 패키지명은 여전히 `claude-flow`** (버전 3.25.4~3.6.10 확인) 이고 `ruflo`, `@claude-flow/cli` 와 동일 버전으로 공동 배포된다. 아래는 저장소 `main` (v3 계열) 기준 실측이며, 초기 v2 의 "swarm/hive-mind + SQLite" 설계 위에 v3 monorepo 가 얹힌 구조다.

## 1. Layer structure — core vs runtime/adapter

- 문서상의 계층 스택 (README): `User → Claude Code / CLI → Orchestration Layer (MCP Server, Router, Hooks) → Swarm Coordination → 100+ Specialized Agents → Memory & Learning → LLM Providers`. 즉 **core(오케스트레이션/스웜/메모리) 와 runtime(Claude Code/CLI/Provider) 를 분리**한 다층 모델.
- v3 는 **monorepo of `@claude-flow/*` 패키지**로 core 를 쪼갠다 (CLAUDE.md 실측):
  - `@claude-flow/cli` — CLI entry point (26 commands)
  - `@claude-flow/codex` — "Dual-mode Claude + Codex collaboration" (adapter 계층)
  - `@claude-flow/guidance` — "Governance control plane"
  - `@claude-flow/hooks` — "17 hooks + 12 workers"
  - `@claude-flow/memory` — "AgentDB + HNSW search"
  - `@claude-flow/security` — input validation, CVE remediation
- 해석: **core(오케스트레이션·메모리·hooks·guidance) 와 runtime-adapter(codex, provider routing) 가 별도 패키지로 구획**돼 있다. 우리 하네스의 `core/` vs `adapters/claude|codex` 분리와 개념적으로 대응하는 명시적 adapter 계층(`@claude-flow/codex`)이 존재.

## 2. 단일 vs 멀티 런타임

- **멀티 런타임 지향**이 명시적. README: "native Claude Code / Codex / Hermes and many more". Provider routing 은 "Claude, GPT, Gemini, Cohere, Ollama with smart routing" (LLM 백엔드 레벨) + `@claude-flow/codex` 의 dual-mode(Claude+Codex) 협업 (에이전트 런타임 레벨).
- 다만 1차 통합 표면은 여전히 **Claude Code** (settings.json / hooks / skills / MCP 가 전부 Claude Code 규격). Codex 는 adapter 로 부착되는 형태 — parity 는 미검증(문서가 "dual-mode collaboration" 이라 표현하나 hook/skill projection 동등성 근거는 확인 못 함, **unverified**).

## 3. Packaging / installation & drift 처리

- 세 경로 (실측 명령):
  1. **npm/CLI**: `npm install -g ruflo@latest` 또는 `npx ruflo@latest init` (패키지 `claude-flow`/`ruflo`/`@claude-flow/cli` 동일 버전)
  2. **MCP server**: `claude mcp add ruflo -- npx ruflo@latest mcp start` — `.claude/settings.json` 의 `mcpServers.claude-flow` 가 `npx -y ruflo@latest mcp start` 로 등록 (실측)
  3. **Claude Code plugins/marketplace**: `/plugin install ruflo-core@ruflo` (35개 plugin). plugin 경로는 slash command 위주, full CLI 는 MCP 툴(`swarm_init`, `agent_spawn`, `memory_store`) 노출 — **경량 vs 프로덕션 이중 설치 경로**.
- **Update vs customization drift**: `init` 이 `.claude/` (settings.json, agents, commands, hooks helpers) 와 CLAUDE.md 를 프로젝트에 스캐폴딩한다. 즉 우리 하네스처럼 core 를 참조(reference)하지 않고 **프로젝트로 파일을 복사·생성하는 모델** → update 시 사용자 커스터마이즈와 충돌(drift) 가능. 저장소 자체 settings.json 주석이 이 문제를 자인: "repo has 367 SKILL.md files (5x duplicates of common skills) across .agents/skills, .claude/skills, archive/v2/.claude/skills ... Long-term fix is to prune the duplicates" (#1834). 즉 **다중 복제본 drift 를 프레임워크 스스로 겪는 중**. 대응책은 §6 의 MetaHarness snapshot.

## 4. Workflow gate enforcement — convention vs mechanism

**메커니즘 기반** (우리 하네스의 hook 강제와 유사, 다만 gate 성격은 다름):
- **Claude Code hooks 로 강제** (`.claude/settings.json` 실측). 모든 hook 이 `node .claude/helpers/hook-handler.cjs <phase>` 단일 dispatcher 로 라우팅:
  - `PreToolUse`(matcher `Bash`) → `pre-bash`
  - `PostToolUse`(matcher `Write|Edit|MultiEdit`) → `post-edit`
  - `UserPromptSubmit` → `route` (프롬프트 라우팅/인텔리전스)
  - `SessionStart` → `session-restore`
  - `SessionEnd` / `Stop` / `PreCompact` → `session-end`
- **12 background workers** 가 파일 변경·패턴·세션 이벤트로 auto-dispatch (audit, optimize, testgaps 등). "Intelligence Loop (ADR-050) automates this cycle through hooks."
- **Swarm/Hive-mind 오케스트레이션 gate**: queen-led 계층(strategic/tactical/adaptive queen + 8 worker types) + **consensus 프로토콜**(Raft / Byzantine / Gossip)로 조율 — 순차 실행이 아니라 합의 기반. `--consensus byzantine` 등 CLI 플래그로 지정. GOAP A* planner 로 state 변화 시 replanning.
- 주의: 이 gate 는 우리 하네스의 "산출물 생성 _순서_ 강제(artifact-guard)" 와 성격이 다르다 — claude-flow 의 gate 는 **agent 조율/합의/lifecycle hook** 이지, spec→plan 같은 파이프라인 순서 불변식 강제는 확인되지 않음(**unverified**). guidance 패키지("governance control plane")가 정책 gate 를 담당할 가능성은 있으나 내부 동작 미확인.

## 5. State / artifact management

- **하이브리드 메모리 백엔드 (ADR-009: "Hybrid Memory Backend (SQLite + HNSW)")**:
  - **SQLite persistence with WAL** — Hive Mind "Collective Memory" 의 shared knowledge base, LRU cache, 8 memory types. USERGUIDE 표: "Persistent Memory: SQLite + AgentDB + PostgreSQL". (v2 계보의 `.swarm/memory.db` 가 이 SQLite 층에 해당하는 것으로 보이나 정확한 파일 경로는 이번 실측에서 직접 확인 못 함 — **partially unverified**.)
  - **AgentDB** — HNSW-indexed vector DB (파일 `agentdb.rvf` 저장소 루트에 실재 확인), sub-ms 검색, "measured ~1.9x faster at N=20k". `ruflo-rvf` plugin 이 "save and restore agent memory across sessions" (RVF 포맷).
  - Data normalize → SQLite cache → Vector 파이프라인 (mermaid 다이어그램 실측).
- **Session 지속**: `SessionStart` hook 의 `session-restore` + `SessionEnd`/`Stop`/`PreCompact` 의 `session-end` 로 "Cross-Session Context: Full restoration". `claude -p ... --session-id "task-N" &` 로 병렬 세션 실행.
- **SONA self-learning / ReasoningBank** — 실행 trajectory·outcome 을 vector memory 에 저장해 향후 plan 검색에 재사용 (self-learning 층).

## 6. Core↔per-project drift 방지

- **MetaHarness** 감사 스위트가 명시적 drift 대응: "Audit your AI agent setup before you ship. Grade readiness (1-100), scan tool configs for security issues, **snapshot the whole project to catch regressions over time**". 즉 프로젝트 config 스냅샷 → 회귀/drift 탐지.
- **`ruflo verify`**: cryptographic witness manifest validation (저장소 `verification/` 디렉터리, `.harness/manifest.json`·`mcp-policy.json` 실재).
- **Team Gateway checklist** (`docs/TEAM-GATEWAY-CHECKLIST.md`): dual-mode handoff·memory namespace consistency 강제.
- 한계/자성: §3 서술대로 프레임워크 자신이 **복제본 SKILL.md drift(#1834)** 를 겪고 있어, "core 를 프로젝트로 복사·생성" 하는 배포 모델의 구조적 drift 취약성을 그대로 보여준다. 우리 하네스의 "core 단일 SoT + adapter 파생, 직접 선행수정 금지" 규율과 대비되는 지점.

### 우리 하네스 대비 시사점 (요약)
- 공통: hook 로 lifecycle 강제, SQLite 계열 memory DB, core/adapter(codex) 분리, session persistence.
- 차이: claude-flow 는 (a) **파일 복사식 스캐폴딩** → update/customization drift 를 스냅샷 감사(MetaHarness)로 사후 탐지하는 반면 우리는 core reference + 생성순서 hard-gate; (b) gate 가 **agent 합의/조율** 중심이지 **산출물 파이프라인 순서 불변식**은 아님; (c) 규모가 훨씬 크고(314 MCP tools, 100+ agents) 자체 drift(중복 skill) 를 안고 있음.

## Sources

- ruvnet/claude-flow (=ruflo) 저장소 트리·파일 실측 (gh API, `main`, 2026-07-09):
  - `package.json` — name `claude-flow`, version 3.25.4, bin `./bin/cli.js`
  - `CLAUDE.md` — "Ruflo v3.5/v3.6", `@claude-flow/*` 패키지 표(cli/codex/guidance/hooks/memory/security)
  - `.claude/settings.json` — hooks(PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/SessionEnd/Stop/PreCompact → hook-handler.cjs), mcpServers.claude-flow(`npx -y ruflo@latest mcp start`), skillListingBudgetFraction 주석(#1834 중복 drift 자인)
  - `.claude/mcp.json`, `.harness/{manifest.json,mcp-policy.json}`, `agentdb.rvf`, `verification/` 존재 확인
  - `docs/USERGUIDE.md` — Hive Mind(queen-led, SQLite persistence with WAL), ADR-009(Hybrid Memory SQLite+HNSW), ADR-050(Intelligence Loop), `hive-mind spawn`, `--consensus byzantine`, SQLite+AgentDB+PostgreSQL
  - `docs/TEAM-GATEWAY-CHECKLIST.md`, `docs/metaharness-user-guide.md` (존재)
- https://github.com/ruvnet/ruflo (README — 계층 스택, multi-runtime "Claude Code / Codex / Hermes", MetaHarness, `ruflo verify`)
- https://github.com/ruvnet/claude-flow (redirect → ruflo)
- https://github.com/ruvnet/ruflo/wiki/Workflow-Orchestration (swarm workflow orchestration, stream-json chaining)
- https://github.com/ruvnet/ruflo/issues/945 (Claude Flow V3 rebuild 배경)
- https://dev.to/stevengonsalvez/claude-flow-the-multi-agent-swarm-orchestrator-before-it-got-a-new-name-4kd4 (리브랜드 배경, 2차 출처)

### Unverified / 표시
- Codex adapter 의 hook/skill projection parity — 미확인
- v2 `.swarm/memory.db` 정확한 파일 경로·스키마 — 이번 실측 미확인 (SQLite 층 존재는 확인)
- guidance("governance control plane") 가 파이프라인 순서 gate 를 강제하는지 — 내부 동작 미확인
