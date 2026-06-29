# MANUAL — agent harness 전체 흐름

> **앞층(사용자용 지도, 2026-06-23 신설).** 이 한 파일로 세팅 전체가 _어떻게 짜여 돌아가는가_ 를 4축으로 본다. 정밀 규칙·정의는 _뒤층_ 문서(끝 §5 reference)에 있고, 여기선 **진입점·요약·링크**만 — 흐름을 잃지 않게(정의 복사 X, 링크만).

## 0. 30초 지도

이 세팅은 _프롬프트와 로컬 도구로 재구성한 에이전트 하네스_ 다. 자연어로 부르면 메인 에이전트가 컨텍스트(`cwd`·artifact root·발화)를 읽어 알맞은 **capability 파이프라인**을 고른다. 산출물은 새 표준 `.agent_reports/` 에 쌓이고, 기존 `.claude_reports/` 도 legacy alias 로 읽는다. **hook** 이 순서·안전을 결정론으로 강제하며, 세션 밖에선 **loop** 가 점검·정리한다. 사용자는 _운전자_ — 자연어로 부르고 방향을 정한다.

네 축으로 읽는다:

| 축 | 무엇 | 한 줄 |
|---|---|---|
| **① 작업 워크플로우** | 발화 → 파이프 → 산출물 | 가장 자주 보는 축 — 무엇을 부르면 무엇이 되나 |
| **② 시스템 구조** | skills·agents·hooks·loops·memory | 부품과 그 관계 |
| **③ 운영·자동화** | 세션 밖 루프 | 당직·연수·모의훈련·일지가 언제 돌고 뭘 하나 |
| **④ 원칙 ↔ 구현** | 에이전트 엔지니어링 원칙 | 원칙이 어느 파일·기능으로 강제되나 |

---

## ① 작업 워크플로우 — 발화에서 산출물까지

자연어로 부르면 메인 에이전트가 옵션을 조립·컨펌하고 파이프라인을 실행한다. **하드 순서 게이트**(우회 불가): `research/analyze → spec → code`(문서는 `research/analyze → draft → refine → apply`) — 앞 단계 산출물 없이는 다음 단계로 못 간다(`hooks/artifact-guard.sh` 강제).

**4 트랙** (작업 본질에 맞춰 고른다):

```
📄 문서        analyze-project / autopilot-research  →  autopilot-draft  →  autopilot-refine ↻  →  autopilot-apply
🔬 연구·실험   analyze / autopilot-research  →  autopilot-spec ↻  →  autopilot-code ↻  →  autopilot-lab ↻
💻 앱          autopilot-spec ↻  →  autopilot-design  →  autopilot-code ↻  →  autopilot-ship ↻
📦 라이브러리  analyze-project  →  autopilot-spec ↻  →  autopilot-code ↻
```

각 단계는 _자연어 한 줄_ 로 부른다(예: "이 결과로 보고서 만들어줘" → `autopilot-draft`). 메인이 cwd·발화를 보고 옵션을 조립해 한 번 컨펌 뒤 실행한다. `↻` = 검토·정정 반복(refine·code·lab 등).

- **산출물**: 각 파이프는 artifact root(`.agent_reports/`, legacy `.claude_reports/`)의 `<영역>/` 에 쌓인다 — `research/`·`analysis_project/`·`documents/`·`spec/`·`plans/`·`experiments/`. 코드는 `spec/`(청사진, 항상 최신) + `plans/<date>_<slug>/`(작업 사이클) 두 갈래.
- **사후 수정**: spec-backed 프로젝트는 즉석 직접 편집이 아니라 _기존 산출물 파악 → spec-drift 체크 → autopilot-code_ 경로를 탄다.
- **모드 신호**: 매 프롬프트 statusline 에 📌tracked(파이프 경유) / ⚡untracked(`/track`, 직접 편집 자유)가 뜬다.

→ 라우팅 정밀 규칙·발화 매핑·spec mode·서브에이전트 분기: [`core/WORKFLOW.md`](core/WORKFLOW.md) · 호출 패턴·응답 규율: runtime adapter bootstrap (현재 Claude Code: [`adapters/claude/CLAUDE.md`](adapters/claude/CLAUDE.md) §0)

---

## ② 시스템 구조 — 부품과 관계

```
자연어 발화
   │  (메인 에이전트가 라우팅)
   ▼
skills/ (28)  ──호출──►  roles/ (8)         ◄── 팀별 모드(roles/modes/)
                       └ Claude adapter: adapters/claude/agents/
   │  파이프라인          기획·개발·품질·연구·자료·디자인·편집·external adversary
   ▼
.agent_reports/   ◄──강제── hooks/ (생성순서·git상태·spec게이트·메모리가드)
   산출물                         │
   │                              ▼
   └──────────────────►  memory/ (mem.py DB store)  ◄── 세션 주입/회수
                                  ▲
세션 밖:  loops/ (당직·연수·모의훈련·일지) ──점검·정리──┘
```

- **skills** = 동사(일하기). autopilot-\* 10(추적형 파이프) + 사전분석 2(analyze-project/-user) + code·draft·design 가족 + 운영 3(audit·post-it·sync-skills).
- **roles** = skill 이 일을 맡기는 팀 의미(개발·품질관리·연구·자료·디자인·편집 등). Claude Code 에서는 `adapters/claude/agents/`가 이를 native Agent 파일로 실현한다. 모드 페르소나는 `roles/modes/`.
- **hooks** = 결정론 가드. 에이전트 판단 대신 코드가 강제한다 — 생성 순서·git 상태·spec 게이트·메모리 write 경로.
- **memory** = 단기(working)·장기(durable)·프로필을 하나의 DB(`memory.db`)로 묶어 세션 시작에 주입하고 종료에 회수한다.
- **loops** = 부사(언제·얼마나·끝났는지). 세션 밖 cron·headless 로 돈다.

