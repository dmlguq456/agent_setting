# Axis 1 — 아키텍처 전반 + 실행 모델 (Hermes Agent / Nous Research)

> 조사 범위: repo·docs 식별 / repo 구조·핵심 모듈 / 실행 모델 / built-in tools / 플랫폼 게이트웨이
> 1차 소스 = github.com/NousResearch/hermes-agent + hermes-agent.nousresearch.com/docs
> 조사일: 2026-06-14. 대상 버전: v0.16.0 "The Surface Release" (2026-06-06)

---

## 0. 정식 repo / docs 확정

| 항목 | 값 | confidence |
|---|---|---|
| GitHub repo | **https://github.com/NousResearch/hermes-agent** | high (검색 1순위 + 직접 fetch 성공) |
| 공식 docs | **https://hermes-agent.nousresearch.com/docs/** | high (fetch 성공, TOC 확인) |
| License | **MIT** | high (README + repo LICENSE) |
| 언어/스택 | **Python 82.4% / TypeScript 13.6% / JavaScript 1.3%** (+ TeX, Shell) | high (repo 언어 통계) |
| 최신 릴리스 | **v0.16.0 "The Surface Release"** (2026-06-06) | high (repo release) |
| 인기도 | ~193k stars / 33.8k forks (2026-06 기준) | medium (단일 fetch, 시점 변동값) |

> ⚠️ 주의: 과제 브리프의 "47 built-in tools" 와 "hermes-agent.nousresearch.com/docs" 도메인은 확인됨. 단 **툴 개수는 버전별로 상이** — 아래 4절 참조. "47" 은 중간 버전 스냅샷으로 추정되며 현재 main 과 불일치.

---

## 1. 핵심 모듈 / repo 구조

**claim**: repo 는 단일 agent core (`AIAgent`) 를 중심으로 다중 entry point (CLI / Gateway / ACP / cron) 가 같은 core 를 공유하는 hub-and-spoke 구조다.
**근거**: 아키텍처 doc + 3rd-party mirror — *"The agent core is `AIAgent` in `run_agent.py`. All other subsystems — gateway, CLI, ACP server, cron scheduler — use this single agent core, so behavior is consistent across all platforms."*
**confidence**: high (공식 doc + mirror 교차)

### top-level 디렉토리 (repo file browser 직접 확인)

| 디렉토리 | 역할 | confidence |
|---|---|---|
| `agent/` | 코어 agent 로직 (`run_agent.py` = `AIAgent` orchestrator) | high |
| `tools/` | built-in tool 구현 (~86 .py 파일, registry 자동 등록) | high |
| `gateway/` | 메시징 플랫폼 게이트웨이 (`gateway/run.py` long-running process) | high |
| `hermes_cli/` (+ `cli.py`) | CLI 인터페이스 / entry point | high |
| `cron/` | 스케줄러 (`scheduler.py`, `jobs.py`, `blueprint_catalog.py`, `suggestions.py`) | high |
| `acp_adapter/`, `acp_registry/` | ACP (Agent Client Protocol) entry point | high |
| `plugins/` | 플러그인 확장 (user/project/entry-point 3중 discovery) | high |
| `providers/` | LLM provider 추상화 (`runtime_provider.py` 가 (provider,model)→(api_mode,key,base_url) 매핑) | high |
| `optional-mcps/`, `optional-skills/` | pluggable MCP·skill 번들 | high |
| `ui-tui/`, `tui_gateway/`, `web/`, `website/` | 인터페이스 레이어 (TUI / web) | high |
| `apps/`, `docker/`, `nix/`, `packaging/` | 앱 모듈·배포·패키징 | high |
| `tests/`, `scripts/`, `locales/`, `docs/` | 테스트·유틸·i18n·문서 | high |

### 코어 서브시스템 (아키텍처 doc 의 명명)

