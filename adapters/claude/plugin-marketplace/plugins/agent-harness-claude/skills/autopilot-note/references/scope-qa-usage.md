## Scope

### 입력 source (6 갈래, 기본 5 + Phase 3 노션 1)

| # | Source | 위치 | 매달림 단서 (frontmatter / 본문) |
|---|---|---|---|
| 1 | autopilot-research | `<artifact-root>/research/{topic}/pipeline_summary.md` + chapters + `cards/` | topic 이름 + cards 안 paper id |
| 2 | autopilot-draft | `<artifact-root>/documents/{date}_{name}/pipeline_summary.md` + draft | name + frontmatter `topic` / paper id |
| 3 | autopilot-code | `<artifact-root>/plans/<date>_<slug>/pipeline_summary.md` + dev_logs | plan/checklist 키워드 |
| 4 | autopilot-lab | `experiments/<id>/STORY.md` + `experiments/_RUNLOG.md` | experiment id + 부모 link + similar_models 참조 |
| 5 | analyze-project | `<artifact-root>/analysis_project/{code,paper,doc}/{matching}/` | matching label |
| 6 | git log | `git log --since=<scope> --name-only --pretty=oneline` | commit message + 변경 파일 path |
| 7 | (Phase 3) Notion | `~/.agent_reports/notion_mirror/<date>/` (legacy `~/.claude_reports/notion_mirror/<date>/`) 의 Notion API export | DB 별 page id + property |

Phase 2 까지 source 1-6 활성, source 7 (노션) 은 _Phase 3 활성_ — `--source notion` flag 명시 자리.

### 출력 자리

| 자리 | 레이어 | 본 skill 동작 |
|---|---|---|
| `<target>/_layer2/notes/<id>.md` | **L2** | _핵심 출력_ — 산출물 1개 = 노트 row 1개. frontmatter (card_id/backbone_ids/task_ids/paper_id/intent/work_status) + 노트화 본문 |
| `<target>/_layer2/{backbones,tasks,papers}/<slug>.md` | **L2** | 노트가 참조하는 카탈로그 entry. 없으면 _emerge_ (자동 생성, 로그). frontmatter spec = 각 폴더 README |
| `<target>/cards/**.md` | **L1** | _read-only_ — note `card_id` 매칭 대상. **본문·frontmatter 안 건드림** |
| `<target>/_triage/{date}_<seq>.md` | **L1 제안** | 신규 L1 카드 (project/task) _제안_. worklog-board `/triage` UI 가 본 폴더 read |
| `<target>/digests/YYYY-MM-DD.md` | — | 매일 다이제스트. 신규 entry 최상단, 과거 보존 (누적) |
| `<artifact-root>/notes/{date}/` | — | 본 skill 자체 routing log (T1 결과 표 / T2 source scan / T3 reviewer) |

> 🗄️ **DB 적재 step (필수)**: worklog-board 앱은 이제 L2 를 **libSQL DB(`.cache/worklog.db`) 에서 read** 한다 (마크다운 `_layer2/*.md` = source/mirror). 따라서 노트·카탈로그 `.md` 를 쓴 _뒤_ Stage D 끝에 **`npm run migrate:fs-to-db`** (worklog-board cwd 에서) 를 돌려 DB 에 반영해야 허브에 보인다. idempotent upsert 라 재실행 안전. 검증 = `npx tsx scripts/verify-migration.ts` (count parity + extras round-trip). _다른 NAS 자리(`--target`) 에 쓴 경우엔 worklog-board 가 그 `_layer2` 를 가리키도록 LAYER2_DIR 일치 확인 후 migrate._
>
> 📝 **노트 본문 = rich (열람용 — 사용자가 파일 더미 안 뒤지고 이것만 읽음)**: frontmatter 아래 본문을 충실히 — `# 제목` / 1-2줄 요약 / `## 결과` (**실험·벤치마크면 metric·수치 반드시** — SI-SDR/PESQ/DER/WER/통과수 등) / `## 핵심 결정·해결` (root cause·설계 결정) / `## 변경 코드` (주요 파일·규모) / `## 남은 자리` (🔴/🟡) / `**원본**: <source 경로 또는 Notion URL>`. 품질 기준 = `_layer2/notes/note-20260528-onnxse.md`. 위키처럼 관련 노트·backbone 을 `[[slug]]` 로 cross-link. **backbone/tech 카탈로그 `.md` 본문 = 위키 앵커** (정의·계보·다룬 작업·주요 노트 [[링크]]·쓰인 과제) — emerge 시 채우고 노트 누적 시 갱신.

