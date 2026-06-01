# CLAUDE.md — Session Bootstrap

> 세션 시작 자동 로드. 본 문서는 _얇은 부트스트랩_. skill 카탈로그·description 은 매 세션 자동 주입, 운영 라우팅은 본 문서 §0 가 단일 출처.
>
> **워크플로우 맵 (4 트랙 skeleton — 라우팅 기본. 옵션·디테일 금지, 트랙 지도만)**:
> - 📄 문서: `analyze-project`/`autopilot-research` → `autopilot-draft` → `autopilot-refine`↻ → `autopilot-apply`
> - 🔬 연구·실험: `analyze-project`/`autopilot-research` → `autopilot-spec`↻ → `autopilot-code`↻ → `autopilot-lab`↻
> - 💻 앱: `autopilot-spec`↻ → `autopilot-design` → `autopilot-code`↻ → `autopilot-ship`↻
> - 📦 라이브러리·CLI: `analyze-project` → `autopilot-spec`↻ → `autopilot-code`↻
> - 사후 공통: `audit` (점검)·`autopilot-refine` (정정) / cross-project: `analyze-user`·`memo --scope user`
>
> **세션 시작 시 `~/.claude/WORKFLOW.md` (라우팅 코어, ~90 줄) 를 Read 한다** — 위 skeleton 은 트랙 지도, WORKFLOW 는 작업 본질 매핑·spec mode·entry→서브에이전트 분기·폴더 맵까지의 라우팅 표. 라우팅 결정 (특히 _기존 spec 프로젝트의 사후 수정_ 자리) 전 손에 있어야 함. `~/.claude/README.md` 는 GitHub 사용자용 문서 — 세션 시작 강제 Read 대상 아님.

---

## 응답 원칙 (메인 Claude 모든 응답에 적용)

### §0. [최상단 규칙] 작업 라우팅 — spec-first 파이프 + autopilot-* 호출

다른 모든 원칙에 앞서는 최우선 규칙.

**(A) spec-backed 프로젝트 — 파이프 우선.** cwd 또는 상위에 `.claude_reports/spec/<project>/pipeline_state.yaml` 이 있으면 (새 세션 포함), 수정·기능 요청을 _ad-hoc 직접 진단 + Edit 으로 끝내지 않는다._
1. **기존 산출물 파악** (손대기 전) — `spec/<project>/prd.md` · `pipeline_state.yaml` · 최근 `plans/<project>/*`.
2. **spec-drift 사전 체크** — spec-significant (route / schema·entity / UI-flow / 외부 연동 / 마이그레이션) 면 `autopilot-spec` update (prd.md 갱신 + `_internal/versions/v{N}/` snapshot). drift 명확하면 자율 진행, 애매하면 확인. spec 없으면 `autopilot-spec` 먼저 (throwaway 1 회성만 예외).
3. **`autopilot-code --qa quick` 경유** — 작은 요청도 파이프로 산출물 남김 → `plans/<project>/`. 직접 Edit 은 순수 typo·1 줄만. 상세 = `WORKFLOW.md` §7.

**(B) autopilot-* 호출 패턴 — 옵션 자동 구성 + 컨펌.** 자연어 한 줄로 부르면 컨텍스트 (cwd / `.claude_reports/` / 발화) 보고 옵션 조합 → 한 번 컨펌 (자연어 한 줄 요약 + 옵션 + 근거) → invoke.
- **발화 분류** (turn 첫 단계): ceremony 큰 6 (`autopilot-code/draft/research/refine/apply` + `analyze-user`) → 컨펌 흐름 / 작은 3 (`audit`/`memo`/`analyze-project`) → 즉시 invoke / sub-skill 자연어 → autopilot-* `--from <stage>` 재개 / 매칭 없음 → 직접 처리. 판단: 추적 필요 + 산출물 누적 → autopilot, 짧은 단발 → 직접.
- **Skip**: `/autopilot-code <args>` 같이 slash 직접 입력 = 컨펌 skip.
- **High-stakes → qa 상향**: _신중히 / 꼼꼼히 / camera-ready / submission·PR open 직전_ → adversarial 자동. `analyze-user` 는 항상 adversarial 고정.
- **무응답**: §2 자율 진행 적용 — 컨펌 시 `ScheduleWakeup` 10-30 분, 답 없으면 추천대로 invoke + "N 분 안 답 없으면 자율 진행" 한 줄.

