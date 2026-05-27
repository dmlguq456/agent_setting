# Skill / Agent / Workflow 시각화 가이드

> 1차 자료 직접 read 후 가공 (2026-05-26). 분석 대상 — `~/.claude/skills/*/SKILL.md` (29), `~/.claude/agents/*.md` (8), `CLAUDE.md` §6, `CONVENTIONS.md` §1.4·§2·§5.4, `README.md` mermaid (참고만), `user_profile/README.md`.
>
> 본 문서는 디자인팀이 추가 질문 없이 SVG 를 그릴 수준의 _구체 가이드_ 다. §1~§6 은 정리된 사실, §7 은 시각화 설계.

---

## §1. Skill 카탈로그

29 skill 을 ceremony tier × 역할로 분류한다. **orchestrator** (사용자 호출 단위) / **sub-skill** (orchestrator 내부 자동) / **meta** (운영) 3 계층.

### §1.1. Orchestrator (사용자 호출 단위) — 13

| skill | category | entry mode | input (auto-discover) | output 폴더 | sub-skill 호출 | agent 호출 |
|---|---|---|---|---|---|---|
| `analyze-project` | 점검·입력 | code / paper / doc | 현 cwd 코드·PDF·doc raw | `analysis_project/{code,paper,doc}/` | — | 연구팀 (classify), 품질관리팀 (code-review cross-check) |
| `analyze-user` | 사용자 분석 | aspect (paper/pres/code/...) | cross-project 사용자 산출물 | `user_profile/0X_*.md` | — | (adversarial 고정 QA) |
| `autopilot-research` | 연구 | academic / technology / market | `analysis_project/paper/` | `research/{topic}/` | — | 연구팀 (survey + fact-check), 자료팀 (페이월 fetch / figure / 수치 카드) |
| `autopilot-spec` | 청사진 | app/library/api/cli/research (+다중/auto) | `research/*`, `analysis_project/code/` | `specs/{name}/` | app-init, app-spec | 개발팀 (new-lib scaffold), 디자인팀 (UI 자리, via autopilot-design) |
| `autopilot-code` | 코드 | dev / debug | `specs/{name}/`, `analysis_project/code/` | `plans/{date}_{name}/` | code-plan, code-refine, code-execute, code-test, code-report | 기획팀 (plan), 연구팀 (plan review), 품질관리팀 (QA·test), 개발팀 (hotfix), 디자인팀 (app UI critic) |
| `autopilot-lab` | 실험 | ml / script / auto | `analysis_project/code/` (conventions·similar) | experiment 단위 폴더 | — | 개발팀 (new-lib scaffold), 품질관리팀 (ml-debug·smoke), 자료팀 (figure-gen) |
| `autopilot-draft` | 문서 | paper / presentation / doc | `analysis_project/{paper,doc}/`, `research/*` | `documents/{date}_{name}/` | draft-strategy, draft-refine | 연구팀 (도메인 review + fact-check), 편집팀 (ko/en mirror), 자료팀 (figure 게이트) |
| `autopilot-apply` | 정정·적용 | latex (default) | `documents/*/draft/` cheatsheet | 실제 source (git branch) | — | — (build/compile gate; reviewer QA 없음) |
| `autopilot-refine` | 정정 | research / doc artifact | `research/*`, `documents/*` | 대상 in-place + `_internal/versions/` | (draft-refine 류 직접) | 연구팀 (fact-check), 편집팀 (style) |
| `autopilot-design` | 디자인 | ui/slide/icon/diagram/mixed | 사용자 ref, `specs/{name}/02_design/` | `designs/{name}/` 또는 `specs/{name}/02_design/` | design-init, design-refs, design-tokens, design-components, design-review, design-handoff | 디자인팀 (maker + critic), 자료팀 (web-image-search ref) |
| `autopilot-ship` | 앱 배포 | (단일) | `specs/{name}/` | `specs/{name}/` deploy_record | — | — (안내만) |
| `audit` | 점검 | auto (plans/research/documents) | `.claude_reports/{plans,research,documents}/*` | `{artifact}/_internal/audit/` | — | 연구팀 (fact-check), 편집팀 (보고서 polish) |
| `notes` | 점검·메모 | project / user | — | `NOTES.md` 또는 `user_profile/0X_*.md` | — | — |

