## ━━━ eval 모드 ━━━ (학습 후 평가·분석)

학습 완료된 ckpt 를 평가·분석한다. 대상은 _직전 setup 실험_ (자동) 또는 `--parent <slug>` (재평가·새 데이터).

### E1: eval spec (1 화면)

**E1-1. 대상 결정** — `--from`/직전 `_RUNLOG` ⏳ 대기 줄 또는 `--parent` 로 _어떤 실험·ckpt_ 인지 확정. 평가 데이터(기존 test set 또는 새 데이터)·metric 자동 추론.

**E1-2. 한 화면 컨펌**:

```
=== Eval Spec ===
대상 실험:    <date>_<slug> (또는 parent: <slug>)
ckpt:        experiments/<slug>/runs/run-001/ckpt/best.pt
mode:        eval
평가 데이터:   <기존 test set / 새 데이터 — 재평가 자리>
metric:      <PSNR / SSIM / SI-SDR / 등>
비교 대상:    <sibling 실험 / 부모 / paper baseline>

이대로 진행? (진행 / 수정 / 중단)
```

**E1-3. run.json 출생 (eval-only `--parent` 진입 자리 — 기계판독 짝)** — `experiments/<id>/run.json` 이 _없으면_ 여기서 출생한다 (**file-existence 가드**: setup→eval 정상 사이클은 S3-2 에서 이미 만들었으므로 _재출생·덮어쓰기 X_). `eval --parent` 직접 진입(학습 없이 재평가 — 아래 예시 4)은 S3 를 안 거쳐 run.json 이 안 태어나는 공백을 닫는다 (사람용 거울 = E3-4 의 "⏳ 줄 없으면 새 줄 append" 와 짝). 출생값: `status:"running"`, `skill_mode:"eval"`(= `pipeline_state.mode`), `parent`(`--parent` slug), `started_at`(now, ISO8601), `config_ref`(부모 config 경로 또는 null), `ckpt_path`(평가 대상 ckpt — 예: `experiments/<parent>/runs/run-001/ckpt/best.pt`), `best` _생략_. E3-4 에서 setup run 과 동일하게 `done`+`best`+`ended_at` 갱신 (S3-2 setup 출생과 대칭 — §출력 데이터계약 lifecycle).

### E2: eval 실행 안내

**E2-1. eval 명령 안내** — scaffold 된 `eval.py` 를 ckpt + 데이터에 실행:

```
실행:
  cd experiments/<slug>
  python eval.py --config config.yaml --ckpt runs/run-001/ckpt/best.pt [--data <new_data>]
```

무거운 평가는 사용자 직접. _가벼운 평가_ (작은 test set) 자리는 사용자 발화 시 테스트팀 자동 실행 가능:

```
"가볍게 평가 돌려줘" 자리:
Agent(subagent_type="테스트팀"):
  "Mode: functional (eval run).
   target: experiments/<slug>/eval.py + ckpt
   Return: metric 값 (eval 최종 묶음 — run.json best 로 요약) + per-step stream 경로 (experiments/<slug>/metrics.jsonl)."
```

### E3: 분석 + summary + `_RUNLOG` ✅

**E3-1. 결과 정리** — 사용자가 "결과 정리해" 발화 또는 메인 에이전트가 eval 종료 보고 인지:

```
=== REPORT draft (→ REPORT.md 로 저장, E3-4) ===
실험:        {date}_{slug}
시도:        <spec 의 이번 시도 한 줄>
결과:        <metric 표 — best / final / 차이>
ablation:    <표 — 변수 × metric (sibling 실험 비교)>
부모 대비:    <parent 있으면 — delta>
관찰:        <2-3 bullet>
그림:        <figures/*.png 을 REPORT.md 본문에 ![](figures/..) 로 인라인 임베드 — 경로만 적기 X>
다음 후보:    <한 줄 — 다음 실험 시드>

이대로 저장? (저장 / 수정 / 중단)
```

**E3-2. plot / 시각화 → 자료팀 _figure-gen_ (옵션, 사용자 발화 시)**:

```
"결과 plot 그려줘" / "ablation 표 정리" 발화 자리:
Agent(subagent_type="자료팀", mode="figure-gen"):
  "Mode: figure-gen.
   target: experiments/{date}_{slug}/metrics.jsonl
   spec: 사용자 코드베이스의 figure 컨벤션 (project_user_paper_figure_style 메모리 또는 cwd 의 기존 plot 참고)
   Output: experiments/{date}_{slug}/figures/{plot_name}.{png,pdf}."
```

> **생성한 figure 는 반드시 `REPORT.md` 본문에 markdown 이미지로 인라인 임베드** (`![<caption>](figures/<plot>.png)`) — `figures/` 에 저장만 하고 경로만 적는 것 **X**. REPORT.md 가 _그림 들어간_ 보고서가 되게 (그림 없는 텍스트 보고서 금지). figure 가 STORY 의 결과 서술과 직결되면 STORY.md 에도 임베드.
> **이미지 vs 오디오 경계 (보고서 형식 선택의 단일 기준)**: markdown 은 이미지를 인라인 렌더하므로 _그림은 항상 md 임베드로 충분_ — **그림만 있으면 HTML 만들지 말 것**. E3-5 의 HTML 은 _오직 오디오/미디어 재생_ 용 (markdown 이 `<audio>` 재생을 막기 때문). 즉 figure→md 인라인(default) / audio→HTML(E3-5).

**E3-3. paper 비교 → 연구팀 _research-survey_ (옵션, qa standard+ + 사용자 발화 시)**:

```
"결과를 기존 paper 와 비교해줘" 발화 자리:
Agent(subagent_type="연구팀", mode="research-survey"):
  "Mode: research-survey (실험 결과 자리).
   결과: experiments/{date}_{slug}/REPORT.md
   사전 자료: <artifact-root>/research/ + analysis_project/paper/

   비교 axis:
   - 본 실험의 metric vs 기존 paper baseline
   - 본 실험의 변경 자리가 paper 어디 자리와 닿나
   - 본 실험의 관찰이 paper 의 주장·반박과 어떤 자리

   Return: 비교 표 + 한국어 한 단락 요약 (REPORT.md 에 ## 기존 paper 와의 비교 섹션 추가)."
```

**E3-5. 정식 보고서 (옵션 — 공유·의사결정용. `--report` / "보고서 써줘"·"공유용" 발화 / high-stakes(논문·외부 공개))**:

`summary.md` 는 _1 화면 실험 기록_ (계보·다음 후보). 그걸 넘어 _공유·의사결정용 정식 문서_ 가 필요하면 본 단계에서 산출. 두 형태 — 실험 성격으로 분기:

- **prose 보고서** (일반 실험) → `autopilot-draft --mode doc` 핸드오프. 입력 = `experiments/{date}_{slug}/{summary.md, STORY.md, figures/}` + runs metrics. 산출은 `documents/{date}_{slug}/` (draft 컨벤션·리뷰·다듬기). eval 은 _요청·핸드오프_ 만 — prose 생성은 draft 가 담당(machinery 중복 방지).
- **재생 HTML 보고서** (음성·오디오·미디어 실험 — 청취·스펙트로그램·시각 비교가 본질) → `자료팀 figure-gen` 으로 분리음/스펙트로그램 세그먼트 + 임베드 `<audio>`/`<img>` **단일 HTML** 생성 (`experiments/{date}_{slug}/report/report.html`). _markdown `<audio>` 는 VS Code 프리뷰가 차단_ → **audio 도메인은 HTML 기본**. 긴 오디오는 _N분 단위 세그먼트 페이지_ 분할. 필요시 `python -m http.server --bind 0.0.0.0 <port>` 로컬 서빙 + 접속 URL 안내.

기본 deliverable = `REPORT.md`(E3-4, 자체완결 정식 보고서). 본 E3-5(autopilot-draft prose / 재생 HTML)는 그 위에 _외부 공개·의사결정용 doc-pipeline_ 또는 _오디오/미디어 재생_ 이 필요할 때만 추가. 둘 다 필요하면 prose + HTML 병행(prose 가 HTML 비교본을 상대링크).

**E3-4. 저장 — 산출물 갱신** (최종 deliverable = `REPORT.md`):

- `experiments/{date}_{slug}/REPORT.md` — **eval 의 최종 산출물 = 자체완결 정식 보고서.** 구조: _요약(Executive Summary) 맨 위_ → 배경·동기 → 가설 → 방법 → 결과 → 해석 → 결론 → 다음 → 재현. **figure 는 `![](figures/..)` 본문 인라인.** **자체완결 필수** — 실험에서 도입한 조건명·구조명·약자·metric 정의를 _보고서 안에서 풀어_ 대화 맥락 없는 독자도 읽히게(예: "single/multi 같은 게 뭔지 보고서만 봐선 모름"을 차단). 사용자가 볼 것은 흩어두지 말고 _전부 이 한 파일에 통합_ (summary·STORY 요지·metrics·figure 를 여기로).
- `experiments/{date}_{slug}/summary.md` — RUNLOG/parent auto-read 용 _1줄 인덱스_ (판정 한 줄 + `REPORT.md` 포인터). _사용자 deliverable 아님._
- `experiments/{date}_{slug}/STORY.md` — narrative 누적 (motivation·이전/부모 정리·이번 시도·결과·다음 후보 한 단락)
- `<artifact-root>/experiments/_RUNLOG.md` — S3-2 에서 append 한 _해당 실험(date+slug) 줄_ 을 찾아 _상태 ✅ 완료 + 결과·다음_ 으로 **갱신** (새 줄 append X — 한 실험 = 한 줄 유지):
  ```
  | 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | ✅ 완료 | val PSNR 28.4→28.7 (+0.3) · 다음: warmup 1k step |
  ```
  - 부모 있으면 _시도_ 칸에 `(← <parent_slug>)` 표기. 드물게 ⏳ 줄이 없으면(예: setup 없이 `--from eval` 직접 진입) 새로 append. 중단·실패는 `❌ 중단` 으로 갱신.
- `experiments/{date}_{slug}/run.json` — **기계판독 manifest 갱신** (S3-2 setup / E1-3 eval-only 에서 출생한 파일을 찾아). `status:"done"`, `ended_at`(now, ISO8601), `best:{name,value,step}`(eval 분석 산물 — `_RUNLOG ✅`·REPORT 와 동일 metric). 중단·실패는 `status:"failed"` + `ended_at`(중단 시각) 기록, `best` _생략_ (`_RUNLOG ❌ 중단` 거울 — §출력 데이터계약 best 부재 규칙). `_RUNLOG.md` 는 이 파일의 사람용 거울.
- **종료 dispatch (방출만)** — eval 종료 시 `run.json` 의 `best` + parent 대비 delta 를 worklog 결재함/보드가 소비하도록 _방출_. **lab 은 방출만 — 능동 push X** (수신·카드화는 worklog E3, PRD §25.7; loops 결재함 패턴 동형). 소스 = `run.json best:{}` (새 분석 0). (§출력 데이터계약 종료 dispatch)
