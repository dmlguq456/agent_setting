# 축 3 — Hermes Agent 장기기억(long-term memory) 체계

> 대상: NousResearch **Hermes Agent** (오픈소스 self-improving AI agent, 2026-02-25 공개, MIT). 1차 소스(github.com/NousResearch/hermes-agent docs·source, plastic-labs/honcho) 우선. 조사일 2026-06-14.

---

## 0. 한눈 요약

Hermes 의 기억은 **3 층**이다 — (1) 시스템 프롬프트에 frozen snapshot 으로 박히는 **curated memory 파일**(MEMORY.md / USER.md), (2) 전 세션을 적재하는 **SQLite session archive**(`state.db`, FTS5 full-text + trigram), (3) optional 한 **외부 memory provider**(Honcho 등 9 종). 무엇을 기억으로 승격할지는 **에이전트 자신**이 정하고, **periodic nudge**(턴 카운터 기반의 self-directed 내부 프롬프트 + 비활성 기반 Curator)가 주기적으로 "지금까지를 돌아보고 persist 할 게 있나" 자문하게 만든다. recall 은 frozen 파일(상시) + `session_search` tool(on-demand) + provider prefetch(턴 전 background) 의 3 경로로 라우팅된다.

---

## 1. 메모리 아키텍처 전체상 (몇 층 · 무엇이 어디)

**claim**: Hermes 의 persistent 기억은 두 개의 built-in 파일 레이어 + SQLite session 레이어로 구성된다.
- **MEMORY.md** — 에이전트의 personal notes(environment facts, project conventions, lessons learned). **2,200 char limit (~800 tokens)**.
- **USER.md** — user profile(preferences, communication style). **1,375 char limit (~500 tokens)**.
- 두 파일 모두 `~/.hermes/memories/` 에 위치, **세션 시작 시 system prompt 에 "frozen snapshot" 으로 주입**.
- 세 번째 레이어 = SQLite `~/.hermes/state.db` (FTS5 full-text search) — 전 CLI·messaging 세션 적재, 과거 회상용.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md , https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- confidence: **high**

