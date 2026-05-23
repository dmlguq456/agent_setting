---
name: sync-skills
description: "Skills + Agents 정의 변경을 감지해 ~/.claude/README.md(GitHub)와 Notion 대문 페이지(Agents/Skills) 상단의 대시보드(워크플로우 map + cheat-sheet + 통합 가이드라인)를 동기화한다. drift 체크 전용 모드도 지원."
argument-hint: "[--check] [--readme-only] [--notion-only] [--force] [--prefer-local | --prefer-notion] [--auto-fix [--dry-run]]"
---

## Language Rule
- 사용자 응답은 한국어로.

## Purpose
스킬·에이전트를 수정한 후 매번 GitHub과 Notion에 일관된 정보가 반영되어 있는지 확인하는 도구.

**Source of Truth**:
- `~/.claude/skills/*/SKILL.md` + `~/.claude/agents/*.md` — 각 skill·agent의 frontmatter + 본문
- **`~/.claude/CONVENTIONS.md`** — family-wide 운영 규칙의 단일 source (QA 5단계 정의 / agent model 표기 / cross-doc invariants). 본 skill의 Step 5b가 본 문서를 canonical로 cross-doc grep해 drift 보고·자동 fix.

**파생 산출물**: GitHub README.md, Notion 대문 페이지 상단 대시보드

이 스킬은 Source of Truth로부터 README와 노션 대시보드를 재생성한다. 사용자가 두 파생물을 직접 편집해서는 안 된다 (자동 생성 표지 있음).

## Targets

### 입력
- **Skills**: `~/.claude/skills/*/SKILL.md`
- **Agents**: `~/.claude/agents/*.md`

자동 발견: `ls ~/.claude/skills/*/SKILL.md ~/.claude/agents/*.md`. 실제 sync 시점에 발견된 파일 list 가 진실. 본 SKILL.md 본문에는 카운트·명단 hardcode 안 함 — drift 의 자기참조 source 가 됨.

각 파일에서 추출:
- frontmatter `name`, `description`, `argument-hint` (skills only), `tools`, `model`
- argument-hint 파싱 → 옵션 값 (예: `--mode dev|debug`, `--from analyze|strategy|...`)

### 출력
1. **GitHub**: `~/.claude/README.md` (repo: `git@github.com:dmlguq456/claude_setting.git`, root: `~/.claude/`)
2. **Notion 대문 상단 대시보드**: `Agents/Skills` 페이지 (id: `34987c2b-b753-80d6-8df4-d6ce4d469bff`)
   - **상단 대시보드 영역**(자동 갱신): H1 `# 전체 워크플로우` ~ 첫 `<columns>` 직전까지
   - **하단 세부 영역**(보존, 갱신 X): `<columns>` 안의 Skills/Agents 서브페이지 링크들 + 페이지 하단 메모
3. **개별 skill/agent README ↔ Notion 자식 페이지** (양방향 동기화):
   - 로컬: `~/.claude/skills/{name}/README.md`, `~/.claude/agents/_notion_mirror/{name}.md`
   - Notion: 대문의 `<columns>` 영역에 링크된 자식 페이지 (UUID는 `.sync_state.json`에 매핑 저장)
   - 양방향: SHA 비교 → 다르면 last_edited_time / file mtime 비교 → newer가 source. 양쪽 모두 변경(충돌) 시 사용자 확인.
4. **상태 파일**: `~/.claude/skills/.sync_state.json` — 각 입력 파일의 SHA-256, README/Notion sync 시각, Notion 페이지 매핑

## Argument Parsing
- `--check`: drift만 보고하고 종료. 쓰기 작업 X.
- `--readme-only`: README.md (대문) + 개별 README만 갱신, Notion은 건드리지 않음.
- `--notion-only`: Notion 대문 상단 + 자식 페이지만 갱신, 로컬 README는 건드리지 않음.
- `--force`: SHA가 같아도 재생성 (포맷 일괄 적용·서식 수정에 사용).
- `--prefer-local`: 충돌 시 자동으로 local README가 source (Notion 덮어쓰기).
- `--prefer-notion`: 충돌 시 자동으로 Notion이 source (local README 덮어쓰기).
- `--auto-fix`: Step 5b에서 발견한 cross-doc invariant drift를 CONVENTIONS.md canonical wording으로 자동 교체 (default는 report-only). `--dry-run`과 조합 시 미리보기.

기본(인자 없음): drift 감지 → 변경 있으면 README + Notion 모두 갱신. 개별 README ↔ Notion 양방향은 newer side가 source, 충돌 시 사용자 확인.

## Pipeline

