<div align="center">

# ⚙️ Claude Setting

**Claude Code 워크플로우 — skill·agent·운영 규칙을 한 장으로**

[📌/⚡ 모드](#-작동-방식--tracked--untracked) · [mental model](#-mental-model) · [4 트랙](#-큰-갈래-4-트랙--흐름의-의미) · [Skills](#-skill-카탈로그--의의핵심) · [산출물](#-산출물의-구조적-의미) · [부르는 법](#-부르는-법) · [Agents](#-agents) · [더 깊이](#-더-깊이)

</div>

---

## 🚦 작동 방식 — 📌 tracked ↔ ⚡ untracked

산출물 흐름·순서를 hook 이 강제하는 기본 모드. 계약 본문은 [`WORKFLOW.md`](WORKFLOW.md) §0/§7.

| | 📌 tracked (기본) | ⚡ untracked (예외) |
|---|---|---|
| **생성 순서** | 신규 산출물 ← 앞 단계 (hook 차단) | 전부 우회 |
| **모드 신호** | 매 프롬프트 📌 WORKFLOW 따름 (skill 경유) | 매 프롬프트 ⚡ 면제 (직접 자유) |
| **전환** | (기본값) | `/track` 토글 |

**hook 이 hard 차단하는 건 _신규 산출물 생성 순서_ 뿐** (자동 scope — `.claude_reports` 보유 프로젝트):

- 신규 `spec` ← research · 신규 `plan` ← spec · 신규 `documents` ← research. 어기면 차단 + 권고.

기존 산출물 _편집_ · 소스 코드 · `user_profile` · `post-it.md` 는 convention (소유 스킬·autopilot-code 권장, 비차단). 작업 유도는 라우팅 리마인더가 맡는다. statusline 에 📌/⚡ 표시.

---

## 🧭 Mental model

자연어 한 줄로 부르면 메인 Claude 가 컨텍스트 (cwd / `.claude_reports/` 산출물 / 발화) 를 읽어 **skill + 옵션을 조립하고, 자연어 요약으로 컨펌받은 뒤 실행**한다. 사용자는 _운전자_ — 다음 의도만 말하면 된다.

- **autopilot-\*** = 추적형 파이프라인. plan·log 가 `.claude_reports/` 에 누적돼 흐름이 남는다. 큰 작업·반복 작업용.
- **직접 처리** = plan/log 안 남는 가벼운 일 (throwaway). 단, `spec/` 잡힌 프로젝트의 사후 수정은 거의 다 `--qa quick` 파이프로 _산출물 남기며_ 진행한다 — 신규 산출물 생성 순서만 [📌 tracked](#-작동-방식--tracked--untracked) hook 강제, 편집·코드는 convention ([CLAUDE](CLAUDE.md) §0 · [WORKFLOW](WORKFLOW.md) §7).
- 입력은 외부 flag 없이 **`.claude_reports/` 영속 산출물에서 자동 발견**. cross-project 는 `cd <other>` 후 별도 세션.

> 본 문서는 _의미 지도_ 다. 옵션 spec·trigger 룰·QA 정의 같은 운영 디테일은 각 SKILL.md 와 [`CONVENTIONS.md`](CONVENTIONS.md) · [`CLAUDE.md`](CLAUDE.md) 가 단일 출처 — 여기서 중복하지 않고 링크한다.

---

## 🌳 큰 갈래 4 트랙 — 흐름의 의미

작업 종류가 흐름을 정한다. 이름이 문서용인지 코드용인지 헷갈리면 _순서_ 로 보면 분명하다. (`↻` = 반복 자리)

### 📄 문서

```text
analyze-project / autopilot-research  →  autopilot-draft  →  autopilot-refine ↻  →  autopilot-apply
```

자료를 영속화한 뒤 _markdown 초안·cheatsheet_ 를 만들고, 정정을 반복한 끝에 실제 `main.tex` 같은 소스에 반영·컴파일한다. draft 산출물은 최종 문서가 아니라 _적용용 plan_ 이고, 실제 소스 반영은 사용자가 직접 하거나 `autopilot-apply` 가 맡는다 (초안 _생산_ 과 소스 _적용_ 의 분리).

### 🔬 연구·실험

```text
analyze-project / autopilot-research  →  autopilot-spec ↻  →  autopilot-code ↻  →  autopilot-lab ↻
```

자료 → 청사진·skeleton (외부 ref repo fetch·ckpt 사전 검증) → baseline 학습 가능 코드 완성 → variation 실험 반복. `autopilot-lab` 은 `setup`(학습 세팅) / `eval`(완료 ckpt 평가·분석) 2 모드로 실험 단위 폴더를 강제해 _덮어쓰기·휘발_ 을 막고, 직전 실험의 summary 가 다음 실험의 input 이 된다 (`--parent` 로 fine-tune·재평가 계보 연결).

> **곁가지 잡일**(데이터 split·log 파싱·metric·통계)은 lab 아니라 `autopilot-code --qa quick`. lab 은 학습 실험 전용.

### 💻 앱

```text
autopilot-spec ↻  →  autopilot-design  →  autopilot-code ↻  →  autopilot-ship ↻
```

PRD·skeleton → (UI 있으면) 시각 사이클 → 기능 구현 반복 → 마지막에 배포 셋업. `autopilot-ship` 은 _첫 setup_ 자리고 이후 push 가 자동 deploy 하므로 매번 부르지 않는다.

### 📦 라이브러리·CLI

```text
analyze-project  →  autopilot-spec ↻  →  autopilot-code ↻
```

기존 코드를 분석해 공개용 청사진을 잡고 정돈한다. 연구·실험 트랙의 _졸업 자리_ 와 이어진다.

> **점검·정정은 모든 트랙 공통, 사후** — `audit` (읽기 전용 점검) · `autopilot-refine` (markdown 정정) · `autopilot-apply` (cheatsheet → 실제 소스).
> **코드 트랙 사후 수정** — `spec/` 잡힌 프로젝트의 수정·기능 요청은 _기존 산출물 파악 → spec-drift 체크 (`autopilot-spec` update) → `autopilot-code`_ 순서 (spec→dev 하드 원칙 — 생성 순서 hook 강제, 편집은 convention). 상세 → [WORKFLOW](WORKFLOW.md) §7 · [CLAUDE](CLAUDE.md) §0.
> **사용자 프로필은 cross-project** — `analyze-user` · `post-it --scope user` 가 `~/.claude/user_profile/` 를 만들고, 모든 트랙이 작업 시작 자리에서 default 로 참조한다.

체이닝 청사진·서브에이전트 분기·호출 예시는 → [`WORKFLOW.md`](WORKFLOW.md).

**이름 읽는 법** — prefix·동사로 도메인 구분: `analyze-*` 사전 분석 · `autopilot-research` 분야 조사 · `autopilot-draft`/`-apply` 문서 초안·적용 · `autopilot-refine` markdown 정정 · `autopilot-spec`/`-code`/`-lab` 코드 청사진·작업·실험 · `autopilot-design` 시각 · `audit` 읽기 전용 점검.

---

## 📋 Skill 카탈로그 — 의의·핵심

| Skill | 의의 — 왜 있나 / 핵심 |
|---|---|
| [`analyze-project`](skills/analyze-project/SKILL.md) | 모든 트랙의 _사전 분석_. code/paper/doc 자료를 `analysis_project/` 에 영속화 — 다운스트림 skill 의 입력 source |
| [`autopilot-research`](skills/autopilot-research/SKILL.md) | 어느 트랙이든 공통 _분야 조사_. academic/technology/market 3 mode 보고서. 실제 문서·코드 생성은 다운스트림이 담당 |
| [`autopilot-spec`](skills/autopilot-spec/SKILL.md) | 코드 _청사진 + skeleton_ 일반화 entry (app/library/api/cli/research) + **update 모드** (기존 `prd.md` 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). 만들 _것 자체_ 결정 자리라 사용자 비중 큼 — 중간 컨펌 default |
| [`autopilot-code`](skills/autopilot-code/SKILL.md) | 코드 _작업_ 일반 (라이브러리·연구·앱 모두). dev/debug. `spec/` 발견 시 spec mode 별 분기 자동. `--qa quick` = 소규모 잡일 경량 tier (로그 남김) |
| [`autopilot-lab`](skills/autopilot-lab/SKILL.md) | _빠른 실험 prototype_. 무거운 학습은 사용자가 실행, lab 은 `setup`(학습 세팅) / `eval`(평가·분석) 로 앞뒤를 도움. `--parent` 계보로 fine-tune·재평가, `_RUNLOG`(⏳→✅) 누적. 졸업은 autopilot-code |
| [`autopilot-design`](skills/autopilot-design/SKILL.md) | _시각_ 산출물 (UI·슬라이드·다이어그램·아이콘). Design MCP(`~/.claude/tools/design-mcp`)로 렌더→view_image→수정 루프 + verifier 게이트(콘솔·레이아웃) — Claude-Design 패리티. scaffold(deck_stage 등)·converters(PDF/PPTX/번들)·standalone `preview.html` |
| [`autopilot-ship`](skills/autopilot-ship/SKILL.md) | 앱 _배포 셋업_ 안내 (호스팅·CI/CD·env·domain). 실제 배포 명령은 사용자 직접. 첫 setup·재호출 자리 |
| [`autopilot-draft`](skills/autopilot-draft/SKILL.md) | 문서 _초안_ (paper/presentation/doc, markdown). 산출물은 최종 문서가 아니라 _적용용 cheatsheet(plan)_ |
| [`autopilot-apply`](skills/autopilot-apply/SKILL.md) | cheatsheet 를 `.claude_reports/` _밖_ 실제 소스 (`main.tex`) 에 git 위로 적용 + 컴파일 검증. draft 의 apply 팔 (현재 LaTeX 한정) |
| [`autopilot-refine`](skills/autopilot-refine/SKILL.md) | doc/research markdown _사후 정정_. prompt + memo 통합 entry, 버전·이력 자동 관리 |
| [`audit`](skills/audit/SKILL.md) | 산출물 _읽기 전용_ multi-aspect 점검 + 기본 auto-fix dispatch. refine 이 _수정 흐름_ 이면 audit 은 _점검 흐름_ |
| [`analyze-user`](skills/analyze-user/SKILL.md) | cross-project 사용자 산출물 분석 → `user_profile/` 갱신. 모든 sub-agent 의 default 자료라 QA adversarial 고정 |
| [`autopilot-note`](skills/autopilot-note/SKILL.md) | 산출물·git log 변화를 주기적·on-demand 로 worklog 카드(task/project/tech)에 routing. 일일 digest 누적, idempotent (cron 친화 `--qa light`) |
| [`post-it`](skills/post-it/SKILL.md) | 사용자 통제 _임시 포스트잇_ 메모. `--scope project`(cwd post-it.md) / `--scope user`(user_profile aspect). `sweep`=산출물 졸업·stale prune · `promote`=user 메모 구조화 졸업 — 영구 누적 X |
| [`sync-skills`](skills/sync-skills/SKILL.md) | 본 README 를 SKILL.md·agent 정의로부터 재생성·동기화 |

> sub-skill 은 autopilot 내부 자동 호출 (사용자가 직접 안 부름): code 가족 (`code-plan`/`-refine`/`-execute`/`-test`/`-report`) · draft 가족 (`draft-strategy`/`-refine`) · app 가족 (`app-init`/`app-spec`) · design 가족 (`design-init`/`-refs`/`-tokens`/`-components`/`-review`/`-handoff`).

세부 옵션 (`--mode`·`--qa`·`--from`·`--user-refine`) 은 각 SKILL.md 의 `argument-hint`. QA 5단계 (quick/light/standard/thorough/adversarial) 정의는 [`CONVENTIONS.md`](CONVENTIONS.md) §1.

---

## 📦 산출물의 구조적 의미

산출물은 두 축으로 나뉜다 — _현 프로젝트 자료_ 와 _cross-project 사용자 자료_.

**per-project — `<proj>/.claude_reports/`** — 후속 skill 이 자동 발견. `audit` 은 _읽기만_, `autopilot-refine` 은 _read+write_.

| 폴더 | 무엇이 쌓이나 |
|---|---|
| `analysis_project/{code,paper,doc}/` | 사전 분석 |
| `research/{topic}/` | 분야 조사 |
| `documents/{date}_{name}/` | 문서 산출물 |
| `spec/` | 코드 청사진 — prd·stack·design·ship (프로젝트당 한 개, 항상 최신 `prd.md` T1) |
| `plans/{date}_{slug}/` | 작업 사이클 (spec 유무 무관, spec 과 형제) |
| `experiments/{date}_{slug}/` | ML 실험 prototype (`autopilot-lab`) — lab 이 세팅, 사용자가 실행. `_RUNLOG.md` 에 실험당 한 줄 (⏳ 대기 → ✅ 완료 상태) |

**cross-project — `~/.claude/user_profile/`** — `analyze-user` 가 6 aspect 파일을 누적. 모든 트랙·sub-agent 가 작업 시작 자리에서 default 로 Read. 짧은 메모는 `/post-it --scope user <aspect>` 가 같은 파일에 append.

**3-tier 컨벤션** — 한 산출물 폴더 안에서 T1 root (메인 산출물) / T2 named subdir (검토 자료) / T3 `_internal/` (audit·raw·versions) 로 나뉜다. _사용자는 보통 T1 만 보면 된다._ 한 프로젝트는 `spec/`(청사진, 항상 최신) + `plans/`(작업 사이클) 두 형제 bucket 으로 같은 이름에 묶인다.

상세 디렉토리 매핑·폴더 컨벤션은 → [`CONVENTIONS.md`](CONVENTIONS.md) §5·§6.5, [`WORKFLOW.md`](WORKFLOW.md) §4. 산출물 위치·scope 경계·함정은 → [`CLAUDE.md`](CLAUDE.md) "Drift-Free Essentials".

---

## 🗣️ 부르는 법

입구는 두 갈래 — _자연어_ 와 _slash_. 동작은 동일하다.

### (1) 자연어 발화

메인 Claude 가 옵션을 자동 구성하고 **한 줄 요약 + 옵션 펼침 + 선택 근거** 로 컨펌을 묻는다. yes / 수정 ("qa thorough 로", "X 빼고") / cancel. 무응답이면 추천안으로 자율 진행. ceremony 큰 10 개 (autopilot-\* 9 + analyze-user) 만 컨펌 의무, `audit`/`post-it`/`analyze-project` 는 즉시 invoke. 상세 룰은 → [`CLAUDE.md`](CLAUDE.md) §0.

| 사용자 발화 | 메인 Claude 컨펌 (자연어 요약) |
|---|---|
| "ICML camera-ready 마무리 도와줘" | autopilot-draft paper 모드로 camera-ready 본문 다듬기 (qa adversarial — high-stakes) |
| "이 에러 디버그해봐" | autopilot-code debug 모드로 root-cause 분석 + 수정 (qa standard) |
| "diffusion 분야 최근 동향 조사해줘" | autopilot-research academic, depth medium, 최근 1년 (qa thorough) |
| "X 기능 새로 만들어줘" | autopilot-code dev 모드 (spec/ 자리면 spec mode 별 분기 자동) |
| "할 일 앱 만들고 싶어, PRD 부터" | autopilot-spec app 모드 (PRD + 스택 + scaffolding + skeleton) |
| "lr 1e-3 → 3e-4 비교" / "MDTA 빼고 ablation" | autopilot-lab ml 모드 (직전 RUNLOG + similar_models 자동 참조, qa light) |
| "이번 발표 자료 만들어줘" | autopilot-draft presentation 모드로 슬라이드 markdown (qa thorough) |
| "내 figure 스타일 분석해줘" | analyze-user figure — incremental update (qa adversarial 고정) |

### (2) slash 직접 입력

옵션을 명시하거나 컨펌을 건너뛸 때는 slash 를 그대로 친다 — _의도 명시_ 라 곧장 invoke.

```
/autopilot-code   --mode dev|debug "<task>" [--qa ...] [--from <step>]
/autopilot-draft  --mode paper|presentation|doc "<task>" [--qa ...]
/autopilot-refine "<prompt>" [--qa ...] [--memo <file>]
/audit            <artifact> [--scope ...]
/track            현재 프로젝트 📌tracked ↔ ⚡untracked 토글 (harness 차단 on/off)
```

전체 옵션 조합·default·QA 의미는 각 SKILL.md `argument-hint` / `## Usage`.

---

## 🤝 Agents

autopilot-\* 가 내부에서 자동 라우팅하는 전문 팀. 사용자는 보통 이름을 명시하지 않는다.

| Agent | 모델 | 의의 |
|---|---|---|
| [기획팀](agents/plan-team.md) | opus | 구현 plan 문서 작성·갱신 (code-plan/-refine) |
| [개발팀](agents/dev-team.md) | sonnet | 코드 작업 — backend/frontend/refactor/new-lib |
| [품질관리팀](agents/qa-team.md) | opus (light: sonnet) | QA — code-review/plan-review/test/ml-debug/data-curate (read-only) |
| [연구팀](agents/research-team.md) | opus (fact-check: sonnet) | plan-review(paper-grounding)/research-survey/fact-check |
| [자료팀](agents/material-team.md) | opus | 자료 수집·시각·분석 — browser-fetch/pdf-extract/web-image-search/figure-gen/data-script |
| [디자인팀](agents/design-team.md) | opus (verifier: sonnet) | 시각 산출물 — maker (제작) / critic (6축 품질 비평) / verifier (독립 컨텍스트 깨짐 게이트). 모두 Design MCP 렌더 |
| [편집팀](agents/editorial-team.md) | opus | 사용자 향 문서 — translate/polish/review |
| [codex-review-team](agents/codex-review-team.md) | Codex CLI (GPT-5) + opus | 외부 hostile reader 관점 review (adversarial 자동) |

**직접 호출** — 추적 안 남아도 되는 단발 작업은 `Agent(개발팀)` / `Agent(연구팀)` 등으로 autopilot 우회. plan/log 가 필요하면 autopilot 으로.

각 agent 가 작업 시작 자리에서 Read 하는 `user_profile/` aspect 매트릭스는 → [`user_profile/README.md`](user_profile/README.md) (single source).

---

## 📚 더 깊이

| 문서 | 내용 |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | 응답 원칙 §1~§8 · §6 autopilot 호출 룰 · 도메인 트리거 · Drift-Free Essentials |
| [`CONVENTIONS.md`](CONVENTIONS.md) | QA 5단계 정의 · agent model · 산출물 컨벤션 · cross-doc invariants (family-wide 단일 출처) |
| [`WORKFLOW.md`](WORKFLOW.md) | 4 트랙 체이닝 청사진 · 호출 예시 · 서브에이전트 분기 · 폴더 구조 |
| [`DESIGN_PRINCIPLES.md`](DESIGN_PRINCIPLES.md) | autopilot 아키텍처 설계 원칙 |
| [`user_profile/README.md`](user_profile/README.md) | cross-project 사용자 프로필 6 aspect · agent 참조 매트릭스 |
| `hooks/` · `utilities/` · `tools/` · `scaffolds/` · `statusline.sh` | **harness** — `artifact-guard.sh`(산출물·순서 강제) · `workflow-guard-hook.sh`(매 프롬프트 모드 신호 📌따름/⚡면제 + flag GC; WORKFLOW·post-it 읽기는 지침) · `design-postwrite.sh`(design HTML 저장 시 콘솔 자동 체크) · `tools/design-mcp`(시각 검증 MCP) · `scaffolds/`(deck_stage 등 디자인 scaffold) · `statusline.sh`(📌/⚡·context 막대) · `/track` 토글. [📌/⚡ 모드](#-작동-방식--tracked--untracked) |

### 🔁 동기화

- `/sync-skills` — 본 README 갱신 · `/sync-skills --check` — drift 확인만

GitHub: [dmlguq456/claude_setting](https://github.com/dmlguq456/claude_setting)
