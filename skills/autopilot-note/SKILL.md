---
name: autopilot-note
description: Autopilot family — periodic + on-demand 산출물 routing pipeline (2-Layer 모델). Scans `.claude_reports/{research,documents,plans,analysis_project}/` + `experiments/` + `git log` for artifacts changed since last run, then turns each into a **Layer 2 산출물 노트** (`_layer2/notes/<id>.md`) and links it to the user's **Layer 1** board cards. 5-way routing — create L2 note row (auto), link note `card_id` → existing L1 card (auto-PROPOSE as `routing_status: inbox` with `routing_confidence`/`routing_reason`; unattended cron NEVER auto-confirms — user confirms in `/triage`), link `backbone_ids`/`task_ids` → L2 catalog (auto, emerge if needed), propose new L1 card (triage), park as ambient `card_id: null` note (auto fallback). Daily digest accumulates at `<target>/digests/YYYY-MM-DD.md`. Idempotent — same source processed twice never duplicates a note. Default `--qa light` (routine cron). Escalate to standard+ for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 includes Notion mirror (Phase 3, gated).
argument-hint: "[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--qa quick|light|standard|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>] [--no-fact-check]"
---

> 산출물 폴더 컨벤션: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). Artifact: `.claude_reports/notes/{date}/` — routing log + digest staging + reviewer logs. 진본 노트는 `<target>/_layer2/notes/<id>.md` (Layer 2), 진본 카드는 `<target>/cards/**.md` (Layer 1) — 둘 다 본 skill 산출물 (`.claude_reports/notes/`) 과 _분리_. default `<target>` = `/home/nas/user/Uihyeop/notes/` (worklog-board 의 `CARDS_DIR` 부모).

## 2-Layer 모델 (worklog-board PRD §2 — 본 skill 의 동작 전제)

worklog-board 는 _2-Layer_ 로 동작 (PRD v18, 2026-06-09):

| | **Layer 1** (`<target>/cards/`) | **Layer 2** (`<target>/_layer2/`) |
|---|---|---|
| 주인 | **사용자** — 보드에서 직접 생성 | **에이전트 (본 skill)** — 산출물 기반 정리 |
| 단위 | `kind: task` · `kind: project` 카드 | `backbones/` · `tasks/` · `papers/` 카탈로그 + `notes/` (산출물 노트화 row) |
| 본 skill | _read-only_ (매칭 대상) + 신규는 `_triage/` 제안만 | _write_ (note row 생성 + 카탈로그 emerge) |

**연결 고리 = `_layer2/notes/<id>.md` row.** 한 노트가 `card_id`(→L1 카드) + `backbone_ids`·`task_ids`(→L2 축) + `paper_id`(→papers) 를 동시에 들고 양 레이어를 잇는다. 본 skill 의 핵심 출력 = _이 노트 row 들_.

> ⚠️ **v18 이전 모델과 다름**: 이전 SKILL 은 산출물을 _Layer 1 카드 본문_ (`## 진행`/`## 쓰인 자리`) 에 줄-append 했으나, v18 부터는 _Layer 2 note row_ 로 노트화한다. 카드 본문은 _건드리지 않는다_.

## note row 스키마 (`_layer2/notes/<id>.md`)

`<target>/_layer2/notes/README.md` 의 frontmatter spec 준수:

```yaml
---
id: note-YYYYMMDD-xxxxxx        # 자동 생성 — date + source-path 해시 6자 (idempotency key)
card_id: research_some-task     # → Layer 1 카드 파일 stem. null = ambient (매칭 카드 없음)
backbone_ids: [sr-corrnet]      # → _layer2/backbones/<slug>.md (M:N)
task_ids: [sep]                 # → _layer2/tasks/<slug>.md (M:N)
paper_id: tf-restormer-icml2026 # → _layer2/papers/<slug>.md (optional)
intent: 원천기술                # 원천기술 | 상용화 | 논문 | 수탁
work_status: 검증               # 탐색 | 검증 | 통합 | 출시 | null (발산 단계)
routing_status: inbox           # inbox | confirmed | manual — ⟨2026-06-10 prd §13.C ①⟩ 무인 cron = 항상 inbox(제안 staging). confirmed 승격은 사용자 컨펌만
routing_confidence: 0.82        # ⟨§13.C ②⟩ 0–1 라우팅 신뢰도 — 자동확정 아님, /triage·홈 정렬·하이라이트용
routing_reason: "TF window ablation → ICML TF-Restormer 과제 키워드 일치"  # ⟨§13.C ②⟩ 왜 이 카드/기술에 붙였나 (사용자 아침 교정용 한 줄)
matched_signals: [project:TF-Restormer, path:plans/2026-..._exp-043, kw:ablation]  # ⟨§13.C ②⟩ 매칭 단서 (키워드·경로)
run_id: run-20260610-0500       # ⟨§13.C ③⟩ 이 노트를 만든 밤 실행 배치 id
run_at: 2026-06-10T05:00:00.000Z
created_at: 2026-06-09T00:00:00.000Z
source: .claude_reports/plans/2026-06-08_x/   # 원본 산출물 경로 (idempotency check key)
---

산출물을 _읽기 편하게 노트화_ 한 본문 (한국어). 결과·결정·가설·metric 요약 + [[연결]].
```