### Step 1: Discover + hash
```bash
ls ~/.claude/skills/*/SKILL.md ~/.claude/agents/*.md
```
각 파일:
- SHA-256 (`shasum -a 256 <file> | awk '{print $1}'`)
- frontmatter 파싱 (간단한 YAML 파서: 첫 `---` ~ 두 번째 `---`)

### Step 2: Read sync state
`~/.claude/skills/.sync_state.json` 로드. 없으면 빈 dict.

스키마:
```json
{
  "version": 3,
  "last_readme_sync": "ISO8601",
  "last_notion_sync": "ISO8601",
  "items": {
    "skills/autopilot-code": {
      "sha256": "...",
      "synced_at": "ISO8601",
      "readme_path": "skills/autopilot-code/README.md",
      "readme_sha256": "...",
      "readme_mtime": "ISO8601",
      "notion_page_id": "32787c2b-b753-81d4-8170-dae1e5074b5c",
      "notion_last_edited_time": "ISO8601",
      "notion_synced_sha256": "..."
    },
    "agents/research-team": {
      "sha256": "...",
      "synced_at": "ISO8601",
      "readme_path": "agents/research-team.README.md",
      "readme_sha256": "...",
      "readme_mtime": "ISO8601",
      "notion_page_id": "34987c2b-b753-818a-a2c0-cd5a9a0b3237",
      "notion_last_edited_time": "ISO8601",
      "notion_synced_sha256": "..."
    }
  }
}
```

- `sha256` / `synced_at` — SKILL.md 자체 (frontmatter parsing source)
- `readme_path` / `readme_sha256` / `readme_mtime` — 로컬 README의 동기화 상태
- `notion_page_id` / `notion_last_edited_time` / `notion_synced_sha256` — Notion 자식 페이지 매핑과 마지막 동기화 시점의 본문 SHA. `notion_synced_sha256`은 _마지막 sync 시점의 Notion 본문 hash_로, 다음 sync에서 변경 감지 기준으로 사용.

> **version migration**: v2 state JSON 로드 시 `readme_path` / `notion_page_id` 자동 채움 (skill name 기반 fuzzy lookup + Agents/Skills 대문 페이지의 columns에서 child page URL parsing).

### Step 3: Drift report
**신규 / 변경 / 삭제 / 동일** 4 분류. 한국어 출력:
```
Sync 상태 (2026-05-06 12:34 KST)
─────────────────────────────────────
Skills:  변경 3 / 신규 0 / 삭제 0 / 동일 9
Agents:  변경 0 / 신규 0 / 삭제 0 / 동일 8

[변경된 항목]
  ✏️  skills/autopilot-code   (마지막 sync: 2026-04-21)
  ✏️  skills/autopilot-draft    (마지막 sync: 2026-04-21)
  ✏️  skills/init-plan        (마지막 sync: 2026-04-21)

마지막 README sync: 2026-04-21 09:08
마지막 Notion sync: 2026-04-21 01:26
```

`--check`이면 종료.

### Step 4: Generate dashboard sections (공통 — README와 Notion 상단 모두 사용)

#### 4a. 워크플로우 다이어그램

A(사전조사) → B(코드)/C(문서) → D(점검) → E(정정) 5 갈래 큰 그림만. 옵션 플래그·호출 구조는 README 본문에서 _자연어 사용 표_ 가 대체.

```mermaid
flowchart LR
    ANA["analyze-project<br/>(code/paper/doc)"]
    RES["autopilot-research"]
    CODE["autopilot-code"]
    DOC["autopilot-draft"]
    REF["autopilot-refine<br/>(doc + research 정정)"]
    AUD["audit<br/>(모든 산출물 점검)"]
    ANA --> CODE
    ANA --> DOC
    RES --> CODE
    RES --> DOC
    RES --> REF
    DOC --> REF
    RES --> AUD
    DOC --> AUD
    CODE --> AUD
    AUD -.->|auto-fix doc/research| REF
    AUD -.->|auto-fix plans| CODE
```

> 다이어그램 직후 본문은 _5 카테고리 bullets_ (A 사전조사 / B 코드 / C 문서 / D 점검 / E 정정) + _3-tier 산출물 컨벤션 reference_ (CONVENTIONS.md §5) 까지만. 파이프라인별 prose·체이닝 패턴 prose·사용자 개입 지점 prose 는 새 layout 에서 _넣지 않음_ (자연어 사용 표 §2 가 대체).
>
> **Agent 호출 구조 mermaid 는 자동 생성에서 제외** — 새 README 핵심 메시지는 _자연어로 부르면 메인 Claude 가 알아서 컨펌받고 진행_ 이라 호출 구조 강조는 정보 dump. 필요 시 각 agent .md 또는 글로벌 CLAUDE.md 도메인 트리거에서 참조.

