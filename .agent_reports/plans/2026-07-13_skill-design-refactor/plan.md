# Skill-Design Refactor — Implementation Plan

> mode: **refactor** (behavior-preserving) · date: 2026-07-13 · owner: autopilot-code · cycle 1
> 입력 청사진: `.agent_reports/spec/skill-design-refactor/prd.md` (SD-1~10 locked, D1·D3 resolved)
> 근거: `analysis_project/code/skill_design_audit{,_per_skill}.md` (file:line) · `_internal/scan_baseline.tsv` (정량 baseline)
> 실행 순서(SD-1): **core-first 계약 추가 → Cluster 2(SoT 통합) → Cluster 3(sprawl 추출) → Cluster 1(invocation 재분류·검증 게이트 후)**.
> 전 스텝 read-first 확정(2026-07-13): 아래 file:line·블록 범위는 live 스킬을 grep/sed 로 실측한 값.

---

## 0. 실행 원칙 (전 Cluster 공통)

- **behavior-preserving**: 이 refactor 는 신기능 0. pointer 화·references/ 추출·frontmatter flip 은 _내용을 옮길 뿐_ 의미를 바꾸지 않는다. 각 pointer 교체 후 원문과 SoT 텍스트가 semantic-equivalent 인지 diff 확인.
- **core-first (DESIGN_PRINCIPLES §0.8)**: `core/*.md` 를 먼저 편집 → `adapters/*` 미러는 `sync-skills` 재투영으로 파생. 손으로 adapter 미러를 선행 편집하지 않는다. 대상 core 파일: `core/CONVENTIONS.md`·`core/DESIGN_PRINCIPLES.md`·`roles/modes/design/_design_rules.md`(SoT 이미 존재).
- **SD-6 (각 Cluster 종료 게이트)**: Cluster 완료 시 반드시 `sync-skills` 실행 → (a) `README.md` 대시보드 재생성 (b) `manifest.json` 재방출 (c) adapter `doctor`/parity-mirror 체크 통과 확인. skills/ 3-harness(claude/codex/opencode) 1:1:1(skills 28/commands 28/agents 9) 유지.
- **SD-10 (강점 회귀 금지)**: audit §5 4강점 = `variance-bug=0 · premature-completion=0 · no-op=0 · sediment=0`. 각 Cluster 후 재확인 방법은 §6.
- **git 격리**: 본 plan 실행은 worktree `skill-design-refactor` 브랜치에서 진행(이미 격리됨). main 직접 편집 금지.

---

## 1. Step CORE — 설계 계약 core-first 정착 (SD-3, PRD §2) — **최선행**

> Cluster 2 의 SoT 규칙이 이 PRD 자신의 산출물에도 적용된다 — 정량 규범은 CONVENTIONS 에만, 4축 tenet 은 DESIGN_PRINCIPLES 에만. 두 문서는 상호 포인터 1줄로 연결(중복 서술 금지).

### CORE-1. `core/CONVENTIONS.md` — 신규 `§5.6a Skill-Design 정량 규범` (정량 규범 SoT)
- **자리**: `§5.6 SKILL.md 작성 규칙`(현 :357) 직후 신규 `### §5.6a. Skill-Design 정량 규범 (scan.sh lint SoT)`.
- **내용(정량 규범 표 — scan.sh 컬럼과 1:1)**:
  | 규범 | 기준 | scan.sh 컬럼 |
  |---|---|---|
  | SKILL.md body 길이 | `< 500` lines | `body_lines`/`line_ok` |
  | references/ depth | 1-depth (하위 디렉터리 0) | `ref_depth_ok` |
  | invocation frontmatter | user-only manual skill = `disable-model-invocation: true`; parent/pipeline 호출·subagent preload 대상 = model-invoked; entry-router = model-invoked + 영문 "Use when" 트리거 병기 | `disable_model`/`invocation`/`use_when` |
- **강제 경로 1줄**: "본 규범 위반은 `sync-skills --check`가 `check.sh`(scan 관측 + invocation registry)로 자동 감지(§CORE-4). 신규/수정 스킬은 통과가 merge 전제."
- **DESIGN_PRINCIPLES 상호 포인터**: 표 아래 "4축 철학·비용축 tenet 은 [DESIGN_PRINCIPLES §10](DESIGN_PRINCIPLES.md#10) — 여기선 규범만, tenet 중복 서술 없음."

