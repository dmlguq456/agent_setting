# §paper — LaTeX 학술 본문

> autopilot-draft `--mode paper` 의 본문 구조 + 강제 룰. `common.md` (§Common) 의 룰도 모두 적용.
>
> 적용 범위 — 학술 논문 (initial submission / camera-ready / major revision) / thesis / book chapter / LaTeX 기반 paste-ready cheatsheet.

## 본문 구조

- Frontmatter — type · venue · status: draft · date
- 본문 outline (section 별 draft):
  - **Abstract** — background → gap → method → results → impact 순서
  - **Introduction** — hook → context → gap → contribution → outline
  - **Related Work** — strategy 의 framing 에 맞춰 구성
  - **Method** — strategy outline 따라 작성, equation 은 placeholder
  - **Experiments** — setup → results → ablation 순, table 은 skeleton
  - **Conclusion**
- Figure / table placeholder + caption

## Camera-ready / major-revision 한정 — Natural-integration rule for paper-body mutations

(cross-ref: `draft-strategy/SKILL.md` paper mode "Natural-integration rule" — single source of truth)

> **reviewer 의견 / rebuttal 자료 → paper-body mutation paste-ready block 으로 옮길 때** mutation 마다 한 질문: _"1~2 문장 in-line rewrite 로 surrounding paragraph 흐름에 자연스럽게 녹일 수 있나?"_
> - **YES → inline rewrite mutation** — subsection head opening + body paragraph touch-up + Figure cascade reference. 실험 수치는 body / Appendix 에 두고 opening / intro 에는 박지 X
> - **NO → drop 또는 Appendix 로 미룸** — rebuttal-format 산출물 (model-by-model 비교 표 / 구조화 Q&A block / point-by-point 응답 paragraph) 은 reviewer 가 "통합 강하게 권장" 해도 paper-body mutation 으로 부적합. verbatim paste 시 rebuttal 톤이 본문 흐름 깸

**Hard-fail 거부 신호** — paste-ready block 이 다음 셋 중 하나라도 해당하면 mutation entry 작성 거부:
- (a) rebuttal 출처 standalone `\begin{table}` / `\begin{itemize}` 통째 paste
- (b) opening / framing paragraph 에 experimental 수치 verbatim 박기
- (c) 별도 `\paragraph{...}` INSERT 인데 surrounding text 와 bridge 안 됨

**Why**: 2026-05-19 camera-ready cycle 에서 reviewer 의견을 mechanically 🔴 mandatory body mutation 으로 변환한 incident (rebuttal-format 비교 표 포함). 사용자 거부 패턴: _"rebuttal 자료를 본문에 그대로 가져다 붙이지 말고 자연스럽게 문장으로 녹여 넣어라."_

## Paste-ready cheatsheet 형식 강제 (paper mode camera-ready / paste-ready subtype)

> **언제 적용되는가**: paper mode 의 산출물이 _연속 본문 paragraph 가 아니라 사용자가 LaTeX 에 직접 paste 하는 _카드 묶음__ 일 때 (camera-ready / major revision / `subtype: camera-ready-paste-ready` 같은 frontmatter). 즉 사용자가 _preview 로 보면서_ 카드 단위로 paste 작업하는 산출물.

본 형식은 **사용자가 preview 에서 보는 것** 과 **에이전트 추적용 메타** 를 _명확히 분리_ 한다. 사용자가 한 사이클에 한 번 보면 끝나는 정보가 매 entry 옆에 박혀 있으면 preview 가 줄글로 깨지고 paste 자리를 찾기 어려워진다. 사용자 불만 (2026-05-21): _"preview 에서 그냥 쭉 줄글로 깨진다 — 형식 자체 문제다"_.

**1. Frontmatter 는 최소만**

`draft.md` / `draft_ko.md` 의 frontmatter 에는 **사용자에게 의미 있는 필드만**:
- `type`, `venue`, `paper_id`, `status`, `date`, `baseline` (LaTeX 파일 경로)

