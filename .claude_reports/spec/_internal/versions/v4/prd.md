# Unified Memory System — PRD

> mode: **library + cli** · 작성 2026-06-15 · v3(DB화·저장소분리) · **v4 개정 2026-06-15** (profile 완전통합 + Hermes 잔여 port + 결정론-우선 원칙)
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

## 4. Cluster A — profile **완전** 통합 (v4 신규, D-3/D-7 격상)

> **현 상태 정직 명시**: profile은 지금 *recall/inject 표면*만 통합됨. sub-agent가 읽는 권위 소스는 여전히 `user_profile/*.md` 원본(de facto SoT)이고 `memory.db`는 후행 mirror — **절반짜리 통합**. (사용자 지적 2026-06-15 "별론데".)

**목표**: DB가 profile의 진짜 SoT, md는 DB→generated view. sub-agent 경로 Read(매트릭스 = `user_profile/README.md` per-agent 매핑)는 **보존** — md가 view라 안 깨짐.

- **A1 — DB가 SoT**: `memory.db` type=profile 레코드가 권위 소스. body = aspect 문서 전문.
- **A2 — DB→md projection wiring** (결정론, §0.5): `mem export --target profile`을 **SessionEnd `mem sync` + analyze-user 종료에 자동 연결**해 `user_profile/0X_*.md`를 faithful view로 재생성. body round-trip byte-identical 이미 검증(v3). 파일명은 source stem(`user-profile:07_coding_convention`)에서 결정론적으로 도출 → 매트릭스 경로 불변.
- **A3 — analyze-user를 DB-first로**: aspect 문서를 DB 레코드로 쓰고 거기서 md export (현재는 md 쓰고 DB가 mirror — 거꾸로). analyze-user의 _aspect별 분석_ 산출을 DB write로 종단.
- **A4 — 편집 경로 단일화 (edit-via-DB)**: `/post-it --scope user`도 DB 경유. 사람 직접 md 편집은 다음 export가 덮으므로 **DB가 단일 편집 경로**. (md 직접편집 방지 가드 — 결정론: export가 view를 권위화.)
- **트레이드오프(명시)**: profile 편집이 전부 DB 경유가 됨. cold-start corpus 수집은 여전히 사람(§Non-goals 인접 — 정체성 모델의 deliberate seed). steady-state drift 자동화는 Cluster B와 연계.

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
v3 그대로 (add/note/recall/index/inject/sync/export/import/migrate/lifecycle/project/stats/register-postit). v4에서 export의 profile target이 sync/analyze-user에 wiring (A2), B2용 turn-counter는 hook+state.

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
  - **D-9 (profile 완전통합)**: DB=profile SoT, md=generated view, analyze-user/post-it DB-first (§4).
  - **D-10 (Hermes 잔여 port)**: session_search 자율호출 + turn-counter 자기회고, 둘 다 결정론-우선 (§5).

## Next (구현 순서 — autopilot-code, 본 v4 입력)
1. **Cluster A (profile 완전통합)** 먼저 — 사용자 지적 incoherence 해소. `mem export --profile` wiring(A2) → analyze-user DB-first(A3) → post-it/edit 경로 단일화(A4).
2. **Cluster B (Hermes port)** — B2(turn-counter hook, 결정론) → B1(session_search 자율호출 강화).
3. **구현 hygiene** (spec 외): sync-skills/drill 회귀 · stale 매뉴얼 draft 정정 · research 03↔08 cross-ref · DESIGN_PRINCIPLES.md에 §0.5 결정론-우선 격상.
