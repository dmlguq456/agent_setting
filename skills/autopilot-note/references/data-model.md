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
source: <artifact-root>/plans/2026-06-08_x/   # 원본 산출물 경로 (idempotency check key)
---

산출물을 _읽기 편하게 노트화_ 한 본문 (한국어). 결과·결정·가설·metric 요약 + [[연결]].
```

## Position in autopilot family

`autopilot-note` 는 _누적·routing_ 자리 (Layer 2 생성). 다른 autopilot-* 멤버는 _산출물 생성_ 자리:

- `autopilot-research` / `autopilot-code` / `autopilot-draft` / `autopilot-lab` / `analyze-project` → 산출물 _생성_, `<artifact-root>/{research,plans,documents,experiments,analysis_project}/` 또는 `experiments/` 에 떨어트림.
- `autopilot-note` → 위 산출물들을 _읽어서_ Layer 2 노트로 _노트화_ + Layer 1 카드에 _연결_. _원본 산출물 불변_.

worklog-board 앱 (`~/worklog-board/`) 은 _노트·카드를 보여주는 UI_, 본 skill 은 _Layer 2 노트 생성_, 사용자 cron 또는 수동 호출이 _트리거_. 세 자리 분리.

`autopilot-refine` 과의 차이 — refine 은 _<artifact-root>/{research,documents}/ 의 markdown 산출물 자체_ 정정, autopilot-note 는 _그 산출물을 source 로 읽어 별도 Layer 2 노트로 노트화_. 대상과 동작 본질이 다름.
