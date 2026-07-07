# Memory — 통합 기억 시스템 (canonical)

> CONVENTIONS.md 에서 분리(2026-06-23). 메모리는 독립 서브시스템. **§7 번호·heading 보존**. 단일 출처. spec=`<artifact-root>/spec/prd.md` (`.agent_reports` 우선, legacy `.claude_reports` 호환), 구현=`tools/memory/mem.py`.

## §7. 통합 기억 시스템 (canonical)

> 흩어졌던 3개 기억면(post-it 단기 · auto-memory 장기 · user_profile 전역)을 **하나의 포터블 store** 로 통합 — Hermes Agent 메모리 벤치마킹(2026-06-15). spec = `<artifact-root>/spec/prd.md`, 구현 = `tools/memory/mem.py`. 본 §7 이 단일 출처. **행동양식·운영규율은 메모리가 아니다** — 원칙 문서(runtime adapter bootstrap / CONVENTIONS / WORKFLOW / SKILL).

### §7.0. store 아키텍처 (개요)

- **store** = `<agent-home>/memory/memory.db` (SQLite WAL = 진실원천 SoT, FTS5 내장) + `dump.jsonl`(결정론적 텍스트 mirror, git추적). **전용 private memory repo** 로 분리 — config repo(`<agent-home>`)에선 `memory/` gitignore. 레코드 = `tier`(working 단기 / durable 장기) × `scope`(project / global) × `type`. (2026-06-15 DB-as-SoT 전환 — 구 markdown 원본 SoT + `.index.db` 파생색인 모델 대체. 복원 = `mem import dump.jsonl`.)
- **store tier × scope** (DB 가 단일 SoT — 파일 면은 on-demand 뷰):

  | 채널 | store tier/scope | 동기화 |
  |---|---|---|
  | `post-it` (DB working tier alias — `/post-it` 스킬이 author) | working/project | `/post-it` → `mem note`/`mem add` → SessionEnd `mem sync` |
  | `projects/<cwd>/memory/` (내장 file 메모리 — 직접 write 는 `builtin-memory-guard.sh` hard-block) | durable/project | 다른 세션·하네스의 _stray_ write 만 SessionEnd `mem sync` 안전망 흡수 (주 durable 학습은 외부 distiller `mem add` — Cluster C) |
  | DB `type=profile` 레코드 (cross-project 프로필 SoT) | durable/global (type=profile) | `analyze-user` → `mem add` → `mem sync`; `user_profile/*.md` = on-demand `mem export` 사람 열람 캐시 (SoT 아님) |

