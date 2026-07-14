# Memory — Unified Store (canonical)

> Split from `CONVENTIONS.md` on 2026-06-23. Memory is an independent subsystem. Preserve the §7 numbering. This is the single source; the spec is `<artifact-root>/spec/prd.md` (`.agent_reports` first, legacy `.claude_reports` compatible), and the implementation is `tools/memory/mem.py`.

## §7. Unified Memory System (canonical)

> Three former memory surfaces—short-lived post-its, durable learned memory, and the global user profile—share **one portable store**. The store is infrastructure, not a semantic policy engine. **The agent decides contextually what is worth storing, retrieving, promoting, merging, or pruning.** Deterministic code owns only mechanical concerns such as schema validity, scope isolation, lifecycle execution, pending protection, bounded I/O, telemetry, and recovery. Behavioral rules belong in the runtime bootstrap, `CONVENTIONS`, `WORKFLOW`, or Skills rather than memory.

### §7.0. store 아키텍처 (개요)

- **store** = `<agent-home>/memory/memory.db` (SQLite WAL = 진실원천 SoT, FTS5 내장) + `dump.jsonl`(결정론적 텍스트 mirror, git추적). **전용 private memory repo** 로 분리 — config repo(`<agent-home>`)에선 `memory/` gitignore. 레코드 = `tier`(working 단기 / durable 장기) × `scope`(project / global) × `type` × `delivery_state`(ordinary / pending / consumed). (2026-06-15 DB-as-SoT 전환 — 구 markdown 원본 SoT + `.index.db` 파생색인 모델 대체. 복원 = `mem import dump.jsonl`.)
- **store tier × scope** (DB 가 단일 SoT — 파일 면은 on-demand 뷰):

  | 채널 | store tier/scope | 동기화 |
  |---|---|---|
  | `post-it` (DB working tier alias — `/post-it` 스킬이 author) | working/project | `/post-it` → `mem note`/`mem add` → SessionEnd `mem sync` |
  | `projects/<cwd>/memory/` (내장 file 메모리 — 직접 write 는 `builtin-memory-guard.sh` hard-block) | durable/project | 다른 세션·하네스의 _stray_ write 만 SessionEnd `mem sync` 안전망 흡수 (주 durable 학습은 외부 distiller `mem add` — Cluster C) |
  | DB `type=profile` 레코드 (cross-project 프로필 SoT) | durable/global (type=profile) | `analyze-user` → `mem add` → `mem sync`; `user_profile/*.md` = on-demand `mem export` 사람 열람 캐시 (SoT 아님) |