#### 4b. README 본문 구조 (canonical layout — 자연어 사용 표 중심)

`~/.claude/README.md` 가 본 sync 의 단일 진실 출처 (reference layout). sync 시 다음 순서로 7 섹션을 채운다:

1. **Header** — title + source 안내 (`/sync-skills` 자동 갱신 표지) + Notion 대문 링크 + 운영 가이드 (`notion_guide.md`) 링크. sync 시각·이력은 git commit log 가 단일 출처.
2. **📊 워크플로우** — workspace 전제 quote (Claude 는 프로젝트 루트에서 실행 / `.claude_reports/` 현재 dir 생성 / `--refs` flag 없음) + sub-section 두 개:
   - `### Skill 호출 흐름` — Diagram 1 (위 4a) + 5 카테고리 한 줄 (A 사전조사 / B 코드 / C 문서 / D 점검 / E 정정)
   - `### 산출물 I/O (\`.claude_reports/\` 관점)` — Diagram 2 (산출물 I/O mermaid) + 누적 디렉토리 안내 + D/E 역할 한 줄 (D 는 OUT 을 _읽기만_ + 자동 fix dispatch / E 는 OUT 을 _read+write_ 양방향)
   - 3-tier 산출물 컨벤션 reference + 산출물 위치·scope·함정 reference (글로벌 CLAUDE.md "Drift-Free Essentials")
3. **🗣️ 사용 방식** (핵심 섹션 — _§3.(1) 자연어 발화 예시 표는 사람 유지 영역_)
   - 두 갈래 평등 prose 한 줄 (자연어 발화 / 직접 slash 입력 — 동일 skill 동일 동작)
   - `### (1) 자연어 발화로 부르기` — prose (메인 Claude 의 옵션 자동 구성 + 자연어 한 줄 요약 + 옵션 펼침 + 옵션 선택 근거 컨펌 흐름 + yes/수정/cancel/자율 진행) + ceremony 큰 5 (autopilot-* 4 + analyze-user) vs 작은 3 (audit / notes / analyze-project) 컨펌 의무 안내 + 글로벌 [`CLAUDE.md`](CLAUDE.md) §6 reference + **자연어 발화 예시 표** (사용자 발화 / 메인 Claude 컨펌 자연어 요약 — 6 행 정도, _사람 유지_)
   - `### (2) slash 명령 직접 입력` — prose (직접 입력 = 의도 명시 = 컨펌 skip 즉시 invoke 안내) + slash 예시 code block (autopilot-code / autopilot-draft / autopilot-research / autopilot-refine / audit / notes 6 줄, SKILL.md frontmatter `argument-hint` 에서 자동 생성) + QA 5단계 단일 정의는 [`CONVENTIONS.md`](CONVENTIONS.md) §1 reference
4. **📋 Skills** — name (SKILL.md 링크) / 역할 표만. 옵션 dump **X**. 표 직후 sub-skill 한 줄 + 세부 옵션은 각 SKILL.md `## Usage` reference 안내.
5. **🤝 Agents** — name (agent .md 링크) / 모델 / 역할 표. _자동 호출자 컬럼 X_ (새 패턴은 자연어로 부르면 메인 Claude 가 알아서). 직접 호출 안내 한 단락. Notion sub-agent 위임 X 주의 한 줄.
6. **⚙️ 운영 룰** — 한 단락. _자동 호출 패턴은 글로벌 [`CLAUDE.md`](CLAUDE.md) 가 단일 source of truth_ 안내. §6 autopilot-* 호출 패턴 + 도메인 트리거 표 reference. 각 SKILL.md `## Default Invocation Rule` 은 _그 SKILL.md 안에서만_ 의미 — README 에 모으지 않음.
7. **🔁 동기화** — `/sync-skills` 두 명령 + GitHub 링크

원칙:
- prose 최소화, 표·bullet 우선. 단 §2 _자연어 사용 방식_ 섹션은 _자연어 발화 예시 표_ 가 핵심 anchor 라 단단히 유지.
- 같은 정보를 두 군데 반복하지 않음 (옵션 spec 은 각 SKILL.md 가 source, autopilot 호출 룰은 글로벌 CLAUDE.md §6 가 source).
- _넣지 않음_ 항목 (의도적 제거):
  - 호출 구조 mermaid (Agent 측)
  - "자주 쓰는 명령" 시나리오 × 명령 표
  - "핵심 옵션 3가지" prose (`--user-refine` / `--from` / `--qa`)
  - 파이프라인별 prose / 체이닝 패턴 prose
  - Skills 표의 "주요 옵션" 컬럼 (argument-hint 자동 추출)
  - 운영 룰 표 (skill 별 4컬럼 dump)