### CORE-2. `core/DESIGN_PRINCIPLES.md` — 신규 `## §10 Skill-Design Tenets (Pocock 4축 + Predictability)`
- **자리**: `## 9. Design ownership`(현 :230) 직후 신규 `## §10`.
- **내용(tenet만 — 정량 수치는 넣지 않음)**:
  - **root virtue = Predictability**(같은 *출력*이 아니라 같은 *과정* 재현) — 이미 28스킬 🟢, refactor 가 흔들면 안 되는 골격.
  - **4축 레버**: ① Invocation(도달성 gain 없는 resident description은 context 낭비지만 호출 그래프를 먼저 보존 — manual-only만 disable, parent-invoked는 model-invoked 유지) ② Information Hierarchy(3-rung: SKILL.md 라우터 → references/ disclosure) ③ Steering(leading concept·checkable completion; safety negation 은 정당) ④ Pruning(cross-skill SoT 단일 authority + pointer).
  - **1줄 포인터**: "정량 규범(줄 수·depth·frontmatter 요건)은 [CONVENTIONS §5.6a](CONVENTIONS.md#56a-skill-design-정량-규범) — 스캔 가능 기준은 그쪽 단일 SoT."
- **부록 이력 1줄**(`## 부록` :241): "2026-07-13 skill-design-refactor: §10 tenet + CONVENTIONS §5.6a 정량 규범 분할 배치."

### CORE-3. `roles/modes/design/_design_rules.md` — 시각검증 loop SoT 확정 (Cluster 2 선반영)
- **현황**: `## 시각 자가검증 루프 (필수 — Design MCP 경유)`(현 :14) 가 이미 존재 = 이미 SoT. **신규 작성 불필요** — 지정만 한다.
- **보강(선택)**: scope 별 렌더 표(ui/slide/icon/diagram)가 skills 쪽에만 있고 SoT 엔 산문만 있음. Cluster 2 에서 skills 의 scope 표를 걷어내려면 SoT 에 scope 표를 흡수해야 pointer 가 정보 손실 없이 성립 → `_design_rules.md §시각 자가검증 루프` 에 4-scope(ui/webapp·slide·icon·diagram) 렌더 표를 1회 추가(design-components:120-125 + design-review:65-70 의 합집합). core-first 대상.

### CORE-4. scan.sh 상시 lint 승격 + drill 회귀 케이스 (SD-4)
- **scan.sh 이전(location 결정)**: 현재 `.agent_reports/analysis_project/code/_internal/skill_design_audit/scan.sh` = audit run 의 throwaway scratch. **stable 위치로 이전**: `tools/skill-conformance/scan.sh` (신규 dir). 근거 — lint 자산은 audit 산출물 수명과 분리돼야 하고, `tools/` 는 harness 도구 표준 자리.
- **상시 lint 자리(결정)**: **`sync-skills` 파이프 `--check` 모드**에 편입(추천) > hooks/ PreToolUse. 근거 — sync-skills 는 이미 "스킬 정의 변경 감지" 게이트이고 `build-manifest.py --check`·cross-doc-invariants 를 돌린다(`skills/sync-skills/references/finalize-and-hooks.md:14`). scan.sh 를 같은 `--check` 흐름에 붙이면 정의 변경 자리에서 정량 규범 drift 를 exit≠0 로 노출. hooks/ 매-편집 가드는 per-edit noisy 라 2순위.
  - 구현: `skills/sync-skills/references/finalize-and-hooks.md` 에 `check.sh` 구조+invocation gate(§CONVENTIONS 5.6a) 스텝 추가 + `sync-skills` Step 표에 한 행.
- **drill 회귀 케이스 `g7_skill_conformance`** (static-assert, prompt-driven 아님):
  - `loops/drill/cases/g7_skill_conformance/{config,fixture.sh,assert.sh}` 신규.
  - `config`: `AXIS=static`(신규 축; run.sh 가 Claude turn 없이 assert 만 돌리도록) 또는 기존 축 재사용 + `MAX_TURNS=0`.
  - `assert.sh`: `check.sh`를 양 Claude skill 트리에 실행 → (a) `line_ok=N` 0 (b) `ref_depth_ok=N` 0 (c) parent-invoked 13개 `disable_model=false` 강제 (d) 명시 `user-only`만 `true` 허용. parent/user-only 양방향 failure control도 실행.
  - drill README/run.sh case 목록에 `g7_skill_conformance` 등재(run.sh 는 `cases/` 자동 discovery 이므로 dir 생성만으로 편입, :106/:130).

