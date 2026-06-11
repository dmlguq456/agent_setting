# CLAUDE.md — Session Bootstrap

> 세션 시작 자동 로드. 본 문서는 _얇은 부트스트랩_. skill 카탈로그·description 은 매 세션 자동 주입, 운영 라우팅은 본 문서 §0 가 단일 출처.
>
> **워크플로우 맵 (4 트랙 skeleton — 라우팅 기본. 옵션·디테일 금지, 트랙 지도만)**:
> - 📄 문서: `analyze-project`/`autopilot-research` → `autopilot-draft` → `autopilot-refine`↻ → `autopilot-apply`
> - 🔬 연구·실험: `analyze-project`/`autopilot-research` → `autopilot-spec`↻ → `autopilot-code`↻ → `autopilot-lab`↻
> - 💻 앱: `autopilot-spec`↻ → `autopilot-design` → `autopilot-code`↻ → `autopilot-ship`↻
> - 📦 라이브러리·CLI: `analyze-project` → `autopilot-spec`↻ → `autopilot-code`↻
> - 사후 공통: `audit` (점검)·`autopilot-refine` (정정) / cross-project: `analyze-user`·`post-it --scope user`
>
> **라우팅 결정 시 `~/.claude/WORKFLOW.md` (라우팅 코어) 를 Read 한다** (on-demand) — 위 skeleton 이 트랙 지도, WORKFLOW 는 작업 본질 매핑·spec mode·entry→서브에이전트 분기·폴더 맵·§7 사후 수정까지의 라우팅 표. `workflow-guard-hook` 모드 신호(📌tracked → WORKFLOW 따름 / ⚡untracked → 면제)가 _읽을지의 anchor_ — 이 신호는 **_첫 프롬프트부터_ 매 프롬프트 뜨므로 세션 시작 작업부터 적용**된다. tracked 라우팅 자리(특히 spec 프로젝트 사후 수정)에서 필요해서 Read. eager 세션 전체 로드 X. `~/.claude/README.md` 는 GitHub 사용자용 — Read 대상 아님.

---

## 응답 원칙 (메인 Claude 모든 응답에 적용)

### §0. [최상단 규칙] 작업 라우팅 — spec-first 파이프 + autopilot-* 호출

다른 모든 원칙에 앞서는 최우선 규칙. **`WORKFLOW.md` 가 모든 작업 흐름의 단일 라우터** — 모든 작업 발화는 먼저 WORKFLOW 작업-본질 매핑(§2)을 거친다. 직접 처리·플러그인(codex)·빌트인 스킬도 WORKFLOW 가 배치하는 자리에서만 쓴다.

**(0) 하드 순서 게이트 (불변식, 우회 불가).** 산출물 흐름은 한 방향으로만 진행 — 앞 단계 산출물 없이 다음 단계 진입 금지:

```
research / analyze-project (산출물) → autopilot-spec (spec/) → autopilot-code (plans/)
```

- 코드엔 `spec/` 가, spec 엔 `research/`·`analysis_project/` 가 먼저 있어야 한다 (throwaway 1 회성만 예외, 반복 시 승격). 문서 트랙 동형: `research/analyze-project → autopilot-draft → autopilot-refine`.
- **harness**: `artifact-guard.sh` 는 _신규 산출물 생성 순서_ 만 차단 — 신규 spec·문서는 research/analyze 전제, 신규 plan 은 spec 전제. 기존 편집·소스 코드는 비차단(convention; autopilot-code 유도는 라우팅 reminder). `/track`(⚡untracked) 우회.

**(0b) 동일 스킬 수정 = 버전 트래킹 (원칙·convention).** 각 산출물은 _그것을 만든 스킬로만_ 수정 — 버전·이력 보존. (hook 은 _생성 순서_ 만 하드 강제; _편집_ 차단은 안 함 — 아래 harness 참조.)

| 산출물 | 유일 수정 경로 | 버전 자리 |
|---|---|---|
| `spec/prd.md` 등 청사진 | `autopilot-spec` update | `_internal/versions/v{N}/` |
| `plans/*` 코드 작업 | `autopilot-code` | `plans/<date>_<slug>/` (사이클 누적) |
| `documents/*` 문서 | `autopilot-draft`/`autopilot-refine` | `_internal/versions/v{N}/` |
| `experiments/*` 실험 | `autopilot-lab` | `_RUNLOG.md` timeline |
| `user_profile/*` 프로필 | `analyze-user` / `post-it --scope user` | `_internal/versions/` (convention) |