**claim**: 기억 / skill / session history / 파일의 구분 = 정보의 **수명·재사용 범위**로 갈린다.
- **항상 필요(every future conversation)** → MEMORY.md / USER.md (frozen snapshot).
- **특정 토픽에서만 유용** → session archive(state.db) 에 남고 `session_search` 로만 꺼냄.
- **재사용 가능한 절차(5+ tool call 복잡 작업)** → skill document(`~/.hermes/skills/`, Markdown). skill 은 Curator 가 `active→stale→archived` 로 lifecycle 관리.
- 근거: medium 분석(https://medium.com/@xpf6677/hermes-agent-memory-system-curated-memory-session-search-and-self-improvement-a84d2a9d5d01) + curator doc(https://hermes-agent.nousresearch.com/docs/user-guide/features/curator)
- confidence: **high** (3층 구분 = 1차 doc, skill lifecycle = 1차 doc)

### 레이어 비교표

| 레이어 | 저장 위치 | 크기/범위 | 주입 방식 | 수명 |
|---|---|---|---|---|
| MEMORY.md (agent notes) | `~/.hermes/memories/MEMORY.md` | 2,200 char | 세션 시작 frozen snapshot → system prompt | 영구(consolidate 전까지) |
| USER.md (user profile) | `~/.hermes/memories/USER.md` | 1,375 char | 세션 시작 frozen snapshot → system prompt | 영구 |
| session archive | `~/.hermes/state.db` (SQLite, WAL) | 전 세션·전 메시지 | `session_search` tool on-demand | 영구(아카이브) |
| skills | `~/.hermes/skills/*.md` | 절차 단위 | 관련 시 로드 | active→stale→archived (Curator) |
| external provider | Honcho 등(server/API) | 무제한(서버) | 턴 전 background prefetch → system prompt | 서버 관리 |

---

## 2. agent-curated memory + periodic nudges

**claim**: "에이전트가 스스로 큐레이팅" = write 결정의 주체가 **에이전트 자신**이며, 무엇을 승격할지 명시적 휴리스틱을 따른다.
- **저장(promote)**: user preferences·environment facts, project conventions·corrections, completed work·lessons learned, explicit user save requests.
- **skip**: trivial info, easily re-discoverable facts, raw data dumps, session ephemera, 이미 context 파일에 있는 정보.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md
- confidence: **high**

**claim**: write 는 `write_approval` 설정으로 게이팅된다.
- `write_approval: false` (default) = "write freely". `true` = approval 필요, background review write 는 `/memory pending` 으로 staged.
- 검토 명령: `/memory pending`, `/memory approve <id>`, `/memory reject <id>`, `/memory approval on/off`.
- memory tool actions = **add / replace / remove** (replace·remove 는 `old_text` substring matching). **read action 없음** — 기억은 system prompt 에 자동 등장.
- 근거: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- confidence: **high**

### periodic nudges — 무엇을·누구에게·언제

**claim**: nudge 는 **사용자가 아니라 에이전트 자신에게 보내는 internal system-level 프롬프트**다 — "지금까지 일어난 일을 돌아보고 persist 할 가치가 있는지 평가하라"는 self-directed 회고 신호.
- 근거: https://medium.com/@xpf6677/hermes-agent-memory-system-curated-memory-session-search-and-self-improvement-a84d2a9d5d01 (2차, 단 1차 doc 의 "background self-improvement review that runs after a turn" 와 정합)
- confidence: **medium** (방향성=자기 자신은 정합도 높음, 정확한 wording 은 2차)

**claim**: nudge 트리거는 **두 경로**다.
- **(a) 턴 카운터 기반 in-session nudge**: user 턴마다 `turns_since_memory` 증가, `turns_since_memory >= nudge_interval` 이면 background review 요청. (memory tool available + MemoryStore 존재 조건)
- **(b) 비활성 기반 Curator(skill 측)**: cron daemon 아니라 **inactivity check**. CLI 세션 시작 시 + gateway cron-ticker thread tick 마다, `interval_hours`(default **7일/168h**) 경과 AND `min_idle_hours`(default **2h**) idle 충족 시 발동. 산출물: `~/.hermes/logs/curator/{run.json, REPORT.md}`, telemetry `~/.hermes/skills/.usage.json`.
- 정확한 `nudge_interval` 턴 수치는 ❓미검증 (1차 doc 에 숫자 미노출).
- 근거: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator (Curator·inactivity·defaults = 1차) + medium(턴 카운터 메커니즘 = 2차)
- confidence: Curator 경로 **high** / 턴 카운터 경로 **medium**

**claim**: nudge 시 에이전트의 판단 기준 = "every future conversation 에 필요 → MEMORY.md/USER.md, 특정 토픽만 → session archive 에 잔류". 즉 nudge 는 승격(promote)뿐 아니라 **레이어 배치 결정**까지 수행.
- 근거: medium(2차) + memory doc 의 skip 기준과 정합
- confidence: **medium**

---

## 3. FTS5 cross-session recall (스키마·인덱싱·주입)

**claim**: 모든 CLI·messaging 세션은 `~/.hermes/state.db`(SQLite, **WAL 모드**)에 적재되고, `session_search` tool 이 SQLite **FTS5** 로 과거 전 대화를 full-text 검색한다 (~20ms FTS5 query). 트리거 = "did we discuss X last week?" 류.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/session-storage.md , memory.md
- confidence: **high**

### state.db 스키마 (1차 source — session-storage doc)

**테이블 구성** (schema_version = 11):
```
sessions              -- 세션 메타(source, user_id, model, 토큰 카운트, billing/cost, title, parent_session_id …)
messages              -- 전 메시지(role, content, tool_calls, tool_name, reasoning, timestamp, token_count …)
messages_fts          -- FTS5 virtual (content=messages, external content mode, 기본 unicode61 tokenizer)
messages_fts_trigram  -- FTS5 virtual (trigram tokenizer — CJK/substring)
state_meta            -- key/value 메타 (key TEXT PRIMARY KEY, value TEXT)
schema_version        -- 마이그레이션 버전 (version INTEGER)
```

**핵심 DDL (인용)**:
```sql
-- messages_fts: external content mode (messages 를 외부 content 로 참조, 중복 저장 회피)
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content, content=messages, content_rowid=id
);

-- trigram: 3-byte overlapping → 어떤 script(CJK/Thai)든 substring 검색 native
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts_trigram USING fts5(
    content, tokenize='trigram'
);

-- 동기화: INSERT/UPDATE/DELETE 3 trigger 로 messages → messages_fts 자동 싱크
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```
- messages index: `idx_messages_session ON messages(session_id, timestamp)`.
- sessions index: source / parent_session_id / started_at DESC / title(unique, NULL 허용).
- write 안정화: 1s busy timeout, app-level retry(20–150ms jitter, max 15회), **WAL checkpoint 50 write 마다 PASSIVE**.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/session-storage.md , https://github.com/NousResearch/hermes-agent/blob/main/hermes_state.py
- confidence: **high** (DDL 다수 1차 source 인용)

**claim**: `search_messages()` 는 FTS5 쿼리 문법(keyword·quoted phrase·AND/OR/NOT·prefix `*`)을 지원, 결과는 `>>>match<<<` 마커 snippet + 주변 context + 세션 메타. unmatched quote·hyphen·dangling operator 입력 sanitize.
- 단 **bm25 ranking 명시·이중 테이블(unicode61 vs trigram) 결합 로직**은 visible doc 에 미노출 → ❓미검증(코드 후반 cut off).
- 근거: session-storage doc
- confidence: ranking 구체값 **low** / 검색 인터페이스 **high**

### recall → context 주입 흐름 (ASCII)

```
세션 시작 ─────────────────────────────────────────────
  ~/.hermes/memories/MEMORY.md ─┐
  ~/.hermes/memories/USER.md  ──┼──► frozen snapshot ──► system prompt (상시, prefix-cache 보존)
                                │     헤더: "[67% — 1,474/2,200 chars]"
  provider(Honcho 등) prefetch ─┘     (턴 전 background, non-blocking)

세션 중 "지난주 X 논의했나?" ──► session_search tool ──► FTS5(messages_fts[+trigram])
                                                        └► snippet(>>>match<<<)+세션메타 ──► context 주입

세션 중 write ──► MEMORY.md/USER.md 즉시 디스크 반영
              └► 단 "다음 세션 시작 전엔 system prompt 에 안 보임" (frozen 특성)
```
- claim: 세션 중 memory 변경은 디스크엔 즉시, **system prompt 엔 다음 세션부터** 반영 (frozen snapshot 이라). prefix cache 성능 보존 목적.
- 근거: memory.md
- confidence: **high**

---

## 4. Honcho dialectic user modeling

**claim**: Honcho 는 **Plastic Labs**(github.com/**plastic-labs/honcho**) 의 "AI-native memory backend" — "memory infrastructure for building stateful agents that understand changing people … over time". Hermes 의 built-in 기억 **위에** dialectic reasoning + deep user modeling 을 얹는다.
- 정체: **FastAPI server**(managed `api.honcho.dev` 또는 self-host) + Python/TS SDK. Hermes 와는 **외부 서비스**로 통합 — `HONCHO_API_KEY` 환경변수, honcho.dev 에서 API key 발급. Memory Providers plugin system 의 unified interface 를 통해 연결.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/honcho.md , https://github.com/plastic-labs/honcho
- confidence: **high**

**claim**: **dialectic user modeling** = 대화 "후" 비동기 reasoning 으로 사용자 모델(preferences·communication style·goals·patterns)을 계속 갱신하는 방식.
- **Cold/Warm prompting**: dialectic 이 두 전략을 자동 선택 — 신규 user 엔 general "Who is this person?", 재방문 user 엔 session-scoped "이 user 에 대해 지금 가장 관련된 context 는?".
- **Multi-pass reasoning**: `dialecticDepth > 1` 이면 여러 pass — initial assessment → self-audit(gap 식별) → reconciliation(모순 점검). pass 별 proportional reasoning level(초기 가볍게, main pass 는 base).
- **Automatic updates**: `dialecticCadence` 가 제어하는 주기로, 대화 턴 후 Honcho 가 exchange 를 분석해 user insight 를 도출·누적.
- Honcho 내부적으로 `(observer, observed)` peer pair 키의 vector-embedded document 로 representation 저장, background derivation task 로 갱신 → Conclusions API·peer card·chat endpoint 로 surface.
- 근거: honcho.md(Hermes 측) + plastic-labs/honcho(Honcho 측)
- confidence: **high** (Hermes 통합 wording = 1차 / "theory of mind" 정의 자체는 Honcho README 에서 명시 약함 → 그 라벨은 medium)

**claim**: Honcho 의 5 tool —
| tool | 동작 |
|---|---|
| `honcho_profile` | peer card 읽기/갱신 (`card` = facts list 전달 시 update, 생략 시 read) |
| `honcho_search` | context semantic search — raw excerpt, LLM synthesis 없음 |
| `honcho_context` | full session context — summary · representation · card · recent messages |
| `honcho_reasoning` | Honcho LLM 의 synthesized answer (`reasoning_level` 로 depth 제어) |
| `honcho_conclude` | conclusion 생성/삭제 (`conclusion` 생성, `delete_id` 삭제) |
- 근거: honcho.md
- confidence: **high**

**built-in vs Honcho 차이** (1차 표):
| 항목 | built-in | Honcho |
|---|---|---|
| persistence | file(MEMORY/USER.md) | server-side API |
| user profile | 수동 agent curation | 자동 dialectic reasoning |
| session summary | 없음 | session-scoped context 주입 |
| multi-agent isolation | 없음 | per-peer profile 분리 |
| search | FTS5 session search | conclusion 대상 semantic search |

---

## 5. 메모리 수명주기 (write / prune / recall routing / 중복·stale)

**write 트리거**:
- (a) in-session: 위 §2 의 학습 이벤트(correction·preference·convention 발견)를 에이전트가 감지 → memory tool `add`.
- (b) periodic: 턴 카운터(`turns_since_memory >= nudge_interval`) background review.
- (c) explicit: user 의 명시적 save 요청.
- confidence: **high** (a,c) / **medium** (b 수치)

**prune / forget / consolidation**:
- **명시적 시간 기반 prune·forget 메커니즘은 메모리 파일에 없음** — 대신 **capacity-driven consolidation**. memory 가 한도(2,200/1,375 char)에 닿으면 memory tool 이 **error 반환**, 에이전트가 **같은 턴 안에** overlapping 병합 또는 stale 제거 후 재시도해야 함(silent drop 아님).
- skill 쪽은 별도 — Curator 가 usage telemetry 로 `active→stale→archived` 자동 전이(이게 사실상 skill 의 forget).
- 근거: memory.md, memory(doc), curator doc
- confidence: **high**

**recall routing (언제 어떤 기억)**:
- 상시 필요 → frozen MEMORY/USER.md (system prompt, 비용 0 회상).
- 과거 specifics → `session_search`(FTS5) on-demand.
- provider 활성 시 → 턴 전 background prefetch 로 관련 memory 미리 주입(non-blocking).
- confidence: **high**

**중복 · stale**:
- **중복**: memory 시스템이 **exact duplicate 자동 거부**. 추가로 memory content 는 injection/exfiltration 패턴 스캔.
- **stale**: 자동 만료 없음 — capacity 압박 시 consolidation 으로 수동 정리(에이전트 판단). provider(Holographic) 류는 `contradict` action 으로 모순 fact 자동 탐지 옵션 존재.
- 근거: memory.md, memory-providers.md
- confidence: **high**

---

## 부록 — external memory provider 9 종 (FTS5 비교 참고)

Honcho 외에도 provider 교체 가능(unified interface, 턴 전 background prefetch):
OpenViking(ByteDance, filesystem-style hierarchy) · Mem0(server-side LLM fact extraction + dedup) · Hindsight(knowledge graph + entity resolution) · **Holographic(local SQLite + FTS5 + trust scoring + HRR; `fact_store` 9 actions: add/search/probe/related/reason/contradict/update/remove/list; DB `$HERMES_HOME/memory_store.db`)** · RetainDB(Vector+BM25+Rerank) · ByteRover(`brv` CLI hierarchical tree) · Supermemory · Memori.
- 근거: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory-providers.md
- confidence: **high**

---

## 출처 ledger

| # | 출처 | URL | 신뢰도 | 비고 |
|---|---|---|---|---|
| 1 | Hermes docs — Persistent Memory (memory.md) | https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md | 1차 high | 2층 파일·char limit·curation 기준·중복거부 |
| 2 | Hermes docs site — Persistent Memory | https://hermes-agent.nousresearch.com/docs/user-guide/features/memory | 1차 high | write_approval·/memory 명령·frozen snapshot |
| 3 | Hermes docs — Memory Providers | https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory-providers.md | 1차 high | 9 provider·Holographic FTS5 |
| 4 | Hermes docs — Honcho | https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/honcho.md | 1차 high | dialectic·5 tool·built-in 비교표 |
| 5 | Hermes docs — Session Storage (dev) | https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/session-storage.md | 1차 high | state.db 전 DDL·FTS5 trigger·WAL |
| 6 | Hermes source — hermes_state.py | https://github.com/NousResearch/hermes-agent/blob/main/hermes_state.py | 1차 high | trigram DDL·state_meta·schema_version |
| 7 | Hermes docs — Curator | https://hermes-agent.nousresearch.com/docs/user-guide/features/curator | 1차 high | inactivity check·interval_hours 7d·min_idle_hours 2h |
| 8 | Plastic Labs — Honcho repo | https://github.com/plastic-labs/honcho | 1차 high | Honcho 정체·FastAPI·peer pair representation |
| 9 | Medium — Hermes Memory System (Timi) | https://medium.com/@xpf6677/hermes-agent-memory-system-curated-memory-session-search-and-self-improvement-a84d2a9d5d01 | 2차 medium | 턴 카운터 nudge 메커니즘(1차 미노출 보완) |
| 10 | DEV/NxCode 등 개관 | https://dev.to/wonderlab/...-4ale · https://www.nxcode.io/... | 2차/저신뢰 | 개관·40% faster 벤치(단독근거 X) |

### ❓미검증 항목
- `nudge_interval` 의 정확한 턴 수치 (1차 doc 미노출).
- `session_search` 의 bm25 ranking 적용 여부 및 messages_fts(unicode61) vs messages_fts_trigram 결합 로직 (hermes_state.py 후반 cut off).
- Honcho "theory of mind" 라벨 — Hermes 측은 "dialectic" 으로 기술, Honcho README 에 ToM 명시는 약함.