- **자체 하네스 (store 가 세션 주입의 source)**: SessionStart hook `mem inject --hook` → store 의 현 cwd working+durable + global profile 을 `additionalContext` 로 주입할 수 있다. 단 Codex처럼 start 이벤트가 startup/resume/clear/compact에서 반복될 수 있는 adapter는 기본 자동 주입을 끄고 명시 opt-in 또는 수동 recall/memory 조회로 낮출 수 있다. SessionEnd hook `mem sync` → 하네스 write 회수 + 색인 재생성. **SessionEnd sync 계약 = `mem sync` + `MEM_DUMP_PUSH=1`(dump.jsonl git mirror push, E-5 내구성 안전망) — adapter-agnostic: 어댑터가 SessionEnd 에서 push 를 생략하면 그 어댑터로 돈 세션의 기억이 원격 mirror 에서 drift 한다(D-31). push 는 5s bounded·never-fatal 이라 세션 종료를 블록하지 않는다.** **SessionEnd + turn-counter(UserPromptSubmit N턴) 두 트리거가 공유**하는 `mem-distill-dispatch.sh` → 세션 transcript 의 공유 marker 이후 구간을 detached fast distiller worker 로 분사해 working/durable 흡수 자동화(adapter realization 은 각 runtime 문서가 소유; D-12/D-13 통일 worker · 세션당 mkdir lock 동시 1개 · 재귀가드 `MEM_DISTILL=1` 세 hook 다 · distiller worker 는 도구 0, JSON-lines 구조화 출력만 내고 dispatch 스크립트가 검증 후 `mem add` 실행(LLM=판단·코드=실행, v8 no-tools — D-14)). Portable shared dispatcher 는 background LLM 비용과 transcript 신뢰경계 때문에 `MEM_DISTILL_ENABLE=1` opt-in 전 no-op 이 기본이다. 단 adapter 가 runtime-native no-tools/action 계약과 recursion boundary 를 검증하고 그 증거를 adapter 문서·테스트에 고정한 경우, 해당 adapter-owned SessionEnd/UserPromptSubmit realization 은 기본 ON 으로 승격할 수 있으며 명시적 opt-out env 를 제공해야 한다. UserPromptSubmit `mem-recall-inject.sh` → 회상 신호어 regex 감지 시 `mem recall` 실행 → `additionalContext` 사전주입(D-15). PreToolUse `builtin-memory-guard.sh` → 내장 file 메모리(`projects/*/memory/`) 직접 Write **hard-block(deny)** → 기억 write 는 `mem` CLI(DB) 단일 경로로 강제. Hook/event registration is adapter-native.
- **회상**: `tools/memory/recall.sh` = `mem recall` thin wrapper — store FTS5 + `--sessions`(raw 대화 jsonl) + `--all`(전 scope). 트리거 = runtime adapter bootstrap 의 도메인 트리거 + §7.4.
- **CLI**: `mem {add, note, recall, index, sync, inject, export, import, migrate, lifecycle, delete, project, stats, profile, distill, register-postit}` + **γ 큐레이터 `{curate-snapshot, reinforce, merge, prune, graduate, reattribute}`**. (`profile <stem>` = DB type=profile 레코드 body 출력 — read-only; `export --target dump|profile` = DB→git mirror / on-demand 사람 열람 캐시 (SoT 아님); `import <dump.jsonl>` = 복원; `delete <id>` = 단건 결정론 삭제(records+FTS5 3-table) — **사용자-개시**(LLM 미개입) 즉시삭제 경로; `register-postit` = deprecated/legacy-migration-only, skills 에서 더 이상 호출 안 함.) **γ 큐레이터 서브커맨드**(D-18) — `curate-snapshot`(read-only, deep curator 입력 DATA: durable/working snapshot+SIGNALS+`IDS:` 멤버십) / `reinforce`(strength++, E-1) / `merge`(strength 합산+canonical 외 graveyard+삭제, 원자적) / `prune`(graveyard 백업 **성공 후** 삭제, S1 fail-closed) / `graduate`(working→durable, E-6) / `reattribute`(고아 재귀속, 역게이트). 전부 화이트리스트 게이트(현 프로젝트만; profile·global·타프로젝트·존재안함 거부). distiller(no-tools)는 action JSON 만, script(shell=False)가 argv 로 호출.
- **불변식 (D-18 갱신)**: 기억 저장 = 자동(품질필터만 — §7.1·§7.2, 사람 승인 게이트 없음). **추가(가역)=외부 distiller/hook 자동 · 삭제·prune·consolidate·merge·graduate(비가역)=세션끝 deep curator**(deep curator role; full context 보유, no-tools+action JSON+script 실행; worst=비효율, graveyard+dump 로 복구가능) · **메인 housekeeping 0**(inject 정리신호는 informational — 메인이 직접 정리/prune 하지 않음) · N턴 distiller=fast add-only worker(fast distiller role) · working TTL(21일)=deterministic backstop(2차 안전망). lifecycle = working 시간만료 / durable consolidate(§7.3 lifecycle). (D-17 "삭제=메인" → D-18 "삭제=세션끝 deep curator" 이전.)

> 위 intro 의 _write 면_ 세부 (무엇을 저장/생략하고 어떻게 쓰는지) 는 §7.1–§7.2, recall 은 §7.4. Hermes `write_approval` 게이트·promote/skip·session_search 벤치마킹(T5/T1).

### §7.1. Promote (저장) vs Skip (생략)

| 저장한다 (promote) | 생략한다 (skip) |
|---|---|
| **preferences** — 사용자 선호·작업 방식 (비자명) | **재발견 가능** — 코드·git 이력·runtime adapter bootstrap 에 이미 있는 것 |
| **conventions** — 코드에 안 드러나는 프로젝트 규약 | **trivial / ephemera** — 이 대화에서만 의미 있는 것 |
| **corrections** — 사용자 교정 (같은 실수 반복 방지) | **행동양식 변경** — → 원칙 문서 자리 (메모리 X) |
| **lessons** — 비자명 결정의 _이유·맥락_ | **진행 맥락·handoff** — → `post-it` 자리 |
| **references** — 외부 자원 포인터(URL·티켓·대시보드) | **stale 확정** — 틀린 것으로 판명 → 저장 말고 기존 것 삭제 |

판단 한 줄: _"다음 세션의 다른 나에게 이게 비자명하게 유용한가, 그리고 코드/이력에서 다시 못 찾는가?"_ 둘 다 yes 면 promote.

### §7.2. Write 연산 (add / replace / remove) + dedup