**§3.(1) 자연어 발화 예시 표는 _사람 유지 영역_** — 자연어 발화 예시 표는 사람 손길 큐레이션 자료라 자동 생성 어려움. sync-skills 는 _현행 README 의 §3.(1) 자연어 발화 표 + 그 직전 prose 한 두 단락 을 그대로 보존_ 하고 (SHA 비교 skip), 나머지 (§1·§2·§3.(2)·§4-§7) 만 자동 갱신. 사용자가 §3.(1) 을 직접 편집해도 sync-skills 가 덮어쓰지 않음.

현행 README 가 본 layout 의 reference. 대규모 변경 시 README 를 먼저 손보고 본 SKILL.md 를 동기화.

### Step 5: Write README.md

`~/.claude/README.md` 를 4b 의 layout 그대로 작성. 단 _섹션별 자동 갱신 정책_ 이 다름:

| 섹션 | 처리 |
|---|---|
| §1 Header | 표지 텍스트 / Notion 링크 / 운영 가이드 링크 자동 갱신 |
| §2 워크플로우 | Diagram 1 (Skill 호출 흐름) + 5 카테고리 한 줄 + Diagram 2 (산출물 I/O `.claude_reports/` 관점) + 3-tier 컨벤션 reference 자동 갱신. workspace 전제 quote 고정 wording |
| **§3 사용 방식** | **§3.(1) 자연어 발화 예시 표 + 그 직전 prose 는 사람 유지 영역 — 현행 wording 그대로 보존 (SHA 비교 skip).** 사용자가 직접 편집한 발화 예시 표 그대로. 단 _섹션 헤딩 자체_ 가 누락됐으면 placeholder 헤딩 + 한 줄 안내만 자동 삽입. §3.(2) slash 예시 code block 은 각 SKILL.md frontmatter `argument-hint` 에서 자동 생성 + ceremony 큰 5 (autopilot-* 4 + analyze-user) vs 작은 3 (audit / notes / analyze-project) 컨펌 의무 안내·QA 5단계 reference 자동 갱신 |
| §4 Skills 표 | name / 역할 자동 추출. 옵션 컬럼 X. 새 skill 추가·삭제 자동 반영 |
| §5 Agents 표 | name / 모델 / 역할 자동 추출. 자동 호출자 컬럼 X |
| §6 운영 룰 | _글로벌 CLAUDE.md §6 가리킴 한 단락_. 표 자동 채우기 X |
| §7 동기화 | 두 명령 + GitHub 링크 고정 wording |

**sync 시각·이력은 README 본문에 쓰지 않음** (git commit log 가 단일 출처).

### Step 5a: 편집팀 검수 (사용자 영역 wording — LLM 스러운 어조 회피)

Step 5 에서 README 본문 wording 을 자동 생성·갱신한 자리 (§1 Header / §2 워크플로우 / §3.(2) slash 명령 직접 입력 / §4 Skills 표 wording / §5 Agents 표 wording / §6 운영 룰 / §7 동기화) 는 메인 Claude 가 wording 을 직접 짜므로 _LLM 스러운 인공적 어조_ (풀어쓰기 과잉·모범생 화법·친절 안내체) risk. Step 5 자동 갱신 직후 _같은 turn 안에_ `Agent(편집팀)` _다듬기 모드_ 호출해 검수.

**검수 범위** — Step 5 가 _자동 갱신_ 한 섹션만. _§3.(1) 자연어 발화 예시 표 + 그 직전 prose_ 는 _사람 유지 영역_ (이미 사람 손길 큐레이션) 이므로 검수 제외.

**Prompt 초점** (Agent 호출 시 그대로 전달):
- 풀어쓰기 과잉 정리 (한 줄 표현 가능한 자리)
- 모범생·친절 안내체 ("~가 평등하게 있습니다" / "어느 쪽을 써도 ~합니다") 회피
- 간결·단정 한국어 (`~다` / `~이다` 어미)
- 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §1 한국어 가독성 정책 + 도메인 트리거 표 _사용자 영역 메타 문서 작성·수정_ 행 준수
- 표·코드 블록·heading 구조·mermaid·링크는 그대로 유지 (의미·구조 변경 X, 어조만)

**Skip 조건** — `--notion-only` 일 때만 README 안 만지므로 검수 skip. `--readme-only` / `--force` / default 는 모두 검수 포함. `--check` 는 drift 보고만이라 Step 5 자체가 안 돌아 검수 무관.

