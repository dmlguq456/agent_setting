## Process

### Stage A — Source scan
1. Read `<artifact-root>/notes/.last_run.yaml` → `last_run_ts`. 없으면 `--scope` 시작 자리.
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
`<artifact-root>/notes/{date}/pipeline_summary.md` 작성 (3-tier §5):
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
• 자체 로그: <artifact-root>/notes/<date>/

다음 자리 ⟨2026-06-10⟩: worklog-board 홈/`/triage` 에서 이번 run <N> 건 검토 — 승인/고치기/폐기로 confirmed 승격 (무인 실행은 자동확정 안 함). {if M > 0:}+ 신규 L1 카드 제안 <M> 건 confirm.
```
