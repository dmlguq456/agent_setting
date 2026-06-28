---
name: post-it
description: "Manually-controlled working-memory layer, two scopes. `--scope project` (default): `mem note`/`mem add` (working tier, per-cwd) — thread/decision/convention/reference records in DB. `--scope user <aspect>`: `mem add` (durable, global, profile-adjacent) — splices a note into the `## 사용자 수동 메모` block of the profile record (`source user-profile:<stem>`), shared with analyze-user. All entries are designed to graduate (into artifacts/profiles) or expire — `sweep` flags stale working records; `promote` graduates user notes into the profile record. DB working tier is injected at session start by `mem inject` (not a file read)."
argument-hint: "[show] | add <category> <text> | resolve <hint> | decide <text> | handoff [--no-confirm] | sweep [--no-confirm] | promote [<hint>] [--scope project|user [<aspect>]]"
metadata:
  group: ops
  fam: ops
  modes: []
  blurb: "프로젝트·cross-project 기록·handoff — 세션 간 연속성 working 메모"
---

## 목적

사용자가 **직접 통제하는** 포스트잇 메모리. `~/.claude/projects/*/memory/` 의 자동 메모리 시스템과는 별개로, 사용자가 명시적으로 `/post-it` 명령을 호출할 때만 변경된다. 세션 종료 시 conversation 이 사라지는 휘발성을 메우는 목적 (compact 는 일시적 보존이라 불충분).

**핵심 비유 — 임시 포스트잇.** post-it 은 _영구 기록이 아니다_. 영구 진실은 산출물(`plans/`·`documents/`·`spec/`·code·git) 과 구조화 프로필(DB `type=profile` 레코드) 에 있다. post-it 은 그 사이를 잇는 _휘발성 작업면_ — 지금 떠올려야 할 것만 짧게 붙여두고, 산출물로 졸업하면 떼어낸다.

> **불변식 — 사용자는 post-it 을 들여다보지 않는다 (fire-and-forget).** post-it 은 _Claude 의 세션-간 연속성 작업면_ 이지 사용자 읽기용 문서가 아니다. 따라서 (1) lean 유지·졸업 prune 는 **Claude 책임** — 사용자에게 레코드를 줄 단위로 검토시키지 않는다. (2) 자동 nudge 자리의 sweep 은 _확실한_ 졸업·stale 만 **자동 제거 + 한 줄 보고** (애매하면 keep). (3) 사용자에겐 _짧은 요약_ 만 주고, 액션 _저장 여부_ 만 confirm 받는다. 줄 단위 preview 는 사용자가 `/post-it sweep` 를 직접 칠 때만.

> **통합 기억 store 연동 (2026-06-15, v5).** post-it 은 _프로젝트 단위 working tier_ 로서 통합 store([tools/memory](../../tools/memory/README.md)) DB(`memory.db`, SQLite WAL) 에 저장된다 — `mem note`/`mem add` 로 working 레코드 write, `mem recall` 로 검색, working lifecycle(만료·졸업)은 `mem lifecycle` 이 관할. 세션 주입은 `python3 ~/.claude/tools/memory/mem.py inject --hook` 가 DB working tier 에서 수행. sweep 의 시간 lifecycle 은 `mem lifecycle` 과 동류(시간 기반 working lifecycle)이되 임계값·동작이 다름 — post-it 은 ≥30d stale·≥90d archive 를 _플래깅_(사람-점검), store 는 `WORKING_TTL_DAYS`(현재 21d)로 _자동 만료_.
## Lifecycle (post-it 원칙 — 모든 엔트리는 졸업하거나 만료한다)

엔트리는 영구 누적되지 않는다. 각 레코드는 둘 중 하나로 끝난다:

| 상태 | 의미 | 처리 |
|---|---|---|
| **graduated** | 내용이 산출물·구조화 절에 영구 반영됨 (decision → plan, convention → CLAUDE.md/code, user 메모 → profile 레코드 절) | working 레코드 만료 (`sweep` / `promote`). 산출물이 진실, 사본은 중복 |
| **stale** | 오래된 `[in-progress]`·이미 끝난 hint — 더는 안 맞음 | 만료 (`sweep` / `resolve`) |
| **live** | 아직 working 레코드에만 있고 유효 | 유지 |

