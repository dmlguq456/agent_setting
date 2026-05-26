# Conventions — Family-Wide Operational Rules

> 본 문서는 autopilot family 전체에 적용되는 _운영 규칙·정의_의 **단일 source of truth**. `DESIGN_PRINCIPLES.md`가 _architectural design_(orchestrator/skill/agent 분리, interface contract 등)을 다룬다면, 본 문서는 _operational conventions_(QA level 정의, model 표기, family-wide flag 정책 등)을 다룬다.
>
> **자동 로드 메커니즘**: `CLAUDE.md`의 "Source of Truth"에 본 파일이 등재되어 세션 시작 시 README 부트스트랩을 통해 인지. QA·model·family-wide flag 관련 작업 시 메인 Claude가 본 파일을 직접 read해 정의를 가져옴.
>
> **자동 propagation**: `/sync-skills`의 Step 5b.5가 본 문서를 canonical로 cross-doc grep해 drift 보고. `--auto-fix` flag로 자동 propagation 수행 (default는 report-only).

---

## §1. QA Levels (canonical)

### §1.1. 5단계 공통 정의

| Level | Quality reviewer (parallel) | Fact-checker¹ (parallel) | Codex (parallel) | Max round | 비고 |
|---|---|---|---|---|---|
| **quick** | 1× sonnet | skip | skip | 1 (강제) | refine 단계 skip / 1라운드 강제 종료 / 🔴 잔존 시 `unresolved.md` 에 기록만 |
| **light** | 2× sonnet (다른 axes²) | skip | skip | 1 | 사소 작업 — refine 단계 skip |
| **standard** | 1× opus + 2× sonnet (다른 axes²) | 1× sonnet | skip | 1 | 간단 작업 — refine 단계 가능 |
| **thorough** | 2× opus + 2× sonnet (다른 axes²) | 1× sonnet | skip | 2 | **default** — refine 단계 가능 |
| **adversarial** | 2× opus + 2× sonnet (다른 axes²) | 1× sonnet | 1× `Agent(codex-review-team)` — Codex CLI (GPT-5) external review | 2 + Codex 1 | high-stakes — _모든 autopilot-* 4 개 지원_ |

¹ Fact-checker 는 _doc/research/refine 파이프라인_ 에만 적용. autopilot-code 계열 (init-plan / refine-plan / execute-plan / run-test) 은 fact-checker 없음 — ground-truth 가 코드 자신이라 verbatim 대조 무용.

² 다중 reviewer 는 _다른 axes_ 분담: opus 행은 도메인 expertise / methodology / completeness / safety 같은 깊이 필요 axis, sonnet 행은 coverage·typo·표기 일관성·structure 같은 surface scan axis. 각 skill SKILL.md 가 자기 axis 분담 명시.

### §1.2. Codex availability 정책 (adversarial 전용)

- Adversarial 선택 전 `codex --version 2>/dev/null` 실행
- 실패 시: `--qa adversarial` _명시_ 호출 → fail loudly / auto-detect로 adversarial 선택 → Thorough로 silent fallback
- Codex agent는 `adversarial-review --wait --scope auto` 실행 → `_internal/{stage}_reviews/round_{N}_codex.md` 작성

### §1.3. opt-out flags (orthogonal)

- `--no-fact-check` — 모든 level에서 fact-checker 단독 skip (`quick`/`light`는 어차피 skip이라 무의미)
- `--no-style-audit` — Stage B.5 style aspect skip (refine 계열만)

이 두 flag는 `--qa` level 무관하게 적용되며, fact-checker / style audit을 끄는 _유일한_ 메커니즘 (ad-hoc prompt로 무시 불가). **autopilot-refine · audit 전용** — 다른 skill의 argument-hint에 노출되면 drift.

### §1.4. Skill별 사용 매트릭스

