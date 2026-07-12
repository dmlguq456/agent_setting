# 06 · Goal-Adaptive Action Roadmap — Skill Design Principles

> mode: technology · date: 2026-07-13
> Inferred goal: adopt/build 혼합 — 최종 소비자가 우리 harness 자체(28스킬 audit+개선). 표준 5 goal 중 adopt(기술 도입 결정)에 가장 근접하되 build(실제 audit 실행) 요소 포함.

## 1. 하네스 스킬 아키텍처 개괄

우리 harness 의 스킬은 **SKILL.md(router) + references/(disclosure)** 구조를 표준으로 한다. SKILL.md body 는 라우터·불변식·sub-action 분기만 담고, 상세 절차는 `references/*.md` 로 밀어낸다(progressive disclosure, 1-depth). 산출물은 CONVENTIONS §5 의 3-tier(T1 root / T2 named subdir / T3 `_internal/`)를 따르며, 오토파일럿 파이프 아키텍처는 DESIGN_PRINCIPLES 가 규정한다. 이 구조는 Pocock 의 **3-rung Information Hierarchy** 를 그대로 구현한 것 — `autopilot-research/SKILL.md` 의 `## Required Reads`·`## Reference Map` 절이 곧 context pointer 집합(*"이 파일은 라우터와 stage 계약만 담고… 필요할 때 아래 reference 를 Read"*)이고, `post-it/SKILL.md` 의 `## Quick Contract`(*"본 SKILL.md 는 라우터"*)와 불변식 블록이 rung 1-2 를 legible 하게 유지한다.

## 2. 4원칙 정합·gap 매핑 (개괄 예시, 전수 아님)

예시 스킬 3-5개로 4축 정합을 개괄한다. 전수 audit 은 §3 로드맵으로 인계.

| 스킬 | ① Invocation | ② Information Hierarchy | ③ Steering | ④ Pruning | 관찰된 gap |
|---|---|---|---|---|---|
| **autopilot-research** | model? user? — entry router, 컨펌 의무 대상 (CLAUDE.md §0). 자동 라우팅 신호 명시 | 3-rung 우수 — Required Reads/Reference Map 로 references/ 4파일 1-depth 분리 | leading word? — "search→analyze→report" stage 명사는 앵커, 그러나 강한 _Leitwort_ 는 약함 | 중복? — Safety Rules·Mode Routing 이 references 와 부분 중복 가능 | invocation 이 model/user 명시 안 됨(라우팅은 하되 frontmatter 분류 불명) |
| **post-it** | 실사용상 `/post-it` 슬래시로만 변경돼 user-driven 이나, frontmatter 에 `disable-model-invocation` flag **부재** → 원문 기준(user-invoked=disable flag)상 **model-invoked default**(판정 기준의 대칭 적용) | lean router — Quick Contract + Reference Map 3파일 | 불변식=steering — "fire-and-forget" "사용자는 들여다보지 않는다" 강한 앵커 | SoT 명시 — "영구 진실은 산출물… post-it 은 휘발성 작업면" | **invocation flag 명시 필요** — 실사용(user-driven)과 frontmatter 분류(model-invoked default)의 불일치 |
| **(예시) autopilot-code** | model? — 코드 파이프 entry | stage 분사 구조 | "plan→execute→test→report" 앵커 | 파이프 문서 중복 위험 | invocation 분류·leading word 강도 점검 필요 |

**Takeaway**: `post-it` 은 steering·SoT·lean router 정합은 모범이나 **frontmatter invocation flag 부재**(실사용 user-driven vs 원문 기준 model-invoked default)라는 gap 을 가지며, `autopilot-research` 는 IH 는 우수하나 **frontmatter invocation 분류 명시**와 **leading word 강도**에 gap 이 보인다 — 둘 다 전수 스캔에서 표준적으로 나타날 패턴이다.

> **표본 대표성 hedge**: 위 표의 실 스킬 근거는 `autopilot-research`·`post-it` 2개(+가설적 `autopilot-code`)로 표본이 얇다. gap 패턴은 예시적이며, 대표성은 §3 로드맵의 전수 audit 에서 확정한다.

## 3. 28개 스킬 전수 audit 절차 로드맵

analysis_summary §7 감사 체크리스트를 단계화. 각 Step 은 체크리스트 기반이며 Before/After 예시를 동반한다(예시는 원칙 설명용 **가공 예시**이며, 실제 스킬 인용 시 출처를 표기).

