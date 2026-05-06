---
name: sync-skills
description: "Skills + Agents 정의 변경을 감지해 ~/.claude/README.md(GitHub)와 Notion 대문 페이지(Agents/Skills) 상단의 대시보드(워크플로우 map + cheat-sheet + 통합 가이드라인)를 동기화한다. drift 체크 전용 모드도 지원."
argument-hint: "[--check] [--readme-only] [--notion-only] [--force]"
---

## Language Rule
- 사용자 응답은 한국어로.

## Purpose
스킬·에이전트를 수정한 후 매번 GitHub과 Notion에 일관된 정보가 반영되어 있는지 확인하는 도구.

**Source of Truth**: `~/.claude/skills/*/SKILL.md` + `~/.claude/agents/*.md` (frontmatter)
**파생 산출물**: GitHub README.md, Notion 대문 페이지 상단 대시보드

이 스킬은 Source of Truth로부터 README와 노션 대시보드를 재생성한다. 사용자가 두 파생물을 직접 편집해서는 안 된다 (자동 생성 표지 있음).

## Targets

### 입력
- **Skills**: `~/.claude/skills/*/SKILL.md` (현재 12개: autopilot-research/code/doc, init-plan, refine-plan, execute-plan, run-test, final-report, init-doc-strategy, refine-doc-strategy, analyze-project, analyze-papers, sync-skills 자기 자신)
- **Agents**: `~/.claude/agents/*.md` (현재 8개: 기획팀/품질관리팀/개발팀/테스트팀/연구팀/탐색팀/기록팀/codex-review-team)

자동 발견: `ls ~/.claude/skills/*/SKILL.md ~/.claude/agents/*.md`. 위 목록은 현재 알려진 항목.

각 파일에서 추출:
- frontmatter `name`, `description`, `argument-hint` (skills only), `tools`, `model`
- argument-hint 파싱 → 옵션 값 (예: `--mode dev|audit|debug`, `--from analyze|strategy|...`)

### 출력
1. **GitHub**: `~/.claude/README.md` (repo: `git@github.com:dmlguq456/claude_setting.git`, root: `~/.claude/`)
2. **Notion 대문**: `Agents/Skills` 페이지 (id: `34987c2b-b753-80d6-8df4-d6ce4d469bff`)
   - **상단 대시보드 영역**(자동 갱신): H1 `# 전체 워크플로우` ~ 첫 `<columns>` 직전까지
   - **하단 세부 영역**(보존, 갱신 X): `<columns>` 안의 Skills/Agents 서브페이지 링크들 + 페이지 하단 메모
3. **상태 파일**: `~/.claude/skills/.sync_state.json` — 각 입력 파일의 SHA-256, 마지막 README/Notion sync 시각

## Argument Parsing
- `--check`: drift만 보고하고 종료. 쓰기 작업 X.
- `--readme-only`: README.md만 갱신, Notion은 건드리지 않음.
- `--notion-only`: Notion 대문 상단만 갱신, README는 건드리지 않음.
- `--force`: SHA가 같아도 재생성 (포맷 일괄 적용·서식 수정에 사용).

기본(인자 없음): drift 감지 → 변경 있으면 README + Notion 모두 갱신.

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
  "version": 2,
  "last_readme_sync": "ISO8601",
  "last_notion_sync": "ISO8601",
  "items": {
    "skills/autopilot-code": {"sha256": "...", "synced_at": "ISO8601"},
    "agents/research-team": {"sha256": "...", "synced_at": "ISO8601"}
  }
}
```

### Step 3: Drift report
**신규 / 변경 / 삭제 / 동일** 4 분류. 한국어 출력:
```
Sync 상태 (2026-05-06 12:34 KST)
─────────────────────────────────────
Skills:  변경 3 / 신규 0 / 삭제 0 / 동일 9
Agents:  변경 0 / 신규 0 / 삭제 0 / 동일 8

[변경된 항목]
  ✏️  skills/autopilot-code   (마지막 sync: 2026-04-21)
  ✏️  skills/autopilot-doc    (마지막 sync: 2026-04-21)
  ✏️  skills/init-plan        (마지막 sync: 2026-04-21)