## Position in autopilot family

`autopilot-note` 는 _누적·routing_ 자리 (Layer 2 생성). 다른 autopilot-* 멤버는 _산출물 생성_ 자리:

- `autopilot-research` / `autopilot-code` / `autopilot-draft` / `autopilot-lab` / `analyze-project` → 산출물 _생성_, `.claude_reports/{research,plans,documents,experiments,analysis_project}/` 또는 `experiments/` 에 떨어트림.
- `autopilot-note` → 위 산출물들을 _읽어서_ Layer 2 노트로 _노트화_ + Layer 1 카드에 _연결_. _원본 산출물 불변_.

worklog-board 앱 (`~/worklog-board/`) 은 _노트·카드를 보여주는 UI_, 본 skill 은 _Layer 2 노트 생성_, 사용자 cron 또는 수동 호출이 _트리거_. 세 자리 분리.

`autopilot-refine` 과의 차이 — refine 은 _.claude_reports/{research,documents}/ 의 markdown 산출물 자체_ 정정, autopilot-note 는 _그 산출물을 source 로 읽어 별도 Layer 2 노트로 노트화_. 대상과 동작 본질이 다름.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §0 의 _ceremony 작은_ 자리 — 컨펌 없이 즉시 invoke. 메인 Claude 가 사용자 발화에 _"산출물 정리" / "오늘 누적" / "다이제스트" / "triage 확인" / "어제부터 변화 노트화"_ 같은 표현 등장 시 자동 호출.

**운영 자리**:
- **Cron** (사용자 자리) — 매일 새벽 05:00 KST 사용자 crontab 또는 worklog-board server-side scheduler 가 호출. _SKILL 안에 cron 명세 X_ — 본 SKILL 은 _idempotent 호출 가능_ 만 보장.
- **수동** — `/autopilot-note` slash 또는 자연어 발화. _묶음 정리_ 자리는 `--scope since <date>` + `--qa standard` 권장. _첫 historical bulk_ 는 `--scope all`.

**Idempotency 보장** — 같은 source 가 두 번 들어와도 _노트 중복 X_. note `id` 가 _date + source-path 해시_ 라 같은 source → 같은 id → 갱신/skip (§Stage D).

## Scope

### 입력 source (6 갈래, 기본 5 + Phase 3 노션 1)

| # | Source | 위치 | 매달림 단서 (frontmatter / 본문) |
|---|---|---|---|
| 1 | autopilot-research | `.claude_reports/research/{topic}/pipeline_summary.md` + chapters + `cards/` | topic 이름 + cards 안 paper id |
| 2 | autopilot-draft | `.claude_reports/documents/{date}_{name}/pipeline_summary.md` + draft | name + frontmatter `topic` / paper id |
| 3 | autopilot-code | `.claude_reports/plans/<date>_<slug>/pipeline_summary.md` + dev_logs | plan/checklist 키워드 |
| 4 | autopilot-lab | `experiments/<id>/STORY.md` + `experiments/_RUNLOG.md` | experiment id + 부모 link + similar_models 참조 |
| 5 | analyze-project | `.claude_reports/analysis_project/{code,paper,doc}/{matching}/` | matching label |
| 6 | git log | `git log --since=<scope> --name-only --pretty=oneline` | commit message + 변경 파일 path |
| 7 | (Phase 3) Notion | `~/.claude_reports/notion_mirror/<date>/` 의 Notion API export | DB 별 page id + property |

Phase 2 까지 source 1-6 활성, source 7 (노션) 은 _Phase 3 활성_ — `--source notion` flag 명시 자리.

### 출력 자리

| 자리 | 레이어 | 본 skill 동작 |
|---|---|---|
| `<target>/_layer2/notes/<id>.md` | **L2** | _핵심 출력_ — 산출물 1개 = 노트 row 1개. frontmatter (card_id/backbone_ids/task_ids/paper_id/intent/work_status) + 노트화 본문 |
| `<target>/_layer2/{backbones,tasks,papers}/<slug>.md` | **L2** | 노트가 참조하는 카탈로그 entry. 없으면 _emerge_ (자동 생성, 로그). frontmatter spec = 각 폴더 README |
| `<target>/cards/**.md` | **L1** | _read-only_ — note `card_id` 매칭 대상. **본문·frontmatter 안 건드림** |
| `<target>/_triage/{date}_<seq>.md` | **L1 제안** | 신규 L1 카드 (project/task) _제안_. worklog-board `/triage` UI 가 본 폴더 read |
| `<target>/digests/YYYY-MM-DD.md` | — | 매일 다이제스트. 신규 entry 최상단, 과거 보존 (누적) |
| `.claude_reports/notes/{date}/` | — | 본 skill 자체 routing log (T1 결과 표 / T2 source scan / T3 reviewer) |