| Skill | Supported levels | Default | Adversarial | Fact-checker | 비고 |
|---|---|---|---|---|---|
| `autopilot-research` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | 모든 autopilot 통일 |
| `autopilot-code` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ (dev only; debug 는 thorough 로 downgrade) | **X** (code 는 fact-checker 없음) | |
| `autopilot-lab` | quick/light/standard/thorough/**adversarial** | `light` | ✓ | **X** (실험 prototype — code 와 동일 — fact-checker 없음) | default 가 light 인 이유: 실험 prototype 빠른 cycle 1순위. 사용자 high-stakes 발화 (논문 결과·외부 공개) 시 standard+ 자동 상향 |
| `autopilot-draft` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | |
| `autopilot-refine` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | default 변경 (이전 quick → thorough) |
| `autopilot-apply` | — (`--qa` 없음) | — | — | **X** | verify = build/compile gate (latexmk) + latexdiff. reviewer QA loop 아님 — `run-test` 의 build 검증과 동류. ground-truth 는 컴파일 결과 |
| `analyze-user` | **adversarial (고정)** | `adversarial` | ✓ (강제) | standard+ | user profile 정확성 critical — qa 협상 불가, 다른 level 명시해도 adversarial 로 force |
| `audit` | — | — | — | `--no-fact-check` flag | `--qa` 대신 `--scope` 사용; fact-check 는 Stage B.5 에서 별도 |
| `init-plan` (sub) | quick/light/standard/thorough/adversarial | auto-detect from scope (plan frontmatter override) | ✓ | X | autopilot-code 내부 |
| `refine-plan` (sub) | quick/light/standard/thorough/adversarial | inherit from plan frontmatter | ✓ | X | autopilot-code 내부 |
| `execute-plan` (sub) | inherit | inherit | inherit | X | autopilot-code 내부 |
| `run-test` (sub) | **forced thorough** (`--qa` 무시) | thorough | auto-upgrade if Codex available | X | 항상 2팀 병렬, Codex 가용 시 자동 상향 |
| `final-report` (sub) | sonnet 1× (level-independent) | — | — | — | 모든 level 에서 writer 는 항상 sonnet |
| `init-doc-strategy` (sub) | quick/light/standard/thorough/adversarial | inherit from autopilot-draft | ✓ | standard+ | autopilot-draft 내부 |
| `refine-doc` (sub) | quick/light/standard/thorough/adversarial | inherit | ✓ | standard+ | autopilot-draft 내부 |

> _Sub-skill_ (init-plan / refine-plan / execute-plan / run-test / final-report / init-doc-strategy / refine-doc): orchestrator가 결정한 `--qa` 값을 그대로 받음. 직접 호출 시는 자체 default 사용.

---

## §2. Agent Model 표기 (canonical)

각 agent의 frontmatter `model:` 필드는 _sub-agent runtime_ model. 실제 작업 시 가변 또는 외부 LLM 호출이 있는 경우 본문·매트릭스에 명시.

| Agent | frontmatter `model:` | 실제 작동 |
|---|---|---|
| `기획팀` (plan-team) | opus | opus 단일 |
| `품질관리팀` (qa-team) | opus | **가변** — review 모드: Light=1× sonnet / Standard=1× opus / Thorough=doc·research·refine 갈래 2× opus parallel · code 갈래 (init-plan/refine-plan/execute-plan) 1× opus + 1× sonnet parallel (completeness reviewer 가 비교적 mechanical 매칭이라 sonnet 가 cost-efficient — code 의 ground-truth 가 코드 자신이므로 verbatim 비교 비중이 큼). test 모드 (run-test): Agent A=sonnet coverage + Agent B=opus accuracy (2026-05-22 테스트팀 흡수) |
| `연구팀` (research-team) | opus | **가변** — default opus (Plan Review·domain reviewer); fact-checker subrole·light QA는 sonnet (cost-aware verbatim matching) |
| `분석팀` (analysis-team) | opus | opus 단일 — 수치·시각 자료 생성 (matplotlib figure 자산 + 데이터 분석 스크립트 + 결과 후처리) |
| `탐색팀` (browser-team) | sonnet | sonnet 단일 |
| `개발팀` (dev-team) | sonnet | sonnet 단일 |
| `편집팀` (editorial-team) | opus | opus 단일 |
| `codex-review-team` | opus | **Codex CLI (GPT-5)** — actual review·analysis는 외부 Codex CLI에서; sub-agent 본체(opus)는 호출·결과 한국어 재정리만 담당 |

---

## §3. Hard Cross-Doc Invariants (sync-skills `--check`가 자동 검사)

1. 각 SKILL.md / README / `_notion_mirror`/*에서 §1.1 5단계 정의의 **Quality reviewer / Fact-checker / Codex 컬럼 wording**은 본 문서와 의미 일치 (사소한 표현 차이는 허용, 의미가 다르면 drift).
2. **adversarial** 정의는 반드시 `thorough + 1× codex-review-team`. 자주 잘못 적힌 패턴: `standard + Codex` — _틀림_.
3. autopilot-code의 QA 표에 fact-checker가 적힌 곳이 있으면 drift (code는 fact-checker 없음).
4. `--no-fact-check` / `--no-style-audit`는 autopilot-refine / audit 외 다른 skill에 노출되면 안 됨.
5. `codex-review-team`의 model 표기가 `opus` 단독이면 drift — 실제 review는 Codex CLI (GPT-5). §2 매트릭스에 따라 "Codex CLI (GPT-5) + opus orchestrator" 같이 분리 표기.

새 invariant 추가는 본 섹션 list에 한 행 추가하면 sync-skills Step 5b.5의 자동 검사 list에 포함.

---

## §4. 자동 fix 정책

`/sync-skills --auto-fix` (default는 report-only):
- §3의 hard invariants 위반 발견 시 canonical wording을 다른 곳으로 propagate
- _Wording 자체_가 다를 경우 (의미 동일·표현 차이): skip (사람 결정 사항)
- _의미가 다른_ 명백한 drift: canonical로 강제 교체 + commit 안내
- `--auto-fix --dry-run`으로 미리보기

---

## §5. Skill Output Convention (3-Tier T1/T2/T3)

> 모든 autopilot family + analyze-project skill이 따르는 산출물 폴더 구조 표준. 본 절이 single source of truth — 각 SKILL.md는 본 절을 참조한다 (재정의 금지).
>
> 이전 산출물은 legacy 구조(파일들이 평면 배치, `_v{N}.md` 형제, reviews/ 메인 레벨)를 유지하며, **새 호출부터 신 컨벤션 적용**.

### §5.1. Workspace assumption (전제)

**모든 skill은 Claude가 _프로젝트 루트에서 실행됨_을 전제로 함**:
- `.claude_reports/`는 _현재 작업 디렉토리_에 생성·읽기·쓰기
- analyze-project는 현재 dir의 파일을 읽음 (code/paper/doc 모드)
- autopilot-code는 현재 dir에서 코드 변경
- autopilot-{doc,research,refine}는 `.claude_reports/` 하위 영속 산출물을 input으로 implicit 인지 (cross-project 작업은 `cd <other>` 후 별도 세션)

모든 입력은 _프로젝트 컨텍스트 내부의 영속 산출물_ (`.claude_reports/analysis_project/*`, `.claude_reports/research/{topic}/`)에서 옴. 외부 폴더를 직접 가리키는 flag는 family 에 없음. 외부 raw 자료가 있으면 먼저 `analyze-project --mode {paper|doc}`로 영속 산출물화.

### §5.2. Tier 정의

사용자 가시성을 기준으로 3 단계로 나눔:

| Tier | 의미 | 폴더 위치 |
|---|---|---|
| **T1 (Primary)** | 사용자가 _항상_ 보는 핵심 산출물 (entry/index + main deliverable) | artifact root 최상위 |
| **T2 (Secondary)** | 사용자가 _필요 시_ 검토 (chapters / strategy / analysis / logs) | artifact root 하위 폴더 |
| **T3 (Tertiary)** | 사용자가 _거의_ 안 봄 (audit / raw metadata / 버전 스냅샷) | `_internal/` 하위로 격리 |

`_internal/` underscore prefix는 시각 신호 ("이 폴더는 들어갈 일 적음"). dot prefix(`.internal/`)는 ls 기본 표시 안 됨이라 너무 숨겨짐 → underscore 채택.

### §5.3. 표준 폴더 구조

아래는 **대표 표기**입니다 (개념 단순화). 실제 skill별 매핑에서는 `_internal/` 하위 폴더가 더 세분화될 수 있습니다 (예: doc은 `_internal/strategy_reviews/` + `_internal/draft_reviews/` 분리; code는 `_internal/plan_reviews/` + `_internal/dev_reviews/` + `_internal/test_reviews/`). 각 매핑 섹션 참조.

```
{artifact_dir}/
├── pipeline_summary.md           [T1] entry/index + 통합 history
├── <T1 main deliverables>        [T1] skill별로 구체적
├── <T2 subfolder...>             [T2] 필요 시 검토
└── _internal/                    [T3] audit / raw / versions
    ├── <reviews/...>              ← skill별 *_reviews/ (구체 매핑 참조)
    ├── <raw metadata files>       ← 검색 raw, batches.json 등 (research)
    └── versions/                  ← refine 스냅샷 (autopilot-refine이 관리)
        └── v{N}/<changed-files>/
```

### §5.4. 각 skill 매핑

#### §5.4.1. autopilot-research → `.claude_reports/research/{topic}/`

```
{topic}/
├── pipeline_summary.md           [T1]
├── pipeline_state.yaml           [T1] --from 재개용 stage state
├── 00_briefing.md                [T1] executive summary
├── 01_landscape.md ~ NN_*.md     [T1+T2] 챕터들 (numeric prefix로 정렬·groupling)
├── analysis_summary.md           [T2]
├── cards/                        [T2] 논문/레퍼런스 카드 (primary source)
├── code_resources/               [T2] code-search hit + HF 사전 fetch (autopilot-research 06_implementation 단계)
├── figures/                      [T2] paper figure 추출 (figure_index.md + {paper_id}_fig*.png)
└── _internal/                    [T3]
    ├── search_results.json, search_results.md
    ├── phase_a_batches.json, phase_a_final_batches.json
    ├── access_classification.json
    ├── chaining_results.md
    ├── code_search.md
    ├── hf_prefetch.md
    ├── reviews/                  ← report_reviews/
    └── versions/                 ← autopilot-refine 스냅샷
```

> chapters/ 별도 subdir 도입은 비용 대비 효과 부족 (numeric prefix가 이미 grouping 역할). chapter 파일은 root에 그대로 두고 `_internal/`만 분리.

#### §5.4.2. autopilot-draft → `.claude_reports/documents/{date}_{name}/`

```
{date}_{name}/
├── pipeline_summary.md           [T1]
├── pipeline_state.yaml           [T1] --from 재개용 stage state
├── draft/                        [T1] latest만
│   ├── draft.md
│   └── draft_ko.md
├── strategy/                     [T2] latest만
│   ├── strategy.md
│   └── strategy_ko.md
├── analysis/                     [T2]
│   ├── material_index.md
│   └── ref_analysis.md (or reviewer_analysis.md for rebuttal)
├── assets/                       [T2] 본문 삽입용 figure (figures/figure_index.md + *.png; Source 3)
└── _internal/                    [T3]
    ├── draft_meta.md             ← strategy 단계에서 결정된 의도·format spec hint 등
    ├── strategy_reviews/         ← 기존 strategy_reviews/ 그대로 이동
    ├── draft_reviews/
    ├── audit/                    ← /audit 보고서 (skill 본문 정의)
    ├── discarded/                ← 폐기된 draft·strategy 변형 (실험적)
    └── versions/
        ├── v1/strategy/, draft/
        ├── v2/...
        └── v{N}/...
```

> **중요**: 기존 `_v{N}.md` 형제 패턴 (`strategy_v1.md` next to `strategy.md`)은 **폐기**. 새 컨벤션은 `_internal/versions/v{N}/strategy/strategy.md`. 단, 기존 산출물에 이미 형제 파일이 있으면 그대로 둠 (legacy 호환).

#### §5.4.3. autopilot-code → `.claude_reports/plans/{date}_{name}/`

```
{date}_{name}/
├── pipeline_summary.md           [T1]
├── pipeline_state.yaml           [T1] --from 재개용 stage state (plan frontmatter 와 병용 가능)
├── plan/                         [T1]
│   ├── plan.md, plan_ko.md
│   └── checklist.md
├── dev_logs/                     [T2] execute-plan 변경 narrative
├── test_logs/                    [T2] test_report.md 등 (failure 시 봄)
└── _internal/                    [T3]
    ├── plan_reviews/             ← init-plan / refine-plan QA round logs
    ├── test_reviews/             ← run-test reviewer logs
    └── versions/                 ← (autopilot-refine 사용 시; 코드는 git 권장)
```

> 코드 산출물에 autopilot-refine 적용 안 됨 (기본). 그래도 `_internal/versions/`는 차후 plan refine 시 사용 가능.

#### §5.4.4. analyze-project (3 modes) → `.claude_reports/analysis_project/{code,paper,doc}/`

`analyze-project` skill이 단일 entry point. `--mode <X>`로 분기.

```
analysis_project/
├── code/                            [--mode code, flat]
│   ├── 00_overview.md or topic_*.md  [T1]
│   ├── interface_reference          [T1]
│   └── _internal/                   [T3] raw scan + QA logs
├── paper/                           [--mode paper, flat]
│   ├── 00_overview_and_constraints.md [T1]
│   ├── per-paper *.md               [T1·T2]
│   └── _internal/                   [T3]
└── doc/                             [--mode doc, per-task]
    └── {name}/
        ├── 00_overview.md           [T1] inventory + classification
        ├── reviewers/               [T2]
        ├── formats/                 [T2]
        ├── samples/                 [T2]
        ├── misc/                    [T2]
        └── _internal/               [T3]
```

scoping 비대칭 의도:
- `code/`, `paper/` flat: 프로젝트당 1개씩 누적 (코드는 1개 codebase, 논문은 1개 모음)
- `doc/{name}/` per-task subdir: doc 자료는 task별로 입력 폴더가 다름 (reviewer1, template2, patent3...)

### §5.5. Legacy 호환

기존 산출물 (본 컨벤션 도입 이전에 만들어진)은 평면 구조 (`*_reviews/` 메인 레벨, `_v{N}.md` 형제, raw json 메인 평면)로 남아 있을 수 있음. 모든 skill은 다음 룰을 따름:

1. **신규 호출** (artifact_dir이 비어있거나 새로 만드는 경우) → 본 컨벤션 적용
2. **기존 산출물 재진입** (`--from <stage>` resume, `autopilot-refine` apply) → artifact_dir에 이미 존재하는 구조를 _감지_:
   - `_internal/` 폴더 존재 → 신 컨벤션 → 신 컨벤션으로 계속
   - `_internal/` 부재 + `*_reviews/` 메인 레벨 / `_v{N}.md` 형제 등 → legacy → legacy 유지 (강제 마이그레이션 X)
3. **마이그레이션** 필요 시 사용자가 명시적으로 요청해야 함 (skill이 자동 X). 별도 1회성 helper script로 처리.

### §5.6. SKILL.md 작성 규칙

본 절은 _artifact_dir 을 직접 만드는 orchestrator-level skill_ (`analyze-project`, `autopilot-{research,code,doc,draft}`, `autopilot-refine`, `audit`) 에만 적용. sub-skill (`init-plan` / `refine-plan` / `execute-plan` / `run-test` / `final-report` / `init-doc-strategy` / `refine-doc`) 은 orchestrator 가 만든 폴더 안에서 동작하므로 본 참조를 강제하지 않는다.

해당 orchestrator-level skill 의 SKILL.md 는:
- 산출물 경로 명시 시 _구체적 file path_가 아닌 _Tier_ 또는 _폴더 컨벤션_으로 표현
  - 좋음: "review log → `_internal/reviews/round_{N}.md`"
  - 나쁨: "review log → `{artifact_dir}/strategy_reviews/round_{N}_quality.md`" (절대 경로 hardcode → drift 위험)
- 본 절 참조 한 줄 포함:
  ```markdown
  > 산출물 폴더 컨벤션: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier)
  ```

### §5.7. Backward compat detection (구현 가이드)

skill이 artifact_dir을 다룰 때:

```bash
# 1. _internal/ 존재 → modern
test -d "{artifact_dir}/_internal" && CONVENTION=modern || CONVENTION=legacy

# 2. legacy일 때 reviews/versions 위치
if [[ $CONVENTION == legacy ]]; then
  REVIEWS_DIR="{artifact_dir}/strategy_reviews"  # 또는 draft_reviews / plan_reviews
  VERSIONS_PATTERN="_v{N}.md sibling"
else
  REVIEWS_DIR="{artifact_dir}/_internal/reviews"
  VERSIONS_PATTERN="_internal/versions/v{N}/"
fi
```

신규 산출물에는 항상 `_internal/` 디렉토리를 생성 (빈 폴더라도) → modern 표시.

---

## §6. Autopilot-* 흐름 매트릭스 (사용자 호출 단위)

> 본 절은 autopilot-* skill 들의 _작업 본질·역할·경계_ 의 단일 source of truth. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙. 자세한 사용자 향 청사진: [`~/.claude/AUTOPILOT_FLOWS.md`](AUTOPILOT_FLOWS.md).

### §6.1. 작업 본질 매트릭스 (대칭 강제 X)

| 작업 종류 | 사전 (외부 조사·내부 분석) | 신규 의도·청사진 | 자산 작업 (신규·기존) |
|---|---|---|---|
| **문서** (paper / presentation / 보고서 / proposal / rebuttal) | `autopilot-research` (academic / market) + `analyze-project --mode paper/doc` | `autopilot-draft` (신규 strategy + draft) | `autopilot-refine` (기존 정정·확장) |
| **코드 (모든 자리 — 라이브러리·연구·앱·CLI·API)** | `autopilot-research` (academic / technology) + `analyze-project --mode code` | **`autopilot-spec`** (mode 5종 + 복합 + auto. 모든 mode 가 PRD + Architecture Diagrams + **scaffold (skeleton 코드)** 통일 산출. ML / DL 자리는 Phase 1.5 pretrained ckpt 사전 동작 점검 자동. 중간 컨펌 6-8 자리 default) | **`autopilot-code`** (spec mode 별 분기 자동 — _layout 위 logic 추가_ 자리만) |
| **실험 prototype (ML / one-shot script)** | `analyze-project --mode code` 의 4 종 실험 자료 (`experiment_conventions` / `experiment_readiness` / `cleanup_candidates` / `similar_models`) + 직전 실험 `_RUNLOG.md` | — (spec 없이 빠른 cycle 1순위) | **`autopilot-lab`** (반복 호출, STORY+RUNLOG 누적; 졸업 자리 `autopilot-code`) |
| **공통 시각 자산** | — | `autopilot-design` (신규 디자인 사이클) | `autopilot-design` 재호출 (cycle 2+) |
| **공통 사용자 프로필** | — | `analyze-user --mode init` (aspect 7 종 — figure / writing / presentation / analysis / domain / collab / **coding_convention**) | `analyze-user --mode update` |

> **`coding_convention` aspect 의 자리** (2026-05-26): 사용자 cross-project 코드 일관 패턴 (model 폴더 / config / prefix / preferred layer / framework / metric / log·ckpt / seed) 을 `~/.claude/user_profile/07_coding_convention.md` 에 누적. autopilot-lab / autopilot-spec / autopilot-code / 개발팀 _new-lib_ 의 _cross-project default · fallback_ 자리 (2순위). **개별 프로젝트의 `analysis_project/code/experiment_conventions.md` 가 1순위 source of truth** — 충돌 자리는 per-project 우선, user_profile/07 은 _per-project 부재·빈 자리만_ 보강. 사용자 첫 호출 자리에 source 폴더 명시 (cwd 자동 발견 + `--source <path>`) — 하드코딩 path X.

### §6.2. 사용자 호출 단위 흐름 (3 패턴)

**1. 연구·실험**:
```
/autopilot-research "X 분야"                      ← (선택) 사전 조사
/analyze-project --mode code                       ← (선택) 기존 코드 청사진 + 4 종 실험 자료
/autopilot-spec --mode research,cli                ← 뼈대·skeleton + ref repo 옮김 + Phase 1.5 ckpt 검증
/autopilot-code "data loader / loss / training loop logic 구현"  ← layout 위 logic (baseline 학습 가능 코드 완성) — 필수
/autopilot-lab "X 실험"                            ← baseline 학습 + variation 실험 반복
```

**1b. 라이브러리·CLI 정돈·공개** (별도 트랙, 연구·실험 lab 졸업 후 자연 연결):
```
/analyze-project → /autopilot-spec --mode library,cli → /autopilot-code (반복)
```

**2. 문서**:
```
/autopilot-research "X 분야"                  ← (선택) 사전 조사
/analyze-project --mode paper/doc              ← (선택) 외부 자료 영속화
/autopilot-draft "X paper / 발표 자료"          ← 신규 entry
/autopilot-refine "X v2"                        ← 정정 entry (반복)
```

**3. 앱 (사용자 대상 소비자 앱)**:
```
/autopilot-research "X 도메인 / reference 앱"      ← (선택, 복잡 도메인만)
/autopilot-spec --mode app "X 앱"                  ← PRD + 스택 + scaffolding + skeleton
/autopilot-design --app X                          ← (옵션) 시각 사이클
/autopilot-code "Y 기능"                            ← app mode 추가 logic (디자인팀 critic + DB 안전 + push 자동 deploy) — 반복
/autopilot-spec --mode setup-only                  ← (가끔) ship 첫 setup·env·domain·migration 보강
```

### §6.3. _작업 본질에 맞는 분리_ 원칙

대칭 강제 X:

- **문서** 의 draft vs refine 분리 = _cross-artifact 정정_ (다른 prior 문서 가져와서 인용·정정) 가능 → 분리 자연
- **코드** 의 신규 vs 기존 = 흐름 동일, _현재 코드 상태_ 만 다름 → 한 skill 통합 자연 (autopilot-code)
- **spec** vs **code** = _코드 외 결정 + 뼈대·skeleton 생성_ ≠ _layout 위 logic 추가_ → 두 skill 분리. 단 spec mode (app/library/api/cli/research) 는 _자리별 청사진 형식·scaffold 산출물_ 만 다름 → 한 skill (autopilot-spec) 의 mode 로 통합. _빈 자리에서 baseline 구축_ 자리에서도 spec 의 scaffold 가 _ref repo 기반 skeleton_ 까지 완성 → code 는 logic 추가 자리만

### §6.3a. PRD 묶음 갱신 (Architecture Diagrams 포함)

PRD 의 textual 자리 (`api_contract.md` / `data_model.md` / `ui_flow.md`) + Architecture Diagrams (Component / Deployment) 가 _drift 빠지지 않게_ — 변경 자리에서 _영향 받는 모든 자리 한 트랜잭션_ 갱신.

| 변경 | 영향 자리 (묶음) |
|---|---|
| API endpoint·body·error | api_contract + Component (+ 옵션 Sequence) |
| DB entity·필드 | data_model + Component(backend) (+ 옵션 ER) |
| UI flow | ui_flow + Component(frontend) (+ 옵션 Activity) |
| 외부 service 통합 | api_contract(auth) + Deployment + deploy_record + .env.example |
| 스택 교체 | stack_decision + Component + Deployment |
| 상태 모델 | data_model (+ 옵션 State) |

**호출 자리**:
- `autopilot-spec` refine (사용자 의도 변경) → 영향 자리 자동 list → confirm → 일괄
- `autopilot-code` 가 spec 영향 변경 감지 → 묶음 갱신 plan → confirm → autopilot-spec back-jump

**Architecture Diagrams 기본 포함**: app / api mode 의 Component + Deployment 두 자리만. library 의 Component (module 의존) 는 옵션. ER / Sequence / Activity / State / Class 는 _복잡 자리·사용자 명시 요청_ 자리만.

### §6.4. autopilot-* family 의 컨텍스트 자동 감지 (신규 vs 재진입 통합 패턴)

autopilot-* 5 개 (`code` / `spec` / `lab` / `research` / `design`) 모두 _호출 자리에서 발화 + cwd 검사로 신규 vs 재진입 자동 분기_. 사용자가 `--from <step>` 명시 없이도 동작 — 메인 Claude 가 발화 의도 분류 + 컨펌.

#### 통합 패턴 (skill 무관 공통)

| 단계 | 처리 |
|---|---|
| 1. `pipeline_state.yaml` (또는 `design_state.yaml`) 자동 검사 | _존재_ → 재진입 / _부재_ → 신규 |
| 2. 발화 → step/stage/phase 자동 분류 | 각 skill 의 _발화→stage 매핑 표_ (SKILL.md 안 Context Auto-Detection 절 참조) |
| 3. 자동 컨펌 한 화면 | _신규 vs 재진입 자리 + 진행 자리_ 명시 + 4 갈래 응답 (진행 / 다른 step / 새로 / 중단) |

각 skill 의 _구체적 stage list + 발화→stage 매핑_ 은 해당 SKILL.md 의 `## Context Auto-Detection` 절 single source.

#### skill 별 stage 자리 (단순 reference)

| skill | stage list | state file |
|---|---|---|
| `autopilot-code` | spec 발견 자동 분기 + dev/debug mode + `--from plan/refine/execute/test/report` | `specs/<name>/pipeline_state.yaml` (있으면) |
| `autopilot-spec` | 신규 / refine v{N+1} / setup-only — `--from spec/scaffold` 등 step 별 | `specs/<name>/pipeline_state.yaml` |
| `autopilot-lab` | 신규 실험 / 재진입 — `--from spec/scaffold/run/summary` | `experiments/{date}_{slug}/pipeline_state.yaml` + `_RUNLOG.md` |
| `autopilot-research` | 신규 topic / `--from search/analyze/report` | `research/<topic>/pipeline_state.yaml` |
| `autopilot-design` | 신규 cycle / 재호출 — `--from init/refs/tokens/components/review/handoff` | `designs/<name>/design_state.yaml` 또는 `specs/<name>/02_design/design_state.yaml` |

> **autopilot-draft ↔ autopilot-refine 의 _분리_** 는 _자동 분기_ 패턴과 별개. 본 두 skill 은 _작업 본질 자체_ 가 다름 (draft = 신규 문서 작성 / refine = cross-artifact 정정, default qa 다름). 분리 유지 — 메인 Claude 가 자연어 발화 ("X 새로" vs "X v2") 로 자동 분기.

### §6.4-legacy. autopilot-code 의 컨텍스트 자동 감지

호출 자리에서 _cwd / spec 파일_ 검사로 자동 분기:

#### 1단계 — spec 존재 여부

| 감지 조건 | 처리 |
|---|---|
| `.claude_reports/specs/<name>/pipeline_state.yaml` 존재 | spec 자동 Read + 그 안 `mode` 배열 따라 _추가 logic_ 활성화. 산출 `specs/<name>/dev_log/<date>_<slug>/` |
| 부재 (spec 없이 호출) | 일반 mode — cwd 단서 (`package.json` / framework) 만 보고 _경량 추론_. 산출 `plans/<date>_<slug>/` |

#### 2단계 — spec mode 별 추가 logic

| mode | 추가 logic |
|---|---|
| **app** | UI 변경 자리 디자인팀 critic 자동 + DB migration destructive 자리 안내·자동 실행 X + push 후 CI/CD 자동 deploy 인지 |
| **library** | 공개 API 변경 자리 _semver 영향 분석_ + export 일관성 + 사용 예시 갱신 권장 |
| **api** | endpoint·body·error 일관성 (spec contract) + auth 변경 자리 보안 검토 |
| **cli** | 명령·옵션 일관성 + input/output 형식 + exit code |
| **research** | entry point 변경 자리 재현 명령 갱신 + configs 변경 시 spec 동기화 + 예상 metric 검증 |

복수 mode 시 _해당하는 logic 모두_ 활성화.

### §6.5. 산출물 폴더 컨벤션 정리

| skill | 산출물 폴더 |
|---|---|
| `autopilot-research` | `.claude_reports/research/<topic>/` |
| `analyze-project` | `.claude_reports/analysis_project/{code,paper,doc}/` (code mode 자리에 lab 사전 4 종 자료 포함) |
| `autopilot-spec` | `.claude_reports/specs/<name>/` (mode 무관 한 폴더, 안에 `01_spec/PRD.md` 의 mode 별 섹션) |
| `autopilot-design` (단독) | `.claude_reports/designs/<name>/` |
| `autopilot-design` (spec 위임) | `.claude_reports/specs/<name>/02_design/` |
| `autopilot-code` (spec 있음) | `.claude_reports/specs/<name>/dev_log/<date>_<slug>/` |
| `autopilot-code` (spec 부재) | `.claude_reports/plans/<date>_<slug>/` |
| `autopilot-lab` | `.claude_reports/experiments/{date}_{slug}/` + `.claude_reports/experiments/_RUNLOG.md` (timeline) |
| `autopilot-draft` | `.claude_reports/documents/<date>_<name>/` |
| `autopilot-refine` | 대상 artifact 안 v{N+1} 갱신 |
| `autopilot-apply` | 자체 artifact_dir 없음 — `.claude_reports/` _밖_ 실제 source 편집 (git branch 위) + 로그는 cheatsheet artifact 의 `_internal/apply/` |

### §6.6. DEPRECATED sub-skill (2026-05-25)

- `app-build` → autopilot-code 의 spec-aware mode 가 흡수
- `app-qa` → autopilot-code spec-aware mode 안 검증 단계가 흡수
- `app-ship` → `autopilot-spec --mode setup-only` 가 흡수
- `app-iterate` → autopilot-code 호출 자체가 iteration

`autopilot-app` 자체 (이전 skill name) → `autopilot-spec` 로 일반화 (mode 5종 + 다중 + auto 지원). 산출물 폴더 `apps/<name>/` → `specs/<name>/`.

본 4 sub-skill 파일은 _레거시 참조_ 용으로 보존. 신규 호출 자리 X.