### §1.2. Sub-skill (orchestrator 내부 자동 호출) — 15

| sub-skill | 부모 orchestrator | 매핑 stage | agent 호출 |
|---|---|---|---|
| `code-plan` | autopilot-code | Step 1 (`--from plan`) | 기획팀 + 품질관리팀 (plan-review) |
| `code-refine` | autopilot-code | Step 2 (`--from refine`) | 기획팀 + 품질관리팀 + 연구팀 (memo) |
| `code-execute` | autopilot-code | Step 3 (`--from execute`) | 품질관리팀 (code-review) |
| `code-test` | autopilot-code | Step 4 (`--from test`) | 품질관리팀 2× parallel (test 모드), 개발팀 (hotfix) |
| `code-report` | autopilot-code | Step 5 (`--from report`) | 품질관리팀 (sonnet), 편집팀 (polish) |
| `draft-strategy` | autopilot-draft | Step 2 (`--from strategy`) | 연구팀 (review + fact-check) |
| `draft-refine` | autopilot-draft | Step 3·5 (`--from strategy-refine\|draft-refine`) | 연구팀 (memo + fact-check) |
| `app-init` | autopilot-spec | cold start Phase 0 | — |
| `app-spec` | autopilot-spec | PRD Phase | 기획팀 (옵션) |
| `design-init` | autopilot-design | Phase 0 | — |
| `design-refs` | autopilot-design | Phase 1 | 자료팀 (web-image-search) |
| `design-tokens` | autopilot-design | Phase 2 | — |
| `design-components` | autopilot-design | Phase 3 | 디자인팀 (maker) |
| `design-review` | autopilot-design | Phase 4 | 디자인팀 (critic) |
| `design-handoff` | autopilot-design | Phase 5 | — |

> 주의 — 자료의 stage 라벨은 두 종류. autopilot-code 는 `plan/refine/execute/test/report`, autopilot-draft 는 `clarify/analyze/strategy/strategy-refine/draft/draft-refine/finalize`, autopilot-research 는 `search/analyze/report`, autopilot-design 은 `Phase 0~5`. SVG 에서 stage 라벨을 부모별로 정확히 구분할 것.

### §1.3. Meta — 1

| skill | 역할 | output |
|---|---|---|
| `sync-skills` | skill/agent 정의 변경 감지 → README 대시보드 동기화 + §3 invariant 자동 검사 | `~/.claude/README.md` |

---

## §2. 도메인 트랙 정리

작업 본질 기준 9 트랙. 각 트랙은 _entry orchestrator_ + _선행 입력_ + _후속 흐름_ 으로 구성.

| 트랙 | entry orchestrator | 선행 입력 (보통) | 후속 hand-off | 핵심 agent |
|---|---|---|---|---|
| 코드 | `autopilot-code` | `specs/*` 또는 `analysis_project/code/` | (실험 졸업 ← autopilot-lab) | 기획팀·품질관리팀·개발팀 |
| 문서 | `autopilot-draft` | `analysis_project/{paper,doc}/` + `research/*` | `autopilot-apply` (cheatsheet → real source) | 연구팀·편집팀·자료팀 |
| 연구 | `autopilot-research` | `analysis_project/paper/` | autopilot-draft / autopilot-code / autopilot-spec | 연구팀·자료팀 |
| 실험 | `autopilot-lab` | `analysis_project/code/` (conventions) | autopilot-code (정련·라이브러리화) | 개발팀·품질관리팀·자료팀 |
| 디자인 | `autopilot-design` | 사용자 ref / `specs/*/02_design/` | autopilot-spec build phase / 프론트 dev | 디자인팀·자료팀 |
| 앱 | `autopilot-spec` → `autopilot-ship` | `research/market` | autopilot-code (구현) + autopilot-design (UI) | 개발팀·디자인팀 |
| 사용자 분석 | `analyze-user` | cross-project 산출물 | (모든 sub-agent default 참조) | (adversarial QA) |
| 점검 | `analyze-project` / `audit` / `notes` | cwd 자료 / 기존 artifact | 모든 트랙 input | 연구팀·품질관리팀·편집팀 |
| 정정 | `autopilot-refine` / `autopilot-apply` | 기존 `research/*` `documents/*` artifact | (대상 in-place) | 연구팀·편집팀 |

