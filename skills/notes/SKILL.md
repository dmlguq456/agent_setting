---
name: notes
description: Manually-controlled memory — two scopes. `--scope project` (default): `.claude_reports/NOTES.md` (per-cwd, 5 categories). `--scope user <aspect>`: `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절 (cross-project, aspect 기반 — 별도 NOTES 안 만들고 구조화 파일 안 _user-owned 자리_ 에 append). Auto-loaded at session start, edited only via explicit `/notes` sub-actions. Separate from the auto-memory system at `~/.claude/projects/*/memory/`.
argument-hint: "[show] | init | add <category> <text> | resolve <hint> | decide <text> | handoff [--no-confirm] [--scope project|user [<aspect>]]"
---

## 목적

사용자가 **직접 통제하는** 메모리. `~/.claude/projects/*/memory/`의 자동 메모리 시스템과는 별개로, 사용자가 명시적으로 `/notes` 명령을 호출할 때만 변경된다. 세션 종료 시 conversation이 사라지는 휘발성을 메우는 목적 (compact는 일시적 보존이라 불충분).

## Scope — project vs user

본 skill 은 _두 자리_ 에 자료를 저장할 수 있음. `--scope` flag 로 분기:

| Scope | 파일 위치 | 다루는 자료 | 자동 로드 |
|---|---|---|---|
| `project` (default) | `.claude_reports/NOTES.md` | 현 cwd 의 _프로젝트 단위_ 자료 — 진행 중 작업·결정·외부 자원·다음 세션 hint 등 | 글로벌 `~/.claude/CLAUDE.md` 도메인 트리거 |
| `user <aspect>` | `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절 (default aspect = `collab`) | _사용자 단위 cross-project_ 자료 — 범용 패턴·preference·도메인 메모. analyze-user 가 손대지 않는 _user-owned 자리_ 에 append | 별도 자동 로드 X (sub-agent 가 작업 자리에서 aspect 파일 Read 할 때 같이 적재) |

**Scope 선택 기준**:

- _이 프로젝트에서만 의미 있는 자료_ → `--scope project`
- _다른 프로젝트에서도 이어 쓸 사용자 자료_ → `--scope user <aspect>`
- 애매하면 `project` (default)

**user scope 의 aspect 선택**:

| aspect | 갱신 파일 | 들어갈 자료 예시 |
|---|---|---|
| `figure` | `01_paper_figure_style.md` | 시각·figure 관련 자기 선호 ("Times 폰트 고정") |
| `writing` | `02_paper_writing_style.md` | paper 작성 톤·표현 ("LLM-flavor _instantiation_ 회피") |
| `presentation` | `03_presentation_strategy.md` | 슬라이드 layout·서사 결정 |
| `analysis` | `04_analysis_methodology.md` | 데이터·실험 결과 분석 방법 메모 |
| `domain` | `05_domain_expertise.md` | 도메인 용어·선호 표현 |
| `collab` (default) | `06_collaboration_style.md` | 작업 흐름·feedback·결정 패턴 — 가장 흔한 자리 |

**왜 별도 NOTES.md 가 아니라 aspect 파일 안 _사용자 수동 메모_ 절인가**:

- 사용자 레벨 note 는 거의 항상 6 aspect 중 하나에 자연 분류.
- 별도 NOTES.md 만들면 _구조화 (analyze-user 영역)_ 와 _free-form (사용자 영역)_ 이 _두 파일로 분산_, sub-agent 가 Read 자리 늘어남.
- aspect 파일 안 _두 절_ (analyze-user 영역 + 사용자 수동 메모 영역) 로 책임 분리 + 한 Read 로 모두 적재.

**`/analyze-user` 와의 책임 분리**:

- `## 사용자 수동 메모` 절 — _사용자 영역_. analyze-user 는 _읽기만_ 하고 손대지 않는다.
- 그 외 모든 절 — _analyze-user 영역_. 사용자가 직접 Edit 해도 다음 update 사이클에 덮어쓰일 수 있음 (단, frontmatter `changelog:` 에 갱신 기록 남기면 보존).

## 파일 위치 & 자동 로드

