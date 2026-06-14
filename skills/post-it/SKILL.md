---
name: post-it
description: Manually-controlled "post-it" memory — a self-pruning note layer, two scopes. `--scope project` (default): `.claude_reports/post-it.md` (per-cwd, 5 categories; legacy `memo.md` auto-read). `--scope user <aspect>`: `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절 (cross-project, aspect 기반, analyze-user 사이의 상시 수동 채널). 모든 엔트리는 _졸업_(산출물·구조화 절에 반영) 하거나 _만료_ 하도록 설계 — `sweep` 가 산출물과 대조해 중복·stale 항목을 prune, `promote` 가 user 메모를 구조화 절로 졸업. Auto-loaded at session start, edited only via explicit `/post-it` sub-actions. Separate from the auto-memory system at `~/.claude/projects/*/memory/`.
argument-hint: "[show] | init | add <category> <text> | resolve <hint> | decide <text> | handoff [--no-confirm] | sweep [--no-confirm] | promote [<hint>] [--scope project|user [<aspect>]]"
---

## 목적

사용자가 **직접 통제하는** 포스트잇 메모리. `~/.claude/projects/*/memory/` 의 자동 메모리 시스템과는 별개로, 사용자가 명시적으로 `/post-it` 명령을 호출할 때만 변경된다. 세션 종료 시 conversation 이 사라지는 휘발성을 메우는 목적 (compact 는 일시적 보존이라 불충분).

**핵심 비유 — 임시 포스트잇.** post-it 은 _영구 기록이 아니다_. 영구 진실은 산출물(`plans/`·`documents/`·`spec/`·code·git) 과 구조화 프로필(`user_profile/`) 에 있다. post-it 은 그 사이를 잇는 _휘발성 작업면_ — 지금 떠올려야 할 것만 짧게 붙여두고, 산출물로 졸업하면 떼어낸다.

> **불변식 — 사용자는 post-it 을 들여다보지 않는다 (fire-and-forget).** post-it 은 _Claude 의 세션-간 연속성 작업면_ 이지 사용자 읽기용 문서가 아니다. 따라서 (1) lean 유지·졸업 prune 는 **Claude 책임** — 사용자에게 파일을 줄 단위로 검토시키지 않는다. (2) 자동 nudge 자리의 sweep 은 _확실한_ 졸업·stale 만 **자동 제거 + 한 줄 보고** (애매하면 keep). (3) 사용자에겐 _짧은 요약_ 만 주고, 액션 _저장 여부_ 만 confirm 받는다. 줄 단위 preview 는 사용자가 `/post-it sweep` 를 직접 칠 때만.

## Lifecycle (post-it 원칙 — 모든 엔트리는 졸업하거나 만료한다)

엔트리는 영구 누적되지 않는다. 각 bullet 은 둘 중 하나로 끝난다:

| 상태 | 의미 | 처리 |
|---|---|---|
| **graduated** | 내용이 산출물·구조화 절에 영구 반영됨 (decision → plan, convention → CLAUDE.md/code, user 메모 → aspect 절) | post-it 에서 **제거** (`sweep` / `promote`). 산출물이 진실, 사본은 중복 |
| **stale** | 오래된 `[in-progress]`·이미 끝난 hint — 더는 안 맞음 | **제거** (`sweep` / `resolve`) |
| **live** | 아직 post-it 에만 있고 유효 | 유지 |

- _졸업 자체_ (내용을 산출물에 반영) 는 소유 스킬이 한다 (autopilot-code 가 plan 에, autopilot-spec 이 spec 에, analyze-user 가 프로필에). post-it 의 `sweep`/`promote` 는 _졸업한 사본을 떼어내는_ 역할.
- 세션 연속성(handoff)과 lean 유지(sweep)는 한 쌍 — 인계 전에 졸업·stale 을 떼어야 다음 세션이 _현재 유효한 것만_ 받는다. `handoff` 가 sweep 을 먼저 제안하는 이유.

## Proactive nudge (context-aware — 메인 Claude 가 먼저 제안)

post-it 의 목적 = Claude 가 _사용자 흐름을 이어가고_(연속성) + _사용자가 놓친 것을 상기_(nudge). 수동 통제이되(자동 기록 X), 세션 단절을 막기 위해 메인 Claude 는 다음 신호에서 **먼저 제안**한다:

- **context 사용량 ~50%+** — statusline context 막대·긴 대화·compaction 임박. → "지금 `/post-it handoff` 해둘까요?"
- **wind-down 발화** — "오늘 여기까지" / "내일 이어서" / `/clear` 직전 류.
- **작업 한 덩어리 완료** — "이거 `/post-it add thread` 로 남길까요?"

> **자동 제안의 confirm 모델 (사용자는 post-it 을 안 본다)**: 자동 handoff 는 sweep 을 _자동 포함_ — 확실한 졸업·stale 만 자동 prune (애매하면 keep), 결과는 _한 줄 보고_. 사용자에겐 **짧은 요약(무엇을 정리했고 다음 세션 hints 가 무엇인지)** 만 보여주고 _저장 여부_ 만 confirm 받는다. 파일을 줄 단위로 검토시키지 않는다 (그건 사용자가 `/post-it sweep` 를 직접 칠 때만).

> 이 nudge 의 _트리거 규칙_ 은 항상 로드되는 글로벌 CLAUDE.md §2 에도 한 줄 있다 (SKILL.md 는 호출 시만 로드되므로, 자발적 제안은 CLAUDE.md 가 발화시킴). hard backstop 으로 PreCompact hook 을 둘 수 있으나(옵션, 미설정 시 nudge 만), hook 은 셸 스크립트라 _고정 리마인드_ 만 — 똑똑한 요약 handoff 는 대화 안의 Claude 만 가능.

## Scope — project vs user

본 skill 은 _두 자리_ 에 자료를 저장. `--scope` flag 로 분기:

| Scope | 파일 위치 | 다루는 자료 | 자동 로드 | 졸업 경로 |
|---|---|---|---|---|
| `project` (default) | `.claude_reports/post-it.md` (legacy `memo.md` 자동 read) | 현 cwd 의 _프로젝트 단위_ 자료 — 진행 중 작업·결정·외부 자원·다음 세션 hint | 글로벌 CLAUDE.md 도메인 트리거 | `sweep` → 산출물(`plans/`·`documents/`·`spec/`·git) 대조 후 prune |
| `user <aspect>` | `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절 (default aspect = `collab`) | _cross-project 사용자_ 자료 — 범용 패턴·preference·도메인 메모. **analyze-user 사이의 상시 수동 채널** | sub-agent 가 aspect 파일 Read 시 같이 적재 | `promote` → 구조화 aspect 절로 졸업 후 manual 에서 제거 |