**CORE 완료 게이트**: `sync-skills` 1회 → core→adapter 미러 재투영(DESIGN_PRINCIPLES/CONVENTIONS 는 core, adapter 파생) + doctor 통과.

---

## 2. Cluster 2 — SoT 통합 (P2+P5, PRD §3.1) — 즉시·검증 불요

### C2-1. Plan Resolution 단일 authority (SD-2)
- **authority 지정**: `skills/autopilot-code/references/arguments-and-decisions.md` 의 Plan Resolution 블록(현 :95-105) = 단일 SoT.
  - 헤더 정정: `## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine)`(:95) → `## Plan Resolution (canonical authority — single SoT)`. ("keep in sync" 문구 제거 — 이 파일이 SoT 이므로 sync 대상 없음. grep glob 밖이라 완료기준엔 무영향이나 자백 문구 청소.)
- **블록 → 1줄 pointer 교체(SKILL.md 4개)**:
  | 파일 | 현 블록 범위 | 교체 |
  |---|---|---|
  | `skills/code-execute/SKILL.md` | `:14-22` (`## Plan Resolution (canonical — keep in sync…)` + 4-step) | `> **Plan Resolution**: `$ARG`→plan 경로 해석은 [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md) 단일 authority.` |
  | `skills/code-test/SKILL.md` | `:14-…` (동일 블록) | 동일 pointer |
  | `skills/code-report/SKILL.md` | `:14-…` (동일 블록) | 동일 pointer. 추가: `:45` "resolved via Plan Resolution above" → "resolved via Plan Resolution(위 pointer)" 문구 유지 확인 |
  | `skills/code-refine/SKILL.md` | `:12-…` (동일 블록; fuzzy 는 `*$ARGUMENTS*` 변형) | 동일 pointer |
- **README.md compat 미러 4개**: `code-execute/README.md:13`·`code-test/README.md:13`·`code-report/README.md:13`·`code-refine/README.md:13` 의 `## Plan Resolution (canonical)` 블록도 pointer 화. (README 는 sync-skills 가 재투영하나, 완료기준 grep 에 `skills/*/README.md` 포함이므로 명시 처리.)
- **code-plan 제외**: Pre-Check 사용, Plan Resolution 블록 없음(per-skill :144). 무편집.
- **완료 기준**: `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` = **0 lines**. Plan Resolution 본문은 authority 1곳에만 존재.

### C2-2. Language Rule 통합
- **SoT 결정**: `skills/autopilot-code/references/arguments-and-decisions.md` 의 `## Language Rule`(현 :1) = SoT. code-* 5개가 이미 Plan Resolution 으로 같은 파일을 참조하므로 pointer 타깃 1개로 통일(신규 파일 최소화). (대안 = CONVENTIONS §5 — Language Rule 이 code-* 밖으로 확산되면 그때 승격.)
  - SoT 텍스트 정정: authority :1-2 "When explaining something to the user, write in Korean." → code-* 쪽 richer wording "All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft)." 로 흡수(정보 손실 방지).
- **블록 → pointer 교체(5개)**: `code-execute/SKILL.md:23`·`code-refine/SKILL.md:23`·`code-report/SKILL.md:23`·`code-plan/SKILL.md:16`·`code-test/SKILL.md:25` 의 `## Language Rule` 블록 → `> **Language Rule**: [arguments-and-decisions.md#language-rule](../autopilot-code/references/arguments-and-decisions.md).`
- **완료 기준**: `grep -rln "## Language Rule" skills/code-*/SKILL.md` = 0(전부 pointer). SoT 본문 1곳.