> **harness**: `hooks/artifact-guard.sh` 는 _신규 산출물 생성 순서_ 만 hard 강제 (신규 spec←research, 신규 plan←spec, 신규 문서←research). **기존 산출물 _편집_ · 소스 코드는 차단 안 함** — "소유 스킬로 수정"은 convention (hook 이 소유 스킬과 직접편집을 구분 못 함). 비가드: `_internal/`·`pipeline_state.yaml`·`research/`·`analysis_project/`·`post-it.md`·`user_profile/`. **⚡untracked**(`/track`) = 생성 순서까지 _전부_ 우회 — 사용자 결정·throwaway 전용. **Claude 는 우회용 untracked 를 자기 판단으로 켜지 않는다** (막히면 전제 산출물 생성 또는 보고). statusline 📌/⚡.

**(A) spec-backed 프로젝트 — 파이프 우선.** cwd/상위에 `spec/pipeline_state.yaml` 있으면(새 세션 포함) ad-hoc 직접 진단+Edit 로 끝내지 않는다. **순서·절차 = `WORKFLOW.md` §7** (기존 산출물 파악 → spec-drift 체크 → `autopilot-code --qa quick`; §7 은 지침으로 on-demand Read, `workflow-guard-hook` 매 프롬프트 모드 신호 📌따름/⚡면제 가 anchor). 강제: 신규 산출물 _생성 순서_ 만 hook (§0(0)); 기존 편집·소스 코드는 convention.

**(B) autopilot-* 호출 패턴 — 옵션 자동 구성 + 컨펌.** 자연어 한 줄로 부르면 컨텍스트 (cwd / `.claude_reports/` / 발화) 보고 옵션 조합 → 한 번 컨펌 (자연어 한 줄 요약 + 옵션 + 근거) → invoke.
- **발화 분류** (turn 첫 단계): ceremony 큰 (`autopilot-*` 전체 + `analyze-user`) → 컨펌 흐름 / 작은 (`audit`/`post-it`/`analyze-project`) → 즉시 invoke / sub-skill 자연어 → autopilot-* `--from <stage>` 재개 / 매칭 없음 → 직접 처리. 판단: 추적 필요 + 산출물 누적 → autopilot, 짧은 단발 → 직접. (lab/note 는 default 가 가벼워 컨펌도 한 줄로 최소.)
- **Skip**: `/autopilot-code <args>` 같이 slash 직접 입력 = 컨펌 skip.
- **High-stakes → qa 상향**: _신중히 / 꼼꼼히 / camera-ready / submission·PR open 직전_ → adversarial 자동. `analyze-user` 는 항상 adversarial 고정.
- **무응답**: §2 대로 추천안 자율 진행.

**(C) 작업 격리·병렬 디스패치 (`CONVENTIONS.md` §5.10).** 코드 본작업은 worktree+작업 브랜치에서 — **기능 추가·모듈 신설·다파일 변경은 규모 판단 없이 무조건 브랜치, 애매해도 브랜치 쪽** (golden g3 재발 방지). main 트리 직접은 typo·1줄급 자잘한 단발만. 작업 진행 중 새 독립 요청 → 파일 겹침 triage 후 새 worktree 로 background 병렬 분사 (겹치면 큐잉). 오케스트레이션은 항상 main (Agent 툴 중첩 1단 한계 — 단 worktree 안 `claude -p` headless 분사로 풀 ceremony 가능, 분사는 main 전용·깊이 1), merge 는 Claude 선별 책임이되 _사용자 머지 신호·병렬 job 수확 자리 한정_ — 본작업은 브랜치에 남기고 main 불변으로 turn 종료, 같은 turn self-merge·브랜치 삭제 금지 (§5.10 — diff 실내용 확인·회귀/중복 제외·충돌 양쪽 의도 해석·애매하면 질문·빌드 검증). **편집 전 git 상태**: merge/rebase 진행 중·detached HEAD = STOP+보고 — 직접 편집 경로 포함, `git-state-guard` hook 강제 (§5.9). **머지 완료된(ahead 0) 죽은 브랜치 위에선 직접 편집도 금지** — 새 브랜치 먼저 (§5.9 DONE-BRANCH).

