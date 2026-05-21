# §presentation — PPT 슬라이드 markdown

> autopilot-draft `--mode presentation` 의 본문 구조 + 강제 룰. `common.md` (§Common) 의 룰도 모두 적용.
>
> 적용 범위 — 학회 발표 / 세미나 / 강의 / cheatsheet variant (기존 PPT 본문 일부 보강). full deck + cheatsheet variant 모두.
>
> **출처**: 2026-05-21 이전 단독 파일 `PRESENTATION_FIGURE_CONVENTIONS.md` 폐기 후 본 파일로 흡수 + skill rename `autopilot-doc` → `autopilot-draft` 정합.

Generate a **PPT cheatsheet markdown** — single file, optimized for human reading and slide-by-slide copy/paste into PowerPoint. **NOT a pandoc conversion target**. Avoid pandoc-specific syntax (`::: notes`, `:::: {.columns}`, YAML frontmatter for auto-title generation).

## §presentation-0. 슬라이드 분량 제한 (강제, 16:9 기준)

PPT 슬라이드 한 장의 텍스트 분량은 엄격히 제한 — 매 페이지 자가 검사 ("이게 슬라이드 한 장에 들어가는가") 필수:

- bullet **최대 5~6 줄**
- 한 줄 **1~2 키워드** (대략 10 단어 이하, 풀 문장 지양)
- **그림 / 표가 슬라이드 면적의 ≥ 60%** 차지
- 표는 행 ≤ 6, 열 ≤ 5 정도 — 그보다 크면 별도 슬라이드 분리

> **16:9 공간은 생각보다 작음**. cheatsheet markdown 본문도 동일 기준 — 한 페이지의 bullet 수와 길이가 PPT 슬라이드 한 장 분량을 넘으면 안 됨. 긴 설명·수치 정당화·detail 은 **발표자 노트 / backup 슬라이드** 로 분리. draft 작성 시 매 페이지마다 자가 검사 필수.

## §presentation-1. Figure 안 텍스트 최소화

긴 suptitle / subplot title 금지. 짧은 token 라벨 박스만 사용. 수치·해석은 figure 가 아닌 draft 본문 표로. caption 은 한 줄 — figure 가 무엇을 보여주는지만. informal / conversational 단어 금지 (administrative neutral 톤).

## §presentation-2. 비교 plot 의 공통 scale

비교군 전체의 공통 peak 를 기준 (0) 으로 정규화 후 동일 scale 적용. 각 panel 자체 normalize 는 절대 진폭 비교가 깨지고, absolute scale 만 쓰면 약한 신호가 안 보임. dynamic range 는 데이터 분포에 맞춰 좁힘.

## §presentation-3. 시계열 plot 의 window / y-limit

dense window + overlap 으로 trajectory 와 spike 양쪽 가시성 확보. y-axis 는 percentile 기반 robust limit 사용 (raw max 금지). 너무 큰 window 는 거칠고 너무 작은 window 는 산만. 비교 panel 간 axis 통일.

## §presentation-4. 청중 친화적 단위 변환

raw engineering 단위 (도구가 내부에서 쓰는 수치) → 청중에게 익숙한 단위 (비율 · 로그스케일 · percentage 등) 로 변환 표기. 두 값 비교 시 절대값 + 상대값 함께. 비전공자 의사결정자가 청중에 포함되면 특히.

## §presentation-5. 기존 deck 톤 미러

cheatsheet variant 의 헤더 양식 / bullet 구조 / 결론 형식은 기존 deck 과 일치. pre-flight 단계에서 기존 deck 텍스트 추출 → 톤 파악 → 새 슬라이드 첫 페이지가 기존 deck 마지막 placeholder 의 자연스러운 연결.

## §presentation-6. Asset 풍부 활용

사용자가 준비한 자료 (sample data, intermediate artifacts 등) 를 다양한 케이스 + multipanel 로 활용. 한두 그림으로 끝내면 발표 자료로서 약함 — 게으른 자료 X.

## §presentation-7. Path 컨벤션

markdown image / link embed 는 draft 위치 기준 상대 경로. absolute path 는 viewer / 환경에 따라 안 보임.

## §presentation-8. 보조 자료 (raw asset) 링크

figure 에 대응되는 원본 raw asset 은 페이지 단위 zip 묶어 제공 + draft 본문에 `[label](path)` 형식 link. 진폭 / 크기가 비교하기 어려운 경우 동일 scalar 정규화로 가독성 확보 (상대 비율 보존).

