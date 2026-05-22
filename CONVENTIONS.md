# Conventions — Family-Wide Operational Rules

> 본 문서는 autopilot family 전체에 적용되는 _운영 규칙·정의_의 **단일 source of truth**. `DESIGN_PRINCIPLES.md`가 _architectural design_(orchestrator/skill/agent 분리, interface contract 등)을 다룬다면, 본 문서는 _operational conventions_(QA level 정의, model 표기, family-wide flag 정책 등)을 다룬다.
>
> **자동 로드 메커니즘**: `CLAUDE.md`의 "Source of Truth"에 본 파일이 등재되어 세션 시작 시 README 부트스트랩을 통해 인지. QA·model·family-wide flag 관련 작업 시 메인 Claude가 본 파일을 직접 read해 정의를 가져옴.
>
> **자동 propagation**: `/sync-skills`의 Step 5b.5가 본 문서를 canonical로 cross-doc grep해 drift 보고. `--auto-fix` flag로 자동 propagation 수행 (default는 report-only).

---

## §1. QA Levels (canonical)

### §1.1. 5단계 공통 정의

| Level | Quality reviewer | Fact-checker (parallel) | Codex (parallel) | 비고 |
|---|---|---|---|---|
| **quick** | 1× sonnet, 1-pass | skip | skip | refine entire skip / loop 1라운드 강제 종료 / 🔴 잔존 시 `unresolved.md`에 기록만 |
| **light** | 1× sonnet, single-pass | skip (quality reviewer가 spot-check 커버) | skip | 경량 리뷰 |
| **standard** | 1× opus, single-pass | 1× sonnet, parallel¹ | skip | _doc/research/refine 한정_ — fact-checker는 cards/PDFs verbatim 대조 (venue/year/metric/citation) |
| **thorough** | doc/research/refine: 2× opus, parallel (다른 focus²) · code (init-plan/refine-plan/execute-plan): 1× opus + 1× sonnet, parallel (A=correctness focus opus / B=completeness focus sonnet, cost-aware) | 1× sonnet, parallel¹ | skip | 고위험 산출물 (final-version paper draft, public-facing report 등). code 갈래에서 completeness reviewer 가 sonnet 인 이유는 §2 비고 |
| **adversarial** | 2× opus, parallel (= thorough quality) | 1× sonnet, parallel¹ | 1× `Agent(codex-review-team)` parallel — Codex CLI (GPT-5) external review | _autopilot-code · autopilot-refine 전용_ — autopilot-draft / autopilot-research는 지원 X (thorough까지) |

¹ Fact-checker는 _doc/research/refine 파이프라인_에만 적용. autopilot-code 계열 (init-plan / refine-plan / execute-plan / run-test)은 fact-checker 없음 — code는 ground-truth source가 코드 자신이므로 quality reviewer만 운용.

² thorough에서 2개 quality reviewer는 _다른 axes_ 분담: 예: A=domain expert + methodology / B=content expert + quality / C=safety. 각 skill SKILL.md가 자기 axis 분담 명시.

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
| `autopilot-research` | quick/light/standard/thorough | `standard` | X | standard+ | thorough max |
| `autopilot-code` | quick/light/standard/thorough/**adversarial** | `standard` | ✓ (dev only; debug는 thorough로 downgrade) | **X** (code는 fact-checker 없음) | adversarial 전용 |
| `autopilot-draft` | quick/light/standard/thorough | `thorough` | X | standard+ | thorough max, default thorough |
| `autopilot-refine` | quick/light/standard/thorough/**adversarial** | `quick` | ✓ | standard+ | adversarial 전용 + default quick |
| `audit` | — | — | — | `--no-fact-check` flag | `--qa` 대신 `--scope` 사용; fact-check는 Stage B.5에서 별도 |
| `init-plan` (sub) | quick/light/standard/thorough/adversarial | auto-detect from scope (plan frontmatter override) | ✓ | X | autopilot-code 내부 |
| `refine-plan` (sub) | quick/light/standard/thorough/adversarial | inherit from plan frontmatter | ✓ | X | autopilot-code 내부 |
| `execute-plan` (sub) | inherit | inherit | inherit | X | autopilot-code 내부 |
| `run-test` (sub) | **forced thorough** (`--qa` 무시) | thorough | auto-upgrade if Codex available | X | 항상 2팀 병렬, Codex 가용 시 자동 상향 |
| `final-report` (sub) | sonnet 1× (level-independent) | — | — | — | 모든 level에서 writer는 항상 sonnet |
| `init-doc-strategy` (sub) | quick/light/standard/thorough | inherit from autopilot-draft | X | standard+ | autopilot-draft 내부 |
| `refine-doc` (sub) | quick/light/standard/thorough | inherit | X | standard+ | autopilot-draft 내부 |

> _Sub-skill_ (init-plan / refine-plan / execute-plan / run-test / final-report / init-doc-strategy / refine-doc): orchestrator가 결정한 `--qa` 값을 그대로 받음. 직접 호출 시는 자체 default 사용.

---

## §2. Agent Model 표기 (canonical)

각 agent의 frontmatter `model:` 필드는 _sub-agent runtime_ model. 실제 작업 시 가변 또는 외부 LLM 호출이 있는 경우 본문·매트릭스에 명시.

| Agent | frontmatter `model:` | 실제 작동 |
|---|---|---|
| `기획팀` (plan-team) | opus | opus 단일 |
| `품질관리팀` (qa-team) | opus | **가변** — Light=1× sonnet / Standard=1× opus / Thorough=doc·research·refine 갈래 2× opus parallel · code 갈래 (init-plan/refine-plan/execute-plan) 1× opus + 1× sonnet parallel (completeness reviewer 가 비교적 mechanical 매칭이라 sonnet 가 cost-efficient — code 의 ground-truth 가 코드 자신이므로 verbatim 비교 비중이 큼) |
| `연구팀` (research-team) | opus | **가변** — default opus (Plan Review·domain reviewer); fact-checker subrole·light QA는 sonnet (cost-aware verbatim matching) |
| `테스트팀` (test-team) | opus | opus + sonnet 혼합 (Agent A=sonnet coverage / Agent B=opus accuracy) |
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
