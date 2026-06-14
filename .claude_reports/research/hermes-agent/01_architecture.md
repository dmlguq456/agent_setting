# 01 — Hermes Agent 아키텍처 landscape

> 근거: `cards/axis1_architecture.md` (1차 = github.com/NousResearch/hermes-agent + hermes-agent.nousresearch.com/docs). 대상 v0.16.0.

---

## 1. 한눈 요약

Hermes 는 **단일 agent core (`AIAgent`)** 를 중심으로 4개 entry point 가 같은 core 를 공유하는 **hub-and-spoke** 구조이며, gateway 가 **persistent daemon** 으로 떠서 20+ 채널을 받고 상태는 SQLite 로 재시작에 걸쳐 지속된다. LLM backend 는 provider-agnostic, tool 은 import-time auto-discovery 로 70+ 등록, prompt 는 3-tier 로 조립된다.

---

## 2. hub-and-spoke — 단일 core, 4 entry

**claim**: 모든 서브시스템(gateway·CLI·ACP·cron)이 `AIAgent`(`run_agent.py`) 하나를 공유 → "behavior is consistent across all platforms". (confidence: high — 공식 doc + mirror 교차)

| entry point | 모듈 | 성격 |
|---|---|---|
| CLI | `hermes_cli/` · `cli.py` | 대화형 단발 |
| Gateway | `gateway/run.py` | long-running, 20+ 채널 |
| ACP | `acp_adapter/` · `acp_registry/` | Agent Client Protocol |
| Cron | `cron/scheduler.py` · `jobs.py` | 60초 tick 스케줄러 |

코어 서브시스템(architecture doc 명명):

| 컴포넌트 | 모듈 | 역할 |
|---|---|---|
| **AIAgent** | `run_agent.py` | "synchronous orchestration engine" — provider 선택→prompt 조립→tool 실행→retry→persistence |
| **Prompt Builder** | — | 3-tier system prompt (§5) |
| **Provider Resolution** | `runtime_provider.py` | (provider,model)→(api_mode,key,base_url) 매핑, 18+ provider |
| **Tool Registry** | `tools/registry.py` | "70+ registered tools across ~28 toolsets" |
| **Session Storage** | `hermes_state.py` | SQLite + FTS5 full-text search |
| **Context Engine** | `ContextCompressor` | 임계치 초과 시 lossy summarization (pluggable) |

**Takeaway**: 한 core·N entry 설계 덕에 채널이 늘어도 동작 일관성이 공짜로 따라온다 — 우리 세팅의 "한 라우터(WORKFLOW.md)·N entry(autopilot-*)" 와 철학적으로 닮았다.

---

## 3. persistent daemon 실행 모델

**claim**: gateway 가 long-running process 로 살며, 상태는 SQLite 로 재시작에 걸쳐 지속, profile 마다 격리되어 동시 실행 가능. (confidence: high)

| 측면 | 내용 | confidence |
|---|---|---|
| 데몬 모델 | gateway(`gateway/run.py`)가 장수 프로세스, profile 마다 PID 분리 | high |
| 멀티-profile 격리 | `hermes -p <name>` 마다 독립 HERMES_HOME/config/memory/sessions, 동시 실행 | high |
| 세션 지속 | SQLite, lineage tracking(compression 간 parent/child), per-platform isolation, atomic writes | high |
| 동시성 | tool call 을 `ThreadPoolExecutor` 로 순차/병렬, 최대 8 parallel workers | high (mirror; ❓공식 doc 직접 수치 미확인) |
| 컨텍스트 관리 | `ContextCompressor` lossy summarization | high |

**self-host 가정**: 단일 사용자 self-host 기본. "$5 VPS ~ GPU cluster ~ serverless" — "lives wherever you put it". 6 terminal backend = local / Docker / SSH / Singularity / Modal / Daytona (Modal·Daytona 는 idle 시 hibernate). user authorization = allowlist + DM pairing (개인/소규모 신뢰 모델). (confidence: high)

**Takeaway**: persistent daemon + multi-channel gateway 는 우리에게 **전혀 없는 축**이다 — 우리는 세션 단위 + cron(oncall/note) 분리 모델. 다만 우리 쓰임(논문·실험·코드 파이프)에는 daemon 이 불필요할 수 있어, 이식보다는 "왜 우리에겐 안 맞나"를 명시하는 게 정직하다.

---

## 4. tool registry — 70+ tools, auto-discovery

