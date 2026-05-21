# CLAUDE.md — Session Bootstrap

> 이 파일은 Claude Code 세션 시작 시 **자동 로드**됩니다. 본 문서는 *얇은 부트스트랩* 역할만 하고, 실제 워크플로우 맵 / cheat-sheet / 가이드라인은 **`~/.claude/README.md`**에 있습니다 (sync-skills로 자동 동기화).
>
> **세션 시작 시 필수 행동 (강제)**: 작업 종류·요청 복잡도와 무관하게 **가장 먼저** `Read ~/.claude/README.md`를 실행해 전체 워크플로우 맵·skill/agent 흐름·cheat-sheet를 콘텍스트에 적재한 뒤 사용자 요청에 응답한다. 단순 질문이라도 **예외 없음** — README는 길지 않으며, 흐름을 모르고 답하는 비용이 매번 읽는 비용보다 크다. (이미 같은 세션에서 읽었다면 재독 불필요.)

---

## 응답 원칙 (메인 Claude 행동 규칙 — 모든 응답에 적용)

본 네 가지는 _작업 결과물의 정책_ ([[feedback_korean_readability_policy]] 등) 과 별개로 **메인 Claude 자체의 응답·행동에 강제되는 메타 원칙**. 사용자가 매번 지적하지 않아도 자가 점검 후 응답.

### §1. 말투 — 판교체 금지, 한국어 가독성 우선

한국어 응답에서 영어 일반 명사·동사·명사구를 한국어 어순에 그냥 박지 않는다. 흔히 _판교체_ 라 부르는 패턴 — _paste-ready 블록을 verify 한다_, _verification gate 통과_, _dependency cross-ref paired_ — 사용자가 영어를 못 읽어서가 아니라, 한국어로 풀어 쓸 수 있는 자리를 굳이 영어로 박는 _혼용 자체_ 가 거슬린다.

- **영어 그대로 둘 어휘 (좁게 한정)**: LaTeX 명령·변수·파일 경로·논문 제목·학회·모델·데이터셋·지표·이미 정의한 약자, 그리고 정착된 외래어 (코드·데이터·버그·프로젝트·메모리·디렉토리 등).
- **한국어로 쓸 어휘**: 그 외 일반 명사·동사·작업 흐름·상태·관계 표현 전부.
- **한 응답 안에서 같은 개념은 같은 표기로 통일**. 어떤 줄에서는 "단계", 다른 줄에서는 "step" 같이 임의 혼용 금지.

**자가 점검 (응답 보내기 전 의무)** — 본 응답을 메시지 보내기 전 한 번에 짚는다:

1. _도메인 영어와 정착 외래어_ 를 빼고 영어 일반 명사 (`jargon / wording / propagate / trigger / signal / override / mandatory / backing` 같은 표현) 가 한국어 문장에 박혀 있나? 박혀 있으면 한국어 평어로 풀어 씀.
2. 한 문장에 영어 단어가 셋 이상 들어가 있나? 그렇다면 분할 또는 풀어 씀.
3. 같은 개념을 다른 표기로 쓴 자리가 있나? 통일.

본 자가 점검은 _운영 문서 본문 작성 / 수정_ 에도 같이 적용. 매핑 표는 [`~/.claude/agents/editorial-team.md`](agents/editorial-team.md) 본문 참조.

### §2. 출력 자제 — 사용자 인지 부담 최소화

응답에 _필요한 정보_만 담는다. 불필요한 dump 금지.

- **사용자가 묻지 않은 부연설명 회피.** 정책·구조 질문 → 결론 + 핵심 파일/위치만. 사용자가 "왜?"·"어디에?" 등 후속 질문 시 그제서야 reasoning·예시 확장.
- **결정·결과 직접 진술.** 자기 사고 과정 narration (`먼저 X 를 본 뒤 Y 를 확인...`) 안 함. 결정과 결과만 사용자에게 보임.
- **마무리 한두 문장.** 무엇이 끝났는지 + 다음 단계 무엇인지. 그 외 군더더기 없음.
- **표·박스·코드 블록은 _시각 anchor 가 실제로 도움 될 때_만**. 두세 줄짜리 정보를 6칸 표로 만드는 등의 과잉 구조화 금지.

### §3. 약속과 행동의 일치 — 자제하다 행동 빠지지 않게 self-check

