## Pipeline (6 phase)

### Phase 1 — Source Discovery + 자동 변환 (PDF + PNG 하이브리드)

목적: aspect 별 _모든 expected source_ 를 발견·분류·인덱싱 + 에이전트가 직접 read 못하는 자료 (docx / pptx / hwpx) 는 _PDF + PNG_ 자동 변환.

절차:

1. **사용자 `--source <path>` 일람** — _사용자가 명시한 폴더 path_ (콤마 분리 복수 가능). `--source` 없으면 _자료 0 자리_ + 한 줄 안내: _"참고 자료 폴더 path 자리 `--source` 로 명시 부탁"_.
2. **재귀 자동 발견** — 사용자 명시 path 안 _모든 subfolder_ 재귀 scan. 자료 type 별 aspect 자동 분류 (`all` 호출 자리 또는 aspect 별 매핑):
   - `*.pdf` (paper / report) → figure / writing / analysis / domain aspect 자리
   - `*.pptx` / `*.ppt` → presentation aspect 자리 (자동 PDF + PNG 변환)
   - `*.docx` / `*.hwpx` / `*.hwp` → writing aspect 자리 (자동 PDF 변환)
   - `model/` / `*.py` / `*.yaml` / `*.ipynb` / 코드 자료 → coding_convention / analysis aspect 자리
   - 폴더 안 `figures/` / `figure_ppt/` → figure aspect 자리
   - 폴더 안 `analysis/` → analysis aspect 자리
   - `*.mp4` / `*.mov` 등 video 자료 → **skip** (analyze-user 자리 분석 X, 한 줄 보고)
3. **메모리 자료 일람** (domain aspect 시) — `<agent-home>/projects/*/memory/*.md` 전수 (시스템 자료 자동, 도메인 약자 자리 확인).
4. **scholar / arXiv 자료 일람** (writing / domain aspect 시) — 사용자 명시 paper 목록 + abstract.
5. **자동 변환 (LibreOffice headless)** — 에이전트가 직접 read 못하는 자료 (docx / pptx / hwpx / xlsx / doc / ppt / hwp) 발견 시:

**LibreOffice 자동 설치 (부재 자리)**:

```bash
if ! command -v libreoffice &>/dev/null; then
  echo "LibreOffice 부재 — 자동 설치 시도..."
  sudo apt install -y libreoffice 2>&1 || {
    echo "❌ 자동 설치 실패 (sudo 권한 자리 필요)."
    echo "   사용자가 직접 설치: sudo apt install libreoffice"
    echo "   또는 사용자 사전 PDF 변환 후 source 자리 재지정 fallback"
  }
fi
```

자동 설치 시도 자리 — _권한 자리_ 또는 _네트워크 자리_ 실패 가능. fallback 안 시 _변환 안 된 자료 skip + 보고_.

| 자료 | 변환 | 저장 자리 |
|---|---|---|
| **docx / hwpx / xlsx / doc** (텍스트 위주) | `libreoffice --headless --convert-to pdf` — PDF 한 자리 | `<agent-home>/user_profile/_internal/converted_pdfs/<name>.pdf` |
| **pptx / ppt** (시각 layout 핵심) | PDF + page 별 PNG 두 자리 — PDF 는 텍스트·layout / PNG 는 시각 fidelity (글자 크기·폰트·배치 보존) | `_internal/converted_pdfs/<name>.pdf` + `_internal/converted_pngs/<name>_slide{NN}.png` |
| **hwp** (legacy) | LibreOffice 변환 _부분적_ — 시도 + 실패 시 사용자 안내 ("hwp 자리 변환 깨짐 — 사용자 직접 PDF 변환 후 재지정") | 성공 자리 PDF / 실패 자리 skip + 보고 |
| **mp4 / mov / 기타 video** | _skip_ — analyze-user 자리 분석 X | 한 줄 보고 |

변환 명령 자리:

```bash
# docx / hwpx / xlsx
libreoffice --headless --convert-to pdf "<file>" --outdir _internal/converted_pdfs/

# pptx — PDF + 슬라이드별 PNG 두 자리
libreoffice --headless --convert-to pdf "<file>.pptx" --outdir _internal/converted_pdfs/
pdftoppm -png -r 150 _internal/converted_pdfs/<file>.pdf _internal/converted_pngs/<file>_slide
```

