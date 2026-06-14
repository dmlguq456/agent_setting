# 03 — 장기기억(long-term memory) 심층

> 근거: `cards/axis3_memory.md` (1차 = hermes-agent docs·`hermes_state.py` source + plastic-labs/honcho). 핵심 보고서.

---

## 0. 한눈 요약 — Hermes 기억은 3층 + optional provider

(1) system prompt 에 frozen snapshot 으로 박히는 **curated memory 파일**(MEMORY.md/USER.md), (2) 전 세션을 적재하는 **SQLite session archive**(`state.db`, FTS5 full-text + trigram), (3) optional **외부 provider**(Honcho 등 9종). 무엇을 승격할지는 **에이전트 자신**이 정하고, **periodic nudge**(턴 카운터 + 비활성 Curator)가 주기적으로 자기회고를 유도한다. recall 은 frozen(상시) + `session_search`(on-demand) + provider prefetch(background) 3 경로.

---

## 1. 3층 아키텍처

| 레이어 | 위치 | 크기/범위 | 주입 방식 | 수명 |
|---|---|---|---|---|
| MEMORY.md (agent notes) | `~/.hermes/memories/MEMORY.md` | 2,200 char (~800 tok) | 세션 시작 frozen snapshot → system prompt | 영구(consolidate 전) |
| USER.md (user profile) | `~/.hermes/memories/USER.md` | 1,375 char (~500 tok) | 세션 시작 frozen snapshot → system prompt | 영구 |
| session archive | `~/.hermes/state.db` (SQLite WAL) | 전 세션·전 메시지 | `session_search` tool on-demand | 영구(아카이브) |
| skills | `~/.hermes/skills/*.md` | 절차 단위 | 관련 시 로드 | active→stale→archived (Curator) |
| external provider | Honcho 등 server/API | 무제한 | 턴 전 background prefetch | 서버 관리 |

**구분 기준 = 정보의 수명·재사용 범위**: every future conversation → MEMORY/USER.md / 특정 토픽만 → session archive(`session_search`) / 재사용 절차 → skill. (confidence: high — 3층 구분·skill lifecycle 모두 1차 doc)

---

## 2. agent-curated write + write_approval 게이트

**claim**: write 결정 주체는 에이전트 자신, 명시 휴리스틱 따름. (confidence: high)

| promote (저장) | skip |
|---|---|
| user preferences·environment facts | trivial info |
| project conventions·corrections | easily re-discoverable facts |
| completed work·lessons learned | raw data dumps |
| explicit user save requests | session ephemera, 이미 context 파일에 있는 것 |

**write_approval 게이트** (confidence: high):
- `false`(default) = write freely. `true` = approval 필요, background review write 는 `/memory pending` staged.
- 명령: `/memory pending` · `approve <id>` · `reject <id>` · `approval on/off`.
- memory tool actions = **add / replace / remove** (replace·remove 는 `old_text` substring matching). **read action 없음** — 기억은 system prompt 에 자동 등장.

> 우리 이식 후보 T5(품질 휴리스틱)·write_approval 류 게이트의 1차 근거.

---

## 3. periodic nudge = 자기회고

**claim**: nudge 는 사용자가 아니라 **에이전트 자신에게 보내는 internal system-level 프롬프트** — "지금까지를 돌아보고 persist 할 가치가 있나 평가하라". (confidence: medium — 방향성은 1차 review 진술과 정합, 정확 wording 은 2차)

**두 트리거 경로**:
- **(a) 턴 카운터 in-session**: user 턴마다 `turns_since_memory`++, `>= nudge_interval` 이면 background review. (confidence: medium — 정확 턴 수치 ❓ 1차 미노출)
- **(b) 비활성 Curator(skill 측)**: inactivity check — `interval_hours`(7일) AND `min_idle_hours`(2h). (confidence: high)

nudge 는 승격뿐 아니라 **레이어 배치 결정**(MEMORY/USER vs session archive)까지 수행. (confidence: medium)

> 우리 이식 후보 T4(periodic self-review nudge)의 1차 근거.

---

## 4. FTS5 cross-session recall (핵심 차별점)

**claim**: 모든 세션이 `state.db`(SQLite WAL)에 적재, `session_search` tool 이 FTS5 로 과거 전 대화 full-text 검색(~20ms). 트리거 = "did we discuss X last week?". (confidence: high)

### state.db 스키마 (schema_version=11)