- _졸업 자체_ (내용을 산출물에 반영) 는 소유 스킬이 한다 (autopilot-code 가 plan 에, autopilot-spec 이 spec 에, analyze-user 가 프로필에). post-it 의 `sweep`/`promote` 는 _졸업한 working 레코드를 만료시키는_ 역할.
- 세션 연속성(handoff)과 lean 유지(sweep)는 한 쌍 — 인계 전에 졸업·stale 을 떼어야 다음 세션이 _현재 유효한 것만_ 받는다. `handoff` 가 sweep 을 먼저 제안하는 이유.

## Proactive nudge (context-aware — 메인 Claude 가 먼저 제안)

post-it 의 목적 = Claude 가 _사용자 흐름을 이어가고_(연속성) + _사용자가 놓친 것을 상기_(nudge). **working 기억 저장은 _자동_** (통합 기억 §7 자동 write 불변식 — confirm 없음), 세션 단절을 막기 위해 메인 Claude 는 다음 신호에서 working 맥락을 **자동 기록(store working tier)** 한다:

- **context 사용량 ~50%+** — statusline context 막대·긴 대화·compaction 임박. → working 맥락 자동 기록 + 한 줄 보고.
- **wind-down 발화** — "오늘 여기까지" / "내일 이어서" / `/clear` 직전 류. → 세션 working 맥락(진행중·결정·다음 hint) 자동 handoff 기록.
- **작업 한 덩어리 완료** — 재사용 가치 있는 thread/decision 자동 `mem note`.

> **자동 기록 모델 (사용자는 post-it 을 안 본다)**: working 맥락은 _자동 기록_ (저장 confirm 없음 — §7 기억 저장 자동). 자동 handoff 는 sweep 을 _자동 포함_ — 확실한 졸업·stale 만 자동 prune (애매하면 keep), 결과는 _한 줄 보고_. **confirm 은 _prune/삭제_ 같은 비가역 자리만** (저장 자체는 자동). 줄 단위 검토는 사용자가 `/post-it sweep` 를 직접 칠 때만.

> 이 nudge 의 _트리거 규칙_ 은 항상 로드되는 글로벌 CLAUDE.md §2 에도 한 줄 있다 (SKILL.md 는 호출 시만 로드되므로, 자발적 제안은 CLAUDE.md 가 발화시킴). hard backstop 으로 PreCompact hook 을 둘 수 있으나(옵션, 미설정 시 nudge 만), hook 은 셸 스크립트라 _고정 리마인드_ 만 — 똑똑한 요약 handoff 는 대화 안의 Claude 만 가능.

## Scope — project vs user

본 skill 은 _두 자리_ 에 자료를 저장. `--scope` flag 로 분기:

| Scope | 저장 위치 | 다루는 자료 | 세션 주입 | 졸업 경로 |
|---|---|---|---|---|
| `project` (default) | DB working tier (`mem note`/`mem add`, cwd-scoped) | 현 cwd 의 _프로젝트 단위_ 자료 — 진행 중 작업·결정·외부 자원·다음 세션 hint | `mem inject` 가 DB working 에서 수행 | `sweep` → 산출물(`plans/`·`documents/`·`spec/`·git) 대조 후 만료 |
| `user <aspect>` | DB durable 레코드 (`mem add`, global, `source user-profile:<stem>`) — profile 레코드의 `## 사용자 수동 메모` 블록 내 | _cross-project 사용자_ 자료 — 범용 패턴·preference·도메인 메모. **analyze-user 사이의 상시 수동 채널** | `mem inject` 가 `type=profile` 레코드에서 수행 | `promote` → profile 레코드 구조화 절로 졸업 후 수동 메모 블록에서 제거 |

**Scope 선택 기준**:
- _이 프로젝트에서만 의미 있는 자료_ → `--scope project`
- _다른 프로젝트에서도 이어 쓸 사용자 자료_ → `--scope user <aspect>`
- 애매하면 `project` (default)

**user scope 의 aspect 선택**:

| aspect | 갱신 대상 (profile 레코드) | 들어갈 자료 예시 |
|---|---|---|
| `figure` | `mem profile 01_paper_figure_style` | 시각·figure 선호 ("Times 폰트 고정") |
| `writing` | `mem profile 02_paper_writing_style` | paper 작성 톤·표현 |
| `presentation` | `mem profile 03_presentation_strategy` | 슬라이드 layout·서사 결정 |
| `analysis` | `mem profile 04_analysis_methodology` | 데이터·실험 분석 방법 메모 |
| `domain` | `mem profile 05_domain_expertise` | 도메인 용어·선호 표현 |
| `collab` (default) | `mem profile 06_collaboration_style` | 작업 흐름·feedback·결정 패턴 — 가장 흔한 자리 |