**LibreOffice 부재 자리** — 한 줄 안내: _"LibreOffice headless 부재 — `sudo apt install libreoffice` 또는 사용자가 직접 PDF 변환 후 source 자리 재지정"_. 변환 안 한 자료는 분석 source 자리에서 _제외_ + 보고.

6. **분류 표기** — 각 source 별 type (figure / latex / slide / py-script / memory / paper-abs / code-model / code-train / code-config / code-notebook / **converted-pdf (변환 결과 PDF) / converted-png (pptx 변환 슬라이드 PNG)**) + 마지막 수정 시각 + 사이즈 + (변환 자료) 원본 path.
7. **`_internal/source_index.md` 작성** — 위 일람 통째.

산출:
- `<agent-home>/user_profile/_internal/source_index.md` (또는 갱신)
- `_internal/converted_pdfs/*.pdf` + `_internal/converted_pngs/*_slide{NN}.png` (자동 변환 결과)
- Phase 1 verdict 한 줄 (총 source N 건 발견, 어느 aspect 에 몇 건씩, 자동 변환 M 건).

### Phase 2 — Aspect-specific Analysis (3-instance consensus, parallel)

목적: aspect 별 source 에서 _범용 패턴_ 추출 + consensus 가중치 부여. _autopilot-research 의 paper-agent fan-out_ 과 같은 결 — 한 source 에서 _3 인스턴스_ 가 독립적으로 패턴 카탈로그를 만들고, _공통 등장 빈도_ 로 신뢰도 가중.

#### Phase 2.1 — 3-instance parallel extraction

각 aspect 별로 _연구팀 3 인스턴스_ 병렬 호출. 같은 source index · 같은 prompt · 다른 conversation thread (LLM stochasticity → 자연 다양성, cross-talk X).

```
Agent(연구팀, prompt="""
사용자 산출물 분석 — aspect: figure (인스턴스 {A|B|C})
Source index: <agent-home>/user_profile/_internal/source_index.md
기존 profile 레코드 (mem profile 01_paper_figure_style): {기존 내용}

자료 read 자리:
- 원본 read 가능 자료 (PDF / PNG / md / py 등) — 직접 Read
- docx / hwpx / xlsx — `_internal/converted_pdfs/<name>.pdf` 자료 read (Phase 1 자동 변환)
- pptx — `_internal/converted_pdfs/<name>.pdf` (텍스트·layout 자료) **+** `_internal/converted_pngs/<name>_slide{NN}.png` (시각 fidelity·글자 크기·폰트·배치 자료) **두 자리 모두**. 시각 자리 핵심 자리 (presentation aspect 자리) 는 PNG 자료 1순위 인용.

추출 대상 패턴 (aspect 별 — 예 figure):
1. Architecture diagram 양식
2. Curve plot 양식
3. Scatter / 표 layout
4. Spectrogram 관례
5. 도메인별 metric set
6. ours 강조 패턴

**figure aspect 는 _거시 디자인 취향·감각_ 중심 추출** (2026-05-27 재정의): 원본 도형은 Phase 5b 가 `assets/figure/svg/<base>_slide-N.svg` 로 **개체 추출 → 디자인팀이 복사**한다. 따라서 _micro 재현 spec_ (geometry H-비율 · corner radius · stroke 수치 · marker path · drop shadow opacity · isometric 각도 · zoom 배율 · 단계별 재현 recipe) 은 **분석에서 뺀다** — 추출 개체에 이미 들어 있어 잉여. 대신 _어떤 개체를 골라 어떻게 배치하는가_ 를 좌우하고 _신규 작업에도 전이_ 되는 **macro 취향**을 깊게 (위 6 패턴 + 아래):

7. **Composition / 거시 레이아웃 감각** — banner+분해도 2단 구성, density(어디를 빡빡하게 / 어디에 숨통을), 정렬·대칭, 화면 분할 비율. 구체 px 아닌 _원칙·느낌_.
8. **강조·절제 전략** — 무엇을 강조(novelty 빨강·굵은 테두리·빨강 텍스트)하고 무엇을 절제(표 색음영 자제·색 남발 X·bold+위치 우선)하는가. ours 부각 방식.
9. **위계·시선 흐름** — focal point 가 어디고, 좌→우(top-level)/아래→위(unit) 흐름, 라벨 크기 위계.
10. **색 _의미_ 체계** — 역할→색군 매핑 원칙(encoder green / decoder orange / novelty red / aux gray / zoom gold). exact hex 는 추출 개체에 내장 — _매핑 규칙_ 만 (hex 표는 참고용 §A7 유지하되 분석 부담 X).
11. **시그니처·일관성** — deck 가로질러 반복돼 "이 연구자 figure"답게 만드는 것(key/value 라벨 화살표 · 텐서 glyph+처리축 · magma anchor 등 _존재·의미_ 수준, 그리는 법 X).

산출 = **Part A(무엇을/왜 + 거시 취향) 중심** + §B0(원본 개체 라이브러리 `assets/figure/svg/` 위치 + 복사·재배치 가이드). 무거운 Part B 재현 recipe 는 _최소화_ — pptx 없는 fallback 재현 자리에서만 필요.

각 패턴은 _source 인용_ 필수 (어느 paper / figure / script). pptx 자리는 _slide{NN}.png_ 자리 명시 (시각 자리 검증 가능 자료).
다른 인스턴스의 결과를 보지 않고 _독립_ 으로 추출.
mode=init 통째 교체, mode=update 누적.

산출: <agent-home>/user_profile/_internal/aspect_{aspect}_run_{A|B|C}.md
""")
```