**금지 (추적용은 별도 파일로)**:
- `changelog:` 배열 → `_internal/draft_meta.yaml` 또는 `pipeline_summary.md` 으로 격리
- `mutation_count`, `intentional_id_gaps`, `predecessor`, `strategy_ref`, `qa_level`, `subtype`, `scope` 같은 추적용 → 같은 격리 파일로
- frontmatter 안 긴 `note` 줄 (변경 이력) → frontmatter 밖 평문으로 또는 격리 파일로

이유: YAML frontmatter 가 길면 preview 에서 줄글로 깨져 사용자가 본문 첫 줄까지 도달하는 데 한 화면을 소비한다.

**2. 문서 정체성 — H1 제목 + 한 단락 개요 + Legend blockquote 1개**

사용자가 문서를 처음 열었을 때 _이게 무엇인지_ 한 화면에서 인지할 수 있도록:

- **H1 제목 1줄** — 예: `# TF-Restormer Camera-Ready Cheatsheet v3 — Appendix + Conclusion`
- **한 단락 개요 (2-4문장)** — 본 cheatsheet 가 다루는 범위 / 산출 entries 수 / paste 작업 흐름 한 줄 안내. 추적용 메타 (changelog / mutation 분포 통계) 는 박지 않음 — _문서 정체성_ 만.
- **Legend blockquote 1줄** — `> **Legend**: 🔴 mandatory · 🟡 high · 🟢 optional · ✅ already applied · audit link inline`

여기까지가 _문서 첫 화면_ 의 사용자 영역. "사용 방식" / "Strategy details" / "Wording invariants" / "Preserve note" 같은 _추가 안내 blockquote 는 박지 않는다_ — 사이클이 끝나면 의미 없는 메타.

**3. 각 entry 는 _카드 단위_**

한 entry 의 골격:

```markdown
### {ID} {tier 이모지} — {짧은 한 줄 action}

- [ ] 📌📌📌📌📌 **반영 완료** 📌📌📌📌📌

**위치**: `\section{...}` 또는 `\label{...}` 또는 `\paragraph{...}` (한 줄, inline code 활용)

​```latex
% paste-ready 블록
...
​```

**한 줄 이유** (선택): 왜 이 자리에 이게 필요한지 한 문장. 두 줄 넘어가면 cut.
```

- H3 헤더 한 줄 + _바로 아래 task-list 체크박스 한 줄 의무_. cheatsheet 가 사용자의 최종 paste 작업을 위한 자료라, 진행 중에 어디까지 반영했는지 추적할 수 있게 entry 첫 자리에 체크박스 anchor 가 박혀야 함. 형식은 `- [ ] 📌📌📌📌📌 **반영 완료** 📌📌📌📌📌` 한 줄 고정 — `- [ ]` markdown task-list 가 preview 에서 interactive 체크박스로 렌더링, 좌우 📌 다섯 개씩이 시각 anchor (H3 tier 이모지 🔴🟡🟢 와 역할 분리), bold 라벨이 강조. 사용자가 반영 완료한 항목은 직접 `[x]` 로 갈아 끼움.
- `**위치**:` 한 줄 — `**Anchor**` / `**latex anchor**` 같은 영어 라벨 금지, `**위치**:` 통일
- LaTeX 블록 한 개 (필요 시 함께 paste 할 짧은 블록 하나 더)
- `**한 줄 이유**` 선택, 두 줄 이내

**4. entry 안 절대 박지 않는 것**

- Reviewer 매핑 (`Reviewer: cytr-W3`) → `_internal/draft_meta.md`
- dependency 표 / cross-ref dependency 표 → `_internal/draft_meta.md`
- Wording invariant 안내 / Style Guide 인용 → 본문 맨 앞에 한 줄 또는 격리 파일
- Verification gate / column count 안내 → 본문 끝의 _마무리 확인 목록_ 안 한 줄로 통합
- inline `<!-- memo: [REFINE-R2] F{N} applied: ... -->` 표시 → 본문에 절대 박지 않음. refine 추적은 `pipeline_summary.md` `## 마이너 변경 로그` 안에만.