> 본 step 추가 사유 (2026-05-22): 사용자가 README §3 사용 방식 첫 줄 _"두 가지 입구가 평등하게 있습니다 — 자연어로 부르기 와 직접 slash 입력. 어느 쪽을 써도 같은 skill 이 같은 방식으로 동작합니다."_ 같은 LLM 스러운 어조 지적. 자동 sync 가 매번 같은 risk 재발하지 않도록 검수 단계 의무화.

### Step 5b: Cross-doc invariant scan (QA 정의 & family-wide 규칙)

> 각 SKILL.md `## Default Invocation Rule` 은 _그 SKILL.md 안에서만_ 의미를 가지고 README 에 모으지 않음 (README §6 운영 룰은 _글로벌 CLAUDE.md §6 가리킴 한 단락_). autopilot-* 4 개 SKILL.md 의 trigger 신호·default 옵션·override 는 글로벌 §6 의 일반 패턴 + 각 SKILL.md 의 skill-specific 정보로 분리.

QA level / model 표기 / family-wide invariant은 **`~/.claude/CONVENTIONS.md`**가 단일 source of truth. 각 SKILL.md / README / `_notion_mirror`의 QA 표 wording은 본 문서와 의미상 일치해야 함.

#### 5b-1. Canonical 정의 로드

```bash
# Read CONVENTIONS.md fully; then parse:
#   §1.1 5단계 공통 정의 표 → QA wording (canonical)
#   §2 Agent Model 표기 → agent model 정의
#   §3 Hard Cross-Doc Invariants → invariant rule list
```

이로부터 5단계 정의(quick/light/standard/thorough/adversarial)의 _구성_을 추출 (Quality reviewer / Fact-checker / Codex 컬럼 wording).

#### 5b-2. 모든 .md 파일에서 QA wording 추출

대상 파일:
- `~/.claude/skills/*/SKILL.md`
- `~/.claude/skills/*/README.md`
- `~/.claude/agents/*.md`
- `~/.claude/agents/_notion_mirror/*.md`
- `~/.claude/README.md`

각 파일에서 다음 패턴 grep:
- `adversarial` 정의 문장 (예: `adversarial = ...`, `Adversarial | ...`, `adversarial.*Codex`)
- `quick`/`light`/`standard`/`thorough` 정의 표 행
- "fact-checker" 적용 여부
- model 표기 (`opus`, `sonnet`, 가변 표기)

#### 5b-3. Invariance 검사 (drift 보고)

각 추출된 wording을 canonical 정의와 비교. 다음 drift 패턴을 _하드 검사_:

| Invariant | 검사 패턴 | drift 시 보고 |
|---|---|---|
| **adversarial = thorough + Codex** | `adversarial.*standard.*Codex` 또는 `adversarial.*=.*standard` | 🔴 `잘못된 정의: adversarial 은 thorough + Codex 이지 standard + Codex 가 아님` |
| **autopilot-code 는 fact-checker 없음** | autopilot-code/SKILL.md or autopilot-code/README.md 에서 `fact-checker` 언급 (단, "doc/research 에만" 이라는 negative 안내는 OK) | 🔴 `code 파이프라인은 fact-checker 미적용` |
| **autopilot-* + analyze-user adversarial 지원** | autopilot-code / autopilot-draft / autopilot-research / autopilot-refine / analyze-user 의 argument-hint 에 `adversarial` 누락 | 🔴 `2026-05-22 통일 — analyze-user 는 adversarial 고정, 나머지 4 개는 default thorough + adversarial 지원` |
| **quick 은 refine skip + 1라운드 강제 종료** | quick 정의에서 위 둘 중 하나 누락 | 🟡 `quick 정의 incomplete` |
| **`--no-fact-check` / `--no-style-audit` 는 autopilot-refine·audit 전용** | 다른 skill 의 argument-hint 에 노출 | 🔴 `해당 flag 는 refine·audit 외 노출 금지` |

#### 5b-4. 보고 형식

drift 발견 시 Step 8 final report에 별도 섹션:
```
[QA invariant drift]
🔴 skills/autopilot-refine/SKILL.md:46 — adversarial 정의가 'standard + Codex'로 잘못 적힘 (canonical: 'thorough + Codex')
🟡 skills/autopilot-research/SKILL.md:632 — quick 정의에 'refine skip' 명시 누락
```

자동 fix 정책 (CONVENTIONS.md §4):
- **default (report-only)**: drift 보고만, 수정 안 함
- **`--auto-fix`** flag 시: CONVENTIONS.md §3 hard invariants 위반은 canonical wording으로 강제 교체. 단 _wording 자체_가 다를 경우 (의미 동일·표현 차이): skip (사람 결정). _의미가 다른_ 명백한 drift만 propagate.
- **`--auto-fix --dry-run`**: 미리보기 (실제 write 안 함)
- `--check` 모드에서는 invariant drift만 보고하고 종료 (auto-fix 자동 적용 안 함).