**Scope 선택 기준**:
- _이 프로젝트에서만 의미 있는 자료_ → `--scope project`
- _다른 프로젝트에서도 이어 쓸 사용자 자료_ → `--scope user <aspect>`
- 애매하면 `project` (default)

**user scope 의 aspect 선택**:

| aspect | 갱신 파일 | 들어갈 자료 예시 |
|---|---|---|
| `figure` | `01_paper_figure_style.md` | 시각·figure 선호 ("Times 폰트 고정") |
| `writing` | `02_paper_writing_style.md` | paper 작성 톤·표현 |
| `presentation` | `03_presentation_strategy.md` | 슬라이드 layout·서사 결정 |
| `analysis` | `04_analysis_methodology.md` | 데이터·실험 분석 방법 메모 |
| `domain` | `05_domain_expertise.md` | 도메인 용어·선호 표현 |
| `collab` (default) | `06_collaboration_style.md` | 작업 흐름·feedback·결정 패턴 — 가장 흔한 자리 |

**user scope 가 별도 파일이 아니라 aspect 파일 안 _사용자 수동 메모_ 절인 이유**:
- 사용자 레벨 note 는 거의 항상 6 aspect 중 하나에 자연 분류.
- 별도 파일이면 _구조화(analyze-user 영역)_ 와 _free-form(사용자 영역)_ 이 분산 → sub-agent Read 자리 증가.
- aspect 파일 안 _두 절_(analyze-user 영역 + 사용자 수동 메모) 로 책임 분리 + 한 Read 로 모두 적재.