### §2.1. 트랙 간 큰 흐름 (3 stage)

연구·실험·점검은 _선행 자료 생성_, autopilot orchestrator 는 _산출_, refine/apply/audit 는 _사후_. 한 줄 요약:

```
[선행 입력]                  [산출 (orchestrator)]              [사후]
analyze-project ─┐
analyze-user ────┤
autopilot-research ─→ autopilot-{draft, code, spec} ─→ autopilot-{refine, apply}
autopilot-lab ───┘    autopilot-{design, ship}          audit / notes
```

핵심 데이터 전달 4 가지 (자료가 명시):
- `analyze-project --mode paper` → `autopilot-research` (paper/ auto-detect)
- `autopilot-research academic` → `autopilot-draft` (paper/presentation) + `autopilot-code` (baseline 코드)
- `autopilot-research technology` → `autopilot-code` + `autopilot-spec`
- `autopilot-research market` → `autopilot-draft` (proposal) + `autopilot-spec` (reference UX)
- `autopilot-spec` → `autopilot-code` (`specs/<name>/` 자동 감지) + `autopilot-design` (Phase 2 UI) → `autopilot-ship`
- `autopilot-draft` (cheatsheet) → `autopilot-apply` (real source 적용·verify)
- `autopilot-lab` (summary) → `autopilot-code` (졸업) / 다음 실험 spec 의 input

---

## §3. 자연어 발화 → invoke 분류 (4 갈래)

`CLAUDE.md` §6 Pre-check 발화 분류. 메인 Claude 가 turn 첫 단계에 분류.

| 갈래 | 구성원 | 동작 |
|---|---|---|
| **A. ceremony 큰 6** | `autopilot-code`, `autopilot-draft`, `autopilot-research`, `autopilot-refine`, `autopilot-apply` + `analyze-user` | 옵션 자동 구성 → 자연어 1줄 컨펌 → invoke. §5 자율 진행 (10-30분 timer) 적용 |
| **B. ceremony 작은 3** | `audit`, `notes`, `analyze-project` | 컨펌 없이 즉시 invoke |
| **C. sub-skill 발화** | `init-plan`/`refine-plan` 등 자연어 | 부모 autopilot-* 의 `--from <stage>` 재개로 라우팅 (단독 invoke 는 slash 직접 입력 시만) |
| **D. skill 매칭 없음** | 짧은 한 번 작업 | 메인 Claude 직접 처리 (Read/Edit/Bash/Agent 직접) |

> 갈래 A 에 `autopilot-spec`/`autopilot-design`/`autopilot-lab`/`autopilot-ship` 은 §6 의 명시 6개 리스트엔 없으나 _ceremony 큰_ 본질 (`.claude_reports/` 누적). SVG 에서는 A 를 _ceremony 큰 (컨펌)_ 으로 묶되 명시 6개를 굵게, 나머지 autopilot 을 같은 군에 옅게 둘 것.
> High-stakes 신호 (_신중히 / camera-ready / submission 직전_) → QA adversarial 자동 상향. `analyze-user` 는 신호 무관 항상 adversarial.

---

## §4. 산출물 흐름 (`.claude_reports/` 관점)

6 + 2 폴더. 3-tier (T1 root / T2 subdir / T3 `_internal/`) 구조 공통.

