# Unified Memory System — PRD

> mode: **library + cli** · 작성 2026-06-15 · v3(DB화·저장소분리) · v4(결정론-우선 원칙·Hermes port) · v5(Option 2 — user_profile·post-it 파일 메커니즘 제거, DB 단일 store, sub-agent DB 직접 읽기) · v6(Cluster C — 세션 자동 distillation: orchestration raw log → tier 메모리, "기억해둬" 수동 의존 제거) · v7(D-13 외부 분사화 + distiller sonnet + D-14 권한 하드닝 시도) · v8(D-14 권한 allowlist 무력 → no-tools+스크립트 실행 재설계) · v9(Cluster D — 결정론-first lifecycle 정비) · **v10 2026-06-17** (Cluster E — 큐레이션 단순화[세션끝 opus 풀 큐레이터, 메인 housekeeping 0] + audit P0 하드닝[strength·project_key·recall엔진·내구성])
> 입력: `research/hermes-agent/{03_memory_system,04_benchmark_gap,07_security,08_source_grounded}.md` · 기존 `tools/memory/*` · `skills/{post-it,analyze-user}/` · `user_profile/`
> · **v11 2026-06-22** (Cluster F — 루프↔메모리 환류: 루프 자율성 재정의·아침 논의 데스크·curator 산출물 대조 적극 prune·메모리 제도화 승격 채널 + 선결 버그 복원력)
> · **v12 2026-07-03** (Cluster G — recall-first guidance and memory-scout; semantic recall mandate superseded by v17 D-40, core-first adapter guard retained)
> · **v13 2026-07-04** (Cluster H — memory 도메인 adapter-parity 불변식: session-end distill 2-tier·MEM_DUMP_PUSH·portable distill dispatcher 계약. 근거 = codex-adapter-parity 감사 P-10·P-12·P-13·P-25·P-36)
> · **v14 2026-07-10** (Cluster I — retrieval usability and pending protection; automatic recall portion retired by v17 D-40)
> · **v15 2026-07-11** (Cluster J — 쓰기 관측성·전수 진단: 변이 이벤트 저널 + `mem log` + `mem doctor`. 계기 = fleet 메모리 가시화[agent-fleet-dashboard F-19]의 전제 + 읽기/쓰기 telemetry 비대칭 실측)
> · **v16 2026-07-14** (historical language-neutral automatic recall design, retired in full by v17 D-40)
> · **v17 2026-07-14** (agent-owned semantic memory judgment: automatic prompt classification/recall injection retired; deterministic code is limited to mechanical safety and retrieval infrastructure)
> · **v18 2026-07-14** (Cluster L — background-model storm containment: atomic global slots, rolling start budget, kill switch, adapter/runtime projection parity)
> · **v19 2026-07-15** (D-42 — main-session-only model lifecycle and explicit worker bootstrap boundary)
> · **v20 2026-07-20** (D-43 — on-call incident-to-proposal bridge with live corroboration, exact-key recurrence, and human-state ceiling)
> · **v21 2026-07-22** (Cluster N — 감사-주도 엔진 하드닝: 빈-스토어 생성 가드·cwd_origin v6 remap·CJK bigram 회수·plain-commit 미러+`mem maintenance`·pending drain. 근거=`plans/2026-07-22_memory-system-audit/`)
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`).
> **방향(사용자 확정 2026-06-15)**: "대공사 OK, 보수적 현상유지 X, 제대로·깔끔·근본부터." Hermes 메모리 적극 결합 + 중복 cut + DB-SoT.

## 0. 한 줄

흩어진 3개 기억(post-it 단기 · auto-memory 장기 · user_profile 전역)을 **하나의 SQLite store(`memory.db`) + tier 모델**로 통합. 진실원천=DB, git=`dump.jsonl` 텍스트 mirror, 전용 private repo `agent-memory`(구 claude-memory, 2026-07-10 개명). v4에서 **profile을 진짜 완전 통합**하고 **Hermes 잔여 port 2종**을 결정론-우선으로 붙인다.

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
- **D4 (revised by D-40)**: an agent-backed write does not require a separate human approval gate. The agent makes the semantic choice; code enforces action shape, exact deduplication, scope, and injection/secret safety.
- **D5**: lifecycle — working 자동만료/졸업, durable consolidate. gc만 사람 게이트.
- **D6**: 자체 하네스 — SessionStart `mem inject --hook` + SessionEnd `mem sync`.
- **D7 → Cluster A로 격상** (§4): 통합 깊이.
- **D8**: 보안 — injection 패턴·secret 마스킹 (코드). 메모리는 데이터로만.
- **D9**: 저장소 분리 — 전용 private repo `agent-memory`(구 claude-memory), config repo `memory/` gitignore + 이력 filter-repo 제거.

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

## 5.5 Cluster C — 세션 자동 distillation (v6 신규, 사용자 확정 2026-06-16)

> **문제 (사용자 지적)**: 세션 끝낼 때마다 "기억해둬"를 _수동_ 으로 말하는 게 번거롭다 — 자동화하고 싶다. 현 시스템 분석: ① 세션 raw 대화 로그는 하네스가 `projects/<enc_cwd>/*.jsonl`에 _이미 기계적으로 저장_ (우리 세팅 아님, Claude Code 기능). ② 서브에이전트 작업은 `.agent_reports/{plans,documents,...}` _산출물_ 로 이미 요약·정리됨 → 그걸 읽으면 됨. ③ **자동 회수가 비어있는 유일한 자리 = 메인 에이전트의 _orchestration raw log_** — 현재 turn-nudge(B2)+§2가 "타이밍"만 자동이고 _쓰기는 에이전트 행동_ 이라, 마지막 저장 이후 구간이 cold-close 시 유실. SessionEnd는 shell `mem sync`라 대화를 못 읽어 회고 불가.

핵심 = **raw 아카이브(전부 verbatim 색인→검색)가 아니라 distillation**. 세션 대화를 에이전트가 읽어 tier 메모리(working/durable)로 _정리_ 하는 자동 장치. (raw FTS 아카이브는 §5 B1이 지목한 검색 갭이나, durability는 jsonl이 이미 해결하고 현 규모에서 grep 회상으로 충분 → 본 cluster 범위 제외, recall --sessions는 grep 유지.)

**통일 메커니즘 — 단일 공유 increment marker (불변식)**: 두 발동 조건(① 프롬프트 N개 누적 / ② 세션 종료)은 _같은 증분 연산_ 을 cadence만 달리해 돌린다. **v7: 둘 다 detached 외부 distiller 분사** — 메인 에이전트는 정리에 관여 안 함(메인 turn 을 housekeeping 에 안 씀, 사용자 결정 2026-06-16). 둘이 **세션별 _하나의_ marker(마지막 처리 uuid)를 공유** — 어느 쪽이 발동하든 "marker 이후 새로 생긴 메시지"만 처리하고 marker 를 끝까지 전진. → 이중 처리·구간 누락 0. 세션 중엔 ①이 주기적으로 흡수, cold-close 는 ②가 잔여 tail 마감. **동시성**: 세션당 동시 distiller 1개 lock(① 실행 중 ② 발동 등 겹침 방지). 두 트리거 hook(turn-counter·SessionEnd) 모두 재귀가드 `MEM_DISTILL=1` 보유(distiller 가 `claude -p` 라 자기 UserPromptSubmit·SessionEnd 가 또 분사하는 것 차단).

### 5.5.1 D-11 — Harness-agnostic 세션 source 추상화
- 세션 raw log 흡수를 **pluggable source** 로 추상화: `ingest_session(source)` — source가 정규화된 (role, ts, text, uuid, is_sidechain) 메시지 스트림을 내놓음.
- **현재 adapter 1개 = Claude Code jsonl** (`projects/<enc_cwd>/<uuid>.jsonl`). 미래에 Claude를 못 쓰는 하네스로 가면 _그 하네스용 adapter만 추가_ → distiller·tier 로직은 불변.
- 다른 하네스 adapter는 **지금 구현 안 함**(YAGNI) — source 인터페이스 자리만 비워 둠. "멀리 봐서 하네스에 안 묶이게"의 구조적 대비.

### 5.5.2 D-12 — SessionEnd distiller (detached, 최종 sweep)
- SessionEnd hook이 **detached `claude -p` 분사**(§5.10 headless 패턴)로 방금 끝난 세션 jsonl을 읽어 salient(결정·교훈·미해결·컨벤션)를 working/durable tier로 `mem add` distill. 세션 닫힘을 블록하지 않음(fire-and-forget).
- **재귀 가드 (불변식)**: distiller 분사 세션은 `MEM_DISTILL=1` 환경에서 돌고, SessionEnd hook은 이 플래그면 _또 분사하지 않음_ → 무한 재귀 차단.
- **증분 스코프**: 위 _공유 marker 이후 구간_ 만 읽음(전체 재요약 비용 회피) — D-13 ①이 이미 흡수한 앞부분은 건너뛰고 잔여 tail 만 마감.
- tier 분류 = 기존 정의 재사용 (working=진행중·미해결·hint, durable=결정·교훈·컨벤션·사실, §1).
- **모델 = sonnet** (`claude-sonnet-4-6`, v7 — distillation 정확도 우선, 사용자 결정). cheap-tier(haiku) 아님.

### 5.5.3 D-13 — In-session 증분 consolidation (외부 detached distiller, v7)
- turn-nudge hook(B2) 확장: N턴마다 **메인이 아니라 detached distiller 를 분사**(D-12와 같은 worker·같은 marker, cadence만 다름). v7 전환 근거(사용자 결정 2026-06-16): "메인 클로드가 그 정리 일 하느라 load 걸리잖아 — 외부로 던져라". 이전 v6 의 '메인이 context 보유라 쌈' 논리를 사용자가 명시 waive(메인 turn 보존 우선).
- **증분만**: _공유 marker 이후_ _새 맥락 요약 mem add/note_ + _해결된 working 항목 prune(mem delete)_, 처리 후 marker 전진. 메인 컨텍스트·turn 소모 0.
- D-12와 동일 worker — 사실상 "주기 트리거(①) + 종료 트리거(②)"가 같은 detached distiller 를 부르는 구조. cold-close 유실 구멍은 ②가 마감.

### 5.5.4 D-14 — distiller 신뢰경계 차단: no-tools + 스크립트 실행 (보안, v8 정정)
> **v7 시도 실패 (라이브 검증 발견 2026-06-16)**: v7 은 distiller 권한을 `--allowedTools 'Bash(python3 *mem.py*:*)'` 로 "mem.py-only 제한"하려 했으나, **무력**으로 실측됨 — `settings.json` 의 `permissions.allow` 에 blanket `Bash` 가 있고 CLI `--allowedTools` 는 allow 에 _additive_(replace 아님)라 임의 명령(`date >> file`)이 그대로 실행됨. v7 빌드의 "비-mem.py 미실행"은 모델 자체 거부의 오인(권한 차단 아님). → 권한 allowlist 접근 폐기.
- **v8 해법 = distiller LLM 에서 실행 권한을 _아예 제거_ (§0.5 결정론-우선 정합 — LLM 은 판단, 코드가 실행)**:
  - dispatch 스크립트가 `mem distill <sid>` 로 대화 delta 를 미리 읽어 **프롬프트에 데이터로 주입**.
  - distiller `claude -p` 는 **도구 0**(`--disallowedTools` 로 Bash 등 전부 차단) — "어떤 기억을 남길지"를 **구조화 출력(JSON-lines: {tier,type,body})만** stdout 으로.
  - **dispatch 스크립트가 그 출력을 파싱·검증(tier∈{working,durable}, 형식)해 `mem add` 를 직접 실행**. LLM 출력은 _명령이 아니라 데이터_ 로만 다뤄짐(스크립트가 `mem add` 인자로만 전달, eval/실행 안 함).
  - injection 이 LLM 을 완전히 속여도 할 수 있는 건 "기억 레코드 텍스트 오염"뿐 — 명령 실행 _물리적 불가_(도구 자체가 없음). `mem add` 의 기존 injection/secret 마스킹이 2차 방어.
- **acceptance gate (enable 전 필수)**: distiller 호출에 "임의 셸 명령 실행" 프롬프트를 줘도 명령이 실행 안 되는지 실측(v7 의 `date >> file` 테스트 재현 — 파일 미생성 + hang 없음).
- opt-in 게이트(`MEM_DISTILL_ENABLE=1`) 유지. enable 전 검증 ✅완료분: 재귀가드 env-상속(`claude -p` 가 SessionEnd 발화 + `MEM_DISTILL=1` 상속 확인)·ghost-marker·hang-free. 남은 gate = 위 no-tools acceptance.

### 5.5.5 데이터 모델 영향
- 신규 테이블 **없음** — distill 결과는 기존 `records`(working/durable)로 흡수. raw 대화는 jsonl(하네스 native)에 남고 DB로 복제 안 함(D-11 source는 read-only adapter). dump.jsonl·agent-memory 동기 대상은 기존 records 그대로(원문 대화 비포함 — 프라이버시·용량).
- 신규 상태 파일: **단일 공유 increment marker**(세션별, `memory/.distill-state-<sid>` 류 — turn-state 패턴 동형) + 세션당 distiller lock(`.distill-lock-<sid>`, mkdir-atomic 동시 1개). 둘 다 루트 `/memory/` gitignore 가 커버 — 별도 gitignore 파일 불필요(구현 D1; 루트 ignore 가 `memory/` 전체를 무시하므로 lock·state 가 git 에 침투 못 함). 두 트리거(①·②) 양쪽이 같은 marker 를 읽고 전진시킴.

## 5.6 Cluster D — 결정론-first lifecycle 정비 (v9, 사용자 확정 2026-06-17)

> **원칙 정립 (사용자, 2026-06-17)**: 판단 본체(salience 등)는 결정론화 _불가_ — 핵심은 "누가 판단하나". **추가(가역·저위험) 판단 → 외부 싼 에이전트 offload OK / 삭제·정리(비가역·data-loss) 판단 → 메인 클로드 직접.** 결정론 scaffold(트리거·탐지·실행·보안)가 판단을 감싸 신뢰성·재현성을 주되, 판단은 가장 싼 자리에 배치. §0.5 의 정확한 형태. Hermes 도 consolidation 은 메인이 함(capacity-error 강제 트리거) — 같은 자리, 트리거만 다름.

### 5.6.1 D-15 — recall 자동 사전주입 hook (B1 완성)
- Historical decision, **retired by D-40**. The UserPromptSubmit classifier treated semantic relevance as a deterministic token/threshold problem. Current adapters expose explicit retrieval, and the acting agent decides when memory is relevant.

### 5.6.2 D-16 — lifecycle 탐지 → 메인 노출 (consolidation/prune 후보)
- 현 `lifecycle` 의 durable near-dup `[dup-flag]` 가 SessionEnd `mem sync` 출력으로 흘러 *아무도 안 봐서* 死. → **`mem inject`(세션 시작)에 "정리 후보" 섹션으로 노출** — 메인이 보고 직접 consolidate/prune/graduate (실행=메인, 원칙대로). 탐지(결정론)와 실행(메인 판단) 분리.
- 노출 대상: durable near-dup 그룹 + (옵션) durable soft-ceiling 초과·usage(Hermes e-4 차용 — capacity 가시화) + 만료 임박 working.

### 5.6.3 D-17 — working TTL = backstop, 삭제 권한 = 메인
- **distiller(외부) = add-only 확정** (prune/delete 안 붙임 — v8 현 구현 ratify). working prune/graduate·durable consolidation = **메인 직접**(D-16 노출 받아 in-context 실행).
- **working TTL(21일) = deterministic backstop** 유지 — 메인이 검토 못 하고 방치된 working 만 시간 정리(안전망). 1차=메인 검토(노출 기반), 2차=TTL. (spec §1 "자동만료/졸업" 중 _졸업_ 은 메인이 D-16 노출 받아 수행 — 그간 미구현분 충원.)
- Hermes 대비: Hermes 는 시간 prune 없음(capacity-only), 우리는 TTL backstop + 메인검토 hybrid.

## 5.7 Cluster E — 큐레이션 단순화 + audit P0 하드닝 + model-agnostic 캡처 (v10, 사용자 확정 2026-06-17)

> **계기**: 사용자 "메모리는 가장 중요한 시스템 — 다각도 점검+강화". 8각도 read-only audit(`analysis_project/memory-audit/findings.md`, 716줄) 실측 + "구조가 너무 복잡 → 세션끝 distiller 를 opus 로 올려 메인 일까지 위임" 단순화 지시 + "대화 로깅을 일반화해 on-premise 로(궁극 솔루션)" 결정. 결정론-first 정합: schema·marker·script 실행·dump·프록시 = 코드, opus 판단 = salience·병합·prune 만.

### 5.7.1 큐레이션 단순화 (Cluster C/D 정정 — 역할 collapse)
복잡했던 3자(distiller add → script flag → 다음세션 메인 consolidate)를 **세션끝 opus 1주체**로 collapse:
- **세션끝 distiller = opus 풀 큐레이터** (D-12 모델 sonnet→**opus**, 역할 add-only→full-curate): 전체 세션 + 현 프로젝트 메모리 읽어 **add + semantic consolidate + strength 합산 + resolved-working prune** 통째로. "새 메인이 뭐가 해결됐는지 모름" 문제 소멸(세션끝이 full context 보유 — 해결·dup 을 직접 앎).
- **N턴 in-session distiller = sonnet, 경량 add-only 유지** (D-13). 증분 capture 만.
- **메인 세션 = 메모리 housekeeping 0** — D-16 정리후보의 _메인 실행_ 부분을 세션끝 opus 로 위임(메인 load 0 완성). inject 정리후보는 informational 로 축소.
- **D-17 "삭제=메인" → "삭제=세션끝 opus"** 이전. 정당화: opus capable + full context + **worst=비효율(손실 아님)** + dump 버저닝(E-5)으로 잘못된 prune 복구가능. durable 삭제도 opus 가 보수적 프롬프트 + dump 안전망 하에.
- **보안 불변(v8 D-14 확장)**: distiller 여전히 **no-tools**. 출력계약을 `{tier,type,body}` → **action JSON**(`add`/`reinforce(id)`/`merge(ids→canonical)`/`prune(id)`)으로 확장. **script 가 검증 후 실행**(INSERT/strength++/merge/DELETE, shell=False, LLM 실행 0). prune/merge id 는 현 프로젝트 records 화이트리스트 대조(profile 등 보호).

### 5.7.2 E-1 — strength/reinforcement 차원
- records 에 **`strength`(재출현 횟수) + `last_accessed`** 칼럼 추가(schema 변경 — E-5 user_version 게이트 선행).
- **dedup = 버리기 아니라 reinforce**: ≈이미 있으면 새 레코드 대신 strength++ (2번 나옴 = 중요 신호, Hebbian). **exact-match = script 결정론 reinforce / fuzzy 근접 = script 가 후보 flag → opus 가 병합 판단**(flag 는 비파괴라 false-positive 무해 — 메인/opus 가 거름).
- strength → injection 랭킹 · recall 랭킹 · cold-decay 저항.

### 5.7.3 E-2 — 폭증 방지 (distiller 가 add 엔진이라 필수)
- **add-time dedup(원천)**: distiller 에 현 durable snapshot 주입 → "이미 있는 것 재기록 마라".
- **durable soft-ceiling** passive 한 줄 → opus 큐레이터 트리거 신호로 격상 (현 78/80, 임박).
- **injection budget**: strength 랭크 top-K(폭증해도 컨텍스트 bounded).
- **cold-decay**: `last_accessed` 오래된 durable = prune 후보(opus 판단).

### 5.7.4 E-3 — project_key robust (audit P0 #1 — 폭증·recall·inject·lifecycle 4면 동시해소)
- 현 raw `enc_cwd(Path.cwd())` → worktree·이동에 silo/오펀(worklog-board 3분할 실증). → **project_key 해석순서**: ① git remote URL → ② `git-common-dir` 캐노니컬 repo root(worktree→main 매핑) → ③ `.claude-project-id` 마커(이동 견딤) → ④ cwd(최후).
- **fail-safe**: hard-fail 금지(항상 ④까지)·키 불확실 시 broad inject(놓치는 것보다 안전)·**삭제는 opus+dump 안전망**이라 오인식해도 손실 0.
- **고아 탐지**: 어떤 live 프로젝트로도 해석 안 되는 cwd_origin → 고아 후보 surface. 기존 cwd_origin 옛경로 → project_key 마이그레이션.

### 5.7.5 E-4 — recall 엔진 교체 (audit P0 #2 — 死 promise)
- 현 `recall()` query 통째 단일 phrase FTS → 다단어·NL hit 0. → **multi-term OR + bm25 + top-K** + strength 가중. Ranking and multilingual tokenization remain retrieval infrastructure after an agent initiates a query; they do not classify whether a prompt should trigger recall (D-40).

### 5.7.6 E-5 — 내구성 봉합 (audit P0 #3, dump 버저닝이 삭제 안전망)
- `mem sync` 에 **dump 자동 commit(+버전 이력 = 잘못된 prune 복구 안전망)**. 현재 push 0 → 머신 손실 시 영구소실 갭.
- import 멱등화(FTS ghost fix) · **`PRAGMA user_version` 마이그레이션 게이트**(다발 schema 변경 C5 선행) · **INJECTION_PAT flag persist**(현재 계산만·persist X → poisoning 무한재주입 — 데이터펜스로 차단).

### 5.7.7 E-6 — graduate (working→durable, 미구현 확정)
- 세션끝 opus 가 "이 working 은 durable 가치"면 promote(졸업). spec §1 "자동만료/졸업" 의 졸업분 충원.

### 5.7.8 E-7 — model-agnostic 캡처 = D-11 adapter (프록시 폐기, 사용자 재검토 2026-06-17)
- **검토 결론**: on-premise 로깅 프록시(API 경계 캡처)는 **redundant** 로 폐기. 근거(사용자 지적): **다른 하네스도 _자기_ 세션 로그를 남긴다** → 우리가 캡처를 새로 만들 필요 없이 **그 로그를 읽는 D-11 adapter 만 추가** 하면 model-agnostic 달성. 프록시는 fidelity 이득 0(둘 다 같은 대화), 한계이득(미로깅 하네스·포맷 통일·로깅 독립)은 좁은데 비용(상시 서비스·SSE 재조립·보안 surface·fail-open)은 큼 → 비용 ≫ 이득.
- **확정 방향**: model-agnostic 캡처 = **D-11 source 추상화(이미 보유) + "하네스는 어차피 로그를 남긴다"**. Claude Code 외 하네스로 가면 그때 그 포맷 adapter 1개 추가. 신규 컴포넌트·상시 서비스 없음.
- **optional(미채택, 메모만)**: 현 vendor jsonl 을 우리 store 로 미러하는 hook(durability 사본) — jsonl 이 이미 디스크에 있어 실익 낮아 보류.

### 5.7.9 데이터 모델 영향
- records 신규 칼럼: `strength` INTEGER · `last_accessed` TEXT (E-1). `cwd_origin` → project_key 값(E-3, 의미 변경+마이그레이션). **`PRAGMA user_version` 마이그레이션 프레임**(E-5) — 다발 schema 변경의 단일 게이트.
- 신규 컴포넌트 **없음** (E-7 프록시 폐기). raw 대화는 계속 vendor jsonl(하네스 native)에 — distiller 가 D-11 adapter 로 읽고 distill, DB 복제 X. dump.jsonl·agent-memory 동기엔 distill 결과만(raw 비포함) 유지.

## 5.8 Cluster F — 루프↔메모리 환류 + 적극 정리 (v11, 사용자 확정 2026-06-22)

> **계기**: 메모리에 영구 누적되는 데이터를 주기적으로 ① 세팅·하네스·루프 등 시스템 구조로 *제도화* 하고 ② 불필요분을 *적극 정리* 하는 환류 고리 부재 지적(사용자). 조사 결과 — `graduate` 는 working→durable tier 내부 전환뿐(메모리 *밖* 승격 경로 0), curator 정리는 대화+메모리 snapshot 만 보고 *산출물 미대조*, 연수(study) 루프는 도입 후 한 번도 정상 작동 못 함(2026-06-21 401 즉사·hold). 선결 버그(D-29) → 환류 설계(D-25~28). v17 D-40 정합: 트리거·산출물 캡처·action 검증·graveyard = 코드, salience·승격·prune·merge 의미 판단 = acting agent.

### 5.8.1 D-25 — 루프 자율성 재정의
- 기존 `loops/README` line 21 "**루프는 일을 하지 않는다** — 삭제·지침 적용은 사용자 결정" 원칙을 **폐기·재정의**. 근거: curator 가 *이미* 무인 prune 중 — 원칙이 이미 반쯤 거짓이었고, 매 건 사용자 사전승인은 비효율(연수·당직 제안이 06-19 이월 누적 실증).
- **새 원칙**: 루프는 *되돌릴 수 있고 명백한* 일은 **무인 직접 처리**하되 **한 일을 전수 보고**한다. 되돌리기 어렵거나 판단이 필요한 것만 아침 논의로.
- **전제 가드 2개** (원래 원칙이 막으려던 리스크 — 무인 오판·injection·깜깜이 변경 — 을 대신 차단): (a) **되돌림 보장** — 삭제·변경은 graveyard·git 등 복구 가능 경로로만 (b) **전수 보고** — 무인 처리분은 빠짐없이 아침 브리핑에. = "사전 승인"을 "되돌림 가능 + 사후 통보"로 교체.
- 동기화 대상: `loops/README`·`DESIGN_PRINCIPLES`·`oncall.md`("보고만" → "처리+보고").

### 5.8.2 D-26 — 아침 논의 데스크
- **트리거**: `당직 cron(05:37) 이후 AND cwd==~/.claude AND 그날 첫 사용자 발화` → UserPromptSubmit hook 이 '밤 처리 요약 + 논의 안건'을 additionalContext 로 주입. 상태파일(마지막 브리핑 날짜)로 하루 1회.
- **왜 SessionStart 아니라 '그날 첫 상호작용'**: 세션을 장시간 유지하는 환경이라 SessionStart 가 아침에 안 뜸. '하루 첫 입력'이 견고한 기준.
- **전용 데스크**: `~/.claude` cwd 세션 = 당직/연수 논의 자리. 다른 프로젝트 cwd 에선 브리핑 안 뜸(작업 방해 차단).
- 기존 '당직 처리해줘' *발화* 트리거를 이 *자동* 트리거로 승격 — 안 물어도 안건이 안 쌓이고 뜬다.

### 5.8.3 D-27 — curator 산출물 대조 + 적극 prune
- SessionEnd opus 큐레이터 입력에 `=== ARTIFACTS (DATA) ===` 블록 추가 — git log(머지·완료 커밋)·plans done 여부·spec phase 를 기계 캡처해 주입. 대화에 안 나와도 *산출물 증거*로 "이 working 이 가리키는 작업이 끝났나" 판단.
- prune 지침 `보수적, 확신 없으면 두세요` → `산출물 증거가 받쳐주면 적극적으로 prune`. 적극성 방향 = "막연히 더"가 아니라 "증거 기반 자신있게".
- **죽은 working 조기정리**(21일 TTL 안 기다림) + **명백한 durable 정리** 통합 — 둘 다 "산출물에서 끝난 증거 → 삭제".
- **안전 3겹 유지**: snapshot-id 화이트리스트(대상 제한)·graveyard fail-closed(복구)·DATA 라벨(injection 무력화). graveyard 가 적극화의 안전망.
- (확인됨) `/clear` 도 SessionEnd reason=`clear` 를 쏘고 우리 hook matcher 가 `*` 라 curator 발동 — 세션 유실 구멍 없음.

### 5.8.4 D-28 — 메모리 제도화 환류 (승격 채널)
- **v17 D-40 supersession**: the historical implementation filtered `convention|lesson` records as promotion candidates. That fixed semantic type gate is retired. The read-only projection now exposes a bounded view of all visible durable records; type and strength are evidence only, and the acting agent judges whether any item should be institutionalized.
- **Destination is contextual**: a useful item may belong in a runtime bootstrap, CONVENTIONS, DESIGN_PRINCIPLES, a hook, a drill case, another artifact, or memory only. No record type automatically selects a destination.
- **Prune and graduate-out remain separate actions**, but neither is decided by a fixed fact/decision/history versus rule/principle taxonomy. Apply and verify the destination first; then the agent decides whether pruning the memory record is useful.
- **prune 순서**: 반영·검증 *후*에만 prune (반영 전 삭제 = 영구 소실, graveyard 만으론 부족). "반영 → drill 통과 → prune".
- **Agent judgment, not a rule button**: institutionalization and cleanup require contextual judgment. Deterministic code may present candidates and enforce recovery/safety; it does not make the semantic decision.

### 5.8.5 D-29 — 루프 인프라 복원력 (선결 버그, ✅ main `b95b9a9`)
- ① `loops/lib.sh` PATH 보정 — cron 제한 PATH 가 `/usr/bin/node`(v10) 를 집어 codex hook(.mjs ESM)이 SyntaxError 로 죽던 것 → `~/.local/bin`(v20) 앞세움.
- ② `run_claude_retry` — 401/5xx/overloaded 일시장애 백오프 재시도(3회), session/usage limit 즉시 ABORT, 실패 마커 기록.
- ③ oncall 생존체크 — 루프 '실행 시각'만 보던 점검에 exit code·실패마커 추가(2026-06-21 연수 401 즉사를 시각점검이 못 잡은 사고 재발방지).

### 5.8.6 데이터 모델·컴포넌트 영향
- 신규 테이블·칼럼 **없음**. curator 입력 ARTIFACTS 블록은 dispatch 스크립트가 기계 캡처(코드, §0.5). 신규 상태파일: 아침 브리핑 날짜 마커(`memory/.briefing-<date>` 류) + 승격 후보 추출은 read-only projection. 신규 컴포넌트: `loops/lib.sh`(✅ 머지) + 아침 데스크 UserPromptSubmit hook(D-26).
- **post-it 역할 재검토(열림)**: distiller 자동화로 `/post-it` 의 '수동 기억' 용도가 distiller 와 상당 부분 겹침(Cluster C 가 "기억해둬 수동 의존 제거"가 목적이었음). distiller 의 *명시 override·핸드오프 채널*로 재포지셔닝하거나 deprecate 검토 — v11 범위 밖, 별도 결정.

## 5.9 Cluster G — historical recall-first guidance + core-first guard (v12; recall mandate superseded by D-40)

> 계기: SR_CorrNet_DSC 보고서용 spectrogram 스타일을 기존 메모리 컨벤션(48kHz 풀밴드·ylim 0~24kHz)과 다르게 즉흥 생성한 사고, 그리고 이를 고치며 adapter 를 core 보다 먼저 고친 순서 위반. 둘 다 "생각으로 기억"할 일이 아니라 하네스 원칙과 guard 로 닫는다.

- **Recall guidance (superseded by D-40)**: v12 prescribed topic-based recall before several classes of work. v17 removes that semantic rule; the agent now decides contextually whether prior memory would materially help.
- **memory-scout**: 인라인 1~2쿼리를 넘는 심층 탐색은 read-only memory-scout capability 로 분리한다. 다각 쿼리 → cross-cwd → raw 세션 순으로 확장하고, 결과는 15줄 이하 verdict/record id/적용 지침으로 반환한다. 쓰기 명령은 전면 금지한다.
- **core-first adapter guard**: adapter 편집 전 실제 `core/*.md` read marker 를 요구한다. hard gate 는 검증 가능한 read marker 와 stale 여부만 강제하고, "core 를 먼저 수정했는가"는 `core/DESIGN_PRINCIPLES.md` 제1원칙과 drill 이 보완한다.

## 5.10 Cluster H — memory 도메인 adapter-parity 불변식 (v13, 2026-07-04)

> 계기: codex-adapter-parity 전수 감사(`research/codex-adapter-parity/` — analysis_summary §1, cards/04_memory.md)가 memory lifecycle 의 어댑터 간 비대칭을 확정 — Codex session-end 가 add-only 인데 ADAPTATION 이 "Claude 와 match" 로 신고(P-12 overclaim), 그 구조적 뿌리는 portable dispatcher 미사용(P-13). 본 cluster 는 memory 계약을 adapter-agnostic 불변식으로 명문화한다. 어댑터 _전반_ parity 계약(P-01 derived guard 등)은 본 PRD 범위 밖 — `core/ADAPTATION.md` 소관으로 별도 처리.

### 5.10.1 D-30 — session-end distill 은 adapter-agnostic 2-tier (계약)
- 본 시스템의 distill 은 **turn=increment(add-only, fast tier) + session-end=curate(deep tier — snapshot-grounded prune/merge/graduate/consolidate, D-18)** 2-tier 가 계약이다. 이는 Claude adapter 구현 디테일이 아니라 **모든 어댑터의 session-end 요구사항**.
- 어댑터는 curate 층을 실현하거나, 못 하면 **미실현을 명시 신고**(ADAPTATION 문서에 "increment-only — curate 미실현" disclosure)한다. "matches Claude's session-end distillation" 류 표현은 curate 축까지 성립할 때만 허용.
- 현황(감사 기준): Claude ✅ 2-tier / Codex ❌ increment-only (P-12 — Phase 3 수정 대상).

### 5.10.2 D-31 — SessionEnd sync 계약에 dump mirror push 포함
- SessionEnd sync 는 `mem.py sync` 만이 아니라 **`MEM_DUMP_PUSH=1`(dump.jsonl git mirror push, E-5 내구성 안전망)** 까지가 계약 — 어댑터가 push 를 생략하면 그 어댑터로 돈 세션의 기억이 원격 mirror 에서 drift(P-10).
- 현황: Claude ✅ / Codex ❌ push 생략 (Phase 3 수정 대상).

### 5.10.3 D-32 — distill worker 는 portable dispatcher 계약 경유
- distill worker 는 portable `hooks/mem-distill-dispatch.sh` 의 계약(`MEM_DISTILL_WORKER <mode> <model> <prompt-file>`)을 경유한다. 어댑터가 자체 worker 를 재구현하는 경우에도 **mode/model routing(fast=increment·deep=curate 모델 tier, P-36)·snapshot-id whitelist 안전층(P-25)·per-session lock·재귀가드·D-41 global concurrency/start budget/kill switch** 를 보존할 의무 — increment 프롬프트에 mutation action(prune/merge)을 나열하면서 whitelist 를 우회하는 조합 금지.
- 현황: Claude ✅ dispatcher 경유 / Codex ❌ 자체 재구현 subset (P-13 — Phase 3 에서 dispatcher 채택 또는 계약 요소 보존 증명).

## 5.11 Cluster I — 꺼내 쓰는 경로 강화 + 미소비 인계 보호 (v14, 2026-07-10)

> 계기: Claude Code와 Codex의 독립 진단이 같은 병목을 확인했다. 쓰기·세션 주입은 동작하지만 ① 자동 recall이 고정 과거지시 phrase에 의존해 실제 프로젝트 발화에서 거의 0회였고, ② SessionStart top-K 밖 working/durable은 recall 없이는 잠김, ③ recall은 12-token snippet만 반환해 전문 확인에 SQLite/dump 우회가 필요, ④ 직전 세션의 canonical handoff와 고유 보강 2건이 curator merge에서 near-duplicate로 오판돼 보강 전문이 사라졌다. agent-memory git `55076af→042d277`에서 보강 2건 삭제와 canonical strength `1→3`이 동시에 발생했고 graveyard 전문이 현 `merge()` 경로와 일치하므로 ④는 prune 추정이 아니라 merge 사고로 확정한다. v16은 ①의 잔여 phrase-dependent confidence를 완전히 제거한다.

### 5.11.1 D-33 — full-body retrieval은 1급 CLI 계약
- `mem show <id> [--all]`은 visibility fence 안의 단일 레코드 metadata+전문을 원문 줄바꿈 그대로 출력한다. 기본 fence는 현재 project+global이며 `injection_flag` 레코드는 항상 제외한다. 다른 project ID 존재 여부는 generic not-found로 감춰 scope oracle을 만들지 않는다.
- `mem recall "<query>" [--full] [--limit N]`을 추가한다. ordinary 레코드의 flag 없는 기존 출력은 byte-compatible하게 유지하고, `--full`은 같은 ranked ID의 snippet만 전문으로 교체한다. pending 결과는 소비 workflow를 발화할 수 있도록 `[pending:<id>]`를 식별자로 출력한다. `limit`은 1~100, 기본 20.
- `show`·명시 recall은 `last_accessed`를 갱신하지만 **읽기 자체를 handoff 소비로 간주하지 않는다**. memory-scout는 DB 우회 대신 show/full을 사용한다.

### 5.11.2 D-34 — historical automatic recall probe (retired by D-40)
- The v14/v16 prompt classifier is removed from active adapters and from `mem.py`. It was deterministic and language-neutral, but it still attempted to answer the semantic question “is prior memory relevant now?” with token statistics and thresholds.
- `mem recall --auto` is retired. The former hook remains only as a fail-open compatibility no-op for stale runtime projections.
- Explicit retrieval keeps FTS/BM25 ranking, CJK/identifier tokenization, scope fences, result limits, and bounded access telemetry. These mechanisms organize results only after the agent chooses to search.

### 5.11.3 D-35 — delivery state와 파괴 경로 fail-closed
- schema v5에 `delivery_state TEXT NOT NULL DEFAULT 'ordinary'`를 추가한다(`ordinary|pending|consumed`). 새 `type=handoff`는 자동 `pending`; 인계 목적 thread는 `--requires-consume`로 pending을 명시한다. v4→v5 및 구 dump import는 기존 `type=hint|handoff` 또는 body `^HANDOFF`를 fail-safe하게 pending으로 backfill한다.
- `mem consume <id>`만 일반 `pending→consumed` 전이를 수행한다. `show`, recall/full, SessionStart inject, 자동 hook hit는 비소비다. source upsert·body dedup은 project `cwd_origin` 경계 안에서만 일어나며 pending 보호를 단조 보존해 ordinary 재기록으로 되돌리지 않는다. working pending은 소비 전 expiry 없이 유지하고 consume 시점부터 21일 TTL을 다시 시작한다.
- 실행시점 이중 가드: curator snapshot에서 pending을 `PROTECTED PENDING`으로 보이되 destructive `IDS:`에서 제외하고, `prune`·`delete`·`merge`·`lifecycle --apply`가 `BEGIN IMMEDIATE` 이후 같은 write transaction 안에서 DB 상태를 다시 확인해 미소비 pending을 거부/보존한다. pending 하나라도 포함된 merge는 삭제·strength 변경 없이 전체 원자 취소한다. 명시 delete는 consume 선행 또는 `--force`가 필요하다.
- graveyard는 `_deleted_at`, `_action`, `_canonical` 메타를 보존하고 `mem restore <id>` 단건 복구를 제공한다. pipeline/post-it 자동 consume은 handoff ID가 명시 입력되고 성공 산출물이 의무 반영을 증명할 때만 허용한다.

### 5.11.4 D-36 — SessionStart cap은 retrieval 개선 뒤 재관찰
- 현 top-K/문자 cap 자체는 이번 단계에서 확대하지 않는다. D-40 이후 관측은 explicit recall/show/consume과 SessionStart injection에 한정한다.
- Codex SessionStart memory inject opt-in과 adapter별 lifecycle 차이는 유지한다. Explicit retrieval, full-body access, and pending protection remain runtime-neutral; automatic prompt recall policy is retired by D-40.

## 5.12 Cluster J — 쓰기 관측성 + 전수 진단 (v15, 사용자 확정 2026-07-11)

> 계기: fleet 메모리 가시화(agent-fleet-dashboard **F-19**) 설계 중 실측 — 읽기측 telemetry(D-34 recall-events.jsonl)는 있는데 **쓰기측은 삭제만 graveyard 에 남고 add/note/consume/reinforce/merge/graduate 는 per-event 흔적 0** (간접 이력 = dump.jsonl git diff 뿐). `mem` 에 `log`/`recent` 류 명령 없음, `stats` 는 시간축 부재. "최근 무엇이 기억되고 무엇이 지워졌나"의 1급 경로와 store 전수 건강 진단이 둘 다 부재. §0.5 결정론-first 정합 — 이벤트 기록·진단 전부 코드, LLM 판단 0.

### 5.12.1 D-37 — 쓰기 이벤트 저널 (write-side event telemetry)
- mem.py 의 **모든 변이 경로**(add/note/consume/reinforce/merge/prune/graduate/reattribute/delete/restore/lifecycle-expire)가 write-events.jsonl 에 1줄 append — 위치·패턴 = D-34 recall-events 와 대칭(`$XDG_STATE_HOME/agent-memory/`, bounded rotation 256KB/최근 500줄, raw 대화·전문 비저장).
- 레코드: `ts / action / id / tier / scope / type / actor / sid / snippet(≤80자) / cwd`. `actor ∈ {manual, distiller, curator, lifecycle, sync, restore}` — apply-distill-actions·hook 경유는 env(`MEM_DISTILL`·mode)로 결정론 판별, 판별 불가면 `manual`. `cwd`(additive 2026-07-16)는 변이 프로세스의 레포 귀속 — `MEM_CWD` env 우선, 프로세스 cwd 폴백; fleet F-19 v11 레포별 카드 행이 `project_of(cwd)`로 소비하며, 필드 없는 구행은 소비자가 정직 생략(포맷 양 spec 동기 조항 이행 기록).
- **fail-open (graveyard 와 반대 방향, 의도적)**: 저널 append 실패는 쓰기를 막지 않는다 — graveyard(파괴 복구 안전망)=fail-closed 유지, 저널(관측 telemetry)=fail-open. 이중화 아님: 파괴 이벤트는 양쪽에 남되 역할이 다름(복구 vs 관측).
- dump.jsonl·agent-memory 동기 대상 아님(로컬 관측 데이터).

### 5.12.2 D-38 — `mem log` (최근 활동 1급 조회)
- `mem log [--limit N] [--action <a>] [--tier <t>] [--actor <a>] [--json]` — 저널 tail 을 사람용(1줄/이벤트)·기계용(`--json`)으로 출력, 기본 20건. fleet·oncall·사용자 공용 표면.
- `stats`(스냅샷 카운트)는 불변 — log 는 흐름(시간축)을 보완.

### 5.12.3 D-39 — `mem doctor` (read-only 전수 진단) + oncall 편입
- 서브커맨드 1개, 전 항목 결정론 체크·read-only·수정 0: ① `PRAGMA integrity_check` ② records↔FTS 카운트 정합 ③ schema 불변식(tier/delivery_state enum·working 의 expires 존재) ④ working 비대 ⑤ stale pending(pending 21일+ 미소비) ⑥ durable soft-ceiling 초과 ⑦ graveyard↔DB 정합(graveyard 의 삭제 id 가 DB 에 생존 시 위반) ⑧ dump.jsonl 신선도(마지막 sync 반영 vs DB max(updated)) ⑨ 워커 건강(프로젝트별 마지막 distill/curate 시각 — 저널 기반, 활성 프로젝트 장기 무소식 = silent-death 신호).
- 출력: 항목별 OK/WARN/FAIL + exit code(0 clean / 1 warn / 2 fail) — oncall·스크립트 기계 소비.
- **oncall 항목 1개 추가, 새 loop 신설 없음** — D-25 계약대로 read-only 진단+보고(아침 브리핑 편입). **조치 권한 불변**: 삭제·consolidate·merge = D-18 세션끝 opus 큐레이터 소유 — doctor 발견은 아침 논의 안건·큐레이터 입력으로만 흐른다(doctor 는 진단, 고치는 손은 기존 소유자).
- `tools/memory/index-check.sh`(legacy 파일 인덱스 대상)와 별개 — doctor 는 store(DB) 대상.

### 5.12.4 데이터 모델·컴포넌트 영향
- 신규 테이블·칼럼 **없음** — 저널은 XDG state jsonl 1개, doctor 는 read-only 조회.
- 소비자: fleet `collectors/memory.py`(agent-fleet-dashboard F-19 — read-only tail 관찰; 저널은 memory 시스템이 자기 목적으로 남기는 로그라 fleet F-1 zero-injection 과 정합) + oncall(doctor) + 사용자(`mem log`). 저널 포맷 변경 시 양 spec 동기 의무.

## 5.13 Cluster K — Agent-owned semantic memory judgment (v17, 2026-07-14)

### 5.13.1 D-40 — Semantic decisions stay with an agent
- The acting agent—main, distiller, or curator—decides contextually what to store, retrieve, promote, merge, or prune. The contract does not encode fixed signal phrases, mandatory recall topics, promote/skip categories, semantic confidence thresholds, or keyword classifiers as substitutes for that judgment.
- Deterministic code owns mechanical integrity only: schema and action validation, scope/visibility isolation, pending protection, transaction boundaries, lifecycle scheduling, bounded output/telemetry, no-tools execution, and graveyard/dump recovery.
- Prompt-submit bridges no longer pass every prompt to a recall classifier. `preflight recall <query>`, `tools/memory/recall.sh`, and `mem recall` are explicit agent-invoked retrieval surfaces.
- Retrieval ranking and multilingual tokenization remain. They rank records for a chosen query; they do not decide whether the agent should query.
- Regression gates reject active prompt-hook registration of `mem-recall-inject.sh`, active `preflight recall` calls from prompt bridges, and a semantic `mem recall --auto` implementation.

## 5.14 Cluster L — Background-model storm containment (v18, 2026-07-14)

> Incident: a first mass SessionEnd/distill wave and a separate Fleet title-refresh recursion showed that per-session locks and recursion environment markers do not bound work across hundreds of different session IDs. The title chain reached 216 workers and Claude-family process count reached 607 before emergency termination. D-41 covers the memory-dispatch half; agent-fleet-dashboard F-23 covers title refresh.

### 5.14.1 D-41 — Global cost boundary for automatic distillation
- Every `mem-distill-dispatch.sh` realization keeps the existing per-session lock and `MEM_DISTILL=1` recursion cut, then additionally claims a **fixed-name `mkdir` global slot** before any model worker starts. Default concurrency is 2, hard maximum 4, and `MEM_DISTILL_MAX_CONCURRENT=0` disables starts. Count-then-create is forbidden because simultaneous SessionEnd hooks can all observe the same stale count.
- A second fixed-name lease pool is a persistent rolling start budget: default 4 and hard maximum 8 starts per 10 minutes (`MEM_DISTILL_MAX_STARTS`; 0 disables). Worker completion releases its concurrency slot but not its start lease. This prevents a large backlog from draining sequentially as slots reopen.
- `$MEM_STORE/.distill-disable` is the operator kill switch and is checked both at entry and again after leases are acquired. Invalid numeric configuration falls back to safe defaults. Slot/session locks orphaned by SIGKILL are reclaimed by bounded stale GC; start leases expire after 10 minutes. Capacity or guard failure is fail-closed and leaves the distill marker unadvanced for a later safe trigger.
- The portable dispatcher and adapter realizations must preserve this contract, and physical runtime projections must be hash-verified after installation. Hermetic regression launches 12 distinct session IDs concurrently against a sleeping stub, asserts at most 2 model workers, waits for slots to reopen, then asserts a second wave starts 0 because the rolling budget remains full. The kill-switch case invokes 0 workers. No live model is used for verification.

### 5.14.2 D-42 — Main-session-only model lifecycle and worker bootstrap
- Only an interactive, user-facing main session owns automatic model-backed lifecycle work: SessionStart memory injection, prompt-time briefing/turn-nudge, SessionEnd sync+curation, Fleet title summarization, and main-pane status publication. Registered headless dispatches, loop/drill runs, title workers, distillers/curators, and runtime-native subagents are workers and never trigger another automatic model session.
- `AGENT_SESSION_ROLE=worker` is the portable launch marker. Adapter compatibility markers (`AGENT_DISPATCH_CHILD=1`, nonempty `AGENT_DISPATCH_DEPTH`, `CLAUDE_CODE_CHILD_SESSION=1`, nonempty `OPENCODE_DISPATCH_SLUG`, `FLEET_TITLE_REFRESH=1`, and `MEM_DISTILL=1`) also force worker behavior. A main marker or default must never override any worker marker.
- Worker bootstrap retains deterministic safety and task-contract surfaces: write/core/spec/artifact/worktree/permission guards, capability/mode/QA routing, explicit status/prompt-signal calls, file-only handoff, liveness, and verification. It omits automatic memory injection, briefing, turn counters, SessionEnd sync/curation, title generation, token-budget commentary, and interactive-pane state publication. Memory recall remains an explicit acting-agent decision.
- Every repo-owned background model launcher and all three dispatch wrappers set the portable worker marker before process creation. Runtime hooks and preflight session-end/turn-nudge commands enforce the same boundary independently so a stale wrapper or inherited compatibility environment fails closed. Worker lifecycle hooks are silent no-ops and do not advance counters, markers, stamps, or memory state.
- Regression is hermetic and uses no live model: worker-marker cases assert zero worker invocations and zero lifecycle state writes; main-session cases preserve current behavior; runtime projection and physical Claude hook copies are hash-checked after activation.

## 5.15 Cluster M — On-call incident promotion (v20, 2026-07-20)

### 5.15.1 D-43 — Memory leads, live evidence, exact-key recurrence
- An on-call worker may read bounded recent memory mutation events as discovery leads. It must read a selected record in full and corroborate the claim against current source, tests, logs, artifacts, or runtime evidence. Memory is never proposal evidence by itself and remains unchanged.
- The acting agent authors one stable, one-line incident identity. Deterministic proposal code compares only that exact key under the inbox lock. A match appends bounded recurrence evidence and the incoming context fingerprint without changing state, approval provenance, or the stored base; ambiguous duplicates fail closed.
- Named automated collectors (`loop:*`) require an incident key and may advance only to `reproduced` or `proposed`. A collector-bound reproduction requires current context and may rebase only a proposal that has never crossed the human-review boundary. Manual actor behavior remains compatible with the v1 proposal CLI.
- Reviewed and terminal proposals accept recurrence evidence without reopening. Named collectors cannot defer, reject, review, adopt, impersonate `human:*`, activate realizations, edit source/generated output/runtime config, run another model session, or mutate memory. This bounded inbox operation therefore preserves D-42.
- Evidence and top-level history are bounded to 128 items. The on-call report preserves the worklog approval parser contract: each promoted incident is one `## ` finding block containing proposal ID, state, ingest result, live corroboration, and next human decision.

## [library] 공개 API (v3 + v4 추가)
```
mem_write / mem_recall / mem_index_rebuild / mem_inject / mem_sync / mem_export(dump|profile) / mem_import / mem_migrate / mem_lifecycle / mem_project
+ (B2) turn-counter state (hook이 갱신, mem이 읽어 nudge 판정)
+ (I) mem_show / mem_consume / mem_restore
+ (J) mem_log / mem_doctor (+ 내부: write-event append 훅 — 전 변이 경로 공용)
```

## [cli] `mem` 명령
v3 명령 + **v5 신규 `mem profile <aspect>`** (DB type=profile 레코드의 body를 결정론적으로 출력 — sub-agent·CLAUDE.md 트리거의 user_profile 파일 Read 대체). **v14 신규 `mem show <id>`, `mem recall --full [--limit N]`, `mem consume <id>`, `mem restore <id>`**. **v17 retires `mem recall --auto`** because recall relevance is an agent judgment (D-40). **v15 신규 `mem log [--limit/--action/--tier/--actor/--json]`, `mem doctor`** (§5.12). `export --target profile`은 on-demand 사람 열람 캐시용으로만(SoT 아님, sync/analyze-user 자동 wiring 불필요 — 파일 없음). `register-postit`·`.postit-roots`는 **폐기**(post-it.md 파일 제거). B2 turn-counter는 hook+state.

## 5.16 Cluster N — Audit-driven engine hardening (v21, 2026-07-22)

> 계기: 2026-07-22 메모리 체계 전수 감사(사용자 지시 "매우 강하게"). 4-stream 병렬 감사가
> 신뢰성 실측·아키텍처·화석 스윕·OSS 지형을 판정, 사용자 3답(값 확정·remap 승인·추천안
> 일괄)으로 실행. 전 항목 구현·병합 완료 상태의 사후 spec-sync. 산출물:
> `plans/2026-07-22_memory-system-audit/`(감사·verdict), `plans/2026-07-22_pending-drain/`(구현 사이클).

### 5.16.1 D-44 — 빈-스토어 생성 가드 (파생 경로 fail-loud)
- 파생(AGENT_HOME/기본) 해석에서 `memory.db` 부재 시 조용한 빈 DB 생성을 거부하고 해석된
  STORE/DB 경로를 stderr로 출력한다. 명시적 `MEM_STORE`(테스트·격리 환경)와 `MEM_INIT=1`
  (진짜 첫 설치)만 신규 생성을 허용한다.
- 폐쇄한 위험: worktree/drill식 export가 빈 스토어를 만들어 "지식이 존재하지 않는다"는
  거짓 확신을 주던 최고위험 미커버 경로(감사 P2, relocation 선행조건). 회귀:
  `empty-store-guard.test.sh` 4케이스.

### 5.16.2 D-45 — cwd_origin 정규화 불변식 + v6 remap
- absorb/이관 경로는 항상 canonical `project_key` 형태의 `cwd_origin`을 기록한다(legacy
  경로-망글 키 재생산 금지). 스키마 v6 일회성 remap: 비모호 키 102건 정규화(주소 오류 24
  + `claude_setting` 계보 65 + 13), 홈-디렉터리 등 비모호화 불가 90건은 근거와 함께 잔류.
- 효과: 7/15–21 고가치 사용자 교정 기억 24건이 기본 recall에 재가시화(split-brain 해소).
  UPDATE-only(삭제 없음)·idempotent·`pre-remap-v6.bak` 백업. D-22(project_key robust)의
  절단면을 흡수 경로까지 확장.

### 5.16.3 D-46 — 한국어 회수: CJK bigram shadow FTS
- SQLite 3.31(trigram 부재) 제약 하에서 한글/CJK 연속열을 겹침 bigram으로 색인·질의하는
  shadow FTS(`records_cjk`)를 도입 — 한국어 부분문자열이 무순위 LIKE 폴백 대신 bm25
  순위로 회수된다. 영어/토큰 경로 무변경, 1379/1379 parity, 최초 open 시 self-healing
  backfill. `MEM_NO_TRIGRAM` 비활성 후크 유지.
- 검증: retrieval-eval 하네스(TIER2 한국어 프로브 상시화) + `mem_repairs_v15` 스위트.

### 5.16.4 D-47 — dump 미러 내구성: plain commit + `mem maintenance`
- `_commit_dump`는 amend-rolling을 폐기하고 plain commit을 쓴다. git 실패는 삼키지 않고
  stderr 1줄 경고(rc+tail)로 보고한다(비치명 유지). 신설 `mem maintenance [--squash-days N]
  [--apply]`: N일 이전 first-parent 이력 squash + reflog expire + gc — 운영자 실행 전용,
  dry-run 기본, push 안 함.
- 계기(사건 기록): 7/14 고아 `index.lock`(0바이트)이 모든 dump commit을 rc=128로 죽이고
  실패가 침묵 흡수되어 **재해복구 미러가 8일간 사망** — 복구 과정에서 원격 전용 169건 중
  168건은 deleted-records로 정당 삭제 확인, 진짜 유실 1건(onedrive 피드백)은 정식 경로로
  복원. amend 루프의 고아 blob 축적(406MB)은 squash+gc로 5.1MB로 정리. D1(dump=재해복구
  미러) 계약의 실질 복원.

### 5.16.5 D-48 — pending 배수(drain) 정책 (Cluster I 연장)
- `mem doctor`: 정체 pending을 나이순(oldest-first)으로 노출(기존 `[WARN] stale-pending:`
  prefix·exit 계약 보존). `mem maintenance --drain-pending [--pending-stale-days N]`:
  consumed 레코드만 graveyard 백업 후 정리(--apply), N일 초과 정체 pending은 **보고 전용**
  폐기 후보. dry-run 기본.
- 불변식: D5(gc만 사람 게이트)·D-35(파괴 경로 fail-closed) 보존 — pending 자동 삭제 경로는
  어떤 형태로도 존재하지 않는다(회귀로 봉인). CLI 표면 추가는 [cli] 모드 계약에 포함.
- 구현 provenance: 신규 unit 파이프라인 정식 사이클(autopilot-code standard,
  `rt-04b88e3110f2c2f0`, 6노드 marker 완주)로 구현 — dogfood 겸 인도.

## 데이터 모델
기존 records v4 15컬럼에 v14 `delivery_state`를 추가한 schema v5. `records_fts` FTS5 + trigram 보조 + `idx_records_scope`; `dump.jsonl` 결정론적 export/import는 delivery_state를 round-trip하고 구 dump는 heuristic backfill한다. profile = type=profile 레코드(body=aspect 전문), source=`user-profile:<stem>` (A2 파일명 도출 근거).

## Non-goals
- 외부 메모리 서비스(Honcho/Turso/libSQL 원격) — **로컬 only**.
- **profile cold-start 자동화** — 정체성 corpus의 deliberate seed는 사람이(garbage-in·consent 경계). 단 steady-state drift는 자동(B 연계).
- Memory does not automatically rewrite settings or governing principles. Automated memory mutations still require an agent-backed semantic decision plus mechanical validation.

## 확정 결정 (사용자 lock 2026-06-15)
- v3: D-1~D-7 (삭제정책·post-it alias·user_profile view·hook·SoT=SQLite·저장소분리·통합깊이).
- **v4 신규**:
  - **D-8 (결정론 우선)**: 결정론·SW 가능 요소는 코드로 대체, agent 판단 최소화 (§0.5, cross-cutting).
  - **D-9 (파일 메커니즘 제거, Option 2)**: user_profile/·post-it.md 별도 파일 제거, DB가 유일 SoT·유일 읽기 소스. sub-agent는 `mem profile`/`mem recall`로 DB 직접 읽기. analyze-user·/post-it DB authoring. (§4)
  - **D-10 (Hermes 잔여 port)**: session_search 자율호출 + turn-counter 자기회고, 둘 다 결정론-우선 (§5).
- **v6 신규 (Cluster C — 세션 자동 distillation, §5.5)**:
  - **D-11 (harness-agnostic source)**: 세션 raw log 흡수를 pluggable `ingest_session(source)`로 추상화. 현재 adapter = Claude Code jsonl 1개, 미래 하네스는 adapter만 추가 (지금 미구현·자리만).
  - **D-12 (SessionEnd distiller)**: SessionEnd hook이 detached `claude -p`로 세션 jsonl 읽어 working/durable로 distill. 재귀 가드 `MEM_DISTILL=1`. 증분 marker 스코프.
  - **D-13 (in-session 증분 consolidation)**: turn-nudge 확장 — N턴마다 delta만 정리(요약 추가 / 해결분 prune). **v7: 메인 아니라 외부 detached distiller 분사**(D-12와 같은 worker, 메인 load 0). D-12와 상보(cold-close 구멍 차단).
- **v7 신규 (D-13 외부화 + distiller sonnet + 보안)**:
  - **D-13 개정**: in-session 정리를 메인 에이전트 → **외부 detached distiller 분사**로(메인 turn 보존, 사용자 결정). 두 트리거(turn-counter·SessionEnd)가 같은 distiller·marker 공유. 재귀가드 두 hook 다 + 세션당 lock.
  - **distiller 모델 = sonnet** (`claude-sonnet-4-6`, haiku 아님).
  - **D-14 (distiller 권한 하드닝)**: distiller 권한을 `mem.py` 명령만으로 제한 시도 → **v8 에서 무력 실측·폐기**(아래).
- **v8 정정 (D-14 재설계 — 라이브 검증 발견)**:
  - **D-14 (no-tools + 스크립트 실행)**: v7 의 `--allowedTools` mem.py-제한이 settings.json blanket `Bash` allow + additive 의미로 **무력**(임의 명령 실행 실측). → distiller LLM 에서 도구를 _전부 제거_(`--disallowedTools`), 구조화 출력(JSON-lines)만 받아 **dispatch 스크립트가 검증 후 `mem add` 직접 실행**. LLM 판단·코드 실행(§0.5). injection 이 속여도 명령 실행 물리 불가. acceptance gate = `date>>file` 류 실측 차단.
- **v9 신규 (Cluster D — 결정론-first lifecycle, §5.6)**:
  - **원칙**: 추가(가역) 판단 → 외부 에이전트 offload / 삭제·정리(비가역) 판단 → 메인 직접. (Hermes 도 consolidation=메인.)
  - **D-15 (recall 자동주입 hook)**: B1 instruction → 모든 tracked/project prompt를 동일한 content-based threshold로 평가하는 UserPromptSubmit hook. 고정 자연어 신호어와 phrase-dependent confidence는 없음.
  - **D-16 (정리 후보 메인 노출)**: lifecycle 의 durable near-dup(+옵션 capacity·만료임박 working)를 `mem inject` 에 노출 → 메인이 consolidate/prune/graduate. 死 dup-flag 부활.
  - **D-17 (TTL backstop·삭제=메인)**: distiller add-only 확정. working prune/graduate·durable consolidation=메인. TTL=deterministic 안전망(2차). **→ v10 Cluster E 에서 정정: 삭제=세션끝 opus distiller.**
- **v10 신규 (Cluster E — 큐레이션 단순화 + audit P0 하드닝, §5.7)**:
  - **D-18 (큐레이션 단순화)**: 세션끝 distiller = **opus 풀 큐레이터**(add+consolidate+strength+prune), N턴=sonnet add-only, 메인 housekeeping 0. D-17 "삭제=메인" → "삭제=세션끝 opus"(opus capable + full context + dump 복구 안전망 + worst=비효율). no-tools 유지, 출력=action JSON(add/reinforce/merge/prune), script 검증·실행.
  - **D-19 (strength)**: records 에 strength+last_accessed 칼럼. dedup=reinforce(재출현=중요도). exact=script 결정론, fuzzy=script flag→opus 병합. strength→injection·recall 랭킹·decay.
  - **D-20 (폭증 방지)**: add-time dedup(durable snapshot 주입)·durable soft-ceiling 트리거·injection budget strength top-K·cold-decay.
  - **D-21 (project_key robust)**: remote URL→git-common-dir→.claude-project-id 마커→cwd. worktree·이동 오펀 해소. fail-safe·고아 탐지·마이그레이션.
  - **D-22 (recall engine)**: single phrase → multi-term OR+bm25+top-K+strength. The historical automatic relevance classifier is retired by D-40; ranking remains for explicit queries.
  - **D-23 (내구성)**: dump 자동 commit(삭제 복구 안전망)·import 멱등·user_version 게이트·INJECTION_PAT persist(anti-poisoning).
  - **D-24 (E-7 폐기·model-agnostic=D-11)**: 로깅 프록시 redundant 폐기(하네스는 어차피 로그 남김→adapter 만). + graduate(working→durable) opus 가 수행.
- **v11 신규 (Cluster F — 루프↔메모리 환류, §5.8)**:
  - **D-25 (루프 자율성 재정의)**: "루프는 일을 하지 않는다" 폐기 → "되돌림 가능+명백 = 무인 직접 처리+전수 보고 / 그 외 = 아침 논의". 가드: 되돌림 보장(graveyard·git)+전수 보고 = "사전 승인"을 "되돌림 가능+사후 통보"로. loops/README·DESIGN_PRINCIPLES·oncall.md 동기화.
  - **D-26 (아침 논의 데스크)**: 당직 이후 cwd==~/.claude 그날 첫 발화 → UserPromptSubmit hook 브리핑 주입(밤 처리 요약+논의 안건). SessionStart 아니라 '그날 첫 상호작용'(세션 유지 환경). '당직 처리해줘' 발화 트리거 승격.
  - **D-27 (curator 산출물 대조 적극 prune)**: SessionEnd opus 입력에 ARTIFACTS(git/plans/spec) DATA 블록 + prune 지침 '적극'. 죽은 working 조기정리(21일 TTL 안 기다림)+명백한 durable 정리. 안전 3겹(snapshot-id 화이트리스트·graveyard·DATA 라벨). /clear 도 SessionEnd 발동(matcher '*') 확인.
  - **D-28 (제도화 승격 채널; v17 D-40로 semantic gate 수정)**: bounded visible durable evidence → 아침 논의 안건 → agent가 맥락으로 종착지(문서/hook/drill/기타/메모리 유지) 판단 → 반영·검증 후 prune 여부도 agent가 판단. record type/strength는 자동 승격·정리 규칙이 아님.
  - **D-29 (루프 복원력, ✅ main b95b9a9)**: lib.sh PATH 보정(cron v20 node)·run_claude_retry(401/5xx 재시도, session limit ABORT)·oncall exit code 생존체크.
- **v13 신규 (Cluster H — memory adapter-parity 불변식, §5.10)**:
  - **D-30 (session-end 2-tier adapter-agnostic)**: increment+curate 2-tier 는 모든 어댑터의 session-end 계약 — 미실현 어댑터는 명시 신고 의무, "matches" 표현은 curate 축 성립 시만 (감사 P-12).
  - **D-31 (dump mirror push 계약)**: SessionEnd sync = `mem.py sync` + `MEM_DUMP_PUSH=1` — 어댑터 생략 시 원격 mirror drift (감사 P-10).
  - **D-32 (portable dispatcher 계약)**: distill worker 는 `mem-distill-dispatch.sh` 계약 경유 — 재구현 시 mode/model routing·snapshot whitelist·lock·재귀가드 보존 의무 (감사 P-13·P-25·P-36).
- **v14 신규 (Cluster I — retrieval usability, §5.11)**:
  - **D-33~D-36**: `show`/`recall --full` access, bounded retrieval telemetry, and `delivery_state`-based pending handoff protection. The automatic recall portion is retired by D-40.
- **v15 신규 (Cluster J — 쓰기 관측성+전수 진단, §5.12)**:
  - **D-37 (쓰기 이벤트 저널)**: 전 변이 경로 → write-events.jsonl (XDG state, bounded 256KB/500줄, **fail-open** — graveyard 는 fail-closed 불변). D-34 recall-events 와 읽기/쓰기 대칭.
  - **D-38 (`mem log`)**: 저널 tail 1급 조회 (--limit/--action/--tier/--actor/--json, 기본 20건). stats 는 불변(스냅샷), log 는 흐름.
  - **D-39 (`mem doctor` + oncall 편입)**: read-only 전수 진단 9항목(integrity·FTS 정합·schema 불변식·working 비대·stale pending·ceiling·graveyard 정합·dump 신선도·워커 건강) + exit code. 새 loop 없음 — oncall 항목 1개. 조치 권한 = D-18 큐레이터 불변(doctor 는 진단만). 소비자 = fleet F-19·oncall·사용자.
- **v17 신규 (Cluster K — agent-owned semantic memory judgment, §5.13)**:
  - **D-40**: semantic memory choices belong to the acting agent. Automatic prompt classification and recall injection are retired; deterministic code is limited to storage/retrieval mechanics and safety boundaries. D-15 and the automatic portion of D-34 are historical only.
- **v18 신규 (Cluster L — background-model storm containment, §5.14)**:
  - **D-41**: all automatic distill paths share an atomic global concurrency pool(default 2/hard max 4), persistent 10-minute start budget(default 4/hard max 8), `.distill-disable` kill switch, stale-lease recovery, and adapter/runtime hash parity. Per-session locks remain necessary but are explicitly insufficient as a global cost boundary.
- **v19 신규 (D-42 — main/worker lifecycle boundary, §5.14)**:
  - **D-42**: automatic model-backed lifecycle belongs only to the interactive main session. All dispatch/title/distill/loop workers export `AGENT_SESSION_ROLE=worker`; compatibility markers also fail closed. Workers keep deterministic safety and task routing but never inject memory/briefing, increment distill counters, run SessionEnd sync/curation, summarize titles, publish main-pane state, or emit token-budget context.
- **v20 신규 (D-43 — on-call incident promotion, §5.15)**:
  - **D-43**: recent memory mutations are agent-evaluated leads only. Full-body read plus live corroboration precede a guarded offline proposal write; exact incident keys append bounded recurrence evidence, named collectors stop at `proposed`, and no collector may cross a prior human decision or run automatic memory lifecycle.

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
4. **Cluster C (세션 자동 distillation)** — autopilot-code --mode dev, worktree 브랜치:
   - ✅ **v6 구현·머지 완료** (main `e491241`): `ingest_session(source)` + jsonl adapter (D-11) / 공유 marker 헬퍼 / `mem distill <sid>` / SessionEnd distiller + 재귀가드 (D-12) / turn-nudge 확장 (D-13). 테스트 distill 36 + turn-nudge 11.
   - ✅ **v7 구현·머지 완료** (main `fab5b46`): ① turn-nudge → detached distiller 분사(D-13 외부화) ② D-12·D-13 통일 dispatch·세션 lock ③ 모델 sonnet ④ 재귀가드 turn-counter 확장. 테스트 distill 37+turn-nudge 12+dispatch 17.
   - ✅ **v8 구현·머지·ENABLE 완료** (main `cd9f220`): D-14 no-tools(`--disallowedTools`)+스크립트 mem add 재설계. acceptance(control 생성 vs disallow 차단)·env-상속·ghost-marker·e2e(84줄→6레코드) 검증 후 `MEM_DISTILL_ENABLE=1` 켜짐(신규세션부터 가동).
5. **Cluster D (결정론-first lifecycle 정비, v9 신규)** — autopilot-code --mode dev, worktree:
   - **D-15 (historical, retired by D-40)**: the automatic prompt-recall hook is no longer registered.
   - **D-16**: `mem inject` 에 "정리 후보" 섹션 — lifecycle 의 durable near-dup(+옵션 capacity·만료임박 working) 노출. `mem lifecycle` 의 dup 탐지 재사용(read-only projection).
   - **D-17**: distiller add-only 유지(무변경). CONVENTIONS §7 + CLAUDE.md §2 에 "add=외부·삭제=메인, working 졸업=메인, TTL=backstop" 명문화.
6. **Cluster E (큐레이션 단순화 + audit P0 하드닝, v10 신규)** — autopilot-code, worktree, **phase 분할 권장**(한 사이클에 다 X):
   - **Phase E-α (DB 하드닝 기반)**: user_version 마이그레이션 프레임 + strength/last_accessed 칼럼 + project_key(remote→git-common-dir→marker→cwd) + cwd_origin 마이그레이션·고아 탐지. (다발 schema 라 user_version 선행 — audit C5.)
   - **Phase E-β (recall·내구성)**: recall 엔진 교체(multi-term OR+bm25+top-K+strength, corpus-based term filtering) + dump 자동 commit·import 멱등·INJECTION_PAT persist.
   - **Phase E-γ (큐레이션 단순화)**: 세션끝 distiller opus 풀 큐레이터(action JSON add/reinforce/merge/prune + script 실행) + N턴 sonnet add-only + 폭증 4겹(durable snapshot 주입·ceiling 트리거·budget·cold-decay) + graduate. 메인 housekeeping 0. v8 no-tools 보안 유지·acceptance 재검증.
   - E-7(프록시) 구현 없음 — D-11 adapter 원칙으로 충분.
7. **Cluster F (루프↔메모리 환류, v11 신규)** — autopilot-code, worktree, phase 분할:
   - ✅ **선결 버그 D-29 머지 완료** (main `b95b9a9`): `loops/lib.sh` 신규 + study/oncall 수정 (cron node PATH·재시도·생존체크).
   - **Phase 1 (D-27 curator 산출물 대조)**: `hooks/mem-distill-dispatch.sh` 에 ARTIFACTS(git log·plans done·spec phase) DATA 블록 캡처·주입 + curate 프롬프트 prune 지침 적극화. mem.py 에 산출물 캡처 헬퍼(`curate-artifacts` 류). 안전 3겹 유지·acceptance 재검증.
   - **Phase 2 (D-26 아침 데스크)**: 신규 `hooks/mem-briefing-inject.sh`(UserPromptSubmit, cwd==~/.claude AND 당직후 그날 첫 발화 게이트 → 밤 처리 요약+논의 안건 inject) + 상태 마커(`.briefing-<date>`) + settings.json 배선. CLAUDE.md '당직 처리' 발화 트리거 → 자동 승격.
   - **Phase 3 (D-28 승격 채널; v17 D-40 supersession)**: all visible durable records의 bounded read-only evidence + 아침 안건 제시 + agent-owned 종착지·prune 판단. fixed `convention|lesson` type filter는 폐기.
   - **D-25 원칙 문서화**: `loops/README`·`DESIGN_PRINCIPLES`·`oncall.md` "보고만"→"되돌림가능+명백=처리+보고" 동기화. **post-it 역할 재검토(§5.8.6)**: distiller 와 중복 — 별도 결정.
8. **Cluster H (memory adapter-parity, v13 신규)** — autopilot-code --mode dev, worktree (codex-adapter-parity 감사 Phase 3 과 동일 사이클로 인계 가능):
   - **D-30/D-32**: Codex `distill-worker.sh` 를 portable `mem-distill-dispatch.sh` 계약으로 정렬 — session-end 를 curate mode(+snapshot 캡처·whitelist)로, turn-nudge 는 increment 유지. 불가 시 ADAPTATION 에 "increment-only" disclosure 로 문구 정정 (P-12 overclaim 해소는 두 경로 중 하나 필수).
   - **D-31**: Codex `preflight.sh session-end` 에 `MEM_DUMP_PUSH=1` 추가 (P-10).
   - **D-32 안전층**: increment 프롬프트의 mutation action 나열 제거 또는 snapshot whitelist 적용 (P-25) + per-mode 모델 tier (P-36).
9. **Cluster I (retrieval usability, v14 신규)** — autopilot-code, worktree, standard QA:
   - **D-33**: show/full/limit + visibility fence + memory-scout/README 동기화.
   - **D-34 (historical, retired by D-40)**: automatic prompt classification removed; explicit retrieval and bounded access telemetry remain.
   - **D-35**: schema v5 migration/import, consume/restore, pending fail-closed gates(prune/merge/delete/lifecycle+curator snapshot), 실사고 fixture 회귀.
   - **D-36**: SessionStart cap 유지, 배포 후 recall funnel 재관찰.
10. **Cluster J (쓰기 관측성+전수 진단, v15 신규)** — autopilot-code, worktree, standard QA: **D-37 저널**(mem.py 변이 경로 공용 append 훅 + rotation, fail-open) → **D-38 `mem log`** → **D-39 `mem doctor`** + `loops/oncall.md` 항목 1개. fleet F-19(agent-fleet-dashboard spec §4.6)가 저널 포맷을 소비 — 포맷 변경 시 양 spec 동기. F-19 구현은 fleet 사이클 별도(파일 표면 비겹침 — 병렬 가능, 저널 부재 시 graveyard-only degrade 계약).