```
sessions              -- 메타(source,user_id,model,token,cost,title,parent_session_id)
messages              -- 전 메시지(role,content,tool_calls,reasoning,timestamp,token_count)
messages_fts          -- FTS5 virtual (content=messages, external content, unicode61)
messages_fts_trigram  -- FTS5 virtual (trigram — CJK/substring)
state_meta            -- key/value
schema_version        -- 마이그레이션 버전
```

핵심 DDL (1차 인용):
```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(content, content=messages, content_rowid=id);
CREATE VIRTUAL TABLE messages_fts_trigram USING fts5(content, tokenize='trigram');
-- INSERT/UPDATE/DELETE 3 trigger 로 messages → messages_fts 자동 싱크
```
- index: `idx_messages_session ON messages(session_id, timestamp)`.
- write 안정화: 1s busy timeout, app-level retry(20–150ms jitter, max 15회), WAL checkpoint 50 write 마다 PASSIVE.

**검색 인터페이스**: `search_messages()` 가 FTS5 문법(keyword·quoted phrase·AND/OR/NOT·prefix `*`) 지원, 결과 = `>>>match<<<` snippet + 주변 context + 세션 메타. unmatched quote/hyphen sanitize. (confidence: high). ❓ bm25 ranking·이중 테이블 결합 로직은 doc 미노출(low).

### recall → context 주입 흐름

```
세션 시작 ─ MEMORY.md/USER.md ─► frozen snapshot ─► system prompt (상시, prefix-cache)
            provider prefetch ─┘  (턴 전 background, non-blocking)
세션 중 "지난주 X?" ─► session_search ─► FTS5(messages_fts[+trigram]) ─► snippet+메타 ─► context
세션 중 write ─► MEMORY/USER.md 즉시 디스크 (단 system prompt 엔 다음 세션부터, frozen 특성)
```

> **이 FTS5 자동 recall 이 우리와의 최대 메모리 갭** — 우리 auto-memory 는 세션 시작 주입 + 수동 recall 뿐, 과거 세션 전문(全文)을 자동 검색하는 층이 없다.

---

## 5. Honcho dialectic user modeling (외부 provider)

**claim (C3 정정)**: Honcho = **Plastic Labs**(`plastic-labs/honcho`)의 AI-native memory backend, **FastAPI server**(managed `api.honcho.dev` 또는 self-host) + SDK. Hermes 와는 **외부 서비스** 통합 — `HONCHO_API_KEY`, Memory Providers plugin 의 unified interface. (confidence: high)

**dialectic user modeling** = 대화 *후* 비동기 reasoning 으로 user model(preferences·style·goals·patterns) 갱신. (confidence: high)
- **Cold/Warm prompting**: 신규 user 엔 general "Who is this person?", 재방문엔 session-scoped.
- **Multi-pass**: `dialecticDepth>1` 이면 initial → self-audit → reconciliation.
- **Automatic updates**: `dialecticCadence` 주기로 exchange 분석 → user insight 누적.
- 내부: `(observer, observed)` peer pair 키의 vector-embedded document, background derivation.

5 tool: `honcho_profile`(peer card r/w) · `honcho_search`(semantic, synthesis 없음) · `honcho_context`(full session) · `honcho_reasoning`(synthesized answer) · `honcho_conclude`(conclusion 생성/삭제).

built-in vs Honcho (1차 표): user profile 이 *수동 curation*(built-in) vs *자동 dialectic*(Honcho), search 가 FTS5(built-in) vs semantic(Honcho), multi-agent isolation 이 없음(built-in) vs per-peer(Honcho).

> Honcho 의 *자동 dialectic user modeling* 은 우리 user_profile(analyze-user 로 *수동* 갱신)의 자동화 버전 — 단 외부 FastAPI 의존이라 직접 이식은 부적합, *개념*(대화 후 비동기 프로필 갱신)만 차용 가능.

---

## 6. 수명주기 — prune / consolidation / 중복

- **시간 기반 prune·forget 없음** (memory 파일). 대신 **capacity-driven consolidation** — 한도(2,200/1,375 char) 도달 시 memory tool 이 **error 반환**, 에이전트가 같은 턴에 overlapping 병합/stale 제거 후 재시도(silent drop 아님). (confidence: high)
- skill 쪽은 별도 — Curator 가 usage telemetry 로 active→stale→archived 자동 전이(사실상 skill 의 forget).
- **중복**: exact duplicate 자동 거부 + injection/exfiltration 패턴 스캔. **stale**: 자동 만료 없음(capacity 압박 시 수동 consolidation). (confidence: high)