### Step 0 — Predictability(root virtue) 정합 점검

4축 레버 점검에 앞서, 각 스킬이 **Predictability(같은 *과정*의 재현)** 를 목표로 진술·구현하는지 확인한다 — 4축은 모두 이 root virtue 를 위한 수단이므로, root 목표가 흐릿한 스킬은 레버 점검이 무의미하다.

- **Before(가공)**: SKILL.md 가 "이 스킬은 X 를 한다"만 서술, 매 실행에서 *같은 과정*을 재현하도록 강제하는 장치(불변식·stage 계약·completion criterion) 부재.
- **After(가공)**: "매 실행 동일 과정 보장 — 불변식/stage 경계 명시"로 root virtue 를 진술 + 하위 레버가 이를 뒷받침.

### Step 1 — frontmatter invocation 전수 분류

code_search.md 의 카탈로그 방법을 재사용해 28스킬 전수 스캔: model-invoked(description 에 "Use when…" 트리거) / user-invoked(`disable-model-invocation: true`) 분류 + 트리거 유무.

```bash
# code_search.md 재현 명령의 harness 적용판
for f in $(find ~/.claude/skills -name SKILL.md); do \
  awk '/^---/{c++;next} c==1' "$f" | grep -E '^(name|disable-model-invocation):'; done
```

- **Before(가공)**: `description: "코드 리뷰 스킬"` — 트리거 없음, model/user 불명.
- **After(가공)**: `description: "Use when reviewing a diff for standards or spec conformance. …"` — 3인칭 + "Use when…" 트리거 명시(gerund 형태는 우리 컨벤션 선호이며 Anthropic verbatim 규범은 "third person"까지).

### Step 2 — 정량 규범 스캔

line count(<500) + reference depth(1-depth) + description 3인칭 + "Use when…"(gerund 형태는 우리 컨벤션).

```bash
for f in $(find ~/.claude/skills -name SKILL.md); do \
  echo "$(wc -l < "$f") $f"; done | sort -rn | head   # 500 초과 후보
```

- **Before(가공)**: SKILL.md 780줄, references 2-depth(references/a.md 가 다시 sub/b.md 참조).
- **After(가공)**: body 420줄 + references/ 1-depth 평탄화.

### Step 3 — failure-mode 후보 flag (no-op/sediment/duplication/sprawl)

문장 단위 no-op 테스트(모델이 기본으로 이미 하는가) + cross-skill duplication(같은 규칙이 여러 SKILL.md 에 = SoT 위반) + sediment(낡은 문장) + sprawl(불필요 인라인).

- **Before(가공)**: *"Claude 는 코드를 신중히 읽어야 한다."* — no-op(기본 행동, 행동 변화 없음).
- **After(가공)**: 문장 통째 삭제("delete the whole sentence… Be aggressive"). duplication 은 한 권위 자리로 통합 + 나머지는 pointer.

### Step 4 — completion criterion / premature completion 점검 (Steering failure)

Steering 축의 조기 종료 failure 를 스캔한다: completion criterion 이 **checkable + exhaustive** 한가 / 관찰된 **rush(premature completion)** 신호가 있는가 / **post-completion steps 가 실제 context 경계(subagent·user hand-off) 뒤에** 있는가(인라인 model-invoked 는 숨겨지지 않음).

- **Before(가공)**: "작업이 끝나면 마무리한다." — 완결 판정 기준 부재(무엇이 "끝"인지 checkable 하지 않음) + 후속 단계가 본문에 노출돼 조기 종료 유발.
- **After(가공)**: "completion = 아래 3개 산출물이 모두 존재할 때. 그 뒤 단계는 stage 경계 뒤로 분리." — checkable+exhaustive 기준 + post-completion steps 를 context 경계 뒤로 이동.

### Step 5 — leading-word / negation 재작성 후보

약한 동사구 → pretrained prior 소환 단어(_Leitwort_). negation → positive.

- **Before(가공, leading word)**: *"작은 단위로 나눠서 하나씩 테스트하며 진행한다."*
- **After(가공)**: *"vertical slice 로 진행 — 각 test 는 tracer bullet."* (tdd 실물 leading word 차용, 출처: tdd-skill-example)
- **Before(가공, negation)**: *"description 을 모호하게 쓰지 마라."*
- **After(가공)**: *"description 에 'Use when…' 트리거를 첫 문장으로 둬라."* (긍정 지시)