- 저장 전 기존 메모리 확인 — 같은 사실을 이미 다루는 파일이 있으면 _새 파일 만들지 말고 그 파일 갱신_(replace). 한 사실 = 한 파일(near-duplicate 거부).
- 틀렸다고 판명된 메모리는 즉시 삭제(remove) — 누적 stale 금지.
- 관련 메모리는 본문에서 `[[name]]` 로 링크 (DB `links` 컬럼에 저장). DB INSERT 시 FTS5 가상테이블이 자동 색인 — 별도 `MEMORY.md` 인덱스 포인터 write 없음 (MEMORY.md 는 legacy projection 뷰).
- Hermes 처럼 _capacity 압박 시 consolidation_ 을 원칙으로 — cwd 메모리가 비대해지면 통합·압축(별 파일 난립 대신).

### §7.3. 메모리 _승격_ 제안 한정 (불변식)

oncall self-review nudge(`loops/oncall.md` item 9) 등 _자동_ 자리의 **메모리 승격(promote)·post-it write** 는 후보 **제시까지** — 실제 승격 write 는 사용자 흐름 안에서(`/post-it` 또는 메모리 저장 발화). ※ 이는 _승격_ 축 한정 — 세션끝 deep curator role 의 무인 prune/merge/graduate(§7.0)·루프의 되돌림가능+명백한 무인 정리(D-25, [loops/README](loops/README.md):21 가 "출구는 제안까지" 옛 원칙 폐기)와는 적용 축이 다르다.

### §7.4. Recall — on-demand 회상 (canonical, T1 / Hermes session_search 벤치마킹)

세션 시작 시 자동 또는 명시 opt-in으로 주입되는 것은 `mem inject` 의 DB 요약 블록 (working+durable+profile) — _요약_ 만 본다 (`MEMORY.md` 는 legacy projection 뷰, 주입원 아님). 이 요약은 컨텍스트 비용을 막기 위해 기본 2000자·15개 bullet hard cap(`MEM_INJECT_MAX_CHARS`, `MEM_INJECT_MAX_BULLETS`)을 적용하고, 초과분은 생략 요약과 recall 안내만 남긴다(2026-07-06 토큰 절감). 요약 블록에 안 잡히는 _과거 메모리 본문_ 이 필요한 자리(과거 결정·교정·컨벤션을 _다시 떠올려야_ 할 때)는 읽기 전용 helper 로 능동 검색한다. **읽기 전용 = 정보 제공일 뿐 — recall 자체는 결정·write 아님(무해, §7.3 게이트와 독립).**

| helper | 용도 | 비고 |
|---|---|---|
| `tools/memory/recall.sh "<query>" [--all] [--sessions]` | `mem recall` thin wrapper — store FTS5 색인(bm25 랭킹) 검색, 색인 없으면 LIKE/rg fallback. 현 cwd / `--all`=전 cwd. `--sessions` = raw 세션 transcript(`*.jsonl`)까지 | per-cwd 격리 = 기본 현 cwd. cross-cwd·raw 는 명시 플래그 시만. |
| `tools/memory/index-check.sh [dir] [--fix]` | *legacy* `projects/<cwd>/memory/` 의 `MEMORY.md` *텍스트 인덱스* drift 점검 전용 (누락·고아). `--fix` = 누락 포인터 _append-only_ | store FTS5 색인(`memory.db` 내장)은 `mem index` 관할 — 별개 대상. 기존 큐레이션 줄 보존 |

**두 검색면 (Hermes session_search 의 두 절반)**: (1) _정제 메모리_(store durable+working, 기본) = `mem recall` 이 SQLite FTS5(bm25 랭킹)로 검색, 색인 없으면 LIKE/rg fallback. Hermes 와 동형으로 수렴. (2) _raw 세션_(`*.jsonl`, `--sessions`) = 메모리로 정제 안 된 과거 대화까지, 노이즈 크니 정제 메모리로 안 나올 때만 보조로.

**recall-first 반사** — "메모리에 있을지도 모른다"는 판단이 서는 _순간_ recall 이 1차 행동이다. 창작·스타일 결정·설계 착수 _전_ 선행한다. "나중에 찾아보자" 또는 "일단 진행"은 금지다. recall miss 는 거의 무료이고, 잠복 컨벤션 위반으로 생기는 재작업이 항상 더 비싸다.