| 폴더 | 생성 skill | T1 (항상 봄) | T2 (필요 시) | T3 (`_internal/`) |
|---|---|---|---|---|
| `analysis_project/{code,paper,doc}/` | analyze-project | overview, interface_reference | per-paper, reviewers/, formats/ | raw scan, QA logs |
| `research/{topic}/` | autopilot-research | pipeline_summary, 00_briefing, 01~NN 챕터 | cards/, code_resources/, figures/ | search_results.json, chaining, reviews/, versions/ |
| `specs/{name}/` | autopilot-spec, ship | pipeline_state, PRD | 02_design/, api_contract, data_model | reviews |
| `plans/{date}_{name}/` | autopilot-code | pipeline_summary, plan/ | dev_logs/, test_logs/ | plan_reviews/, test_reviews/, versions/ |
| `documents/{date}_{name}/` | autopilot-draft | pipeline_summary, draft/ | strategy/, analysis/, assets/ | draft_meta, strategy_reviews/, draft_reviews/, audit/, versions/ |
| `designs/{name}/` | autopilot-design | handoff.md, design_state | tokens, components | reviews |
| `~/.claude/user_profile/0X_*.md` | analyze-user, notes | aspect 파일 | — | — |
| `NOTES.md` (per-cwd) | notes | 5 categories | — | — |

데이터 누적의 핵심 비대칭:
- `analysis_project/{code,paper}/` flat — 프로젝트당 1개씩 누적
- `analysis_project/doc/{name}/` per-task subdir — task별 입력 폴더 다름
- `research`/`documents`/`plans` 는 `{topic}` / `{date}_{name}` 단위로 여러 개 병존
- `_internal/versions/v{N}/` 는 autopilot-refine 스냅샷 (코드는 git 권장)

---

## §5. Agent 호출 매트릭스

행 = 8 agent, 열 = 호출하는 skill. ● = 자동 호출, ○ = 옵션/조건부.

| Agent (model) | 호출하는 skill | 주 mode | 비고 |
|---|---|---|---|
| **기획팀** (opus) | code-plan ●, code-refine ● | (단일) | 사용자 직접 호출 X (skill 전용) |
| **품질관리팀** (opus 가변) | code-plan ●, code-refine ●, code-execute ●, code-test ●(2×), code-report ●(sonnet), analyze-project ○, autopilot-lab ○ | code-review / plan-review / test / ml-debug / data-curate | Thorough 시 2× parallel (code 갈래 opus+sonnet) |
| **연구팀** (opus 가변) | analyze-project ●, autopilot-research ●, draft-strategy ●, draft-refine ●, autopilot-code(plan review) ●, audit ●(fact-check), autopilot-refine ● | research-survey / plan-review / fact-check | fact-checker subrole 은 sonnet |
| **자료팀** (opus) | autopilot-research ○, autopilot-draft ○(figure 게이트), autopilot-code ○, autopilot-lab ○, design-refs ● | browser-fetch / pdf-extract / web-image-search / figure-gen / data-script | 분석팀+탐색팀 통합 (2026-05-25) |
| **개발팀** (sonnet) | autopilot-spec(scaffold) ●, autopilot-lab(scaffold) ●, code-test(hotfix) ○ | backend / frontend / refactor / new-lib | 유일 sonnet 단일 |
| **디자인팀** (opus) | autopilot-design ●, design-components ●, design-review ●, autopilot-code(app UI) ○ | maker / critic | sonnet→opus 승격 (2026-05-26) |
| **편집팀** (opus) | code-report ●, audit ●, autopilot-draft(ko/en mirror) ●, autopilot-refine ○ | translate / polish / review | instruction 파일은 트리거 대상 X |
| **codex-review-team** (Codex GPT-5 + opus) | adversarial QA 자리 (모든 autopilot) ○ | review / adversarial-review | adversarial level 에서만 1× |

