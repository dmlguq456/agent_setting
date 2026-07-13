# BLOCKING FINDING — audit/PRD target tree is not the live Claude skill source

> 발견 시점: Cluster 2 실행 완료 직후(sync-skills 게이트 시도 중), 2026-07-13.
> 심각도: spec-significant — PRD 전체 대상 범위 재검토 필요.

## 무엇을 발견했나

`skill_design_audit.md`/`skill_design_audit_per_skill.md`(그리고 이를 그대로 인계한 본 PRD)가 진단·리팩터 대상으로 삼은 `<repo>/skills/*/SKILL.md` (root) 는 **더 이상 Claude 런타임의 live source 가 아니다**.

- `sync-skills` 스킬 정의(SKILL.md 본문, invoke 시 로드) 는 명시한다: "**Source of Truth**: `<agent-home>/adapters/claude/skills/*/SKILL.md` … `<agent-home>/skills/*/SKILL.md` 는 historical compatibility reference 로 보존하며, Claude runtime source 로 취급하지 않는다."
- `capabilities/README.md`(2026-06-29 도입, `cda5052 docs: add portable capability catalog`) 도 동일하게 명시: "Claude Code realizes these capabilities through adapter-owned concrete Skill files under `adapters/claude/skills/*/SKILL.md`. Historical `skills/*/SKILL.md` files remain compatibility references while portable contracts move into this directory."
- `tools/build-manifest.py` (manifest.json/doctor/parity 체크의 근거) 는 **오직 `adapters/claude/skills/*/SKILL.md`** 만 glob 한다(root `skills/` 는 전혀 안 읽음, :169).
- `adapters/claude/skills/` 는 이미 root `skills/` 와 **내용이 divergent** — 예: `analyze-project` 의 `<artifact-root>` 스니펫 wording·Required Reads 절 형식이 서로 다르고, git log 상 `adapters/claude/skills/` 는 "Split 12 monolithic Claude skills into router references" 등 최근 별도 리팩터를 거쳤다. 즉 두 트리는 **이미 별개로 발산**해 있었다(본 PRD 착수 이전부터).
- `skill_design_audit{,_per_skill}.md` 는 `capabilities/`·`adapters/claude/skills` 를 **한 번도 언급하지 않는다**(grep 0건) — audit(2026-07-13) 이 capabilities 카탈로그 도입(2026-06-29, 2주 전) 사실을 놓치고 legacy 트리를 "the 28 skills" 로 오인해 진단했다.

## 무엇을 실행했나 (Cluster 2 + CORE)

Plan §1(CORE-1~4)·§2(C2-1~5) 를 root `skills/` + `core/*.md` + `roles/modes/design/_design_rules.md` 에 정확히 완료·검증(grep 0건 완료 기준 전부 충족, `tools/skill-conformance/scan.sh` 통과) 후 커밋(`cd48b25`) 했다. **이 작업 자체는 PRD 지시(§ "대상: `<이 worktree>/skills/`")를 그대로 따랐고 behavior-preserving 이며 root skills/ 트리 내에서는 정합하다.**

**그러나** SD-6 게이트("각 Cluster 완료 시 sync-skills 실행 + adapter doctor/parity mirror 검증 의무")를 satisfy 하려 sync-skills 를 호출한 결과, 위 사실이 드러났다: root `skills/` 편집은 **manifest.json/doctor/parity 파이프라인에 전혀 반영되지 않는다** — sync-skills 가 실제로 읽는 소스가 다른 트리이기 때문이다. 즉 SD-6 게이트는 **root skills/ 를 대상으로는 구조적으로 통과 불가능**(만족시킬 대상 자체가 없음).

## 왜 이게 spec-significant 인가

- 이 PRD 의 근본 전제("28스킬 Pocock 4축 진단이 수렴한 gap 을 튜닝") 가 가리키는 실제 결함(Plan Resolution 4중 복제·Language Rule 5중 복제·13 라우터 이중서술·autopilot-design 315줄·13개 순수 sub-skill invocation 오분류)이 **live 런타임(`adapters/claude/skills/`)에도 실재하는지 별도 확인이 안 됐다.** `adapters/claude/skills/` 가 이미 다른 리팩터를 거쳐 router-reference 구조로 바뀌어 있으므로, 같은 결함이 그대로 있을 수도, 이미 해소됐을 수도, 다르게 나타날 수도 있다.
- root `skills/` 계속 편집해봐야 **사용자가 실제로 Claude Code 에서 겪는 스킬 동작에 영향 0** — 이 PRD 의 목적(Predictability·context 절약) 자체를 달성 못 한다.
- 라인 넘버 기반 audit 근거(`skill_design_audit_per_skill.md` 의 file:line)가 `adapters/claude/skills/` 에는 **그대로 안 옮는다**(divergent). Cluster 3(sprawl 추출)·Cluster 1(invocation flip) 을 `adapters/claude/skills/` 로 재대상화하려면 **audit 재실행이 필요**할 가능성이 높다(최소한 line 재검증).

## 권고 (main/spec 세션 결정 필요 — 본 conductor 는 spec 직접 수정 안 함)

1. **audit 재검증 범위 결정**: `adapters/claude/skills/*/SKILL.md` (28개 확인됨, 개수는 root 와 동일) 에 대해 Pocock 4축 rubric 을 **재실행**할지, 아니면 기존 audit 결론(구조적 패턴 — Plan Resolution 복제·13 sub-skill invocation 문제 등)이 새 구조에도 정성적으로 유효하다고 보고 **plan 만 재작성**(line 재검증 + 새 라우터 구조 반영)할지.
2. **root skills/ 트리의 운명 결정**: "historical compatibility reference" 로 완전히 방치(deprecate) 할지, 아니면 root→adapters 로의 **역-동기화(sync-skills 확장)** 가 계획돼 있는지 확인. 후자라면 이번 Cluster 2 작업이 유효한 선행 투자가 되고, 전자라면 되돌리거나 최소 "죽은 트리 편집이었다"는 사실을 인지만 하고 넘어가면 된다.
3. **PRD v2 필요 여부**: 위 결정에 따라 skill-design-refactor PRD 를 `adapters/claude/skills/` 기준으로 갱신(`_internal/versions/v1/` 스냅샷 후 v2)할지 autopilot-spec 세션에서 결정.

## 본 conductor 의 조치

- Cluster 2 + CORE 커밋(`cd48b25`)은 **유지**(root skills/ 관점에서 정합·PRD 문면 그대로 실행·비파괴적) — 되돌리지 않음. 위 권고 ②에서 "죽은 트리"로 결론 나도 git 이력으로 언제든 revert 가능.
- **Cluster 3(sprawl 추출)·Cluster 1(invocation flip) 은 착수하지 않고 중단**한다 — 같은 오류(잘못된 트리 대상)를 반복하지 않기 위해. 특히 Cluster 1 의 `disable-model-invocation` frontmatter flip 은 root skills/ 에 넣어봐야 **manifest.json 에 반영 안 돼 실제 invocation 동작에 영향 0**(trial-flip 게이트 자체가 무의미해짐 — 검증 대상 시스템이 그 파일을 안 읽으므로).
- `sync-skills --check` 결과·manifest 비교 로그를 아래에 첨부.