**언제 recall 하나** — 작업이 _이 프로젝트의 과거 비자명 결정/선호/교정_ 에 닿는 자리(예: "전에 이 모듈 왜 이렇게 정했더라", 같은 실수 반복 회피)뿐 아니라, **산출물 스타일·형식 신규 결정 자리**에서도 선행한다. 예: spectrogram/figure/표 형식/보고서 레이아웃/명명. 특히 범용 기술처럼 보이는 신규 생성도 프로젝트·사용자 잠복 컨벤션이 자주 있는 자리다. 정제 메모리 먼저 → 안 나오면 필요에 따라 `--all` 또는 `--sessions`. 결과는 _현재 코드_ 로 교차검증한다(메모리는 작성 시점 진실, stale 가능 — 글로벌 메모리 규율과 동일). **단 회상 신호어 자동주입(D-15 `mem-recall-inject.sh` hook)은 별개** — hook 이 신호어 감지 시 결정론적으로 사전주입(메인의 'recall 할까' 판단 제거).

**인라인 vs memory-scout 이원화**:

- **인라인 recall**: 스니펫 1~2쿼리까지. 현재 작업을 시작하기 전 메인 에이전트가 `tools/memory/recall.sh "<query>"` 로 직접 수행한다.
- **memory-scout capability**: read-only 메모리 정찰. 심층 탐색(raw 세션 탐색, 다각 쿼리, 본문 다량 열람, cross-cwd)이 필요하면 이 capability 로 위임한다. 절차 = 스니펫 다각(동의어·영/한) → 미스 시 cross-cwd → raw 세션 순 확대 → 히트 본문만 열람 → live 코드 교차검증 한 줄. 반환은 **15줄 이하 고정**: verdict(있음/없음/애매) + 핵심 인용 최대 3개 + record id + 적용 지침 1줄. 쓰기 전면 금지(`add`/`note`/`delete`/`reinforce`/파일 수정 금지).

> per-cwd 격리는 유지된다 — `--all` 은 명시 요청 자리(cross-project 회상)에서만. 인덱스 mass `--fix` 는 live 사용자 데이터(`projects/` gitignored)라 _사용자 흐름_ 에서 실행(자동 자리에선 누락 _보고_ 까지 = oncall 후속 후보).

### §7.5. 결정론 scaffold — 자동 회상 주입(D-15) + 정리후보 노출(D-16)

lifecycle 주변 판단 구조: **감지·탐지=결정론 코드, 삭제·통합 판단=세션끝 deep curator role**(D-18 — D-16 의 "메인 직접 실행"을 세션끝 curator 로 위임; 메인 housekeeping 0).

**D-15 `hooks/mem-recall-inject.sh` (UserPromptSubmit, 읽기 전용):**
- 회상 신호어 regex `지난번|지난번에|예전에|이전에|전에|그때|저번에|아까` 를 프롬프트에서 감지 → `mem recall <prompt>` 실행 → `additionalContext` 사전주입(메인 컨텍스트 도달 전). 메인의 "recall 할까" 판단을 제거 — B1 완성.
- 신호어 불일치·recall 결과 없음·`MEM_DISTILL=1`(distiller 재귀) 시 no-op. 읽기 전용 = 어떤 write 도 없음.
- 주입 상한: `MEM_RECALL_LINES`(기본 12)·`MEM_RECALL_CHARS`(기본 2000) env로 제어.

**D-16 `mem inject` 정리신호 섹션 (SessionStart, 읽기 전용 projection — γ/D-18 에서 informational 로 축소):**
- `mem inject --hook` 기존 블록 이후, 비어 있지 않을 때만 `## 🧹 정리 신호 (세션끝 deep curator 가 처리 — D-18, 메인 조치 불요)` 섹션 추가: cwd-scoped durable near-dup 그룹 + capacity 초과(`durable > soft_ceiling=80`) + 만료 임박 working(`<= 3일`). 이 섹션도 SessionStart 전체 cap 안에서 기본 2줄만 노출된다. 모두 read-only — zero deletes / zero flag writes.
- **γ/D-18**: 이 섹션은 이제 **informational** — 메인은 *조치하지 않는다* (메인 housekeeping 0). 실제 consolidate/prune/merge/graduate 는 **세션끝 deep curator**가 `curate-snapshot`(durable snapshot+SIGNALS) 을 보고 action JSON 으로 수행하고, `mem-distill-dispatch.sh` 의 script(shell=False)가 화이트리스트 게이트로 검증·실행한다. (D-17 "삭제=메인" → D-18 "삭제=세션끝 deep curator" 이전; 정당화: deep role capability + full context + worst=비효율(손실 아님, graveyard+dump 복구) + prune/merge 화이트리스트·fail-closed graveyard.)

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