매트릭스 관찰:
- **연구팀·품질관리팀** 이 호출 hub (각 6~7 skill). 시각적으로 중앙.
- **codex-review-team** 은 leaf — adversarial 일 때만 붙음 (점선).
- **개발팀** 만 sonnet — 시각 톤 다르게 (옅은 채도).
- **편집팀** 은 _사용자 향 한국어 산출물_ 끝자리 일관 호출 (mirror/polish).

---

## §6. QA gate 분포

5 level (`CONVENTIONS.md` §1.4). adversarial = thorough + 1× codex-review-team (불변).

| level | reviewer | fact-checker | codex | 채택 skill (default) |
|---|---|---|---|---|
| **quick** | 1-pass | — | — | autopilot-refine(과거) |
| **light** | 1× sonnet | — | — | **autopilot-lab (default)** |
| **standard** | 1× opus | standard+ | — | (각 skill default fallback) |
| **thorough** | 2× opus parallel (code 갈래 opus+sonnet) | ✓ | — | **research/code/draft/refine (default)** |
| **adversarial** | thorough + 외부 | ✓ | ✓ 1× | **analyze-user (고정)** |

특수:
- `autopilot-apply` — `--qa` 없음. verify = latexmk compile + latexdiff (build gate, reviewer 아님).
- `audit` — `--qa` 대신 `--scope`. fact-check 는 Stage B.5 별도.
- `run-test` (sub) — 항상 forced thorough (level 무시), 2팀 병렬.
- `final-report` (sub) — 항상 sonnet 1× (level 무관).

기본값 분포 핵심 — _대부분 thorough_, lab 만 light (실험 빠른 cycle), analyze-user 만 adversarial 고정.

---

## §7. 시각화 가이드 (디자인팀 전달)

### §7.0. 사용자 figure 성향 default (반드시 반영)

`user_profile/01_paper_figure_style.md` 개별 파일은 현재 부재 (README 만 존재) — 작업 지시문 명시 default 를 적용:

- **architecture diagram outline = grayscale 기조** — 노드 테두리·배경은 무채색, 색은 _의미 강조에만_.
- **색 cool·warm 분리** — encoder/입력계열 = 녹색 `#3F8C5C`, decoder/출력계열 = 주황, **ours/강조 = 빨강 `#A0152A`**.
- **폰트 = Times-equivalent serif** (라벨·캡션). 코드 식별자만 mono.
- **block = rounded rectangle**, **arrow = solid 1.5pt**.
- 본 가이드에 맞춘 색 매핑 (아래 §7.5 팔레트) — grayscale 위에 트랙별 hue 한 점씩만.

### §7.1. 추천 다이어그램 구성 (총 4 장)

자료가 7 차원이라 한 그림에 다 넣으면 과밀. **4 장 분할** 추천 (README 의 3장 mermaid 보다 1장 추가 — agent 매트릭스를 독립 장으로).

| # | 제목 | 다루는 차원 | 메타포 | 비율 |
|---|---|---|---|---|
| D1 | **트랙 오버뷰 (swimlane)** | §2 도메인 트랙 9 + §3 발화 4갈래 진입 | 수영 레인 (가로 9 레인) | 가로 long (16:9 wide) |
| D2 | **orchestrator → sub-skill → agent 호출 그래프** | §1 위계 + §5 agent | layered DAG (3 layer) | 4:3 |
| D3 | **데이터 전달 흐름 (3 stage)** | §2.1 + §4 산출물 폴더 | 좌→우 pipeline + 폴더 아이콘 | 가로 long |
| D4 | **agent 호출 매트릭스 + QA gate** | §5 매트릭스 + §6 QA 5레벨 | 격자 heatmap + 우측 QA 범례 | 4:3 |

### §7.2. D1 — 트랙 오버뷰 (swimlane)

**구조** — 세로로 9 레인 (트랙), 각 레인 안에 entry orchestrator block 1개 + 후속 화살표.