**`/analyze-user` 와의 책임 분리 + 졸업 흐름**:
- `## 사용자 수동 메모` 절 — _사용자 영역_. analyze-user 는 _읽기만_ 하고 silently 손대지 않는다 (이 계약 유지).
- 단 `promote` (또는 analyze-user 가 시작 시 manual 메모를 _반영 후보로 제시_, confirm) 로 안정된 manual 메모를 구조화 절로 졸업시킨 뒤 manual 에서 제거 — manual 절을 _staging post-it_ 으로 유지, 무한 누적 방지.
- 그 외 모든 절 — _analyze-user 영역_. 사용자가 직접 Edit 하면 다음 update 에 덮어쓰일 수 있음 (frontmatter `changelog:` 에 남기면 보존).

> **artifact-guard 주의**: project post-it (`.claude_reports/post-it.md`) 도, user scope (`user_profile/0*.md`) 도 **직접 편집 자유** — 둘 다 artifact-guard 비가드 (user_profile 은 hook 비강제 convention only, CLAUDE.md §0(0b)). 즉 `--scope user` 쓰기에 ceremony 불필요. 단 promote 처럼 _analyze-user 영역 절_ 을 건드릴 땐 preview→confirm 으로 사용자 확인 (계약 보존).

## 파일 위치 & 자동 로드

- **project scope**: 현 cwd 의 `.claude_reports/post-it.md` (단일 파일). 글로벌 CLAUDE.md 도메인 트리거로 새 세션 시작 시 Read. 없으면 무시. **legacy**: `post-it.md` 부재 시 `.claude_reports/memo.md` 가 있으면 그것을 읽고, `init`/첫 편집 때 `post-it.md` 로 이전 제안.
- **user scope**: `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절. 자동 로드 X — sub-agent 가 작업 자리에서 aspect 파일 Read 시 적재.
- **갱신**: 항상 `/post-it` 명령으로만. Claude 가 자동으로 쓰지 않는다.

## 파일 형식 (5 카테고리)

```markdown
# Project Post-it

- **Project**: {프로젝트 이름}
- **Last Updated**: YYYY-MM-DD

## Conventions
- (영속 규약 — 예: 노션 정리 위치, 커밋 메시지 언어)

## External Resources
- (외부 링크/경로 — 예: 데이터셋, Overleaf)

## Open Threads
- [in-progress YYYY-MM-DD] (현재 진행 중인 작업 — 날짜 = 추가·갱신 시점)
- [blocked YYYY-MM-DD] (사용자가 직접 수동 편집)

## Decisions
- YYYY-MM-DD: (그 시점의 의사결정과 사유)

## Next Session Hints
(가장 마지막 `/post-it handoff` 결과로 **덮어쓰여짐** — 누적 X)
- (다음 세션에 알아야 할 현재 진행 상황·다음 할 일·주의사항)
```

> **aging stamp + 시간 tier**: time-sensitive 항목(Open Threads `[in-progress/blocked YYYY-MM-DD]`, Decisions `YYYY-MM-DD:`)은 날짜를 단다 (추가·갱신 시점). `sweep` 가 이 날짜로 시간 tier(active < 30d / stale 후보 ≥30d / archive ≥90d — Curator 벤치마킹, sweep 절 참조)를 판정. 구버전 `[in-progress]`(날짜 없음)도 호환 — sweep 가 만나면 날짜 보강 제안. convention/resource 는 _시간으로 늙지 않는다_ (졸업으로만 떼냄) — 스탬프 불요.

## Sub-Actions

### `/post-it` (인자 없음)
파일을 Read 해서 그대로 표시 (`post-it.md` → 없으면 legacy `memo.md`). 둘 다 없으면 `/post-it init` 안내.

### `/post-it init`
`.claude_reports/post-it.md` 가 없으면 위 템플릿으로 생성 (`.claude_reports/` 없으면 함께). `Project` = cwd basename, `Last Updated` = 오늘. 이미 있으면 "이미 존재" 표시 후 중단. legacy `memo.md` 가 있으면 "내용을 post-it.md 로 이전할까요?" 제안 (confirm 시 rename).

### `/post-it add <category> <text>`
- `<category>` ∈ {`convention`, `resource`, `thread`, `decision`}. Alias: `conv`, `res`, `th`, `dec`.
- 해당 섹션 끝에 bullet 추가.
- `thread` → `- [in-progress YYYY-MM-DD] ` prefix 자동 (오늘 날짜).
- `decision` → `- YYYY-MM-DD: ` prefix 자동.
- `convention`/`resource` → prefix 없이 `- ` bullet.
- **사용자 텍스트 원문 그대로** → **즉시 적용** (검토 X). `--confirm` 시 diff preview.
- 적용 시 `Last Updated` 갱신.

### `/post-it resolve <hint>`
- `## Open Threads` 에서 `<hint>` fuzzy 매칭 thread 제거.
- **default: preview → confirm** (1개 매칭 → 확인 / 여러 매칭 → 번호 선택 / 0개 → 중단).
- `--no-confirm` 시 가장 유사한 1개 즉시 제거. 적용 시 `Last Updated` 갱신.

