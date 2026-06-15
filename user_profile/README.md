# 사용자 특성 자료 (user_profile)

> **읽기 소스 = DB (`mem profile <stem>`)** (`python3 ~/.claude/tools/memory/mem.py profile <stem>`); 본 문서는 어느 agent 가 어느 aspect 를 참조하는지의 **매핑 문서**일 뿐, aspect 본문 SoT 아님.

> Claude Code 의 sub-agent 와 skill 이 _사용자의 일·자료 만들기 성향_ 을 참조할 단일 source. 메모리 (`~/.claude/projects/<cwd>/memory/`) 가 _per-cwd 자동 누적_ 자리라면, 본 폴더는 _deliberate 한 cross-project 사용자 프로필_ 의 매핑 문서 (본문 SoT 는 DB `type=profile` 레코드).

## 파일 구성

| stem (DB `mem profile <stem>`) | 다루는 영역 | 누가 참조 |
|---|---|---|
| `01_paper_figure_style` | paper·논문 figure / 표 / 색 / 폰트 / 사이즈 / metric 묶음 표준 | 자료팀, 디자인팀, **연구팀** (paper 안 figure 인용 자리 양식), 편집팀 |
| `02_paper_writing_style` | paper 본문 작성 톤·argumentation·citation 패턴 | 연구팀, 편집팀, **기획팀** (plan 자리 작성 톤) |
| `03_presentation_strategy` | 슬라이드 구성·서사 flow·시각 결정·청중별 변형 | 자료팀 (presentation 자리), 디자인팀, 편집팀 |
| `04_analysis_methodology` | 데이터·실험 결과 분석 접근법·검증 패턴 | 자료팀, 연구팀, 기획팀, **개발팀** (코드 안 metric·검증 자리), 편집팀, **메인 Claude** (사용자 분석 자리 응답) |
| `05_domain_expertise` | 도메인 배경 (speech / TF DNN / signal processing)·용어 선호 | 연구팀, 자료팀, 디자인팀, 편집팀, **기획팀** (plan 안 약자), **개발팀** (변수명·함수명 자리 약자), **메인 Claude** (사용자 발화 자리 약자 인지) |
| `07_coding_convention` | 코드 일관 패턴 — model 폴더 구조 / config 메커니즘 / prefix / preferred layer / framework / metric set / log·ckpt / seed·reproducibility / naming | 개발팀 (new-lib·refactor·backend·frontend) · 기획팀 (plan 안 코드) · 메인 Claude (autopilot-lab Step 0 / autopilot-spec Phase 0·2 / autopilot-code 4 원칙) |

> 06 (대화 메타 규칙) 은 글로벌 `~/.claude/CLAUDE.md` §1~§7 가 단일 source. user_profile 안 별도 카탈로그 X (2026-05-26 완전 제거 — 중복 회피).

## 갱신 프로토콜

aspect 본문은 DB (`memory.db` `type=profile` 레코드) 가 SoT — 두 경로로 갱신:

1. **`/analyze-user <aspect>`** skill — 사용자 과거 산출물 (paper / presentation / code / report) 을 스캔해 패턴 추출 후 DB 레코드 (`mem add durable profile ... --source user-profile:<stem>`) 에 누적. 처음 셋업 또는 새 자료 누적 시.
2. **`/post-it --scope user <aspect>`** skill — 대화 중 발견한 _범용 패턴_ 을 DB durable/global 레코드에 추가하고 싶을 때 (`mem add durable profile ... --scope global --source user-profile:<stem>`). project-level 기록과 구분.

본 폴더는 _agent 정의_ 가 아니라 _매핑 문서_ — agent 는 작업 시작 자리에서 `mem profile <stem>` 실행해 DB body 를 default 로 따른다 (직접 파일 Read 아님).

## sub-agent 참조 패턴

각 agent 의 작업 흐름 안 첫 자리에서 _해당 aspect_ 를 `mem profile <stem>` 으로 실행해 그 body 를 _default 로_ 따른다 (사용자가 작업 turn 안에서 다른 설정을 명시하면 그 자리만 예외).

예 자료팀 — figure 자산 생성 시:
```
1. mem profile 01_paper_figure_style 실행 (figure 패턴 default)
2. mem profile 03_presentation_strategy 실행 (presentation 자리)
3. mem profile 04_analysis_methodology 실행 (분석 표 metric column)
4. mem profile 05_domain_expertise 실행 (figure caption 안 도메인 약자)
5. 사용자 요청에 다른 명시 있으면 그 자리만 override
```

예 개발팀 _new-lib_ — autopilot-spec scaffold / autopilot-lab Phase 2 호출 자리:
```
1. analysis_project/code/experiment_conventions.md Read (1순위 — per-project source of truth)
2. mem profile 07_coding_convention 실행 (2순위 — cross-project default)
3. mem profile 04_analysis_methodology 실행 (코드 안 metric·검증)
4. mem profile 05_domain_expertise 실행 (변수명·함수명 안 도메인 약자)
5. 충돌 자리는 per-project 우선 — 본 프로젝트의 실제 컨벤션 침범 X
```

> **매트릭스 정리** (2026-05-26): 06 (대화 메타 규칙) 은 _메인 Claude 전용_ — sub-agent 는 사용자와 직접 대화 X 라 적용 영역 없음. 07 (코드 컨벤션) 은 _개발팀·기획팀·메인 Claude 만_ — 편집팀 (wording 영역) 제외. agent 별 3-5 aspect 참조 default.

## 다음 cycle 의 누적 자리

본 사용자가 _새 paper / 발표 / 보고서_ 만들 때, 그 자료의 패턴이 본 폴더에 누적됨. 시간이 지날수록 _default 가 정밀_ 해짐. `/analyze-user --mode update` 로 incremental 갱신.