- **project scope**: 현재 working directory의 `.claude_reports/NOTES.md` (단일 파일). 글로벌 `~/.claude/CLAUDE.md`의 도메인 트리거 표에 의해 메인 Claude가 새 세션 시작 시 Read. 파일이 없으면 무시.
- **user scope**: `~/.claude/user_profile/0X_*.md` 의 `## 사용자 수동 메모` 절. 자동 로드 X — sub-agent 가 작업 자리에서 aspect 파일을 Read 할 때 같이 적재 (메인 Claude 의 글로벌 도메인 트리거 무관).
- **갱신**: 항상 `/notes` 명령으로만. Claude가 자동으로 쓰지 않는다.

## 파일 형식 (5 카테고리)

```markdown
# Project Notes

- **Project**: {프로젝트 이름}
- **Last Updated**: YYYY-MM-DD

## Conventions
- (영속 규약 — 예: 노션 정리 위치, 커밋 메시지 언어)

## External Resources
- (외부 링크/경로 — 예: 데이터셋, Overleaf)

## Open Threads
- [in-progress] (현재 진행 중인 작업)
- [blocked] (사용자가 직접 수동 편집)

## Decisions
- YYYY-MM-DD: (그 시점의 의사결정과 사유)

## Next Session Hints
(가장 마지막 `/notes handoff` 결과로 **덮어쓰여짐** — 누적 X)
- (다음 세션에 알아야 할 현재 진행 상황·다음 할 일·주의사항)
```

## Sub-Actions

### `/notes` (인자 없음)
파일을 Read해서 그대로 표시. 파일이 없으면 `/notes init` 안내.

### `/notes init`
`.claude_reports/NOTES.md`가 없으면 위 템플릿으로 생성. `.claude_reports/` 디렉토리가 없으면 함께 생성. `Project` 필드는 현 directory의 basename을 default로, `Last Updated`는 오늘 날짜. 파일이 이미 있으면 "이미 존재" 표시하고 중단.

### `/notes add <category> <text>`
- `<category>` ∈ {`convention`, `resource`, `thread`, `decision`}. Alias: `conv`, `res`, `th`, `dec`.
- 해당 섹션 끝에 bullet 추가.
- `thread`는 `- [in-progress] ` prefix 자동.
- `decision`은 `- YYYY-MM-DD: ` prefix 자동 (오늘 날짜).
- `convention` / `resource`는 prefix 없이 `- ` bullet만.
- **사용자 텍스트 원문 그대로** 넣음 → **즉시 적용** (검토 X).
- `--confirm` flag 시 diff preview 후 사용자 확인 받음.
- 적용 시 `Last Updated` 갱신.

### `/notes resolve <hint>`
- `## Open Threads` 섹션에서 `<hint>` fuzzy 매칭으로 thread 찾아 제거.
- **default: preview → confirm**:
  - 1개 매칭: "이 항목을 제거할까요? `[in-progress] ...`" 사용자 확인 받음.
  - 여러 매칭: 번호로 사용자가 선택.
  - 0개 매칭: 매칭 없음 안내 후 중단.
- `--no-confirm` flag 시 가장 유사한 1개 즉시 제거.
- 적용 시 `Last Updated` 갱신.

### `/notes decide <text>`
- `## Decisions` 섹션에 `- YYYY-MM-DD: <text>` 추가 (오늘 날짜).
- 사용자 텍스트 원문 → **즉시 적용**.
- `--confirm` flag로 검토 가능.

### `/notes handoff [--no-confirm]`
**Claude가 내용을 생성하는 sub-action**.

1. 메인 Claude는 **현재 세션의 conversation history**를 review하여 다음 세션에 알아야 할 사항을 5-10 bullet로 요약. 다음을 포함:
   - 지금 어디까지 진행했는지 (현재 작업의 위치)
   - 다음 세션에서 가장 먼저 해야 할 일
   - 미해결 질문·블로커
   - 알아둬야 할 주의사항 (예: "tab 12 결과는 재실험 중, 인용 X")
   - **제외**: 이미 코드/문서/git에 영속화된 내용, 이미 NOTES.md의 다른 섹션에 들어가 있는 내용
2. **Default: preview → confirm**. 요약 결과(markdown bullets)를 사용자에게 보여주고 "이대로 `## Next Session Hints`를 덮어쓸까요?" 확인 받음. 사용자는 직접 편집·추가 요청 가능.
3. 확인 받으면 `## Next Session Hints` 섹션 **전체 내용 교체** (이전 hints는 사라짐 — 누적 X). 누적이 필요하면 사용자가 직접 `add thread`로 따로 보존.
4. `--no-confirm` flag 시 검토 없이 즉시 덮어씀.
5. 적용 시 `Last Updated` 갱신.