> **새 invariant 추가**: CONVENTIONS.md §3에 한 행 추가하면 sync 시 자동 검사 list에 포함.

### Step 5c: 개별 README ↔ Notion 자식 페이지 양방향 sync

대문 README (§5)과 별개로 **각 skill/agent의 개별 설명 페이지**가 Notion에 자식 페이지로 존재한다. 본 단계는 그것들과 로컬 `~/.claude/skills/{name}/README.md`·`~/.claude/agents/_notion_mirror/{name}.md`를 양방향 동기화한다.

#### 5c-1. README ↔ Notion 매핑 발견

각 SKILL.md / agent.md에 대해:

1. **Local README path**:
   - skill: `~/.claude/skills/{name}/README.md` — Claude Code skill loader는 `SKILL.md`만 스캔하므로 같은 폴더의 README.md는 자동 로드되지 않아 안전.
   - agent: `~/.claude/agents/_notion_mirror/{name}.md` — `_notion_mirror/` 서브디렉토리로 격리 (agent loader는 `~/.claude/agents/*.md` top-level만 스캔하므로 README가 agent로 오인되지 않음).
   - **Naming rationale**: 과거 `agents/{name}.README.md` 형태는 `*.md` glob에 매칭돼 agent loader가 잘못 로드할 위험이 있어 `_notion_mirror/{name}.md`로 격리.
2. **Notion page id**: `.sync_state.json`의 `notion_page_id` field. 없으면:
   - 대문 페이지(id `34987c2b-b753-80d6-8df4-d6ce4d469bff`)의 `<columns>` 영역을 fetch
   - `<page url="https://www.notion.so/{uuid}">{title}</page>` 패턴에서 title↔skill name fuzzy match
   - 매칭 발견 시 UUID 추출해 state에 저장. 없으면 sync 대상에서 skip + 사용자에게 안내 ("Notion 자식 페이지 없음 — 수동 생성 권장").

#### 5c-2. 변경 감지 (3-way)

각 매핑된 pair에 대해 현재 상태 hash 계산:

- `local_now_sha` — `shasum -a 256 {local_readme_path}` (없으면 null)
- `notion_now_sha` — `notion-fetch` 후 `<content>...</content>` 본문만 추출해 SHA-256
- 비교 baseline: state JSON의 `readme_sha256` (지난 sync 시점 local hash) + `notion_synced_sha256` (지난 sync 시점 notion hash)

변경 분류:

| local 변경 | notion 변경 | 처리 |
|---|---|---|
| ✅ | ❌ | local → notion push (local이 source) |
| ❌ | ✅ | notion → local pull (notion이 source) |
| ✅ | ✅ | **충돌**. `--prefer-local`/`--prefer-notion` 명시 시 자동 처리, 아니면 사용자에게 양쪽 diff 보여주고 선택 요청 |
| ❌ | ❌ | skip (동일) |
| local null + notion ✅ | — | notion → local 1회 마이그레이션 (로컬 README 신규 생성) |
| local ✅ + notion null | — | local → notion 1회 마이그레이션 (Notion 자식 페이지 신규 생성; 새 페이지 ID를 state에 저장) |

`--force` 시: 변경 감지 결과 무시하고 양쪽 모두 local → notion 방향으로 갱신 (또는 사용자가 명시한 방향).

#### 5c-3. README → Notion push

- `update_content`로 페이지 본문 교체. 본문은 ancestor-path / properties wrapper를 제외한 markdown 그대로.
- 큰 본문은 `replace_content` 유혹이 있지만 **사용 금지**. 자식 페이지 삭제 위험. 대신 두 단계:
  1. fetch 후 현재 본문을 정확히 capture
  2. `update_content`로 _전체 본문_ 단일 (old_str, new_str) 쌍으로 교체
- 페이지 본문에 `<page>` / `<database>` 자식 링크가 있으면 (예: autopilot-code 페이지의 sub-skill 링크) **그 라인은 new_str에 포함시켜 보존**.
- 성공 시 state의 `notion_synced_sha256` = new_str의 SHA, `notion_last_edited_time` = update 응답의 시각.

#### 5c-4. Notion → README pull

- `notion-fetch`로 본문 가져옴 → ancestor-path / properties wrapper 제거 → `Write`로 local README 갱신.
- 첫 마이그레이션 시 README 상단에 `> 본 README는 Notion 페이지 [{title}]({url})의 미러. /sync-skills로 양방향 동기화` 헤더 추가.
- state의 `readme_sha256` / `readme_mtime` 갱신.

