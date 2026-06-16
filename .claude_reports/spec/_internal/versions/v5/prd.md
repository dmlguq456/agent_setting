# Unified Memory System — PRD

> mode: **library + cli** · 작성 2026-06-15 · v3(DB화·저장소분리) · v4(결정론-우선 원칙·Hermes port) · **v5 개정 2026-06-15** (Option 2 — user_profile·post-it 파일 메커니즘 제거, DB 단일 store, sub-agent DB 직접 읽기)
> 입력: `research/hermes-agent/{03_memory_system,04_benchmark_gap,07_security,08_source_grounded}.md` · 기존 `tools/memory/*` · `skills/{post-it,analyze-user}/` · `user_profile/`
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`).
> **방향(사용자 확정 2026-06-15)**: "대공사 OK, 보수적 현상유지 X, 제대로·깔끔·근본부터." Hermes 메모리 적극 결합 + 중복 cut + DB-SoT.

## 0. 한 줄

흩어진 3개 기억(post-it 단기 · auto-memory 장기 · user_profile 전역)을 **하나의 SQLite store(`memory.db`) + tier 모델**로 통합. 진실원천=DB, git=`dump.jsonl` 텍스트 mirror, 전용 private repo `claude-memory`. v4에서 **profile을 진짜 완전 통합**하고 **Hermes 잔여 port 2종**을 결정론-우선으로 붙인다.

## 0.5 설계 원칙 — 결정론 우선 (deterministic-first) ★ cross-cutting

> 2026-06-15 사용자 핵심 원칙. 본 시스템뿐 아니라 세팅 전반의 설계 tenet — DESIGN_PRINCIPLES.md에도 격상.

**결정론적·소프트웨어로 처리 가능한 요소는 가능한 한 코드(hook·script·gate·DB)로 대체해, 에이전트가 _생각_ 할 영역을 최소화한다.** 그래야 에이전트가 진짜 판단이 필요한 자리에 집중해 더 똑똑·신뢰성 있게 동작한다.

- **왜**: 매 agent 판단은 비결정·실수 가능·토큰 비용. 결정론 기계화는 무료·정확·재현가능.
- **적용 규칙**: 새 기능·정책 설계 시 *"이걸 코드로 강제·자동화할 수 있나?"* 를 **먼저** 묻는다. 가능하면 instruction(에이전트 판단)이 아니라 메커니즘(hook/script/gate/DB 제약)으로. agent judgment는 결정론이 불가능한 자리의 _fallback_.
- **본 시스템 내 발현**: write 게이트·dedup·injection 마스킹·만료·dedup-flag·turn-counter·export/import·projection은 전부 **코드**(에이전트 판단 아님). 에이전트는 "무엇을 기억할 가치가 있나"의 의미 판단만. v4의 Cluster B도 이 원칙으로 설계 — nudge는 instruction이 아니라 hook 카운터.

## 1. 통합 모델 — 저장소 1개(DB), tier × scope × type

| tier (수명) | scope | 무엇 | 흡수 전 | lifecycle |
|---|---|---|---|---|
| **working** (단기) | project | 진행중 작업·결정·hint·스레드 | post-it | 자동 만료(stale N일)/졸업 |
| **durable** (장기) | project | 프로젝트 사실·교훈·교정·컨벤션 | auto-memory (Claude 내장) | 영구 + consolidate |
| **durable** (장기) | global | cross-project 선호·패턴·**profile** | user_profile | 영구 + consolidate |

"하나로 묶는다" = 한 DB·도구·스키마. `tier/scope/type` 컬럼이 *주입 행동*을 가른다(profile=항상 / working=현 cwd / durable/project=현 프로젝트). 컬럼 = 결정론적 필터(§0.5).

## 2. 설계 결정 (locked, v3에서 유지) — D1~D9

- **D1**: SoT = 로컬 `memory.db`(SQLite WAL, FTS5 내장). git = `dump.jsonl`(결정론적 텍스트 mirror, 레코드당 1줄·id 정렬·sort_keys). 바이너리 .db 비추적. 복원 = `mem import`.
- **D2**: 위치↔스코프 분리 — 단일 DB + `cwd_origin` 컬럼 (필터).
- **D3 → Cluster A로 격상** (§4): user_profile 통합 깊이.
- **D4**: 자동 write (기억 한정, 사람 게이트 없음, 품질필터·dedup·injection 가드만 — 전부 코드).
- **D5**: lifecycle — working 자동만료/졸업, durable consolidate. gc만 사람 게이트.
- **D6**: 자체 하네스 — SessionStart `mem inject --hook` + SessionEnd `mem sync`.
- **D7 → Cluster A로 격상** (§4): 통합 깊이.
- **D8**: 보안 — injection 패턴·secret 마스킹 (코드). 메모리는 데이터로만.
- **D9**: 저장소 분리 — 전용 private repo `claude-memory`, config repo `memory/` gitignore + 이력 filter-repo 제거.

## 3. 잘라낸 것 (v3 완료)
markdown 186 SoT → DB 1개 + dump.jsonl · `.index.db` 파생색인 → DB 내장 FTS5 · post-it 파일/파싱 → working 레코드 · 3중 분산 위치 → 1 store. (✅ 200 레코드 무손실 이주 완료.)

## 4. Cluster A — 파일 메커니즘 제거, DB 단일 store 완성 (v5, Option 2)

> **v4(Option 1) → v5(Option 2) 전환** (사용자 결정 2026-06-15): v4는 "md를 DB→generated view로 유지(sub-agent 경로 Read 보존)"였으나, 사용자 = *"그냥 sub-agent도 DB 읽게 하면 됨"* + *"user_profile·post-it 별도 파일이 왜 있냐 — 그냥 다 DB"*. → **별도 파일 메커니즘 자체를 제거**, DB가 **유일 SoT·유일 읽기 소스**. ("대공사 OK, 보수적 X" 원칙대로 — Option 1의 유일 근거였던 'agent rewire 회피'를 사용자가 명시 waive.)

### 4.1 user_profile 파일 제거 (sub-agent가 DB 직접 읽기)
- DB `type=profile` 레코드가 **유일 SoT**. `user_profile/` 디렉토리 **제거**.
- **sub-agent가 DB를 직접 읽는다**: 에이전트 정의(`agents/*.md`·`agent-modes/*.md`) + CLAUDE.md 도메인 트리거의 `Read ~/.claude/user_profile/0X.md` → **`mem profile <aspect>`** (DB가 결정론적으로 그 aspect body 반환)로 교체.
- `analyze-user`는 **DB에 authoring** (aspect별 분석을 DB 레코드로 종단 write). curated·adversarial QA 그대로 — 저장 위치만 DB. (Option 1의 A2 projection wiring 불필요 — 파일이 없으니 동기 로직 자체 소멸, §0.5 단순화.)
- 매트릭스(어느 agent가 어느 aspect 필요)는 *문서*로 유지, 소스는 DB.
- 사람 열람은 on-demand `mem export --target profile`(gitignored 캐시), **SoT 아님**.

### 4.2 post-it 파일 제거
- 내용은 이미 DB working tier(127 레코드 이주 완료). 세션 주입은 이미 `mem inject`가 DB working에서 수행 → **post-it.md는 이중 redundant**(내용도 DB, 주입도 DB).
- post-it.md 파일(레지스트리 4개) **제거**, CLAUDE.md "세션 시작 post-it.md Read" 도메인 트리거 **제거**(mem inject가 대체).
- `/post-it`은 **DB에 쓰는 thin alias 유지**(D-2 근육기억) — project scope→`working/project`, user scope→`durable/global` profile-인접. `register-postit`·`.postit-roots` 레지스트리는 폐기(파일 없음).

### 4.3 결과 — 파일 메커니즘 0
| | 읽기 | 쓰기 |
|---|---|---|
| 세션 주입 | `mem inject` (DB working+durable+profile) | — |
| sub-agent | `mem profile`/`mem recall` (DB 직접) | — |
| 사람·하네스 | (on-demand `mem export`) | analyze-user·`/post-it`·auto-memory → **전부 DB** |

`user_profile/`·`post-it.md` 별도 파일 없음. §0.5 결정론-우선과 정합 — 파일↔DB 동기 로직이 통째로 사라져 단순화·드리프트 0. **트레이드오프**: profile cold-start corpus의 deliberate seed는 여전히 사람(§Non-goals — 정체성 모델). steady-state drift 자동화는 Cluster B 연계.

## 5. Cluster B — Hermes 잔여 port (v4 신규, 08_source_grounded 검증 근거)

> **08 결론**: memory.db 전환으로 03이 지목한 "FTS5 cross-session recall = Hermes 결정적 단일 우위" 갭은 **사실상 닫힘** (우리=unicode61 항상+CJK시 trigram UNION+explicit bm25, mixed-script에 Hermes의 3-way 상호배타 라우팅보다 강함). promote/skip 게이트 갭은 *환상*(양쪽 다 프로즈). **남은 진짜 port는 둘**, 둘 다 §0.5 결정론-우선으로 설계.

- **B1 — session_search 자율 turn-invocation 강화**: 현 `mem recall` CLI + CLAUDE.md instruction은 있으나 *반사적 습관*이 약함(에이전트 판단 의존). 결정론 강화 방향: (a) 트리거 조건을 instruction에 더 또렷이(어떤 발화 패턴에서 recall 의무), (b) 가능하면 **관련 메모리 사전주입 자동화** — "과거 X 논의?" 류 신호를 hook/heuristic이 감지해 recall 결과를 컨텍스트에 미리 붙임(에이전트가 "recall할까" 판단하는 단계 제거). 완전 결정론 불가 부분만 instruction.
- **B2 — 자동 turn-counter 자기회고** (결정론 핵심 발현): Hermes `nudge_interval=10`턴(turn_context.py:191-215, memory write 시 카운터 리셋 → background review fork)의 우리식 등가물. **우리 모델 = `UserPromptSubmit` hook에 결정론적 turn 카운터** — N프롬프트마다 promote/회고 nudge 자동 발사, memory write 시 리셋. 현 event기반 context-nudge(CLAUDE.md §2 context50%/wind-down)를 **turn기반 결정론 트리거로 보강·통합**. "언제 회고할지"를 에이전트 판단에서 hook 카운터로 이전(§0.5).
- 둘 다 Claude Code hook/CLI 모델 제약 반영 (Hermes의 agent-runtime hook과 다름 — 우리는 SessionStart/SessionEnd/UserPromptSubmit hook + Bash CLI).

## [library] 공개 API (v3 + v4 추가)
```
mem_write / mem_recall / mem_index_rebuild / mem_inject / mem_sync / mem_export(dump|profile) / mem_import / mem_migrate / mem_lifecycle / mem_project
+ (B2) turn-counter state (hook이 갱신, mem이 읽어 nudge 판정)
```

## [cli] `mem` 명령
v3 명령 + **v5 신규 `mem profile <aspect>`** (DB type=profile 레코드의 body를 결정론적으로 출력 — sub-agent·CLAUDE.md 트리거의 user_profile 파일 Read 대체). `export --target profile`은 on-demand 사람 열람 캐시용으로만(SoT 아님, sync/analyze-user 자동 wiring 불필요 — 파일 없음). `register-postit`·`.postit-roots`는 **폐기**(post-it.md 파일 제거). B2 turn-counter는 hook+state.

## 데이터 모델
v3 그대로 (`records` 12컬럼 + `records_fts` FTS5 + trigram 보조 + `idx_records_scope`; `dump.jsonl` 결정론적 export). profile = type=profile 레코드(body=aspect 전문), source=`user-profile:<stem>` (A2 파일명 도출 근거).

## Non-goals
- 외부 메모리 서비스(Honcho/Turso/libSQL 원격) — **로컬 only**.
- **profile cold-start 자동화** — 정체성 corpus의 deliberate seed는 사람이(garbage-in·consent 경계). 단 steady-state drift는 자동(B 연계).
- 세팅·원칙 자동 변경 — 기억만 자동.

## 확정 결정 (사용자 lock 2026-06-15)
- v3: D-1~D-7 (삭제정책·post-it alias·user_profile view·hook·SoT=SQLite·저장소분리·통합깊이).
- **v4 신규**:
  - **D-8 (결정론 우선)**: 결정론·SW 가능 요소는 코드로 대체, agent 판단 최소화 (§0.5, cross-cutting).
  - **D-9 (파일 메커니즘 제거, Option 2)**: user_profile/·post-it.md 별도 파일 제거, DB가 유일 SoT·유일 읽기 소스. sub-agent는 `mem profile`/`mem recall`로 DB 직접 읽기. analyze-user·/post-it DB authoring. (§4)
  - **D-10 (Hermes 잔여 port)**: session_search 자율호출 + turn-counter 자기회고, 둘 다 결정론-우선 (§5).

## Next (구현 순서 — autopilot-code, 본 v5 입력)
1. **Cluster A (파일 메커니즘 제거, Option 2)** 먼저 — 사용자 지적 incoherence 해소:
   - mem.py에 `mem profile <aspect>` 추가 (DB→aspect body 출력).
   - sub-agent 정의(`agents/*.md`·`agent-modes/*.md`) + CLAUDE.md 도메인 트리거: `Read user_profile/0X.md` → `mem profile 0X` 교체.
   - analyze-user를 DB authoring으로 (aspect→DB 레코드).
   - `/post-it` 스킬 DB 경유로 rewire (register-postit·.postit-roots 폐기).
   - 파일 제거: `user_profile/`(7 aspect + README) + post-it.md 4개 (내용 DB 확인 후) + CLAUDE.md post-it.md 세션-read 트리거 제거.
   - 매트릭스(user_profile/README.md per-agent 매핑)는 문서로 보존(소스는 DB).
2. **Cluster B (Hermes port)** — B2(turn-counter hook, 결정론) → B1(session_search 자율호출 강화).
3. **구현 hygiene** (spec 외): sync-skills/drill 회귀 · stale 매뉴얼 draft 정정 · research 03↔08 cross-ref. (DESIGN_PRINCIPLES §0.5 ✅ 완료.)