**user scope 가 별도 파일이 아니라 profile 레코드 안 _사용자 수동 메모_ 블록인 이유**:
- 사용자 레벨 note 는 거의 항상 6 aspect 중 하나에 자연 분류.
- 별도 레코드이면 _구조화(analyze-user 영역)_ 와 _free-form(사용자 영역)_ 이 분산 → sub-agent `mem profile` 호출 자리 증가.
- profile 레코드 안 _두 영역_(analyze-user 구조화 + 사용자 수동 메모) 으로 책임 분리 + 한 `mem profile` 호출로 모두 적재.

**`/analyze-user` 와의 책임 분리 + 졸업 흐름**:
- `## 사용자 수동 메모` 블록 — _사용자 영역_. analyze-user 는 _읽기만_ 하고 silently 손대지 않는다 (이 계약 유지 — 단 `promote` 로 memo 를 구조화 절로 졸업시킨 뒤 manual 에서 제거).
- `promote` (또는 analyze-user 가 시작 시 manual 메모를 _반영 후보로 제시_, confirm) 로 안정된 manual 메모를 구조화 절로 졸업시킨 뒤 manual 에서 제거 — manual 블록을 _staging post-it_ 으로 유지, 무한 누적 방지.
- 그 외 모든 절 — _analyze-user 영역_. 사용자가 직접 편집하면 다음 update 에 덮어쓰일 수 있음 (record body 의 `changelog:` 에 남기면 보존).
- **두 writer 공유 contract**: `/post-it promote --scope user` 와 `analyze-user update` 는 모두 같은 source(`user-profile:<stem>`) 의 profile 레코드에 write한다 — ONE logical record, two writers. Step 4.1 아래 `promote` 동작 명세 참조.

> **artifact-guard 주의**: project post-it (DB working 레코드) 도, user scope (profile 레코드) 도 **직접 편집 자유** — 둘 다 artifact-guard 비가드 (convention only, CLAUDE.md §0(0b)). 즉 `--scope user` 쓰기에 ceremony 불필요. 단 promote 처럼 _analyze-user 영역 절_ 을 건드릴 땐 preview→confirm 으로 사용자 확인 (계약 보존).

## DB working tier & 자동 로드

- **project scope**: `python3 ~/.claude/tools/memory/mem.py note "<text>" --type <type>` 으로 working 레코드 write (단축형 권장). 전체형 필요 시: `mem add working <type> "<body>" --scope project` — `<type>` 자리엔 `thread`/`decision`/`convention`/`reference`/`hint` 중 하나. 세션 주입은 `python3 ~/.claude/tools/memory/mem.py inject --hook` 가 DB working 에서 수행 (파일 read 없음).
- **user scope**: `python3 ~/.claude/tools/memory/mem.py add durable profile <body> --scope global --source user-profile:<stem>` 로 profile 레코드에 merge write. 적재는 sub-agent 가 `python3 ~/.claude/tools/memory/mem.py profile <stem>` 실행 시.
- **갱신**: `/post-it` 명령 또는 §Proactive 자동 기록 (CLAUDE.md §2 / MEMORY §7 자동 write 불변식 — 저장은 자동, 비가역 prune/삭제만 confirm).

## 5 카테고리 — type taxonomy (레코드 type 으로 사용)

파일 형식은 없다. 5 카테고리는 DB working 레코드의 `type` 값으로 사용:

| 카테고리 | type 값 | 내용 예시 | aging |
|---|---|---|---|
| Conventions | `convention` | 영속 규약 (노션 위치, 커밋 메시지 언어) | 시간으로 늙지 않음 — 졸업으로만 제거 |
| External Resources | `reference` | 외부 링크/경로 (데이터셋, Overleaf) | 시간으로 늙지 않음 — 졸업으로만 제거 |
| Open Threads | `thread` | `[in-progress YYYY-MM-DD]` prefix — 현재 진행 중 작업 | 날짜 기준 tier 판정 |
| Decisions | `decision` | `YYYY-MM-DD:` prefix — 의사결정과 사유 | 날짜 기준 tier 판정 |
| Next Session Hints | `hint` | 다음 세션에 알아야 할 진행 상황·다음 할 일·주의사항 | handoff 마다 갱신 |