**5. paste 순서는 본문 끝에 단순 ordered list**

- 표 (`| 단계 | mutation | 위치 |`) 가 아니라 ordered list (`1. M34: ...` / `2. M37 Step 1: ...`)
- 각 단계는 한 줄 — mutation ID + 한 줄짜리 action. 의존성은 본문 entry 안 `**위치**:` 옆에 inline 으로 한 줄 (`함께 paste: M{X}`) — 별도 표 X.

**6. 사용자 결정 분기점은 _발생 entry 안 한 줄_**

Pre-flight 표 / 분기점 표로 앞 페이지에 7행 표 박지 않는다. M2 위치 분기는 M2 entry 안에 한 줄 (`> 위치 선택: (a) §1 끝 / (b) §Acknowledgements 옆 — spec 기준 (a) 권장`), M27-Step3 BibTeX 부재 분기는 M27 entry 안에 한 줄. _발생 자리에서 한 번_.

**7. body audit 진단표는 한 번 보고 끝 — 본문에 박지 않음**

본문 적용 현황 (`§A Applied 16건 / Intentional 5건 / 잔존 2건`) 표 는 사용자가 _작업 시작 전 한 번_ 보고 끝나는 reference. 본문 카드 흐름 안에 박지 말고 `_internal/body_audit.md` 또는 `analysis/` 안 별도 파일로. 본문에는 한 줄 link 만 (`> 본문 적용 현황: [audit.md](./audit.md) 참조`).

**8. 마무리 확인 목록은 본문 맨 끝 한 묶음**

`§F final verification checklist` 는 한 곳에. 각 entry 마다 verification gate 박지 않고 마지막에 한 번에 모음.

**9. 추적 정보는 `_internal/draft_meta.md` 으로 격리**

사이클 중 추적용 메타:
- 변경 이력 (changelog 배열 본문)
- mutation 별 Reviewer 매핑 + dependency 표 + Wording note
- inline refine marker (`[REFINE-R2] F{N} applied`)
- mutation_count / tier 통계

이 모두 `_internal/draft_meta.md` 안. 사용자 영역 (`draft.md` / `draft_ko.md`) 에는 절대 안 박는다.

**10. 가독성 우선 — 무엇을 하지 말라보다 무엇을 _적극적으로_ 할 것인지**

위 1-9 가 _antipattern 차단_ 규칙이라면, 본 항목은 _positive 가독성 원칙_. 사용자 한 줄 (2026-05-21): _"뭐가 됐든 사용자 가독성을 고려해야 한다."_

- **개요·이유·안내 문장은 줄바꿈 적극.** 한 단락이 4-5 문장 이상 되면 무조건 쪼갬 — 의미 단위마다 빈 줄 또는 `- bullet` 으로 분할. preview 에서는 _공백 줄이 호흡_. 한 단락이 6 줄 넘어가면 사용자 시선이 _문장 단위_ 가 아니라 _덩어리_ 로 흘러 정보 단위가 안 보임.
- **위치 한 줄도 자연스럽게 끊김.** `**위치**:` 라인이 30자 넘으면 _두 줄_ 로 쪼개기 OK — `**위치**:` 한 줄 + `**함께 paste**:` 한 줄.
- **bullet 적극 활용.** 분기점·조건·옵션 같이 _병렬 정보_ 는 줄글 대신 bullet 으로 — 사용자가 한 눈에 옵션 수를 카운트할 수 있게.
- **공백 줄로 호흡.** entry 사이 공백 줄 1개, 큰 섹션 사이 2개. preview 에서 공백 줄이 시각적 _장면 전환_.
- **짧은 문장.** 한 문장이 30자 넘으면 _자르거나_ bullet 으로 분해. 한자어·외래어 잡탕 긴 문장은 한국어 자연 표현으로 풀어 씀 (판교체 회피 — CLAUDE.md §1 참조).
- **시각 anchor 가 도움 되는 자리에만 표/박스.** 두세 줄짜리 정보를 6칸 표로 만들어 _과잉 구조화_ 하지 않음 — preview 에서 표는 _진짜 비교가 필요한_ 자리에만.