마지막 README sync: 2026-04-21 09:08
마지막 Notion sync: 2026-04-21 01:26
```

`--check`이면 종료.

### Step 4: Generate dashboard sections (공통 — README와 Notion 상단 모두 사용)

#### 4a. Workflow Map (Mermaid)
SKILL.md의 argument-hint에서 `--mode` / `--from` 값을 매번 다시 추출하여 노드 라벨 자동 갱신:

```mermaid
flowchart LR
    subgraph PREP["📋 사전 준비 (최초 1회)"]
        direction TB
        AP["[0] analyze-project<br/>코드 → docs_code/"]
        ARP["[0] analyze-papers<br/>PDF → docs_paper/"]
    end
    subgraph RUN["🚀 런타임 파이프라인"]
        direction TB
        ARES["[1] autopilot-research<br/>--depth shallow|medium|deep<br/>--from search|analyze|report"]
        ACODE["[2] autopilot-code<br/>--mode dev|audit|debug<br/>--from plan|refine|execute|test|report<br/>--user-refine"]
        ADOC["[3] autopilot-doc<br/>--mode rebuttal|write|review|survey|<br/>report|proposal|presentation<br/>--from analyze|strategy|strategy-refine|<br/>draft|draft-refine|finalize<br/>--user-refine"]
    end
    subgraph AGENTS["🤝 Agents (skills가 호출)"]
        direction TB
        PT["기획팀 (plan-team)<br/>opus"]
        QT["품질관리팀 (qa-team)<br/>opus"]
        RT["연구팀 (research-team)<br/>opus"]
        TT["테스트팀 (test-team)<br/>opus"]
        DT["개발팀 (dev-team)<br/>sonnet"]
        BT["탐색팀 (browser-team)<br/>sonnet"]
        REC["기록팀 (record-team)<br/>sonnet"]
        CRT["codex-review-team<br/>opus"]
    end
    subgraph OUT["📦 산출물"]
        direction TB
        PL[".claude_reports/plans/"]
        RS[".claude_reports/research/"]
        DO[".claude_reports/documents/"]
    end
    AP -.docs_code.-> ACODE
    ARP -.docs_paper.-> ACODE
    ARP -.docs_paper.-> ADOC
    ARES -.research artifact_dir.-> ADOC
    ACODE --> PL
    ARES --> RS
    ADOC --> DO
    ACODE --> PT
    ACODE --> RT
    ACODE --> QT
    ACODE --> TT
    ARES --> RT
    ARES --> BT
    ADOC --> RT
    ADOC --> QT
    ACODE -.--qa adversarial.-> CRT
    ACODE -.final-report auto-update.-> AP
```

#### 4b. Quickstart (자주 쓰는 워크플로우 4종 — 고정 텍스트, sync 시 그대로 박음)

```markdown
### 🎯 Quickstart 시나리오

**A. 세미나 발표자료**
1. `/autopilot-research <주제> --depth medium`
2. `/autopilot-doc --mode presentation --refs <research_artifact_dir> --pptx-template <path> --user-refine`
3. (pause) — `seminar_slides.md`에 직접 메모 추가
4. `/autopilot-doc --mode presentation --from strategy-refine <doc_artifact_dir>`

**B. 새 기능 개발**
1. (선택) `/analyze-project` — 첫 사용 시
2. `/autopilot-code --mode dev --user-refine "<task description>"`
3. (pause) — plan 검토·메모 추가
4. `/autopilot-code --mode dev --from refine <plan-name>`
5. (선택) `/autopilot-code --mode audit <plan-name>` — 사후 감사

**C. 논문 rebuttal**
1. `/autopilot-doc --mode rebuttal --refs <reviewer_comments_folder> --user-refine`
2. (pause × 2: strategy-refine, draft-refine) — 매번 사용자 메모

**D. 디버그**
1. `/autopilot-code --mode debug "<error description / log path>"`
   (debug는 `--user-refine`, `--from` 미지원 — 빠른 진단·수정에 최적화)
