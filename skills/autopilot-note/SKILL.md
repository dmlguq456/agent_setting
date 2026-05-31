---
name: autopilot-note
description: Autopilot family — periodic + on-demand 산출물 routing pipeline. Scans `.claude_reports/{research,documents,plans,analysis_project}/` + `experiment/` + `git log` for artifacts changed since last run, then routes each into the user's worklog-board cards (`kind: task | project | tech`) under a NAS-mounted `notes/cards/**.md`. 5-way routing — append to existing project card (auto), append to existing tech card (auto), propose new tech card (triage), propose new project card (triage), park as `kind: misc` (auto fallback). Daily digest accumulates at `notes/digests/YYYY-MM-DD.md`. Idempotent — same source processed twice never duplicates appends. Default `--qa light` (routine cron). Escalate to standard+ for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 includes Notion mirror (Phase 3, gated).
argument-hint: "[--scope today|yesterday|since <date>|all] [--target <cards-root>] [--dry-run] [--qa quick|light|standard|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>] [--no-fact-check]"
---

> 산출물 폴더 컨벤션: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). Artifact: `.claude_reports/notes/{date}/` — routing log + digest staging + reviewer logs. 진본 카드는 `<target>/cards/**.md` (default `~/notes/cards/`), 본 skill 산출물과 _분리_.

## Position in autopilot family

`autopilot-note` 는 _누적·routing_ 자리. 다른 autopilot-* 멤버는 _생성_ 자리:

- `autopilot-research` / `autopilot-code` / `autopilot-draft` / `autopilot-lab` / `analyze-project` → 산출물 _생성_, `.claude_reports/{research,plans,documents,experiments,analysis_project}/` 또는 `experiment/` 에 떨어트림.
- `autopilot-note` → 위 산출물들을 _읽어서_ 사용자 카드 (`notes/cards/**.md`) 본문에 _routing 누적_. _원본 산출물 불변_.

worklog-board 앱 (`~/worklog-board/`) 은 _카드를 보여주는 UI_, 본 skill 은 _카드 본문에 누적_, 사용자 cron 또는 수동 호출이 _트리거_. 세 자리 분리.

`autopilot-refine` 과의 차이 — refine 은 _.claude_reports/{research,documents}/ 의 markdown 산출물 자체_ 정정, autopilot-note 는 _그 산출물을 source 로 읽어 별도 카드 본문에 누적_. 대상 폴더와 동작 본질이 다름.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 의 _ceremony 작은_ 자리 — 컨펌 없이 즉시 invoke. 메인 Claude 가 사용자 발화에 _"산출물 정리" / "오늘 누적" / "다이제스트" / "triage 확인" / "어제부터 변화 카드에 반영"_ 같은 표현 등장 시 자동 호출.

**운영 자리**:
- **Cron** (사용자 자리) — 매일 새벽 05:00 KST 사용자 crontab 또는 worklog-board server-side scheduler 가 호출. _SKILL 안에 cron 명세 X_ — 본 SKILL 은 _idempotent 호출 가능_ 만 보장.
- **수동** — `/autopilot-note` slash 또는 자연어 발화. _묶음 정리_ 자리는 `--scope since <date>` + `--qa standard` 권장.

**Idempotency 보장** — 같은 source 가 두 번 들어와도 _카드 본문 중복 append X_. 본문 안 _source path + mtime_ 마커로 자체 dedup (§Stage D).

## Scope

### 입력 source (6 갈래, 기본 5 + Phase 3 노션 1)

