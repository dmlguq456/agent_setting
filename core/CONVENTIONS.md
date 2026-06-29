# Conventions — Family-Wide Operational Rules

> 본 문서는 autopilot family 전체에 적용되는 _운영 규칙·정의_의 **단일 source of truth**. `DESIGN_PRINCIPLES.md`가 _architectural design_(orchestrator/skill/agent 분리, interface contract 등)을 다룬다면, 본 문서는 _operational conventions_(QA level 정의, model-role 표기, family-wide flag 정책 등)을 다룬다.
>
> **자동 로드 메커니즘**: runtime adapter bootstrap 의 "Source of Truth"에 본 파일이 등재되어 세션 시작 또는 관련 작업 시 인지. QA·model-role·family-wide flag 관련 작업 시 메인 에이전트가 본 파일을 직접 read해 정의를 가져옴. Claude Code adapter 의 구현 파일은 `adapters/claude/CLAUDE.md`.
>
> **자동 propagation**: `/sync-skills`의 Step 5b.5가 본 문서를 canonical로 cross-doc grep해 drift 보고. `--auto-fix` flag로 자동 propagation 수행 (default는 report-only).

---

## §1. QA Levels (canonical)

### §1.1. 5단계 공통 정의

| Level | Quality reviewer (parallel) | Fact-checker¹ (parallel) | External adversary (parallel) | Max round | 비고 |
|---|---|---|---|---|---|
| **quick** | 1× fast reviewer | skip | skip | 1 (강제) | refine 단계 skip / 1라운드 강제 종료 / 🔴 잔존 시 `unresolved.md` 에 기록만 |
| **light** | 2× fast reviewers (다른 axes²) | skip | skip | 1 | 사소 작업 — refine 단계 skip |
| **standard** | 1× deep reviewer + 2× fast reviewers (다른 axes²) | 1× fast fact-checker | skip | 1 | 간단 작업 — refine 단계 가능 |
| **thorough** | 2× deep reviewers + 2× fast reviewers (다른 axes²) | 1× fast fact-checker | skip | 2 | **default** — refine 단계 가능 |
| **adversarial** | 2× deep reviewers + 2× fast reviewers (다른 axes²) | 1× fast fact-checker | 1× external adversary (`codex-review-team` in current adapters) | 2 + external 1 | high-stakes. **research/doc 트랙은 + `Agent(연구팀 claim-verify)`** (적대적 외부 진위 — N-vote default-refute, WebSearch 모순 탐색; fact-check 와 보완층). code 트랙은 외부 claim 없어 미적용 |

¹ Fact-checker 는 _doc/research/refine 파이프라인_ 에만 적용. autopilot-code 계열 (init-plan / refine-plan / execute-plan / run-test) 은 fact-checker 없음 — ground-truth 가 코드 자신이라 verbatim 대조 무용.

² 다중 reviewer 는 _다른 axes_ 분담: deep reviewer 는 도메인 expertise / methodology / completeness / safety 같은 고추론 axis, fast reviewer 는 coverage·typo·표기 일관성·structure·verbatim matching 같은 비용 효율 axis. 각 skill SKILL.md 가 자기 axis 분담 명시.

> **`quick` 는 모든 autopilot mode 공통의 경량 tier**: 작은 자연어 요청·tweak 도 quick 으로 돌려 plan·log·snapshot artifact 를 남긴다 (1 라운드 강제 / refine 단계 skip). runtime adapter bootstrap 이 강제하는 "작업은 해당 autopilot-* 경유로 산출물 기록" 원칙의 비용 거의 0 인 경로 — 누적 drift 를 막는다.

### §1.2. External adversary availability 정책 (adversarial 전용)

- 현재 구현: `codex-review-team` → Codex CLI (GPT-5) external review
- Adversarial 선택 전 adapter 가 external adversary availability 를 확인한다. Claude Code adapter 는 `codex --version 2>/dev/null` 를 사용한다.
- 실패 시: `--qa adversarial` _명시_ 호출 → fail loudly / auto-detect로 adversarial 선택 → Thorough로 silent fallback
- external adversary 는 `adversarial-review --wait --scope auto` 실행 → `_internal/{stage}_reviews/round_{N}_external.md` 또는 adapter-specific legacy path (`round_{N}_codex.md`) 작성

### §1.3. opt-out flags (orthogonal)

- `--no-fact-check` — 모든 level에서 fact-checker 단독 skip (`quick`/`light`는 어차피 skip이라 무의미)
- `--no-style-audit` — Stage B.5 style aspect skip (refine 계열만)

이 두 flag는 `--qa` level 무관하게 적용되며, fact-checker / style audit을 끄는 _유일한_ 메커니즘 (ad-hoc prompt로 무시 불가). **autopilot-refine · audit 전용** — 다른 skill의 argument-hint에 노출되면 drift.

### §1.4. Skill별 사용 매트릭스