- **레인 순서** (위→아래, 작업 생애주기 순): 점검 → 사용자분석 → 연구 → 실험 → 청사진(앱) → 코드 → 디자인 → 문서 → 정정.
- **노드** — 각 트랙 entry orchestrator = rounded rectangle, 트랙 hue 테두리 (§7.5).
- **상단 띠** — 발화 4갈래 (A 큰컨펌 / B 작은즉시 / C sub재개 / D 직접). 각 갈래에서 해당 레인으로 점선 진입 화살표.
- **엣지** — 트랙 간 hand-off (research→draft/code/spec, lab→code, draft→apply, spec→code/design/ship) 는 레인 가로질러 solid 1.5pt 화살표.

**노드 목록** (block 라벨):
```
점검:       analyze-project | audit | notes
사용자분석:  analyze-user
연구:       autopilot-research
실험:       autopilot-lab
청사진:     autopilot-spec → autopilot-ship
코드:       autopilot-code
디자인:     autopilot-design
문서:       autopilot-draft
정정:       autopilot-refine | autopilot-apply
```

**엣지 목록** (cross-lane, 라벨 붙임):
- research → draft (`academic/market`)
- research → code (`academic/technology baseline`)
- research → spec (`technology/market`)
- lab → code (`졸업·라이브러리화`)
- spec → code (`specs/<name>/ 자동감지`)
- spec → design (`Phase 2 UI`)
- spec → ship
- draft → apply (`cheatsheet → real source`)
- analyze-project → research/spec/draft (`선행 입력`, 옅은 점선 3갈래)

**기대 인사이트** — "내가 무슨 말을 하면 어느 트랙·어느 entry skill 로 떨어지고, 그 결과가 다음 어디로 흘러가는가" 를 한눈에. 특히 _research 가 3 트랙으로 갈라지는 fan-out_ 과 _draft→apply, lab→code 의 졸업 화살표_ 가 보이게.

### §7.3. D2 — orchestrator → sub-skill → agent 호출 그래프 (layered DAG)

**3 layer (좌→우)**:
- **L1 orchestrator** (좌) — autopilot-code, autopilot-draft, autopilot-design, autopilot-spec/lab.
- **L2 sub-skill** (중) — code-plan/refine/execute/test/report, draft-strategy/refine, design-init~handoff, app-init/spec.
- **L3 agent** (우) — 8 agent = 원 (circle) 노드.

**엣지**:
- L1→L2 = 부모-자식 (굵은 solid, stage 라벨 `Step N`/`Phase N`).
- L2→L3 = 호출 (solid 1.5pt). L3 의 codex-review-team 으로 가는 엣지만 _점선_ (adversarial 조건부).
- 같은 agent 를 여러 sub-skill 이 부르면 fan-in — 연구팀·품질관리팀 원이 가장 많은 엣지 수렴 (hub 강조: 원 크기 ↑ 또는 빨강 `#A0152A` 링).

**메타포** — skill = rounded rectangle (grayscale fill), agent = circle. agent 색은 frontmatter color 차용해도 좋으나 §7.0 grayscale 기조 유지 위해 _테두리만_ 색: 연구팀 보라, 품질관리팀 빨강, 자료팀 노랑, 개발팀 녹색, 디자인팀 분홍, 편집팀 청록, 기획팀 파랑, codex 빨강(점선).

**기대 인사이트** — "autopilot 하나 부르면 내부에서 sub-skill 이 순차로 돌고, 각 단계가 어느 전문 팀을 부르는지" 위계. 연구팀·품질관리팀이 _hub_ 임이 시각적으로 자명하게.

### §7.4. D3 — 데이터 전달 흐름 (3 stage pipeline)

**3 세로 밴드 (좌→우)**: [선행 입력] → [산출 orchestrator] → [사후].

- 각 orchestrator 아래 **폴더 아이콘** (산출물 위치) 달기 — `research/{topic}/`, `documents/{date}_{name}/`, `plans/{date}_{name}/`, `specs/{name}/`, `designs/{name}/`, `analysis_project/{...}/`.
- 폴더 아이콘 안에 T1/T2/T3 3 칸 미니 스택 (T1 진한 grayscale, T3 옅은) — 3-tier 시각화.
- 화살표가 _폴더에서 다음 skill 로_ 들어가게 (산출물이 곧 다음 입력임을 강조).