| # | Source | 위치 | 매달림 단서 (frontmatter / 본문) |
|---|---|---|---|
| 1 | autopilot-research | `.claude_reports/research/{topic}/pipeline_summary.md` + chapters + `cards/` | topic 이름 + cards 안 paper id |
| 2 | autopilot-draft | `.claude_reports/documents/{date}_{name}/pipeline_summary.md` + draft | name + frontmatter `topic` / paper id |
| 3 | autopilot-code | `.claude_reports/plans/{date}_{name}/pipeline_summary.md` + dev_logs / 또는 `specs/<name>/dev_log/<date>_<slug>/` | spec 이름 + plan/checklist 키워드 |
| 4 | autopilot-lab | `experiment/<id>/STORY.md` + `experiment/_RUNLOG.md` | experiment id + 부모 link + similar_models 참조 |
| 5 | analyze-project | `.claude_reports/analysis_project/{code,paper,doc}/{matching}/` | matching label |
| 6 | git log | `git log --since=<scope> --name-only --pretty=oneline` | commit message + 변경 파일 path |
| 7 | (Phase 3) Notion | `~/.claude_reports/notion_mirror/<date>/` 의 Notion API export | DB 별 page id + property |

Phase 2 까지 source 1-6 활성, source 7 (노션) 은 _Phase 3 활성_ — `--source notion` flag 명시 자리.

### 출력 자리

| 자리 | 역할 | 본 skill 동작 |
|---|---|---|
| `<target>/cards/**.md` (default `~/notes/cards/`) | _사용자 진본 카드_ | 본문 `## 진행` 또는 `## 쓰인 자리` append-only. frontmatter 안 건드림 |
| `<target>/digests/YYYY-MM-DD.md` | 매일 다이제스트 | 신규 entry 최상단 추가, 과거 entry 보존 (누적) |
| `<target>/_triage/{date}_<seq>.md` | 신설 제안 카드 | worklog-board `/triage` UI 가 본 폴더 read |
| `<target>/cards/_misc_<source-slug>.md` | 매핑 모호 자리 (`kind: misc`) | 자동 적재, 정기 cleanup 자리 |
| `.claude_reports/notes/{date}/` | 본 skill 자체 routing log | T1: 결과 표 + 다이제스트 link, T2: source 별 raw scan, T3: reviewer logs |

### NOT for

- _카드 frontmatter 자체 변경_ → 사용자 또는 worklog-board UI 영역.
- _산출물 본문 수정_ → `.claude_reports/{research,documents,plans}/` 는 _read-only_.
- _worklog-board 코드 자체_ → 별도 `autopilot-code` 자리.
- _보고서 작성_ → `autopilot-draft`. 본 skill 은 _보고 후보 추출 + 마커 박기_ 자리만.

## --qa <level> (default: light)