> 🗄️ **⟨2026-06-10 — DB 적재 step (worklog-board DB화 이후 필수)⟩**: worklog-board 앱은 이제 L2 를 **libSQL DB(`.cache/worklog.db`) 에서 read** 한다 (마크다운 `_layer2/*.md` = source/mirror). 따라서 노트·카탈로그 `.md` 를 쓴 _뒤_ Stage D 끝에 **`npm run migrate:fs-to-db`** (worklog-board cwd 에서) 를 돌려 DB 에 반영해야 허브에 보인다. idempotent upsert 라 재실행 안전. 검증 = `npx tsx scripts/verify-migration.ts` (count parity + extras round-trip). _다른 NAS 자리(`--target`) 에 쓴 경우엔 worklog-board 가 그 `_layer2` 를 가리키도록 LAYER2_DIR 일치 확인 후 migrate._
>
> 📝 **노트 본문 = rich (열람용 — 사용자가 파일 더미 안 뒤지고 이것만 읽음)**: frontmatter 아래 본문을 충실히 — `# 제목` / 1-2줄 요약 / `## 결과` (**실험·벤치마크면 metric·수치 반드시** — SI-SDR/PESQ/DER/WER/통과수 등) / `## 핵심 결정·해결` (root cause·설계 결정) / `## 변경 코드` (주요 파일·규모) / `## 남은 자리` (🔴/🟡) / `**원본**: <source 경로 또는 Notion URL>`. 품질 기준 = `_layer2/notes/note-20260528-onnxse.md`. 위키처럼 관련 노트·backbone 을 `[[slug]]` 로 cross-link. **backbone/tech 카탈로그 `.md` 본문 = 위키 앵커** (정의·계보·다룬 작업·주요 노트 [[링크]]·쓰인 과제) — emerge 시 채우고 노트 누적 시 갱신.

### NOT for

- _Layer 1 카드 (frontmatter·본문) 변경_ → worklog-board UI 또는 사용자 영역. 본 skill 은 _read-only + 신규 제안만_.
- _산출물 본문 수정_ → `.claude_reports/{research,documents,plans}/` 는 _read-only_.
- _worklog-board 코드 자체_ (Layer 2 UI/API 빌드 포함) → 별도 `autopilot-code` 자리.
- _보고서 작성_ → `autopilot-draft`. 본 skill 은 _보고 후보 추출 + 노트화_ 자리만.
- _Layer 2 카탈로그 (backbone/task/paper) 의 대규모 재구조_ → 사용자 또는 `autopilot-code`. 본 skill 은 _필요한 카탈로그 entry emerge_ 만.

## --qa <level> (default: light)