**기대 인사이트** — "각 skill 의 결과물이 `.claude_reports/` 어디에 쌓이고, 그게 어떻게 다음 skill 의 입력이 되는가". user_profile 이 _모든 sub-agent 의 default 참조_ 라는 점은 하단 가로 띠로 별도 표기 (analyze-user → user_profile → 전 agent 점선 broadcast).

### §7.5. D4 — agent 호출 매트릭스 + QA gate

**좌측 격자 heatmap** — 행 8 agent × 열 skill (orchestrator+sub 주요 13). 셀 ● 자동 / ○ 옵션. ●= 진한 셀, ○= 옅은 셀, 빈칸 무채색.

**우측 QA 범례 세로 막대** — 5 level 을 강도 그라데이션 (quick 옅음 → adversarial 진한 빨강). 각 level 옆 default 채택 skill 태그. adversarial 만 codex 아이콘 (외부) 표시.

**기대 인사이트** — (1) 어느 팀이 가장 많이 불리는가 (연구팀·품질관리팀 행이 가장 진함), (2) QA 강도 사다리와 각 skill 의 default 위치 (lab=light, 대부분=thorough, analyze-user=adversarial 고정).

### §7.6. 공통 시각 규칙 (4 장 일관)

| 요소 | 표현 |
|---|---|
| skill (orchestrator) | rounded rectangle, 굵은 테두리, 트랙 hue |
| skill (sub) | rounded rectangle, 가는 테두리, 옅은 grayscale fill |
| agent | circle, 테두리만 agent color |
| 산출물 폴더 | folder 아이콘 + T1/T2/T3 미니 스택 |
| 자동 호출 엣지 | solid 1.5pt 화살표 |
| 조건부/옵션 엣지 (codex, analyze-project 선행) | dashed 1.5pt |
| hand-off 엣지 (트랙 간) | solid 1.5pt, 라벨 붙임 |
| 폰트 | Times-equivalent serif (라벨), mono (skill/agent 식별자) |
| 강조색 (ours/hub) | 빨강 `#A0152A` |
| cool 계열 (입력·선행) | 녹색 `#3F8C5C` |
| warm 계열 (산출·후속) | 주황 |
| 기조 | grayscale outline, 색은 의미 강조에만 |

**트랙 hue 매핑** (D1 레인 + orchestrator 테두리):
- 점검 = 회색 / 사용자분석 = 빨강 `#A0152A` (critical) / 연구 = 녹색 `#3F8C5C` / 실험 = 연녹 / 청사진·앱 = 파랑 / 코드 = 청록 / 디자인 = 분홍 / 문서 = 주황 / 정정 = 자주(plum).

---

## §8. 자료 무결성 메모 (디자인팀 참고)

- **README 의 기존 mermaid 3장 (트랙/호출/I-O)** — 본 가이드 D1/D2/D3 과 대응하나, 본 가이드는 agent 매트릭스 (D4) 를 독립 장으로 추가하고, 트랙을 9개로 명시 (README 는 4 subgraph 로 묶음). 더 세분.
- **autopilot-spec/lab/design/ship** 은 CLAUDE.md §6 의 _명시 6 ceremony_ 리스트엔 없지만 ceremony 큰 본질 — D1 에서 같은 군에 두되, 명시 6개 (code/draft/research/refine/apply/analyze-user) 를 _굵게_, 나머지를 _보통_ 두께로 구분.
- **codex-review-team** model 은 `opus` 단독 표기 시 drift (실제 Codex GPT-5) — D2/D4 에서 "Codex GPT-5 + opus orchestrator" 병기.
- `user_profile/01_paper_figure_style.md` 가 실제로 생성되면 §7.0 default 를 그 파일 값으로 교체할 것 (현재는 README 기반 + 지시문 default).