이 항목은 _자가 점검_ 으로 작동 — draft 작성 후 _첫 화면을 사용자 입장에서 한 호흡으로 읽어보고_, 한 덩어리로 흐르는 문단이 있거나 시선이 막히는 자리가 있으면 _즉시 쪼갬_.

**Hard-fail 추가** — 사용자 영역 draft 본문에 다음이 등장하면 즉시 거부 + 재작성:
- frontmatter 줄 수 > 7 (필수 6 필드 + `---` 두 줄)
- 본문 첫 화면에 **H1 제목 또는 한 단락 개요 부재** (사용자가 _이게 무엇인지_ 인지 못 하는 상태)
- 본문 맨 앞 안내 blockquote (Legend 외) 2 개 이상
- 한 entry 안 markdown 표 (paste-ready LaTeX 안의 `\begin{tabular}` 는 OK — markdown `|...|` 표 만 hard-fail)
- 본문 안 inline `<!-- memo: ... -->` marker 등장
- ordered list 아니라 _표 형태_ 의 paste 순서 안내

**Why**: 사용자가 preview 로 보면서 paste 작업한다. preview 에서는 frontmatter / blockquote / 메타 표 가 줄글로 깨져 _paste 자리를 찾기 어렵다_. 사용자 영역과 추적 영역이 같은 위계로 섞이면 매번 사용자가 "이게 내가 봐야 할 건가, 에이전트 추적용인가" 분간해야 한다 — 짜증의 직접 원인.

## Figure 자산 게이트 — 자료팀 위임 (2026-05-22 신설)

paste-ready cheatsheet 안 `\includegraphics{<path>}` 참조 PDF 가 `<paper_dir>/<path>` 에 없을 때, _자산 누락_ 을 사용자가 paste 단계에서야 발견하지 않도록 cheatsheet 작성 자리에서 미리 처리.

**사전 자산 점검** — Step 4 (draft 작성) 직후 / Step 5 (review) 직전 자동:

1. cheatsheet 본문에서 `\includegraphics{...}` 인자 모두 추출.
2. 각 경로에 대해 `<paper_dir>/<path>` 존재 여부 확인.
3. 부재 자산 발견 시 두 경로 중 하나:

**경로 A — `--figures auto` (default)**

`Agent(자료팀, "<자산 spec>")` 자동 위임. spec 은 cheatsheet 의 figure caption + 주변 본문에서 추출 — 함수 / 축 / curve 목록 / 목표 사이즈 / 학회 기본 스타일. 자료팀이 PDF + 스크립트 + preview PNG 생성 후 entry 의 _알아둘 점_ 자동 갱신 (`figure 자산 생성 완료: <path>, 재현 스크립트 <script path>`).

**경로 B — `--figures flag`**

부재 자산만 _알아둘 점_ 에 flag 박고 사용자 직접 처리에 맡김. spec 은 자세하게 (curve 별 함수·축·사이즈 권장 포함). 사용자가 그 spec 으로 직접 만들거나 별도 `Agent(자료팀)` 호출 가능.

**왜 자료팀에 위임하나**: cheatsheet 의 LaTeX 본문은 _paste-ready_ 가 본질이지 _자산 생성_ 책임은 아니다. 자료팀이 학회·논문 기본 스타일 (Times serif / OrRd palette / 6.4×2.8" landscape 등) 의 단일 source 라 figure 들 사이 _스타일 일관성_ 도 한 자리에서 누적된다.

**자산 위치 컨벤션** (자료팀 default 와 정합):
- PDF: `<paper_dir>/figures/<name>.pdf`
- 재현 스크립트: `<paper_dir>/figures/plot_<name>.py`
- preview PNG: `<paper_dir>/figures/<name>_preview.png`

cheatsheet entry 안 _figure preview_ 임베드는 preview PNG 상대 경로로 — 사용자가 markdown preview 띄울 때 자동 표시. (예시: `![Figure description](../../../../<paper_dir>/figures/<name>_preview.png)`)