### C2-3. 시각검증 loop 단일 SoT (CORE-3 확정한 `_design_rules.md §시각 자가검증 루프`)
- **블록 → pointer 교체**:
  | 파일 | 현 블록 | 교체 |
  |---|---|---|
  | `skills/design-components/SKILL.md` | `:118-125` (Step 4 시각 자가검증 산문 + `preview→screenshot` 공통흐름 + scope 표) | 필수 invariant 1줄("산출 직후 렌더해서 본 것으로만 완료")만 남기고 상세 루프·scope 표 → `> 상세: [_design_rules.md §시각 자가검증 루프](../../roles/modes/design/_design_rules.md)` |
  | `skills/design-review/SKILL.md` | `:63-70` (critic render flow + scope 표) | 동일 pointer, verifier/critic 2-gate 고유 서술은 유지 |
  | `skills/design-tokens/SKILL.md` | `:112-121` (specimen 시각 자가검증) | specimen-consume gate(토큰→component 소비 전 검증)는 고유라 유지, 공통 `preview→screenshot→view_image` 루프만 pointer |
  | `skills/autopilot-design/SKILL.md` | `:164-181` (시각 검증 block) | 이미 `:171` 에서 `_design_rules.md` 지시 — 인라인 렌더 경로/루프 산문을 pointer 로 축약(Cluster 3 추출과 합류, §3 참조) |
- **파리티 주의**: `_design_rules.md` 는 3사본(`roles/` + `adapters/claude/agent-modes/design/` + `adapters/codex/modes/design/`). **core-first**: `roles/` 만 편집 → sync-skills 가 adapter 사본 재투영.
- **완료 기준**: `grep -rln "mcp__design__preview.*screenshot\|시각 자가검증 루프 공통" skills/design-*/SKILL.md skills/autopilot-design/SKILL.md` 에서 공통 루프 본문이 SoT 1곳(+CORE-3 scope 표)만. 각 스킬은 pointer + 고유 gate.

### C2-4. `<artifact-root>` 해석 스니펫 → CONVENTIONS §5.1 pointer
- **SoT**: `core/CONVENTIONS.md:192`(§5.1) 이 이미 `<artifact-root>` 해석 + `REPORTS_DIR=…` 치환을 정의 = SoT.
- **verbatim 스니펫 → pointer 교체(실측 6개)**: `analyze-project/SKILL.md:21`·`audit/SKILL.md:17`·`autopilot-research/SKILL.md:18`·`autopilot-draft/SKILL.md:68`·`autopilot-spec/SKILL.md:13`·`autopilot-refine/SKILL.md:101` 의 `> `<artifact-root>` 해석: …치환한다.` 한 줄 → `> `<artifact-root>` 해석·치환: [CONVENTIONS §5.1](../../core/CONVENTIONS.md#51-workspace-assumption-전제).`
  - **PRD 대비 정정**: PRD §3.1 은 analyze-project/analyze-user/audit/autopilot-code/autopilot-draft 를 예시했으나, verbatim "해석" 스니펫 실측 보유는 위 6개. analyze-user/autopilot-code 는 `<artifact-root>` **토큰만** 쓰고 해석 스니펫은 없음 → 무편집(토큰 사용은 정상, 중복 아님).
- **완료 기준**: `grep -rln "REPORTS_DIR=.agent_reports; \[ -d .claude_reports \]" skills/*/SKILL.md` = 0(전부 pointer). 정의는 CONVENTIONS §5.1 1곳.

### C2-5. P5 — Required Reads ↔ Reference Map 이중 서술 병합 (family 컨벤션 1회 결정)
- **결정(family-level)**: 두 절을 단일 `## Reference Index`(파일 + "언제 읽나" 시점 + 의무 표기 1표)로 병합. 컨벤션은 `core/CONVENTIONS.md §5.6`(SKILL.md 작성 규칙)에 "reference 목록은 Required Reads/Reference Map 이원화 대신 단일 Reference Index 표 1회" 1줄 추가.
- **대상 13 라우터**(per-skill 실측 heading 보유): analyze-project·analyze-user·audit·autopilot-code·autopilot-draft·autopilot-lab·autopilot-note·autopilot-refine·autopilot-research·autopilot-spec·draft-strategy·post-it·sync-skills.
  - 각 파일: Required Reads 절(강한 "언제 로드" 의무 표기) + Reference Map 절(파일↔용도)을 → 한 표로 병합. **variance-bug 회귀 금지(SD-10)**: 병합 표에 반드시 _파일명 + 시점 + 의무_ 3요소 유지(포인터 약화 금지 — audit §5 강점 2).
- **완료 기준**: 13 스킬 각각 `Required Reads` **또는** `Reference Map` 헤더 중 하나만(둘 다 보유 0). `grep -c "Required Reads\|Reference Map"` 스킬당 ≤1.