부록 — provider 9종 중 **Holographic** = local SQLite + FTS5 + trust scoring + HRR, `fact_store` 9 actions(add/search/probe/related/reason/**contradict**/update/remove/list) — 모순 fact 자동 탐지 옵션 보유.

---

## 7. ★ 우리 3층 메모리와 1:1 대조

| Hermes 메커니즘 | 우리 대응물 | 누가 앞섰나 | 근거 |
|---|---|---|---|
| MEMORY.md/USER.md frozen snapshot system prompt 주입 | **auto-memory** `projects/<cwd>/memory/*.md` (frontmatter type, MEMORY.md 인덱스, [[link]], 세션 시작 자동 주입) | **동등** (둘 다 세션 시작 주입) | axis3 §1 vs CLAUDE.md 메모리 정책 |
| char limit + capacity-driven consolidation (error on full) | 명시적 capacity 게이트 **없음** (자유 누적) | Hermes 앞섬 (용량 규율) | axis3 §6 vs auto-memory |
| **FTS5 cross-session recall** (`session_search`, 전 세션 full-text, ~20ms) | **세션 시작 주입 + 수동 recall 만** — 과거 세션 전문 자동 검색 층 **없음** | **Hermes 앞섬 (큰 갭)** | axis3 §4 vs auto-memory |
| write_approval 게이트 + promote/skip 휴리스틱 | promote/skip 가이드는 instruction 에 서술, 코드 게이트는 없음 | Hermes 앞섬 (게이트 메커니즘) | axis3 §2 vs CLAUDE.md |
| periodic nudge = 자기회고(턴 카운터 + Curator) | post-it nudge (context 50%+/wind-down 시 *제안*), 자동 턴 카운터 **없음** | Hermes 앞섬 (자동 트리거) | axis3 §3 vs CLAUDE.md §2 |
| Honcho 자동 dialectic user modeling (외부) | **user_profile** 6종 (analyze-user 로 *수동* 갱신, cross-project) | trade-off (우리=수동·검증가능, Honcho=자동·외부의존) | axis3 §5 vs user_profile/ |
| 행동양식도 memory 에 쌓을 수 있음 | **행동양식은 memory 아니라 원칙 문서**(CLAUDE.md/CONVENTIONS/SKILL)에 — 단일 출처 분리 정책 | **우리 앞섬** (관심사 분리·버전관리) | CLAUDE.md 운영 정책 |
| 3층 단일 시스템(파일+SQLite+provider) | **3층 분리 시스템**(auto-memory per-cwd · post-it self-pruning nudge · user_profile cross-project) | 동등 (다른 분할축) | CLAUDE.md vs axis3 |

> **drift note (live 관찰)**: 브리프 digest 는 `.claude` 설정 repo cwd 만 보고 "auto-memory 가 빈 레이어"인 듯 표현했으나, live 재집계 결과 전역으로는 **메모리 dir 15개 / MEMORY.md 인덱스 14개 / 메모리 .md 파일 58개**가 존재(예: `NN-SE-UD-KWS/memory/MEMORY.md` = user_role·project·feedback 3 엔트리). 빈 레이어로 보였던 건 `.claude` 설정 repo cwd 자체(`projects/-home-Uihyeop--claude/memory/`)뿐이고, auto-memory 는 per-cwd 라 config repo cwd 에서 보면 비어 있을 뿐 실제 작업 프로젝트 cwd 들엔 채워져 있다. 정확한 한정 = **"전역으로는 산재하나 cwd 마다 비대칭이고, 새 cwd 는 매번 빈 인덱스로 시작·인덱스 성숙도가 낮다"** — 즉 *얇고 cwd-국소적*. FTS5류 cross-cwd/cross-session 자동 검색이 없다는 갭은 그대로 유효. (CLAUDE.md §1 근거 우선 — live 코드 우선, digest drift 명시)

**Takeaway**: 메모리 축에서 Hermes 의 결정적 우위는 **FTS5 자동 cross-session recall** 하나 — 우리는 주입+수동 recall 에 인덱스마저 얇다. 반대로 우리는 *행동양식/원칙의 단일 출처 분리*와 *user_profile 의 검증가능한 수동 큐레이션*에서 앞선다. 이식 1순위는 명확히 "auto-memory 에 자동 recall 층 + 인덱스 채우기"다.