- **Harness integration**: `mem inject --hook` may expose a bounded working+durable+profile summary at SessionStart. Adapters whose start event repeats on resume, clear, or compact may keep that opt-in. SessionEnd runs `mem sync` plus bounded `MEM_DUMP_PUSH=1` mirroring (D-31). SessionEnd and turn-counter triggers may launch a no-tools distiller agent through `mem-distill-dispatch.sh`; the agent makes semantic choices and the dispatcher validates and executes structured actions (D-12–D-14). Prompt-submit hooks do **not** classify every prompt for recall. Retrieval is agent-initiated through `mem recall` or `recall.sh` (D-40). `builtin-memory-guard.sh` keeps DB writes on the unified `mem` path. Hook registration remains adapter-native.
- **회상**: `tools/memory/recall.sh` = `mem recall` thin wrapper — store FTS5 + `--full`(전문) + `--limit 1..100` + `--sessions`(raw 대화 jsonl) + `--all`(전 scope). ID를 이미 알면 `mem show <id> [--all]`로 전문을 직접 읽는다. 트리거 = runtime adapter bootstrap 의 도메인 트리거 + §7.4.
- **CLI**: `mem {add, note, recall, show, consume, restore, index, sync, inject, export, import, migrate, lifecycle, delete, project, stats, profile, distill, register-postit}` + **γ 큐레이터 `{curate-snapshot, reinforce, merge, prune, graduate, reattribute}`**. (`show <id> [--all]` = visibility fence 안의 metadata+body 전문; `consume <id>` = pending handoff의 명시적 소비 전이; `restore <id>` = graveyard 단건 복구; `profile <stem>` = DB type=profile 레코드 body 출력 — read-only; `export --target dump|profile` = DB→git mirror / on-demand 사람 열람 캐시 (SoT 아님); `import <dump.jsonl>` = 복원; `delete <id>` = 단건 결정론 삭제(records+FTS5 3-table) — pending은 consume 또는 명시 force 전 거부; `register-postit` = deprecated/legacy-migration-only, skills 에서 더 이상 호출 안 함.) **γ 큐레이터 서브커맨드**(D-18) — `curate-snapshot`(read-only, deep curator 입력 DATA: durable/working snapshot+SIGNALS; pending은 `PROTECTED PENDING`에 노출하되 destructive `IDS:`에서 제외) / `reinforce`(strength++, E-1) / `merge`(strength 합산+canonical 외 graveyard+삭제, 원자적) / `prune`(graveyard 백업 **성공 후** 삭제, S1 fail-closed) / `graduate`(working→durable, E-6) / `reattribute`(고아 재귀속, 역게이트). 전부 화이트리스트 게이트(현 프로젝트만; profile·global·타프로젝트·존재안함 거부). distiller(no-tools)는 action JSON 만, script(shell=False)가 argv 로 호출.
- **Invariant (D-18, D-35, D-40)**: semantic memory decisions are made by the acting agent—main, distiller, or curator—using the available context. Scripts may validate action shape, visibility, identity, transaction safety, pending protection, graveyard recovery, and bounded lifecycle mechanics; they do not decide relevance through keyword lists, content categories, confidence thresholds, or fixed phrases. Unconsumed pending handoffs remain fail-closed against destructive operations until an explicit `consume` transition.

> Sections §7.1–§7.3 define the semantic/mechanical boundary for mutations; §7.4 defines agent-initiated retrieval.

### §7.1. Semantic decisions belong to the agent

There is no deterministic promote/skip classifier. The acting agent judges whether a memory operation is useful in context, including whether information is durable, non-obvious, recoverable elsewhere, stale, or merely ephemeral. Preferences, conventions, corrections, rationale, references, handoffs, and current code are considerations—not hard categories or scoring rules. The same boundary applies to retrieval and curation: scripts offer candidates and safe operations, while the agent supplies meaning.

### §7.2. Write mechanics (add / replace / remove) and deduplication

- After an agent decides to write, inspect visible memory and prefer updating the canonical record over creating an obvious duplicate. Fuzzy similarity is candidate evidence for the agent, not an automatic semantic verdict.
- After an agent determines that a memory is stale, use the guarded remove/merge path so recovery metadata is preserved.
- Related records may use `[[name]]` links stored in the DB `links` column. FTS5 indexing happens mechanically on insert; `MEMORY.md` remains a legacy projection view.
- Code may report capacity pressure and similarity candidates. The curator agent decides whether and how to consolidate them.

### §7.3. Agent-backed mutation boundary

Purely deterministic monitors may surface candidates but cannot promote, skip, merge, or prune based on semantic rules. A user-directed post-it flow or an agent-backed distiller/curator may perform the mutation. The script then enforces the mechanical action contract and recovery boundary.

### §7.4. Recall — on-demand 회상 (canonical, T1 / Hermes session_search 벤치마킹)

`mem inject` may provide a bounded SessionStart summary of working, durable, and profile records. The default 2,000-character/15-bullet cap remains. When more history could materially help the current work, the agent chooses a query and invokes the read-only retrieval helper. Retrieval is information access, not handoff consumption: `show`, explicit recall/full, and SessionStart injection do not change `delivery_state`; only `mem consume <id>` does. Bounded telemetry distinguishes `explicit-recall`, `show`, `session-inject`, and `consume` without storing raw prompts.