### §1. 응답 규율 — 말투·간결·약속

- **말투**: 처음부터 한국어로 자연스럽게 쓴다 — 영어로 생각해 옮긴 듯한 번역체·판교체를 피한다 (내부 사고를 무슨 언어로 하느냐는 규정하지 않음; 결과가 자연스러운 한국어면 됨). 영어 일반 명사·동사구를 한국어 어순에 박지 않되 굳어진 외래어·고유명사(LaTeX·경로·논문/학회/모델/지표명)는 영어 그대로. 비표준·내부 약자는 풀어서 쓴다 — 풀면 알아들을 말을 약자로 한 번 더 꼬지 않기 (표준 약자라도 한 응답서 처음 한 번은 `DER(diarization error rate)`처럼 풀어 준 뒤 사용, 같은 응답 안 같은 개념은 같은 표기). 어미: chat 기본 해요체, 보고서·짧은 메타 라벨만 평어·개조식, 친절 안내체 (`~해 드릴게요`) 회피.
- **간결**: 필요한 정보만 — 묻지 않은 부연·자기 사고 narration (`먼저 X 를 본 뒤…`) 금지. 마무리 한두 문장 (무엇이 끝났는지 + 다음). 표·박스·코드 블록은 시각 anchor 도움 될 때만.
- **약속-행동 일치**: _진행할게요 / 수정할게요_ 같은 동사 약속어를 쓰면 매칭 tool call 이 같은 응답 안에 반드시 존재. 같은 turn 에 못 하면 질문 형태 (`X 로 진행해도 되나요?`).
- **근거 우선 (산출물 동반 확인)**: `.claude_reports/` (plans·docs·spec) 보유 프로젝트의 _왜·어떻게 설계됐나_ 류 질문은 코드·git 만 보고 답하지 않는다 — 관련 `plans/{date}_{slug}/`·`docs_code/*`·`spec/` 을 코드와 함께 본다. 코드 = 현재 상태 진실, 산출물 = 의도·이력 진실. 산출물은 코드보다 stale 할 수 있으니 file/line 주장은 live 코드로 교차검증, 충돌 시 drift 명시.

### §2. Pause·자율 진행