```

#### 4c. Skills Cheat-Sheet (table)

| Skill | 역할 | 주요 옵션 | 쓰는 시점 |
|---|---|---|---|
| `analyze-project` | 코드 → `docs_code/` | (없음) | 프로젝트 최초 1회 |
| `analyze-papers` | PDF → `docs_paper/` | (없음) | 논문 자료 최초 1회 |
| `autopilot-research` | 논문 조사 + 9개 보고서 | `--depth` `--qa` `--from` | 새 분야 조사 / 세미나 사전 준비 |
| `autopilot-code` | 코드 dev/audit/debug | `--mode` `--qa` `--from` `--user-refine` | 코드 변경 작업 |
| `autopilot-doc` | 문서 strategy + draft | `--mode`(7종) `--refs` `--qa` `--from` `--user-refine` | 논문/슬라이드/보고서 작성 |
| `init-plan` / `refine-plan` | autopilot-code의 sub | `--qa` | 보통 직접 호출 X |
| `init-doc-strategy` / `refine-doc-strategy` | autopilot-doc의 sub | `--qa` | autopilot-doc pause 후 직접 재개할 때 |
| `execute-plan` / `run-test` / `final-report` | autopilot-code의 sub | (각자) | 보통 내부 호출 |
| `sync-skills` | 본 스킬 — README + Notion 대시보드 동기화 | `--check` `--readme-only` `--notion-only` `--force` | 스킬·에이전트 수정 후 |

각 cell의 description/options는 SKILL.md frontmatter에서 자동 추출 (위 표는 sync 시점 스냅샷으로 채워 넣음).

#### 4d. Agents Cheat-Sheet (table)

| Agent | 역할 | 모델 | 호출자 / 직접 사용 |
|---|---|---|---|
| 기획팀 (plan-team) | plan 문서 작성·갱신 | opus | init-plan / refine-plan |
| 품질관리팀 (qa-team) | plan·diff 리뷰 | opus | 모든 autopilot의 review loop |
| 연구팀 (research-team) | 논문 검색·분석·plan domain review | opus | autopilot-research / -code / -doc |
| 테스트팀 (test-team) | syntax→import→smoke→functional→integration 단계 검증 | opus | run-test |
| 개발팀 (dev-team) | refactor·rename·정리 | sonnet | 사용자 직접 호출 (interactive 또는 auto) |
| 탐색팀 (browser-team) | Playwright 기반 paywall/JS 사이트 접근 | sonnet | autopilot-research |
| 기록팀 (record-team) | Notion CRUD (페이지·DB·실험 로그) | sonnet | 사용자 직접 호출 ("노션에 기록해") |
| codex-review-team | Codex CLI 기반 외부 리뷰 | opus | `--qa adversarial` 시 autopilot-code |

#### 4e. 통합 가이드라인 (사용자가 agents를 어떻게 활용하나)

```markdown
### 🧭 통합 가이드라인

**원칙**: 대부분의 Agent는 Skill이 자동으로 호출한다. 사용자가 직접 부르는 agent는 두 종류뿐:

1. **개발팀** — 작은 리팩토링/정리 ("이 함수 이름 바꿔줘", "이 코드 정리해줘"). plan을 만들 정도가 아닐 때.
2. **기록팀** — Notion 작업 ("노션에 기록해", "이번 실험 노션에 추가").

**나머지 agents는 skill에 위임**:
- 코드 변경이 필요하다 → `/autopilot-code` (내부에서 기획팀 → 품질관리팀 → 연구팀 → 테스트팀 자동 호출)
- 논문 조사 → `/autopilot-research` (연구팀 + 탐색팀)
- 문서 작성 → `/autopilot-doc` (연구팀 + 품질관리팀)
- 외부 리뷰 추가 → `/autopilot-code --qa adversarial` (codex-review-team 추가)

**언제 skill 대신 agent를 직접?**
- skill의 오버헤드가 부담스러울 만큼 작은 작업 → 개발팀
- 단발성 노션 정리 → 기록팀
- 그 외에는 항상 skill을 통해 — agent 단독 호출은 컨텍스트가 분리돼 plan/log 산출물이 남지 않으므로 추적이 어렵다.

**Skill 옵션 cheat-sheet**:
- `--user-refine`: 연구팀 메모 직후 pause해서 사용자가 직접 메모 추가 (autopilot-code dev / autopilot-doc만)
- `--from <stage>`: pause 후 또는 중간 실패 후 재개
- `--qa light|standard|thorough|adversarial`: 리뷰 강도 (adversarial은 codex-review-team 추가)
```

### Step 5: Write README.md
`~/.claude/README.md`를 다음 구조로 통째로 작성:

```markdown
# Claude Setting — Personal Skills & Agents