| helper | 용도 | 비고 |
|---|---|---|
| `tools/memory/recall.sh "<query>" [--full] [--limit 1..100] [--all] [--sessions]` | `mem recall` thin wrapper — store FTS5 색인(bm25 랭킹) 검색, 색인 없으면 LIKE/rg fallback. `--full`은 같은 ranked ID의 snippet을 body 전문으로 교체하고 기본 출력은 유지한다. `--sessions` = raw 세션 transcript(`*.jsonl`)까지 | 기본 limit 20. per-cwd 격리 = 기본 현 cwd. cross-cwd·raw 는 명시 플래그 시만. |
| `python3 <agent-home>/tools/memory/mem.py show <id> [--all]` | 이미 찾은 record id의 metadata+body 전문을 원문 줄바꿈 그대로 출력 | 기본 current project+global visibility; `--all`만 타 project를 허용. `injection_flag`는 항상 제외하고 비가시 ID는 generic not-found. |
| `tools/memory/index-check.sh [dir] [--fix]` | *legacy* `projects/<cwd>/memory/` 의 `MEMORY.md` *텍스트 인덱스* drift 점검 전용 (누락·고아). `--fix` = 누락 포인터 _append-only_ | store FTS5 색인(`memory.db` 내장)은 `mem index` 관할 — 별개 대상. 기존 큐레이션 줄 보존 |

**두 검색면 (Hermes session_search 의 두 절반)**: (1) _정제 메모리_(store durable+working, 기본) = `mem recall` 이 SQLite FTS5(bm25 랭킹)로 검색, 색인 없으면 LIKE/rg fallback. snippet에서 판단이 안 되면 `show <id>` 또는 `recall --full --limit N`으로 즉시 전문을 읽는다. SQLite나 `dump.jsonl` 직접 조회는 정상 retrieval 경로가 아니다. (2) _raw 세션_(`*.jsonl`, `--sessions`) = 메모리로 정제 안 된 과거 대화까지, 노이즈 크니 정제 메모리로 안 나올 때만 보조로.

**Agent-initiated recall** — The agent decides whether prior context may materially improve the current judgment. No fixed signal words, mandatory topic list, prompt classifier, or category-to-recall rule substitutes for that contextual decision. Once the agent chooses to recall, search curated memory first, widen to `--all` or `--sessions` only when useful, and cross-check retrieved claims against current code or artifacts because memory can be stale.

**인라인 vs memory-scout 이원화**:

- **Inline recall**: for a simple agent-chosen search, run `tools/memory/recall.sh "<query>"` directly for one or two queries. If a hit needs more context, follow with `mem show <id>` or `recall --full --limit N`.
- **memory-scout capability**: read-only 메모리 정찰. 심층 탐색(raw 세션 탐색, 다각 쿼리, 본문 다량 열람, cross-cwd)이 필요하면 이 capability 로 위임한다. 절차 = 좁은 recall(동의어·영/한) → hit ID의 `show`/소수 hit의 `--full` → 미스 시 `--all` → raw 세션 순 확대 → live 코드 교차검증 한 줄. DB/`dump.jsonl` 직접 우회 금지. 반환은 **15줄 이하 고정**: verdict(있음/없음/애매) + 핵심 인용 최대 3개 + record id + 적용 지침 1줄. 쓰기 전면 금지(`add`/`note`/`consume`/`restore`/`delete`/`reinforce`/`merge`/`prune`/파일 수정 금지).

> per-cwd 격리는 유지된다 — `--all` 은 명시 요청 자리(cross-project 회상)에서만. 인덱스 mass `--fix` 는 live 사용자 데이터(`projects/` gitignored)라 _사용자 흐름_ 에서 실행(자동 자리에선 누락 _보고_ 까지 = oncall 후속 후보).