`writing` / `presentation` / `analysis` / `domain` / `coding_convention` 동일 패턴 — _추출 대상_ 만 aspect 별 다름. `all` 호출 시 6 aspect × 3 인스턴스 = 18 호출 병렬 (Claude Code Agent tool 단일 메시지 안 multi-call).

`coding_convention` 의 _추출 대상_ (figure 예시 자리와 대칭):
1. model 폴더 구조 (한 모델 = 한 폴더 묶음 단위 / 파일 구성 / naming)
2. config 메커니즘 (yaml / argparse / hydra / dynaconf — 빈출 패턴)
3. 변형 prefix 패턴 (`_ft01_` 식 fine-tuning 변형 / version prefix)
4. preferred layer (cross-project 빈출 — 도메인별 layer set)
5. framework 선호 (pure PyTorch / lightning / accelerate / 기타)
6. metric set (도메인별 — PSNR/SSIM/SI-SDR/WER/CER/Acc)
7. log·ckpt 자리 (`runs/{run-id}/` / wandb / tensorboard / 단순 파일)
8. seed·reproducibility 패턴 (seed 자리 / git hash 기록 / split 고정)
9. naming convention (snake_case / PascalCase / 약자 대문자)

#### Phase 2.2 — Consensus aggregation (메인 skill 직접 처리, sub-agent X)

3 run 의 카탈로그를 메인 skill 이 직접 read + 합산:

1. **패턴 normalize** — 같은 의미 패턴은 같은 식별자 (예 _"Times New Roman fallback chain"_ ↔ _"Times-equivalent serif fallback"_ 은 같은 패턴).
2. **가중치 부여**:
   - 3 인스턴스 모두 발견 → **confidence = 1.0 (high)** — 본문 채택, 가중치 메타 X.
   - 2 인스턴스 발견 → **confidence = 0.6 (medium)** — 본문 채택, `(consensus 2/3)` 메타.
   - 1 인스턴스 발견 → **confidence = 0.3 (low)** — _quarantine_ 자리, Phase 4 QA 통과 시만 본문 채택. 통과 못 하면 _drop_ 또는 _open question_ 으로 이관.
3. **충돌 해소** — 같은 자리에서 인스턴스 간 _값 충돌_ 시 (예 폰트 _Times_ vs _STIX_) 다수결 우선. 1:1:1 으로 갈리면 _open question_.

산출:
- `_internal/aspect_{aspect}_run_{A|B|C}.md` (3 개, 인스턴스별 독립 카탈로그)
- `_internal/aspect_{aspect}_draft.md` (합본 — frontmatter `confidence:` 표 + quarantine 절 분리)
- `_internal/aspect_{aspect}_consensus.md` (합산 메타 — 각 패턴의 _확인된 인스턴스 수_ 일람)
- Phase 2 verdict — aspect 별 confidence 1.0/0.6/0.3 패턴 수.