→ skill 카탈로그·agent 표·디렉토리 맵: [`README.md`](README.md) · 산출물 컨벤션: [`core/CONVENTIONS.md`](core/CONVENTIONS.md) §5

---

## ③ 운영·자동화 — 세션 밖 루프

세션 _안_ 은 skill·agent·hook 이, 세션 _밖_ 은 loop 가 맡는다. 루프는 파이프 일을 대신하지 않는다 — _앞(언제 돌릴지)_ 과 _뒤(정리·감시·검증)_ 만 챙긴다.

| 루프 | 형 | 트리거 | 하는 일 |
|---|---|---|---|
| **당직** `oncall` | 시간 | cron 05:37 | 야간 순찰(repo·산출물·루프 생존·dispatch job) — 발견·보고 |
| **일지** `note` | 시간 | cron 05:03 | 전날 산출물 → worklog-board L2 노트화·라우팅 |
| **연수** `study` | 시간 | 일요일 06:17 | 외부 동향 × 현 세팅 대조 → 개선 제안서 |
| **모의훈련** `drill` | 사건 | 지침 _행동규칙_ 수정 후 | fixture 가상 상황에서 행동 회귀 시험·채점 (정기 회귀는 `--sample 2`) |

> 루프 자율성(D-25): _되돌릴 수 있고 명백한_ 일은 무인 처리하고 전수 보고, _판단이 필요한_ 것만 아침 데스크에서 논의한다.

→ 루프 카탈로그·4계층(초·분·시·주)·승격: [`loops/README.md`](loops/README.md)

---

## ④ 원칙 ↔ 구현 — 에이전트 엔지니어링이 어느 파일인가

이 세팅의 설계 원칙이 _추상_ 에 머물지 않고 어느 파일·기능으로 _강제_ 되는지의 대응표:

| 원칙 | 출처 | 구현 메커니즘 |
|---|---|---|
| **Model-agnostic substrate** | DESIGN §0 | 모든 skill = 프롬프트+로컬도구+scaffold (벤더 내장 기능 자급 재구현) |
| **결정론 우선** (판단 최소화) | DESIGN §0.5 | hook(artifact-guard·git-state·spec-gate) · 메모리 write 게이트 — "코드로 강제 가능?"을 먼저 |
| **의미↔규칙 경계 검증** | DESIGN §0.7 | autopilot-spec 저술 + audit + **drill g7** 회귀 3시점 |
| **하드 순서 게이트** | WORKFLOW §0 | `hooks/artifact-guard.sh` (research→spec→code) |
| **git 안전 상태** | OPERATIONS §5.9 | `hooks/git-state-guard.sh` (merge/rebase/detached 편집 deny) |
| **작업 격리·병렬 디스패치** | OPERATIONS §5.10 | worktree `<repo>-wt/<slug>` + `.dispatch/jobs.log` + dispatch-liveness |
| **메모리 2-layer + 결정론 lifecycle** | DESIGN §7 / MEMORY §7 | `mem.py` DB + 메모리 hook 4종 |
| **회귀 자가 시험** | loops §L4 | `loops/drill/` (행동 assert + 토큰 계측) |

→ 아키텍처 원칙 전문: [`core/DESIGN_PRINCIPLES.md`](core/DESIGN_PRINCIPLES.md)

---

## 5. 더 깊이 — 뒤층 문서(정확성 층)

| 문서 | 역할 |
|---|---|
| [`core/CORE.md`](core/CORE.md) · [`adapters/`](adapters/README.md) | 공통 하네스 계약 + 런타임별 adapter 경계 |
| [`INSTALL_LAYOUT.md`](INSTALL_LAYOUT.md) | neutral repo + runtime home symlink projection 절차 |
| [`adapters/claude/CLAUDE.md`](adapters/claude/CLAUDE.md) | 현재 Claude Code adapter 부트스트랩 + 응답 규율 + 라우팅 §0 |
| [`adapters/codex/AGENTS.md`](adapters/codex/AGENTS.md) | Codex adapter 부트스트랩 + core 문서 로드 순서 |
| [`core/WORKFLOW.md`](core/WORKFLOW.md) | 발화→skill 라우팅 코어 |
| [`core/CONVENTIONS.md`](core/CONVENTIONS.md) | QA·산출물 3-tier 등 family 운영 규칙 |
| [`core/OPERATIONS.md`](core/OPERATIONS.md) | git·worktree·dispatch·push 운영 (§5.8~5.11) |
| [`core/MEMORY.md`](core/MEMORY.md) | 통합 기억 시스템 (§7) |
| [`core/DESIGN_PRINCIPLES.md`](core/DESIGN_PRINCIPLES.md) | 아키텍처·행동 원칙 |
| [`README.md`](README.md) | GitHub 외부용 의미 지도 |
| [`loops/README.md`](loops/README.md) | 상시 루프 카탈로그 |

> 앞층(MANUAL)은 _흐름 지도_, 뒤층은 _정확성 출처_. 충돌하면 뒤층이 진실이고, 앞층은 흐름을 잃지 않게 가리키기만 한다.