### §7.5. Mechanical scaffold — retrieval, curation candidates, and pending protection

lifecycle 주변 판단 구조: deterministic code may detect mechanical conditions and expose candidates; the deep curator agent decides the semantic action. Scripts execute only validated actions (D-18, D-40).

**D-40 agent-owned semantic memory judgment (supersedes the automatic part of D-15/D-34):**
- Prompt-submit bridges do not send every user prompt through a semantic classifier and do not inject threshold-qualified recall results.
- `mem recall` and `tools/memory/recall.sh` remain explicit retrieval tools. Ranking, tokenization, scope fences, limits, and access telemetry organize results after the agent has chosen to search; they do not decide whether recall is relevant.
- `mem recall --auto` is retired. `hooks/mem-recall-inject.sh` remains only as a fail-open compatibility no-op for stale installed projections and is not registered by current adapters.
- `$XDG_STATE_HOME/agent-memory/recall-events.jsonl` remains bounded local telemetry for explicit retrieval and lifecycle access events. Raw prompts are not stored.

**D-16 `mem inject` 정리신호 섹션 (SessionStart, 읽기 전용 projection — γ/D-18 에서 informational 로 축소):**
- `mem inject --hook` 기존 블록 이후, 비어 있지 않을 때만 `## 🧹 정리 신호 (세션끝 deep curator 가 처리 — D-18, 메인 조치 불요)` 섹션 추가: cwd-scoped durable near-dup 그룹 + capacity 초과(`durable > soft_ceiling=80`) + 만료 임박 working(`<= 3일`). 이 섹션도 SessionStart 전체 cap 안에서 기본 2줄만 노출된다. 모두 read-only — zero deletes / zero flag writes.
- **γ/D-18**: 이 섹션은 이제 **informational** — 메인은 *조치하지 않는다* (메인 housekeeping 0). 실제 consolidate/prune/merge/graduate 는 **세션끝 deep curator**가 `curate-snapshot`(durable snapshot+SIGNALS) 을 보고 action JSON 으로 수행하고, `mem-distill-dispatch.sh` 의 script(shell=False)가 화이트리스트 게이트로 검증·실행한다. (D-17 "삭제=메인" → D-18 "삭제=세션끝 deep curator" 이전; 정당화: deep role capability + full context + worst=비효율(손실 아님, graveyard+dump 복구) + prune/merge 화이트리스트·fail-closed graveyard.)

**D-35 미소비 handoff/thread 보호 (delivery state):**
- `delivery_state=ordinary|pending|consumed`. 새 `type=handoff`와 명시 `--requires-consume` thread는 pending이며, `mem consume <id>`만 일반 pending→consumed 전이를 수행한다. source upsert/body dedup은 pending을 단조 보존해 ordinary 재기록으로 낮추지 않는다. `show`, recall/full, and inject are non-consuming. When retrieval exposes `[pending:<id>]`, read the full obligation, apply and verify it, and only then run `mem consume <id>`. A working pending record does not expire before consumption; its 21-day TTL restarts at consumption.
- `curate-snapshot`은 pending을 `PROTECTED PENDING`으로 보여주되 destructive `IDS:`에서 제외한다. `prune`·`delete`·`merge`·`lifecycle --apply`도 실행 직전 DB 상태를 다시 확인하고 pending을 fail-closed로 거부/보존한다. pending 하나라도 포함된 merge는 strength 변경과 삭제 없이 전체 취소한다.
- 삭제된 레코드는 action/canonical 메타와 함께 graveyard에 남고 `mem restore <id>`로 단건 복구한다. 자동 consume은 handoff ID가 명시되고 성공 산출물이 의무 반영을 증명하는 좁은 pipeline/post-it 자리만 허용한다.

### §7.6. 사용자 프로필 (type=profile) — aspect ↔ 참조 매트릭스 (canonical)