### §1. 응답 규율 — 말투·간결·약속

- **말투**: 한국어 응답에 영어 일반 명사·동사구를 어순에 박지 않는다 (LaTeX·경로·논문/학회/모델/지표·정착 외래어는 영어 그대로). 한 응답 안 같은 개념은 같은 표기. 어미: chat 기본 해요체, 보고서·짧은 메타 라벨만 평어·개조식, 친절 안내체 (`~해 드릴게요`) 회피.
- **간결**: 필요한 정보만 — 묻지 않은 부연·자기 사고 narration (`먼저 X 를 본 뒤…`) 금지. 마무리 한두 문장 (무엇이 끝났는지 + 다음). 표·박스·코드 블록은 시각 anchor 도움 될 때만.
- **약속-행동 일치**: _진행할게요 / 수정할게요_ 같은 동사 약속어를 쓰면 매칭 tool call 이 같은 응답 안에 반드시 존재. 같은 turn 에 못 하면 질문 형태 (`X 로 진행해도 되나요?`).

### §2. Pause·자율 진행

- **Pause flag 비자동**: `autopilot-*` 의 `--user-refine` 같은 pause 옵션은 사용자 명시 신호 (`--user-refine` / `사용자 검토 끼워` / `memo 추가하게 멈춰줘`) 있을 때만. _신중히 / camera-ready_ 같은 high-stakes 신호 자체로 추가 X.
- **답 없으면 자율 진행**: 질문 뒤 답 없으면 추천 방향 진행.
  - **A. ScheduleWakeup 자동 깨움** (선택): 거는 자리 = ceremony 큰 컨펌·장시간 대기·일회성 큰 결정 / 안 거는 자리 = 작은 yes-no·자율 sequence 중간·짜증 신호. timeout 10–30 분. 깨움 시 직전 메시지가 알람 후 도착했는지 점검, stale 이면 skip + 한 줄 보고.
  - **B. 다음 메시지 시점** (fallback): 다음 메시지가 답 아니면 즉시 진행. 같은 질문 두 번 금지. 진행 시 "X 추천 방향으로 진행" 한 줄.
  - skill 내부 ask 자리 (analyze-project mode / autopilot-draft Step 0 등) 도 자동 적용.

### §3. 요청 흐름 안 후속 단계 자동 진행

_"X 해라"_ 명시 흐름 안 commit / git add / push / 메모리 저장 / 파일 정리 같은 후속 단계 매번 컨펌 묻기 금지. 자동 진행 후 한 줄 결과 보고. 별도 컨펌 자리 — (a) 새 디자인 결정 / 큰 layout 변화 (b) 파괴 작업 (git reset --hard / force push) (c) 다른 시스템 손대기. _"다음 단계 진행할까요?"_ 같은 닫기 wording 금지.

---

## Source of Truth

- **Skills**: `~/.claude/skills/*/SKILL.md` (invoke 시 자동 로드)
- **Agents**: `~/.claude/agents/*.md`
- **Family-wide 운영 규칙**: `~/.claude/CONVENTIONS.md` (QA 정의 / agent model / 산출물 컨벤션 / cross-doc invariants)
- **Autopilot 아키텍처**: `~/.claude/DESIGN_PRINCIPLES.md`
- **워크플로우 맵**: `~/.claude/README.md` (sync-skills 자동)
- **사용자 메모리**: `~/.claude/projects/<encoded-cwd>/memory/` — per-cwd, cross-project 공유 X
- **사용자 프로필**: `~/.claude/user_profile/` — cross-project 사용자 산출물 패턴 (figure / writing / presentation / analysis / domain / coding)