### Phase 3 — Cross-reference Validation

목적: aspect 사이 _일관성_ 점검. 예 `01_paper_figure_style` (`mem profile 01_paper_figure_style`) 의 _ours 색_ 이 `03_presentation_strategy` 의 _슬라이드 강조 색_ 과 어긋나면 어느 쪽이 맞는지 결정.

절차:

1. 7 aspect draft 를 모두 Read.
2. 다음 _cross-aspect 일관성 axis_ 점검:
   - 색 팔레트 — figure / presentation / scatter / spectrogram 의 색 결정이 같은가?
   - 폰트 — figure / presentation / paper 의 폰트 일관성.
   - 도메인 용어 — writing / domain 의 약자·용어 사용이 일치하는가?
   - metric set — figure 의 metric column / analysis 의 검증 방법 / **coding_convention 의 metric set** 이 매칭되는가?
   - **도메인 layer** — coding_convention 의 preferred layer 가 domain expertise 의 주력 도메인 자리와 매칭되는가? (예 TF dual-path DNN 자리면 LayerNorm2d / dual-path block 자리)
3. 모순 발견 시 _source 인용 빈도가 더 많은 쪽_ 우선 (또는 _더 최근 자료_ 우선).
4. 모순 자체를 _open question_ 으로 남길지, _즉시 해소_ 할지 결정 — 사용자 명시 패턴 (`/post-it --scope user`) 이 있으면 그게 ground truth.

산출:
- `_internal/cross_aspect_consistency.md` — 점검 결과 + 모순 해소 결정.
- Phase 3 verdict — N 자리 모순 발견, M 자리 해소, K 자리 open question 남김.

### Phase 3.5 — Prior-version 변증법 대조 (dialectic reconciliation, `--mode update` 한정)

> Hermes Honcho 의 _dialectic user modeling_ 벤치마킹 이식(T6, 2026-06-15). Phase 3 이 _aspect 사이_ 일관성을 본다면, 본 phase 는 _이번 추출(antithesis) vs 직전 프로필(thesis)_ 을 변증법적으로 대조해 _synthesis_ 를 만든다. user_profile 은 누적 자료라 "최신이 옳다"는 단순 덮어쓰기가 사용자 모델을 _퇴행_ 시킬 수 있다 — 모델이 _왜_ 바뀌었는지 추론해야 한다. `--mode init` 은 직전 버전이 없으므로 skip.

절차:

1. 각 aspect 의 _직전_ profile 레코드 (`mem profile <stem>`) 대조 (있으면 `_internal/versions/` 최신 snapshot 도 참조) — 이번 draft 와 항목별 대조.
2. 각 패턴을 4 분류:
   - **confirm** — 직전과 일치 (강화, confidence 유지/상향).
   - **refine** — 직전을 _구체화·정밀화_ (모순 아님, 결대로 발전).
   - **contradict** — 직전과 _충돌_. 여기서 빈도·최신 자동승자 금지 — 아래 3 의 추론을 거친다.
   - **new** — 직전에 없던 신규 패턴 (confidence 는 Phase 2 consensus 따름).
3. **contradict 합치기 (synthesis)** — 단순 "최근 우선" 대신 _왜 달라졌나_ 를 셋 중 하나로 판정하고 근거 1줄:
   - (a) **사용자 진화** — 실제 선호·방식이 바뀜 (최근 source 가 일관되게 신호) → 갱신 + 변경 이력 1줄.
   - (b) **직전이 과잉일반화** — 직전이 적은 표본의 잘못된 일반화 → 정정 + 직전 오류 명시.
   - (c) **맥락 의존** — 둘 다 맞고 _조건이 다름_ (예: 학회별·도메인별) → 덮어쓰지 말고 _조건부 분기_ 로 양립 기술.
4. 사용자 명시 패턴 (`/post-it --scope user` 의 `## 사용자 수동 메모`) 은 모든 추론에 우선하는 ground truth — contradict 시 사용자 메모 채택.