**C2 완료 게이트(SD-6)**: `sync-skills` → README/manifest 재생성 + adapter doctor/parity 통과. `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` = 0.

---

## 3. Cluster 3 — Sprawl 추출 (P3+P6, PRD §3.2) — Cluster 2 후

> 원칙: references/ **1-depth 불변**(SD-8, 하위 디렉터리 0). SKILL.md 엔 라우터·계약·mapping 표만 남기고 worked example/delegate prompt/템플릿/실행 본문은 `references/*.md` 로. progressive disclosure(audit §5 강점 3) 강화이지 회귀 아님.

### C3-1. autopilot-design (315 → 목표 <200) — 최우선(유일 double-🔴)
- **신규**: `skills/autopilot-design/references/` (현재 없음) — 1-depth.
- **추출 매핑**:
  | 추출 대상(현 범위) | → references/ |
  |---|---|
  | `## Pipeline Execution` Phase 0-5 본문 (`:183-271`) | `references/pipeline-execution.md` |
  | `## 하네스 (…harness-spec 기반)` 표 (`:149-162`) | `references/harness.md` |
  | `## 시각 검증` block (`:164-181`) | **추출 아님** — C2-3 대로 `_design_rules.md` pointer 로 축약(중복 추출 금지) |
- **SKILL.md 잔류**: intake gate·Argument Parsing·Context Auto-Detection·`## Pipeline Overview`(:114) + **stage-worker mapping 표**(`:127-138`, per-skill :90 "phase 목록은 mapping 표로 이미 완결") + Return/Update memory. phase 상세는 references pointer.
- **완료 기준**: `wc -l skills/autopilot-design/SKILL.md` < 200. references/ 1-depth.

### C3-2. draft-refine (278) — delegate prompt + changelog 예시 추출
- **신규**: `skills/draft-refine/references/`.
- **추출**: `## Delegate to 연구팀`~ref-grounding delegate 프롬프트 거대 inline (`:57-96` 골격 + 위임 프롬프트) → `references/delegate-prompt.md`; Changelog `### Worked example`(`:153-198`) before/after 예시 → `references/changelog-example.md`.
- **잔류**: Document Resolution·Memo Detection·MANDATORY Ref-Grounding 계약·QA Scaling 요약(상세는 draft-strategy `references/qa-review.md` cross-pointer, per-skill :242 중복 해소).
- **완료 기준**: body 감소(목표 <200), references/ 1-depth.

### C3-3. autopilot-ship (241) — Examples + 발화→자리 표 dedupe
- **신규**: `skills/autopilot-ship/references/`.
- **추출**: `## Examples` 3개(`:207-238`) → `references/examples.md`. 발화→자리 표 3중 서술(`:64-71`·`:93-95`·`:165-169`) + "deploy=user" 3중(`:51`·`:133`·`:184`) → 단일 authority(Step 2 표 1곳)로 dedupe, 나머지는 pointer.
- **완료 기준**: body 감소, references/ 1-depth.

### C3-4. design-tokens (212) — 70줄 exemplar + 템플릿 추출
- **신규**: `skills/design-tokens/references/`.
- **추출**: worked `tokens.md` exemplar(`:41-110`, ~70줄) → `references/tokens-exemplar.md`; CSS/TS 템플릿(`:129-167`) → `references/templates.md`. schema skeleton + single-token-contract gate + specimen-consume gate 는 SKILL.md 잔류.
- **완료 기준**: body 감소(목표 <150), references/ 1-depth.

### C3-5. autopilot-apply (190) — 제외 목록 dedupe + rationale 추출
- 190 은 임계 근접 — **references/ 신설 최소화**. 우선 3중 제외 목록(Scope NOT-for `:54-57` / Override `:43-46` / When NOT `:186-190`, per-skill :79) 단일 authority dedupe. `$BUILD_OUT` 근거 문단(`:78`)이 reference급이면 `references/build-detection.md` 로.
- **완료 기준**: body 감소, references/ 1-depth.

**C3 완료 게이트(SD-6)**: `bash tools/skill-conformance/scan.sh skills` 재실행 → (a) 각 타깃 `body_lines` baseline 대비 감소(scan_baseline.tsv 비교: autopilot-design 315→<200 등) (b) `ref_depth_ok=N` 행 0. + `sync-skills` → adapter 미러(references/ 파일 투영)·doctor 통과.

---

