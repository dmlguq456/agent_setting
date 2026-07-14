---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: autopilot-note
description: "Use when invoking the portable autopilot-note capability. 산출물 라우팅/노트화. digest와 triage 제안을 만든다."
argument-hint: "[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]"
metadata:
  group: entry
  fam: ops
  modes: []
  blurb: "산출물 라우팅/노트화. digest와 triage 제안을 만든다."
---

# autopilot-note

autopilot-note 는 다른 autopilot-* 산출물을 _읽어_ Layer 2 노트 row 로 노트화하고 Layer 1 카드에 연결을 _제안_ 하는 누적·routing entry. 이 파일은 라우터와 호출 계약(자동 라우팅·Mode Forms·Routing Rules·Constraints)만 담고, 데이터 모델·매칭 로직·Stage 오케스트레이션·QA·예시·경계는 필요할 때 아래 reference 를 Read 한다.

> 산출물 폴더 컨벤션: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). Artifact: `<artifact-root>/notes/{date}/` — routing log + digest staging + reviewer logs. 진본 노트는 `<target>/_layer2/notes/<id>.md` (Layer 2), 진본 카드는 `<target>/cards/**.md` (Layer 1) — 둘 다 본 skill 산출물 (`<artifact-root>/notes/`) 과 _분리_. default `<target>` = `/home/nas/user/Uihyeop/notes/` (worklog-board 의 `CARDS_DIR` 부모).

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 _ceremony 작은_ 자리(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0) — 컨펌 없이 즉시 invoke. 메인 에이전트가 사용자 발화에 _"산출물 정리" / "오늘 누적" / "다이제스트" / "triage 확인" / "어제부터 변화 노트화"_ 같은 표현 등장 시 자동 호출.

**운영 자리**:
- **Cron** (사용자 자리) — 매일 새벽 05:00 KST 사용자 crontab 또는 worklog-board server-side scheduler 가 호출. _SKILL 안에 cron 명세 X_ — 본 SKILL 은 _idempotent 호출 가능_ 만 보장.
- **수동** — `/autopilot-note` slash 또는 자연어 발화. _묶음 정리_ 자리는 `--scope since <date>` + `--intensity standard` 권장. _첫 historical bulk_ 는 `--scope all`.

**Idempotency 보장** — 같은 source 가 두 번 들어와도 _노트 중복 X_. note `id` 가 _date + source-path 해시_ 라 같은 source → 같은 id → 갱신/skip (§Stage D).

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
| `autopilot-note --feedback` | **검토함 피드백 간단 처리 모드** (worklog-board prd §16 v50) — `_feedback/` 큐의 pending 의견을 갈래별 라우팅. 아래 §피드백 간단 처리. 가벼운 ceremony(Stage A-F 비적용) — 항목당 가볍게. |

## Routing Rules (5 갈래 — 본 skill 핵심)

| # | 자리 | Trigger | 동작 | 자동 / triage |
|---|---|---|---|---|
| **1** | L2 note row 생성 | 모든 trackable 산출물 | `_layer2/notes/<id>.md` 생성 (노트화 본문 + frontmatter) | **자동** |
| **2** | note `card_id` → L1 카드 연결 | 1차/2차 매칭 | frontmatter `card_id` set + `routing_status: inbox`(제안) + `routing_confidence`/`routing_reason` ⟨2026-06-10⟩ | **자동(제안)** |
| **3** | note `backbone_ids`/`task_ids` → L2 카탈로그 연결 (+emerge) | architecture·task 키워드 매칭 / emerge 단서 | frontmatter id list set + 없으면 카탈로그 entry 생성 | **자동 (카탈로그 emerge 포함)** |
| **4** | 신규 L1 카드 / 기존 task 연결 _제안_ | 매칭 task 없고 새 작업 단위 / 기존 task 강하게 부합 | `_triage/<id>.md` 제안 — ⟨v41/v44⟩ **기본 = task 카드**(`new-card` + `source_note_ids`), ⟨v45⟩ **묶음 우선**(노트당 1제안 금지)·**기존 task 부합 시 `link-note`**(연결만, 생성 0), project 는 보수적 세트 제안 한정 | **triage** (자동생성 X — L1 사용자 소유) |
| **5** | ambient note | 위 어디에도 확신 없음 | `card_id: null` + `routing_status: inbox` | **자동 (ambient)** |