> **Source of Truth**: `~/.claude/skills/*/SKILL.md` + `~/.claude/agents/*.md`
> **마지막 sync**: {ISO8601 KST}
> **자동 생성**: 직접 편집 금지. 수정하려면 SKILL.md / agent.md를 고치고 `/sync-skills`.

## 📊 전체 워크플로우

{Step 4a Mermaid}

{Step 4b Quickstart}

## 📋 Skills Cheat-Sheet

{Step 4c table}

## 🤝 Agents Cheat-Sheet

{Step 4d table}

{Step 4e 통합 가이드라인}

## 📁 디렉토리 구조

```
~/.claude/
├─ skills/         # /<name> 형태로 호출되는 슬래시 스킬
├─ agents/         # Agent 도구로 위임되는 서브에이전트
├─ settings.json   # hooks, permissions, env, model 등
└─ README.md       # 이 파일 (자동 생성)
```

## 🔗 관련 링크

- Notion 대문: [Agents/Skills](https://www.notion.so/34987c2bb75380d68df4d6ce4d469bff)
- GitHub: https://github.com/dmlguq456/claude_setting

---
*sync 명령*: `/sync-skills` (변경 감지 시 README + Notion 갱신) / `/sync-skills --check` (drift만 확인)
```

### Step 6: Update Notion 대문 상단

페이지 id: `34987c2b-b753-80d6-8df4-d6ce4d469bff`

#### 6a. Fetch current content
`mcp__claude_ai_Notion__notion-fetch`로 현재 마크다운 받기.

#### 6b. 영역 식별
페이지 구조:
```
# 전체 워크플로우          ← 갱신 대상 (대시보드 시작)
{mermaid}
### 흐름 읽는 법
{설명 텍스트}
---
<columns>                   ← 보존 (서브페이지 링크)
  ## Skills | ## Agents
</columns>
{하단 메모, 마지막 업데이트 라인 등}    ← 보존 / 마지막 업데이트만 갱신
```

`---` (구분선)이 대시보드 영역과 columns 영역 사이의 마커. 이를 기준으로 search-and-replace.

#### 6c. 새 대시보드 콘텐츠
교체할 새 블록은 다음 마크다운:

```markdown
# 전체 워크플로우

> 마지막 sync: {ISO8601 KST} (자동) — Source: ~/.claude/skills + ~/.claude/agents
> 직접 편집 금지. 수정은 SKILL.md/agent.md 후 `/sync-skills`.

{Step 4a Mermaid}

{Step 4b Quickstart}

## 📋 Skills Cheat-Sheet

{Step 4c table}

## 🤝 Agents Cheat-Sheet

{Step 4d table}

{Step 4e 통합 가이드라인}

---
```

(끝의 `---`가 columns 영역 시작 마커.)

#### 6d. update_content 호출
```
mcp__claude_ai_Notion__notion-update-page(
  page_id = "34987c2b-b753-80d6-8df4-d6ce4d469bff",
  command = "update_content",
  content_updates = [{
    old_str = "# 전체 워크플로우\n...{현재 대시보드 전체}...\n---",
    new_str = "{새 대시보드 + ---}"
  }]
)
```

`<page url=...>` / `<database url=...>` 자식 링크는 columns 안에 있어 영향 받지 않음 — 안전.

#### 6e. 페이지 하단 "마지막 업데이트" 라인도 갱신
별도 content_update 항목으로:
```
old_str: "*마지막 업데이트: 2026-04-21 — 서브스킬·에이전트 팀별 페이지 분리*"
new_str: "*마지막 업데이트: {YYYY-MM-DD} — `/sync-skills`로 자동 갱신*"
```

(현재 라인 텍스트는 fetch 결과에서 추출.)

### Step 7: Update sync state
`~/.claude/skills/.sync_state.json`을 새 SHA + 시각으로 저장.

### Step 8: Final report
```
✅ Sync 완료
─────────────────────────────────────
Skills 변경: 3 (autopilot-code, autopilot-doc, init-plan)
Agents 변경: 0
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

## Task
$ARGUMENTS