## Confirm 정책 요약

| Sub-action | Default | Override |
|---|---|---|
| `show` (default) / `init` | 즉시 | n/a |
| `add` / `decide` | 즉시 (사용자 텍스트 원문) | `--confirm` |
| `resolve` / `handoff` | preview → confirm (Claude 생성/매칭) | `--no-confirm` |

원칙: **사용자가 텍스트를 직접 적은 경우는 즉시, Claude가 내용을 만들거나 fuzzy 매칭하는 경우는 검토**.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — `~/.claude/projects/*/memory/`의 user / feedback / project / reference 메모는 그대로 작동. 본 skill은 추가 layer.
- **코드 변경 기록 X** — `autopilot-code`의 `plans/dev_logs/` 사용.
- **문서 변경 기록 X** — `autopilot-draft`의 `documents/` 사용.
- **세션 활동 로그 X** — pipeline_summary.md 등 다른 곳에 이미 누적됨.

NOTES.md는 "매 세션 시작 시 자동으로 떠올리고 싶은 한정된 정보"만 담는다.

## Auto-memory와의 경계

| 위치 | 범위 | 갱신 |
|---|---|---|
| `~/.claude/projects/*/memory/` (auto memory) | account-wide cross-project | Claude가 자동으로 학습·기록 |
| `.claude_reports/NOTES.md` (본 skill) | per-project (현 working directory 한정) | 사용자가 `/notes` 명령으로만 |

구분 기준:
- **이 레포에만 적용되는 사실** (이 레포의 노션 위치, 데이터셋 경로, 진행 중 작업 등) → NOTES.md
- **사용자 자신 / 일반 작업 선호** (Korean output, 코드 스타일 등) → auto memory

겹치는 경우 NOTES.md가 더 정확한 local context를 가지므로 우선.

## Writing Style (간결성 원칙 — 반드시 준수)

NOTES.md는 세션 시작 시 항상 읽히는 컨텍스트 파일. **짧고 dense하게** 유지.

- **한 bullet = 한 줄**. 줄바꿈 금지 (기본). 정 길어지면 최대 2줄.
- **명사구 / 사실 문장** 위주. 형용사·부사·접속사·존댓말·이유 설명 최소화.
  - ❌ `Overleaf 는 X 폴더 아래 정리하는 게 좋습니다. 이유는...`
  - ✅ `Overleaf 정리 위치: <Overleaf URL>/TF-Restormer`
- **핵심 어휘만**. 한국어/영어 혼용 OK, 약어·기호 (`→`, `&`, `vs`) 적극 사용.
- **카테고리 중복 금지**. 같은 정보는 한 곳에만. (예: 데이터셋 경로는 External Resources만, Conventions에 다시 적지 말 것.)
- **시간성**:
  - Conventions / External Resources → 시점 무관 (날짜 X).
  - Decisions → `YYYY-MM-DD: ` prefix 필수.
  - Open Threads → `[in-progress]` / `[blocked]` status prefix 필수.
  - Next Session Hints → 매 handoff에서 통째로 교체 (시점은 자동으로 "직전").
- **메타 코멘트 금지**. "TODO 추후 확인" 같은 막연한 표현 X — Open Threads로 옮길 것.

`handoff`가 요약을 생성할 때도 이 원칙 적용. 5-10 bullet, 각 bullet 1줄.

## Language Rule

- 사용자 대화는 한국어.
- NOTES.md 본문은 사용자 언어 그대로 보존 (한·영 혼용 OK).
- 카테고리 헤더는 영어 고정 (`## Conventions` 등) — 형식 안정성.

## Task

Argument `$ARG`를 파싱:
- 비어 있으면 `show` (파일 표시 또는 init 안내).
- `init` → 템플릿 생성.
- `add <category> <text>` → 해당 섹션 bullet 추가.
- `resolve <hint>` → Open Threads fuzzy 매칭 제거.
- `decide <text>` → Decisions 추가.
- `handoff [--no-confirm]` → 세션 요약 → Next Session Hints 덮어쓰기.
- 그 외 → 사용법 안내.
