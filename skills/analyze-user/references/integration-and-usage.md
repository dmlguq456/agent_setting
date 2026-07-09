## sub-agent 참조 패턴 (작업 시작 자리에서 실행)

각 agent 가 어떤 aspect 를 참조해야 하는지. **읽기 소스 = DB (`mem profile <stem>`)**; 본 매트릭스는 _어느 agent 가 어느 aspect 를 참조하는지의 매핑 문서_ — aspect 본문 SoT 는 DB. 본 매트릭스의 single source = [`MEMORY.md §7.6`](../../core/MEMORY.md) (aspect-중심 표) — 본 표는 그 agent-중심 동형 뷰; drift 발견 시 MEMORY §7.6 가 진실.

| Agent | 작업 시작 시 `mem profile <stem>` 실행 | 이유 |
|---|---|---|
| 자료팀 | `01_paper_figure_style` · `03_presentation_strategy` · `04_analysis_methodology` · **`05_domain_expertise`** | figure / 슬라이드 / 데이터 분석 시각 + 도메인 약자 (figure caption / 슬라이드 안 약자) |
| 디자인팀 | `01_paper_figure_style` · `03_presentation_strategy` · **`05_domain_expertise`** | UI mockup·슬라이드 비주얼·다이어그램 톤 + 도메인 약자 (UI 안 표현) |
| 연구팀 | **`01_paper_figure_style`** · `02_paper_writing_style` · `04_analysis_methodology` · `05_domain_expertise` | paper figure 인용 양식 (`01`) + 본문 톤 + 검증 방법론 + 도메인 약자 |
| 편집팀 | `01_paper_figure_style` · `02_paper_writing_style` · `03_presentation_strategy` · **`04_analysis_methodology`** · `05_domain_expertise` | 사용자 향 문서 wording (figure caption / paper / 발표 / 분석 표현) + 도메인 약자 |
| 기획팀 | **`02_paper_writing_style`** · `04_analysis_methodology` · **`05_domain_expertise`** · `07_coding_convention` | plan 작성 톤 (`02`) + 검증 패턴 + 도메인 약자 + 코드 컨벤션 (plan 안 코드 정합성) |
| 개발팀 | **`04_analysis_methodology`** · **`05_domain_expertise`** · `07_coding_convention` | 코드 안 metric·검증 (`04`) + 도메인 약자 (변수명·함수명, `05`) + model 폴더·config·prefix·preferred layer (`07`). per-project `experiment_conventions.md` 가 1순위, 본 레코드는 fallback |
| 메인 에이전트 | **`04_analysis_methodology`** · **`05_domain_expertise`** · `07_coding_convention` | 사용자 분석 응답 (`04`) + 도메인 약자 인지 (사용자 발화, `05`) + 코드 컨벤션 (autopilot-lab Step 0 / autopilot-spec Phase 0·2 / autopilot-code 4 원칙 prepend, `07`) |

> **매트릭스 정리** (2026-05-26): 06 (대화 메타 규칙) 은 _메인 에이전트 전용_ 으로 분리 — sub-agent 는 사용자와 직접 대화 X 라 적용 영역 없음 (글로벌 CLAUDE.md + 메모리 always-on 자료와 중복). 07 (코드 컨벤션) 은 _개발팀·기획팀·메인 에이전트만_ — 편집팀 (wording 영역) 은 코드 구조 컨벤션 적용 자리 없어 제외. agent 별 3-5 aspect 참조 default. 06 profile 레코드 자체는 `/post-it --scope user` default collab 저장처로 유지 (제거된 것은 _이 agent 참조 매트릭스 등록_ 뿐).

본 참조 패턴은 _agent 정의 본문_ 에 명시되어 있어 agent 가 invoke 될 때 자동.

## 메모리와의 관계

| | 메모리 (`<agent-home>/projects/<cwd>/memory/`) | user profile (DB `type=profile` 레코드, `mem profile <stem>`) |
|---|---|---|
| scope | per cwd (project) | cross-project (user) |
| 누적 | 자동 (대화 중) | 명시 (`/analyze-user` 또는 `/post-it --scope user`) |
| 형태 | 짧은 feedback / preference / fact | 구조화 패턴 카탈로그 |
| 갱신 | turn-by-turn | cycle-by-cycle |
| QA gate | X (raw) | O (다중 reviewer — refined) |

메모리는 _대화 메타 규칙·feedback 자료_ 의 raw 누적 (글로벌 CLAUDE.md 가 메인 source). user profile DB 레코드 는 _사용자 산출물 패턴_ (figure / writing / presentation / analysis / domain / coding) 의 verified refined 카탈로그 — 두 자료 영역 분리.

## 호출 예시

```
/analyze-user figure --source ~/nas/user/Uihyeop/doc/presentation/
```
→ figure aspect, 추가 source 로 presentation 폴더 포함.

```
/analyze-user all --mode init
```
→ 모든 aspect 통째 재셋업 — 첫 셋업 또는 _장기 미갱신_ 시.

```
/analyze-user --from qa --user-refine
```
→ 이전 pipeline 의 QA phase 부터 재개 + Phase 5 직전 사용자 memo pause.

```
/analyze-user coding_convention --source ~/path/to/NN_Zoo --source ~/path/to/other_repo
```
→ coding_convention aspect. 하드코딩 path X — 사용자가 코드 폴더 list 명시. cwd 자동 발견 (`model/` / `train*.py` / `config*.yaml` / `*.ipynb` 패턴) + 추가 폴더 `--source` 콤마 분리 복수.

## 갱신 빈도 권장

- **첫 셋업** — `/analyze-user all --mode init`. 본 사용자 자료 충분히 누적된 시점 (paper 5 편 이상) 에 한 번.
- **새 paper / 발표 / 보고서 직후** — 그 자료 추가만 incremental. `/analyze-user <relevant aspect>`.
- **새 모델 / 새 코드 repo 완성 직후** — `/analyze-user coding_convention --source <new-repo>`. cross-project 코드 패턴 누적.
- **장기 미갱신 (6 개월+)** 후 — 전체 통째 재검증 `/analyze-user all`.

(매 호출이 _adversarial 4-reviewer parallel_ 이라 _가벼운 호출_ 자체가 없음. 호출 빈도로만 부담 조절.)
