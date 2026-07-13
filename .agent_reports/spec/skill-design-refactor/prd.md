# Skill-Design Refactor — PRD

> mode: **library** · component spec (repo 루트 spec = unified-memory-system, 무관) · 작성 2026-07-13 v1
> · **v2 2026-07-13** (편집 대상 = live 트리 `adapters/claude/skills/` 정정 + root `skills/` = 미러 불변식. back-jump 사유: dev Cluster 2 실행 중 `BLOCKING_FINDING.md` — audit/PRD v1 이 legacy root `skills/` 를 대상으로 삼았으나 live Claude source 는 `adapters/claude/skills/*/SKILL.md`. 단 main 기준 두 트리 내용 동일이 확인돼(§1.5) audit 진단·file:line 근거는 live 에 유효 — 재감사 불요, 대상 경로만 정정.)
> · **runtime amendment 2026-07-13** (C1 runtime gate 결과 반영: `disable-model-invocation`은 context 최적화 힌트가 아니라 programmatic Skill 호출·subagent preload를 막는 hard boundary. manual-only와 parent-invoked를 분리하고 13개 parent-invoked는 model-invoked 유지.)
> 입력: `analysis_project/code/skill_design_audit.md`(28스킬×4축 진단·Step7 P1~P8·§6 Cluster 인계) · `skill_design_audit_per_skill.md`(file:line 근거) · `research/skill-design-principles/`(00_briefing·02_standards·04_technical_deep_dive·cards — Pocock 4축 SoT)
> 본 문서는 청사진(PRD). 구현은 `/autopilot-code --mode refactor` (산출물 `plans/`).
> **방향(사용자 확정 2026-07-13)**: Pocock 4축(Invocation/Information Hierarchy/Steering/Pruning) + root virtue **Predictability** 를 보수적 cherry-pick 이 아니라 **적극 표준 채택**. 단 하네스가 원칙보다 더 나간 지점(auto-activation hook 우회 등)은 **유지가 기본** — 원칙 쪽 회귀 금지, 충돌은 §Decision 에 명시.

## 0. 한 줄

28스킬 진단(`skill_design_audit.md` §4 P1~P8)이 제기한 두 gap — **Invocation systemic**(13개 sub-skill의 호출 성격 미검증) + **Pruning 중복**(cross-skill SoT 물리 복제·장문 sprawl) — 을 Pocock 4축을 정식 설계 계약으로 앉힌 위에서 **Cluster 2(SoT 통합·즉시) → Cluster 3(sprawl 추출) → Cluster 1(invocation runtime 검증·분류 확정)** 순서로 정합 튜닝한다. C1 실측 결과 13개는 parent/pipeline 호출 대상이므로 model-invoked 유지가 올바른 계약이다.

## 1. 배경 — 진단이 수렴한 것

audit `skill_design_audit.md` §0 verdict 분포:

| 항목 | 🟢 | 🟡 | 🔴 | 읽기 |
|---|---|---|---|---|
| Step 0 · Predictability | **28** | 0 | 0 | root virtue 는 이미 전 스킬 달성 — refactor 가 흔들면 안 되는 골격 |
| ① Invocation | 0 | 28† | 0† | 진단 당시 전 스킬 model-invoked + "Use when" 트리거 부재. 13개 sub-skill은 C1 runtime gate에서 parent/pipeline 호출 대상임이 확인돼 model-invoked 유지로 재분류 |
| ② Information Hierarchy | 18 | 9 | 1 | autopilot-design(315줄) 유일 🔴 |
| ③ Steering | 19 | 9 | 0 | negation 8건 대부분 load-bearing safety invariant — 재작성 대상 소수 |
| ④ Pruning | 3 | 24 | 1 | duplication 25/28 — 위험한 건 cross-skill SoT 복제뿐 |

† harmonize: 연구팀 그룹 C 는 code-* 5개를 Invocation 🔴(user-invoked 강권)로 dissent, 종합은 🟡 정규화하되 aggregate 영향을 Step7 P1 로 승격(audit §0 각주).

**진단 강점(§5 — refactor 가 보존할 불변)**: `variance-bug·premature-completion·no-op·sediment 0건`. Pocock rubric 이 겨냥하는 attention-budget 낭비의 주 원천이 이미 부재. 따라서 이 PRD 는 "구조 도입"이 아니라 **정합성 튜닝**이다.

