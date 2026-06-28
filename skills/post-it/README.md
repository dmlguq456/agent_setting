# post-it

> 본 README 는 `SKILL.md` 의 GitHub 표시용 mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요

사용자가 **직접 통제하는** _임시 포스트잇_ 메모리. `<agent-home>/projects/*/memory/`의 자동 메모리와 별개 layer로, 사용자가 명시적으로 `/post-it` 명령을 호출할 때만 변경된다. 세션 종료 시 conversation이 사라지는 휘발성을 메우는 목적.

**핵심 비유 — 포스트잇.** post-it 은 영구 기록이 아니다. 영구 진실은 산출물(`plans/`·`documents/`·`spec/`·code·git)·구조화 프로필(DB `type=profile` 레코드)에 있고, post-it 은 그 사이를 잇는 휘발성 작업면. 산출물로 _졸업_ 하면 떼어낸다.

> **불변식 — 사용자는 post-it 을 읽지 않는다.** 에이전트의 세션-간 연속성 작업면이지 사용자 읽기용 문서가 아니다. lean 유지·prune 은 에이전트 책임 (사용자에겐 한 줄 요약만).

## 생애주기 (모든 엔트리는 졸업하거나 만료)

| 상태 | 의미 | 처리 |
|---|---|---|
| **graduated** | 산출물·구조화 절에 영구 반영됨 | 만료 (`sweep`/`promote`) |
| **stale** | 오래된 `[in-progress]`·끝난 hint | 만료 (`sweep`/`resolve`) |
| **live** | working 레코드에만 있고 유효 | 유지 |

## Scope — project vs user

| Scope | 저장 위치 | 갱신 경로 |
|---|---|---|
| `project` (default) | DB working tier (`mem note`/`mem add`, cwd-scoped) | `/post-it` — `mem inject` 가 DB working 에서 세션 주입 |
| `user <aspect>` | DB durable 레코드 (`mem profile <stem>` / `mem add ... --source user-profile:<stem>`) — profile 레코드의 `## 사용자 수동 메모` 블록 | `/post-it --scope user <aspect>` — analyze-user 사이 상시 수동 채널; `mem profile` 호출 시 적재 |

## 5 카테고리 — type taxonomy (레코드 type 값)

| 카테고리 | type 값 | 내용 예시 |
|---|---|---|
| Conventions | `convention` | 영속 규약 (노션 위치, 커밋 메시지 언어 등) |
| External Resources | `reference` | 외부 링크/경로 (데이터셋, Overleaf 등) |
| Open Threads | `thread` | `[in-progress YYYY-MM-DD]` — 진행 중 작업 |
| Decisions | `decision` | `YYYY-MM-DD:` — 의사결정과 사유 |
| Next Session Hints | `hint` | 다음 세션에 알아야 할 진행 상황·다음 할 일·주의사항 |

## Sub-Actions

| 명령 | 동작 | Confirm |
|---|---|---|
| `/post-it` (또는 `show`) | DB working 레코드 preview (`mem recall --tier working`); 없으면 `add` 안내 | — |
| `/post-it add <category> <text>` | `mem note "<text>" --type <type>` write. category ∈ {convention, resource, thread, decision} (alias conv/res/th/dec). thread→`[in-progress YYYY-MM-DD]`, decision→`YYYY-MM-DD:` 자동 | **즉시** (`--confirm`) |
| `/post-it resolve <hint>` | thread 레코드 fuzzy 매칭 + `mem delete <id>` 결정론적 삭제 | preview→confirm (`--no-confirm`) |
| `/post-it decide <text>` | `mem note "<YYYY-MM-DD: text>" --type decision` write | **즉시** (`--confirm`) |
| `/post-it sweep` | 산출물(`plans`·`documents`·`spec`·git)과 working 레코드 대조 → graduated·stale flag/만료 | 수동 호출 preview→confirm / 자동(nudge) 확실분 자동+한 줄 보고 |
| `/post-it promote [--scope user <aspect>]` | profile 레코드 `## 사용자 수동 메모` 항목을 구조화 절로 졸업 (read-modify-write: `mem profile` → splice → `mem add ... --source user-profile:<stem>`) | preview→confirm |
| `/post-it handoff [--no-confirm]` | sweep 먼저 → conversation review → 5-10 bullet → `mem note --type hint` write | preview→confirm (`--no-confirm`) |

## Confirm 원칙

사용자가 직접 적은 텍스트(add/decide)는 즉시; 에이전트가 만들거나 매칭·분류·졸업(resolve/sweep/promote/handoff)하는 건 검토. 단 _사용자는 post-it 을 안 보므로_ 자동 nudge 자리의 sweep 은 확실분만 자동 prune + 한 줄 보고 (줄 단위 검토 강요 X).

## 간결성 원칙 (working 레코드 작성 시 강제)

세션 주입 시 항상 읽히는 컨텍스트 — **짧고 dense하게.**
- 한 bullet = 한 줄 (최대 2줄). 명사구·사실 문장. 약어·기호(`→`,`&`,`vs`) 적극.
- 같은 정보는 한 카테고리에만. thread는 `[상태 YYYY-MM-DD]` 필수, decision는 `YYYY-MM-DD:` 필수.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — post-it 은 DB store 의 _working tier 사람-편집 자리_(`mem recall` 한 면에서 검색). 하네스 auto-memory(`projects/*/memory/` → store durable mirror)와 역할이 다르다.
- **영구 기록 X** — 포스트잇. 영구 진실은 산출물·코드·git·DB type=profile 레코드. 졸업하면 뗀다.
- **코드/문서 변경 기록 X** — `autopilot-code` plans/ · `autopilot-draft` documents/.

## Auto-memory와의 경계

store 단일소스 모델에서 두 경로는 같은 `memory.db` 의 다른 면이다.

| 경로 | store 위치 | 갱신 |
|---|---|---|
| `<agent-home>/projects/*/memory/` (하네스 auto-memory write 면) | SessionEnd `mem sync` → store **durable** mirror | 하네스 자동 write → sync |
| DB working tier (본 skill — `mem note`/`mem add`) | `memory.db` **working** 레코드 직접 write; git 미러 `dump.jsonl` | 사용자가 `/post-it`로만 |

이 레포에만 적용되는 사실 → `--scope project` (DB working) / 사용자·일반 작업 선호 → durable auto-memory 또는 `--scope user` (`mem profile <stem>`). `mem recall` 이 양쪽을 한 면에서 검색.