**L2 적재·연결은 자동 _제안_ (#1·#2·#3·#5 — 무인 cron 은 전부 `routing_status: inbox`), L1 신설만 triage (#4)** ⟨2026-06-10⟩ — 에이전트는 _제안_, 확정(`confirmed`)은 worklog-board `/triage` 노트 라우팅에서 사용자 컨펌. 신규 L1 카드 confirm 도 `/triage` UI 가 watcher.

### Language Rule
- 사용자 향 출력 (chat report / digest 본문 / triage 카드 본문 / **노트화 본문**) 은 자연스러운 **한국어** (번역체 회피).
- frontmatter id / slug / file 이름은 영어·소문자·하이픈 (`note-20260609-a1b2c3` / `sr-corrnet` / `sep` / `tf-restormer-icml2026`).

## Constraints

- **L1 카드 불변** — `cards/**.md` frontmatter·본문 안 건드림. 매칭 read + 신규 `_triage/` 제안만. 사용자/UI 가 카드 책임.
- **L2 note 가 핵심 출력** — 산출물 1개 = note row 1개. 본문은 _노트화_ (원본 산출물 dump 아님 — 읽기 편한 요약).
- **카탈로그 emerge 는 가볍게** — backbone/task/paper entry 는 _필요 시 자동 생성_, 단 대규모 재구조는 사용자/autopilot-code.
- **Idempotent** — 같은 source → 같은 note id → 중복 X (`id` + frontmatter `source` + `.last_run.yaml` 다중 layer check).
- **원본 산출물 불변** — `<artifact-root>/{research,documents,plans,analysis_project}/` + `experiments/` 는 read-only.
- **신규 L1 카드는 triage 의무** — 자동 생성 X. 사용자 confirm 후 worklog-board UI 가 카드 실제 생성.
- **ambient 는 임시** — `card_id: null` note 는 자동 적재, 단 사후 사용자 promote 자리 (`/hubs` inbox).
- **STRUCT halt 자리 없음** — 본 skill 은 _노트화·routing_ 만. 산출물 자체 대규모 변경은 `autopilot-refine` 또는 사용자.
- **`<target>` default** — `/home/nas/user/Uihyeop/notes/` (worklog-board `CARDS_DIR` 부모). 하위 `cards/`·`_layer2/{backbones,tasks,papers,notes}/`·`_triage/`·`digests/`. 다른 자리는 `--target` flag.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/data-model.md` | 데이터 모델·계약 자리 | 2-Layer 모델(worklog-board PRD §2), note row 스키마(`_layer2/notes/<id>.md`), Position in autopilot family |
| `references/scope-qa-usage.md` | 입력 source·출력 자리·검증 rigor·경계 판단 시 | Scope(입력 source 6갈래·출력 자리·NOT for), 검증 rigor tier(intensity 파생, default light-tier), Examples, When NOT to use, Post-Run Checklist |
| `references/feedback-mode.md` | `--feedback` 검토함 양방향 루프 처리 시 (worklog-board prd §16) | 입력·라우팅(proposal/ui-code·위험도 분기)·처리 후·경계 |
| `references/resolution.md` | Stage A/C 매칭 로직 실행 시 | Source Resolution(Stage A 신규·변경 감지), Target Resolution(Stage C — card_id 1/2/3차·backbone_ids/task_ids/paper_id·intent/work_status) |
| `references/process.md` | Stage A-F 오케스트레이션 실행 시 (필수) | Stage A(scan)·B(본문 분석)·C(target matching)·C.5(verification)·D(apply)·D.5(편집팀 polish)·E(digest)·F(report) |
