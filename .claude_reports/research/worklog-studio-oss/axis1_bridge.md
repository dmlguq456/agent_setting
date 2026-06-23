# 축 1 — 에이전트를 백엔드로 쓰는 브리지 (로컬 coding-agent CLI ↔ 웹 UI)

> 조사 목적: 로컬 coding-agent CLI(claude code / codex / aider 등)를 long-running 프로세스로 감싸 stdio/pty 를 websocket·SSE 로 중계해 웹/데스크톱 UI 에 스트리밍하는 OSS 패턴 발굴.
>
> **제약/렌즈**: local-first(클라우드 의존 X) · BYOK · 기존 하네스(PATH 의 claude code/codex CLI + skills/memory) 재사용 · 디스크=상태(live-REPL 메모리상태 회피) · 앱에 임베드 가능(통째 채택 아님) · 라이선스 명확(MIT/Apache 선호).
>
> **이미 검토한 기준선** (중복 서술 금지, 대비만): `nexu-io/open-design`(OD) = web+daemon 이 CLI 를 spawn, sandboxed iframe 프리뷰, `agents.ts` 어댑터로 여러 CLI 추상화. / `opencoworkai/open-codesign`(OCD) = Electron + pi 엔진 내장(spawn 아님), boolean parity 검증.
>
> 메타데이터는 GitHub API / npm registry / crates.io 실측 (2026-06-23 조회). 못 본 경로는 "(추정)" 표기.

---

## 후보 1 — pi (earendil-works/pi)