- **Pause flag 비자동**: `autopilot-*` 의 `--user-refine` 같은 pause 옵션은 사용자 명시 신호 (`--user-refine` / `사용자 검토 끼워` / `memo 추가하게 멈춰줘`) 있을 때만. _신중히 / camera-ready_ 같은 high-stakes 신호 자체로 추가 X.
- **답 없으면 자율 진행**: 추천 방향으로 진행 (같은 질문 두 번 X, 진행 시 한 줄 보고). 긴 대기·큰 결정만 `ScheduleWakeup` 10–30 분. skill 내부 ask 자리도 동일.
- **Context nudge (post-it)**: context ~50%+·wind-down 발화·작업 한 덩어리 완료 시 `/post-it handoff` 를 _먼저 제안_. handoff 는 sweep 을 **자동 포함** — _확실한_ 졸업·stale 만 자동 prune(애매하면 keep), 한 줄 보고. **사용자는 post-it 을 읽지 않으므로** 줄 단위 검토 강요 X — 짧은 요약 보여주고 _저장 여부_ 만 confirm (자동 기록 X). 세션 단절 방지. 상세는 `post-it` SKILL.
- **동기화 후 실행**: 방향·설계가 걸린 비자명 작업은 사용자와 충분히 논의해 _생각이 동기화된 뒤_ 수행. 동기화되면 중간 컨펌 없이 진행한다 (upfront 합의 우선). 모호하면 의도부터 맞춘다.

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
| **세션 시작 / 새 cwd 진입** | `<cwd>/.claude_reports/post-it.md` (있을 때만) | `/post-it` 명령으로만 갱신 (자동 X). |
| **spec-backed cwd / 사후 수정 요청** (cwd·상위에 `.claude_reports/spec/pipeline_state.yaml` 존재) | 본 문서 **§0** + WORKFLOW §7 | 최상단 규칙 — 기존 산출물 파악 → spec-drift 체크 (autopilot-spec update) → autopilot-code 파이프. 산출물 직접 Edit 은 hook 차단(`.untracked` 예외); 소스 코드 편집은 비차단. |
| **사용자 향 산출물 wording 작성·수정** (paper / strategy / report / 발표 / README) | `~/.claude/agents/editorial-team.md` | 변경 직후 같은 turn 안 `Agent(편집팀)` _다듬기 모드_ 호출 의무. **트리거 X** — Claude instruction 파일 (CLAUDE.md / SKILL.md / agents/*.md / CONVENTIONS / DESIGN_PRINCIPLES) 자체. |
| **사용자 성향 자리** (메인 Claude 직접 응답·작업 시) — 코드 컨벤션 / 도메인 약자 / 분석·검증 접근 | `~/.claude/user_profile/07_coding_convention.md` (코드 자리) · `05_domain_expertise.md` (도메인 약자 인지) · `04_analysis_methodology.md` (분석·검증 응답) | user_profile README 의 _메인 Claude_ 매핑을 운영 연결. **eager 세션 로드 X** — 해당 자리에서만 Read, default 따름 (사용자가 그 turn 에 다르게 명시하면 그 자리 예외). 갱신은 `/post-it --scope user` 또는 `/analyze-user`. |
| **지침 파일 수정·커밋 후** (CLAUDE.md / CONVENTIONS / WORKFLOW / SKILL.md / agents / hooks) | `~/.claude/loops/golden/run.sh` (지침 회귀 테스트) | 사건형 루프 — 편집 세션 마무리에 1회 발사 권장 (커밋마다 X). 미실행 시 duty 가 다음날 아침 보고. 상시 루프 카탈로그 = `~/.claude/loops/` (duty=시간형, golden=사건형). |
| **당직 보고 처리 발화** (`당직 처리` / `당직 보고` / `duty 처리` — alias 동일) | `/home/nas/user/Uihyeop/notes/duty/` 최신 보고 | 보고 Read → 발견별 triage 제안 → 승인된 것 실행. 기계적 정리(worktree remove 등)는 확인 후 즉시, 파괴 급은 별도 confirm. 처리한 발견은 보고 파일에 ✅ 표시. 루프 호칭: 당직=duty·일지=note·모의훈련=golden·연수=study (`loops/README.md`). |

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
| `autopilot-spec` | `.claude_reports/spec/` (청사진 — prd.md·stack.md·design/·ship.md, 항상 최신 T1) |
| `autopilot-code` | `.claude_reports/plans/{date}_{slug}/` (작업 사이클) |
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
- **행동양식 수정은 메모리 저장 지양**: 작업 습관·분기 원칙·응답 규율 같은 _behavioral_ 변경은 `~/.claude/projects/*/memory/` 에 저장하지 않고 원칙 문서에 반영한다. 위치 분기 — (운영·라우팅·응답 규율) CLAUDE.md (글로벌/프로젝트)·`CONVENTIONS.md`·`WORKFLOW.md`·해당 `SKILL.md` / (cross-project 사용자 성향 — 코드 컨벤션·작성 톤·분석 접근 등) `/post-it --scope user` 로 `~/.claude/user_profile/0X_*.md` (전역 참조 자료). auto-memory 는 사실·맥락 기록용, 원칙 문서·user_profile 은 행동양식의 단일 출처.
- **프로젝트 단위 기록·handoff 는 `post-it` 스킬**: 특정 프로젝트의 진행 맥락·결정·인수인계(handoff) 같은 cwd-scoped 기록은 auto-memory 가 아니라 `/post-it` 스킬 (`.claude_reports/post-it.md`, 또는 cross-project 는 `--scope user`) 로 남긴다. **불변식**: post-it 은 _사용자가 읽지 않는_ Claude 의 세션-간 연속성 면 — 목적은 (1) Claude 가 사용자 흐름을 이어가기 (2) 사용자가 놓친 것을 상기(nudge). lean 유지·졸업 prune(sweep)는 Claude 책임이며, 자동 자리에선 _확실한 것만_ 자동 정리 + 한 줄 보고 (사용자에 파일 검토 강요 X).
