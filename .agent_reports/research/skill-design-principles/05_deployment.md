# 05 · 우리 harness 적용 시 배포 고려사항 — Skill Design Principles

> mode: technology · date: 2026-07-13
> 우리 자체 harness(28개 skill)에 4축 원칙을 얹을 때의 배포 관점. 04_technical_deep_dive 의 메커니즘과 중복을 피하고 *배포·운영* 측면만 다룬다.

## 1. Reference Architecture — skill 로딩 흐름 (4축 관점)

우리 harness 의 skill 로딩은 Anthropic 3-level 과 Pocock 3-rung 을 동시에 구현한다.

```
[Level 1 · always @ startup]   description 상주 (~100 tokens/skill)
   28 skill × description        ──► Invocation 축: context load 지불
   + hook 신호(workflow-guard)         (auto-activation 불안정 → hook 보강)
        │
        │  트리거(발화/hook 강제)
        ▼
[Level 2 · when triggered]      SKILL.md body 로드 (<5k tokens, <500 lines)
   router SKILL.md               ──► Information Hierarchy 축: rung 1-2
   (Quick Contract / Task 분기)         step + in-file 개념만, lean 유지
        │
        │  Required Reads / Reference Map (context pointer)
        ▼
[Level 3 · as needed]          references/*.md on-demand 로드
   references/invocation-and-modes.md   ──► IH 축: rung 3 (external ref)
   references/pipeline-*.md              progressive disclosure
   references/report-generation.md       pointer wording 이 도달 신뢰도 결정
```

실물 예시 — `autopilot-research/SKILL.md` 의 `## Required Reads` + `## Reference Map` 절이 곧 context pointer 집합이며, body 는 *"라우터와 stage 계약만"* 담고 상세는 references/ 로 밀어냈다(progressive disclosure). `post-it/SKILL.md` 는 *"본 SKILL.md 는 라우터"*임을 명시하고 불변식만 body 에 둔다.

**Takeaway**: 우리 harness 는 이미 3-rung progressive disclosure 를 구현하고 있어, 4축 audit 은 "새 구조 도입"이 아니라 "기존 구조의 정합성 점검"이다.

## 2. Context Budget Breakdown

| 항목 | 추정 | 근거 |
|---|---|---|
| description 상주 (Level 1) | 28 skill × ~100 tokens ≈ **~2,800 tokens** always-loaded | anthropic-skills-overview: ~100 tokens/skill |
| 트리거 시 body (Level 2) | 스킬당 **<5k tokens** (라우터는 실제 훨씬 작음) | anthropic-skills-overview: Level 2 <5k |
| references (Level 3) | 필요 branch 만, on-demand | progressive disclosure |
| hook 신호 상주 | mem-recall-inject·workflow-guard 주입분 (추가 상주) | harness 고유 |

- **상주 비용의 함의**: 28 skill 의 description 합(~2,800 tokens)이 매 턴 어텐션 경쟁에 참여한다. skill 수가 늘수록 description sprawl 이 *다른* 스킬 발화 정확도를 깎으므로(Invocation 축 메커니즘), description pruning 이 배포 우선순위다.
- **hook 상주분**은 auto-activation 보강 대가로 추가 context 를 쓴다 — wording 단독의 자동발화 불안정(hook 후에도 ~50%, scottspence)을 보강하려는 지출로 합당한 방향이나, hook 이 신뢰도를 끌어올린다는 이득 자체는 측정 미검증이고 hook 주입 텍스트도 pruning 대상이다.

**Takeaway**: 28스킬 description 합(~2,800 tokens)이 상주 예산의 핵심이며, description pruning 이 가장 비용 효율 높은 배포 최적화다.

## 3. Integration Paths — 기존 28스킬 → 4축 audit 마이그레이션

| 경로 | 절차 | 위험 |
|---|---|---|
| **점진(권장)** | 축별 스캔(Invocation→IH→Steering→Pruning) → flag → 우선순위 정렬 → skill 단위 수정 | 낮음 (되돌림 가능) |
| **일괄 rewrite** | 전 스킬 동시 재작성 | 높음 (회귀·버전 이력 손실) — 지양 |
| **hook 우선** | description wording 개선 전에 hook 라우팅부터 강화 | 중 (근본 wording 문제 은폐 위험) |

권장 = **점진 경로** + 각 수정을 `autopilot-code --mode refactor` 로 버전 트래킹. 산출물 폴더는 CONVENTIONS §5(T1 root / T2 named subdir / T3 `_internal/`) 준수.

**Takeaway**: 마이그레이션은 축별 점진 스캔으로 진행하고 skill 단위로 버전 트래킹해야 하며, 일괄 rewrite 는 회귀·이력 손실 위험으로 지양한다.

## 4. Failure Modes + Mitigation (배포 관점)

04 의 메커니즘과 달리, 여기서는 *배포·운영* 시 나타나는 실패와 대응만.

| 배포 failure | 증상 | mitigation | harness 자산 |
|---|---|---|---|
| auto-activation 불안정 | model-invoked skill 이 발화돼야 할 때 무시됨; hook 워크어라운드 후에도 ~50% 잔존(scottspence) | **hook 강제 라우팅**(합당한 방향, 신뢰도 이득 미검증) | `mem-recall-inject`, `workflow-guard-hook` |
| description sprawl | 28 skill description 합이 상주 예산 잠식 | **description pruning** (no-op/relevance) | audit Step 2·3 |
| cross-skill duplication | 같은 규칙이 여러 SKILL.md 에 중복 | **SoT** — 한 권위 자리로 통합, 나머지는 pointer | CONVENTIONS·DESIGN_PRINCIPLES |
| variance bug | must-have reference 가 약한 pointer 뒤 | **pointer wording 강화** | Required Reads/Reference Map 점검 |
| premature completion | 파이프 stage 가 조기 종료 | **completion criterion 명시 + stage 경계 분사** | stage-dispatch(OPERATIONS §5.10) |

**Takeaway**: 우리 harness 의 배포 failure 는 대부분 이미 대응 자산(hook·CONVENTIONS·stage-dispatch)을 갖고 있으며, audit 의 역할은 새 방어 구축이 아니라 *기존 자산의 커버리지 점검*이다.

## Cross-References

- 4원칙 메커니즘(왜 실패하나) → [04_technical_deep_dive.md](04_technical_deep_dive.md)
- audit 절차 상세 → [06_implementation.md](06_implementation.md)
- 정량 규범 스캔 기준 → [02_standards.md](02_standards.md)
