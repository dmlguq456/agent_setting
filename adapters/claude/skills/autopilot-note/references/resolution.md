## Source Resolution (Stage A 의 신규·변경 감지)

`<artifact-root>/notes/.last_run.yaml` 의 `last_run_ts` 기준:

1. **pipeline_state.yaml 기반** — autopilot-* 산출물은 모두 `pipeline_state.yaml` 의 `last_updated` 가짐, `last_run_ts` 와 비교.
2. **mtime fallback** — `<artifact-root>/**/pipeline_summary.md` mtime 이 `last_run_ts` 보다 신규 → 변화 자리.
3. **git log** — `git log --since=<scope> --name-only --pretty=oneline` → 변경 commit + 파일 list.
4. **노션 자리 (Phase 3)** — `~/.agent_reports/notion_mirror/<date>/` (legacy `~/.claude_reports/notion_mirror/<date>/`). Phase 2 까지 _skip_, `--source notion` flag 명시 시 활성.

`last_run_ts` 는 `<artifact-root>/notes/.last_run.yaml` 에 누적 — 본 skill 자체의 _세션 상태_, idempotency 의 한 layer.

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
- **제안만 · 자동 생성 절대 금지 + 묶음 우선 + 기존 task 매칭 우선 ⟨2026-06-12 prd v45⟩** (사용자 강한 반대 후 — verbatim: _"노션 아닌 경우 새 카드는 애초에 제안만 하라니까? 혹은 하나의 카드에 묶어서 넣을 수 있으면 하나로."_): no-match 산출물은 **검토함 보드 세그먼트 _제안_ 으로만** 올린다 — skill·cron 어느 경로도 `l1_cards` 를 **직접 생성하지 않는다**(생성은 오직 사용자 승인 시 보드 approve). 3 규칙:
  - ① **묶음 우선** — 여러 산출물이 같은 project + 내용/키워드로 묶이면 **한 제안에 `source_note_ids` 복수**로(산출물마다 제안 1개 금지). 묶음은 _의미 기반_ 클러스터(rule 문자열 매칭 아님).
  - ② **기존 task 매칭 우선** — 신규 task 를 제안하기 _전에_ 그 project 안 기존 task 와 의미상 부합하는지 본다. 강하게 부합하면 **`type: link-note` 제안**(`payload`{`target_card_id`=기존 task·`source_note_ids` 복수}) — 카드 생성 없이 _연결만_ 제안(보수적, 강한 부합만). 부합 task 없을 때만 ①의 `new-card` 신규 제안.
  - ③ **생성 0 불변식** — 제안은 `_triage/<id>.md` 파일만(`id`=묶음 note_ids stable hash → idempotent). `l1_cards` 생성·`l2_notes.card_id` 변경 0 — 332건 재라우팅(prd v44 ④)도 _제안_ 으로(스크립트 직접 DB 생성 번복). 상세 = worklog-board prd §4.3 ⟨v45⟩.
  - ④ **IA 모델 정렬 ⟨2026-06-19 prd §19 v56/v57⟩** — 제안의 project 귀속 우선순위: **기존 _활성_ 프로젝트 > 미연결(단발성, `project_id=NULL`) > 새 프로젝트(예외)**.
    - **닫힌(archived `status:closed`) 프로젝트는 후보에서 제외** — IA 재설계로 해체된 '기타 작업'·'기타 업무 & 개발' 버킷(현 status:closed)에 _절대_ 끌어붙이지 않는다.
    - 마땅한 _활성_ 프로젝트가 없고 단발성 작업이면(어느 줄기에도 안 매달림) → 새 프로젝트·가짜 버킷 대신 **미연결**: `new-card` 제안을 **project 미지정**(payload 에 `project_ref`/`project` 없음 → 승인 시 `project_id=NULL` = 단발성 면 §19.2)으로 emit.
    - **새 프로젝트 = 예외 유지**(v55 prefer-existing 임계 — 기존 매칭 없음 + 폴더 ≥2·노트 ≥3 묶음일 때만). 폐기된 게 아니라 _드물게_ 만 뜬다(평소 0~1건).
  - ⑤ **제안 task 제목 = 서술적 ⟨2026-06-19⟩** — `new-card` 의 `proposed_title` 은 _제목만 봐도 무슨 작업인지_ 읽히는 구절로(노트 내용 요약). **폴더 슬러그·source_dir basename·노트 id·날짜 같은 무의미 라벨 금지** — 묶인 노트들의 핵심 작업을 한 줄로 요약한 자연스러운 제목(예: `triage-tabs` ❌ → "검토함 4-탭 재편 구현" ✅). 사용자: _"제목만 봐서 뭔지 알 길이 없어."_

### backbone_ids / task_ids / paper_id (→ Layer 2) 결정
- 산출물 본문의 _architecture·기법 키워드_ (SR-CorrNet / TF-Restormer / attention / separation / enhancement …) → `<target>/_layer2/backbones/` · `tasks/` slug 매칭.
- 매칭 없고 _재사용 자산 emerge 단서_ (재사용 / 경량 / 변형 / 새 backbone / architecture / baseline) → **카탈로그 entry emerge** (자동 생성, 로그 — backbone/task/paper 각 README frontmatter spec).
- paper 산출물 (autopilot-draft paper / research paper id) → `papers/` slug, 없으면 emerge.

### intent / work_status 추정
- `intent` — _horizontal 재사용 자산_ → `원천기술` / _특정 product·API_ → `상용화` / _외부 공표 텍스트_ → `논문` / _외부 납품_ → `수탁` / _연구실 운영·행정_ → `운영`. 산출물 종류·키워드로 default.
- `work_status` — 산출물 단계: _청사진·설계_ → `설계` / _아이디어·탐색_ → `탐색` / _실험·검증_ → `검증` / _진행 중_ → `진행중` / _통합·라이브러리화_ → `통합` / _릴리스·제출_ → `출시` / _완료_ → `완료` / _불명_ → `null`.
- **스키마 tolerance (2026-06-10)**: `intent`/`work_status` 는 NoteSchema 에서 `z.string()` (enum 아님) — 위 canonical 값을 _권장_ 하되 새 vocab 도 silent-drop 안 됨. 단 _일관성_ 위해 가능한 canonical 사용 (UI picker·badge 가 canonical 기준).