### `/post-it decide <text>`
- `## Decisions` 에 `- YYYY-MM-DD: <text>` 추가. 원문 → **즉시 적용**. `--confirm` 으로 검토.

### `/post-it sweep [--no-confirm] [--scope project|user [<aspect>]]`
**산출물과 대조해 졸업·stale 엔트리를 prune 하는 sub-action** (post-it lean 유지의 핵심). Claude 가 분류한다.

- **자동 자리** (nudge·handoff 내부): _확실한_ graduated/stale 만 **자동 prune + 한 줄 보고**, 애매하면 keep (사용자는 post-it 을 안 봄 — 불변식). 줄 단위 검토 X.
- **수동 자리** (`/post-it sweep` 직접 호출): 그때만 **preview → confirm** (사용자가 명시적으로 들여다보겠다는 신호). `--no-confirm` 시 확실분 즉시 제거.

**project scope (default)**:
1. post-it 의 모든 bullet 을 읽는다 (Conventions / External Resources / Open Threads / Decisions / Next Session Hints).
2. 현 산출물과 대조: `.claude_reports/plans/*/`·`documents/*/`·`spec/`·`experiments/*/` + `git log --oneline -30` + 관련 코드·문서.
3. 각 bullet 분류:
   - **graduated** — 내용이 산출물에 영구 반영됨 (decision 이 plan 에, convention 이 CLAUDE.md/code 에, resource 가 spec/stack 에) → 제거 후보 (+ 어디로 갔는지 한 줄 pointer).
   - **stale** — 시간 기반 lifecycle tier (Hermes Curator active→stale→archive 벤치마킹, T3). 대상 = 날짜를 가진 time-sensitive 항목(`Open Threads` 의 `[in-progress/blocked YYYY-MM-DD]`, `Decisions` 의 `YYYY-MM-DD:`, 실행 정황 있는 `Next Session Hints`):
     - **active** (< 30d 또는 최근 git 활동과 연결) → 유지.
     - **stale 후보** (≥ ~30d 미갱신, git 활동과 단절) → 제거(resolve) 후보로 분류. (기존 ~2주 기준의 명시화 — 2주는 _주의_, 30d는 _제거 후보_.)
     - **archive 대상** (≥ ~90d 미갱신, 또는 완료 정황 확실) → 자동 자리는 drop(한 줄 보고). 사용자가 보존 원하면 `_internal/post-it-archive.md` 로 이동(삭제 아닌 flagging) — 단 graduated 내용은 이미 산출물에 있으므로 archive 불요(drop).
   - **live** — post-it 에만 있고 유효(시간 무관 — convention/resource 는 _졸업_ 으로 떼지 시간으로 떼지 않는다) → 유지.
4. 분류 결과를 **graduated / stale / keep 3 묶음으로 preview** → 사용자가 제거할 항목 confirm (전체·선택).
5. 확정분 제거 + `Last Updated` 갱신.
- `--no-confirm` 시 graduated+stale 자동 제거 (정황 확실할 때만 — 추정 섞이면 위험).
- **sweep 은 post-it 만 prune** — 산출물에 _추가_ 하지 않는다 (졸업 반영은 소유 스킬 몫). 졸업 정황이 불확실하면 제거 말고 keep + "이건 plan 으로 졸업시킬까요" 안내.