QA 5 단계 정의 매트릭스는 [`CONVENTIONS.md §1`](../../CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용:

| Level | Behavior |
|---|---|
| **quick** | Routing 분류 + Stage C dry-summary + 자동 apply. _매일 cron_ 기본 자리. reviewer round 0. |
| **light** (default) | + 1× sonnet reviewer single axis (routing precision). _주중 묶음 정리_. |
| **standard** | + 1× opus + 2× sonnet reviewer (다른 axes — routing precision / digest narrative / triage proposal quality) + 1× sonnet fact-checker (source ↔ 카드 매달림 verbatim 대조). round 1. _주말 묶음 정리_. |
| **thorough** | + 2× opus + 2× sonnet + 1× sonnet fact-checker. round 2. _월간 cleanup_ / _노션 migration 검수_. |
| **adversarial** | thorough + 1× `Agent(codex-review-team)` Codex CLI external review. _Phase 3 노션 migration 1차 검수_ 같은 high-stakes 자리. |

opt-out flag — `--no-fact-check` 만 (standard+ 자리에서). `--no-style-audit` 자리 없음 (본 skill 은 style 검수 자리 X).

**reviewer axis 분담**:
- _routing precision_ (opus) — source ↔ 카드 매달림 1:1 정합, 잘못된 매달림 자리 catch
- _digest narrative_ (sonnet) — 다이제스트 한 줄 요약이 _누적 자리에 부합_ + _markdown 정합_
- _triage proposal quality_ (sonnet) — 신설 제안 카드의 _frontmatter 완성도 + 본문 outline 정합_

## Mode Forms

| Form | Behavior |
|---|---|
| `autopilot-note` (default) | Stage A-F 전체. `--scope today` default. |
| `autopilot-note --scope yesterday` | 어제 자정 0:00 ~ 오늘 0:00 변화 |
| `autopilot-note --scope since 2026-05-20` | 명시 시작 이후 모든 변화 |
| `autopilot-note --scope all` | _첫 실행_ 자리 — 전체 source 스캔, _historical bulk_ |
| `autopilot-note --dry-run` | Stage A-D 만 (실제 apply X). chat 에 routing plan 출력 |
| `autopilot-note --digest-only` | Stage E 만 (이미 누적 본문 → 다이제스트 재생성) |
| `autopilot-note --triage-only` | Stage D 신설 제안 자리만 (`/triage` 큐 점검) |
| `autopilot-note --source plans,experiment` | source 6 갈래 중 명시 자리만 |
| `autopilot-note --target <cards-root>` | default `~/notes/cards/` override (다른 NAS 마운트 자리) |

## Source Resolution (Stage A 의 신규·변경 감지)

`.claude_reports/notes/.last_run.yaml` 의 `last_run_ts` 기준:

1. **pipeline_state.yaml 기반** — autopilot-* 산출물은 모두 `pipeline_state.yaml` 의 `last_updated` 가짐, `last_run_ts` 와 비교.
2. **mtime fallback** — `.claude_reports/**/pipeline_summary.md` mtime 이 `last_run_ts` 보다 신규 → 변화 자리.
3. **git log** — `git log --since=<scope> --name-only --pretty=oneline` → 변경 commit + 파일 list. `<scope>` 가 `today` 면 `today 00:00`, `yesterday` 면 `yesterday 00:00` 식으로 변환.
4. **노션 자리 (Phase 3)** — `~/.claude_reports/notion_mirror/<date>/` 의 Notion API export 본. Phase 2 까지 _skip_, `--source notion` flag 명시 시 활성.

`last_run_ts` 자체는 `.claude_reports/notes/.last_run.yaml` 에 누적 — 본 skill 자체의 _세션 상태_, idempotency key 의 한 layer.

## Target Resolution (카드 매칭, Stage C 의 핵심)

각 source artifact 에 대해 _어느 카드에 매달리나_ 결정. 3 갈래 결정론:

### 1차 — 결정론적 frontmatter

- autopilot-code / autopilot-lab 산출물 자리 → `pipeline_state.yaml` 의 `task_card` 또는 `project` 명시 자리 따라감 (worklog-board 가 _코드 작업 시작 자리_ 에 미리 박은 매달림).
- 산출물 frontmatter 안 `project: <name>` 또는 `uses: [<tech>]` 명시 자리 → 그대로 따라감.
- 없으면 2차로.

### 2차 — fuzzy 키워드 매칭

- 산출물 본문 / topic / name 의 키워드 → `<target>/cards/**.md` 중 frontmatter `title` / 본문 `# heading` / `aliases:` 와 fuzzy 매칭.
- 카탈로그 카드 (`kind: project` / `kind: tech`) 우선, 그 다음 할일 카드.
- 매칭 confidence:
  - **≥0.7** → 자동 매달림
  - **0.4-0.7** → triage 큐 (사용자 confirm)
  - **<0.4** → 3차로

### 3차 — misc 자동 적재

- 어디에도 매칭 안 되는 자료 → `_misc_<source-slug>.md` 신규 misc 카드 자리.
- 사용자가 _정기 misc 정리 자리_ 에서 promote 또는 삭제.

## Routing Rules (5 갈래 — 본 skill 핵심)

| # | 자리 | Trigger | 동작 | 자동 / triage |
|---|---|---|---|---|
| **1** | 과제 카드 본문 `## 진행` append | 1차/2차 매칭 → `kind: project` | 한 줄 entry 추가 | **자동** |
| **2** | 기술 카드 본문 `## 쓰인 자리` append | 1차/2차 매칭 → `kind: tech` (또는 할일 카드 `uses: [...]` 매달림이 가리키는 tech 카드) | wikilink + 한 줄 추가 | **자동** |
| **3** | 새 기술 카드 _신설 제안_ | 본문 키워드 _영속 자산 emerge_ 추정 (재사용 / 경량 / 변형 / backbone / 새 architecture) | `_triage/{date}_<seq>.md` 카드 생성 | **triage** |
| **4** | 새 과제 카드 _신설 제안_ | 매핑 안 되는 산출물 + 외부 클라이언트 / 사업명 / 논문 출간 단위 키워드 | 같은 자리 | **triage** |
| **5** | 매핑 모호 자료 → misc | 위 4 갈래 어디에도 안 맞음 | `_misc_<source-slug>.md` 신규 misc 카드 | **자동 (기타)** |

**누적은 무조건 자동, 신설만 triage** — 사용자 부담 최소 자리. 신설 confirm 은 worklog-board `/triage` UI 가 watcher.

### 진행 줄 형식 (#1·#2 공통)

```
- <마커> YYYY-MM-DD: <한 줄 요약 ≤80자> [<source: .claude_reports/...>]
```

- `<마커>` ∈ {`✓`, `-`, `×`} — visibility 추정 (아래)
- `<source: ...>` — idempotency check key

**visibility 자동 추정 (default 한 글자만)**:
- `✓` — `reportable` + 보고 가능 추정 자리 (외부 가시 결과·진척·결정)
- `-` — `internal` 추정 (실패·중단·내부 결정)
- `×` — `private` 추정 (회사 비공개·물밑 발산·`visibility: private` 카드 자체)

사용자가 worklog-board `/triage` 의 _보고 후보_ 자리에서 줄 단위로 한 글자 조정 (PRD v2 §3.5 B).

## Language Rule

- 내부 사고 / source 본문 scan / classification 분석은 영어.
- 사용자 향 출력 (chat report / digest 본문 / triage 카드 본문 / 카드 본문 append 줄) **한국어**.
- 카드 frontmatter / wikilink slug / file 이름은 영어·소문자·하이픈 (`_project_icml-2026-tf-restormer.md` / `_tech_tf-restormer.md`).

## Process

### Stage A — Source scan

1. Read `.claude_reports/notes/.last_run.yaml` → `last_run_ts`. 없으면 `--scope` 의 시작 자리.
2. Source 6 갈래 모두 시간 필터 (mtime > last_run_ts).
3. `--source` flag 있으면 명시 자리만.
4. 결과 list: `[(source_type, path, mtime, summary_excerpt)]`.

### Stage B — Source 본문 분석

각 source 에 대해:
1. `pipeline_summary.md` 우선 read (T1, 짧음).
2. 키워드 추출 — 제목 / topic / project / paper id / commit message / experiment id.
3. _영속 emerge 단서_ scan — _재사용_ / _경량_ / _변형_ / _새 backbone_ / _architecture_ / _baseline_ 패턴 매칭 → routing 분류 #3 후보.
4. 매달림 단서 — 산출물 frontmatter `project` / `uses` / pipeline_state.yaml `task_card`.
5. 결과: `[(source, keywords, emerge_signals, frontmatter_hints, body_excerpt)]`.

### Stage C — Target matching

각 source 에 대해 §Target Resolution 의 1차/2차/3차 결정론 적용. 결과:
```
[(source, target_card_path, routing_class, confidence, marker)]
routing_class ∈ {append_project, append_tech, propose_tech, propose_project, park_misc}
```

`marker` (visibility 추정) 는 본문 키워드 + frontmatter `visibility` 따라 default.

### Stage C.5 — Verification (light+)

`--qa` level 매트릭스에 따라 reviewer 호출. CONVENTIONS.md §1 정합. 검수 자리:
- _routing precision_ — 잘못 매달림 없나
- _신설 제안_ 너무 너그러운가 / 박한가
- _digest narrative_ 정합 (standard+)
- _fact-check_ — source 안 명시 venue / 년도 / 지표가 target 카드 본문과 일치 (standard+)

reviewer 가 issue flag 시 — `_internal/reviews/round_{N}.md` 에 기록 + 사용자 향 report 에 surface. blocking issue 시 _자동 apply halt_, dry-run 모양으로 fallback.

### Stage D — Apply

1. **자동 routing (#1·#2·#5)**:
   - `<target>/cards/<card>.md` 의 `## 진행` (`kind: project`) 또는 `## 쓰인 자리` (`kind: tech`) 섹션 끝에 한 줄 append.
   - 섹션 없으면 _새 섹션 생성_ — 본문 끝 자리.
   - 형식: `- <마커> YYYY-MM-DD: <한 줄 요약> [<source: .claude_reports/...>]`
   - `#5` misc 는 새 파일 생성 — frontmatter `kind: misc` + 본문 outline + source link.

2. **triage 적재 (#3·#4)**:
   - `<target>/_triage/{date}_<seq>.md` 신규 파일.
   - 본문 = _제안 카드 frontmatter_ (`kind: tech` 또는 `kind: project` + slug 후보) + _본문 outline_ (`## 자료 위치` 후보 + `## 쓰인 자리` 후보 / `## 동원 기술` 후보) + _confirm/reject 자리_ 표시 + _근거 source link_.
   - worklog-board `/triage` UI 가 본 폴더 watch.

3. **idempotency check** — 카드 본문 안 `[<source: <path>>]` 마커 이미 있으면 _skip_ (재실행 안전).

4. **frontmatter 안 건드림** — 본 skill 의 _Apply 자리_ 는 본문 append 만.

### Stage E — Digest 생성

1. `<target>/digests/YYYY-MM-DD.md` 파일에 다이제스트 entry 추가:

```markdown
## YYYY-MM-DD <weekday> (autopilot-note <scope>)

- 누적 자동: <N> 건 (과제 <P> / 기술 <T>)
- 신설 제안 (triage): <M> 건
- 기타 (misc): <K> 건

### 상위 변화
- ▭ <과제 카드> — <한 줄>
- ◯ <기술 카드> — <한 줄>
- ...

### Triage 자리 (신설 제안)
- <triage path 1>
- ...
```

2. 본 파일은 _누적_ — 신규 entry _최상단_, 과거 entry 보존.
3. worklog-board `/` 홈의 TodayDigest 가 본 파일의 _최신 entry_ 읽음.

### Stage F — Report

`.claude_reports/notes/{date}/pipeline_summary.md` 작성 (3-tier 컨벤션 §5):
- **T1**: 오늘 routing 결과 표 + 다이제스트 link + `.last_run.yaml` 갱신 시각
- **T2**: source 별 raw scan log (`scan_research.md`, `scan_plans.md`, ...)
- **T3**: `_internal/reviews/round_{N}_<axis>.md` (light+ 자리 reviewer log)

`.last_run.yaml` 갱신 — 다음 실행 자리.

Final user-facing report (≤8 줄):

```
✓ autopilot-note 완료 — <scope>
• 누적 자동: <N> 건 (과제 <P> / 기술 <T>)
• 신설 제안 (triage): <M> 건
• 기타 (misc): <K> 건
• 다이제스트: <target>/digests/<date>.md
• 자체 로그: .claude_reports/notes/<date>/
{if M > 0:}
다음 자리: worklog-board /triage 에서 신설 제안 confirm
```

## Constraints

- **카드 frontmatter 불변** — 본 skill 은 frontmatter 안 건드림. 사용자 또는 worklog-board UI 가 책임.
- **본문 append-only** — 기존 본문 줄 삭제·수정 X. 신규 줄·신규 섹션 추가만.
- **Idempotent** — 같은 source 두 번 들어와도 중복 append X (`[<source: <path>>]` 마커 + `.last_run.yaml` 두 layer check).
- **원본 산출물 불변** — `.claude_reports/{research,documents,plans,analysis_project}/` + `experiment/` 는 read-only.
- **신설은 triage 의무** — 새 카탈로그 카드 (#3·#4) 는 _자동 생성 X_. 사용자 confirm 후 worklog-board UI 가 카드 실제 생성.
- **misc 는 임시** — `_misc_*` 카드는 _자동 적재_, 단 _정기 사용자 cleanup_ 자리 (적재 후 N 일 지나면 alert).
- **visibility 자동 추정 default 한 글자만** — 사용자 worklog-board UI 에서 줄 단위 조정.
- **STRUCT halt 자리 없음** — 본 skill 은 _routing 누적_ 만, _대규모 변경_ 자리 없음. 산출물 자체 _대규모 변경_ 은 `autopilot-refine` 또는 사용자 직접 Edit.
- **`<target>` 자리 — default `~/notes/cards/`, `~/notes/digests/`, `~/notes/_triage/`** — worklog-board PRD 와 정합. 다른 자리는 `--target <cards-root>` flag.

## Examples

```
# 매일 cron — 가장 흔한 자리
/autopilot-note --scope today --qa quick

# 주말 묶음 정리 — 한 주 누적 + 다이제스트 narrative
/autopilot-note --scope since 2026-05-26 --qa standard

# 첫 실행 (historical bulk) — 가용 source 모두 스캔
/autopilot-note --scope all --qa light

# Dry-run — 적용 전 routing plan 확인
/autopilot-note --scope yesterday --dry-run

# 다이제스트만 재생성 (본문 누적은 이미 됨)
/autopilot-note --scope today --digest-only

# Triage 큐 점검만 — 신설 제안 자리만 결산
/autopilot-note --triage-only

# 노션 migration (Phase 3)
/autopilot-note --scope since 2026-01-01 --source notion --qa adversarial

# 한 source 만 — autopilot-lab 실험 산출물만 카드에
/autopilot-note --source experiment --scope yesterday

# 다른 NAS 자리 — target override
/autopilot-note --target ~/nas_alt/notes/cards/
```

## When NOT to use

- **카드 frontmatter 수정 자리** → worklog-board UI 또는 사용자 직접 Edit.
- **산출물 본문 수정** → `autopilot-refine`.
- **worklog-board 코드 변경** → `autopilot-code`.
- **한 산출물 → 한 카드 _수동 매달림_** → 사용자가 산출물 frontmatter `project` / `uses` 직접 입력 (본 skill 의 1차 결정론 자리에 반영됨).
- **보고서 작성 자체** → `autopilot-draft`. 본 skill 은 _보고 후보 추출 + 마커 박기_ 자리만.
- **migration 본 변환 자체** (Notion API export → 마크다운) → 별도 helper script, 본 skill 은 _변환된 mirror 를 source 7 로 read_ 하는 자리만.

## Post-Run Checklist

성공 후 사용자에게 권장:

1. **신설 제안 confirm** (M > 0 시) — worklog-board `/triage` 의 _autopilot-note 제안_ 자리 한 번 검토.
2. **다이제스트 확인** — worklog-board `/` 홈의 TodayDigest 한 번 봄.
3. **보고 후보 마커 조정** (주 1 회 자리) — `/triage` 의 _이번 주 보고 후보_ 줄 단위 ✓ / - / × 조정.
4. **misc cleanup** (월 1 회 자리) — `<target>/cards/_misc_*` 누적 자리 정기 정리.
5. **`.last_run.yaml` 검수** — autopilot-note 자체의 cron 정합 확인 (장기 미실행 시 catch).