## §presentation-9. Plot 먼저, draft 나중

plot 생성 → 사용자 검토 제출 → 수정 반영 → 그 후 draft 본문 작성. 본문 먼저 쓰고 잘못된 plot 임베드하면 본문 수치 / 해석도 함께 다시 써야 해서 비용 큼.

## §presentation-10. 적용 범위

본 §presentation 룰은 autopilot-draft presentation mode (full deck / cheatsheet variant) + refine-doc / audit 으로 presentation artifact 수정·점검 시 모두 검사 적용.

## 본문 구조

### Slide Format Conventions (mandatory — derived from user feedback to prevent revision loops)

1. **Chapter visualization in slide headers** — every body slide's heading: `## Slide N — [Ch.N 챕터명] (sub.번호) 슬라이드 제목`. Chapter-transition slides marked with `— 시작` / `— start`. Each slide has a `**챕터**: N. 챕터명 (M장 중 K번째)` meta line below the title.

2. **Visual placeholder must include chapter band** — every body slide's `**시각자료**:` block first line: `- **상단 헤더 띠**: "N. 챕터명"` (per Korean industry-academia format spec). Chapter-transition slides additionally specify "Ch.X와 색상/strength를 다르게 — 챕터 전환 시각 신호".

3. **Concrete visual placeholders** — NO vague terms like "X 카드", "적절한 도식", "comparison chart". Every visual specifies (a) diagram type + (b) component list + (c) layout/color hints. Example: ❌ "학회 위상 카드" → ✅ "NeurIPS/ICLR/ICML 3-row table (h5-index 컬럼 + acceptance-rate 컬럼)".

4. **Table column header clarity** — NO ambiguous headers like "비교 1위" or "vs ours". Use full noun phrases with clear semantic units. If needed, add a 1-line column-meaning footnote above the table.

5. **Foreign-language quote → Korean keyword gloss** (mandatory for non-AI audiences) — every English quote (paper review citation, technical term, model description) gets a Korean appeal-commentary box directly below:
   ```
   > "English quote..."
   > — Source

   📌 **핵심 키워드 — "X"**: 한국어 풀이 1문장 (청중 친화 어필 메시지)
   ```

6. **Speaker notes default = empty** — do NOT auto-fill speaker notes in the initial draft. Wait for explicit user request as a separate post-polish step. Reason: speaker notes drift with slide-content edits; auto-fill wastes regeneration cost during iterative refinement.

7. **No body-bullet ↔ visual redundancy** — the same fact should NOT appear in both body bullets AND visual placeholder. Body bullets = "what the speaker says"; visual = "what the audience sees at-a-glance". If redundant, simplify one of the two.

8. **Slide-number consistency on insertion/deletion** — when inserting/removing/renumbering a slide, update ALL of the following in the same edit pass:
   - (a) All subsequent slide numbers (`Slide N+1`, `Slide N+2`, ...)
   - (b) Contents slide's chapter slide-counts ("Ch.N (M장)")
   - (c) Changelog entry inside the frontmatter `changelog:` array (per `refine-doc` convention — never a top-of-file HTML comment, which breaks markdown preview when frontmatter is present)
   - (d) Time-budget line in the top-of-file guide
   - (e) Cross-references in other slides ("Slide M의 ...")
   - (f) Chapter meta lines ("M장 중 K번째")

### Top-of-file guide (mandatory header before any slides)

```markdown
# {발표 제목} — Seminar Slide Deck

> **사용 가이드**: 본 markdown은 PPT 복사·붙여넣기용 단일 파일이다. 각 슬라이드는 `---`로 분리되어 있으며, 슬라이드 번호·제목·bullet·시각자료·Speaker note 순서로 구성된다.
>
> - **총 슬라이드 수**: **N main + M backup = total**
> - **시간 분배 ({X}분 기준)**: Opening / Ch.0 / Ch.1 / ... 분 단위 명시
> - **청중 baseline**: 한 줄로 청중 특성과 작성 톤 (약어 풀어쓰기 / 직관 비유 / 수식 최소 등)
> - **설계 의도**: 챕터 구성·narrative arc 한 단락
```

### 슬라이드 단위 형식 (모든 main + backup 슬라이드)