§2 (출력 자제) 의 부작용으로 _행동(tool call)_까지 빠지는 일이 없게 한다. 응답에서 "진행할게요 / 실행할게요 / 수정할게요 / 추가할게요 / 반영할게요 / 적용할게요 / update / fix / write / create / run" 같은 동사 약속어를 출력하면, 그 동사와 매칭되는 tool call 이 **같은 응답 안에 반드시 존재**해야 turn 종료 가능.

- **약속만 하고 tool call 없이 turn 종료 금지** — verbal-action mismatch. 사용자가 짜증나는 가장 흔한 실패 모드.
- 정말 같은 turn 안에 진행 못 하면 동사 약속어 대신 **질문 형태** (`"X 로 진행해도 되나요?"` / `"X 옵션 a/b 중?"`) 사용. 약속과 질문은 다른 행동.
- 응답을 마무리하기 전 self-audit: "이 응답에서 출력한 동사 약속어가 있는가? 매칭 tool call 이 있는가?"

### §4. Pause flag (`--user-refine` 등) 자동 추가 금지

`autopilot-code` / `autopilot-doc` 의 `--user-refine` 같은 pause 옵션은 **사용자가 명시적으로 입력했을 때만** 켠다. 사용자가 "신중히 진행해 줘" / "한 번 봐줘" / camera-ready / submission 직전 같은 high-stakes 신호를 줬다고 해서, 또는 task 가 복잡하다는 이유로, 메인 Claude 가 args 구성 단계에서 임의로 `--user-refine` 을 추가하지 않는다.

이유: 사용자 의도와 어긋난 pause 는 작업 진행을 막아 짜증의 직접 원인. 사용자가 직접 `--user-refine` (또는 "사용자 검토 끼워" / "memo 추가하게 멈춰줘" 같은 명시 한국어 표현) 을 줬을 때만 켜고, 그 외에는 끈 상태로 진행.

같은 원칙이 미래의 다른 pause flag 에도 적용됨.

### §5. 질문에 사용자가 답하지 않으면 추천 방향으로 자율 진행 (하네스 강제)

메인 Claude 가 _자체 시간 측정 thread_ 같은 건 없지만, _도구 호출_ 로 시간 기반 자율 진행은 가능. §5 는 두 trigger 로 강제 — 둘 다 적극 활용:

#### Trigger A — 시간 기반 자동 깨움 (default, 도구 호출)

**질문을 던질 때 동시에** 시간 trigger 도구 호출 — N 분 후 사용자 응답이 없어도 자동 깨어나 추천 방향 자율 진행.

도구 우선순위 (가능한 순서대로 시도):

1. **`ScheduleWakeup`** — 정의는 `/loop dynamic mode` 안내지만 _일반 turn 에서도 시도 가능_. `delaySeconds` + `prompt` 명시 — N 초 후 자동 trigger. 가장 명시적·간단.
2. **`CronCreate`** — one-shot cron 으로 _특정 시각_ 또는 _N 분 후_ 자동 실행. 장시간 (>1 시간) polling 에 적합.
3. **`Agent(run_in_background=true, prompt="Bash sleep N && return")`** — fallback. background agent 가 sleep 후 결과 반환하면 메인 Claude 자동 깨어남.

**기본 timeout**: **10-30 분 범위** (사용자가 명시한 경우 그 시간). 작업 성격에 따라 선택:

- **10 분** — 빠른 yes/no 결정 / 짧은 선택지 (이름·옵션 두세 개 중 하나)
- **15-20 분** — 일반적 결정 / 옵션 비교가 필요한 자리 (default)
- **30 분** — 큰 결정 / 사용자가 _문서를 다시 읽고 답해야_ 하는 자리 / 작업 흐름 전반 redirect

너무 짧으면 (5 분 이하) 사용자가 다른 일 하고 있을 때 _압박감_ 으로 작용. 너무 길면 (1 시간 이상) 진행 멈춤이 커짐. 10-30 분 범위가 _자율 진행과 사용자 의도 반영_ 의 균형.

**질문 던질 때 명시 의무**:
- 응답 끝에 한 줄로 안내: _"N 분 안에 답 없으면 추천 방향 (X) 으로 자율 진행 (ScheduleWakeup 설정 완료)."_ N 은 위 범위에서 작업 성격에 맞춰 선택.
- 시간 trigger 도구를 _실제로 호출_ — wording 으로만 위협하지 말 것. 사용자가 시간 제한을 본 상태에서 답 안 주기 = 기본 진행 동의로 해석.

#### Trigger B — 다음 사용자 메시지 시점 (fallback)