### Step 6 — context pointer wording 견고성 점검

must-have 자료가 약한 pointer 뒤에 있으면 variance bug(동전 던지기식 로딩).

- **Before(가공)**: *"필요하면 참고 파일을 볼 수도 있다."* (약한 pointer, must-have 인데 조건부)
- **After(가공)**: *"실행 전 references/pipeline.md 의 Step 2 를 반드시 Read 한다."* (강한 pointer, 도달 시점·의무 명시)

### Step 7 — 우선순위 정렬

impact × 수정비용으로 정렬 → 개선 spec 입력. auto-activation·SoT 위반 같은 high-impact 는 상위, 문구 다듬기는 하위.

**Takeaway**: 8-Step(0~7)은 root virtue 정합(Step 0) → 기계적 스캔(Step 1-2) → 판정 필요(Step 3-6) → 우선순위(Step 7) 순으로 비용이 증가하며, Step 1-2 는 스크립트로 전수 자동화하고 Step 0·3-6 만 사람/에이전트 판정에 남긴다. 이 구성은 02 의 failure-mode 6종을 빠짐없이 커버한다(no-op/sediment/duplication/sprawl=Step 3, premature completion=Step 4, negation=Step 5; variance bug=Step 6).

## 4. Next Pipeline

| Inferred Goal | Recommended next command | Rationale |
|---|---|---|
| adopt/audit (사후 점검·drift 진단) | `/audit` | 산출물·스킬셋 사후 점검, 4축 정합 drift 진단 |
| build (개선 spec 필요 시) | `/autopilot-spec "28-skill 4-axis audit 개선 청사진"` | audit 결과를 개선 spec 으로 정형화 (spec-first 게이트) |
| build (개선 실행) | `/autopilot-code --mode refactor "28-skill 4-axis audit 반영"` | 축별 수정을 버전 트래킹하며 실행 |

권장 순서: `/audit` → (필요 시) `/autopilot-spec` → `/autopilot-code --mode refactor`.

**Takeaway**: 먼저 `/audit` 로 4축 정합 drift 를 전수 진단하고, gap 이 확인되면 `/autopilot-spec` 으로 개선 청사진을 정형화한 뒤 `/autopilot-code --mode refactor` 로 축별 수정을 버전 트래킹하며 실행한다 — spec-first 게이트를 지키는 단방향 순서다.

> **Boundary disclaimer**: 이 06_implementation.md는 분야 분석에서 도출된 high-level 계획입니다. 스킬셋 전수 audit(28개)은 본 보고서 범위 밖의 별도 사이클이며, 본격적인 점검·개선은 /audit → /autopilot-spec → /autopilot-code로 인계됩니다.

## 5. Cross-References & 요약

- 4축 개념 정의·계보 → [01_landscape.md](01_landscape.md)
- 정량 스캔 기준(500줄·1-depth·3인칭 "Use when…") → [02_standards.md](02_standards.md)
- 원칙 메커니즘(왜 이렇게 audit 하나) → [04_technical_deep_dive.md](04_technical_deep_dive.md)
- 배포 시 context budget·failure mitigation → [05_deployment.md](05_deployment.md)
- 소스·재현 명령 → [07_resources.md](07_resources.md)

**요약**: 우리 harness 는 이미 SKILL.md(router) + references/(3-rung disclosure) 구조로 Pocock 의 Information Hierarchy 를 구현하고 있어, 4축 audit 은 새 구조 도입이 아니라 정합성 점검이다. 28스킬 전수 audit 은 Predictability 정합(Step 0) → frontmatter invocation 분류(Step 1) → 정량 규범 스캔(Step 2) → failure-mode flag: no-op/sediment/dup/sprawl(Step 3) → completion criterion/premature completion(Step 4) → leading-word/negation 재작성(Step 5) → pointer wording 견고성(Step 6) → 우선순위 정렬(Step 7)의 8단계로 진행하며, 02 의 failure-mode 6종을 빠짐없이 커버한다. 예시 스캔에서 `post-it` 은 steering·SoT 는 모범이나 frontmatter invocation flag 부재 gap, `autopilot-research` 는 frontmatter invocation 분류와 leading word 강도에 gap 을 보였다(표본 2개로 예시적, 대표성은 전수 audit 에서 확정). 실행은 `/audit → /autopilot-spec → /autopilot-code --mode refactor` 로 인계되며, 전수 audit 자체는 본 보고서 범위 밖의 별도 사이클이다.