#### 5c-5. 새 페이지 생성 (local-only → Notion)

local README는 있는데 Notion에 매칭 페이지 없음:

1. `mcp__claude_ai_Notion__notion-create-pages` 호출
2. parent: 대문 페이지의 `<columns>` 영역 (skill은 첫 컬럼, agent는 두 번째 컬럼). 단, 컬럼 안에 새 페이지 추가는 MCP가 직접 지원 안 할 수 있음 — 그 경우 대문 페이지 직속 자식으로 생성 후 사용자에게 "컬럼에 이동 필요" 안내.
3. 생성 응답의 page_id를 `.sync_state.json`에 저장.
4. **로컬 README의 stub 헤더 교체** — local README가 `> ⚠️ **Notion 페이지 없음**...` stub 헤더로 시작하면, 표준 미러 헤더 `> 본 README는 Notion 페이지 [{icon} {name}]({url})의 미러. \`/sync-skills\`로 양방향 동기화. 권위 있는 동작 명세는 \`SKILL.md\` (skill) 또는 \`{agent_basename}.md\` (agent).` 로 교체. 누락 시 다음 sync에서 stub이 영구히 남는 버그가 발생 (예: 2026-05-12 audit/autopilot-refine/sync-skills 3건).

#### 5c-6. 충돌 처리 (양쪽 모두 변경)

```
[충돌 감지] skills/autopilot-draft
  Local README:  마지막 수정 2026-05-12 14:30 (5분 전)
  Notion 페이지: 마지막 수정 2026-05-12 14:25 (10분 전)
  
어느 쪽을 source로 할까요?
  (a) Local (Notion 덮어쓰기)
  (b) Notion (Local 덮어쓰기)
  (c) Skip (이번 sync에서 둘 다 두기)
  (d) Diff 보기
```

`--prefer-local` / `--prefer-notion` flag로 자동화. CI/script에서 사용.

#### 5c-7. 안전 규칙

1. **content_updates는 항상 두 단계 이상으로 분리** (전체 본문 교체 + 마지막 업데이트 라인). 단일 큰 교체는 part-of-match 실패 위험.
2. **`<page>` / `<database>` 자식 링크는 항상 new_str에 포함**. 누락 시 자식 페이지 분리.
3. local README 신규 생성 시 같은 디렉토리에 `SKILL.md` 또는 `.md`가 존재하는지 먼저 확인. 잘못된 디렉토리에 생성하지 말 것.
4. Notion fetch 실패 (404 / 권한) → 해당 pair는 sync 대상에서 skip + 사용자 보고. state는 변경 안 함.
5. 본문이 매우 큰 페이지 (`>50KB`) 는 `update_content`가 실패할 수 있음. 그 경우 사용자에게 안내 + 수동 동기화 요청.

### Step 6: Update Notion 대문 상단 (메인 컨텍스트 직접 호출)

페이지 id: `34987c2b-b753-80d6-8df4-d6ce4d469bff`

**원칙**: 메인 컨텍스트에서 Notion MCP 도구를 직접 호출 (sub-agent runtime 에서 MCP 도구 미접근). 자식 페이지 보존 등의 안전 규칙은 본 SKILL.md + `~/.claude/notion_guide.md`에 명시.

> 노션 운영 가이드 참조: `~/.claude/notion_guide.md` (페이지 타입 템플릿 + workspace 구조 + 일반 운영 규칙)

#### 6a. MCP 도구 로드

deferred tool 로드 (5c와 공유):
```
ToolSearch(query="select:mcp__claude_ai_Notion__notion-fetch,mcp__claude_ai_Notion__notion-update-page,mcp__claude_ai_Notion__notion-create-pages")
```

#### 6b. 페이지 fetch + update

```python
# 1. fetch 현재 콘텐츠
mcp__claude_ai_Notion__notion-fetch(id="34987c2b-b753-80d6-8df4-d6ce4d469bff")

# 2. update_content 두 단계로 분리:
#    - (a) 상단 대시보드 영역 교체 (시작 헤더 ~ columns 직전 `---`)
#    - (b) 페이지 하단 `*마지막 업데이트: ...*` 라인의 날짜만 갱신
mcp__claude_ai_Notion__notion-update-page(
    page_id="34987c2b-b753-80d6-8df4-d6ce4d469bff",
    command="update_content",
    properties={},
    content_updates=[
        {"old_str": "<현재 대시보드 영역의 정확한 워딩>", "new_str": "<새 대시보드 콘텐츠>"},
        {"old_str": "*마지막 업데이트: <기존 날짜>*", "new_str": "*마지막 업데이트: <새 날짜 + 변경 요약>*"}
    ]
)
```