**user scope (`--scope user <aspect>`)**:
- `## 사용자 수동 메모` 의 각 항목을 _같은 aspect 의 구조화 절_ 과 대조 → 이미 반영된 항목을 제거 후보로 preview → confirm.
- user_profile 직접 쓰기 자유 (convention — ceremony 불필요).

### `/post-it promote [<hint>] [--scope user [<aspect>]]`
**user 메모를 구조화 aspect 절로 _졸업_ 시키는 sub-action** (user scope 전용 — project 졸업은 산출물 작업이 담당하므로 sweep 만).
1. `<aspect>` (또는 default `collab`) 파일의 `## 사용자 수동 메모` 항목 중 _안정·범용_ 한 것을 식별 (`<hint>` 주면 그 항목). 일회성·임시 메모는 대상 X.
2. 적절한 구조화 절(해당 aspect 본문)에 통합할 문안을 제안 → **preview → confirm** (analyze-user 의 "읽기만" 계약을 confirm 으로 보존).
3. 확정 시 구조화 절에 추가 + `## 사용자 수동 메모` 에서 그 항목 제거 (졸업) + frontmatter `changelog:` 한 줄.
4. _대량·정식 재구조화_ 가 필요하면 promote 대신 `/analyze-user` 를 권한다 (promote 는 가벼운 1-2 항목 졸업용).
- user_profile 직접 쓰기 자유 (convention) — 단 promote 는 analyze-user 영역 절을 건드리므로 preview→confirm 유지.

### `/post-it handoff [--no-confirm]`
**세션 인계 — sweep 먼저, 그 다음 hints 생성** (Claude 가 내용 생성).

1. **sweep 자동 포함** — `sweep` 로직을 돌려 _확실한_ graduated·stale 을 자동 prune (애매하면 keep). post-it 이 lean 해진 상태로 인계. 사용자에겐 줄 단위 검토 없이 _한 줄 보고_ ("졸업 N·stale M 정리"). 수동 호출 자리라면 preview→confirm.
2. **hints 생성** — 현 세션 conversation 을 review 해 다음 세션에 알아야 할 5-10 bullet 요약:
   - 지금 어디까지 진행했는지 / 다음 세션에서 먼저 할 일 / 미해결 질문·블로커 / 주의사항.
   - **제외**: 이미 산출물·git 에 영속화된 내용, post-it 의 다른 섹션에 이미 있는 내용 (sweep 후라 중복 적음).
3. **Default: preview → confirm** — 요약 bullets 를 보여주고 "이대로 `## Next Session Hints` 를 덮어쓸까요?" 확인. 사용자 직접 편집·추가 가능.
4. 확인 시 `## Next Session Hints` **전체 교체** (이전 hints 사라짐 — 누적 X). 누적 필요분은 `add thread` 로 보존.
5. `--no-confirm` 시 sweep·hints 검토 없이 즉시 적용. 적용 시 `Last Updated` 갱신.

## Confirm 정책 요약

| Sub-action | Default | Override |
|---|---|---|
| `show` / `init` | 즉시 | n/a |
| `add` / `decide` | 즉시 (사용자 텍스트 원문) | `--confirm` |
| `resolve` | preview → confirm (fuzzy 매칭) | `--no-confirm` |
| `sweep` (수동 호출) | preview → confirm (Claude 분류) | `--no-confirm` |
| `sweep` (자동 — nudge/handoff 내부) | 확실분 자동 prune + 한 줄 보고 (애매 keep) | n/a |
| `promote` | preview → confirm (Claude 제안 + 구조화 절 편집) | (없음 — 항상 confirm) |
| `handoff` (자동 nudge) | sweep 자동 포함 → 짧은 요약 보여주고 _저장 여부_ confirm | `--no-confirm` |