### NOT for

- _Layer 1 카드 (frontmatter·본문) 변경_ → worklog-board UI 또는 사용자 영역. 본 skill 은 _read-only + 신규 제안만_.
- _산출물 본문 수정_ → `<artifact-root>/{research,documents,plans}/` 는 _read-only_.
- _worklog-board 코드 자체_ (Layer 2 UI/API 빌드 포함) → 별도 `autopilot-code` 자리.
- _보고서 작성_ → `autopilot-draft`. 본 skill 은 _보고 후보 추출 + 노트화_ 자리만.
- _Layer 2 카탈로그 (backbone/task/paper) 의 대규모 재구조_ → 사용자 또는 `autopilot-code`. 본 skill 은 _필요한 카탈로그 entry emerge_ 만.

## 검증 rigor tier (intensity-파생, default: light-tier)

검증 rigor 는 별도 `--qa` 축이 아니라 `--intensity` 에서 결정론적으로 파생된다 — tier 정의·매핑은 [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot) 단일 source. 아래 tier 는 각각 intensity `quick`←quick, `direct`←light, `standard`←standard, `thorough`←thorough, `adversarial`←adversarial 에 대응. 본 skill 적용:

| Rigor tier | Behavior |
|---|---|
| **quick** | Routing 분류 + Stage C dry-summary + 자동 apply. _대량 backfill·1회성 경량_ 자리. reviewer round 0, polish 없음. |
| **light** (default) | + 1× fast reviewer single axis (linking precision — card_id/backbone/task 매달림 정합) + **편집팀 polish batch 1회** (Stage D.5). _매일 cron 기본_. |
| **standard** | + 1× deep reviewer + 2× fast reviewers (linking precision / note 노트화 narrative / 카탈로그 emerge·triage 제안 quality) + 1× fast fact-checker (source ↔ 노트 verbatim 대조). round 1. _주말 묶음 정리_. |
| **thorough** | + 2× deep reviewers + 2× fast reviewers + 1× fast fact-checker. round 2. _월간 cleanup_ / _노션 migration 검수_. |
| **adversarial** | thorough + 1× external adversary (`codex-review-team` in Claude adapter). _Phase 3 노션 migration 1차 검수_ 같은 high-stakes 자리. |

Fact/source checks follow the derived rigor budget (intensity-파생); this entrypoint does not expose a fact-check opt-out flag.

**reviewer axis 분담**:
- _linking precision_ (deep reviewer) — note `card_id`/`backbone_ids`/`task_ids` 가 올바른 L1 카드·L2 카탈로그 가리키나, 잘못된 매달림 catch
- _note narrative_ (fast reviewer) — 노트화 본문이 _source 핵심 (결과·결정·metric) 을 읽기 편하게 요약_ + markdown 정합
- _emerge·triage quality_ (fast reviewer) — 신설 카탈로그 entry·신규 L1 카드 제안의 _frontmatter 완성도 + 근거_

## Examples

```
# 매일 cron — 가장 흔한 자리
/autopilot-note --scope today --intensity quick

# 주말 묶음 정리 — 한 주 누적 + 다이제스트 narrative
/autopilot-note --scope since 2026-05-26 --intensity standard

# 첫 실행 (historical bulk) — 가용 source 모두 노트화 (default light-tier)
/autopilot-note --scope all

# Dry-run — 적용 전 routing plan (note id / card_id / catalog) 확인
/autopilot-note --scope yesterday --dry-run

# 다이제스트만 재생성
/autopilot-note --scope today --digest-only

# 신규 L1 카드 제안 자리만 결산
/autopilot-note --triage-only

# 노션 migration (Phase 3)
/autopilot-note --scope since 2026-01-01 --source notion --intensity adversarial

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