```markdown
---

## Slide N — {짧은 슬라이드 제목}

**제목**: {실제 슬라이드에 들어갈 제목 문구 (한국어 또는 본인이 쓰는 발표 언어)}

**부제** (선택): {부제 문구 — 첫 슬라이드 또는 챕터 디바이더에 한정}

- 본문 bullet 1 (개념/이름/수치 위주, 간결하게)
- 본문 bullet 2
- 본문 bullet 3 (보통 3-5개)

| 표가 더 적합한 경우 | 이렇게 markdown 표 |
|---|---|
| 모델 A | 수치 |
| 모델 B | 수치 |

**시각자료**:
- 좌측 1/2 (또는 메인): {도식·차트 설명}
- 우측 1/2 (또는 보조): {보조 시각}
- 또는 전체 화면: {풀 페이지 도식 설명}

<!-- 자동 figure embed (Step 4.0a/4.0b 결과 figure_index.md 매핑이 있는 슬라이드만) -->
<!-- Source 1 (research): <img src="../../../research/{topic}/figures/{paper_id}_fig{N}.png" alt="..." width="500" /> -->
<!-- Source 2 (analysis paper): <img src="../../../analysis_project/paper/figures/{paper_id}_fig{N}.png" alt="..." width="500" /> -->
<!-- Source 3 (artifact self): <img src="../assets/figures/slideXX_*.png" alt="..." width="500" /> -->
<!-- 작은 크기 (width=500) 미리보기 수준; 사용자 메모리 정책 — feedback_figure_combined_pptx_only.md 참조 -->
<!-- Path은 draft 위치 기준 자동 계산 (Step 4.0c Path Convention) — 사용자 수동 X -->
{자동 embed: 사용 가능 figure 목록 (figure_index.md 매핑) 중 본 슬라이드 토픽과 매치되는 figure가 있으면 inline `<img width="500" />` syntax로 자동 embed. 자동 매핑이 모호하면 placeholder만 두고 사용자 polish 영역으로 표시.}

**Speaker note**:
1. {발화 1 — 슬라이드 본문 보충, 직관 풀이, 비유, 일화}
2. {발화 2 — 다음 슬라이드/챕터로 가는 transition}
3. {발화 3 — 청중 질문 예상 시 짧은 답변 메모, 선택}

**Citation** (선택): [Author Year, Venue](cards/{file}.md) — 정확한 paper card를 가리키는 인라인 링크
```

### 구조 요건

- **표지** (Slide 1) — 제목 + 부제 + 발표자/소속 + 날짜 + 발표 자료 출처 한 줄
- **목차** (Slide 2) — 챕터별 슬라이드 수와 한 줄 설명
- **챕터 디바이더** — `## Slide N — Ch.X 제목` 형식. 슬라이드 본문은 챕터 의도/시기 한두 줄. 별도 슬라이드 카운트에 포함.
- **본문 슬라이드** — 위 슬라이드 단위 형식
- **챕터 마무리** (선택) — Ch.X 정리 + Ch.X+1 transition. 인지 부담 분산용
- **Conclusion** — Take-home 5 / Open Problems / 한 페이지 요약 / Q&A / Thank you
- **Backup** — `## Slide BN — Backup: 제목` 형식. 메인 흐름 끝난 뒤 배치
- **References** (선택) — 마지막에 핵심 인용 정리

### 작성 톤

- 본문 bullet은 *키워드 + 수치 + 모델명* 위주. 풀 문장 지양 (그건 speaker note에).
- 약어는 첫 등장 시 풀어쓰기: `Speech Enhancement (SE)`, `NFE (Number of Function Evaluations)` 등.
- Citation은 paper card markdown 링크로 (`[Author Year](../../research/{topic}/cards/{file}.md)` 또는 같은 artifact_dir 내 cards/).

### Quality

- 모든 본문 슬라이드에 **Speaker note 필수** (≥80% — 기술 비중 낮은 표지·인사 슬라이드 제외).
- 모든 슬라이드에 시각자료 placeholder (텍스트만으로 끝나는 슬라이드는 cheatsheet로서 약함).
- 시각자료 설명은 *PPT에서 그릴 수 있을 만큼 구체적*으로 (예: "5-stage timeline 가로 막대, 색상 5개" 같은 수준).
- Strategy doc의 슬라이드 outline을 그대로 매핑 (총 슬라이드 수와 챕터 시간 분배 일치).
