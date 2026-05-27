# Skill / Agent / Workflow 다이어그램 (3장)

자료팀 분석 (`_analysis/skill_graph.md`) 의 노드·관계 사실 위에, **가독성 1순위·정보량 2순위** 로 재설계한 SVG 3장. 사용자가 README 등에 어느 그림을 어디 박을지 결정하는 인덱스다.

> **2026-05-26 전면 재설계** — 직전 4장 (D1~D4) 은 edge 교차·hairball 로 mermaid 보다 못하다는 평가를 받아 폐기. 핵심 설계 결정은 아래 "교차 회피 전략" 항목 참조. 시각 토큰은 `user_profile/01_paper_figure_style.md` 의 역할→색 매핑·흰 fill + colored stroke·subtle drop shadow·rounded rect 를 따른다.

| 파일 | viewBox | 한 질문 | 메타포 |
|---|---|---|---|
| `track_pipelines.svg` | 1280×760 | 어떤 작업이 어느 트랙으로 흐르나 | 순수 수평 swimlane (레인 1개 = 트랙 1개) |
| `data_flow.svg` | 1280×720 | 산출물이 어떻게 다음 입력이 되나 | 3 zone 좌→우 pipeline + 폴더 아이콘 |
| `agent_qa_matrix.svg` | 1180×720 | 어느 skill 이 어느 agent 를 부르고 QA 는 어디 | 매트릭스 (화살표 0) + QA 사다리 |

---

## 교차 회피 전략 (재설계 핵심 결정)

직전 4장의 실패는 전부 _한 평면에 many-to-many 관계를 화살표로 그린 것_ 이 원인이었다. 재설계는 세 원칙으로 교차를 구조적으로 제거했다.

1. **many-to-many 관계는 화살표 대신 매트릭스** — agent 호출 (13 skill × 8 agent) 은 셀 채움으로 표현. 행·열 격자라 교차가 발생할 평면 자체가 없다 (G3). 직전 D2 의 orchestrator→agent 직선 수렴 hairball 을 근본 제거.
2. **트랙 간 hand-off 는 화살표 대신 우측 배지** — G1 은 레인 _안에서만_ 좌→우 단방향 화살표를 쓰고, 레인을 가로지르는 hand-off (research→code, lab→code 등) 는 레인 우측 끝 텍스트 배지로 옮겼다. 직전 D1 의 swimlane 가로지르는 스파게티를 제거.
3. **남은 화살표는 직교(orthogonal) 단방향만, 좌표로 교차 0 검증** — G2 의 cross-zone 화살표 7 개는 모두 axis-aligned 세그먼트로 라우팅하고, 제작 후 좌표 기반 스크립트로 interior 교차 0 을 확인했다. lab→code 졸업 화살표만은 어느 직교 통로를 써도 ap→draft 수평선과 한 점에서 교차해, _화살표를 포기하고 배지로 강등_ (원칙 2 적용).

---

## track_pipelines.svg · "어떤 작업이 어느 트랙으로 흐르나"

- **레이아웃** — 9 개 순수 수평 레인 (점검 → 사용자분석 → 연구 → 실험 → 청사진·앱 → 코드 → 디자인 → 문서 → 정정). 레인당 트랙 1개, 레인 tint 로 트랙 hue 구분.
- 각 레인 안에서 좌→우 단방향 파이프라인 (entry skill + stage 흐름 텍스트). 레인 간 화살표는 0 — hand-off 는 우측 끝 배지 컬럼으로.
- ceremony 큰 6 (research/code/draft/refine/apply/analyze-user) 노드는 빨강 점선 stroke (novelty device 차용) 로 구분, 나머지는 트랙색 실선 stroke.
- **인사이트** — 발화가 어느 entry 로 떨어지고 그 트랙 안에서 뭘 거치는지 레인만 따라가면 안다. research 의 3트랙 fan-out, lab/draft 의 졸업은 우측 배지로.

## data_flow.svg · "산출물이 어떻게 다음 입력이 되나"

