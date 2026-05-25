# §presentation — PPT 슬라이드 markdown

> autopilot-draft `--mode presentation` 의 본문 구조 + 강제 룰. `common.md` (§Common) 의 룰도 모두 적용.
>
> 적용 범위 — 학회 발표 / 세미나 / 강의 / cheatsheet variant (기존 PPT 본문 일부 보강). full deck + cheatsheet variant 모두.

본 skill 의 산출은 **PPT cheatsheet markdown** — 사용자가 PowerPoint 로 직접 옮기는 _slide-by-slide copy/paste 용 단일 파일_. pandoc 자동 변환 대상 아님 (`::: notes`, `:::: {.columns}`, YAML frontmatter for auto-title generation 같은 pandoc 전용 syntax 회피).

## §presentation-0. 슬라이드 분량 제한 (강제, 16:9 기준)

PPT 슬라이드 한 장의 텍스트 분량은 엄격히 제한 — 매 페이지 자가 검사 ("이게 슬라이드 한 장에 들어가는가") 필수:

- bullet **최대 5~6 줄**
- 한 줄 **1~2 키워드** (대략 10 단어 이하, 풀 문장 지양)
- **그림 / 표가 슬라이드 면적의 ≥ 60%** 차지
- 표는 행 ≤ 6, 열 ≤ 5 정도 — 그보다 크면 별도 슬라이드 분리

> **16:9 공간은 생각보다 작음**. cheatsheet markdown 본문도 동일 기준 — 한 페이지의 bullet 수와 길이가 PPT 슬라이드 한 장 분량을 넘으면 안 됨. 긴 설명·수치 정당화·detail 은 **발표자 노트 / backup 슬라이드** 로 분리.

## §presentation-1. Figure 안 텍스트 최소화

긴 suptitle / subplot title 금지. 짧은 token 라벨만. 수치·해석은 figure 가 아닌 draft 본문 표로. caption 은 한 줄 (figure 가 무엇을 보여주는지만). informal / conversational 단어 금지 — neutral 톤.

## §presentation-2. 비교 plot 의 공통 axis / scale

비교군 전체에 동일 axis 와 scale 적용. 각 panel 자체로만 normalize 하면 비교군 간 절대 차이가 안 보임. dynamic range 는 데이터 분포에 맞춰 설정.

## §presentation-3. Axis 범위는 robust statistics

축의 min / max 를 raw extreme value 로 잡지 X (outlier 한 점이 가시성 깸). percentile 기반 robust limit 사용. 비교 panel 간 axis 통일.

## §presentation-4. 청중 친화 단위 변환

raw engineering 단위 (도구가 내부에서 쓰는 수치) → 청중에게 익숙한 단위 (비율 · 로그스케일 · percentage 등) 로 변환. 두 값 비교 시 절대값 + 상대값 함께. 비전공자 청중 포함 시 특히.

## §presentation-5. 기존 deck 톤 mirror

cheatsheet variant 의 헤더 양식 / bullet 구조 / 결론 형식은 기존 deck 과 일치. pre-flight 단계에서 기존 deck 텍스트 추출 → 톤 파악 → 새 슬라이드 첫 페이지가 기존 deck 마지막 페이지와 자연스럽게 이어짐.

## §presentation-6. Asset 풍부 활용

사용자가 준비한 자료 (sample data, intermediate artifacts 등) 를 다양한 case + multipanel 로 활용. 한두 그림으로 끝내면 발표 자료로서 약함.

## §presentation-7. 보조 raw asset 링크

figure 에 대응되는 원본 raw asset (source data / wav / video / dataset / 등) 은 page 단위 zip 또는 cloud link 로 묶어 제공 + draft 본문에 `[label](path)` 형식 link.

## §presentation-8. Plot 먼저, draft 나중

plot 생성 → 사용자 검토 → 수정 반영 → 그 후 draft 본문 작성. 본문 먼저 쓰고 잘못된 plot 임베드하면 본문 수치 / 해석도 함께 다시 써야 해서 비용 큼.

## §presentation-9. 적용 범위

본 §presentation 룰은 autopilot-draft `--mode presentation` (full deck / cheatsheet variant) + draft-refine / audit 으로 presentation artifact 수정·점검 시 모두 검사 적용.

## 본문 구조

### Slide Format Conventions (mandatory)

1. **Chapter 시각화 in slide header** — body 슬라이드 heading: `## Slide N — [Ch.N 챕터명] (sub.번호) 슬라이드 제목`. chapter-transition 슬라이드는 `— 시작` / `— start` 표시. 각 슬라이드에 `**챕터**: N. 챕터명 (M장 중 K번째)` meta 라인.

2. **Visual placeholder 의 chapter band** — body 슬라이드 `**시각자료**:` block 첫 줄: `- **상단 헤더 띠**: "N. 챕터명"`. chapter-transition 슬라이드는 추가로 "Ch.X 와 색상/strength 다르게 — 챕터 전환 시각 신호" 명시.

3. **Concrete visual placeholder** — vague 표현 (예: "X 카드", "적절한 도식", "comparison chart") 금지. 모든 visual 은 (a) diagram type + (b) component list + (c) layout / color hint 명시. 예시: ❌ "학회 위상 카드" → ✅ "NeurIPS / ICLR / ICML 3-row table (h5-index 컬럼 + acceptance-rate 컬럼)".

4. **Table column header 명확성** — ambiguous header (예: "비교 1위", "vs ours") 금지. full noun phrase + clear semantic unit 사용. 필요하면 column 의미 1-line footnote 표 위에 추가.

