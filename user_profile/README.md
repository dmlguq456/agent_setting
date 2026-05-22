# 사용자 특성 자료 (user_profile)

> Claude Code 의 sub-agent 와 skill 이 _사용자 (Ui-Hyeop Shin / Ui-Hyeop Shin / shinuh@mpwav.com) 의 일·자료 만들기 성향_ 을 참조할 단일 source. 메모리 (`~/.claude/projects/<cwd>/memory/`) 가 _per-cwd 자동 누적_ 자리라면, 본 폴더는 _deliberate 한 cross-project 사용자 프로필_.

## 파일 구성

| 파일 | 다루는 영역 | 누가 참조 |
|---|---|---|
| `01_paper_figure_style.md` | paper·논문 figure / 표 / 색 / 폰트 / 사이즈 / metric 묶음 표준 | 분석팀, 연구팀, 편집팀 |
| `02_paper_writing_style.md` | paper 본문 작성 톤·argumentation·citation 패턴 | 연구팀, 편집팀 |
| `03_presentation_strategy.md` | 슬라이드 구성·서사 flow·시각 결정·청중별 변형 | 분석팀 (presentation 모드), 편집팀 |
| `04_analysis_methodology.md` | 데이터·실험 결과 분석 접근법·검증 패턴 | 분석팀, 연구팀, 기획팀 |
| `05_domain_expertise.md` | 도메인 배경 (speech / TF DNN / signal processing)·용어 선호 | 연구팀, 분석팀, 편집팀 |
| `06_collaboration_style.md` | 작업 흐름·의사결정·feedback 패턴 (메모리 자동 누적 자료의 _구조화 요약_) | 메인 Claude, 모든 sub-agent |

## 갱신 프로토콜

본 폴더의 파일은 두 경로로 갱신:

1. **`/analyze-user <aspect>`** skill — 사용자 과거 산출물 (paper / presentation / code / report) 을 스캔해 패턴 추출 후 해당 파일에 누적. 처음 셋업 또는 새 자료 누적 시.
2. **`/notes --scope user`** skill — 대화 중 발견한 _범용 패턴_ 을 사용자가 명시적으로 추가하고 싶을 때. project-level note 와 구분.

본 폴더는 _agent 정의_ 가 아니라 _사용자 자료_ — agent 본문에 박지 않고 _agent 가 작업 시작 자리에서 Read_ 하는 형태로 참조.

## sub-agent 참조 패턴

각 agent 의 작업 흐름 안 첫 자리에서 _해당 aspect_ 파일을 Read 한 뒤 _default 로_ 따른다 (사용자가 작업 turn 안에서 다른 설정을 명시하면 그 자리만 예외).

예 분석팀 — figure 자산 생성 시:
```
1. ~/.claude/user_profile/01_paper_figure_style.md Read
2. 그 패턴을 default (색 팔레트·aspect ratio·폰트·임베드 등) 로 사용
3. 사용자 요청에 다른 명시 있으면 그 자리만 override
```

## 다음 cycle 의 누적 자리

본 사용자가 _새 paper / 발표 / 보고서_ 만들 때, 그 자료의 패턴이 본 폴더에 누적됨. 시간이 지날수록 _default 가 정밀_ 해짐. `/analyze-user --mode update` 로 incremental 갱신.