산출:
- `_internal/prior_reconciliation.md` — 패턴별 confirm/refine/contradict/new 분류 표 + contradict 의 synthesis 판정(a/b/c)·근거.
- contradict 합치기 결과를 aspect draft 에 반영 (변경 이력은 각 파일 `changelog:` frontmatter 에 한 줄).
- Phase 3.5 verdict — confirm/refine/contradict/new 개수 + 진화(a)/정정(b)/분기(c) 내역.

### Phase 4 — Multi-agent QA Verification (adversarial 고정, 4 parallel reviewer)

목적: 추출된 패턴이 _실제 source 와 일치_ 하는지, _사실 오류·과잉 일반화·bias·missing aspect_ 없는지 검증. 사용자 프로필은 propagating 자료라 _4 개 reviewer 모두 항상_ 병렬.

- **Agent A — source coverage** (fast reviewer; Claude adapter: sonnet; `_internal/qa_coverage.md`):
  ```
  사용자 프로필 draft 와 source index 대조.
  각 추출된 패턴이 _하나 이상의 source 인용_ 을 갖는가?
  source 일람의 file 들이 _모두 추출 대상에 포함_ 됐는가?
  누락된 source 또는 인용 없는 패턴은 🔴 finding.
  ```

- **Agent B — pattern accuracy + low-confidence verification** (deep reviewer; Claude adapter: opus; `_internal/qa_accuracy.md`):
  ```
  draft 의 각 패턴을 source 자료와 직접 대조.
  색 hex code · 폰트 이름 · figsize · paper title / venue / 연도 등 verbatim 정확성.
  잘못된 fact · 과장된 일반화 · source 와 모순되는 표현은 🔴 finding.

  **추가 axis — confidence 0.3 (low) quarantine 패턴 집중 검증**:
  - 1 인스턴스만 발견한 패턴이 source 와 verbatim 일치하면 → confidence 0.6 으로 _승격_ 권장.
  - source 에서 찾을 수 없거나 인스턴스의 over-generalization 이면 → _drop_ 권장.
  - 한 인스턴스만 봤지만 source 가 _희소_ (예 단 한 paper 에서만 등장) 한 자리면 → 0.3 그대로 _open question_ 으로 이관 권장.
  ```

- **Agent C — factcheck** (fast fact-checker; Claude adapter: sonnet; `_internal/qa_factcheck.md`):
  ```
  paper 인용 verbatim 점검 — 제목 / 학회 / 연도 / 인용수 / DOI / arXiv ID.
  metric 수치 인용 점검 — paper / abstract 에서 직접 대조.
  ```

- **Agent D — external adversary review** (`codex-review-team` in Claude adapter, `_internal/qa_external.md` or legacy `_internal/qa_codex.md`):
  ```
  외부 hostile reader 관점 review — 사용자 프로필이 _과잉 일반화_ · _bias_ · _missing aspect_ 가 있는가?
  ```

> external adversary 가용 안 한 환경이면 Agent D 만 skip + 한 줄 경고. A·B·C 는 반드시 실행.

산출:
- `_internal/qa_{coverage,accuracy,factcheck,external}.md` (4 개; Claude adapter legacy path may use `qa_codex.md`)
- Phase 4 verdict:
  - 🔴 N · 🟡 M · 🟢 K finding 누적.
  - Consensus 변화 — _승격_ (0.3 → 0.6) N 건 · _drop_ M 건 · _open question 이관_ K 건.
- 🔴 finding 1 개 이상 → Phase 2–3.5 로 _자동 retry_ (max 2 회). 2 회 모두 실패 시 _pipeline failed_ 보고.

### Phase 5 — Output Generation

목적: verified draft 를 _DB `type=profile` 레코드_ 에 write. agent invoke 시점 부담 줄이면서 _핵심 anchor 는 본문 유지_.

**본문 vs internal 분리** (목표: 각 profile 레코드 body **7-10K tokens**. `01_paper_figure_style` 레코드는 _거시 취향 중심_ 으로 재정의(2026-05-27) — Part A(무엇을/왜 + composition·강조·위계·색의미·시그니처) + §B0(원본 개체 라이브러리 `assets/figure/svg/` 포인터). 무거운 Part B 재현 recipe·geometry 수치는 _최소화_(디자인팀이 개체를 복사하지 재현 X — fallback 자리에서만). 기존 Part B 가 비대하면 다음 update 에서 거시 취향으로 trim):