> `user_profile/README.md` 에서 이전(2026-06-23 — spec v10 D-9 마무리: `user_profile/` 의 매핑 문서를 제거하고 매트릭스를 본 절로 보존). **읽기 소스 = DB** (`mem profile <stem>` = `python3 <agent-home>/tools/memory/mem.py profile <stem>`) — 본 매트릭스는 _어느 agent 가 어느 aspect 를 참조하는지_ 의 매핑일 뿐, aspect 본문 SoT 는 §7.0 표의 DB `type=profile` 레코드(durable/global). **매트릭스 single source = 본 절(§7.6)**; `capabilities/analyze-user.md` 와 각 adapter-native `analyze-user` projection 은 이 절을 참조해야 하며, root `skills/analyze-user/SKILL.md` 는 compatibility reference 일 뿐이다.

| stem (`mem profile <stem>`) | 다루는 영역 | 누가 참조 |
|---|---|---|
| `01_paper_figure_style` | paper figure / 표 / 색 / 폰트 / 사이즈 / metric 묶음 | 자료팀 · 디자인팀 · **연구팀**(figure 인용 양식) · 편집팀 |
| `02_paper_writing_style` | paper 본문 톤 · argumentation · citation | 연구팀 · 편집팀 · **기획팀**(plan 작성 톤) |
| `03_presentation_strategy` | 슬라이드 구성 · 서사 flow · 시각 결정 · 청중 변형 | 자료팀(presentation) · 디자인팀 · 편집팀 |
| `04_analysis_methodology` | 데이터·실험 결과 분석 접근 · 검증 패턴 | 자료팀 · 연구팀 · 기획팀 · **개발팀**(metric·검증) · 편집팀 · **메인 에이전트**(분석 응답) |
| `05_domain_expertise` | 도메인 배경(speech / TF DNN / signal processing) · 용어 선호 | 연구팀 · 자료팀 · 디자인팀 · 편집팀 · **기획팀**(plan 약자) · **개발팀**(변수·함수명 약자) · **메인 에이전트**(발화 약자 인지) |
| `07_coding_convention` | 코드 일관 패턴 — 폴더 구조 / config / prefix / preferred layer / framework / metric set / log·ckpt / seed·reproducibility / naming | 개발팀 · 기획팀(plan 코드) · 메인 에이전트(autopilot-lab Step 0 / autopilot-spec Phase 0·2 / autopilot-code 4 원칙) |

> **06 (대화 메타 규칙)** 은 매트릭스 제외 — runtime adapter bootstrap 의 응답 규율이 단일 source (메인 에이전트 전용; sub-agent 는 사용자와 직접 대화 X). `/post-it --scope user` 의 default collab 저장처로 `06_collaboration_style` 레코드 자체는 유지. **07 (코드)** 은 개발팀·기획팀·메인 에이전트만 — 편집팀(wording 영역) 제외. agent 별 3–5 aspect 참조 default (2026-05-26 정리).

**갱신 프로토콜** — aspect 본문은 DB(`type=profile`) SoT, 두 경로: ① `/analyze-user <aspect>` — 과거 산출물(paper / 발표 / code / report) 스캔 → 패턴 추출 → `mem add durable profile --source user-profile:<stem>` 누적(셋업 · 신규 자료 · `--mode update` incremental). ② `/post-it --scope user <aspect>` — 대화 중 발견한 _범용_ 패턴을 durable/global 레코드에 추가.

**참조 패턴** — 각 agent 는 작업 흐름 첫 자리에서 해당 aspect 를 `mem profile <stem>` 으로 읽어 body 를 _default_ 로 따른다(사용자가 그 turn 에 다르게 명시하면 그 자리만 예외). per-project 컨벤션(`analysis_project/code/experiment_conventions.md`)이 1순위, profile 은 2순위 cross-project default. 예: 자료팀 figure → `01·03·04·05` / 개발팀 new-lib → (1순위 experiment_conventions) `07·04·05`.