> **aging stamp + 시간 tier (thread/decision/hint)**: time-sensitive 레코드는 `created` / `expires` 컬럼으로 판정. `sweep` 가 이 날짜로 시간 tier(active < 30d / stale 후보 ≥30d / archive ≥90d)를 판정. convention/reference 는 _시간으로 늙지 않는다_ (졸업으로만 제거).

## Sub-Actions

### `/post-it` (인자 없음) = `show`
`python3 ~/.claude/tools/memory/mem.py recall "" --tier working --scope project` 로 현 cwd 의 working 레코드를 preview 표시. 레코드 없으면 `/post-it add` 안내.

### `/post-it add <category> <text>`
- `<category>` ∈ {`convention`, `resource`, `thread`, `decision`}. Alias: `conv`, `res`, `th`, `dec`.
- `python3 ~/.claude/tools/memory/mem.py note "<text>" --type <type>` 실행 (type 매핑: convention→`convention`, resource→`reference`, thread→`thread`, decision→`decision`).
- `thread` → body 에 `[in-progress YYYY-MM-DD]` prefix 자동.
- `decision` → body 에 `YYYY-MM-DD:` prefix 자동.
- **사용자 텍스트 원문 그대로** → **즉시 적용** (검토 X). `--confirm` 시 diff preview.

### `/post-it resolve <hint>`
- working 레코드 중 `type=thread` 인 것에서 `<hint>` fuzzy 매칭 레코드를 찾는다.
- **default: preview → confirm** (1개 매칭 → 확인 / 여러 매칭 → 번호 선택 / 0개 → 중단).
- `mem delete <id>` 로 결정론적 삭제 — `resolve` 는 매칭 thread 레코드를 `mem delete` 로 즉시 제거 (`--no-confirm` 시 가장 유사한 1개 즉시 삭제). default 는 preview → confirm.

### `/post-it decide <text>`
- `python3 ~/.claude/tools/memory/mem.py note "<YYYY-MM-DD: text>" --type decision` 실행. 원문 → **즉시 적용**. `--confirm` 으로 검토.

### `/post-it sweep [--no-confirm] [--scope project|user [<aspect>]]`
**산출물·DB 레코드 대조 → 졸업·stale 항목 플래그/만료 (post-it lean 유지의 핵심).**

- **자동 자리** (nudge·handoff 내부): _확실한_ graduated/stale 만 **자동 flag + 한 줄 보고**, 애매하면 keep.
- **수동 자리** (`/post-it sweep` 직접 호출): **preview → confirm**. `--no-confirm` 시 확실분 즉시 처리.

**project scope (default)**:
1. `python3 ~/.claude/tools/memory/mem.py recall "" --tier working --scope project` 로 현 cwd working 레코드 전체 조회.
2. 현 산출물과 대조: `<artifact-root>/plans/*/`·`documents/*/`·`spec/`·`experiments/*/` + `git log --oneline -30` + 관련 코드·문서.
3. 각 레코드 분류:
   - **graduated** — 내용이 산출물에 영구 반영됨 → 만료 후보 (+ 어디로 갔는지 한 줄 pointer).
   - **stale** — 시간 기반 lifecycle tier. 대상 = `type=thread/decision/hint` (time-sensitive):
     - **active** (< 30d 또는 최근 git 활동과 연결) → 유지.
     - **stale 후보** (≥ ~30d 미갱신, git 활동과 단절) → 만료 후보로 분류.
     - **archive 대상** (≥ ~90d 미갱신, 또는 완료 정황 확실) → 자동 자리는 flag(한 줄 보고). `mem lifecycle` 이 `WORKING_TTL_DAYS` 기준으로 처리. graduated 내용은 이미 산출물에 있으므로 archive 불요(drop).
   - **live** — working 레코드에만 있고 유효(시간 무관 — convention/reference 는 _졸업_ 으로만 제거) → 유지.
4. 분류 결과를 **graduated / stale / keep 3 묶음으로 preview** → 사용자가 제거할 항목 confirm.
5. `mem lifecycle` 트리거 또는 advisory 처리.
- **sweep 은 working 레코드만 처리** — 산출물에 _추가_ 하지 않는다 (졸업 반영은 소유 스킬 몫).

**user scope (`--scope user <aspect>`)**:
- `python3 ~/.claude/tools/memory/mem.py profile <stem>` 으로 profile 레코드 조회.
- `## 사용자 수동 메모` 의 각 항목을 _같은 aspect 의 구조화 절_ 과 대조 → 이미 반영된 항목을 제거 후보로 preview → confirm.