- **레포**: earendil-works/pi (https://github.com/earendil-works/pi) — ⭐64,881 · MIT · 최근 push 2026-06 · archived=No
  - ⚠️ 프롬프트의 `mariozechner/pi-mono` 은 **stale**: 레포는 `badlogic/pi-mono → earendil-works/pi` 로 이전됐고, npm scope `@mariozechner/*` 는 **deprecated**(latest 0.73.1) → 현 scope `@earendil-works/*`(0.79.x).
- **한 줄 정체**: 미니멀 TypeScript 에이전트 toolkit 모노레포 — `packages/{ai, agent, coding-agent, tui}` (web/server 패키지 없음).
- **세션 연속성 방식**: **디스크 JSONL + 트리(branch) 모델**. `~/.pi/agent/sessions/` 에 working-dir 별로 JSONL 자동 저장. 각 엔트리 `id`+`parentId`(파일 안 늘리고 branching). resume: `pi -c`(최근 이어가기)·`pi -r`(선택)·`pi --session <path|id>`·`pi --fork <path|id>`. 프로그램적 opt-out: `SessionManager.inMemory()`. → **디스크=상태 렌즈에 정확히 부합**.
- **tool_call/텍스트 스트림 이벤트 스키마**: **typed event union, NDJSON 직렬화** (JSON-RPC 도 SSE 도 아님). 라이브러리: `agent.subscribe((event,signal)=>…)` 또는 `agentLoop()` async generator. 이벤트 `type`: `agent_start`·`turn_start`·`message_start`·`message_update`(assistant 스트리밍 delta)·`message_end`·`tool_execution_start`(`toolCallId`/`toolName`/`args`)·`tool_execution_update`·`tool_execution_end`(`result`)·`turn_end`(`toolResults[]`)·`agent_end`. CLI `--mode json` 은 동일 이벤트를 LF-delimited JSON lines 로 + `queue_update`·`compaction_start/end`·`auto_retry_start/end`. `--mode rpc` = stdin/stdout LF-delimited JSONL framing(자체 framing, ACP 아님).
- **권한/샌드박스 모델**: **빌트인 없음** — README 명시 "Pi does not include a built-in permission system". 격리는 컨테이너 위임(Gondolin micro-VM / Docker / OpenShell). 툴 게이팅은 allowlist 만(`--tools`/`--exclude-tools`), 인터랙티브 allow/deny 모델 없음.
- **임베드 가능 여부**: **완전 라이브러리화 가능** — 4 npm 패키지 모두 v0.79.x: `@earendil-works/pi-ai`(통합 LLM API `getModel()`)·`pi-agent-core`(런타임·event union·`Agent`·`agentLoop`)·`pi-coding-agent`(CLI+SDK, `bin: pi`)·`pi-tui`. SDK exports: `createAgentSession`·`createAgentSessionRuntime`·`AgentSessionRuntime`·`SessionManager`·`AuthStorage`·`ModelRegistry`.
- **내가 lift할 구체 모듈/파일**:
  - `packages/agent` — `Agent.subscribe()` / `agentLoop()` async generator = ws 로 흘려보낼 자연스러운 feed. `streamProxy()`(브라우저 proxy helper) = 웹 브리지에 직결.
  - `packages/coding-agent/docs/json.md` — `--mode json` NDJSON 와이어 스키마(SSE 로 재방출할 정확한 shape).
  - `SessionManager`(+`.inMemory()`)·`createAgentSessionRuntime` from `pi-coding-agent`.
  - `getModel()` from `pi-ai`; `AuthStorage`·`ModelRegistry`.
  - (추정) 각 패키지 내부 `src/*.ts` 정확 경로는 README export 명 기준.
- **적합도**: **상** — local-first·BYOK(`pi-ai` 멀티프로바이더)·디스크 JSONL·라이브러리 임베드·MIT 모두 충족. 단 권한·server 는 직접 구현.
- **채택 리스크**: 권한/샌드박스·HTTP/ws server **미탑재**(직접 빌드). v0.x — API 변동성. **단일 엔진 종속**(pi 자체가 백엔드가 됨 ≠ 내 PATH 의 claude/codex 재사용). OCD 가 이미 pi 를 내장한 전례 = 안정성 증거이자 차별성 없음.
- **OD/OCD 대비 새로 얻는 것**: OCD 가 임베드한 그 pi 엔진의 _공식 SDK 표면_(`createAgentSessionRuntime`·`--mode json` 와이어). OCD 가 한 "spawn 아닌 내장" 을 더 깔끔한 typed-event feed 로 직접 따라할 수 있음. 단 **내 제약의 "PATH 의 claude/codex 재사용" 은 충족 못 함**(pi 가 곧 엔진).

---

## 후보 2 — Zed ACP (agentclientprotocol/agent-client-protocol)

- **레포**: agentclientprotocol/agent-client-protocol (https://github.com/agentclientprotocol/agent-client-protocol) — ⭐3,480 · Apache-2.0 · 최근 push 2026-06 · archived=No
  - ⚠️ `zed-industries/agent-client-protocol` 에서 **전용 org 로 이전**(301). v1 stable + v2 draft 동시 개발 중(`schema/v1/`, `schema/v2/`).
- **한 줄 정체**: "LSP for AI coding agents" — 에디터↔에이전트 JSON-RPC 2.0 표준 프로토콜(2025-08 Zed 발). 엔진이 아니라 **와이어 계약 + 다언어 reference SDK**.
- **세션 연속성 방식**: **resume-id 기반(spec-level)** — 영속화는 에이전트 책임이되 id 로 표준화. `session/new`(→`sessionId`)·`session/load`·`session/list`·`session/resume`·`session/close`·`session/delete`. JSONL-vs-memory 는 강제 안 함, id 기반 create/load/resume 핸드셰이크만 표준화.
- **tool_call/텍스트 스트림 이벤트 스키마**: **JSON-RPC 2.0(duplex, 보통 stdio)**.
  - Agent-handled: `initialize`·`authenticate`·`session/new`·`session/load`·`session/set_mode`·`session/set_config_option`·`session/prompt`·`session/cancel`·`session/list`·`session/delete`·`session/resume`·`session/close`·`logout`.
  - Client-handled: `session/request_permission`·`session/update`·`fs/write_text_file`·`fs/read_text_file`·`terminal/create`·`terminal/output`·`terminal/release`·`terminal/wait_for_exit`·`terminal/kill`.
  - 스트리밍 = **`session/update` notification**(`sessionUpdate` discriminator): `agent_message_chunk`·`agent_thought_chunk`·`user_message_chunk`·`tool_call`·`tool_call_update`·`plan`·`available_commands_update`. `tool_call` 필드: `toolCallId`·`title`·`status`(`pending`/`in_progress`/`completed`/`failed`)·`kind`(`read`/`edit`/`delete`/`move`/`search`/`execute`/`think`/`fetch`/`switch_mode`/`other`)·`content`(text/diff/terminal)·`locations`·`rawInput`/`rawOutput`. ContentBlock: `text`/`image`/`audio`/`resource`/`resource_link`.
- **권한/샌드박스 모델**: **명시적 client-mediated 권한 RPC** — `session/request_permission`(에이전트가 client/에디터에 툴 액션 승인 요청, 사람이 allow/deny). `authenticate`/`logout` + `session/set_mode`. 파일 접근은 직접 디스크 X, `fs/*`·`terminal/*` 브로커링. → **8 후보 중 권한 모델이 가장 정식으로 명세된 축**.
- **임베드 가능 여부**: 프로토콜이라 모든 바인딩이 라이브러리:
  - Rust: `agent-client-protocol` 0.15.1(crates.io, 누적 ~2.74M·최근 ~1.76M downloads, 어제 갱신) + `agent-client-protocol-schema`(타입).
  - TS/npm: `@agentclientprotocol/sdk` 0.29.0(Apache-2.0, 2026-06-22 publish — 활발). 구명 `@zed-industries/agent-client-protocol` 0.4.5 도 존재.
  - Python: PyPI `agent-client-protocol` 0.10.1. + Java(`java-sdk`)·Kotlin(`acp-kotlin`).
- **내가 lift할 구체 모듈/파일**:
  - TS SDK `@agentclientprotocol/sdk`: `AgentSideConnection`·`ClientSideConnection`. → `ClientSideConnection` 으로 에이전트 구동 + `session/update` 수신 후 ws/SSE 재방출.
  - 스키마 SoT(자체 바인딩 생성용): `schema/v1/schema.json` + `schema/v1/meta.json`(method registry); OpenAPI `agentclientprotocol.com/api-reference/openapi.json`.
  - Rust 측이면 `agent-client-protocol` crate.
  - (추정) stdio transport 배선 세부 = `docs/protocol/v1/transports.mdx`.
- **적합도**: **상(전략)** — **내 제약의 핵심을 정통으로 푼다**: 표준 JSON-RPC 스키마 + 정식 `session/request_permission` + multi-lang client lib. **PATH 의 claude/codex 재사용 직결** — Gemini CLI(`--acp` 네이티브)·Codex CLI·Goose 가 ACP 에이전트, Claude Code 는 Zed SDK 어댑터로 ACP 화 → 내 CLI 를 _바꾸지 않고_ ACP 백엔드로 붙임. archived=No, 어제도 publish.
- **채택 리스크**: 스타 3.5k(프로토콜이라 절대수치 오해 소지 — downloads·구현체 폭이 진짜 신호). v1/v2 동시 진화 = 버전 추적 부담. 엔진이 아니라 **에이전트는 내가 호스팅/어댑트**해야 함(claude code ACP 화는 어댑터 경유). 권한 UX 는 spec 만, UI 는 직접.
- **OD/OCD 대비 새로 얻는 것**: **OD 의 ad-hoc `agents.ts`(여러 CLI 추상화) 를 표준 JSON-RPC 스키마(`session/*`·`tool_call`·`request_permission`)로 대체** — 어댑터를 매 CLI 마다 짜는 대신 ACP 한 계약으로 swappable backend. OD 가 직접 만든 권한/프리뷰 ad-hoc 레이어를 `session/request_permission`+`fs/*`+`terminal/*` 표준으로 승격.

---

## 후보 3 — aider (Aider-AI/aider)

- **레포**: Aider-AI/aider (https://github.com/Aider-AI/aider) — ⭐46,587 · Apache-2.0 · 최근 push 2026-05 · archived=No
- **한 줄 정체**: 터미널 AI pair-programming(Python). 에이전트 "툴" 개념이 아니라 LLM 이 edit-block 을 내고 coder 가 파싱·적용.
- **세션 연속성 방식**: **디스크 Markdown 히스토리**(+ plaintext input history). `--chat-history-file`=`.aider.chat.history.md`·`--input-history-file`=`.aider.input.history`·`--llm-history-file`=None(opt-in raw 로그). **resume-id 없음** — 연속성=마크다운 재읽기(`--restore-chat-history`, default False). 인메모리 상태는 `Coder.cur_messages`/`done_messages`/`partial_response_content`. → 디스크=상태이나 _human-readable md_ 라 replay 용 구조 transcript 아님.
- **tool_call/텍스트 스트림 이벤트 스키마**: **구조화 이벤트 없음 — Python generator + 터미널 텍스트**. `base_coder.py` 가 `yield from send_message()`/`show_send_output_stream()` 로 토큰을 콘솔에 렌더(JSON-RPC·SSE·typed union 전무). "tool call"=edit block(SEARCH/REPLACE·udiff·whole-file·patch)을 `editblock_coder.py`·`udiff_coder.py`·`wholefile_coder.py`·`patch_coder.py` 가 파싱. → **브리지하려면 stdout 스크레이프 or generator 인터셉트 필요**.
- **권한/샌드박스 모델**: **git 이 안전 모델**(OS 샌드박스 아님). `repo.py GitRepo.commit(aider_edits=True)` 가 매 AI 변경 auto-commit, `(aider)` author 표식 → `/undo`·`git revert` 가역. 게이팅=`--yes`(자동 승인)·`--dry-run`. 프로세스 격리 없음.
- **임베드 가능 여부**: **라이브러리 가능(비공식)** — PyPI `aider-chat`(0.86.x, Apache-2.0), `from aider.coders import Coder`. `Model(...)`→`Coder.create(...)`→`coder.run("instruction")`. ⚠️ 문서 명시: "python scripting API is not officially supported or documented, and could change without backwards compatibility".
- **내가 lift할 구체 모듈/파일**:
  - `aider/io.py` `InputOutput` — **가장 깔끔한 주입점**: subclass 해 prompt/output 을 ws 로 리다이렉트(yes/confirm·툴 출력·히스토리 전부 io 경유).
  - `aider/coders/base_coder.py` — `run()`/`run_one()`/`send_message()` generator seam.
  - `editblock_coder.py` 등 — 구조화 "tool call"(edit) 이벤트 노출용.
  - `aider/repo.py GitRepo` — diff/commit 이벤트.
  - `aider/args.py` — flag 표면(`-m`/`-f`/`--stream`/`--yes`/`--gui`).
- **적합도**: **하~중** — local-first·BYOK·git-안전모델·Apache 는 좋으나, **구조화 스트림·server 부재**로 브리지 비용이 높고(stdout 스크레이프) Python API 가 비공식·unstable. coding 특화는 강점.
- **채택 리스크**: scripting API 비공식·무계약. 머신 이벤트 프로토콜 전무 → UI tool-call 렌더가 빈약. `--gui`/`--browser` 는 Streamlit 앱(제어 가능한 API server 아님).
- **OD/OCD 대비 새로 얻는 것**: **git-as-safety auto-commit 패턴**(`(aider)` 표식 + `/undo`) — OD/OCD 의 ad-hoc 프리뷰/롤백 대비 _버전관리 네이티브 가역성_ 을 차용. 단 transport·UI 면에선 OD(spawn+iframe)·OCD(pi 내장)보다 후퇴.

---

## 후보 4 — continue.dev (continuedev/continue)

- **레포**: continuedev/continue (https://github.com/continuedev/continue) — ⭐34,284 · Apache-2.0 · 최근 push 2026-06 · archived=No
- **한 줄 정체**: 오픈소스 coding agent(TS 모노레포) — `core`(엔진) ↔ GUI/IDE 가 typed 메시지 프로토콜로 통신. **이 축에서 구조적으로 가장 "브리지" 같은 설계.**
- **세션 연속성 방식**: **디스크 JSON, resume-by-id first-class**. `core/util/history.ts HistoryManager`: sessions dir `~/.continue/sessions/`, per-session `<sessionId>.json`, index `sessions.json`. `save`/`load({id})`/`list({workspaceDirectory,...})`/`delete({id})`. CLI: `cn --resume`(최근)·`cn ls`(브라우즈). → **디스크=상태 + resume-id 둘 다 충족**.
- **tool_call/텍스트 스트림 이벤트 스키마**: **typed event union(JSON-RPC 유사), `[req,resp]` 튜플**. `core/protocol/*.ts`:
  - Core ← webview/IDE(`core.ts`): `llm/complete`·`llm/streamChat`(→AsyncGenerator)·`llm/compileChat`·`tools/call`·`tools/evaluatePolicy`·`tools/preprocessArgs`·`history/{list,load,save,delete,...}`·`config/*`·`mcp/*`.
  - Core → webview(`webview.ts`): `configUpdate`·`indexProgress`·**`sessionUpdate`**(세션/턴 상태 스트림)·**`toolCallPartialOutput`**(부분 tool-call 출력 스트림)·`getCurrentSessionId` 등.
  - forwarding 화이트리스트 = `core/protocol/passThrough.ts`(`WEBVIEW_TO_CORE_PASS_THROUGH` ~80키 / `CORE_TO_WEBVIEW_PASS_THROUGH` 12키).
- **권한/샌드박스 모델**: **policy layer** — `tools/evaluatePolicy`(`{policy,displayValue}`)·`tools/preprocessArgs` (call 전). 전용 워크스페이스 패키지 `@continuedev/terminal-security`(쉘 툴 가드). MCP 게이팅 `mcp/setServerEnabled`. OS 샌드박스는 미관측, 승인/policy 기반. (policy enum 값=추정, 헤더 파일 미확인.)
- **임베드 가능 여부**: **라이브러리화 가능**. `@continuedev/core`(`core/package.json` v1.1.0, `private` 아님 → publishable; `main`/`exports` 미확인이라 "partially confirmed"). CLI 가 의존하는 publishable 패키지: `@continuedev/sdk`(^0.0.13, 의도된 공개 SDK 표면)·`@continuedev/config-yaml`·`@continuedev/openai-adapters`·`@continuedev/terminal-security`·`@continuedev/cli`.
- **내가 lift할 구체 모듈/파일**:
  - `core/protocol/messenger/index.ts` — **`IMessenger`/`InProcessMessenger`(`send`/`on`/`request`/`invoke`) = 브리지 seam**. ws/SSE transport 위에 `IMessenger` 구현하면 typed 프로토콜 전체를 그대로 얻음.
  - `core/protocol/{core,webview,coreWebview}.ts` — UI 에 노출할 typed 계약.
  - `core/protocol/passThrough.ts` — ws relay 화이트리스트 그대로 사용.
  - `core/util/history.ts`+`paths.ts` — drop-in 세션 영속화(`~/.continue/sessions/<id>.json`).
  - `extensions/cli/`(`@continuedev/cli`, bin `cn`, `cn serve`, `dist/cn.js`) — **이미 "headless agent + HTTP server"** 레퍼런스 구현(처음부터 짜기 vs 베껴 적응).
- **적합도**: **상** — typed 스트림 프로토콜(`llm/streamChat`·`sessionUpdate`·`toolCallPartialOutput`) + swappable `IMessenger` transport + resume-id JSON store + policy/terminal-security + headless CLI(`cn serve`·`-p`·`--format json`) + publishable 패키지. Apache-2.0. local-first·BYOK 부합.
- **채택 리스크**: 종속성 무겁고(거대 모노레포) `core` 공개 표면 일부 미검증(`exports`·npm 403). `cn serve` 엔드포인트/포트/SSE-vs-REST shape 미확인(`extensions/cli/src/` 확인 필요). 자체 엔진이라 **PATH 의 claude/codex 직접 재사용은 아님**(continue core 가 LLM 호출 주체).
- **OD/OCD 대비 새로 얻는 것**: **OD 의 web↔daemon ad-hoc IPC 를 `IMessenger` + typed passThrough 화이트리스트로 정식화** — daemon 메시지를 손으로 정의하는 대신 검증된 namespaced 계약(`sessionUpdate`·`toolCallPartialOutput`)을 lift. `cn serve` 가 OD 의 "web+daemon" 구도를 이미 패키지화한 레퍼런스.

---

## 후보 5 — open-webui (open-webui/open-webui)

- **레포**: open-webui/open-webui (https://github.com/open-webui/open-webui) — ⭐142,686 · **NOASSERTION(수정 BSD-3 + 브랜딩 보호 조항)** · 최근 push 2026-06 · archived=No
- **한 줄 정체**: 풀스택 채팅 앱(Python FastAPI 백 + Svelte 프론트). coding-agent CLI 아니라 LLM UI.
- **세션 연속성 방식**: **DB(SQLAlchemy ORM, 기본 sqlite, Postgres/MySQL 가능)**. `models/chats.py Chat(Base)` — 대화 전체가 `chat = Column(JSON)` blob(history→messages), `chat_message` 테이블에도 dual-write. 서버 authoritative, 재접속 생존.
- **tool_call/텍스트 스트림 이벤트 스키마**: **Socket.IO(브라우저, websocket 우선) + SSE(HTTP fallback)**, 2-hop(upstream LLM SSE 를 서버가 소비→Socket.IO 재방출). `socket/main.py`: `AsyncServer`, 채널 `events`/`events:chat`/`events:channel`, `data.type` discriminator `chat:completion`/`message:update`/`status`/`typing`. 프론트 `Chat.svelte` 가 `choices[0].delta.content` 누적(OpenAI delta shape). tool_call delta 는 서버 `utils/middleware.py` 에서 `_split_tool_calls()` 정규화 + Responses-API path(`response.function_call_arguments.delta`); `__event_emitter__` 가 typed dict(`chat:completion`/`status`/`citation`/`terminal:*`) 방출 = **외부 에이전트 tool 이벤트 번역 seam**. ⚠️ 알려진 결함: 매 이벤트마다 누적 출력 전체를 HTML 재직렬화 → N토큰에 O(N²) 대역폭.
- **권한/샌드박스 모델**: **빌트인 샌드박스 없음** — 코드 실행은 외부 Jupyter 위임(`routers/utils.py` `/code/execute`, `CODE_EXECUTION_ENGINE=='jupyter'`). per-call tool-approval 게이트 없음(config flag 만). 이 축에서 가장 약함.
- **임베드 가능 여부**: **모놀리식 앱** — `main.py` 가 ~30 router 를 SQLAlchemy DB/Socket.IO/auth/RAG 에 결합. publishable 라이브러리·SDK·standalone transport 모듈 없음. 커스텀 라이선스가 UI verbatim lift 도 제한.
- **내가 lift할 구체 모듈/파일**(포크 시):
  - `backend/open_webui/utils/middleware.py` — SSE 소비→tool-call/text delta 파싱→`__event_emitter__` 재방출(**CLI→web 번역기 핵심 레퍼런스**).
  - `socket/main.py`(Socket.IO server+emit)·`functions.py`(Pipe executor, async-gen passthrough).
  - 프론트: `Chat.svelte`·`Messages/ResponseMessage.svelte`·`ContentRenderer.svelte`(tool-call=`<details type="tool_calls">` 마크다운 관례라 isolated 컴포넌트 아님 — 마크다운 스택째 lift 필요).
- **적합도**: **하(라이브러리로서)** — 모놀리식·NOASSERTION 라이선스(>50 user 시 브랜딩 제거 금지)·디스크 아닌 DB·전용 권한 UX 없음. 단 **비포크 경로 1 개 유효**: open-webui 를 그대로 띄우고 **Pipe Function / 외부 Pipelines 사이드카**로 claude/codex 를 shell-out 해 OpenAI-style delta yield → 완성 UI+스트리밍 무포크 획득(라이선스 50user 캡·Socket.IO transport·승인 UX 없음 감수).
- **채택 리스크**: 라이선스(source-available, OSI 비승인) — 재스킨 >50user 제품 불가(브랜딩 유지/엔터프라이즈 라이선스 필요). 결합도 높아 lift=벤더링. O(N²) 대역폭 결함.
- **OD/OCD 대비 새로 얻는 것**: **무포크 "완성 UI 즉시 획득" 경로**(Pipelines 사이드카 = 내 CLI 를 OpenAI-compat HTTP 로 감싸 등록, 소스 변경 0). OD 가 직접 만든 web UI 를 짜는 대신 142k-star 성숙 UI 를 그대로 — 단 local-first/임베드/라이선스 렌즈에선 OD·OCD 보다 후퇴.

---

## 후보 6 — LibreChat (danny-avila/LibreChat)

- **레포**: danny-avila/LibreChat (https://github.com/danny-avila/LibreChat) — ⭐39,662 · MIT · 최근 push 2026-06 · archived=No
- **한 줄 정체**: 풀스택 채팅 앱(Express 5 + MongoDB 백 + React 프론트). agents 프레임워크는 별 repo 의 standalone npm.
- **세션 연속성 방식**: **MongoDB(Mongoose 8)**. Conversation/Message 스키마는 `@librechat/data-schemas`. 진행 중 stream 상태는 별도 `packages/api/src/stream/ GenerationJobManager`(`InMemoryJobStore`/`RedisJobStore`). → 대화=Mongo, in-flight=mem/Redis. **파일 기반 아님**(디스크=상태 렌즈에 덜 부합).
- **tool_call/텍스트 스트림 이벤트 스키마**: **SSE(websocket 아님, native EventSource 도 아님 — `sse.js` POST-capable)**. 서버 `packages/api/src/utils/events.ts sendEvent` = `event: message\ndata: ${JSON}\n\n`. 이벤트 taxonomy(GraphEvents, `@librechat/agents`): 텍스트 `ON_MESSAGE_DELTA`/`ON_REASONING_DELTA`; 툴/스텝 `ON_RUN_STEP`/`ON_RUN_STEP_DELTA`/`ON_RUN_STEP_COMPLETED`/`ON_TOOL_EXECUTE`/`TOOL_END`; usage `CHAT_MODEL_END`/`ON_TOKEN_USAGE`; subagent `ON_SUBAGENT_UPDATE`; lifecycle `{created:true}`/`{final:true,...}`. 클라 `useSSE.ts`+`useStepHandler.ts`(`ON_RUN_STEP`→`ContentTypes.TOOL_CALL` part, delta arg concat). 신규 resumable: `request.js` 가 `{streamId,...}` 반환 후 `GenerationJobManager.emitChunk`.
- **권한/샌드박스 모델**: **Code Interpreter = 호스티드 외부 API**(`code.librechat.ai`, `LIBRECHAT_CODE_API_KEY`) — repo 내 재사용 샌드박스 없음, 유료 외부 서비스 위임. → **local-first 렌즈에 정면 위배.**
- **임베드 가능 여부**: **`@librechat/agents` 는 진짜 standalone npm**(별 repo `danny-avila/agents`, v3.2.45 MIT, 2026-06-23 publish, LibreChat 비의존, `@langchain/langgraph` 기반, exports `Run`·`Providers`·`createAgentSession`·`GraphEvents`). 단 **이건 LangGraph 에이전트 _런타임_ — 내 CLI 를 _호스팅_ 이 아니라 _대체_**. 본체 `packages/{api,client}` 는 workspace-internal("*"), React UI 는 패키지화된 컴포넌트 라이브러리 아님.
- **내가 lift할 구체 모듈/파일**:
  - `packages/api/src/utils/events.ts sendEvent`(~10줄, 즉시 이식) — SSE 라이터.
  - `api/server/controllers/agents/callbacks.js getDefaultHandlers`(GraphEvents→sendEvent 매핑) — **잘 설계된 tool-call/text-delta SSE 스키마 레퍼런스**.
  - 클라: `useSSE.ts`+`useStepHandler.ts`(tool-call delta 누적)·`Content/ToolCall.tsx`/`ToolCallGroup.tsx`(렌더, 단 data-provider 타입·Recoil·i18n 결합 — drop-in 아님).
- **적합도**: **하~중** — MIT 는 좋으나: Code Interpreter 외부 유료 API(local-first 위배)·Mongo(디스크파일 아님)·UI 패키지화 안 됨·**외부 에이전트 프로세스 plugin point 없음**(가장 가까운 게 내 CLI 를 MCP 서버로 감싸기). `@librechat/agents` 는 내 CLI 를 대체해 버림.
- **채택 리스크**: 외부 코드실행 API 의존. UI detangle 비용(Recoil/data-provider/i18n). 외부 프로세스 백엔드 미지원.
- **OD/OCD 대비 새로 얻는 것**: **SSE tool-call/text-delta 와이어 스키마의 모범 설계**(`sendEvent` + GraphEvents taxonomy) — OD 의 ad-hoc 스트림 포맷을 검증된 이벤트 분류(델타/스텝/usage/lifecycle)로 _참조_. 단 모듈 import 가 아니라 청사진으로만.

---

## 후보 7 — Sourcegraph Cody (sourcegraph/cody-public-snapshot)

- **레포**: sourcegraph/cody-public-snapshot (https://github.com/sourcegraph/cody-public-snapshot) — ⭐3,802 · Apache-2.0 · 최근 push 2025-08 · **archived=Yes(동결/사실상 dead)**
  - ⚠️ live `sourcegraph/cody` 는 **private 전환**. 이 snapshot 은 migration 직전 동결본(2025-08-01) — 더 안 받음.
- **한 줄 정체**: AI 코드 어시스턴트(VS Code/JetBrains/Neovim). Cody Agent = JSON-RPC over stdin/stdout 서버.
- **세션 연속성 방식**: `node-localstorage` KV 영속화(disk-backed key-value). resume-id/JSONL 정식 모델 아님 — config·상태를 KV 로. stateful 프로세스.
- **tool_call/텍스트 스트림 이벤트 스키마**: **JSON-RPC over stdin/stdout**. 프로토콜 SoT = `vscode/src/jsonrpc/agent-protocol.ts`("the single source of truth"), agent 측 `agent/src/{agent.ts, jsonrpc-alias.ts, protocol-alias.ts}`. 메서드(예): `initialize`·`extensionConfiguration/didChange`·chat 계열 등. **단 tool-call+text 스트리밍이 불투명한 `webview/postMessage` `ExtensionMessage` payload 안에 묻힘**(에디터 webview 내부 메시지) — clean 한 typed stream union 아님. `there can only be one client per server`(1-client-per-server stateful).
- **권한/샌드박스 모델**: **권한/샌드박스 레이어 없음**(코드 어시스턴트지 실행 에이전트 아님).
- **임베드 가능 여부**: npm `@sourcegraph/cody-agent`(`npx @sourcegraph/cody-agent`) — JetBrains(`CodyAgentClient.java`)·Neovim(`sg.nvim`) 가 소비. 단 "자동 바인딩 생성 툴 없음, 수동 작성" + archived.
- **내가 lift할 구체 모듈/파일**: `vscode/src/jsonrpc/agent-protocol.ts`(프로토콜 정의)·`agent/src/jsonrpc-alias.ts`(stdio JSON-RPC framing). (참조: PriNova/codypy = Python 바인딩, transport shape 확인용.)
- **적합도**: **하** — archived/dead(유지보수 0, live private), 스트리밍이 webview postMessage 에 묻혀 재사용 난해, 권한 모델 부재. JSON-RPC-over-stdio 의 _역사적 레퍼런스_ 가치만.
- **채택 리스크**: **dead 코드베이스 채택 = 최상위 리스크**. 업스트림 없음·보안 패치 없음. 와이어가 에디터 webview 결합.
- **OD/OCD 대비 새로 얻는 것**: 거의 없음 — JSON-RPC-over-stdio 가 ACP/cody-agent 양쪽에 있으나 **ACP 가 살아있고 더 깔끔**하므로 cody 는 ACP 에 흡수됨. dead 라 OD/OCD 대비 순익 없음(프로토콜 아이디어는 ACP 가 대체).

---

## 후보 8 — goose (aaif-goose/goose)

- **레포**: aaif-goose/goose (https://github.com/aaif-goose/goose) — ⭐50,057 · Apache-2.0 · 최근 push 2026-06 · archived=No
  - ⚠️ `block/goose` 에서 org 이전(301). live·유지보수 활발.
- **한 줄 정체**: Block 의 확장형 Rust AI 에이전트(코드 제안 너머 install/execute/edit/test). CLI + 임베드 가능한 API + `goosed` 데몬.
- **세션 연속성 방식**: **SQLite resumable sessions** — `~/.local/share/goose/sessions/sessions.db`. (⚠️ 프롬프트 가설의 `~/.config/goose` JSONL 은 outdated — 실제는 SQLite `sessions.db`.) → 디스크=상태 충족(파일 1개 DB).
- **tool_call/텍스트 스트림 이벤트 스키마**: **2 경로**. (1) `goosed`(Axum HTTP+WS 데몬)의 `/reply` 가 **typed SSE `MessageEvent` enum** 스트림. (2) **네이티브 ACP**(`session/prompt`) — 외부 `agent-client-protocol` crate 사용(`goose-acp-macros` crate 존재). → 자체 SSE _와_ 표준 ACP 둘 다 제공.
- **권한/샌드박스 모델**: **실제 per-tool permission engine**(툴별 승인 — 8 후보 중 pi/aider/cody 보다 정식). 확장은 MCP 기반.
- **임베드 가능 여부**: **clean Rust crate 경계** — `crates/{goose, goose-cli, goose-server, goose-providers, goose-mcp, goose-sdk, goose-sdk-types, goose-acp-macros, goose-test*}`. `goose-sdk`/`goose-sdk-types` = 임베드용 SDK 표면. `goose-server`=`goosed` 데몬.
- **내가 lift할 구체 모듈/파일**:
  - `crates/goose-server`(`goosed`, Axum HTTP+WS, `/reply` SSE `MessageEvent`) — 브리지 server 레퍼런스/직접 활용.
  - `crates/goose-sdk` + `goose-sdk-types` — 에이전트 임베드.
  - `goose-acp-macros` + `agent-client-protocol` crate 연동 — ACP 백엔드화 경로.
  - `crates/goose`(코어 에이전트 루프 + permission engine) · `crates/goose-mcp`(확장).
- **적합도**: **상** — local-first·BYOK·SQLite 디스크 상태·**임베드(crate SDK) + server(goosed) + ACP 둘 다** + 실제 권한 엔진 + MCP 확장 + Apache-2.0. 활발. **단 Rust**(TS/Python 하네스면 마찰).
- **채택 리스크**: Rust 종속(내 하네스 언어와 다르면 빌드/배포 무게). 자체 엔진이라 PATH claude/codex 직접 재사용은 ACP 경유. org 이전 직후 거버넌스 안정성은 모니터링.
- **OD/OCD 대비 새로 얻는 것**: **OD 의 ad-hoc daemon+spawn 을 production Rust 데몬(`goosed` /reply SSE)으로 대체** + **ACP 네이티브**라 OD 의 `agents.ts` 어댑터 불필요. OCD 의 pi-내장 대비 SQLite 세션·per-tool 권한 엔진·MCP 확장을 _기성품으로_ 제공. (단 OD/OCD 의 TS/Electron 스택과 언어 미스매치.)

---

## 축 1 비교표

| 후보 | ⭐stars | license | 세션 연속성 | 스트림 스키마 | 임베드 | 권한/샌드박스 | 적합도 |
|---|---|---|---|---|---|---|---|
| **pi** (earendil-works/pi) | 64.9k | MIT | 디스크 JSONL (+branch, resume id) | typed union NDJSON | ✅ npm 4종 | 없음(컨테이너 위임) | **상** |
| **Zed ACP** | 3.5k | Apache-2.0 | resume-id (spec) | JSON-RPC 2.0(`session/update`) | ✅ Rust/TS/Py/Java/Kt SDK | ✅ `request_permission` | **상(전략)** |
| **aider** | 46.6k | Apache-2.0 | 디스크 Markdown(resume-id X) | 없음(generator/stdout) | △ 비공식 Python API | git auto-commit | 하~중 |
| **continue.dev** | 34.3k | Apache-2.0 | 디스크 JSON, resume-id | typed union(`sessionUpdate`/`toolCallPartialOutput`) | ✅ `@continuedev/{core,sdk}` | policy + terminal-security | **상** |
| **open-webui** | 142.7k | NOASSERTION(브랜딩) | DB(sqlite/PG) | Socket.IO + SSE fallback | ❌ 모놀리식 | 외부 Jupyter, 승인 X | 하 |
| **LibreChat** | 39.7k | MIT | MongoDB | SSE(GraphEvents) | △ `@librechat/agents`만 | 외부 유료 API | 하~중 |
| **cody** (snapshot) | 3.8k | Apache-2.0 | node-localstorage KV | JSON-RPC stdio(webview 묻힘) | △ npm(archived) | 없음 | 하 |
| **goose** | 50.1k | Apache-2.0 | SQLite `sessions.db` | SSE `MessageEvent` + 네이티브 ACP | ✅ `goose-sdk` crate | ✅ per-tool engine | **상** |

---

## 축 1 단독 1픽 + 이유

**🥇 Zed ACP (agentclientprotocol/agent-client-protocol)** — 단, _프로토콜 레이어_ 로서.

이유: 내 제약의 핵심("기존 하네스 PATH 의 claude code/codex CLI 재사용")을 **유일하게 정통으로** 푼다. ACP 는 엔진이 아니라 와이어 계약이라 내 CLI 를 _교체하지 않고_ swappable 백엔드로 붙인다 — Gemini CLI(`--acp` 네이티브)·Codex CLI·Goose 가 이미 ACP 에이전트고 Claude Code 는 Zed SDK 어댑터로 ACP 화된다. (1) 표준 JSON-RPC 스키마(`session/new`·`session/prompt`·`session/update`)가 OD 의 ad-hoc `agents.ts` 를 대체, (2) `session/request_permission` 이 8 후보 중 가장 정식 권한 모델, (3) Rust/TS/Python SDK(`@agentclientprotocol/sdk` 0.29.0·crate 2.7M downloads, 어제 publish) 로 임베드. local-first·BYOK·Apache-2.0·archived No 전부 충족.

**보완 페어링**: ACP 는 transport 계약만 주므로, _실행 가능한 데몬 레퍼런스_ 가 필요하면 **goose**(`goosed` /reply SSE + 네이티브 ACP + per-tool 권한 + SQLite 세션)를 ACP 서버 측 구현체로 함께 본다. TS 하네스로 가볍게 시작이면 **continue.dev** 의 `IMessenger` + `cn serve` 가 "엔진 통째 + headless server" 차선책.

---

## 축 1 핵심 takeaway

**ACP(JSON-RPC 표준)를 브리지 계약으로 삼아 내 PATH 의 claude/codex CLI 를 swappable 백엔드로 붙이고, 실행 레퍼런스가 필요하면 goose(`goosed`+네이티브 ACP)·continue(`IMessenger`+`cn serve`)에서 데몬·권한·세션 구현을 lift 한다 — open-webui/LibreChat 은 완성 UI·SSE 스키마의 _참조_ 일 뿐 임베드 대상은 아니고, cody 는 archived dead 라 ACP 에 흡수된다.**