| Skill | Supported levels | Default | Adversarial | Fact-checker | 비고 |
|---|---|---|---|---|---|
| `autopilot-research` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | adversarial = thorough + external adversary + **claim-verify**(Step 4b 적대적 외부 진위). doc 트랙(draft/refine)도 adversarial 시 claim-verify 적용 후보 |
| `autopilot-code` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ (dev only; debug 는 thorough 로 downgrade) | **X** (code 는 fact-checker 없음) | |
| `autopilot-lab` | quick/light/standard/thorough/**adversarial** | `light` | ✓ | **X** (실험 prototype — code 와 동일 — fact-checker 없음) | default 가 light 인 이유: 실험 prototype 빠른 cycle 1순위. 사용자 high-stakes 발화 (논문 결과·외부 공개) 시 standard+ 자동 상향 |
| `autopilot-draft` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | |
| `autopilot-refine` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | standard+ | default 변경 (이전 quick → thorough) |
| `autopilot-spec` | quick/light/standard/thorough/**adversarial** | `thorough` | ✓ | **X** (spec 은 청사진 — verbatim 대조 대상 아님) | `quick` = 작은 spec tweak·update mode (기존 prd.md 갱신) 자리 — ad-hoc 직접 Edit 대신 quick 으로 돌려 snapshot·log artifact 를 남김 |
| `autopilot-note` | quick/light/standard/thorough/**adversarial** | `light` | ✓ | standard+ | routing skill — default light (routine cron). standard+ 자리는 주말 묶음·노션 migration 검수. fact-check 는 source ↔ 카드 본문 verbatim 대조 |
| `autopilot-apply` | — (`--qa` 없음) | — | — | **X** | verify = build/compile gate (latexmk) + latexdiff. reviewer QA loop 아님 — `run-test` 의 build 검증과 동류. ground-truth 는 컴파일 결과 |
| `analyze-user` | **adversarial (고정)** | `adversarial` | ✓ (강제) | standard+ | user profile 정확성 critical — qa 협상 불가, 다른 level 명시해도 adversarial 로 force |
| `audit` | — | — | — | `--no-fact-check` flag | `--qa` 대신 `--scope` 사용; fact-check 는 Stage B.5 에서 별도 |
| `init-plan` (sub) | quick/light/standard/thorough/adversarial | auto-detect from scope (plan frontmatter override) | ✓ | X | autopilot-code 내부 |
| `refine-plan` (sub) | quick/light/standard/thorough/adversarial | inherit from plan frontmatter | ✓ | X | autopilot-code 내부 |
| `execute-plan` (sub) | inherit | inherit | inherit | X | autopilot-code 내부 |
| `run-test` (sub) | **forced thorough** (`--qa` 무시) | thorough | auto-upgrade if external adversary available | X | 항상 2팀 병렬, external adversary 가용 시 자동 상향 |
| `final-report` (sub) | 1× fast writer (level-independent) | — | — | — | 모든 level 에서 writer 는 항상 fast writer |
| `init-doc-strategy` (sub) | quick/light/standard/thorough/adversarial | inherit from autopilot-draft | ✓ | standard+ | autopilot-draft 내부 |
| `refine-doc` (sub) | quick/light/standard/thorough/adversarial | inherit | ✓ | standard+ | autopilot-draft 내부 |

> _Sub-skill_ (init-plan / refine-plan / execute-plan / run-test / final-report / init-doc-strategy / refine-doc): orchestrator가 결정한 `--qa` 값을 그대로 받음. 직접 호출 시는 자체 default 사용.

---

## §2. Model Role 표기 (canonical)

공통 계약은 concrete model name 이 아니라 _model role_ 을 쓴다. `opus` / `sonnet` / `gpt-*` 같은 이름은 adapter 구현값이다. 새 cross-tool 문서·skill·README 는 아래 role 을 먼저 쓰고, Claude Code 재현값은 `adapters/claude/README.md` 에서 mapping 한다.

### §2.1. Portable model roles

| Role | 의미 | 대표 용도 |
|---|---|---|
| `fast reviewer` | 낮은 비용·낮은 지연으로 넓게 훑는 reviewer. 정답지가 있거나 surface/coverage/format/verbatim matching 비중이 큰 축 | quick/light QA, style/coverage/cross-ref, fact-check narrow matching |
| `deep reviewer` | 높은 추론력·도메인 판단·방법론 검토가 필요한 reviewer | standard+ 핵심 quality review, methodology/domain/safety/security, architecture risk |
| `fast fact-checker` | 창의적 판단을 억제하고 source artifact 와 claim 을 좁게 대조하는 fast role | citation/venue/year/metric/lineage/table value 검증 |
| `fast writer` | 이미 검증된 artifact 를 사용자-facing summary 로 조립하는 저비용 writer | final report, short synthesis |
| `deep maker` | 생성 자체가 미학·전략·도메인 판단을 요구하는 role | plan, research synthesis, visual design, editorial rewrite |
| `external adversary` | 같은 런타임과 다른 독립 engine 으로 hostile review 를 수행하는 role | `--qa adversarial` 추가 검토 |
| `orchestrator` | 호출·도구 실행·결과 병합·한국어 재정리 담당. 실제 판단 role 과 분리 가능 | wrapper agent, headless dispatch, external adversary adapter |

### §2.2. Adapter mapping requirement

각 adapter 는 위 role 을 자기 런타임의 concrete model / tool / prompt profile 로 매핑해야 한다. 매핑은 “기존 품질 재현”의 계약이다. Claude Code adapter 는 기존 운용을 그대로 보존하기 위해 `fast reviewer/fact-checker/writer = sonnet`, `deep reviewer/maker = opus`, `external adversary = Codex CLI (GPT-5)`, `external adversary orchestrator = sonnet` 으로 둔다.

### §2.3. Role profile operation matrix

각 agent의 frontmatter `model:` 필드는 _adapter-specific sub-agent runtime hint_ 이다. 공통 의미는 아래 `Portable role` 열이 canonical 이며, frontmatter 값은 Claude Code adapter 의 현재 재현값이다.

| Agent | Portable role | Claude adapter frontmatter | 실제 작동 |
|---|---|---|---|
| `기획팀` (plan-team) | deep maker | opus | deep maker 단일 |
| `품질관리팀` (qa-team) | variable reviewer | opus | **가변** — review 모드: Light=1× fast reviewer / Standard=1× deep reviewer / Thorough=doc·research·refine 갈래 2× deep reviewers parallel · code 갈래 (init-plan/refine-plan/execute-plan) 1× deep reviewer + 1× fast reviewer parallel (completeness reviewer 는 mechanical 매칭 비중이 커 fast role 이 cost-efficient). test 모드 (run-test): Agent A=fast coverage + Agent B=deep accuracy (2026-05-22 테스트팀 흡수) · security-review 모드: deep reviewer |
| `연구팀` (research-team) | variable research reviewer | opus | **가변** — default deep maker/reviewer (Plan Review·domain reviewer); fact-checker subrole·light QA는 fast fact-checker/reviewer |
| `자료팀` (material-team) | deep maker default, fast tool worker subroles | opus | 자료 수집·시각·분석. browser-fetch/pdf-extract/web-image-search 는 fast tool worker, figure-gen/data-script 는 deep maker |
| `개발팀` (dev-team) | fast implementer default | sonnet | fast implementer 단일. 복잡한 API·라이브러리 설계는 deep maker 로 상향 가능 |
| `디자인팀` (design-team) | deep maker with fast verifier | opus | maker=deep maker, critic=fast/deep reviewer by nuance, verifier=fast reviewer |
| `편집팀` (editorial-team) | deep maker/editor with fast reviewer subrole | opus | translate/polish 는 deep editor, review 는 fast reviewer |
| `codex-review-team` | external adversary orchestrator | sonnet | **Codex CLI (GPT-5)** — actual review·analysis는 external adversary engine 이 수행; sub-agent 본체는 호출·결과 한국어 재정리만 담당 |

---

## §3. Hard Cross-Doc Invariants (sync-skills `--check`가 자동 검사)

1. 각 SKILL.md / README 에서 §1.1 5단계 정의의 **Quality reviewer / Fact-checker / External adversary 컬럼 wording**은 본 문서와 의미 일치 (사소한 표현 차이는 허용, 의미가 다르면 drift).
2. **adversarial** 정의는 반드시 `thorough + 1× external adversary` (+ research/doc 트랙은 `1× 연구팀 claim-verify`). 현재 Claude Code adapter 구현명은 `codex-review-team`. 자주 잘못 적힌 패턴: `standard + external/Codex` — _틀림_ (base 는 thorough).
3. autopilot-code의 QA 표에 fact-checker가 적힌 곳이 있으면 drift (code는 fact-checker 없음).
4. `--no-fact-check` / `--no-style-audit`는 autopilot-refine / audit 외 다른 skill에 노출되면 안 됨.
5. `codex-review-team`의 model 표기가 `opus` 단독이면 drift — 실제 review는 external adversary engine(Codex CLI GPT-5), wrapper 는 orchestrator role. §2 매트릭스에 따라 "external adversary + fast orchestrator" 같이 분리 표기.
6. **의도 동반 (2026-06-11)**: 지침·규칙·hook 의 신설/강화에는 _왜(계기 사건 + 날짜)_ 를 인라인 주석 또는 commit message 에 남긴다 — 예: "(drill g2 가 잡은 구멍, 2026-06-11)". 의도 없는 규칙은 시간이 지나면 정리도 못 하고 의심도 못 하는 짐 — 연수 루프가 _의도 불명 지침_ 을 정리 후보로 보고한다. 의도의 최상위 보존 형태는 drill 케이스 (실행 가능한 의도 — 오답노트 승격 채널).
7. **의미↔규칙 경계 (2026-06-22, worklog-board 참사)**: 의미 판단을 규칙·토큰 매칭 스크립트로 내리지 말 것 — spec 이 "의미 판단"을 명시하면 구현이 그 의미를 capture 했는지 검증한다 (상세·검증 절차·3선택 = DESIGN_PRINCIPLES §0.7).

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

**모든 skill은 에이전트가 _프로젝트 루트에서 실행됨_을 전제로 함**:
- `.agent_reports/`는 새 표준 artifact root 로 _현재 작업 디렉토리_에 생성·읽기·쓰기
- `.claude_reports/`는 기존 프로젝트를 위한 legacy alias 로 읽기·쓰기 호환
- 문서 표기 `<artifact-root>` 는 런타임에서 `.agent_reports` 를 우선 사용하고, `.claude_reports` 는 이미 존재하고 `.agent_reports` 가 없을 때만 legacy fallback 으로 사용한다는 뜻이다. 쉘 예시는 실행 전 `REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports` 로 치환한다.
- analyze-project는 현재 dir의 파일을 읽음 (code/paper/doc 모드)
- autopilot-code는 현재 dir에서 코드 변경
- autopilot-{draft,research,refine}는 artifact root 하위 영속 산출물을 input으로 implicit 인지 (cross-project 작업은 `cd <other>` 후 별도 세션)

> **gitignore 전제 (불변식)**: skill 산출물 폴더 `.agent_reports/`는 _프로젝트 repo 에 커밋하지 않는다_ — 에이전트 작업 산출물(plan·log·snapshot·reviews·lock)이지 소스가 아니다. 새 프로젝트에서 처음 산출물을 만들 때(또는 `git`-tracked repo 에서 처음 호출될 때) `.agent_reports/`가 `.gitignore`에 없으면 한 줄(`.agent_reports/`) 추가한다 (이미 있거나 git repo 가 아니면 skip). legacy 프로젝트는 `.claude_reports/`를 같은 규칙으로 취급한다. OPERATIONS §5.8 의 worktree symlink 가드·`.pipeline-lock` transient 처리도 이 gitignore 전제 위에서 성립. **예외 — `<agent-home>` (하네스 repo 자신, 2026-06-11 사용자 결정)**: 이 repo 는 `.agent_reports` 를 _커밋한다_ — 세팅 개선의 research·audit·plan 이력이 곧 repo 의 자산 (transient `.pipeline-lock`·`.untracked*` 만 ignore). 스킬셋 본작업도 파이프 경유로 `plans/` 사이클을 남기는 정식 프로젝트로 다룬다.

모든 입력은 _프로젝트 컨텍스트 내부의 영속 산출물_ (`<artifact-root>/analysis_project/*`, `<artifact-root>/research/{topic}/`)에서 옴. 외부 폴더를 직접 가리키는 flag는 family 에 없음. 외부 raw 자료가 있으면 먼저 `analyze-project --mode {paper|doc}`로 영속 산출물화.

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

#### §5.4.1. autopilot-research → `<artifact-root>/research/{topic}/`

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

#### §5.4.2. autopilot-draft → `<artifact-root>/documents/{date}_{name}/`

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

#### §5.4.3. 코드 트랙 = `spec/` (청사진) + `plans/` (작업) 2-bucket

> **2026-06-01 평면화: 1 repo = 1 spec.** 청사진은 `spec/`, 작업은 `plans/<date>_<slug>/` — `<project>` 중간 층 없음. repo 의 artifact root 가 곧 그 repo 의 spec. `<project>` 이름을 "고르는" 자리가 없어 네이밍 drift 제거.
>
> **모노레포 예외 (드묾)**: 한 repo 에 _독립 deliverable 여럿_ (web + api + shared lib 등) 이고 각자 별도 PRD·계약이 필요할 때만 `spec/<component>/` + `plans/<component>/<date>_<slug>/` 로 명시 분리. 단일 제품 repo 는 항상 flat. 숫자 prefix (00_/01_/02_/05_) 폐지 — 평이한 이름.

**`spec/`** — repo 당 _한 개_ 청사진 (안정 layer):

```
spec/
├── prd.md                [T1] 핵심 명세 (stack·data_model·ui_flow·api_contract 를 섹션 또는 인접 파일로; app 처럼 큰 자리는 data_model.md/ui_flow.md/api_contract.md 인접 허용)
├── ship.md               [T1] 배포 기록 (autopilot-ship; 배포 자리 생기면)
├── stack.md              [T2] 환경·스택 결정 (이전 00_init; 없으면 prd 섹션)
├── design/               [T2] 디자인 자산 + mockup (autopilot-design 위임; 자산 있을 때만 폴더)
├── pipeline_state.yaml   [기계] --from 재개용 stage state
└── _internal/            [T3] reviews·raw + versions/v{N}/prd.md (구 spec 스냅샷)
```

> **Spec versioning = doc 트랙과 동일 원리** (별도 메커니즘 X — §5.2 versions/ 재사용). `prd.md` 가 _항상 최신_(T1) — 사용자는 최신만 봄. **major 변경 시 autopilot-spec 의 refine 자리가 직전 `prd.md` → `_internal/versions/v{N}/prd.md` 자동 snapshot 후 덮어씀** (doc 은 autopilot-refine, spec 은 autopilot-spec refine — 역할 경계만 다르고 메커니즘 동일). minor 변경은 직접 Edit + pipeline_summary minor-log (누적 5 → `/audit` alert). 사용자 수동 버전 관리 X.

**`plans/<date>_<slug>/`** — 작업 사이클 (반복 layer, 이전 dev_log + 이전 spec-less plans 통합):

```
plans/<date>_<slug>/
├── pipeline_summary.md   [T1]
├── plan/                 [T1] plan.md · plan_ko.md · checklist.md
├── dev_logs/             [T2] execute-plan 변경 narrative
├── test_logs/            [T2] test_report.md (failure 시 봄)
└── _internal/            [T3] plan_reviews/ · test_reviews/
```

> 각 폴더 _user-facing(위, T1) vs 기계·reviews(`_internal/`, T3)_ 2분이 핵심. 코드 산출물에 autopilot-refine 적용 안 됨 (기본) — 버전은 git 권장.

#### §5.4.4. analyze-project (3 modes) → `<artifact-root>/analysis_project/{code,paper,doc}/`

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

본 절은 _artifact_dir 을 직접 만드는 orchestrator-level skill_ (`analyze-project`, `autopilot-{research,spec,code,lab,ship,draft,refine,design,note}`, `audit`) 에만 적용. sub-skill (`init-plan` / `refine-plan` / `execute-plan` / `run-test` / `final-report` / `init-doc-strategy` / `refine-doc`) 은 orchestrator 가 만든 폴더 안에서 동작하므로 본 참조를 강제하지 않는다.

해당 orchestrator-level skill 의 SKILL.md 는:
- 산출물 경로 명시 시 _구체적 file path_가 아닌 _Tier_ 또는 _폴더 컨벤션_으로 표현
  - 좋음: "review log → `_internal/reviews/round_{N}.md`"
  - 나쁨: "review log → `{artifact_dir}/strategy_reviews/round_{N}_quality.md`" (절대 경로 hardcode → drift 위험)
- 본 절 참조 한 줄 포함:
  ```markdown
  > 산출물 폴더 컨벤션: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier)
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

## §5.8~§5.11 → OPERATIONS.md

> **이동(2026-06-23)**: Pipeline Lock(§5.8)·Git preflight(§5.9)·worktree dispatch(§5.10)·`<agent-home>` push(§5.11) → **[`OPERATIONS.md`](OPERATIONS.md)**. § 번호·anchor 보존(`OPERATIONS.md#59-…`). git 운영 단일 출처.

## §6. Autopilot-* 흐름 매트릭스 (사용자 호출 단위)

> 본 절은 autopilot-* skill 들의 _작업 본질·역할·경계_ 의 단일 source of truth. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙. 자세한 사용자 향 청사진: [`WORKFLOW.md`](WORKFLOW.md).

### §6.1. 작업 본질 매트릭스 (대칭 강제 X)

| 작업 종류 | 사전 (외부 조사·내부 분석) | 신규 의도·청사진 | 자산 작업 (신규·기존) |
|---|---|---|---|
| **문서** (paper / presentation / 보고서 / proposal / rebuttal) | `autopilot-research` (academic / market) + `analyze-project --mode paper/doc` | `autopilot-draft` (신규 strategy + draft) | `autopilot-refine` (기존 정정·확장) |
| **코드 (모든 자리 — 라이브러리·연구·앱·CLI·API)** | `autopilot-research` (academic / technology) + `analyze-project --mode code` | **`autopilot-spec`** (mode 5종 + 복합 + auto. 모든 mode 가 PRD + Architecture Diagrams + **scaffold (skeleton 코드)** 통일 산출. ML / DL 자리는 Phase 1.5 pretrained ckpt 사전 동작 점검 자동. 중간 컨펌 6-8 자리 default) | **`autopilot-code`** (spec mode 별 분기 자동 — _layout 위 logic 추가_ 자리만) |
| **실험 prototype (ML / one-shot script)** | `analyze-project --mode code` 의 4 종 실험 자료 (`experiment_conventions` / `experiment_readiness` / `cleanup_candidates` / `similar_models`) + 직전 실험 `_RUNLOG.md` | — (spec 없이 빠른 cycle 1순위) | **`autopilot-lab`** (반복 호출, STORY+RUNLOG 누적; 졸업 자리 `autopilot-code`) |
| **공통 시각 자산** | — | `autopilot-design` (신규 디자인 사이클) | `autopilot-design` 재호출 (cycle 2+) |
| **공통 사용자 프로필** | — | `analyze-user --mode init` (aspect 7 종 — figure / writing / presentation / analysis / domain / collab / **coding_convention**) | `analyze-user --mode update` |

> **`coding_convention` aspect 의 자리** (2026-05-26): 사용자 cross-project 코드 일관 패턴 (model 폴더 / config / prefix / preferred layer / framework / metric / log·ckpt / seed) 을 `mem profile 07_coding_convention` 에 누적. autopilot-lab / autopilot-spec / autopilot-code / 개발팀 _new-lib_ 의 _cross-project default · fallback_ 자리 (2순위). **개별 프로젝트의 `analysis_project/code/experiment_conventions.md` 가 1순위 source of truth** — 충돌 자리는 per-project 우선, `mem profile 07` 은 _per-project 부재·빈 자리만_ 보강. 사용자 첫 호출 자리에 source 폴더는 cwd 자동 발견 또는 `--source <path>` 로 명시한다.

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
/analyze-project --mode code                        ← (선택, 기존 코드 있을 때)
/autopilot-spec --mode app "X 앱"                  ← PRD + 스택 + scaffolding + skeleton
/autopilot-design --app X                          ← (옵션) 시각 사이클
/autopilot-code "Y 기능"                            ← app mode 추가 logic (디자인팀 critic + DB 안전 + push 자동 deploy) — 반복
/autopilot-ship                                     ← 기능 어느 정도 완성 후 (첫 ship setup·env·domain·migration. 재호출 가능)
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
| 공개 API 변경 (export 추가·제거·시그니처) [library] | 공개 API + 사용 예시 + 호환성·versioning(semver 영향) + Component(module dep) |
| CLI 명령·옵션 변경 [cli] | 명령·옵션·exit code + 사용 예시(README) + Component(명령 트리) |

**호출 자리**:
- `autopilot-spec` refine (사용자 의도 변경) → 영향 자리 자동 list → confirm → 일괄
- `autopilot-code` 가 spec 영향 변경 감지 → 묶음 갱신 plan → confirm → autopilot-spec back-jump

**Architecture Diagrams 기본 포함**: app / api mode 의 Component + Deployment 두 자리만. library 의 Component (module 의존) 는 옵션. ER / Sequence / Activity / State / Class 는 _복잡 자리·사용자 명시 요청_ 자리만.

### §6.4. autopilot-* family 의 컨텍스트 자동 감지 (신규 vs 재진입 통합 패턴)

autopilot-* 5 개 (`code` / `spec` / `lab` / `research` / `design`) 모두 _호출 자리에서 발화 + cwd 검사로 신규 vs 재진입 자동 분기_. 사용자가 `--from <step>` 명시 없이도 동작 — 메인 에이전트가 발화 의도 분류 + 컨펌.

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
| `autopilot-code` | spec 발견 자동 분기 + dev/debug mode + `--from plan/refine/execute/test/report` | `spec/pipeline_state.yaml` (있으면) |
| `autopilot-spec` | 신규 / refine v{N+1} — `--from spec/scaffold` 등 step 별 | `spec/pipeline_state.yaml` |
| `autopilot-lab` | 신규 실험 / 재진입 — `--from spec/scaffold/run/summary` | `experiments/{date}_{slug}/pipeline_state.yaml` + `_RUNLOG.md` |
| `autopilot-research` | 신규 topic / `--from search/analyze/report` | `research/<topic>/pipeline_state.yaml` |
| `autopilot-design` | 신규 cycle / 재호출 — `--from init/refs/tokens/components/review/handoff` | `designs/<name>/design_state.yaml` 또는 `spec/design/design_state.yaml` |

> **autopilot-draft ↔ autopilot-refine 의 _분리_** 는 _자동 분기_ 패턴과 별개. 본 두 skill 은 _작업 본질 자체_ 가 다름 (draft = 신규 문서 작성 / refine = cross-artifact 정정, default qa 다름). 분리 유지 — 메인 에이전트가 자연어 발화 ("X 새로" vs "X v2") 로 자동 분기.

### §6.4-staleness. analyze-project 산출물 자동 갱신 (혼합 분기)

코드 변경 후 `<artifact-root>/analysis_project/code/` 자료가 _stale_ 자리 차단:

| 변경 종류 | 분기 | 담당 |
|---|---|---|
| 작은 변경 (한 module 안 / interface_reference 한 행 / signature) | (A) 직접 Edit | **autopilot-code** 의 Step 7 (final-report 후) |
| 큰 변경 (새 module / 모델 폴더 / cleanup / 4 종 실험 자료 영향) | (B) analyze-project incremental 자동 호출 | autopilot-code Step 7 → `/analyze-project --mode code --skip-qa` |

analyze-project 자체는 `_last_run.yaml` 기반 **incremental update** default — 기존 산출물 발견 시 변경 파일만 재분석 (cost 10-20%). `--full` 명시 시 전체 재.

사용자 `"분석 자료 update skip"` / `"--no-analyze-update"` 발화 시 Step 7 skip.

본 자리는 _자동 staleness 차단_ — 사용자가 매번 _analyze-project 재호출 의무_ 부담 해소.

### §6.4-legacy. autopilot-code 의 컨텍스트 자동 감지

호출 자리에서 _cwd / spec 파일_ 검사로 자동 분기:

#### 1단계 — spec 존재 여부

| 감지 조건 | 처리 |
|---|---|
| `<artifact-root>/spec/pipeline_state.yaml` 존재 | spec 자동 Read + 그 안 `mode` 배열 따라 _추가 logic_ 활성화. 산출 `plans/<date>_<slug>/` |
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
| `autopilot-research` | `<artifact-root>/research/<topic>/` |
| `analyze-project` | `<artifact-root>/analysis_project/{code,paper,doc}/` (code mode 자리에 lab 사전 4 종 자료 포함) |
| `autopilot-spec` | `<artifact-root>/spec/` (청사진 한 폴더 — `prd.md` 의 mode 별 섹션 + stack.md·design/·ship.md) |
| `autopilot-ship` | `<artifact-root>/spec/ship.md` (배포 자료 누적, single source) + 프로젝트 root 의 `vercel.json` / `.github/workflows/deploy.yml` / `.env.example` (CI/CD·env 외부 자료, artifact root 밖) |
| `autopilot-design` (단독) | `<artifact-root>/designs/<name>/` — _decision record_ (refs·mockup·결정 근거·specimen). **토큰 _사본 없음_** — 토큰은 앱 실제 파일(globals.css `@theme`/tokens.css)이 단일 계약 (DESIGN_PRINCIPLES §9) |
| `autopilot-design` (spec 위임) | `<artifact-root>/spec/design/` (동일 — decision record; 토큰은 앱 파일) |
| `autopilot-code` | `<artifact-root>/plans/<date>_<slug>/` (spec 유무 무관 — 청사진은 `spec/`, 작업은 항상 `plans/`) |
| `autopilot-lab` | `<artifact-root>/experiments/{date}_{slug}/` + `<artifact-root>/experiments/_RUNLOG.md` (timeline) |
| `autopilot-draft` | `<artifact-root>/documents/<date>_<name>/` |
| `autopilot-refine` | 대상 artifact 안 v{N+1} 갱신 (`_internal/versions/v{N}/`) |
| `autopilot-note` | `<artifact-root>/notes/<date>/` (자체 routing log, T1/T2/T3) + `<target>/cards/**.md` 본문 append (default `~/notes/cards/`) + `<target>/digests/<date>.md` 누적 + `<target>/_triage/{date}_<seq>.md` (사용자 NAS 자리). 본 skill 산출물과 진본 카드 자리 분리 |
| `autopilot-apply` | 대상 artifact 는 artifact root 밖 실제 소스 (e.g., `main.tex`). 버전 자리는 git branch + commit (mutation 마다 한 commit) — `_internal/versions/` 자리 X |
| `autopilot-apply` | 자체 artifact_dir 없음 — artifact root _밖_ 실제 source 편집 (git branch 위) + 로그는 cheatsheet artifact 의 `_internal/apply/` |

### §6.6. Autopilot Intake Gate
<!-- M2 §4.3 intake 게이트, 2026-06-23 — 디자인 스튜디오 핸드오프 -->

(입력 부족 시 구조화 질문 먼저)

autopilot-* 진입 직후, 비가역 결정 커버리지가 미달이면 **1라운드 구조화 질문(AskUserQuestion)을 먼저** 던진다. draft 트랙의 Step 0 · research 트랙의 Step 1.5가 이 패턴의 기존 track-specific 인스턴스이며, spec/code/design 트랙은 본 섹션을 통해 동일 패턴을 새로 채택한다.

#### 4 속성 (모든 트랙 공통)

1. **타입 선택지 제공** — 질문마다 열거된 선택지(enumerated options)를 제시. 사용자가 특정 값을 고르도록 구조화.
2. **항상 탈출구** — 모든 질문에 Other(자유 입력) 또는 skip(기본값으로 진행) 옵션을 포함. 강제 응답 없음.
3. **앞 1라운드만** — 진입 직후 한 번. 이후 재질문 없음.
4. **비가역 결정 커버리지만** — 나중에 바꾸기 비싼 결정(스택·API surface·배포 대상·톤·브랜드)에 한정. 구현 디테일·가역 선택은 포함 X.

#### AskUserQuestion 사용 형식

```
AskUserQuestion(questions=[{
  "question": "<질문 텍스트>",
  "header": "<항목 레이블>",
  "multiSelect": false,
  "options": [
    {"label": "...", "description": "..."},
    ...
  ]
}])
# 탈출구: 사용자는 Other(자유 입력) 또는 skip(기본값으로 진행) 선택 가능 — 항상 1라운드만.
```

> **§0.5 정렬**: "입력 충분 vs 부족" 판단은 LLM 의미 판단(semantic judgment) — 토큰·키워드 규칙으로 기계 게이트 불가. 따라서 본 게이트는 AskUserQuestion _instruction_ 게이트로 발동 (LLM 이 판단, 발동은 구조화) — hard hook 아님. (DESIGN_PRINCIPLES §0.5 line 35 exception 참조.)

**구체적 예시 (design 트랙)**:

```
AskUserQuestion(questions=[{
  "question": "비주얼 방향성·톤은?",
  "header": "Visual tone",
  "multiSelect": false,
  "options": [
    {"label": "Warm",    "description": "따뜻한 색·둥근 모서리"},
    {"label": "Cool",    "description": "차분한 블루·그레이 계열"},
    {"label": "Neutral", "description": "무채색 중심, 톤 최소"}
  ]
}])
# 탈출구: 사용자는 Other(자유 입력) 또는 skip(기본값으로 진행) 선택 가능 — 항상 1라운드만.
```

#### 트랙별 질문 뱅크 (비가역 결정 상위 5개)

| 트랙 | 비가역 결정 top-5 |
|---|---|
| **문서 (draft)** | 청중 · 분량/페이지 제한 · 산출 형태(논문/슬라이드/산문) · 톤(defensive vs concessive / formal vs casual) · 마감·제약 |
| **연구 (research)** | 조사 깊이(shallow/medium/deep) · 인용/연도 커트오프 · 분야 경계(예: speech-only vs audio-general) · 비교 축 우선순위(perf/cost/license) · 결정 목적(survey vs invest vs competitive-intel) |
| **앱 (spec app)** | 스택 · 인증 모델 · DB/영속성 · 배포 타깃 · 핵심 entity |
| **라이브러리·CLI (spec library/cli)** | 공개 API surface(exports) · versioning/semver 정책 · 명령·옵션 형태(cli) · 타깃 런타임/패키지 매니저 · 호환성 제약 |
| **디자인 (design)** | 비주얼 방향성·톤(warm/cool/neutral) · 타깃 디바이스 · 디자인 시스템 유무 · 브랜드 제약 · 산출 형태(standalone HTML vs project) |

> **코드(code/dev) 트랙 — spec 행 차용**: code(dev) 트랙에는 별도 질문 뱅크 행이 없다. spec 분기를 따른다 — app 프로젝트 → 앱 행, library/cli 프로젝트 → 라이브러리·CLI 행. 코드 세션은 이 매핑으로 어떤 질문 뱅크를 쓸지 판단.

#### 게이트 발동 조건 및 skip 조건

**발동**: 진입 직후, 입력이 비가역 결정 커버리지에 미달이면 1라운드 구조화 질문.

**Skip (4가지 — 별도 flag 없이 자동)**:
1. slash 직접 args로 충분히 명시됨
2. 사용자가 이미 해당 결정을 발화에서 명시
3. throwaway / untracked (`/track` 설정 시)
4. 재개 (`--from <stage>` — `pipeline_state.yaml`에 이미 캡처됨)

> **`--no-clarify` flag는 draft/research 전용**: spec/code/design 트랙에는 `--no-clarify` flag가 없다(확인됨). 위 4가지 skip 조건으로 flag 없이 자동 처리 — 존재하지 않는 flag를 찾지 않도록 주의.

#### §2 자율 진행 (응답 없을 때)

질문 발동 시 runtime adapter bootstrap 의 pause/autonomy rule 동일(Claude adapter: [`adapters/claude/CLAUDE.md`](../adapters/claude/CLAUDE.md) §2) — ScheduleWakeup 15-20분 동시 호출, 응답 없으면 추천 기본값으로 자율 진행(한 줄 보고).

#### 기존 track 인스턴스와의 관계

- **draft 트랙**: `autopilot-draft` Step 0 (Scope Clarification) — 본 게이트의 문서 트랙 인스턴스. `--no-clarify` flag로 skip 가능.
- **research 트랙**: `autopilot-research` Step 1.5 (Scope Clarification) — 본 게이트의 연구 트랙 인스턴스. `--no-clarify` flag로 skip 가능.
- **spec/code/design 트랙**: 본 섹션을 기준으로 신규 채택. flag 없이 위 4가지 skip 조건 적용.

## §7 → MEMORY.md

> **이동(2026-06-23)**: 통합 기억(§7.0~§7.5) → **[`MEMORY.md`](MEMORY.md)**. § 번호 보존. 메모리 단일 출처.