### `/post-it promote [<hint>] [--scope user [<aspect>]]`
**user 메모를 구조화 aspect 절로 _졸업_ 시키는 sub-action** (user scope 전용).

**저장 모델 (중요)**: user 메모는 profile 레코드 body 안 `## 사용자 수동 메모` 블록에 embed된다 — 별도 `user-postit:` source 레코드로 분리하지 않는다 (별도 source 는 `mem profile`/`_derive_aspect` 에 보이지 않아 모든 agent 가 읽지 못함).

**promote 동작 (read-modify-write)**:
1. `<aspect>` (또는 default `collab`) profile 레코드에서 `## 사용자 수동 메모` 항목 중 _안정·범용_ 한 것을 식별 (`<hint>` 주면 그 항목).
2. 적절한 구조화 절(해당 aspect 본문)에 통합할 문안을 제안 → **preview → confirm** (analyze-user 의 "읽기만" 계약을 confirm 으로 보존).
3. 확정 시:
   - (1) `python3 ~/.claude/tools/memory/mem.py profile <stem>` 으로 현재 body 읽기 (newest-wins, rowid-DESC tie-broken).
   - (2) 해당 note 를 구조화 절에 splice + `## 사용자 수동 메모` 블록에서 그 항목 제거.
   - (3) `python3 ~/.claude/tools/memory/mem.py add durable profile "<whole-new-body>" --scope global --source user-profile:<stem>` 으로 전체 body write (SAME source = analyze-user 와 같은 logical record; 이전 working 레코드는 만료).
4. _대량·정식 재구조화_ 가 필요하면 promote 대신 `/analyze-user` 를 권한다 (promote 는 가벼운 1-2 항목 졸업용).

> **두 writer 계약**: `/post-it promote --scope user` 와 `analyze-user update` 는 모두 `source user-profile:<stem>` 으로 write — ONE logical record. analyze-user 의 "read existing body" 는 반드시 `mem profile <stem>` (tie-broken) 으로 읽어야 한다 (raw `db_iter_records` 로 읽으면 stale dup 에서 splice 될 위험). `write_record` 는 `(tier, scope, source)` source-keyed UPSERT — 같은 `source=user-profile:<stem>` 면 body 변경 시 기존 레코드를 in-place UPDATE (id 보존), dup row 없음. 두 writer 가 ONE record 로 결정론화.

### `/post-it handoff [--no-confirm]`
**세션 인계 — sweep 먼저, 그 다음 hints 생성** (Claude 가 내용 생성).

1. **sweep 자동 포함** — `sweep` 로직을 돌려 _확실한_ graduated·stale 을 자동 prune (애매하면 keep). 한 줄 보고 ("졸업 N·stale M 정리").
2. **hints 생성** — 현 세션 conversation 을 review 해 다음 세션에 알아야 할 5-10 bullet 요약:
   - 지금 어디까지 진행했는지 / 다음 세션에서 먼저 할 일 / 미해결 질문·블로커 / 주의사항.
   - **제외**: 이미 산출물·git 에 영속화된 내용, 다른 working 레코드에 이미 있는 내용.
3. **Default: preview → confirm** — 요약 bullets 를 보여주고 확인. 사용자 직접 편집·추가 가능.
4. 확인 시 `python3 ~/.claude/tools/memory/mem.py note "<hint-text>" --type hint` 로 각 bullet 기록 (이전 hint 레코드는 `mem lifecycle` 에 의해 교체·만료).
5. `--no-confirm` 시 sweep·hints 검토 없이 즉시 적용.

## Confirm 정책 요약

| Sub-action | Default | Override |
|---|---|---|
| `show` | 즉시 | n/a |
| `add` / `decide` | 즉시 (사용자 텍스트 원문) | `--confirm` |
| `resolve` | preview → confirm (fuzzy 매칭 + advisory) | `--no-confirm` |
| `sweep` (수동 호출) | preview → confirm (Claude 분류) | `--no-confirm` |
| `sweep` (자동 — nudge/handoff 내부) | 확실분 자동 prune + 한 줄 보고 (애매 keep) | n/a |
| `promote` | preview → confirm (Claude 제안 + 구조화 절 편집) | (없음 — 항상 confirm) |
| `handoff` (자동 nudge) | sweep 자동 포함 → 짧은 요약 보여주고 _저장 여부_ confirm | `--no-confirm` |