5. **외국어 quote → 한국어 keyword gloss** (비AI 청중 필수) — 본문 안 영어 quote (paper review citation / 기술 용어 / 모델 설명) 마다 그 아래에 한국어 어필 commentary box:
   ```
   > "English quote..."
   > — Source

   📌 **핵심 키워드 — "X"**: 한국어 풀이 1문장 (청중 친화 어필 메시지)
   ```

6. **Speaker note default = empty** — 초기 draft 에 speaker note 자동 채우지 X. 사용자 명시 요청 시 별도 post-polish step 으로. 이유: speaker note 가 슬라이드 내용 편집에 drift, 자동 채우기는 iterative refinement 중 regeneration cost 낭비.

7. **body bullet ↔ visual 중복 회피** — 동일 fact 가 body bullet + visual placeholder 양쪽 등장 X. body bullet = 발표자 발화, visual = 청중이 한눈에 보는 것. 중복이면 둘 중 하나 단순화.

8. **슬라이드 번호 정합성** (삽입 / 삭제 / 번호 변경 시 같은 edit pass 안에 모두 갱신):
   - (a) 이후 모든 슬라이드 번호 (`Slide N+1`, `Slide N+2`, ...)
   - (b) 목차 슬라이드의 chapter slide-count ("Ch.N (M장)")
   - (c) Changelog entry in frontmatter `changelog:` array (per `draft-refine` 컨벤션 — top-of-file HTML comment 금지, frontmatter 와 같이 있으면 markdown preview 깨짐)
   - (d) Top-of-file guide 의 time-budget 라인
   - (e) 다른 슬라이드의 cross-reference ("Slide M 의 ...")
   - (f) Chapter meta 라인 ("M장 중 K번째")

### Top-of-file guide (모든 슬라이드 앞 mandatory header)

```markdown
# {발표 제목} — Seminar Slide Deck

> **사용 가이드**: 본 markdown 은 PPT 복사·붙여넣기용 단일 파일. 각 슬라이드는 `---` 로 분리되어 있으며, 슬라이드 번호 · 제목 · bullet · 시각자료 · Speaker note 순서로 구성.
>
> - **총 슬라이드 수**: **N main + M backup = total**
> - **시간 분배 ({X} 분 기준)**: Opening / Ch.0 / Ch.1 / ... 분 단위 명시
> - **청중 baseline**: 한 줄로 청중 특성과 작성 톤 (약어 풀어쓰기 / 직관 비유 / 수식 최소 등)
> - **설계 의도**: 챕터 구성·narrative arc 한 단락
```

### 슬라이드 단위 형식 (모든 main + backup 슬라이드)

```markdown
---

## Slide N — {짧은 슬라이드 제목}

**제목**: {실제 슬라이드에 들어갈 제목 (한국어 또는 발표 언어)}

**부제** (선택): {부제 — 첫 슬라이드 또는 챕터 디바이더에 한정}

- 본문 bullet 1 (개념 / 이름 / 수치 위주, 간결)
- 본문 bullet 2
- 본문 bullet 3 (보통 3~5 개)

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
{자동 embed: 사용 가능 figure (figure_index.md 매핑) 중 본 슬라이드 토픽과 매치되는 figure 가 있으면 inline `<img width="500" />` 로 자동 embed. 매핑이 모호하면 placeholder 만 두고 사용자 polish 영역으로 표시.}

**Speaker note**:
1. {발화 1 — 슬라이드 본문 보충, 직관 풀이, 비유, 일화}
2. {발화 2 — 다음 슬라이드 / 챕터 transition}
3. {발화 3 — 청중 질문 예상 시 짧은 답변 메모, 선택}

**Citation** (선택): [Author Year, Venue](cards/{file}.md) — 정확한 paper card 가리키는 inline link
```

### 구조 요건

- **표지** (Slide 1) — 제목 + 부제 + 발표자 / 소속 + 날짜 + 발표 자료 출처 한 줄
- **목차** (Slide 2) — 챕터별 슬라이드 수 + 한 줄 설명
- **챕터 디바이더** — `## Slide N — Ch.X 제목` 형식. 본문은 챕터 의도 / 시기 한두 줄. 슬라이드 카운트에 포함.
- **본문 슬라이드** — 위 슬라이드 단위 형식
- **챕터 마무리** (선택) — Ch.X 정리 + Ch.X+1 transition. 인지 부담 분산용.
- **Conclusion** — Take-home 5 / Open Problems / 한 페이지 요약 / Q&A / Thank you
- **Backup** — `## Slide BN — Backup: 제목` 형식. main 흐름 끝난 뒤 배치.
- **References** (선택) — 마지막에 핵심 인용 정리

### 작성 톤

- body bullet 은 _키워드 + 수치 + 모델명_ 위주. 풀 문장 지양 (그건 speaker note 에).
- 약어는 첫 등장 시 풀어쓰기, 이후 약어.
- Citation 은 paper card markdown link 로 (`[Author Year](../../research/{topic}/cards/{file}.md)` 또는 같은 artifact_dir 내 `cards/`).

### Quality

- 모든 body 슬라이드에 **Speaker note 필수** (≥ 80% — 기술 비중 낮은 표지 / 인사 슬라이드 제외).
- 모든 슬라이드에 시각자료 placeholder (텍스트만으로 끝나는 슬라이드는 cheatsheet 로서 약함).
- 시각자료 설명은 _PPT 에서 그릴 수 있을 만큼 구체적_ 으로 (예: "5-stage timeline 가로 막대, 색상 5개" 수준).
- Strategy 의 슬라이드 outline 그대로 매핑 (총 슬라이드 수 + 챕터 시간 분배 일치).
