# 사용자 특성 자료 (user_profile)

> Claude Code 의 sub-agent 와 skill 이 _사용자의 일·자료 만들기 성향_ 을 참조할 단일 source. 메모리 (`~/.claude/projects/<cwd>/memory/`) 가 _per-cwd 자동 누적_ 자리라면, 본 폴더는 _deliberate 한 cross-project 사용자 프로필_.

## 파일 구성

| 파일 | 다루는 영역 | 누가 참조 |
|---|---|---|
| `01_paper_figure_style.md` | paper·논문 figure / 표 / 색 / 폰트 / 사이즈 / metric 묶음 표준 | 자료팀, 디자인팀, **연구팀** (paper 안 figure 인용 자리 양식), 편집팀 |
| `02_paper_writing_style.md` | paper 본문 작성 톤·argumentation·citation 패턴 | 연구팀, 편집팀, **기획팀** (plan 자리 작성 톤) |
| `03_presentation_strategy.md` | 슬라이드 구성·서사 flow·시각 결정·청중별 변형 | 자료팀 (presentation 자리), 디자인팀, 편집팀 |
| `04_analysis_methodology.md` | 데이터·실험 결과 분석 접근법·검증 패턴 | 자료팀, 연구팀, 기획팀, **개발팀** (코드 안 metric·검증 자리), 편집팀, **메인 Claude** (사용자 분석 자리 응답) |
| `05_domain_expertise.md` | 도메인 배경 (speech / TF DNN / signal processing)·용어 선호 | 연구팀, 자료팀, 디자인팀, 편집팀, **기획팀** (plan 안 약자), **개발팀** (변수명·함수명 자리 약자), **메인 Claude** (사용자 발화 자리 약자 인지) |
| `06_collaboration_style.md` | 작업 흐름·의사결정·feedback 패턴 (메모리 자동 누적 자료의 _구조화 요약_) | **자료팀·디자인팀·연구팀·편집팀·기획팀·개발팀·메인 Claude** (전 agent — 작업 흐름 자료) |
| `07_coding_convention.md` | 코드 일관 패턴 — model 폴더 구조 / config 메커니즘 / prefix / preferred layer / framework / metric set / log·ckpt / seed·reproducibility / naming | 개발팀 (new-lib·refactor·backend·frontend) · 기획팀 (plan 안 코드) · 편집팀 (code-related doc) · 메인 Claude (autopilot-lab Step 0 / autopilot-spec Phase 0·2 / autopilot-code 4 원칙) |

## 갱신 프로토콜

본 폴더의 파일은 두 경로로 갱신:

1. **`/analyze-user <aspect>`** skill — 사용자 과거 산출물 (paper / presentation / code / report) 을 스캔해 패턴 추출 후 해당 파일에 누적. 처음 셋업 또는 새 자료 누적 시.
2. **`/notes --scope user`** skill — 대화 중 발견한 _범용 패턴_ 을 사용자가 명시적으로 추가하고 싶을 때. project-level note 와 구분.

본 폴더는 _agent 정의_ 가 아니라 _사용자 자료_ — agent 본문에 박지 않고 _agent 가 작업 시작 자리에서 Read_ 하는 형태로 참조.

## sub-agent 참조 패턴

각 agent 의 작업 흐름 안 첫 자리에서 _해당 aspect_ 파일을 Read 한 뒤 _default 로_ 따른다 (사용자가 작업 turn 안에서 다른 설정을 명시하면 그 자리만 예외).

예 자료팀 — figure 자산 생성 시:
```
1. 01_paper_figure_style.md Read (figure 패턴 default)
2. 05_domain_expertise.md Read (figure caption 안 도메인 약자 자리)
3. 06_collaboration_style.md Read (자료 보고 자리 응답 톤)
4. 사용자 요청에 다른 명시 있으면 그 자리만 override
```

예 개발팀 _new-lib_ — autopilot-spec scaffold / autopilot-lab Phase 2 호출 자리:
```
1. analysis_project/code/experiment_conventions.md Read (1순위 — per-project source of truth)
2. ~/.claude/user_profile/07_coding_convention.md Read (2순위 — cross-project default)
3. 04_analysis_methodology.md Read (코드 안 metric·검증 자리)
4. 05_domain_expertise.md Read (변수명·함수명 자리 도메인 약자)
5. 06_collaboration_style.md Read (feedback 패턴)
6. 충돌 자리는 per-project 우선 — 본 프로젝트의 실제 컨벤션 침범 X
```

> **적극적 매핑** (2026-05-26): 각 agent 가 _최소 4-5 aspect_ 참조. 사용자 자리 더 적극 반영 — 도메인 용어 / 작업 흐름 / 응답 톤 자리 일관성 보강.

## 다음 cycle 의 누적 자리

본 사용자가 _새 paper / 발표 / 보고서_ 만들 때, 그 자료의 패턴이 본 폴더에 누적됨. 시간이 지날수록 _default 가 정밀_ 해짐. `/analyze-user --mode update` 로 incremental 갱신.