원칙: **사용자가 직접 적은 텍스트는 즉시, Claude 가 만들거나 매칭하는 경우는 검토.** 단 _사용자는 post-it 을 안 본다_ — 자동 자리의 prune 은 _확실한 것만_ 자동 적용 + 한 줄 보고 (애매하면 keep), 사용자에겐 액션 단위 confirm 만. 줄 단위 preview 는 사용자가 직접 `/post-it sweep` 칠 때.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — `~/.claude/projects/*/memory/` 의 user/feedback/project/reference 메모는 그대로. 본 skill 은 추가 layer.
- **영구 기록 X** — post-it 은 포스트잇. 영구 진실은 산출물·코드·git·구조화 프로필. 엔트리는 졸업하면 떼어낸다 (sweep/promote).
- **코드/문서 변경 기록 X** — `autopilot-code` 의 `plans/`, `autopilot-draft` 의 `documents/`.
- **세션 활동 로그 X** — `pipeline_summary.md` 등에 이미 누적.

post-it.md 는 "매 세션 시작 시 자동으로 떠올리고 싶은, 아직 산출물로 졸업하지 않은 한정된 정보"만 담는다.

## Auto-memory와의 경계

| 위치 | 범위 | 갱신 |
|---|---|---|
| `~/.claude/projects/*/memory/` (auto memory) | account-wide cross-project | Claude 자동 학습·기록 |
| `.claude_reports/post-it.md` (본 skill) | per-project (현 cwd 한정) | 사용자 `/post-it` 로만 |

구분:
- **이 레포에만 적용되는 사실** (노션 위치, 데이터셋 경로, 진행 중 작업) → post-it.md
- **사용자 자신 / 일반 작업 선호** (Korean output, 코드 스타일) → auto memory 또는 `--scope user`
겹치면 post-it.md 가 더 정확한 local context 라 우선.

## Writing Style (간결성 원칙 — 반드시 준수)

post-it.md 는 세션 시작 시 항상 읽히는 컨텍스트. **짧고 dense 하게.**

- **한 bullet = 한 줄** (정 길면 최대 2줄).
- **명사구 / 사실 문장**. 형용사·부사·접속사·존댓말·이유 설명 최소화.
  - ❌ `Overleaf 는 X 폴더 아래 정리하는 게 좋습니다. 이유는...`
  - ✅ `Overleaf 정리 위치: <Overleaf URL>/TF-Restormer`
- **핵심 어휘만**. 한·영 혼용 OK, 약어·기호(`→`, `&`, `vs`) 적극.
- **카테고리 중복 금지** — 같은 정보는 한 곳에만.
- **시간성**: Conventions / External Resources → 날짜 X. Decisions → `YYYY-MM-DD:` 필수. Open Threads → `[in-progress YYYY-MM-DD]` / `[blocked YYYY-MM-DD]` 필수. Next Session Hints → handoff 마다 통째 교체.
- **메타 코멘트 금지** — "TODO 추후 확인" 류 X. Open Threads 로.
- `handoff` 요약·`sweep` pointer 도 이 원칙 (1줄).

## Language Rule
- 사용자 대화는 한국어.
- post-it.md 본문은 사용자 언어 그대로 (한·영 혼용 OK).
- 카테고리 헤더는 영어 고정 (`## Conventions` 등) — 형식 안정성.

## Task

Argument `$ARG` 파싱:
- 비어 있으면 `show` (표시 또는 init 안내; post-it.md → legacy memo.md fallback).
- `init` → 템플릿 생성 (legacy memo.md 있으면 이전 제안).
- `add <category> <text>` → 섹션 bullet 추가.
- `resolve <hint>` → Open Threads fuzzy 제거.
- `decide <text>` → Decisions 추가.
- `sweep [--no-confirm] [--scope ...]` → 산출물 대조 후 graduated·stale prune (preview→confirm).
- `promote [<hint>] [--scope user [<aspect>]]` → user 메모를 구조화 절로 졸업.
- `handoff [--no-confirm]` → sweep 제안 → 세션 요약 → Next Session Hints 덮어쓰기.
- `--scope user [<aspect>]` 동반 시 user_profile aspect 파일의 `## 사용자 수동 메모` 절 대상 (쓰기 시 untracked ceremony 안내).
- 그 외 → 사용법 안내.
