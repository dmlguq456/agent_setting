## Lifecycle (post-it 원칙 — 모든 엔트리는 졸업하거나 만료한다)

엔트리는 영구 누적되지 않는다. 각 레코드는 둘 중 하나로 끝난다:

| 상태 | 의미 | 처리 |
|---|---|---|
| **graduated** | 내용이 산출물·구조화 절에 영구 반영됨 (decision → plan, convention → CLAUDE.md/code, user 메모 → profile 레코드 절) | working 레코드 만료 (`sweep` / `promote`). 산출물이 진실, 사본은 중복 |
| **stale** | 오래된 `[in-progress]`·이미 끝난 hint — 더는 안 맞음 | 만료 (`sweep` / `resolve`) |
| **live** | 아직 working 레코드에만 있고 유효 | 유지 |

- _졸업 자체_ (내용을 산출물에 반영) 는 소유 스킬이 한다 (autopilot-code 가 plan 에, autopilot-spec 이 spec 에, analyze-user 가 프로필에). post-it 의 `sweep`/`promote` 는 _졸업한 working 레코드를 만료시키는_ 역할.
- 세션 연속성(handoff)과 lean 유지(sweep)는 한 쌍 — 인계 전에 졸업·stale 을 떼어야 다음 세션이 _현재 유효한 것만_ 받는다. `handoff` 가 sweep 을 먼저 제안하는 이유.

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

> **artifact-guard 주의**: project post-it (DB working 레코드) 도, user scope (profile 레코드) 도 **직접 편집 자유** — 둘 다 artifact-guard 비가드 (convention only, adapter bootstrap). 즉 `--scope user` 쓰기에 ceremony 불필요. 단 promote 처럼 _analyze-user 영역 절_ 을 건드릴 땐 preview→confirm 으로 사용자 확인 (계약 보존).

## DB working tier & 자동 로드

- **project scope**: `python3 <agent-home>/tools/memory/mem.py note "<text>" --type <type>` 으로 working 레코드 write (단축형 권장). 전체형 필요 시: `mem add working <type> "<body>" --scope project` — `<type>` 자리엔 `thread`/`decision`/`convention`/`reference`/`hint` 중 하나. 세션 주입은 `python3 <agent-home>/tools/memory/mem.py inject --hook` 가 DB working 에서 수행 (파일 read 없음).
- **user scope**: `python3 <agent-home>/tools/memory/mem.py add durable profile <body> --scope global --source user-profile:<stem>` 로 profile 레코드에 merge write. 적재는 sub-agent 가 `python3 <agent-home>/tools/memory/mem.py profile <stem>` 실행 시.
- **갱신**: `/post-it` 명령 또는 §Proactive 자동 기록 (adapter pause/autonomy rule / MEMORY §7 자동 write 불변식 — 저장은 자동, 비가역 prune/삭제만 confirm).

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