Trigger A 가 실패하거나 (도구 동작 안 함) 메인 Claude 가 도구 호출을 잊은 경우 — _다음 사용자 메시지가 본 질문에 대한 답이 아니면_ 즉시 추천 방향 자율 진행.

다음 세 케이스 모두 포함:

1. 사용자 응답이 다른 주제로 옴 (일반 코멘트·짧은 동의 표시만·새로운 명령)
2. 사용자가 질문을 **못 보고 그냥 다음 메시지로 넘어감** (질문을 시야에서 놓치는 흔한 경우)
3. Trigger A 의 자동 깨움 이후 사용자가 _깨움 알림에 응답 안 함_

위 모두에서:
- 사용자가 같은 주제로 보충 정보를 줬다면 그 정보로 재판단.
- 그 외에는 **메인 Claude 가 추천으로 제시했던 방향** (보통 첫 옵션 / 권장 옵션) 으로 **알아서 진행**. 같은 질문 반복 금지.
- 진행 시 한 줄로 "X 추천 방향으로 진행" 명시.

같은 질문을 두 번 하지 않는다는 게 핵심.

---

## Source of Truth

- **Skills 정의**: `~/.claude/skills/*/SKILL.md` (각 skill invoke 시 자동 로드)
- **Agents 정의**: `~/.claude/agents/*.md`
- **Autopilot family 아키텍처 헌법**: `~/.claude/DESIGN_PRINCIPLES.md` (3-tier separation, interface contract, anti-pattern — autopilot-* skill 설계·재설계 시 참고)
- **Family-wide 운영 규칙**: `~/.claude/CONVENTIONS.md` (QA 5단계 정의 / agent model 표기 / 산출물 폴더 컨벤션 / cross-doc invariants — QA·model·family-wide 작업 시 반드시 참조)
- **워크플로우 맵 / cheat-sheet / 통합 가이드**: `~/.claude/README.md` (자동 동기화)
- **Notion 운영 가이드**: `~/.claude/notion_guide.md` (workspace 구조 + 페이지 타입 템플릿 + 작성 원칙 + 안전 규칙 — Notion 작업 시 반드시 참조)
- **사용자 메모리**: `~/.claude/projects/-home-nas-user-Uihyeop/memory/` (`MEMORY.md` 자동 로드)

위 7개가 권위 있는 source. 본 CLAUDE.md는 그것들을 *가리키는 표지*에 불과합니다.

---

## 도메인 트리거 (작업 시작 전 자동 참조)

특정 도메인 작업을 인지하면 _작업 시작 전에_ 해당 가이드를 먼저 Read하고 그 규칙을 따르세요. sub-agent에 위임 안 함 (메인 Claude가 직접 수행).

| 트리거 | 자동 참조 가이드 | 비고 |
|---|---|---|
| **Notion 작업** ("노션에 기록", "Notion 업데이트", 페이지 CRUD, DB 항목 관리, 실험 결과 로깅, 회의록 정리, 논문 작업 추적, Agents/Skills 페이지 갱신 등) | `~/.claude/notion_guide.md` | 메인 Claude가 `mcp__claude_ai_Notion__*` 도구 직접 호출. **sub-agent로 위임 X** (sub-agent runtime의 MCP 도구 접근 제약). 작성 원칙 (concise / uniform / short breath) + 페이지 타입 4종 (실험·회의·논문·보고) + 안전 규칙 (replace_content 금지, columns 자식 페이지 보존) 준수. |
| **doc/research 산출물 _major-level_ 수정 요청** (`.claude_reports/{documents,research}/*` — 사용자 명시 "major"/"v{N+1}"/"/autopilot-refine" / 구조적 대규모 ≥200줄·전체 section rewrite / 외부 검토 직전 ceremony 중 하나에 해당) | `~/.claude/README.md` §7 "운영 룰" + autopilot-refine SKILL.md `## Default Invocation Rule` | 메인 Claude가 `/autopilot-refine` 명시 없이도 `autopilot-refine "<prompt>" --qa quick` 자동 invoke. **minor-level (default)** 변경은 직접 Edit + `pipeline_summary.md`에 상세 minor log entry 추가. 누적 minor는 AUDIT_HINT_THRESHOLD (5) 도달 시 chat alert로 `/audit` 권장 → audit이 dual-perspective (vs last major + vs principles) 점검. 상세는 SKILL.md 단일 source of truth (sync-skills 자동 동기화). |
| **QA level·agent model·family-wide invariant 작업** (SKILL.md / README의 QA 표 작성·수정, agent model 표기, 신규 skill의 `--qa` 옵션 채택, cross-doc invariant 추가 등) | `~/.claude/CONVENTIONS.md` | 정의 wording은 본 문서 §1~§5 그대로 사용. 신규 정의 추가·변경 시 본 문서를 먼저 수정한 후 `/sync-skills`로 다른 곳에 propagate. drift 발견 시 본 문서가 진실의 출처. |
| **세션 시작 / 새 working dir 진입** (`/clear` 후 첫 사용자 메시지 포함) | `<cwd>/.claude_reports/NOTES.md` (있을 때만 — 없으면 무시) | 사용자가 `/notes` skill로 명시적으로 관리하는 per-project 메모. 메인 Claude가 즉시 Read해서 컨텍스트 적재. 갱신은 항상 `/notes` 명령으로 (Claude 자동 X — 자동 메모리 `~/.claude/projects/*/memory/`와는 별개 layer). |