**claim**: import-time auto-discovery — `tools/*.py` 에 top-level `registry.register()` 만 있으면 자동 등록(manual import list 불필요). 외부 확장은 3중 plugin discovery(user `~/.hermes/plugins/` · project `.hermes/plugins/` · pip entry points). 특수 plugin 2종 = memory provider, context engine (각 single-select). (confidence: high)

> **개수 주의 (C1 정정)**: architecture doc "70+", docs 일반 "60+", README "40+", 브리프 "47" — **버전 drift**. tool(registry 의 호출 가능 함수) ≠ skill(에이전트가 학습·저장하는 절차 파일). mirror 의 "166 skills(87 bundled + 79 optional)"는 skills 수. tool 개수는 70+ 가 best estimate(confidence: medium).

tool 카테고리 (실제 `tools/*.py` 귀납):

| 그룹 | 대표 tool |
|---|---|
| 파일/터미널/코드 | `file_tools` · `terminal_tool` · `code_execution_tool` · `computer_use_tool` |
| 웹/브라우저 | `web_tools` · `browser_tool` · `browser_cdp_tool` · `x_search_tool` |
| 미디어 생성 | `image_generation_tool` · `video_generation_tool` · `tts_tool` · `vision_tools` |
| 메시징/게이트웨이 | `send_message_tool` · `discord_tool` · `homeassistant_tool` |
| **메모리/스킬 (self-improving 핵심)** | `memory_tool` · `session_search_tool` · `skill_manager_tool` · `skills_hub` · `skill_usage` |
| 스케줄/작업관리 | `cronjob_tools` · `todo_tool` · `kanban_tools` · `delegate_tool` |
| 확장/통합 | `mcp_tool` · `mcp_oauth` · `managed_tool_gateway` |
| 보안/안전 | `path_security` · `url_safety` · `write_approval` · `osv_check` |

**Takeaway**: auto-discovery + 3중 plugin = 우리 `skills/` 디렉토리 자동 로드(SKILL.md description 매 세션 주입)와 동형 — Hermes 는 여기에 *런타임 자기편집*까지 얹은 게 차이.

---

## 5. 3-tier prompt builder

**claim**: system prompt 는 안정도 순 3층으로 조립 — prefix cache 보존을 위해 자주 안 바뀌는 것을 앞에. (confidence: high)

| tier | 내용 | 안정도 |
|---|---|---|
| **stable** | identity / tool guidance / skills | 거의 불변 (prefix-cache 핵심) |
| **context** | context files | 세션·프로젝트 단위 |
| **volatile** | memory / profile / timestamp | 매번 변함 |

이 설계가 axis3 의 "MEMORY.md/USER.md frozen snapshot" 과 직결된다 — memory 를 volatile tier 에 두되 *세션 시작 시 한 번 freeze* 해서, 세션 중 디스크 변경이 prefix cache 를 깨지 않도록 한다.

**Takeaway**: prefix-cache 를 의식한 안정도 layering 은 우리 CLAUDE.md(자동 주입·얇은 부트스트랩) + on-demand Read(WORKFLOW.md) 분리와 같은 직관 — "안 바뀌는 건 항상, 바뀌는 건 필요할 때".

---

## 6. 메시징 게이트웨이 — 1 agent ↔ N 채널

**claim**: 단일 gateway 프로세스가 플랫폼별 adapter 로 20+ 채널 동시 연결, 한 core 가 unified session routing 으로 처리. data flow = `platform event → Adapter → GatewayRunner → AIAgent → response`. (confidence: high; 정확 개수는 medium — 버전 drift 20~22)

- 채널 예: telegram·discord·slack·whatsapp·signal·matrix·email·sms·feishu·wecom·homeassistant·webhook·api_server (+IRC·Teams·LINE·SimpleX in mirror)
- 인증: allowlists + DM pairing.
- cron 결과도 같은 gateway 로 "delivery to any platform" — daily report·nightly backup 을 자연어로 unattended.

**Takeaway**: 우리에겐 gateway 가 없다. 가장 가까운 대응은 oncall/note 가 `notes/` 에 보고서를 떨구는 것 — *push 채널* 이 아니라 *pull 파일* 모델. 이식 우선순위 낮음(쓰임 불일치).

---

## 미검증 / 갭

- ❓ 정확한 tool 수 (40/60/70 drift) — 특정 tag `tools/registry.py` 직독 필요.
- ❓ DGX Spark / RTX 전용 path — NVIDIA NIM 지원은 확인, 전용 최적화는 1차 미확인(low).
- ❓ ThreadPoolExecutor 8-worker — mirror 만, 공식 doc 직접 인용 미확보(medium).