- **AIAgent (`run_agent.py`)** — *"synchronous orchestration engine"*: provider 선택 → prompt 조립 → tool 실행 → retry → persistence. high
- **Prompt Builder** — 3-tier system prompt: `stable` → `context` → `volatile` (identity/tool guidance/skills → context files → memory/profile/timestamp). high
- **Provider Resolution (`runtime_provider.py`)** — 18+ provider 매핑. high
- **Tool Registry (`tools/registry.py`)** — *"70+ registered tools across ~28 toolsets"*. high
- **Session Storage (`hermes_state.py`)** — *"SQLite-based session storage with FTS5 full-text search"*. high
- **Context Engine / `ContextCompressor`** — 임계치 초과 시 lossy summarization 압축 (pluggable). high

---

## 2. 실행 모델

**claim**: Hermes 는 **persistent daemon** 으로 산다 — gateway 가 long-running process 로 떠서 다중 채널 이벤트를 받고, 같은 core 가 동기적으로 turn 을 처리하며, 상태는 SQLite 로 재시작에 걸쳐 지속된다.
**근거**:
- gateway = *"Long-running process with 20 platform adapters, unified session routing, user authorization (allowlists + DM pairing)"* (아키텍처 doc)
- *"Persistent memory, skills, and session history in SQLite across restarts."* (3rd-party mirror)
**confidence**: high

### 프로세스/세션 모델

| 측면 | 내용 | confidence |
|---|---|---|
| 데몬 모델 | gateway (`gateway/run.py`) 가 장수 프로세스, profile 마다 gateway PID 분리 | high |
| 멀티-profile 격리 | `hermes -p <name>` 마다 독립 HERMES_HOME / config / memory / sessions / gateway PID, **동시 실행 가능** | high |
| 세션 지속 | SQLite session storage, lineage tracking (compression 간 parent/child), per-platform isolation, atomic writes | high |
| 동시성 | tool call 을 `ThreadPoolExecutor` 로 순차 또는 병렬 실행 (**최대 8 parallel workers**) | high (mirror; ❓공식 doc 직접 수치 미확인) |
| 컨텍스트 관리 | `ContextCompressor` 가 임계치 초과 시 lossy summarization | high |

### self-host / 배포 가정

**claim**: 단일 사용자 self-host 가 기본 가정. *"$5 VPS"* ~ GPU cluster ~ serverless 까지 *"lives wherever you put it"*. 사용자가 어디에 두든 20+ 메시징 플랫폼으로 원격 대화. user authorization 은 allowlist + DM pairing (= 개인/소규모 신뢰 모델).
**근거**: docs *"lives wherever you put it"*, *"talk to it from Telegram while it works on a cloud VM"*; gateway authorization = allowlists + DM pairing.
**confidence**: high

**6 terminal backend** (execution 환경): **local, Docker, SSH, Singularity, Modal, Daytona**. Modal·Daytona 는 *"serverless persistence — environment hibernates when idle and wakes on demand"* (idle 시 거의 무비용). confidence: high

### LLM backend

**claim**: provider-agnostic. open-source 모델·상용 API·로컬 endpoint 모두 지원.
**근거**: README/docs/mirror 교차 — Nous Portal, OpenRouter (200+ models), OpenAI, Anthropic, AWS Bedrock, Google Gemini, NVIDIA NIM (Nemotron), DeepSeek, NovitaAI, Xiaomi MiMo, z.ai/GLM, Kimi/Moonshot, MiniMax, HuggingFace, 그리고 *"your own endpoint"* (OpenAI-compatible). Nous 자체 모델 = Hermes, Nomos, Psyche.
**confidence**: high (복수 1차 소스). 단 개별 provider 목록은 버전마다 추가됨.
**❓미검증**: 로컬 DGX Spark / RTX 특정 최적화 경로 — 브리프 언급 항목이나 1차 소스에서 명시 못 찾음. (NVIDIA NIM 지원은 확인되나 DGX Spark 전용 path 는 low/미확인.)

---

## 3. Built-in tools

**claim**: 현재 main(v0.16.0) 기준 registry 에 **70+ tools / ~28 toolsets** 등록. 버전별 표기가 달라 단일 숫자로 고정 불가.
**근거 & 버전별 수치 (불일치 명시)**:

| 출처 | 표기 | 분류 |
|---|---|---|
| 아키텍처 doc (현재) | *"70+ registered tools across ~28 toolsets"* | 1차 (가장 권위) |
| docs 일반 페이지 | *"60+ built-in tools"* | 1차 |
| README (스냅샷) | *"40+ tools"* | 1차 (구버전 잔존 추정) |
| 과제 브리프 | "47 built-in tools" | ❓중간 버전 스냅샷 추정, 현재 main 과 불일치 |
| 3rd-party mirror (v0.2.0) | *"166 tracked skills (87 bundled + 79 optional)"* ← 이건 **skills 수** (tool 과 별개 개념) | 2차 |

> **해석 주의**: "tools" (registry 의 호출 가능 함수) 와 "skills" (agent 가 학습해 저장하는 절차적 메모리 파일) 는 **다른 개념**. mirror 의 166 은 skills. tool 수치는 70+ 가 현재 best estimate. confidence: **medium** (1차 소스끼리도 40/60/70 으로 흔들림 — 버전 drift).

### tool 카테고리 (실제 `tools/*.py` 파일에서 귀납)

- **파일/터미널/코드**: `file_tools.py`, `file_operations.py`, `terminal_tool.py`, `read_terminal_tool.py`, `code_execution_tool.py`, `computer_use_tool.py`
- **웹/브라우저**: `web_tools.py`, `browser_tool.py`, `browser_cdp_tool.py`, `browser_camofox.py`, `read_extract.py`, `x_search_tool.py`
- **미디어 생성**: `image_generation_tool.py`, `video_generation_tool.py`, `tts_tool.py`, `transcription_tools.py`, `vision_tools.py`, `voice_mode.py`, `neutts_synth.py`
- **메시징/게이트웨이**: `send_message_tool.py`, `discord_tool.py`, `clarify_gateway.py`, `homeassistant_tool.py`, `feishu_doc_tool.py`, `feishu_drive_tool.py`, `yuanbao_tools.py`
- **메모리/스킬 (self-improving 핵심)**: `memory_tool.py`, `session_search_tool.py`, `skill_manager_tool.py`, `skills_tool.py`, `skills_hub.py`, `skills_sync.py`, `skill_provenance.py`, `skill_usage.py`
- **스케줄/작업관리**: `cronjob_tools.py`, `todo_tool.py`, `kanban_tools.py`, `delegate_tool.py`, `mixture_of_agents_tool.py`
- **확장/통합**: `mcp_tool.py`, `mcp_oauth.py`, `microsoft_graph_client.py`, `managed_tool_gateway.py`
- **보안/안전**: `path_security.py`, `url_safety.py`, `threat_patterns.py`, `tirith_security.py`, `osv_check.py`, `write_approval.py`, `approval.py`

confidence: high (파일명 직접 확인). 단 위 중 다수는 _helper_ (`lazy_deps.py`, `schema_sanitizer.py` 등) 라 실제 registry 노출 tool 수 < 파일 수.

### tool 등록·확장 메커니즘

**claim**: import-time **auto-discovery** — `tools/*.py` 에 top-level `registry.register()` 가 있으면 자동 등록, manual import list 불필요. 외부 확장은 3중 plugin discovery.
**근거**: 아키텍처 doc — *"Any `tools/*.py` file with a top-level `registry.register()` call is auto-discovered — no manual import list needed"*. plugin 소스 3종: user (`~/.hermes/plugins/`), project (`.hermes/plugins/`), pip entry points. 특수 plugin 2종 = memory provider, context engine (각 single-select).
**confidence**: high

---

## 4. 메시징 플랫폼 게이트웨이

**claim**: 단일 gateway 프로세스가 플랫폼별 adapter 를 통해 **20+ 채널** 에 동시 연결. 한 agent core 가 모든 채널을 unified session routing 으로 처리.
**근거 (버전별 수치)**:
- 아키텍처 doc: *"20 platform adapters"* — telegram, discord, slack, whatsapp, signal, matrix, mattermost, email, sms, dingtalk, feishu, wecom, weixin, bluebubbles, qqbot, homeassistant, webhook, api_server, yuanbao (+추가)
- 3rd-party mirror (v0.2.0): **22 platforms** — 위 + IRC, Microsoft Teams, Google Chat, LINE, SimpleX Chat
- README (스냅샷): 6 개 (Telegram/Discord/Slack/WhatsApp/Signal/Email) ← 구버전
**confidence**: high (20+ 라는 사실), 정확 개수는 medium (버전 drift, 20~22)

