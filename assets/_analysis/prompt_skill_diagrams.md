# Prompt — Skill / 워크플로우 시각화 작업

> 다음 세션에서 그대로 던지면 자료팀 → 디자인팀 sequential 흐름이 진행됨. 사용자 컨펌 없이 한 흐름 (옵션 B).

---

## 사용자 명시 의도

`~/.claude/README.md` 의 mermaid 다이어그램 3 개 (트랙 / 호출 그래프 / 산출물 I/O) 를 **시각적으로 잘 이해할 수 있는 SVG 그림** 으로 다시 만든다.

- 형태는 mermaid 형식에 얽매이지 않아도 됨 (한 장 큰 그림 / 도메인별 N 장 / 호출 흐름 / 산출물 I/O 등 자유)
- 현재 README 의 그림 3 개는 **참고만** — 선입견 회피
- 두 단계: (1) 자료팀 분석 → (2) 디자인팀 SVG 작성
- 산출 위치: `~/.claude/assets/diagrams/`

---

## 단계 1 — 자료팀 호출

**Agent**: `자료팀` (= `material-team`, opus). 만약 invoke list 부재 시 `general-purpose` 로 우회하면서 prompt 안에 _자료팀 정신_ 명시.

**Prompt**:

```
~/.claude/ 의 skill / agent / 워크플로우를 직접 read·분석한 뒤,
시각적으로 잘 이해할 수 있는 다이어그램 가이드를 작성해 주세요.

**중요 — 선입견 회피**: 현재 `~/.claude/README.md` 의 mermaid 다이어그램 3 개
(트랙 / 호출 그래프 / 산출물 I/O) 는 **참고만** 하고 그 구조에 끌려가지 마세요.
새로 본 데이터로 더 나은 묶음·시각 메타포가 있으면 그쪽 선택.

**분석 대상**:
1. `~/.claude/skills/*/SKILL.md` (29 자료) — frontmatter (description / argument-hint /
   tools / model) + 본문 일부 (Pipeline / Procedure / Default Invocation Rule /
   산출물 위치)
2. `~/.claude/agents/*.md` (8 자료 — 자료팀 / 디자인팀 / 연구팀 / 편집팀 / 기획팀 /
   개발팀 / 품질관리팀 / codex-review-team) — description / tools / model / 호출 패턴
3. `~/.claude/CLAUDE.md` §6 (autopilot-* 호출 패턴 / Pre-check 발화 분류)
4. `~/.claude/CONVENTIONS.md` §5 (산출물 폴더 컨벤션 3-tier) + §2 (agent model)
5. `~/.claude/WORKFLOW.md` (있으면)
6. `~/.claude/user_profile/01_paper_figure_style.md` (시각 default — 사용자 figure 성향)

**분석 차원** (각 차원의 묶음·관계 정리):
- **도메인 트랙** — 코드 / 문서 / 연구 / 실험 / 디자인 / 앱 / 사용자 분석 /
  점검 / 정정 — 각 트랙의 entry skill 과 흐름
- **skill 사이 데이터 전달** — analyze-project → autopilot-* /
  autopilot-research → autopilot-code · draft / autopilot-spec → autopilot-design ·
  code · ship 등 입출력 관계
- **sub-skill 위계** — autopilot-code 가 init-plan / refine-plan / execute-plan /
  run-test / final-report 자동 호출, autopilot-draft 가 init-doc-strategy /
  refine-doc 호출 등
- **agent 호출 관계** — 각 skill 이 어느 agent 를 부르는지
- **산출물 흐름** — `.claude_reports/{plans,documents,research,specs,
  analysis_project,designs}/` 위치별 데이터 누적
- **자연어 발화 분류** — ceremony 큰 6 + 작은 3 + sub-skill 발화 + 직접 처리 4 갈래
- **QA gate** — 5 level (quick/light/standard/thorough/adversarial) × skill 분포

**산출**: `/home/Uihyeop/.claude/assets/_analysis/skill_graph.md`

본문 구조:
- §1. Skill 카탈로그 (29 자료 표 — name / category / input / output /
  calls sub-skill·agent)
- §2. 도메인 트랙 정리
- §3. 자연어 발화 → invoke 분류 (4 갈래)
- §4. 산출물 흐름 (.claude_reports 관점)
- §5. agent 호출 매트릭스
- §6. QA gate 분포
- §7. **시각화 가이드** (디자인팀에게 전달)
  - 추천 다이어그램 개수·구성 (예: 1 큰 그림 / 도메인별 N 장 / 호출 흐름 /
    산출물 I/O)
  - 각 다이어그램의 노드·엣지·묶음 설계 (구체)
  - 시각 메타포 추천 (예: track = 수영 레인, skill = 둥근 사각형,
    agent = 원, 산출물 = 폴더 아이콘 등)
  - 사용자 figure 성향 (01_paper_figure_style.md v2.5) 자체 read 후 default 반영:
    - architecture diagram outline grayscale (TF-Restormer Fig.1 anchor)
    - 색 cool/warm 분리 (encoder 녹색 #3F8C5C · decoder 주황 · ours 강조
      빨강 #A0152A)
    - Times-equivalent serif 폰트
    - block: rounded rectangle / arrow solid 1.5pt
  - 다이어그램별 _기대 인사이트_ (이 그림을 본 사용자가 무엇을 이해하길 바라는가)

평어 단정형, 표·불릿. 디자인팀이 SVG 만들 때 추가 질문 안 해도 될 수준으로 구체.
```

---

## 단계 2 — 디자인팀 호출 (자료팀 완료 직후)

**Agent**: `디자인팀` (= `design-team`, opus 승격됨). invoke list 부재 시 `general-purpose` 우회.

**Prompt**:

```
자료팀의 분석 결과를 바탕으로 SVG 다이어그램 생성.

**Read 의무**:
1. `/home/Uihyeop/.claude/assets/_analysis/skill_graph.md` (자료팀 분석 결과 —
   §7 시각화 가이드 1순위 따름)
2. `/home/Uihyeop/.claude/user_profile/01_paper_figure_style.md` (사용자 figure
   성향 v2.5 — 색·폰트·layout default)
3. `/home/Uihyeop/.claude/user_profile/05_domain_expertise.md` (도메인 약자 —
   다이어그램 안 약자 표기 시 참조)

**작업**:
- 자료팀 §7 의 추천 다이어그램 개수·구성 그대로 따름
- 각 다이어그램을 SVG 로 작성 — viewBox / 폰트 / 색 hex / arrow marker 모두 명시
- 색 default — 01_figure_style §1 / §3 (encoder 녹색 #3F8C5C / decoder 주황 /
  ours 강조 빨강 #A0152A)
- 폰트 — Times-equivalent serif (e.g. `Times New Roman, Liberation Serif, serif`)
- block — rounded rectangle (rx=6) / outline 1.5pt grayscale / fill light tint
- arrow — solid 1.5pt, marker-end triangle
- 텍스트 — 8-10pt body, 12-14pt heading
- 가독성 1순위 — 노드 간 spacing 충분, label overlap 회피

**산출**:
- `/home/Uihyeop/.claude/assets/diagrams/*.svg` — 자료팀 §7 추천 개수만큼
- `/home/Uihyeop/.claude/assets/diagrams/_README.md` — 각 SVG 의 목적·인사이트
  설명 (사용자가 README.md 에 어느 그림을 어느 자리에 박을지 결정)

**제약**:
- SVG 파일 자체 valid (브라우저에서 열어볼 수 있음)
- 외부 폰트 embed X — system font fallback chain 사용
- 색·텍스트 hardcode (CSS variable X — SVG 자체로 self-contained)
- 한국어 텍스트 OK (Times serif + fallback `Malgun Gothic, Apple SD Gothic Neo`)

평어 단정형 보고. SVG 파일 list + 각 그림의 목적 한 줄씩.
```

---

## 다음 세션 시작 시 던질 메시지

```
~/.claude/assets/_analysis/prompt_skill_diagrams.md 읽고 단계 1 → 단계 2 진행해줘.
중간 컨펌 없이 한 흐름.
```

또는 더 짧게:

```
README 그림 새로 만드는 작업 — assets/_analysis/prompt_skill_diagrams.md 참고해서 진행
```