## 4. Cluster 1 — Invocation 재분류 (P1+P4+P7, PRD §3.3) — **검증 게이트 후**

> 이 Cluster의 trial-flip 절차는 runtime 계약을 확인하기 위한 게이트였다. C1-GATE 결과 slash만 PASS하고 parent Skill-tool·실파이프가 FAIL해 13개 모두 model-invoked 유지로 확정했다.

> **Runtime amendment (2026-07-13, C1-GATE b/c 이후)**: 공식 Claude Code 계약과 fresh probe가 `disable-model-invocation: true`의 Skill-tool·subagent preload 차단을 확인했다. 아래 trial 절차는 역사적 근거로 유지하되, C1-FLIP 지시는 폐기한다. 현재 계약은 user-only manual workflow만 disable하고 parent/pipeline 호출 13개는 model-invoked로 유지하는 것이다.

### C1-GATE. trial-flip 검증 게이트 (flip 전 필수, PRD §3.3 (a)(b)(c))
- **(a) slash 명시 호출 생존**: `draft-strategy` **1개만** trial-flip(`disable-model-invocation: true`) → 격리 검증: `claude -p "/draft-strategy <args>"` slash 호출이 정상 동작하는지 관측. PASS/FAIL 기록. **FAIL 시 즉시 revert**.
- **(b) parent Skill-tool dispatch 무영향**: `code-test` **1개만** trial-flip → autopilot-code conductor 의 depth-2 **Skill-tool dispatch**(code-plan/execute/test 를 Skill 로 호출) 경로가 disable flag 하에 생존하는지 관측. **FAIL 시 즉시 revert**.
- **(c) 실파이프 1회 통과**: (a)+(b) 모두 PASS 시 → autopilot-code standard 사이클 1회 실제 구동 → code-plan→execute→test→report 4스테이지 통과 확인.
- **산출**: `_internal/c1_gate_log.md` 에 3절차 각 PASS/FAIL + 관측 증거(명령·exit·transcript mtime).
- **관측 결과(SD-5 runtime amendment)**: (b)(c) 실패로 pilot을 원복했다. 13개 모두 parent/pipeline 호출 그래프에 있으므로 slash-only 통과분을 안전한 flip 부분집합으로 취급하지 않는다.

### C1-CONTRACT. 13개 parent-invoked model invocation 보존
- **대상 13**: code-execute·code-plan·code-refine·code-report·code-test(5) + design-components·design-handoff·design-init·design-refs·design-review·design-tokens(6) + draft-refine·draft-strategy(2).
- **작업**: `tools/skill-conformance/invocation-policy.tsv`에 `parent-invoked`로 명시하고, `check.sh`가 양 Claude skill 트리에서 `disable_model=false`를 강제한다. manual-only workflow는 `user-only` 분류 뒤에만 `true`를 허용한다.
- **완료 기준**: `check.sh skills adapters/claude/skills` PASS + g7의 parent flip/user-only missing-flag failure control이 각각 예상대로 FAIL하고 user-only true control이 PASS.

### C1-P7. post-it wording 정합
- **대상**: `skills/post-it/SKILL.md:14` "사용자가 명시적으로 `/post-it` 호출할 때만 변경"(user-invoked 계약 wording) ↔ frontmatter model-invoked + proactive-nudge auto-record 불일치(per-skill :257).
- **결정**: **post-it 은 flip 후보 아님**(proactive-nudge 위해 model-invoked 유지가 정당). 따라서 **wording 완화** — ":14" 를 "주 변경 경로는 `/post-it` 명시 호출이나, references/nudge-and-boundaries.md 의 proactive-nudge 로 model-invoked auto-record 도 한다" 식으로 실제 계약과 일치. disable flag 추가 아님.
- **완료 기준**: `:14` wording 이 frontmatter(model-invoked) + nudge 계약과 모순 없음.

### C1-P4. entry-router 영문 "Use when…" 트리거 병기 (D3 resolved)
- **정책**: 기존 한국어 blurb **유지** + description **첫 문장에 영문 트리거 문장 _추가_**(대체 아님). entry-router 한정.
- **대상 12(entry-router = autopilot-*·analyze-*·audit)**: autopilot-apply·autopilot-code·autopilot-design·autopilot-draft·autopilot-lab·autopilot-note·autopilot-refine·autopilot-research·autopilot-spec·analyze-project·analyze-user·audit.
  - sub-skill(code-*·design-*·draft-strategy·draft-refine)·ops(sync-skills·post-it)는 대상 아님(SD-7: hook 라우팅 유지, wording 단독 자동발화 불신).