#### 6c. 안전 규칙 (반드시 준수)

1. **`update_content`만 사용**. `replace_content`는 사용 금지 — 자식 페이지 삭제 위험.
2. **`<columns>` 안의 `<page>` / `<database>` 자식 링크는 절대 삭제 X**. old_str에 그 영역을 포함시키지 말 것.
3. **search-and-replace는 두 단계로 분리** (위 6b 참조).
4. fetch 결과의 워딩과 old_str이 한 글자도 어긋나면 실패. 정확히 복사.
5. 첫 시도 실패(validation_error 등) 시 재시도하되, `allow_deleting_content`는 절대 true 설정 X.
6. 작은 부분만 변경하면 _전체 대시보드 교체_ 대신 _변경된 줄만_ 다중 update_content 작업으로 처리 — 안전성 ↑.

#### 6d. 결과 확인

update_content 성공 응답 (`{"page_id": "..."}`)을 받으면 변경 영역을 사용자에게 한 줄 요약. 실패 시 사용자에게 보고하고 종료 — 자동 재시도는 1회까지만 (old_str 정정 후).

### Step 7: Update sync state
`~/.claude/skills/.sync_state.json`을 새 SHA + 시각으로 저장. v3 스키마 필드 모두 갱신:

- SKILL.md / agent.md: `sha256`, `synced_at`
- 로컬 README: `readme_sha256`, `readme_mtime`
- Notion 자식 페이지: `notion_page_id` (신규 매핑 시), `notion_last_edited_time`, `notion_synced_sha256`
- 전역: `last_readme_sync`, `last_notion_sync`

### Step 8: Final report
```
✅ Sync 완료
─────────────────────────────────────
SKILL.md/agent.md 변경: 3 (autopilot-code, autopilot-draft, init-plan)
README ↔ Notion 자식 페이지:
  - local → notion push: 2 (autopilot-draft, qa-team)
  - notion → local pull: 1 (browser-team)
  - 신규 매핑: 1 (audit — Notion 페이지 생성)
  - 충돌 (사용자 결정): 0
대문 페이지 갱신: Agents/Skills
README.md 갱신: ~/.claude/README.md
Notion 대문 갱신: Agents/Skills (workflow + cheat-sheets)

다음에 PR/푸시:
  cd ~/.claude && git add README.md skills/ agents/
  git commit -m "skills+agents: <변경 요약>"
  git push
```

## Hook integration (옵션)
`~/.claude/settings.json`에 다음 추가하면 세션 종료 시 drift 알림:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "find ~/.claude/skills ~/.claude/agents -name '*.md' -newer ~/.claude/skills/.sync_state.json 2>/dev/null | head -1 | grep -q . && echo '[sync-skills] drift detected — run /sync-skills' || true"
      }]
    }]
  }
}
```

자동 sync는 권하지 않음 (편집 중간마다 노션이 푸시되면 노이즈) — 명시적 호출 + drift 알림만이 권장 패턴.

## Safety Rules
- README.md는 자동 생성 표지가 있는 경우에만 덮어쓴다. 사용자 수동 편집 흔적이 감지되면 abort + 경고.
- Notion 대문 페이지의 `<page>` / `<database>` 자식 링크는 절대 삭제 금지. `update_content` 부분 교체만.
- `--force` 없이는 SHA 동일 항목은 처리 스킵.
- sync state JSON parse 실패 시 backup으로 옮기고 빈 dict로 재시작 (모든 항목을 변경으로 처리).
- Notion MCP 호출 실패 시 README 갱신은 진행, `last_notion_sync`만 갱신 보류 (다음 호출에서 재시도).
- 자기 자신(`sync-skills/SKILL.md`) 갱신도 동일하게 처리 (메타 — `sync-skills`가 자기 hash를 state에 기록).
- **개별 README ↔ Notion 양방향**: 충돌(양쪽 모두 last_sync 이후 변경) 시 자동 해결 금지 — `--prefer-local`/`--prefer-notion` 명시 또는 사용자 응답이 있어야 진행.
- **README 신규 마이그레이션**: 로컬에 README 없고 Notion에만 있는 경우 (또는 그 반대) 사용자 확인 _없이_ 자동 생성 (1회성 양방향 부트스트랩 — 그래야 #5 같은 수동 마이그레이션이 불필요).
- 본문이 매우 긴 페이지 (> 50KB) 는 update_content 실패 가능 — 사용자에게 안내하고 수동 sync 권장. state는 변경 안 함.

## Task
$ARGUMENTS