---

## 도메인 트리거 (작업 시작 전 자동 참조)

| 트리거 | 자동 참조 | 비고 |
|---|---|---|
| **doc/research major 수정** (`major`/`v{N+1}`/`/autopilot-refine` 명시 / ≥200줄·전체 section rewrite / 외부 검토 직전) | 본 문서 §0 + `autopilot-refine` SKILL | minor (default) 는 직접 Edit + `pipeline_summary.md` log. 누적 minor 5+ 시 `/audit` chat alert. |
| **QA·agent model·family-wide 작업** | `~/.claude/CONVENTIONS.md` | drift 발견 시 CONVENTIONS 가 진실. |
| **세션 시작 / 새 cwd 진입** | `<cwd>/.claude_reports/memo.md` (있을 때만) | `/memo` 명령으로만 갱신 (자동 X). |
| **spec-backed cwd / 사후 수정 요청** (cwd·상위에 `.claude_reports/spec/<project>/pipeline_state.yaml` 존재) | 본 문서 **§0** + WORKFLOW §7 | 최상단 규칙 — 기존 산출물 파악 → spec-drift 체크 (autopilot-spec update) → autopilot-code 파이프. ad-hoc 직접 Edit 은 순수 typo 만. |
| **사용자 향 산출물 wording 작성·수정** (paper / strategy / report / 발표 / README) | `~/.claude/agents/editorial-team.md` | 변경 직후 같은 turn 안 `Agent(편집팀)` _다듬기 모드_ 호출 의무. **트리거 X** — Claude instruction 파일 (CLAUDE.md / SKILL.md / agents/*.md / CONVENTIONS / DESIGN_PRINCIPLES) 자체. |

---

## Drift-Free Essentials

### Workspace assumption
모든 skill 은 _프로젝트 루트 실행_ 전제. `.claude_reports/` 는 현재 dir 생성. cross-project 작업은 `cd <other>` 후 별도 세션.

### 산출물 위치
| Skill | Artifact |
|---|---|
| `analyze-project --mode code/paper/doc` | `.claude_reports/analysis_project/{code,paper,doc}/` |
| `autopilot-research` | `.claude_reports/research/{topic}/` |
| `autopilot-draft` | `.claude_reports/documents/{date}_{name}/` |
| `autopilot-spec` | `.claude_reports/spec/{project}/` (청사진 — prd.md·stack.md·design/·ship.md, 항상 최신 T1) |
| `autopilot-code` | `.claude_reports/plans/{project}/{date}_{slug}/` (작업 사이클) |
| `autopilot-lab` | `.claude_reports/experiments/{date}_{slug}/` (+ `_RUNLOG.md`) |
| `autopilot-refine` | (대상 read+write) |

### Scope 경계
- `autopilot-research` = markdown 분석 리포트만
- `autopilot-draft` = strategy + draft (markdown 만, PPTX X)
- `autopilot-code` = code + tests + plan/dev logs (paper X)

산출물 중복·정의 외 추가 생성 시 멈추고 확인.

### 공통 플래그
`--qa quick|light|standard|thorough|adversarial` (정의 → CONVENTIONS §1) / `--from <stage>` / `--user-refine` (doc 전용)

### 자주 빠지는 함정
- pipeline 이 sub-skill 호출 중인데 또 부르기 → 덮어쓰기
- artifact_dir 오타 (research vs documents vs plans)
- PPTX 자동 생성 (presentation 은 markdown 만)
- 처음부터 `--qa thorough`/`adversarial` — 작은 요청은 quick, 본작업은 standard 부터 상향

---

## 운영 정책

- 본 CLAUDE.md **확장하지 말 것**. skill 추가/변경은 README.md (자동 동기화) 에 반영.
- 업데이트 시점: (a) source-of-truth 위치 변경 (b) artifact_dir 변경 (c) scope 경계 변경 (d) 도메인 트리거 행 추가/제거 (e) 응답 원칙 §0~§3 추가/변경.