- **작업**: 각 SKILL.md frontmatter `description:` 첫 문장 앞에 영문 "Use when …" 절 삽입. 예(autopilot-code): `"Use when starting or routing any code task (library/research/app). 코드 작업 일반 entry — …"`.
- **완료 기준**: `scan.sh` 에서 12 entry-router `use_when=Y`(baseline 전부 N). 한국어 blurb 잔존 확인(`desc_has_hangul=Y` 유지).

**C1 완료 게이트(SD-6)**: `sync-skills` → manifest invocation 필드·adapter 미러 재생성 + doctor(skills 28/commands 28/agents 9 유지). scan.sh 재확인.

---

## 5. Cross-harness projection (PRD §4, SD-6) — 각 Cluster 종료 시 의무

- **매 Cluster 후 `sync-skills` 1회**: (C2) pointer 교체·SoT 텍스트 변경 → skill 본문 미러 재투영. (C3) references/ 신설 → adapter skill 디렉터리 파일 투영. (C1) frontmatter invocation/description 변경 → manifest invocation 필드 + adapter 미러.
- **parity mirror 불변**: `roles/modes/design/_design_rules.md` 3사본, `skills/*/README.md` compat 미러, core/*.md adapter 파생 — 전부 byte-parity 대상. 손편집은 core/roles 만, 나머지는 sync-skills 투영. 누락 시 derived 가드(`check_claude_*_projection`) FAIL.
- **doctor/parity 검증**: 각 Cluster merge 전 adapter `doctor`/`check-runtime-projection` 통과 확인 — 3-harness 1:1:1(skills 28/commands 28/agents 9) 유지.
- **README 대시보드**: sync-skills 가 자동 재생성.

---

## 6. SD-10 회귀 재검 (audit §5 4강점 = 0 유지) — 각 Cluster 후

| 강점(=0 유지) | 재검 방법 | 위험 Cluster |
|---|---|---|
| **variance-bug** (must-have 자료가 약한 포인터 뒤) | pointer 교체·Reference Index 병합(C2-1/2/3/4, P5) 후 각 pointer 가 _파일명+시점+의무_ 3요소 유지 확인 | C2(P5 병합이 포인터 약화 위험 최고) |
| **premature-completion** | completion criterion 이 여전히 checkable + post-completion step 이 실제 context 경계(subagent/user) 뒤인지 — 추출로 gate 문장이 references 로 밀려도 SKILL.md 잔류 확인 | C3(추출) |
| **no-op** | 추출·pointer 화가 빈 문장 생성 안 함 — pointer 는 동작 지시(로드 의무) | C2·C3 |
| **sediment** | flip·wording 변경이 낡은 문장 잔류 안 함 — 옛 Plan Resolution 블록 완전 제거(잔재 grep) | C1·C2 |
| **Predictability 골격** | 불변식 블록·stage 계약·checkable completion 무손상 — 각 스킬 diff 리뷰 | 전 Cluster |
| **정량 규범** | scan.sh 재실행 전부 통과(line_ok·ref_depth_ok) | C3·C1 |

- **최종 회귀**: 전 Cluster 종료 후 audit rubric 재적용(drill `g7_skill_conformance` + 필요 시 audit re-run) — SD-10 "refactor 후 본 audit rubric 재적용".

---

## 7. 실행 순서 요약 (체크 게이트)

1. **CORE-1~4** (core-first 계약) → sync-skills → doctor ✅
2. **Cluster 2** (C2-1~5 SoT 통합) → `grep "keep in sync"`=0 → sync-skills → doctor ✅
3. **Cluster 3** (C3-1~5 sprawl 추출) → scan.sh body 감소·1-depth → sync-skills → doctor ✅
4. **Cluster 1** (C1-GATE → C1-CONTRACT → P7 → P4) → check.sh invocation policy/use_when → sync-skills → doctor ✅
5. **최종** SD-10 회귀(drill g7 + audit rubric) ✅

> **결과**: Cluster 1 runtime gate 완료. 새 manual-only 후보가 생기면 호출 그래프를 먼저 확인하고 registry 분류와 frontmatter를 같은 변경에서 추가한다.