QA 5 단계 정의 매트릭스는 [`CONVENTIONS.md §1`](../../CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용:

| Level | Behavior |
|---|---|
| **quick** | Routing 분류 + Stage C dry-summary + 자동 apply. _대량 backfill·1회성 경량_ 자리. reviewer round 0, polish 없음. |
| **light** (default) | + 1× sonnet reviewer single axis (linking precision — card_id/backbone/task 매달림 정합) + **편집팀 polish batch 1회** (Stage D.5). _매일 cron 기본_. |
| **standard** | + 1× opus + 2× sonnet reviewer (linking precision / note 노트화 narrative / 카탈로그 emerge·triage 제안 quality) + 1× sonnet fact-checker (source ↔ 노트 verbatim 대조). round 1. _주말 묶음 정리_. |
| **thorough** | + 2× opus + 2× sonnet + 1× sonnet fact-checker. round 2. _월간 cleanup_ / _노션 migration 검수_. |
| **adversarial** | thorough + 1× `Agent(codex-review-team)` Codex CLI external review. _Phase 3 노션 migration 1차 검수_ 같은 high-stakes 자리. |

opt-out flag — `--no-fact-check` 만 (standard+ 자리에서).

**reviewer axis 분담**:
- _linking precision_ (opus) — note `card_id`/`backbone_ids`/`task_ids` 가 올바른 L1 카드·L2 카탈로그 가리키나, 잘못된 매달림 catch
- _note narrative_ (sonnet) — 노트화 본문이 _source 핵심 (결과·결정·metric) 을 읽기 편하게 요약_ + markdown 정합
- _emerge·triage quality_ (sonnet) — 신설 카탈로그 entry·신규 L1 카드 제안의 _frontmatter 완성도 + 근거_

## Mode Forms

| Form | Behavior |
|---|---|
| `autopilot-note` (default) | Stage A-F 전체. `--scope today` default. |
| `autopilot-note --scope yesterday` | 어제 자정 0:00 ~ 오늘 0:00 변화 |
| `autopilot-note --scope since 2026-05-20` | 명시 시작 이후 모든 변화 |
| `autopilot-note --scope all` | _첫 실행_ 자리 — 전체 source 스캔, _historical bulk_ |
| `autopilot-note --dry-run` | Stage A-C 만 (실제 write X). chat 에 routing plan 출력 |
| `autopilot-note --digest-only` | Stage E 만 (이미 생성된 노트 → 다이제스트 재생성) |
| `autopilot-note --triage-only` | Stage D 의 신규 L1 카드 제안 자리만 (`/triage` 큐 점검) |
| `autopilot-note --source plans,experiment` | source 6 갈래 중 명시 자리만 |
| `autopilot-note --target <notes-root>` | default `/home/nas/user/Uihyeop/notes/` override. 하위 `cards/`·`_layer2/`·`_triage/`·`digests/` 자동 유도 |

## Source Resolution (Stage A 의 신규·변경 감지)

`.claude_reports/notes/.last_run.yaml` 의 `last_run_ts` 기준:

1. **pipeline_state.yaml 기반** — autopilot-* 산출물은 모두 `pipeline_state.yaml` 의 `last_updated` 가짐, `last_run_ts` 와 비교.
2. **mtime fallback** — `.claude_reports/**/pipeline_summary.md` mtime 이 `last_run_ts` 보다 신규 → 변화 자리.
3. **git log** — `git log --since=<scope> --name-only --pretty=oneline` → 변경 commit + 파일 list.
4. **노션 자리 (Phase 3)** — `~/.claude_reports/notion_mirror/<date>/`. Phase 2 까지 _skip_, `--source notion` flag 명시 시 활성.

`last_run_ts` 는 `.claude_reports/notes/.last_run.yaml` 에 누적 — 본 skill 자체의 _세션 상태_, idempotency 의 한 layer.

## Target Resolution — 양 레이어 매칭 (Stage C 의 핵심)

각 산출물에 대해 _어느 L1 카드 + 어느 L2 카탈로그_ 에 매달리나 결정.

> ⚠️ **무인 cron = 제안 staging, 자동확정 금지 ⟨2026-06-10, prd §13.C ①⟩**: 본 skill 의 매칭은 _확정이 아니라 제안_. **무인 cron 실행(트리거가 사용자 직접 호출이 아닌 자리)은 confidence 무관 `routing_status: inbox`** 로 둔다 — confidence 는 `confirmed` 로 끌어올리는 스위치가 _아니라_ `routing_confidence` 필드로 emit 해 `/triage`·홈 정렬·하이라이트에만 쓴다. `confirmed` 승격은 **오직 사용자 컨펌**(worklog-board `/triage` 노트 라우팅 승인/고치기). 이유: 밤 실행이 자동 확정하면 아침 리뷰 큐가 비어 "에이전트 제안 → 사람 daily 보정" 루프(§4.3·§12.A)가 작동하지 않음(실측: confirmed 476 / inbox 4). _예외_ — 사용자가 `/autopilot-note` 를 **직접 호출**하며 즉시 확정을 명시(`--confirm-high` 또는 발화)한 자리만 ≥0.7 confirmed 허용.

### card_id (→ Layer 1) 결정 — 3 갈래

#### 1차 — 결정론적 frontmatter
- autopilot-code / autopilot-lab 산출물의 `pipeline_state.yaml` 의 `task_card` 명시 자리 → 그 **task 카드** stem.
- 산출물 frontmatter `project: <name>` 명시 → 그 project 의 **task 카드**로 해소(`<target>/cards/` 에서 `kind: task` + `project` 매칭). ⟨v44⟩ **project 카드 자체는 `card_id` 대상 아님** — 매칭 task 없으면 신규 task 제안(routing #4)으로(project 직접 연결 금지, project 는 task.`project` 파생 표시).

#### 2차 — fuzzy 키워드 매칭
- 산출물 키워드 → `<target>/cards/**.md` 중 **`kind: task`** 의 `title` / 본문 heading fuzzy 매칭.
- **task only ⟨2026-06-12 prd v44⟩** (불변식 — 사용자 verbatim: _"무조건 연결되는 task가 있어야 한다. 없으면 생성 제안. 노션이면 그냥 동명의 task 카드라도."_): `card_id` 연결의 대상은 **항상 task 카드** — `kind: project` 직접 매칭은 **금지**(project 는 연결 대상이 아니라 그 task 의 `project` 필드에서 파생 표시되는 라벨일 뿐). **매칭할 task 가 없으면 project 로 끌어붙이지 말고** 3차 ambient → routing #4 의 **신규 task 제안**으로 흐른다. 노션 등에서 자연스러운 task 단위가 모호하면 **노트 제목과 동명의 task 카드**라도 제안(동명 허용). 보조(`secondary_card_ids`)도 같은 축 — **task only**(project 보조 연결 금지). (v43 의 "task 우선 + project 보조 fallback" 은 본 v44 에서 폐기 — project 는 후보가 아예 아니다.)
- confidence ⟨2026-06-10⟩: **≥0.7** → `card_id` set + `routing_confidence` 기록(높음). **0.4-0.7** → `card_id` set + `routing_confidence` 기록(중). **<0.4** → 3차. **무인 cron 은 confidence 무관 `routing_status: inbox`** (위 banner) — confidence 는 정렬·하이라이트용 emit 일 뿐 자동 confirmed 아님. `routing_reason`·`matched_signals` 도 같이 기록(아침 교정 단서).
- **다중 카드 제안 ⟨2026-06-11, worklog-board prd v32⟩**: 연결 제안은 **주(primary) 1 + 보조(secondary) 0~N**. 최고 confidence 매칭 = `card_id`(주, 기존 의미 불변). 그 외 유의미 매칭(예: 같은 산출물이 여러 과제·할일에 걸침)은 `secondary_card_ids: [<id>, …]` 로 frontmatter 에 복수 emit — DB 적재 시 `l2.note_cards` M:N 으로 들어가고 `/triage` 검토함 에디터에서 사용자가 추가·삭제. 보조는 제안일 뿐 보고·홈 위젯·다이제스트의 단일 기준은 여전히 주 카드.

#### 3차 — ambient
- 어디에도 안 맞음 → `card_id: null` + `routing_status: inbox` + `routing_confidence: <낮음>`. 사후 사용자 promote. (이전 `kind: misc` 의 Layer 2 대응.)
- 매칭 카드가 _없지만 새 과제·작업 단위_ 로 보이면 → 별도로 **신규 L1 카드 triage 제안** (routing #4). ⟨2026-06-12 prd v41⟩ 제안 기본 단위는 **task 카드** (`type: new-card` + `payload`{…·`source_note_ids: [<note id>, …]`}) — _이 산출물을 담을 카드를 사용자가 아직 못 만든_ 자리라 자연 단위가 task(작업)이지 project 가 아니다. 승인 1번 = 카드 생성 + source 노트 연결. project 제안은 보조 — _여러 task 제안이 같은 미존재 project 맥락을 가리킬 때만_ 'project + task 세트' 제안(보수적). 기존 `proposal_type: new_l1_card`(project) 포맷은 세트의 project 절반으로 하위호환.

### backbone_ids / task_ids / paper_id (→ Layer 2) 결정
- 산출물 본문의 _architecture·기법 키워드_ (SR-CorrNet / TF-Restormer / attention / separation / enhancement …) → `<target>/_layer2/backbones/` · `tasks/` slug 매칭.
- 매칭 없고 _재사용 자산 emerge 단서_ (재사용 / 경량 / 변형 / 새 backbone / architecture / baseline) → **카탈로그 entry emerge** (자동 생성, 로그 — backbone/task/paper 각 README frontmatter spec).
- paper 산출물 (autopilot-draft paper / research paper id) → `papers/` slug, 없으면 emerge.

### intent / work_status 추정
- `intent` — _horizontal 재사용 자산_ → `원천기술` / _특정 product·API_ → `상용화` / _외부 공표 텍스트_ → `논문` / _외부 납품_ → `수탁` / _연구실 운영·행정_ → `운영`. 산출물 종류·키워드로 default.
- `work_status` — 산출물 단계: _청사진·설계_ → `설계` / _아이디어·탐색_ → `탐색` / _실험·검증_ → `검증` / _진행 중_ → `진행중` / _통합·라이브러리화_ → `통합` / _릴리스·제출_ → `출시` / _완료_ → `완료` / _불명_ → `null`.
- **스키마 tolerance (2026-06-10)**: `intent`/`work_status` 는 NoteSchema 에서 `z.string()` (enum 아님) — 위 canonical 값을 _권장_ 하되 새 vocab 도 silent-drop 안 됨. 단 _일관성_ 위해 가능한 canonical 사용 (UI picker·badge 가 canonical 기준).

## Routing Rules (5 갈래 — 본 skill 핵심)

| # | 자리 | Trigger | 동작 | 자동 / triage |
|---|---|---|---|---|
| **1** | L2 note row 생성 | 모든 trackable 산출물 | `_layer2/notes/<id>.md` 생성 (노트화 본문 + frontmatter) | **자동** |
| **2** | note `card_id` → L1 카드 연결 | 1차/2차 매칭 | frontmatter `card_id` set + `routing_status: inbox`(제안) + `routing_confidence`/`routing_reason` ⟨2026-06-10⟩ | **자동(제안)** |
| **3** | note `backbone_ids`/`task_ids` → L2 카탈로그 연결 (+emerge) | architecture·task 키워드 매칭 / emerge 단서 | frontmatter id list set + 없으면 카탈로그 entry 생성 | **자동 (카탈로그 emerge 포함)** |
| **4** | 신규 L1 카드 _제안_ | 매칭 task 없고 새 작업 단위 | `_triage/{date}_<seq>.md` 제안 — ⟨v41/v44⟩ **기본 = task 카드**(`new-card` + `source_note_ids`), project 는 보수적 세트 제안 한정 | **triage** (자동생성 X — L1 사용자 소유) |
| **5** | ambient note | 위 어디에도 확신 없음 | `card_id: null` + `routing_status: inbox` | **자동 (ambient)** |

**L2 적재·연결은 자동 _제안_ (#1·#2·#3·#5 — 무인 cron 은 전부 `routing_status: inbox`), L1 신설만 triage (#4)** ⟨2026-06-10⟩ — 에이전트는 _제안_, 확정(`confirmed`)은 worklog-board `/triage` 노트 라우팅에서 사용자 컨펌. 신규 L1 카드 confirm 도 `/triage` UI 가 watcher.

### Language Rule
- 사용자 향 출력 (chat report / digest 본문 / triage 카드 본문 / **노트화 본문**) 은 자연스러운 **한국어** (번역체 회피).
- frontmatter id / slug / file 이름은 영어·소문자·하이픈 (`note-20260609-a1b2c3` / `sr-corrnet` / `sep` / `tf-restormer-icml2026`).

## Process

### Stage A — Source scan
1. Read `.claude_reports/notes/.last_run.yaml` → `last_run_ts`. 없으면 `--scope` 시작 자리.
2. Source 6 갈래 시간 필터 (mtime > last_run_ts). `--source` flag 있으면 명시 자리만.
3. 결과 list: `[(source_type, path, mtime, summary_excerpt)]`.

### Stage B — Source 본문 분석
각 source 에 대해:
1. `pipeline_summary.md` 우선 read (T1, 짧음).
2. 키워드 추출 — 제목 / topic / project / paper id / commit message / experiment id.
3. _노트화 재료_ 추출 — 결과·결정·가설·metric·다음 단계 (노트 본문이 될 핵심).
4. _L1 매달림 단서_ — frontmatter `project` / pipeline_state `task_card`.
5. _L2 매달림 단서_ — architecture·task 키워드 + _재사용 emerge 단서_.
6. 결과: `[(source, keywords, note_material, l1_hints, l2_hints)]`.

### Stage C — Target matching
각 source 에 §Target Resolution 적용. 결과 ⟨2026-06-10: routing_confidence/reason/signals + run 필드 추가⟩:
```
[(source, note_id, card_id, backbone_ids, task_ids, paper_id, intent, work_status,
  routing_status, routing_confidence, routing_reason, matched_signals[],
  run_id, run_at, emerge_catalog[], propose_l1_card?)]
```
`run_id`/`run_at` 은 _실행 1회 = 1 batch_ — Stage A 진입 시 한 번 정해 그 실행의 모든 노트에 동일하게 박는다 (`run-{YYYYMMDD}-{HHMM}`).

### Stage C.5 — Verification (light+)
`--qa` level 매트릭스에 따라 reviewer 호출. CONVENTIONS.md §1 정합. 검수 자리:
- _linking precision_ — `card_id`/`backbone_ids`/`task_ids` 잘못 매달림 없나
- _카탈로그 emerge·L1 제안_ 너무 너그러운가 / 박한가
- _note narrative_ 가 source 핵심 잘 요약하나 (standard+)
- _fact-check_ — source 안 venue / 년도 / 지표가 노트 본문과 일치 (standard+)

reviewer issue flag 시 — `_internal/reviews/round_{N}.md` 기록 + report surface. blocking issue 시 _자동 apply halt_, dry-run fallback.

### Stage D — Apply
1. **L2 note 생성 (#1·#2·#3·#5)**:
   - `<target>/_layer2/notes/<id>.md` 생성. `id` = `note-{YYYYMMDD}-{source-path 해시 6자}` (idempotency).
   - frontmatter = card_id / **secondary_card_ids** ⟨2026-06-11 v32 — 보조 카드 복수 제안⟩ / backbone_ids / task_ids / paper_id / intent / work_status / routing_status / **routing_confidence / routing_reason / matched_signals / run_id / run_at** ⟨2026-06-10⟩ / created_at / source. (무인 cron 은 routing_status = `inbox` 고정.)
   - 본문 = source 핵심을 _읽기 편하게 노트화_ (한국어 — 결과·결정·metric·다음 단계 + `[[연결]]`).
2. **L2 카탈로그 emerge (#3)**:
   - 참조 backbone/task/paper slug 가 `<target>/_layer2/{backbones,tasks,papers}/` 에 없으면 entry 생성 (각 README frontmatter spec). 로그에 emerge 기록.
3. **L1 카드 제안 (#4)**:
   - `<target>/_triage/{date}_<seq>.md` — 제안 카드 frontmatter (`kind: project` 또는 `task` + slug 후보) + 본문 outline + confirm/reject 표시 + 근거 source link. worklog-board `/triage` UI watch.
4. **idempotency check** — note `id` 또는 frontmatter `source` 마커가 이미 있으면 _갱신 또는 skip_ (재실행 안전). 같은 source → 같은 note (중복 X).
5. **L1 카드 불변** — `<target>/cards/**.md` 는 read-only. 신규는 `_triage/` 제안만.
6. **manifest 유지 ⟨2026-06-11, prd v33 — 일회성 아님⟩**: run 마다 backbone 카탈로그를 스캔해
   - **본문 빈 + 누적 노트 ≥3** 인 backbone → 쌓인 노트들을 근거로 **정의·쓰임새 초안을 자동 작성** (`manifest_status: draft` frontmatter). 빈자리 채움이라 사용자 콘텐츠 훼손 없음 — emerge 로 새로 생긴 backbone 도 노트가 차면 자동 충족.
   - **본문이 이미 있는** backbone (특히 `manifest_status: confirmed`) → 직접 수정 금지. 갱신할 내용이 생기면(새 파생·용도 변화) 검토함 제안으로 staging.
   - **계보(파생 사슬)는 항상 사용자 확정 영역** — 초안엔 "계보 후보" 로만 제시, 단정 서술 금지.

### Stage D.5 — 편집팀 polish (light+, batch 1회)

노트 본문은 _사용자가 직접 읽는_ 산출물 — 글로벌 편집팀 트리거 대상. 이번 run 에서 **생성·갱신된 노트 본문 + (Stage E 후) digest** 를 `Agent(편집팀)` _다듬기 모드_ 한 번에 batch 위임:

- 대상: 한국어 wording 만 (번역체·판교체·풀어쓰기 과잉 정리, 개조식 톤 통일)
- **불변**: frontmatter 전체 · `[[링크]]`·slug · 수치·metric·코드 식별자 · 구조(헤딩·표)
- 호출 1회로 묶음 처리 (노트당 개별 호출 금지 — 비용). 노트 0건 run 은 skip.
- quick 에선 생략 (경량 tier). reviewer (C.5) 와 역할 구분 — reviewer 는 _정합·정확_, 편집팀은 _읽기 품질_.

### Stage E — Digest 생성 (run 기반 리뷰 그룹 ⟨2026-06-10, prd §13.C ③⟩)
다이제스트는 _카운트 요약_ 이 아니라 **밤 실행(run) 단위 리뷰 그룹** — 홈/`/triage` 의 아침 리뷰 진입점. `run_id` 헤더 + "검토 필요(inbox)" 를 _맨 위_ 에 둔다.
1. `<target>/digests/YYYY-MM-DD.md` 에 다이제스트 entry 추가:
```markdown
## YYYY-MM-DD <weekday> (autopilot-note <scope> · run-<YYYYMMDD-HHMM>)

- 이번 run: 생성 <N> · **검토 필요(inbox) <I>** · 카탈로그 emerge <E> · 신규 카드 제안 <M>
- 노트화: <N> 건 (L1 연결 제안 <P> / ambient <A>)
- 카탈로그 emerge: backbone <B> / task <T> / paper <Pa>
- 신규 L1 카드 제안 (triage): <M> 건

### ⚠ 검토 필요 (낮은 confidence·ambient — /triage 에서 보정)
- ◯ <노트 한 줄> — _conf <0.xx>_ · <routing_reason>
- ...

### 상위 노트
- ◯ <backbone/task> · ▭ <연결 카드> — <노트 한 줄>
- ...

### Triage 자리 (신규 L1 카드 제안)
- <triage path 1>
```
2. 누적 — 신규 entry _최상단_, 과거 보존.
3. worklog-board `/` 홈의 TodayDigest 가 최신 entry 읽음.

### Stage F — Report
`.claude_reports/notes/{date}/pipeline_summary.md` 작성 (3-tier §5):
- **T1**: routing 결과 표 (산출물 → note id → card_id / catalog) + 다이제스트 link + `.last_run.yaml` 갱신 시각
- **T2**: source 별 raw scan log
- **T3**: light+ reviewer log

`.last_run.yaml` 갱신.

Final user-facing report (≤8 줄):
```
✓ autopilot-note 완료 — <scope> · run-<YYYYMMDD-HHMM>
• 노트화: <N> 건 (전부 제안 — routing_status: inbox)
• 검토 필요(낮은 confidence·ambient): <I> 건
• 카탈로그 emerge: backbone <B> / task <T>
• 신규 L1 카드 제안 (triage): <M> 건
• 다이제스트: <target>/digests/<date>.md
• 자체 로그: .claude_reports/notes/<date>/

다음 자리 ⟨2026-06-10⟩: worklog-board 홈/`/triage` 에서 이번 run <N> 건 검토 — 승인/고치기/폐기로 confirmed 승격 (무인 실행은 자동확정 안 함). {if M > 0:}+ 신규 L1 카드 제안 <M> 건 confirm.
```

## Constraints

- **L1 카드 불변** — `cards/**.md` frontmatter·본문 안 건드림. 매칭 read + 신규 `_triage/` 제안만. 사용자/UI 가 카드 책임.
- **L2 note 가 핵심 출력** — 산출물 1개 = note row 1개. 본문은 _노트화_ (원본 산출물 dump 아님 — 읽기 편한 요약).
- **카탈로그 emerge 는 가볍게** — backbone/task/paper entry 는 _필요 시 자동 생성_, 단 대규모 재구조는 사용자/autopilot-code.
- **Idempotent** — 같은 source → 같은 note id → 중복 X (`id` + frontmatter `source` + `.last_run.yaml` 다중 layer check).
- **원본 산출물 불변** — `.claude_reports/{research,documents,plans,analysis_project}/` + `experiments/` 는 read-only.
- **신규 L1 카드는 triage 의무** — 자동 생성 X. 사용자 confirm 후 worklog-board UI 가 카드 실제 생성.
- **ambient 는 임시** — `card_id: null` note 는 자동 적재, 단 사후 사용자 promote 자리 (`/hubs` inbox).
- **STRUCT halt 자리 없음** — 본 skill 은 _노트화·routing_ 만. 산출물 자체 대규모 변경은 `autopilot-refine` 또는 사용자.
- **`<target>` default** — `/home/nas/user/Uihyeop/notes/` (worklog-board `CARDS_DIR` 부모). 하위 `cards/`·`_layer2/{backbones,tasks,papers,notes}/`·`_triage/`·`digests/`. 다른 자리는 `--target` flag.

## Examples

```
# 매일 cron — 가장 흔한 자리
/autopilot-note --scope today --qa quick

# 주말 묶음 정리 — 한 주 누적 + 다이제스트 narrative
/autopilot-note --scope since 2026-05-26 --qa standard

# 첫 실행 (historical bulk) — 가용 source 모두 노트화
/autopilot-note --scope all --qa light

# Dry-run — 적용 전 routing plan (note id / card_id / catalog) 확인
/autopilot-note --scope yesterday --dry-run

# 다이제스트만 재생성
/autopilot-note --scope today --digest-only

# 신규 L1 카드 제안 자리만 결산
/autopilot-note --triage-only

# 노션 migration (Phase 3)
/autopilot-note --scope since 2026-01-01 --source notion --qa adversarial

# 한 source 만 — autopilot-lab 실험 산출물만 노트화
/autopilot-note --source experiment --scope yesterday

# 다른 NAS 자리 — target override
/autopilot-note --target ~/nas_alt/notes/
```

## When NOT to use

- **L1 카드 frontmatter·본문 수정** → worklog-board UI 또는 사용자 직접 Edit.
- **산출물 본문 수정** → `autopilot-refine`.
- **worklog-board 코드 변경** (Layer 2 UI/API 빌드 — `/hubs` 산출물 stack 등) → `autopilot-code`.
- **한 산출물 → 한 카드 _수동 매달림_** → 사용자가 산출물 frontmatter `project` 직접 입력 (1차 결정론 반영).
- **보고서 작성 자체** → `autopilot-draft`. 본 skill 은 _보고 후보 노트화 + 마커_ 만.
- **L2 카탈로그 대규모 재구조** (backbone 가족 재편 등) → 사용자 또는 autopilot-code.

## Post-Run Checklist

성공 후 사용자에게 권장:
1. **신규 L1 카드 제안 confirm** (M > 0) — worklog-board `/triage` 의 _autopilot-note 제안_ 검토.
2. **ambient/inbox 노트 연결** (A > 0) — `/hubs` 의 미연결 노트 사후 card_id 지정.
3. **다이제스트 확인** — worklog-board `/` 홈 TodayDigest.
4. **카탈로그 점검** (주 1 회) — emerge 된 backbone/task entry 의 메타 보강.
5. **`.last_run.yaml` 검수** — cron 정합 (장기 미실행 catch).