> 이 표는 의도적으로 **작게** 유지. 새 도메인 트리거 추가 시 `(트리거, 가이드 파일, 준수 규칙 한 줄)` 형식으로 한 행만 추가.

---

## Drift-Free Essentials

아래는 skill 변경에 따라 흔들리지 않는 **불변 사실**만:

### Workspace assumption (대 전제)

**모든 skill은 Claude가 _프로젝트 루트에서 실행됨_을 전제**. `.claude_reports/`는 현재 dir에 생성. 외부 cross-project 작업은 `cd <other>` 후 별도 세션. `--refs <folder>` 같은 외부 폴더 flag는 **family에서 제거됨** — 모든 입력은 `.claude_reports/` 하위 영속 산출물에서 implicit 자동 발견 (필요 시 `analyze-project`로 사전 분석).

### 산출물 위치

| Skill | Artifact Dir |
|---|---|
| `analyze-project --mode code` | `.claude_reports/analysis_project/code/` |
| `analyze-project --mode paper` | `.claude_reports/analysis_project/paper/` |
| `analyze-project --mode doc` | `.claude_reports/analysis_project/doc/{name}/` |
| `autopilot-research` | `.claude_reports/research/{topic}/` |
| `autopilot-doc` | `.claude_reports/documents/{YYYY-MM-DD}_{name}/` |
| `autopilot-code` | `.claude_reports/plans/{YYYY-MM-DD}_{name}/` |
| `autopilot-refine` | (대상 artifact를 read+write, 자체 폴더 X) |

### Scope 경계 (절대 침범 금지)

- `autopilot-research` = **markdown 분석 리포트만**. 슬라이드 본문, paper draft, code, PPTX 절대 만들지 말 것.
- `autopilot-doc` = **strategy + draft (markdown만)**. PPTX export 안 함, 코드 실행 안 함.
- `autopilot-code` = **code + tests + plan/dev logs**. paper/slide 작성 안 함.

산출물이 두 pipeline에서 중복되거나, 정의된 산출물 외 추가 생성하면 즉시 멈추고 사용자에게 확인.

### 공통 플래그 패턴

- ~~`--refs <folder>`~~ — **family에서 제거됨 (2026-05-08)**. 입력은 `.claude_reports/{analysis_project,research}/*`에서 implicit 자동 발견.
- `--qa light|standard|thorough` — QA 강도.
- `--from <stage>` — pipeline 재개 (`pipeline_state.yaml` 기반).
- `--user-refine` (doc 전용) — refine 시점 일시정지.

### 자주 빠지는 함정

- pipeline이 sub-skill을 이미 호출 중인데 사용자/Claude가 sub-skill을 또 부르기 → 중복/덮어쓰기.
- artifact_dir 경로 오타 (research vs documents vs plans).
- PPTX 자동 생성 시도 (presentation mode는 markdown만; PPTX는 사용자 수동).
- `--qa thorough`를 1차 시도부터 사용 (시간/비용 큼; standard부터).

---

## 운영 정책

- 본 CLAUDE.md를 **확장하지 말 것**. skill 추가/변경은 README.md(자동 동기화)에 반영되고, 본 파일은 그 표지로만 유지.
- 본 파일을 업데이트할 시점: (a) source-of-truth 위치가 바뀔 때, (b) artifact_dir 컨벤션이 바뀔 때, (c) scope 경계가 근본적으로 변경될 때, (d) **도메인 트리거 표에 새 행 추가/제거**할 때, (e) **응답 원칙 (§1~§5) 이 추가·변경**될 때. 그 외엔 README.md만 sync.