**표준 채택 posture(사용자 확정)**: 4축 + Predictability 를 적극 표준으로 채택한다. 근거 — 04_technical_deep_dive 가 4원칙 모두를 단일 물리 근거(attention budget + context rot)로 환원했고(04 "메커니즘 근거 표"), 진단이 이 rubric 으로 28스킬 전수 스캔에 성공(00_briefing Key finding #2). 채택 대상은 정량 규범(hard scan)과 4축 tenet(설계 계약) 둘 다.

## 1.5 편집 대상 트리 정정 + 미러 불변식 (v2 신규 — SD-11)

> **back-jump 사유**: dev Cluster 2 실행 완료 후 SD-6 sync-skills 게이트에서 발견(`_internal/../BLOCKING_FINDING.md`). v1 은 audit 을 그대로 인계해 root `skills/*/SKILL.md` 를 편집 대상으로 지정했으나, **live Claude 런타임 source 는 `adapters/claude/skills/*/SKILL.md`** 다 — `sync-skills` SKILL.md :20("root skills/ 는 historical compatibility reference, runtime source 아님")·`tools/build-manifest.py` :169 glob(adapters 트리만 대상)이 SoT.

**핵심 정정 (main 세션 직접 확인 2026-07-13, 재검증 불요)**:

1. **live source = `adapters/claude/skills/*/SKILL.md`** (realization SoT). manifest.json/doctor/parity 파이프라인이 읽는 유일 트리. root `skills/` 편집만으론 실제 스킬 동작에 영향 0 → PRD 목적(Predictability·context 절약) 미달성.
2. **main 기준 root `skills/` ≡ `adapters/claude/skills/` (내용 동일)** — `diff -rq` 차이 = `skills/.sync_state.json` 1개뿐. 따라서 audit(skill_design_audit) 의 진단·file:line 근거는 **live 트리에 그대로 유효 — 재감사 불요**. (BLOCKING_FINDING 의 "이미 divergent" 는 _이 브랜치 자체가_ root 만 편집(`cd48b25`)해 만든 차이의 오독. main 에선 동일.)
3. root `skills/` 는 sync-skills 계약대로 **compatibility mirror 로 유지** — deprecate 는 이번 scope 밖.

**미러 불변식(모든 Cluster 적용)**: 모든 편집의 **정본 대상 = `adapters/claude/skills/*/SKILL.md`** (+ `adapters/claude/skills/*/README.md`·`references/`). root `skills/` 는 **미러 동기화 의무** — 동일 편집을 양 트리에 동일 적용한다. **완료 기준 grep 은 양 트리(`skills/` + `adapters/claude/skills/`) 대상**으로 확인한다. (편집 후 두 트리는 `.sync_state.json` 외 diff 0 이어야 한다 — SD-11.)

### 1.5.1 capabilities/ 계약 drift 체크 (v2 신규 — 각 Cluster 단계)

`adapters/claude/skills/*/SKILL.md` 는 portable `capabilities/*.md` 계약의 Claude realization 이다(`capabilities/README.md`: "Claude Code realizes these capabilities through adapter-owned concrete Skill files"). 따라서 각 Cluster 편집 시 **해당 스킬의 SKILL.md 변경이 대응 `capabilities/<name>.md` 계약 서술과 어긋나는지 확인**한다:

- **어긋나지 않으면**: 진행(대부분의 SoT pointer 화·sprawl 추출은 realization 디테일이라 portable 계약 불변).
- **어긋나면**: **자동 수정 금지** — "계약 갱신 항목"으로 plan 에 표면화(capabilities 계약은 별도 결정 대상). 특히 Cluster 1 invocation 분류는 capability 의 호출 그래프와 직접 맞닿으므로 manual-only/parent-invoked 판정마다 capabilities 계약 정합을 명시 점검.

## 2. 설계 계약의 앉을 자리 (필수 §1)

4축 + Predictability 를 어디에 정식화할지 + 신규 스킬 준수 강제 방법.

### 2.1 후보 비교 — CONVENTIONS vs DESIGN_PRINCIPLES

| 대상 | 자리 | 근거 |
|---|---|---|
| **정량 규범** (SKILL.md <500줄 · references/ 1-depth · invocation frontmatter 요건) | **`core/CONVENTIONS.md`** (신규 §skill-design 절) | CONVENTIONS = family-wide 운영규칙·**정량 규범**의 자리(CLAUDE.md "Family-wide 운영 규칙"). 02_standards §1 표(<500줄/1-depth/"Use when…")가 그대로 정량 스캔 기준 → CONVENTIONS 성격과 일치 |
| **4축 tenet + Predictability root virtue** (Invocation 경제·3-rung IH·Steering leading word·Pruning SoT) | **`core/DESIGN_PRINCIPLES.md`** (신규 tenet 절) | DESIGN_PRINCIPLES = 아키텍처 tenet 의 자리(CLAUDE.md "Autopilot 아키텍처"). 4축은 "체크리스트가 아니라 Predictability 라는 단일 목적을 향한 레버 묶음"(00_briefing Level 2 Takeaway) → tenet 성격 |

**결정**: **분할 배치** — 정량 규범은 CONVENTIONS(스캔 가능한 규범), 4축 철학·비용축(context/cognitive load) tenet 은 DESIGN_PRINCIPLES(아키텍처 원리). 두 문서는 상호 포인터 1줄로 연결(중복 서술 금지 — Pruning SoT 자기적용). 두 문서 모두 core 파생이므로 수정은 core 먼저(CLAUDE.md 운영 정책).

### 2.2 신규 스킬 준수 강제 — 결정론 우선

CLAUDE.md §0.5 결정론 우선 원칙에 따라 **가능한 부분은 스크립트화**하고 의미 판단만 리뷰에 남긴다.

- **재사용 자산**: `.agent_reports/analysis_project/code/_internal/skill_design_audit/scan.sh` 는 이미 존재(audit T3, 확인 완료). Step 1-2 정량 규범 전수 스캔(줄 수·references/ depth·invocation type·"Use when" 트리거 유무)을 `scan_raw.tsv` 로 출력한다.
- **강제 방법**: `scan.sh` 관측값과 `tools/skill-conformance/invocation-policy.tsv` 분류를 합성하는 `check.sh`를 harness 상시 lint 로 사용한다 — 신규 skill 추가 시 (a) `SKILL.md body <500줄` (b) `references/ 1-depth` (c) manual-only=`disable-model-invocation: true`, parent/pipeline/preload=`false`/미지정, entry-router=model-invoked+"Use when"을 자동 검사한다. 분류되지 않은 `true`는 실패한다.
- **drill 회귀 케이스**: `g7_skill_conformance`가 양 live tree를 검사하고, parent-invoked의 잘못된 `true`와 manual-only의 누락된 `true`를 각각 거부하는 negative control 및 올바른 manual-only positive control을 실행한다.
- **의미 판단은 리뷰**: Step 0·3-6(Predictability·failure-mode 판정)은 스크립트화 불가 — plan-review/audit 자리에서 rubric(`RUBRIC_BRIEF.md`)으로 in-session 판정 유지.

## 3. Cluster별 refactor 청사진 (필수 §2)

audit §6 매핑 그대로: **Cluster1=P1+P4+P7, Cluster2=P2+P5, Cluster3=P3+P6**. 실행 순서 = **Cluster 2 → Cluster 3 → Cluster 1**(audit §6 "우선 실행 권장": SoT 검증 불요·즉시 실익 → sprawl → invocation 검증 게이트 후).

> **대상 경로·완료 기준 (v2 SD-11, §1.5)**: 아래 모든 Cluster 의 편집 정본은 `adapters/claude/skills/*` 이며 root `skills/*` 는 동일 편집을 미러한다. 각 완료 기준 grep(“keep in sync”=0, loop/Language Rule 본문 1곳 등)은 **양 트리 대상**으로 확인한다(아래 표에서 경로가 `skills/*` 로만 적힌 자리도 `adapters/claude/skills/*` 를 함께 스캔). 각 Cluster 편집 시 대응 `capabilities/*.md` 계약 drift 를 §1.5.1 대로 점검(어긋나면 계약 갱신 항목 표면화, 자동 수정 금지).

### 3.1 Cluster 2 · SoT 통합 (P2+P5) — 즉시, 검증 불요

> **⚑ dev 재개 첫 항목 (v2 — 기 완료 작업 미러 적용)**: 이 브랜치는 CORE(CORE-1~4) + Cluster 2(C2-1~5) 를 **root `skills/` + `core/*.md` + `roles/modes/design/_design_rules.md`** 에 이미 완료·커밋(`cd48b25`, grep 0건·scan.sh 통과)했다. 그러나 §1.5 대로 **정본 트리는 `adapters/claude/skills/`** 이므로, dev 재개 시 **첫 작업 = `cd48b25` 의 root `skills/` 편집분을 `adapters/claude/skills/` 트리에 동일 미러 적용**(+ 완료 기준 grep 을 양 트리로 재확인, SD-6 sync-skills 게이트 재통과). core/*.md·_design_rules.md 편집분은 트리 무관(공용)이라 이미 유효 — 미러 대상 아님. 이 항목 완료 후 Cluster 3 로 진행.

**대상(물리 복제 SoT 위반, audit §3 핵심 읽기 + per-skill 근거)**:

| 복제 블록 | 현행 | authority 지정 | 완료 기준(checkable) |
|---|---|---|---|
| **Plan Resolution** | code-execute/code-refine/code-report/code-test **4개(code-plan 은 Pre-Check 사용 — 블록 없음, per-skill :144)** 물리 복제 — 헤더 자체가 `## Plan Resolution (canonical — keep in sync with …)` = SoT 위반 자백(per-skill :139 등, `code-execute/SKILL.md:14`). authority 후보 `autopilot-code/references/arguments-and-decisions.md:95` 는 이미 canonical 서술 보유 | **`autopilot-code/references/arguments-and-decisions.md` 를 단일 authority** 로(SKILL.md 본문 아님 — 그 경로엔 블록 없음). 나머지 **4개** 는 1줄 pointer(예: `→ Plan Resolution: autopilot-code/references/arguments-and-decisions.md#plan-resolution`). code-execute/report/test/refine 의 **README.md** 도 동일 블록을 "(canonical)" 표기로 복제 — pointer화 대상에 포함(sync-skills 재투영이 정규화하나 완료기준에 명시) | **양 트리(SD-11)**: `grep -rln "keep in sync" adapters/claude/skills/*/SKILL.md adapters/claude/skills/*/README.md skills/*/SKILL.md skills/*/README.md` = 0건; Plan Resolution 본문이 authority 1곳(`autopilot-code/references/arguments-and-decisions.md`)에만 존재, 나머지(SKILL.md 4개 + README.md 5개)는 pointer 1줄 |
| **시각검증 loop** | design-components(:120)/design-review/design-tokens **3중 verbatim** (per-skill :186; autopilot-design 도 `_design_rules.md` 소유 요약 inline :164-171) | **`_design_rules.md`(또는 공유 reference)** 가 SoT. 3스킬은 pointer | grep 으로 loop 본문이 1곳; SoT = `_design_rules.md` |
| **Language Rule** | code-* 다수 재서술(:137/:146/:155/:164/:173) | **공유 reference 파일(신설)** 또는 CONVENTIONS §5 | grep 으로 Language Rule 본문 1곳 |
| **`<artifact-root>` 스니펫** | analyze-project(:21)/analyze-user(:17)/audit(:68)/autopilot-code(:18)/autopilot-draft(:13) 등 cross-skill 중복 | **CONVENTIONS §5 산출물 컨벤션** 이 이미 SoT — 스킬은 pointer | grep 으로 스니펫 정의 1곳(CONVENTIONS §5), 스킬은 참조 |

**패턴**: 단일 authority 지정 + 나머지는 pointer 교체. 공유 reference 파일 신설 시 위치는 **CONVENTIONS §5 산출물 컨벤션과 정합 필요**(audit §6 "공유 reference 위치") — 산출물 폴더 구조 SoT 를 재정의하지 않고 포인터로 연결.

**P5(within-skill 이중 서술)**: ~13 라우터의 `Required Reads` ↔ `Reference Map` 동일 4개 reference 이중 서술(per-skill :14/:32/:50/:59/:68)은 **family-level 컨벤션 1회 결정**으로 단일 reference index 절로 병합. cosmetic·高빈도(audit P5).

### 3.2 Cluster 3 · Sprawl 추출 (P3+P6) — Cluster 2 후

**우선: autopilot-design(315줄, 28개 중 최장·유일 double-🔴)** — audit §4 P3.

- **추출 대상**: Phase 0-5 Execution 본문(:183-271) + 하네스 표(:149-162) + 시각검증 loop(:164-181) → `references/` 로. phase 목록은 stage-worker mapping 표(:127-138)로 이미 완결이므로 SKILL.md body 엔 mapping 표만 남긴다(per-skill :90 "phase 목록은 mapping 표로 이미 완결").
- **이어서(P6)**: draft-refine(278·delegate prompt :60-207) · autopilot-ship(241) · design-tokens(212·70줄 exemplar :41-110) · autopilot-apply(190)의 worked example/delegate prompt/템플릿을 각 `references/` 로 추출.
- **완료 기준(checkable)**: `scan.sh` 재실행 시 (a) 각 파일 body 라인수 감소(특히 autopilot-design <315, 목표 <200급) (b) references/ **1-depth 유지**(2-depth 중첩 0 — scan.sh 재확인). 진단 §5 강점 3("progressive disclosure 이미 구현")을 회귀시키지 않음.

### 3.3 Cluster 1 · Invocation 분류 확정 (P1+P4+P7) — **runtime gate 완료**

**대상**: code-* 5(execute/plan/refine/report/test) + design-* 6 + draft-refine + draft-strategy의 13개 sub-skill. C1 trial에서 (a) 사용자 `/draft-strategy` 호출은 생존했지만, (b) parent Skill-tool 호출과 (c) autopilot-draft 실파이프 handoff는 `disable-model-invocation` 때문에 명시적으로 실패했다(`_internal/c1_gate_log.md`). pilot flag는 즉시 원복했다.

**확정 계약**:

- `disable-model-invocation: true`는 사용자가 `/name`으로만 시작해야 하는 **manual-only** workflow에만 사용한다.
- parent/pipeline이 Skill tool로 호출하거나 subagent가 preload하는 skill은 **parent-invoked**이며 model-invoked(`false`/미지정)로 유지한다. `user-invocable: false`는 slash 메뉴 노출만 조절하는 별도 축이다.
- 현재 13개는 모두 parent-invoked다. `tools/skill-conformance/invocation-policy.tsv`가 분류 SoT이고 `check.sh`와 g7이 양 Claude skill tree에서 `disable_model=false`를 강제한다.

**완료 기준(checkable)**: 공식 문서+runtime 실측 로그, 13개 registry 정확성, 양 tree `check.sh` PASS, parent/user-only failure control을 포함한 g7 PASS. 새 manual-only skill은 registry 분류와 `true`를 같은 변경에서 추가해야 한다.

- **P7(post-it wording)**: `post-it/SKILL.md:14` "호출할 때만 변경" wording ↔ 실제 model-invoked+proactive-nudge 계약 불일치를 문구 완화 or disable flag 로 정합(audit P7).
- **P4(entry-router 트리거)**: §Decision 참조 — 별도 정책 결정 항목.

## 4. Cross-harness projection 영향 (필수 §3)

`skills/` 수정(특히 frontmatter invocation 변경, references/ 신설)은 **Codex/OpenCode adapter projection 과 한 몸**이다 — `sync-skills` 스킬이 `manifest.json` 을 재생성하고, adapter 하위 skill 미러를 갱신한다(기억: manifest.json = agent_setting/ 최상단 인덱스, 6키 skills(28)/agents(9)…).

- **각 Cluster 완료 시 `sync-skills` 실행 의무**: (Cluster 2) pointer 교체·공유 reference 신설 → skill 본문 변경 → 미러 재투영. (Cluster 3) references/ 신설 → adapter skill 디렉터리 파일 투영 갱신. (Cluster 1) invocation registry/checker와 관련 adapter/plugin 문서를 동기화하고 manifest·mirror를 재검증.
- **parity mirror 영향**: parity 미러 불변식(기억 durable, 2026-07-06 실측) — tools/*·frozen 케이스 변경 시 adapters/claude 하위 concrete 미러 byte-identical 동기화 필수, 누락 시 derived 가드(`check_claude_loop_projection`·`check_claude_tool_projection`)가 FAIL. skills/ 변경도 동형으로 3-harness(claude/codex/opencode) 1:1:1 매핑(기억: doctor check skills 28/commands 28/agents 9)을 유지해야 한다.
- **README 대시보드 갱신**: `sync-skills` 가 README.md 워크플로우 대시보드를 자동 갱신(CLAUDE.md "워크플로우 맵: sync-skills 자동"). Cluster 별 완료 후 대시보드 재생성으로 parity 반영.
- **검증**: 각 Cluster merge 전 adapter `doctor`/`check-runtime-projection` 통과 확인(dispatch-profiles 선례 §6 "활성 게이트" 패턴 승계).

## 5. 버전 트래킹 & 다운스트림 인계 (필수 §4)

- **PRD versioning**: `_internal/versions/v{N}/` — 선행 CLAUDE.md 컨벤션(§0b 버전 트래킹 표: "spec/prd.md 등 청사진 → autopilot-spec update → `_internal/versions/v{N}/`")과 동일. 향후 update 시 스냅샷 보존.
- **다운스트림 인계 커맨드**: **`/autopilot-code --mode refactor`** — spec 컨텍스트 자동 감지(cwd/상위 `spec/pipeline_state.yaml` 존재), plans/ 누적(`plans/<date>_<slug>/`, 사이클 누적). audit §6 "06_implementation §4 권장 순서: `/audit` → `/autopilot-spec` → `/autopilot-code --mode refactor`" 의 마지막 단계.
- **refactor mode 선택 근거**: behavior-preserving cleanup(SoT pointer 화·references/ 추출·invocation 분류 정합)은 신기능이 아니라 정합 튜닝 → refactor mode(개발팀 refactor persona)가 적합.

## 6. Decision 섹션 (main 세션 컨펌용 — 각 항목 추천안+근거 1줄)

| # | 결정 항목 | 추천안 | 근거 1줄 |
|---|---|---|---|
| **D1** | Cluster 1 invocation 분류 | **manual-only만 disable; parent/pipeline/preload는 model-invoked 유지. 현재 13개는 parent-invoked** | 공식 문서와 C1 runtime gate가 flag의 parent Skill-tool·subagent preload 차단을 확인. slash-only 생존은 parent pipeline 안전성을 보장하지 않는다. |
| **D2** | 설계 계약 앉을 자리 | **정량 규범 → CONVENTIONS §skill-design(신규), 4축 tenet+Predictability → DESIGN_PRINCIPLES(신규 tenet)** 분할 배치 + 상호 포인터 | CONVENTIONS=family-wide 정량 규범, DESIGN_PRINCIPLES=아키텍처 tenet — 각 문서 현재 성격에 맞춰 분할(중복은 Pruning SoT 자기위반). |
| **D3** | entry-router "Use when…" 트리거 언어 정책 (P4) | **현행 한국어 blurb 유지 + 영문 트리거 문장을 description 첫 문장에 _추가_(대체 아님)**, entry-router(autopilot-*·analyze-*·audit)만 우선 | 02_standards §3: wording 단독 자동발화 불신(hook 후에도 ~50%, scottspence) → soft 규범. 한국어 blurb 는 트리거 신뢰도 우선이라 유지하되, entry 는 auto-routing 의존 최고라 영문 트리거 병기로 보강(P4 low-cost). |
| **D4** | 원칙-하네스 충돌 유지 항목 (명시 리스트업) | **아래 3건 유지 — 원칙 회귀 금지** | 하네스가 원칙보다 더 나간 지점은 유지가 기본(사용자 확정). |
| **D5** | 실행 순서 | **Cluster 2(SoT·즉시) → Cluster 3(sprawl) → Cluster 1(runtime 검증·분류 확정)** | audit §6 우선 실행 권장대로 invocation을 마지막에 실측했고, 결과를 registry와 g7 강제 규칙으로 닫았다. |

**D4 상세 — 원칙-하네스 충돌 유지 리스트(auto-activation hook 우회 등)**:

1. **auto-activation 신뢰도 우회**: 연구 00_briefing Top-3 insight #1 — description wording 단독 자동발화는 hook 후에도 ~50%(scottspence). 우리는 `workflow-guard-hook`·`mem-recall-inject` 등 **deterministic UserPromptSubmit 주입**으로 이미 우회. → **hook 강제 라우팅 유지**, "Use when" wording 만 믿는 원칙으로 회귀 금지(02_standards §3 "wording 만 믿는 원문 권장을 그대로 hard 강제하지 않는다").
2. **한국어 blurb 유지**: 02_standards §1 은 "3인칭 + Use when…"을 권장하나 우리는 트리거 신뢰도 우선 한국어 blurb(soft 규범). D3 대로 영문 트리거는 _병기_ 만, 한국어 blurb 대체 금지.
3. **entry-router 라우팅 = hook + WORKFLOW 표**: autopilot-* 라우팅은 Pocock router skill 동형(00_briefing insight #3)이나, 우리는 auto-activation 이 아니라 hook 신호(📌tracked)+WORKFLOW §0/§7 표로 강제. → LLM description 매칭에 라우팅을 맡기지 않는 현행 유지.

## 7. 결정 목록 (locked)

- **SD-1**: 실행 순서 = Cluster 2 → 3 → 1 (SoT 즉시 → sprawl → invocation 검증 후). audit §6.
- **SD-2**: Plan Resolution SoT = `autopilot-code/references/arguments-and-decisions.md` 단일 authority, code-execute/refine/report/test **4개**(SKILL.md+README.md) pointer. 완료 기준 = **양 트리(SD-11)** `grep -rln "keep in sync" adapters/claude/skills/*/SKILL.md adapters/claude/skills/*/README.md skills/*/SKILL.md skills/*/README.md`=0.
- **SD-3**: 설계 계약 = 정량 규범 CONVENTIONS / 4축 tenet DESIGN_PRINCIPLES 분할 + 상호 포인터.
- **SD-4**: 정량 규범 강제 = `check.sh`(scan 관측 + invocation registry) + g7 failure control(결정론 우선).
- **SD-5** (runtime amendment): invocation 분류 = manual-only만 `disable-model-invocation: true`; parent/pipeline/preload는 model-invoked 유지. 현재 13개 parent-invoked는 registry + `check.sh` + g7로 `false`를 강제한다.
- **SD-6**: Cross-harness — 각 Cluster 완료 시 sync-skills 실행 + adapter doctor/parity mirror 검증 의무.
- **SD-7**: 원칙-하네스 충돌 3건(auto-activation hook 우회·한국어 blurb·hook 라우팅) 유지 — 원칙 회귀 금지.
- **SD-8**: references/ 추출 시 1-depth 불변(scan.sh 재확인). autopilot-design 우선.
- **SD-9**: 다운스트림 = `/autopilot-code --mode refactor`, plans/ 누적. PRD 버전 = `_internal/versions/v{N}/`.
- **SD-10**: 진단 §5 강점 4종(Predictability 골격·강한 pointer·정량 규범·no-op 청결) 회귀 금지 — refactor 후 audit rubric 재적용(drill).
- **SD-11** (v2): **편집 대상 = `adapters/claude/skills/` (live realization SoT)**, root `skills/` = 미러 — 모든 편집을 양 트리에 동일 적용, 완료 기준 grep 은 **양 트리** 대상. 두 트리 `diff -rq` 차이는 **`.sync_state.json` 만 허용**(mirror-parity). 근거: `sync-skills` SKILL.md :20·`tools/build-manifest.py` :169(adapters 트리만 glob). audit file:line 근거는 main 기준 두 트리 동일이라 그대로 유효(재감사 불요). 각 Cluster 편집 시 대응 `capabilities/*.md` 계약 drift 점검(§1.5.1) — 어긋나면 계약 갱신 항목 표면화, 자동 수정 금지.

## 8. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간(코드)**: 정량 규범 스캔·invocation registry/checker·`grep` 완료 기준·sync-skills projection·parity mirror 가드 — 전부 결정론(§0.5).
- **의미 판단 구간(리뷰)**: Step 0·3-6 failure-mode 판정·negation→positive 선별(safety invariant 제외)·"어느 블록이 authority 인가" 지정 — plan-review/audit 자리 LLM 판정.
- **충돌**: Cluster 1은 호출 그래프 의미 판단을 공식 문서+runtime gate로 매개하고, 확정된 분류만 registry/checker로 규칙화했다. 없음.