| 자리 | 본문 채택 | 본문 외 자리 |
|---|---|---|
| high confidence (3/3) | ✅ 채택 | — |
| medium (2/3) | ✅ 채택, `_(consensus 2/3)_` 메타 | — |
| quarantine (1/3, drop) | ❌ | `_internal/aspect_{x}_dropped.md` |
| Open Questions | ❌ | `_internal/open_questions.md` |
| 분석 source 일람 | ❌ | `_internal/source_index.md` 참조 |
| 사용자 수동 메모 | ✅ `## 사용자 수동 메모` 절 보존 | — |

**본문 wording 정책** — 불릿 1-3 줄 + 핵심 anchor 유지:
- _구체 anchor_ — paper Fig.N / hex code / 모델명 / 데이터셋 / 변수명 / 함수명 → **본문 유지**
- _긴 explanatory prose_ — 풀어쓰기 설명·중복 narrative → **draft 로 이관** (`_internal/aspect_{x}_draft.md` 참조)
- 예:
  ```markdown
  ## 1. Architecture diagram
  - block: rounded rectangle, outline grayscale (TF-Restormer Fig.1 / TF-CorrNet Fig.2)
  - 색: encoder 녹색 #3F8C5C / decoder 주황 / ours 강조 빨강 #A0152A
  - arrow: solid 1.5pt, label 산세리프 8pt
  ```

5K 이하는 무리 — agent 가 self-contained 하려면 구체 anchor 가 필요. 7-10K 가 적정선.

절차:

1. **--user-refine pause** (있으면) — draft + qa review path 안내 후 종료. resume: `/analyze-user --from output`.
2. **mode 별 처리 (DB record write)**:
   - `init` — 새 body 작성. 기존 레코드가 있으면 먼저 `python3 <agent-home>/tools/memory/mem.py profile <stem>` 으로 현재 body 를 읽어 `## 사용자 수동 메모` 절을 추출·보존 후 새 body 에 포함. `_internal/versions/v{N}/` 에 이전 body 텍스트 스냅샷 보존(convention). 이후 `python3 <agent-home>/tools/memory/mem.py add durable profile <body> --scope global --source user-profile:<stem>` 으로 DB write.
   - `update` — 반드시 **`python3 <agent-home>/tools/memory/mem.py profile <stem>`** (rowid-DESC newest-wins tie-break 적용 읽기) 로 현재 body 를 읽는다 — raw `db_iter_records` 직접 쿼리 X (stem-dup 발생 시 stale body 를 읽어 `/post-it promote` 로 splice 된 `## 사용자 수동 메모` 를 orphan 시킬 수 있음). 읽은 body 에 새 분석 내용을 splice — `## 사용자 수동 메모` 절은 그대로 유지. body 안에 changelog 절 한 줄 추가 (`## Changelog` 내 `{date}: {변경 요약}`). 전체 새 body 를 `python3 <agent-home>/tools/memory/mem.py add durable profile <whole-new-body> --scope global --source user-profile:<stem>` 으로 DB write (파일 Edit X).
   - **Write-path (source-keyed UPSERT)**: `mem add` 의 `write_record` 는 `(tier, scope, source)` 키로 in-place UPDATE — 같은 `source=user-profile:<stem>` 레코드를 body 변경 시 교체 (id 보존, dup row 없음). `mem profile <stem>` 읽기와 결합해 read·write 양쪽 결정론.
   - **수동 메모 two-writer contract**: `## 사용자 수동 메모` 절은 analyze-user(`update`) 와 `/post-it promote --scope user` 두 곳이 같은 source `user-profile:<stem>` 레코드에 write. 반드시 `mem profile <stem>` tie-broken 읽기로 현재 body 를 확인 후 splice — 다른 경로(raw query) 사용 시 stale dup 에서 splice 해 promoted memo 를 orphan 시킴.
3. **per-stem 사후 검증 (source-blind dedup caveat)**: 각 stem write 직후 `python3 <agent-home>/tools/memory/mem.py profile <stem>` 로 read-back 해 반환 body 가 방금 쓴 body 와 일치하는지 확인. 불일치 → `find_dup` 의 source-blind dedup 으로 다른 stem 의 기존 레코드와 병합된 것 — 큰 소리로 fail (stem body 충돌, 수동 확인 요).

