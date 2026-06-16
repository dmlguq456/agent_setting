<div align="center">

# ⚙️ Claude Setting

**Claude Code 워크플로우 — skill·agent·운영 규칙을 한 장으로**

</div>

> **🧬 존재의의 — model-agnostic skeleton.** 이 레포는 _특정 LLM 에 종속되지 않는, 어떤 모델로 갈아타도 동작하는 작업 substrate_ 다. "평생 Claude 만 쓴다는 보장은 없다." 벤더 내장(Claude Design·deep-research 등)이 _지금 더 좋아도_ 우리 온프레미스 구현을 빼지 않는다 — advantage 는 벤더에 묶여 모델 전환 시 증발하지만 우리 골격은 살아남는다. 잘 설계된 내장은 _RE 해서 흡수_(자급 재구현). 단일 출처 = [`DESIGN_PRINCIPLES.md`](DESIGN_PRINCIPLES.md) §0.

<div align="center">

[📌/⚡ 모드](#-작동-방식--tracked--untracked) · [mental model](#-mental-model) · [4 트랙](#-큰-갈래-4-트랙--흐름의-의미) · [Skills](#-skill-카탈로그--의의핵심) · [산출물](#-산출물의-구조적-의미) · [부르는 법](#-부르는-법) · [Agents](#-agents) · [더 깊이](#-더-깊이) · [디렉토리 맵](#%EF%B8%8F-전체-디렉토리-맵)

</div>

---

## 🚦 작동 방식 — 📌 tracked ↔ ⚡ untracked

결정론적으로 강제할 수 있는 건 코드(hook/script/gate/DB)가 맡고, 에이전트 판단은 진짜 비결정 자리에만 쓴다 ([`DESIGN_PRINCIPLES.md §0.5`](DESIGN_PRINCIPLES.md) · [`WORKFLOW.md`](WORKFLOW.md) §0/§7).

| | 📌 tracked (기본) | ⚡ untracked (예외) |
|---|---|---|
| **생성 순서** | 신규 산출물 ← 앞 단계 (hook 차단) | 전부 우회 |
| **모드 신호** | 매 프롬프트 📌 WORKFLOW 따름 (skill 경유) | 매 프롬프트 ⚡ 면제 (직접 자유) |
| **전환** | (기본값) | `/track` 토글 |

**hook 이 hard 차단하는 건 셋** — _신규 산출물 생성 순서_ · _git 위험 상태의 편집_ · _spec 라우팅 계약 게이트_:

- 생성 순서 (자동 scope — `.claude_reports` 보유 프로젝트): 신규 `spec` ← research · 신규 `plan` ← spec · 신규 `documents` ← research. 위반 시 차단 + 권고.
- git 상태 (`git-state-guard`): merge/rebase/cherry-pick 진행 중 repo 의 파일 편집 차단 — 반쯤 머지된 트리를 임의로 굳히는 사고 방지 ([CONVENTIONS](CONVENTIONS.md) §5.9).
- spec-skill-gate (`spec-skill-gate.sh`): spec-backed cwd 에서 spec 변경 스킬이 `prd.md` 등 청사진을 거치지 않고 작업 진입하는 것을 차단 (라우팅 계약 게이트, settings.json 등록).

기존 산출물 _편집_ · 소스 코드 · `user_profile` · post-it 메모 (DB working 레코드) 는 convention (소유 스킬·autopilot-code 권장, 비차단). 작업 유도는 라우팅 리마인더 몫. statusline 에 📌/⚡ 표시.

---

## 🧭 Mental model

자연어 한 줄로 부르면 메인 Claude 가 컨텍스트 (cwd / `.claude_reports/` 산출물 / 발화) 를 읽어 **skill + 옵션을 조립하고, 자연어 요약으로 컨펌받은 뒤 실행**한다. 사용자는 _운전자_ — 다음 의도만 말하면 된다.

- **autopilot-\*** = 추적형 파이프라인. plan·log 가 `.claude_reports/` 에 누적돼 흐름이 남는다. 큰 작업·반복 작업용.
- **직접 처리** = plan/log 안 남는 가벼운 일 (throwaway). 단, `spec/` 잡힌 프로젝트의 사후 수정은 거의 다 `--qa quick` 파이프로 _산출물 남기며_ 진행한다 — 신규 산출물 생성 순서만 [📌 tracked](#-작동-방식--tracked--untracked) hook 강제, 편집·코드는 convention ([CLAUDE](CLAUDE.md) §0 · [WORKFLOW](WORKFLOW.md) §7).
- 입력은 외부 flag 없이 **`.claude_reports/` 영속 산출물에서 자동 발견**. cross-project 는 `cd <other>` 후 별도 세션. 코드 본작업은 작업 브랜치(worktree 격리), 기억 추가는 외부에서 자동·삭제는 메인이 직접 ([`CONVENTIONS.md §7`](CONVENTIONS.md) · [`DESIGN_PRINCIPLES.md §7`](DESIGN_PRINCIPLES.md)).

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

무엇을 부르면 무엇이 되나(자연어 발화→동작) — 여기가 사용자 API 표면이다. 부르는 법은 [§7](#-부르는-법), 옵션 세부는 각 SKILL.md.

| Skill | 의의 — 왜 있나 / 핵심 |
|---|---|
| [`analyze-project`](skills/analyze-project/SKILL.md) | 모든 트랙의 _사전 분석_. code/paper/doc 자료를 `analysis_project/` 에 영속화 — 다운스트림 skill 의 입력 source |
| [`autopilot-research`](skills/autopilot-research/SKILL.md) | 어느 트랙이든 공통 _분야 조사_. academic/technology/market 3 mode 보고서. 실제 문서·코드 생성은 다운스트림이 담당 |
| [`autopilot-spec`](skills/autopilot-spec/SKILL.md) | 코드 _청사진 + skeleton_ 일반화 entry (app/library/api/cli/research) + **update 모드** (기존 `prd.md` 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). 만들 _것 자체_ 결정 자리라 사용자 비중 큼 — 중간 컨펌 default |
| [`autopilot-code`](skills/autopilot-code/SKILL.md) | 코드 _작업_ 일반 (라이브러리·연구·앱 모두). dev/debug. `spec/` 발견 시 spec mode 별 분기 자동. `--qa quick` = 소규모 잡일 경량 tier (로그 남김) |
| [`autopilot-lab`](skills/autopilot-lab/SKILL.md) | _빠른 실험 prototype_. 무거운 학습은 사용자가 실행, lab 은 `setup`(학습 세팅) / `eval`(평가·분석·`--report` 시 정식 보고서[prose→draft / 음성·미디어는 재생 HTML]) 로 앞뒤를 도움. `--parent` 계보로 fine-tune·재평가, `_RUNLOG`(⏳→✅) 누적. 졸업은 autopilot-code |
| [`autopilot-design`](skills/autopilot-design/SKILL.md) | _시각_ 산출물 (UI·슬라이드·다이어그램·아이콘). Design MCP(`~/.claude/tools/design-mcp`)로 렌더→view_image→수정 루프 + verifier 게이트(콘솔·레이아웃) — Claude-Design 패리티. scaffold(deck_stage 등)·converters(PDF/PPTX/번들)·standalone `preview.html` |
| [`autopilot-ship`](skills/autopilot-ship/SKILL.md) | 앱 _배포 셋업_ 안내 (호스팅·CI/CD·env·domain). 실제 배포 명령은 사용자 직접. 첫 setup·재호출 자리 |
| [`autopilot-draft`](skills/autopilot-draft/SKILL.md) | 문서 _초안_ (paper/presentation/doc, markdown). 산출물은 최종 문서가 아니라 _적용용 cheatsheet(plan)_ |
| [`autopilot-apply`](skills/autopilot-apply/SKILL.md) | cheatsheet 를 `.claude_reports/` _밖_ 실제 소스 (`main.tex`) 에 git 위로 적용 + 컴파일 검증. draft 의 apply 팔 (현재 LaTeX 한정) |
| [`autopilot-refine`](skills/autopilot-refine/SKILL.md) | doc/research markdown _사후 정정_. prompt + memo 통합 entry, 버전·이력 자동 관리 |
| [`audit`](skills/audit/SKILL.md) | 산출물 _읽기 전용_ multi-aspect 점검 + 기본 auto-fix dispatch. refine 이 _수정 흐름_ 이면 audit 은 _점검 흐름_ |
| [`analyze-user`](skills/analyze-user/SKILL.md) | cross-project 사용자 산출물 분석 → DB `type=profile` 레코드 (`mem profile <stem>`) 갱신. 모든 sub-agent 의 default 자료라 QA adversarial 고정 |
| [`autopilot-note`](skills/autopilot-note/SKILL.md) | 산출물·git log 변화를 L2 노트로 만들어 L1 worklog 카드에 routing (2-Layer — 연결은 제안만, 확정은 `/triage` 사용자 몫). 일일 digest 누적, idempotent (cron 친화 `--qa light`) |
| [`post-it`](skills/post-it/SKILL.md) | 사용자 통제 _임시 포스트잇_ 메모. `--scope project`(DB working 레코드) / `--scope user`(profile 레코드 `## 사용자 수동 메모` 블록). `sweep`=졸업·stale prune · `promote`=user 메모 구조화 졸업 — 영구 누적 X |
| [`sync-skills`](skills/sync-skills/SKILL.md) | 본 README 를 SKILL.md·agent 정의로부터 재생성·동기화 + cross-doc invariant·이름 drift 검사 + 에이전트 매뉴얼 동기 검토 제안 |

> sub-skill 은 autopilot 내부 자동 호출 (사용자가 직접 안 부름): code 가족 (`code-plan`/`-refine`/`-execute`/`-test`/`-report`) · draft 가족 (`draft-strategy`/`-refine`) · design 가족 (`design-init`/`-refs`/`-tokens`/`-components`/`-review`/`-handoff`). (spec 은 `autopilot-spec` 본문이 mode 무관 직접 처리 — 별도 sub-skill 없음.)

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

**통합 기억 — `~/.claude/memory/` (store, P10)** — 흩어졌던 단기(post-it)·장기(auto-memory)·프로필(user_profile) 3 면을 _하나의 store_ 로 통합. SQLite `memory.db`(진실원천 SoT, FTS5 내장) + `dump.jsonl`(결정론적 텍스트 mirror, git추적) — **전용 private repo `claude-memory`** 로 분리(config repo 에선 `memory/` gitignore). 레코드 = tier(working/durable) × scope(project/global) × type. **store 가 세션 주입의 source** — SessionStart hook `mem inject` 이 현 cwd 기억(단기+장기+사용자특성)을 자동 주입, SessionEnd `mem sync` 가 회수, `mem recall`(=`recall.sh`)이 store+세션 FTS 회상. **(C) 세션 자동 distillation** — 외부 detached distiller 가 세션 delta 를 추려 `mem add`; 트리거는 turn-counter hook(N턴) + SessionEnd 공유 marker, distiller 는 판단만 하고(도구 0) dispatch 스크립트가 JSON-lines 검증 후 실행(판단↔실행 분리). `MEM_DISTILL_ENABLE=1` 일 때만 분사(off 면 완전 no-op), 현재 켜져 있다. **(D) 결정론-first lifecycle** — 회상 신호어 감지 시 `mem-recall-inject` hook 이 `mem recall` 결과를 additionalContext 에 자동 주입; 정리 후보는 `mem inject` 로 노출해 메인이 그 자리에서 consolidate/prune/graduate. **추가(가역)는 외부에서 자동·삭제(비가역)는 메인이 직접**. 상세 → [`CONVENTIONS §7`](CONVENTIONS.md) · `tools/memory/`.

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
| [품질관리팀](agents/qa-team.md) | opus (light: sonnet) | QA — code-review/plan-review/test(+5b 런타임 관찰)/ml-debug/data-curate/security-review (read-only) |
| [연구팀](agents/research-team.md) | opus (fact-check·claim-verify: sonnet) | plan-review(paper-grounding)/research-survey/fact-check/claim-verify(adversarial 외부 진위) |
| [자료팀](agents/material-team.md) | opus | 자료 수집·시각·분석 — browser-fetch/pdf-extract/web-image-search/figure-gen/data-script |
| [디자인팀](agents/design-team.md) | opus (verifier: sonnet) | 시각 산출물 — maker (제작) / critic (6축 품질 비평 — render 후 결과 + render 전 UI plan-review) / verifier (독립 컨텍스트 깨짐 게이트). 모두 Design MCP 렌더 |
| [편집팀](agents/editorial-team.md) | opus | 사용자 향 문서 — translate/polish/review |
| [codex-review-team](agents/codex-review-team.md) | Codex CLI (GPT-5) + opus | 외부 hostile reader 관점 review (adversarial 자동) |

**직접 호출** — 추적 안 남아도 되는 단발 작업은 `Agent(개발팀)` / `Agent(연구팀)` 등으로 autopilot 우회. plan/log 가 필요하면 autopilot 으로. 각 agent 의 (`mem profile <stem>`) aspect 매트릭스는 → [`user_profile/README.md`](user_profile/README.md) (single source).

---

## 📚 더 깊이

| 문서 | 내용 |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | 응답 원칙 §1~§8 · §6 autopilot 호출 룰 · 도메인 트리거 · Drift-Free Essentials |
| [`CONVENTIONS.md`](CONVENTIONS.md) | QA 5단계 정의 · agent model · 산출물 컨벤션 · cross-doc invariants (family-wide 단일 출처) |
| [`WORKFLOW.md`](WORKFLOW.md) | 4 트랙 체이닝 청사진 · 호출 예시 · 서브에이전트 분기 · 폴더 구조 |
| [`DESIGN_PRINCIPLES.md`](DESIGN_PRINCIPLES.md) | autopilot 아키텍처 설계 원칙 |
| [`user_profile/README.md`](user_profile/README.md) | cross-project 사용자 프로필 6 aspect · agent 참조 매트릭스 |
| `hooks/` · `utilities/` · `tools/` · `scaffolds/` · `statusline.sh` | **harness** — `artifact-guard.sh`(산출물·순서 강제) · `git-state-guard.sh`(merge/rebase 중 편집 차단) · `workflow-guard-hook.sh`(매 프롬프트 모드 신호 📌따름/⚡면제 + flag GC; WORKFLOW·post-it 읽기는 지침) · `design-postwrite.sh`(design HTML 저장 시 콘솔 자동 체크) · `spec-skill-gate`/`spec-read-marker`(spec 라우팅 게이트) · `tools/design-mcp`(시각 검증 MCP) · `tools/memory/mem.py`(통합 기억 store·CLI) + SessionStart `mem inject`/SessionEnd `mem sync` + **메모리 hook 4종**(`builtin-memory-guard`·`mem-recall-inject`·`mem-turn-nudge`·`mem-distill-dispatch` — 내장메모리 차단·회상 자동주입·distiller 트리거·dispatch, [§7](CONVENTIONS.md)) · `scaffolds/`(deck_stage 등 디자인 scaffold) · `statusline.sh`(📌/⚡·context 막대) · `/track` 토글. [📌/⚡ 모드](#-작동-방식--tracked--untracked) |
| [`loops/README.md`](loops/README.md) | **상시 루프** (세션 밖 cron·headless) — **당직**(`oncall`, 시간형 05:37 순찰·보고) · **일지**(`note`, 시간형 05:03 산출물→worklog-board L2 노트화 — cron runner 는 worklog-board) · **연수**(`study`, 시간형 일요일 06:17 외부 동향→제안) · **모의훈련**(`drill/`, 사건형 — 지침 수정 후 행동 회귀 시험) · 후보 backlog. 모두 보고·제안에서 멈춘다 (merge 만 Claude 선별 책임 — CONVENTIONS §5.10) |

---

## 🗺️ 전체 디렉토리 맵

```text
~/.claude/
├── CLAUDE.md               세션 부트스트랩 — 라우팅 §0 + 응답 규율 (매 세션 자동 로드)
├── WORKFLOW.md             4트랙 라우팅 코어 (tracked 계약 §0·사후 수정 §7, on-demand)
├── CONVENTIONS.md          family 운영 규칙 단일 출처 — QA 5단계·산출물 3-tier·git 가드 §5.8~5.10
├── DESIGN_PRINCIPLES.md    autopilot 아키텍처 철학 (model-agnostic skeleton)
├── README.md               본 문서 — GitHub 의미 지도 (sync-skills 가 재생성)
├── settings.json           harness 설정 — hook 등록·권한
├── statusline.sh           상태줄 (📌/⚡ 모드·git·context 막대)
│
├── skills/                 작업 매뉴얼 28 — 폴더당 SKILL.md (단일 출처)
│   ├── [entry 파이프]      autopilot-research(분야조사) · -spec(청사진·skeleton) · -code(코드 작업)
│   │                       · -lab(실험 setup/eval) · -draft(문서 초안) · -apply(cheatsheet→실소스+컴파일)
│   │                       · -refine(markdown 정정) · -design(시각 파이프) · -ship(배포 셋업)
│   │                       · -note(산출물→worklog 노트화)
│   ├── [사전 분석]         analyze-project(코드·논문·자료 영속화) · analyze-user(사용자 프로필, adversarial 고정)
│   ├── [code 가족]         code-plan(계획) · code-refine(메모 반영) · code-execute(실행+Safety commit)
│   │                       · code-test(단계 검증) · code-report(변경 보고서) — autopilot-code 내부 자동 호출
│   ├── [draft 가족]        draft-strategy(전략) · draft-refine(메모 반영) — autopilot-draft 내부
│   ├── [design 가족]       design-init·-refs·-tokens·-components·-review·-handoff — autopilot-design 내부
│   └── [운영]              audit(읽기 전용 점검) · post-it(세션 간 메모) · sync-skills(본 README 동기화)
│
├── agents/                 팀 8 — 세션 안 서브에이전트 (agent-modes/ 의 모드 페르소나와 짝)
│   ├── dev-team            개발팀 — backend/frontend·refactor·new-lib 모드
│   ├── plan-team           기획팀 — plan 문서 작성·정정 (code-plan/-refine 이 호출)
│   ├── qa-team             품질관리팀 — code-review·test·plan-review·ml-debug·security (read-only)
│   ├── research-team       연구팀 — plan-review·survey·fact-check·claim-verify (논문 근거)
│   ├── editorial-team      편집팀 — 사용자가 읽는 글 translate·polish·review (번역체 방지)
│   ├── design-team         디자인팀 — maker·critic·verifier (시각 자가검증 루프)
│   ├── material-team       자료팀 — 수집(browser·pdf·웹그림)+가공(figure·표·통계)
│   └── codex-review-team   Codex(GPT) 외부 adversarial 리뷰 — qa adversarial 전용
│
├── agent-modes/            팀별 모드 페르소나 .md (dev / qa / research / editorial / design / material)
├── hooks/                  툴 호출 순간 강제되는 가드
│   ├── artifact-guard      신규 산출물 생성 순서 (spec←research·plan←spec·문서←research)
│   ├── git-state-guard     merge/rebase 중 편집 hard deny (drill g2 가 잡은 구멍)
│   ├── spec-skill-gate/spec-read-marker  spec-backed 프로젝트 라우팅 게이트 (prd.md 실독 마커 짝)
│   ├── design-postwrite    design HTML 저장 시 콘솔 자동 체크 · herdr-agent-state
│   └── [메모리 가드 ×4]   builtin-memory-guard·mem-recall-inject·mem-turn-nudge·mem-distill-dispatch (내장메모리 차단·회상 자동주입·distiller 트리거·dispatch)
│
├── loops/                  세션 밖 상시 루프 (cron·headless)
│   ├── oncall.md·.sh       당직 — 매일 05:37 순찰 6항목, 보고서 notes/oncall/ (파일 자체가 heartbeat)
│   ├── study.md·.sh        연수 — 시간형 학습·정리 루프
│   ├── drill/              모의훈련 — 지침 수정 후 행동 회귀 시험
│   │   ├── run.sh          러너 — 행동 assert + 토큰·비용 계측 + FAIL 자동 진단서
│   │   ├── judge.md        응답규율 2차 채점 prompt (RUN_JUDGE=1)
│   │   ├── cases/g0~g6     g0 세팅세금 측정 · g1 죽은브랜치 · g2 merge중STOP · g3 main직접금지
│   │   │                   · g4 spec게이트 · g5 생성순서차단 · g6 worktree_dispatch
│   │   └── results/        run 별 성적표·transcript·진단서 (+ metrics.csv 추세)
│   └── README.md           루프 카탈로그 4종(당직·일지[note, runner=worklog-board]·연수·모의훈련)·4계층 (단일 출처)
│
├── .claude_reports/        스킬셋 자기개선 산출물 — 이 repo 만 예외로 커밋 (research·audit·plans 이력 = 자산, §5.1 예외)
├── user_profile/           cross-project 사용자 성향 6 aspect (figure·writing·발표·분석·도메인·코딩) — 통합 store 에 profile tier 로 mirror
├── memory/                 통합 기억 store → 전용 repo claude-memory (memory.db SoT + dump.jsonl mirror, gitignore) — 세션 주입 source (§7)
├── tools/                  자체 도구 — design-mcp (시각 자가검증 MCP) · memory (통합 기억 mem CLI) · web-bundle
├── scaffolds/              디자인 재사용 골격 (deck_stage 등)
├── utilities/              보조 스크립트 (workflow-guard-hook · extract_web_figures)
├── commands/               slash 명령 정의 (/track 등)
├── keybindings.json        키바인딩
│
└── (backups · cache · debug · downloads · file-history · ide · paste-cache · plugins ·
     projects · sessions · session-env · shell-snapshots · tasks — harness 런타임 자동 생성, 손대지 않음)
```

> 작업 산출물은 여기가 아니라 각 프로젝트의 `.claude_reports/` (per-project) 와 위 `user_profile/` (cross-project) 에 쌓인다 — [§산출물](#-산출물의-구조적-의미).

### 🔁 동기화

- `/sync-skills` — 본 README 갱신 · `/sync-skills --check` — drift 확인만

GitHub: [dmlguq456/claude_setting](https://github.com/dmlguq456/claude_setting)