- **레이아웃** — [① 선행 입력] → [② 산출 = orchestrator + `.claude_reports` 폴더] → [③ 사후] 3 zone. 직전 D3 계승·정련.
- 산출 orchestrator 마다 폴더 아이콘 (T1 진/T2 중/T3 옅 미니 스택) — 3-tier 구조 시각화. 폴더가 곧 다음 skill 의 입력임을 굵은 직교 화살표 소수로 연결.
- 하단 user_profile broadcast 띠 (analyze-user → `user_profile/0X_*.md` → 전 sub-agent default 참조) 유지.
- **인사이트** — 한 skill 산출 폴더가 다음 skill 의 implicit 입력이 되는 누적 구조. cross-zone 화살표 7개 전부 직교 단방향, interior 교차 0 (좌표 검증).

## agent_qa_matrix.svg · "어느 skill 이 어느 agent 를 부르고 QA 는 어디"

- **레이아웃** — 행 13 orchestrator skill × 열 8 agent 매트릭스 (화살표 0). 셀 = 진한 사각 (● 자동) / 링 (○ 옵션) / 빈칸. agent frontmatter color 를 셀 색에 차용.
- 연구팀·품질관리팀 열은 옅은 빨강 음영 + bold 헤더로 _호출 hub_ 강조. 매트릭스 우측 별도 좁은 컬럼에 각 skill 의 default QA 를 빨강 강도 사다리 (light → standard → thorough → adversarial) 로 병기.
- codex 열 = codex-review-team, `*` 각주로 "frontmatter opus 지만 실제 Codex GPT-5" 명시. ceremony 큰 6 skill 행 라벨은 bold.
- **인사이트** — 연구팀·품질관리팀이 호출 hub 임 + 각 skill 의 기본 엄격도를 한눈에. 교차선 0 (매트릭스 구조상 원천 차단).

---

## 시각 토큰 (`01_paper_figure_style.md` 준수)

- **2026-05-26 강화 프로필(Part B) 기반 재적용** — 라벨 sans-serif (수식 없는 generic 다이어그램이라 Times serif·Courier mono 전부 제거) / 2단계 stroke (의미 노드 굵은 역할색 2.2~2.4 vs I/O·배지 가는 회색 1.2) / stadium I/O (G1·G2 는 폴더 글리프·의미 skill 노드라 stadium 대상 없음, 메타포 유지) / soft drop shadow (우하단 offset dx1.5/dy2.2 + blur 1.5, 하드 엣지 제거) / tint halo (G1 레인 ~10%, G2 zone 배경 ~7% stroke 없는 옅은 역할색).
- 흰 fill + 역할색 stroke (stroke 가 semantic carrier) + subtle drop shadow + rounded rect (rx 6~7).
- 색: encoder/입력/분석 green `#4E7A3A`·tint `#E8F0DD` / 산출 orange `#D2691E`·tint `#FBE7DA` / 보조 gray `#6E6E6E` / novelty·hub 강조 red `#C0392B` (빨강 점선 stroke·텍스트 device) / accent gold `#D4A017`.
- 트랙 고유색: 청사진 파랑 `#4a6fb0` / 코드 청록 `#2f9090` / 디자인 분홍 `#c0508f` / 정정 plum `#8a4fa0` / 실험 연녹 `#6E9447` / 연구팀 보라 `#7a3da0`.
- 폰트: 전부 sans-serif (`-apple-system, 'Segoe UI', Helvetica, Arial` + 한국어 fallback `Malgun Gothic`/`Apple SD Gothic Neo`). 프로필 B5 — 수식 없는 generic 다이어그램은 라벨·식별자·캡션 모두 sans (serif math 는 수식 전용이라 비적용). 본문 10~12.5pt, heading 15~22pt.
- architecture 전용 device (ℝ^{...} 첨자·tensor slab·spectrogram) 는 워크플로우 다이어그램에 부적합해 생략.

## 사용 메모

- 한 자리에 한 장씩 박는 것을 가정. 셋 다 가로 긴 비율 (wide / 4:3 근접) — 본문·슬라이드 가로 자리에 적합.
- 색 hex 는 SVG 내 hardcode (CSS variable X) — 톤 조정 시 해당 fill/stroke 직접 수정.
- hex 는 PNG 육안 추정 ("≈") — 정확값은 원본 pptx eyedropper. 역할→색군 매핑·빨강 점선 novelty device 가 hex 정확도보다 우선.