산출: DB `type=profile` 레코드 (stem 별, `source=user-profile:<stem>`, 7-10K tokens 목표, 구체 anchor 유지). 파일 Write X.

### Phase 5b — pptx 개체 추출 (**figure aspect 전용**, 사용자 참조용 자료 라이브러리 산출)

목적: figure pptx 의 슬라이드를 SVG 로 추출해 **사용자가 pptx 에서 figure 만들 때 참조할 _벡터 개체 라이브러리_** 를 산출. _LLM 이 재현하지 않는다_ — paper architecture figure 는 사용자가 pptx 에서 직접 만들고, 본 라이브러리는 그 작업의 reference 다 (2026-05-28 정책).

> **결정 배경**: ① 텍스트 spec 만으로 LLM 이 재현 → ~92% 천장 · ② LLM 이 primitives `<defs>` 복사로 재유도 → "투박함" 반복 거부 · ③ LLM 이 element 단위로 추출 SVG path 를 떼어 재조합 → 그래도 craft 미달. 결론: figure 본 그림은 _사용자 손_, LLM 은 _layout 가이드 + 자료 안내_ 까지. 본 Phase 는 자료 안내의 자료를 만든다.

절차:

1. **pptx → SVG 슬라이드 추출**: `figure_ppt/*.pptx` (또는 변환된 `_internal/converted_pdfs/<base>.pdf`) 의 전 슬라이드를 `pdftocairo -svg -f N -l N <pdf> out.svg` 로 추출 (도형·텍스트 벡터, 임베드 spectrogram 은 raster). 산출 `<agent-home>/user_profile/assets/figure/svg/<base>_slide-N.svg`. (LibreOffice `--convert-to svg` 도 가능하나 multi-slide 는 pdftocairo per-page 가 안정.)
2. **canonical 앵커 복사** (옵션) — 대표 슬라이드(top-level pipeline 등)를 `assets/figure/ex1_*.svg` 류로 복사해 `01 §B0` 에서 참조하기 쉽게.
3. **`01 §B0` 참조 갱신** — figure 참조를 raster PNG → 추출 SVG 링크로 (clone 가능 형태).

산출:
- **`assets/figure/svg/<base>_slide-N.svg`** — 추출 개체 라이브러리. _사용자가 pptx 에서 figure 작업할 때 reference + 디자인팀 layout 가이드 산출 시 reference_.
- `01` §B0 — 라이브러리 위치·canonical 앵커 안내.
- Phase 5b verdict — 추출 슬라이드 수 + canonical 앵커 list.

> _LLM 재현 fallback·primitives 산출은 폐기 (2026-05-28)._ 추출 라이브러리가 부재해도 LLM 이 재현을 시도하지 않는다 — 사용자에 한 줄 안내 후 layout 가이드만 산출.

### Phase 6 — Pipeline Summary

`<agent-home>/user_profile/_internal/pipeline_summary.md` (단일 파일, append 누적):

```markdown
## {YYYY-MM-DD} — {aspect} {mode}

**Source**: {N source files scanned, breakdown by type}
**Extracted patterns**: {M new + K updated + L removed}
**Consensus distribution**: confidence 1.0 = {n_high} · 0.6 = {n_medium} · 0.3 (quarantine) = {n_low}
**Quarantine outcome (Phase 4 QA)**: 승격 {n_up} · drop {n_drop} · open question {n_oq}
**QA findings**: 🔴 {n_red} 🟡 {n_yellow} 🟢 {n_green}  (resolved {res})
**Affected records**: {갱신된 profile 레코드 source list (user-profile:<stem> 형식)}
**Retry count**: {0 / 1 / 2 if any}
**Figure repro gap** (figure aspect 시): {axis별 수렴 — 색/geometry/glyph/connector/폰트, loop N회, 잔차 = 원본복제-only / open question}
**Total time**: ~{minutes}

**개선 사항**: {이번 사이클에서 발견된 새 패턴 또는 정정된 자리 요약 3-5 줄}
**남은 open question**: {Phase 3 의 미해소 모순 / Phase 4 의 0.3 quarantine 이관 자리}
```