### gateway 아키텍처 (한 agent ↔ N 채널)

**claim**: data flow = `platform event → Adapter → GatewayRunner → AIAgent → response delivery back through adapter`. 채널마다 adapter 가 프로토콜을 정규화하고, session 은 per-platform isolation 으로 분리 저장되나 동일 core·동일 memory/skills/profile 을 공유.
**근거**: 아키텍처 doc data-flow 서술 + *"unified session routing"* + per-platform session isolation.
**confidence**: high

- 인증/접근제어: allowlists + DM pairing (개인/신뢰 그룹 모델). high
- cron 결과도 *"delivery to any platform"* 으로 같은 gateway 통해 push (daily report·nightly backup·weekly audit 를 자연어로 unattended 실행). high

---

## 5. 미검증 / 갭 (정직 표기)

- ❓ **정확한 built-in tool 수**: 1차 소스끼리 40/60/70 불일치. "47" 은 어느 버전에도 정확 매칭 안 됨 (중간 스냅샷 추정). 확정하려면 특정 tag 의 `tools/registry.py` 코드 직독 필요.
- ❓ **DGX Spark / RTX 로컬 backend 전용 path**: NVIDIA NIM 지원은 확인, DGX Spark 전용 최적화는 1차 소스 미확인 (low).
- ❓ **ThreadPoolExecutor 8-worker 수치**: 3rd-party mirror 만 명시, 공식 doc 직접 인용 미확보 (값 자체는 그럴듯, confidence medium).
- ❓ **execution-model 전용 doc 페이지**: `/docs/developer-guide/architecture/execution-model` 등 일부 deep-link 404 — 단일 architecture 페이지에서 정보 취합함.
- 본 카드는 design constraints(`analysis_project/paper/`) 부재 — 해당 프로젝트는 spec/논문이 아닌 _외부 기술 벤치마킹_ 조사라 정상. research survey 와 web 1차 소스에만 근거.

---

## 출처 ledger

| URL | 분류 | 무엇을 근거했나 |
|---|---|---|
| https://github.com/NousResearch/hermes-agent | 1차 | repo 확정·README·license·언어·v0.16.0·top-level 디렉토리·stars |
| https://github.com/NousResearch/hermes-agent/tree/main/tools | 1차 | tools 디렉토리 86 .py 파일 목록 → tool 카테고리 귀납 |
| https://github.com/NousResearch/hermes-agent/blob/main/cron | 1차 | cron 서브시스템 파일 구성 (scheduler/jobs/blueprint_catalog/suggestions) |
| https://raw.githubusercontent.com/NousResearch/hermes-agent/main/README.md | 1차 | README verbatim: 40+ tools·6 platforms·LLM backend 목록·cron 서술·MIT |
| https://hermes-agent.nousresearch.com/docs/ | 1차 | docs 확정·TOC·60+ tools·20+ platforms·learning loop |
| https://hermes-agent.nousresearch.com/docs/developer-guide/architecture | 1차 | 코어 컴포넌트 명명(AIAgent/Prompt Builder/Provider Resolution/Tool Registry/Session Storage)·70+ tools ~28 toolsets·20 adapter·auto-discovery·plugin 3종·data flow |
| https://github.com/mudrii/hermes-agent-docs | 2차 | 교차검증: AIAgent in run_agent.py·ThreadPoolExecutor 8 worker·SQLite+FTS5·22 platforms·166 skills(87+79)·provider 목록 |
| https://medium.com/@tentenco/... (Ewan Mak) | 2차 | 배경 맥락(데스크탑 앱·출시일) — 카드 본문 직접 근거 X |
| https://hermes-ai.net/ | 저신뢰 | SEO 사이트, 교차검증용으로만 봄, 단독 근거 미사용 |
| https://www.aibuilderclub.com/blog/... | 저신뢰 | 배경 수치(180k stars 등) 참고만, 단독 근거 미사용 |
