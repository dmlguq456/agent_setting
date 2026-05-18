# CLAUDE.md — Session Bootstrap

> 이 파일은 Claude Code 세션 시작 시 **자동 로드**됩니다. 본 문서는 *얇은 부트스트랩* 역할만 하고, 실제 워크플로우 맵 / cheat-sheet / 가이드라인은 **`~/.claude/README.md`**에 있습니다 (sync-skills로 자동 동기화).
>
> **세션 시작 시 필수 행동 (강제)**: 작업 종류·요청 복잡도와 무관하게 **가장 먼저** `Read ~/.claude/README.md`를 실행해 전체 워크플로우 맵·skill/agent 흐름·cheat-sheet를 콘텍스트에 적재한 뒤 사용자 요청에 응답한다. 단순 질문이라도 **예외 없음** — README는 길지 않으며, 흐름을 모르고 답하는 비용이 매번 읽는 비용보다 크다. (이미 같은 세션에서 읽었다면 재독 불필요.)

---

## 응답 1원칙 — 핵심 위주 답변

**답변은 사용자가 어지럽지 않게 핵심 위주로 정리해서 출력하고, 부연설명·디테일은 사용자가 추가로 물을 때 제공한다.** 과도한 요약은 아님 — _불필요한 부연설명을 줄이라는 것_. 예: 정책·구조 질문 → 결론 + 핵심 파일/위치만 / 사용자가 "왜?" "어디에?" 등 후속 질문 시 그제서야 reasoning·layer·예시 확장.

---

## Source of Truth

- **Skills 정의**: `~/.claude/skills/*/SKILL.md` (각 skill invoke 시 자동 로드)
- **Agents 정의**: `~/.claude/agents/*.md`
- **Autopilot family 아키텍처 헌법**: `~/.claude/DESIGN_PRINCIPLES.md` (3-tier separation, interface contract, anti-pattern — autopilot-* skill 설계·재설계 시 참고)
- **Family-wide 운영 규칙**: `~/.claude/CONVENTIONS.md` (QA 5단계 정의 / agent model 표기 / 폐기 flag·name / cross-doc invariants — QA·model·family-wide 작업 시 반드시 참조)
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
| **QA level·agent model·family-wide flag 정의 작업** (SKILL.md / README의 QA 표 작성·수정, agent model 표기, 신규 skill의 `--qa` 옵션 채택, `--refs`/`--format-ref` 같은 폐기 flag 검증 등) | `~/.claude/CONVENTIONS.md` | 정의 wording은 본 문서 §1~§5 그대로 사용. 신규 정의 추가·변경 시 본 문서를 먼저 수정한 후 `/sync-skills`로 다른 곳에 propagate. drift 발견 시 본 문서가 진실의 출처. |
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
- 본 파일을 업데이트할 시점: (a) source-of-truth 위치가 바뀔 때, (b) artifact_dir 컨벤션이 바뀔 때, (c) scope 경계가 근본적으로 변경될 때, (d) **도메인 트리거 표에 새 행 추가/제거**할 때. 그 외엔 README.md만 sync.