원칙: **사용자가 직접 적은 텍스트는 즉시, Claude 가 만들거나 매칭하는 경우는 검토.** 단 _사용자는 post-it 을 안 본다_ — 자동 자리의 prune 은 _확실한 것만_ 자동 적용 + 한 줄 보고 (애매하면 keep), 사용자에겐 액션 단위 confirm 만.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — post-it 은 DB store 의 _working tier 사람-편집 자리_ 이고(`mem recall` 한 면에서 검색), 하네스 auto-memory(`projects/*/memory/` → store durable mirror)와 역할이 다르다.
- **영구 기록 X** — post-it 은 포스트잇. 영구 진실은 산출물·코드·git·구조화 프로필(DB type=profile 레코드). 엔트리는 졸업하면 떼어낸다 (sweep/promote).
- **코드/문서 변경 기록 X** — `autopilot-code` 의 `plans/`, `autopilot-draft` 의 `documents/`.
- **세션 활동 로그 X** — `pipeline_summary.md` 등에 이미 누적.

post-it 은 "매 세션 시작 시 알아야 할, 아직 산출물로 졸업하지 않은 한정된 working 맥락"만 담는다.

## Auto-memory와의 경계

store 단일소스 모델에서 두 경로는 같은 `memory.db` 의 다른 면이다.

| 경로 | store 위치 | 갱신 |
|---|---|---|
| `~/.claude/projects/*/memory/` (하네스 auto-memory write 면) | SessionEnd `mem sync` → `memory.db` **durable**(project/global scope) 행으로 mirror; git 미러 `dump.jsonl` | 하네스 자동 write → sync |
| DB working tier (본 skill — `mem note`/`mem add`) | `memory.db` **working**(project scope) 레코드 직접 write; git 미러 `dump.jsonl` | 사용자 `/post-it` 로만 |

구분:
- **이 레포에만 적용되는 사실** (노션 위치, 데이터셋 경로, 진행 중 작업) → `--scope project` (DB working)
- **사용자 자신 / 일반 작업 선호** (Korean output, 코드 스타일) → durable auto-memory 또는 `--scope user`
겹치면 project working 레코드가 더 정확한 local context 라 우선. `mem recall` 이 양쪽을 한 면에서 검색한다.

## Writing Style (간결성 원칙 — 반드시 준수)

working 레코드는 세션 주입 시 항상 읽히는 컨텍스트. **짧고 dense 하게.**

- **한 bullet = 한 줄** (정 길면 최대 2줄).
- **명사구 / 사실 문장**. 형용사·부연·존댓말·이유 설명 최소화.
  - ❌ `Overleaf 는 X 폴더 아래 정리하는 게 좋습니다. 이유는...`
  - ✅ `Overleaf 정리 위치: <Overleaf URL>/TF-Restormer`
- **핵심 어휘만**. 한·영 혼용 OK, 약어·기호(`→`, `&`, `vs`) 적극.
- **카테고리 중복 금지** — 같은 정보는 한 곳에만.
- **시간성**: convention/reference → 날짜 X. decision → `YYYY-MM-DD:` 필수. thread → `[in-progress YYYY-MM-DD]` / `[blocked YYYY-MM-DD]` 필수.
- **메타 코멘트 금지** — "TODO 추후 확인" 류 X. thread 로.
- `handoff` 요약·`sweep` pointer 도 이 원칙 (1줄).

## Language Rule
- 사용자 대화는 한국어.
- working 레코드 본문은 사용자 언어 그대로 (한·영 혼용 OK).

## Task

Argument `$ARG` 파싱:
- 비어 있으면 `show` (DB working 레코드 preview — 없으면 `/post-it add` 안내).
- `add <category> <text>` → working 레코드 `mem note` write.
- `resolve <hint>` → thread 레코드 fuzzy advisory 처리.
- `decide <text>` → decision 레코드 write.
- `sweep [--no-confirm] [--scope ...]` → 산출물·레코드 대조 후 graduated·stale flag/만료.
- `promote [<hint>] [--scope user [<aspect>]]` → user 메모를 profile 레코드 구조화 절로 졸업 (read-modify-write).
- `handoff [--no-confirm]` → sweep 제안 → 세션 요약 → hint 레코드 write.
- `--scope user [<aspect>]` 동반 시 `mem profile <stem>` / `mem add ... --source user-profile:<stem>` 대상 (profile 레코드 직접 write, ceremony 불필요).
- 그 외 → 사용법 안내.
