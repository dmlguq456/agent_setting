# Autopilot Design Principles

> `<agent-home>/core/` 의 _아키텍처 헌법_ — autopilot family 가 어떻게 분리되고 어떻게 협력하는지의 single source.
>
> 자매 문서 (각자 단일 출처, 본 문서는 포인터만):
> - `CONVENTIONS.md` — QA 5단계 / agent model 표기 / 산출물 폴더 컨벤션 (§5) / hard invariants
> - runtime adapter bootstrap (Claude Code: `adapters/claude/CLAUDE.md` §0~§3) — 작업 라우팅 (spec-first 파이프 + autopilot-* 호출 Pre-check) + 메인 에이전트 행동 메타 원칙 (응답 규율·pause/자율·후속 단계)
>
> 본 문서는 _구조와 행동의 골격_ 만 담고, 정의·정책·운영 wording 은 위 자매 문서로 위임.

---

## §0. 존재의의 — model-agnostic skeleton (다른 모든 절보다 상위)

이 레포(`<agent-home>`)의 근본 목적은 **특정 LLM 에 종속되지 않는, 어떤 모델로 갈아타도 동작하는 작업 substrate(skeleton)** 다. _"평생 Claude 만 쓴다는 보장은 없다."_ 모든 스킬·에이전트·하네스는 _프롬프트 + 로컬 도구 + 인코딩된 판단 규칙 + scaffold_ 로 구성돼, 모델을 갈아끼워도 그 골격 위에서 동작한다.

- **가치 판단 규칙 (불변)**: 어떤 능력이 특정 벤더 내장(Claude Design · deep-research 등)으로 _지금 더 잘_ 되더라도, **그것을 이유로 우리 온프레미스 구현을 빼지 않는다.** 벤더 advantage 는 그 벤더에 묶여 있어 모델 전환 시 증발하지만, 우리 스킬은 살아남는다.
- **평가 기준의 전환**: 산출물·스킬을 _"현재 Claude 대비 우열"_ 로 재지 않는다. 기준은 _"다른 LLM(GPT·Gemini·로컬)이 몰아도 그럭저럭 동작하는가"_. 따라서 **_실사용 빈도 0 도 제거 근거가 아니다_** — 일부는 daily tool 이 아니라 _모델 전환 대비 보험·substrate_ 다.
- **그래서 internalization**: 벤더 내장의 잘 설계된 파이프는 _RE 해서 우리 스킬로 흡수_ 한다 (deep-research → 연구팀 claim-verify, `/security-review` → qa security-review, Claude Design 공개 룰 → `_design_rules.md` 등). 호출이 아니라 _자급 재구현_ — 의존 없이 단독으로 돈다. 작업·소스 보존 = `nas_Uihyeop/claude-meta-spec/`.

> 구조 결정(역할 분리·QA·산출물 컨벤션)이 이 §0 과 충돌하면 **이 원칙이 우선**한다.

---

## §0.5 결정론 우선 — deterministic-first (cross-cutting, §0 다음 상위)

> 2026-06-15 사용자 핵심 원칙. §1 의 _Orchestrator = deterministic state machine_ 을 **전 스킬·하네스의 보편 tenet 으로 격상**.

**결정론적·소프트웨어로 처리 가능한 요소는 가능한 한 코드(hook·script·gate·DB 제약)로 대체해, 에이전트가 _생각_ 할 영역을 최소화한다.** 그래야 에이전트가 진짜 판단이 필요한 자리에 집중해 더 똑똑·신뢰성 있게 동작한다.

- **왜**: 매 agent 판단은 비결정·실수 가능·토큰 비용. 결정론 기계화는 무료·정확·재현가능. (또 §0 과 정합 — hook/script/gate 는 모델 전환에도 살아남는 substrate, agent 판단은 모델 능력에 종속.)
- **적용 규칙**: 새 기능·정책 설계 시 _"이걸 코드로 강제·자동화할 수 있나?"_ 를 **먼저** 묻는다. 가능하면 instruction(에이전트 판단)이 아니라 메커니즘(hook/script/gate/DB)으로. **agent judgment 는 결정론이 불가능한 의미·창의 판단의 _fallback_.**
- **발현 예**: orchestrator state machine(§1) · artifact-guard·git-state·pipeline-lock hook · 메모리 write 게이트·dedup·만료·turn-counter nudge · QA gate 통과기준. ↔ anti-pattern: "에이전트가 매번 알아서 판단" 으로 떠넘기기 (재현 불가·드리프트).

> 구조 결정이 본 §0.5 와 충돌하면 (§0 다음으로) **이 원칙을 우선** 적용한다 — 단 결정론화가 *과한 경직*을 낳는 자리(진짜 의미 판단)는 예외.

---

## §0.7 의미↔규칙 경계 검증 — semantic↔rule boundary verification (cross-cutting, §0.5 의 검증 층)

> 2026-06-22 worklog-board 참사 계기. §0.5(결정론 우선)는 _설계 시점_에 "이걸 코드로 강제 가능한가"를 먼저 묻는 원칙이고, 본 §0.7은 _작성·완료·회귀 시점_에 "그 경계가 의미를 규칙으로 떨구지 않았나"를 재검하는 검증 층이다 — §0.5와 시점·동작이 달라 재탕이 아니며, §0.5 내용을 복사하지 않고 참조만 한다.

**규칙(deterministic)이 맡는 것** = 큰 갈래 경계·정책 (라우팅·gate·hard 불변식). 세부 의미 판단(맥락·적절성·"의미상 맞는 매칭")은 LLM의 몫 — §0.5의 _fallback_ 규정과 정합 (참조: §0.5 line 32 fallback 절, line 35 예외절).

**본 §0.7의 검증 _판정_ 자체**(어느 구간이 의미요구인가·구현이 의미를 capture 했나)는 의미 판단이라 §0.5 line 35 예외절·line 32 fallback에 해당 — 결정론화 대상이 아니다. 단 검증의 _발사_(언제·어디서 도나)는 결정론으로 강제한다(Step 3d substep·audit auto-scope·drill 회귀). 즉 _판정은 LLM·발사는 결정론_ 분리 — 이게 §0.5와의 정확한 정합점이다.

**anti-pattern (worklog 참사형, 2026-06-22)**: spec이 "의미 판단"을 명시했는데 구현이 그 의미를 토큰 매칭·규칙 스크립트로 *내려버리는* 것. 규칙은 의미를 capture 못 하므로 silent 오작동.

**검증 절차 (3 step)**:

- **(a)** spec 본문에서 _의미 판단 구간_ 찾기 (키워드 신호: 의미/판단/적절/맥락/contextual/semantic 등).
- **(b)** 대응 구현이 그 의미를 _규칙으로 떨궜는지_ 확인 (토큰 매칭·정규식·고정 룰만으로 의미 판단을 대신하고 있나).
- **(c)** 충돌 시 **3선택**: ① spec 재정의 (의미 요구를 규칙으로 표현 가능하게 좁힘) / ② 구현 수정 (의미 판단을 LLM 단계로 올림) / ③ LLM 판단문 추가 (규칙 갈래 뒤에 의미 판단 fallback 명시).

**적용 자리 (3 시점 커버)**:

- autopilot-spec Step 3d (_저술 시점_ — PRD 작성 중 의미 구간 표시)
- audit plans aspect (_완료 시점_ — done plan에서 spec 의미요구 ↔ 구현의 drift 재검출, Step 3d 통과분이 이후 코드 수정으로 어긋났나)
- drill g7 (_회귀 시점_)

본 §0.7은 그 세 층의 _공통 정의 출처_ — 각 층은 본 절을 참조한다 (재정의 금지). **미커버: autopilot-code dev 단계(구현이 의미요구를 규칙으로 떨구는 _순간_)는 현재 게이트가 없어 사후 audit에서만 잡힌다 — 향후 확장 여지. 즉 본 체계는 _완전_ 커버가 아니라 저술·완료·회귀 _3 시점_ 커버다.**

> 운영 1-liner 불변식 = CONVENTIONS §3 #7. 본 절이 상세 단일 출처.

---

## §0.8 Loop Engineering 제1원칙 — core first, adapters derived

**공통 원칙(core) 확정 → 어댑터 파생. 어댑터 선행 수정 금지.** 어댑터에서 발견된 개선 필요도 반드시 `core/` 의 모델 중립 계약으로 올려 확정한 뒤, 각 adapter runtime surface 로 파생한다. 예외 없음.

- **왜**: adapter 는 런타임 매핑이고 core 는 의미 계약이다. adapter 를 먼저 고치면 같은 행동이 Claude/Codex/OpenCode 사이에서 갈라지고, 다음 포팅 때 의도를 잃는다.
- **절차**: ① 관련 core 문서를 읽고 ② core 계약을 갱신하거나 core 에 이미 계약이 있음을 확인한 뒤 ③ adapter bootstrap·hook·projection 을 수정한다.
- **기계화**: `core-read-marker` + `core-first-guard` 는 `adapters/**` 편집 전에 이번 세션의 `core/*.md` 실제 read marker 를 요구한다. hard gate 는 검증 가능한 read marker 까지만 맡고, “core 를 실제로 먼저 고쳤는가”는 본 원칙과 drill 이 보완한다.
- **위반 사례**: 2026-07-03 `adapters/claude/CLAUDE.md` 회상 행을 core 확정 없이 선수정했다가 revert. 이 사건을 계기로 본 불변식과 guard 를 추가했다.

---

## §0.6 긍정형 지침 — 부정형 직접금지 절제 (cross-cutting, 지침 _편집_ 의 tenet)

> 2026-06-17 사용자 핵심 원칙. 지침을 _고칠 때_ 의 방법론, 특히 hotfix-patch 식 피드백 반영 자리.

**원하는 행동을 지침에 _기술_ 한다 — 원치 않는 행동을 "하지 마"로 막으려 하지 않는다.** 부정형 직접금지("X 하지 마")는 X 를 _언급_ 함으로써 오히려 prime 한다 ("코끼리를 생각하지 마" 효과). hotfix 로 누적되면 금지문 더미가 되어 잡음·prime↑, 유지보수↓.

- **왜**: 언급 자체가 신호다. 안 했을 행동을 "하지 마"로 적으면 그 행동을 _떠올리게_ 만들어 빈도가 되레 오른다. 또 금지 패치는 근본(왜 그 행동이 나왔나)을 안 고치고 증상만 덮는다.
- **올바른 수정 (근본)**: bad behavior 가 _어떤 지침의 잘못된 mention·여지에서_ 비롯됐으면, 금지문을 _덧붙이는_ 게 아니라 **그 원래 mention 을 제거하거나 positive 로 재작성** 한다. _애초에 언급이 없었으면 안 했을 일_ 이면 → 언급을 없앤다. (행동이 지침과 무관한 외부 요인에서 왔을 때만 새 지시를 고려.)
- **부정형 예외 (드물게)**: 안전·비가역·하드 게이트(파괴 작업·보안)처럼 positive 재구성이 불가능하고 _반드시_ 차단해야 하는 자리만. 그 외엔 positive 가 default.
- **적용**: 모든 instruction 편집(autopilot-spec·autopilot-code meta-skill·직접 hotfix). meta-skill 리뷰(연구팀)가 _부정형 남용·prime 위험·증상-덮기 패치_ 를 체크 축으로 잡는다.

---

## 1. 3-Tier Role Separation

| Tier | Role | 예 | Anti-pattern |
|------|------|-----|--------------|
| **Orchestrator** | Deterministic state machine. 라우팅·gate·verdict 만, content 안 봄. | `autopilot-code` / `autopilot-draft` / `autopilot-research` / `autopilot-refine` 의 SKILL.md 본체 | Orchestrator 가 file content 읽기·요약·판단 |
| **Skill** | Expert capability module. WHAT + selected verification/assurance gate 정의. | `code-plan` · `code-execute` · `code-test` · `draft-strategy` · `draft-refine` 등 | Skill 안에 전체 pipeline graph나 반복 QA loop를 숨김 |
| **Agent** | Persona with tools. Skill 안에서 실제 작업 수행. | `기획팀` · `품질관리팀` · `연구팀` · `편집팀` · `자료팀` · `개발팀` · `디자인팀` · `external-adversary` | Agent 가 verbose 결과를 orchestrator 로 반환 |

> **이름 충돌 주의**: 본 절의 _3-Tier_ 는 _역할 분리_. §4 의 _3-tier T1/T2/T3_ 는 _산출물 가시성 분리_. 같은 숫자지만 다른 layer.

### Interface Contract

```
Orchestrator → Agent:  file paths + 1-line task directive
Agent → Orchestrator:  file path + verdict token (한 줄)
Agent ↔ Agent:         file system 통해 (B 가 A 가 쓴 파일을 read)
```

Orchestrator 는 _내용을 매개하지 않는다_ — 오로지 path 만 전달.

### "No Read" 의 범위

이 규칙은 **orchestrator 에만** 적용. Skill 본문과 그 안 agent 는 file 을 자유롭게 read — orchestrator 는 delegate, skill·agent 는 execute.

### Stage 통합 orchestrator 의 예외

orchestrator 가 _단일 expert flow_ 만 다루는 경우 (예: `autopilot-refine` Stage A~E — investigate · plan · diff preview · apply · report 가 한 흐름) sub-skill 분리 비용이 커, orchestrator 가 직접 file read·Edit 해도 헌법 위반 X. _sub-skill 분리_ 는 _두 개 이상의 expert capability_ 가 모일 때만 의미 있고, 단일 expert flow 는 orchestrator-also-execute 가 정당.

같은 원칙이 `final-report` 의 _다른 artifact dir (`analysis_project/code/`) 보강 write_ 같이 _자기 책임의 자연 확장_ 자리에도 적용 — sub-skill 책임 범위가 자기 폴더에 한정된다는 _엄격 해석_ 은 헌법 의도 아님. 신규 sub-skill 도입 시 _분리해야 할 expert capability 가 둘 이상인가_ 만 점검하면 충분.

---

## 2. Default Behavior — Autopilot 정신

family 의 모든 멤버는 confirm 없이 pipeline 을 끝까지 돌린다. 사용자가 명시할 때만 멈춘다.

- `--user-refine` / `--confirm` 같은 pause flag 는 **사용자가 직접 typed 한 자리에서만** 켠다 (default false).
- `--intensity thorough|adversarial` 같은 비싼 stage graph는 명시 신호나 high-risk routing이 있을 때만. `--qa`는 assurance override이며 graph/depth selector가 아니다 — CONVENTIONS.md §1.
- 실패 시 fail loudly + `pipeline_summary.md` 미해결 기록. 다음 호출에서 `--from <stage>` 재개.

**Why**: 사용자가 _명시 요청_ 을 했는데 메인 에이전트가 _신중을 위해_ 라며 confirm 단계를 추가하면 작업이 한 turn 지연되고 "이미 했어?" 같은 follow-up 으로 갈등이 누적. high-stakes 일수록 사용자가 _직접_ pause 를 거는 게 자연스럽다.

**강제 위치**: runtime adapter bootstrap 의 응답 원칙(Pause·자율 진행; Claude Code realization: `adapters/claude/CLAUDE.md` §2) + 각 SKILL.md `--user-refine` 절 default false.

---

## 3. Implicit Input Discovery

입력 자료는 _프로젝트 컨텍스트 내부의 영속 산출물_ 에서 자동 발견한다.

- `<artifact-root>/analysis_project/{code,paper,doc}/*` — analyze-project 산출물
- `<artifact-root>/research/{topic}/*` — autopilot-research 산출물
- 외부 raw 자료는 `analyze-project --mode {code|paper|doc}` 으로 먼저 영속화 → 이후 skill 이 fuzzy match 로 implicit 인지

**Why**: 한 세션 한 프로젝트의 단순한 가정 (cwd = working dir) 이 cognitive cost 를 낮추고, 영속 산출물 재활용성을 높인다. cross-project 작업은 `cd <other>` 후 별도 세션.

---

## 4. Artifact Convention — 3-tier T1/T2/T3

Artifact 폴더 안의 _가시성 분리_. 상세는 CONVENTIONS.md §5 single source.

| Tier | 위치 | 예 |
|---|---|---|
| **T1** Primary | root | `pipeline_summary.md`, `draft/`, `plan/` |
| **T2** Secondary | named subdir | `strategy/`, `analysis/`, `dev_logs/`, `test_logs/`, `cards/` |
| **T3** Tertiary | `_internal/` 하위 | review logs, version 스냅샷, raw scan metadata |

### Minor vs Major 변경

같은 artifact 의 후속 변경도 두 layer 분리:

| Tier | 처리 | 추적 |
|---|---|---|
| **Minor** (default) | 직접 Edit | `pipeline_summary.md` 안 minor log entry |
| **Major** (3-criteria — 사용자 명시 / 구조적 ≥200 줄 / 외부 검토 직전) | `/autopilot-refine` ceremony | snapshot + 통합 history + QA |

누적 minor 5건 도달 시 `/audit` chat alert → audit 이 dual-perspective (vs last major + vs universal principles) batch 점검.

상세 — `autopilot-refine/SKILL.md` Default Invocation Rule + runtime adapter bootstrap 의 도메인 트리거 표(Claude Code realization: `adapters/claude/CLAUDE.md`).

---

## 5. Quality Gates

Quality gates live inside the selected stage graph. The orchestrator chooses `intensity` first, then `--qa` scales `plan-check`, selected independent passes, and final verification. A high QA level does not open hidden stages, repeated loops, or depth2 workers by itself.

- **QA assurance levels** (quick / light / standard / thorough / adversarial) — CONVENTIONS.md §1 single source. They are budgets for selected checks, not pipeline selectors.
- **Stage-local gates** stay small and only decide whether the next stage can proceed.
- **Independent QA passes** run only where the selected intensity/risk calls for them: strongest risk point for `strong`, bounded depth2 for `thorough`, adversary/security/claim-verify for `adversarial`.
- **Fact/source checking** applies to doc / research / refine / note claims when selected; code has no fact-checker because ground truth is code/tests/runtime behavior. `--no-fact-check` remains limited to capabilities that expose it.
- **Natural-integration rule** (paper mode 한정) — reviewer 의견 → 본문 mutation 옮길 때 표·enumeration 통째 paste 금지. 1~2 문장 in-line rewrite 가 안 되면 drop 또는 Appendix. 4-step Paragraph Cohesion Pre-Check (substance 중복 / paragraph axis / cross-section redundancy / EDIT·REPLACE·INSERT·DROP 분류) 가 mechanical INSERT 사전 차단. 상세 — `init-doc-strategy/SKILL.md` paper mode + `autopilot-draft/SKILL.md` Step 4.1.

**Why**: QA budget이 stage graph와 섞이면 작은 작업도 full ceremony가 되고, 반대로 cross-harness 검증은 monolithic skill 안에서 열 수 없다. Graph는 intensity가, assurance는 QA가 소유해야 토큰 비용과 검증 강도를 독립적으로 조절할 수 있다.

---

## 6. Output Surface — 사용자 향 산출물의 일관성

사용자가 직접 보는 markdown 산출물은 _내용 정확성_ 만 아니라 _읽기 호흡_ 까지 책임진다. 전담 부서 — **편집팀** (editorial-team, deep editor; concrete runtime mapping 은 adapter 문서가 소유).

- 모드 3종: A 옮기기 (영문 ↔ 국문) / B 다듬기 (언어 무관, 판교체 + 영문 어색한 표현 모두) / C 점검만
- 판교체 회피 — 한국어 산출물에서 영어 어휘를 한국어 어순에 그냥 박지 않는다. 도메인 영어와 정착 외래어만 영어로, 나머지는 한국어로. 매핑 표 — `adapters/claude/agents/editorial-team.md`
- 적용 범위 — 사용자가 직접 보는 _모든_ .md 산출물 (doc 한정 X). autopilot-code 의 final-report, audit 보고서, autopilot-refine 결과, pipeline_summary 등

**메인 에이전트 응답 자체** 의 메타 원칙은 별개 layer — runtime adapter bootstrap 이 single source (Claude Code: `adapters/claude/CLAUDE.md` §0~§3; §0 작업 라우팅: spec-first 파이프 + autopilot-* 호출 Pre-check·컨펌 · §1 응답 규율: 판교체 회피·출력 자제·동사 약속어 self-check · §2 pause flag 비자동·자율 진행 · §3 후속 단계 자동).

**Why**: 산출물 품질만 좋고 응답 / 가독성이 부자연스러우면 사용자 짜증이 누적. 편집팀이 _마지막 한 번_ 의 다듬기를 책임지고, runtime adapter bootstrap 의 응답 원칙이 _매 turn_ 의 메타 self-check.

---

## 7. Memory Layers

per-project 메모는 두 layer 분리.

| Layer | 위치 | 갱신 주체 | 용도 |
|---|---|---|---|
| **사용자 수동** | DB working tier — `/post-it` 가 `mem note`/`mem add` 로 author; 5 카테고리(conventions·external resources·open threads·decisions·next session hints)는 `type` taxonomy 로 유지 | `/post-it` (사용자 명시) | 사용자가 박아두려는 conventions / resources / threads / decisions / hints |
| **자동 학습** | DB working/durable — 외부 distiller 가 세션 delta 를 distill → `mem add` (Cluster C) | **외부 detached distiller** (메인 아님; turn-counter·SessionEnd hook 트리거 — §0.5 판단 외부화) | 재사용 절차·교정·컨벤션·교훈 자동 학습 |

- 내장 file 메모리(`<agent-home>/projects/*/memory/`)는 **직접 write hard-block**(`builtin-memory-guard.sh`); `mem sync` 는 다른 세션·하네스의 stray write 만 안전망 흡수. 기억 write 경로 = `mem`(DB) 단일.
- **삭제·prune·consolidate·merge·graduate(비가역) = 세션끝 deep curator** (Cluster E — no-tools + action JSON + script 실행, D-18; concrete runtime mapping 은 adapter 문서가 소유; 비가역삭제 3중방어). N턴 distiller = fast add-only worker. 메인 housekeeping 0. working TTL(21일) = deterministic backstop. (원칙: 추가[가역]=외부 자동 / 정리·삭제[비가역]=세션끝 deep curator.)
- 세션 주입 = `mem inject --hook` (DB working+durable+profile). 상세 SoT = runtime adapter bootstrap + MEMORY §7.

**Why**: 자동 메모리가 모든 feedback 을 누적하면 사용자가 _명시적으로 박아두고 싶은_ 정보 (코딩 컨벤션 · 외부 자원 link · 미해결 thread) 가 noise 에 묻혀 보인다. layer 분리 후 우선순위 명확.

---

## 8. Performance Preservation

효율 ≠ corner cutting. 줄어드는 것은 _orchestrator 의 중복 reasoning_ 이지 _verification 의 깊이_ 가 아니다.

- 유지: QA round 수 / agent prompt 풍성함 / verification step
- 줄임: orchestrator 가 agent 작업을 다시 읽고 요약하는 중복 / context 에 결과 본문이 누적되는 노이즈
- 결과 흐름: file 통해 (verdict 만 token)

---

## 9. Design ownership — design 이 리드, code 는 적용 (토큰 단일 계약)

디자인은 _코드에서 즉흥_ 으로 정하지 않는다. **design 이 시각을 먼저 잡고, code 는 적용만** 한다 — design 이 spec 역할(시각 청사진).

- **토큰은 _단일 계약_ — design 소유, code import.** 디자인 토큰(색·타이포·spacing·radius·shadow)은 _하나의 파일_ 에만 산다 = **앱이 실제로 import 하는 파일**(예: `app/globals.css` 의 `@theme`, 또는 `styles/tokens.css`). autopilot-design 이 그 파일을 _결정·편집_ 하고, autopilot-code 는 _참조·사용만_ 한다. **`designs/` 에 토큰 _사본_ 을 두지 않는다** (복제 = drift·화석의 근원). `designs/`(또는 `spec/design/`) 는 _refs·mockup·결정 근거·specimen_ 만 — spec/prd 가 "왜"를 담듯.
- **code 는 토큰을 재정의·즉흥변경하지 않는다.** 컴포넌트는 design 계약의 토큰을 _쓰기만_ (인라인 hex·px 흩뿌리기 금지). 토큰을 바꿔야 하면 design 으로 돌아간다.
- **빌트앱도 design-first** — mockup 이 아니라 **실제 돌아가는 앱 화면을 adapter visual harness 로 렌더** 해서 시각 결정. 그래야 롱테일("쓰다 보니 거슬림")도 design 이 리드한다.
- **경계 (substantial vs trivial)**: 방향·토큰·새 화면 레이아웃·구조 변경 = _substantial_ → **design-first** (실제 앱 렌더 → 결정 → 토큰 계약 갱신), code 적용. 한 요소 색 한 끗 같은 _trivial tweak_ 만 code 직접 허용.

**Why**: design 결정이 code 로 새면 (a) 토큰이 코드에 흩어져 시각 일관성이 무너지고 (b) `designs/` 가 화석이 되며 (c) 디자인 이력의 단일 출처가 사라진다. 토큰을 _design 소유 단일 계약_ 으로 두면 design 이 진짜 spec 역할을 하고, 복제·drift 가 원천 소멸한다. (2026-06-08 worklog-board: `designs/02_tokens/tokens.css`(7KB·06-01 화석) vs `app/globals.css`(50KB·06-08) 복제·drift 진단에서 도출.)

## 부록 — 도입 이력 (간략)

본 문서의 각 절이 어떤 incident 에서 결정됐는지 git log 기반 압축 reference. 상세 narrative 는 `git log --oneline` + 각 SKILL.md 의 `## Why` 절.

| 절 | 도입 incident · key commit |
|---|---|
| §1 3-Tier role | 초기 autopilot family 설계 — orchestrator 가 file 읽고 reasoning 하던 시기 → state machine 으로 분리 |
| §2 Autopilot 정신 | `782ccf6` autopilot-refine default 자동 apply / `2058325` user-refine opt-in only (2026-05-21 사용자 지적) |
| §3 Implicit discovery | `444616a` analyze-project cwd default / `d8f42cd` `--format-ref` 제거 / `215fc23` legacy cleanup |
| §4 T1/T2/T3 + Minor·Major | 초기 SKILL_OUTPUT_CONVENTION 도입 → 2026-05-21 CONVENTIONS.md §5 흡수 / `56708c4` minor vs major + dual-perspective audit |
| §5 Natural-integration | `bf8d565` rebuttal 표 본문 paste 거부 (2026-05-19 ICML camera-ready M11/M15 incident) + 2026-05-20 M8/M9 Paragraph Cohesion Pre-Check 4-step |
| §6 편집팀 + 응답 원칙 | `3f5a48c` translation-team 신설 → `cfb0e12` editorial-team rename + scope 확장 / `bf8d565` 응답 원칙 §3 / `2058325` §4 / `3f5a48c` §1 (판교체) |
| §7 Memory layers | `60f141a` `/notes` skill 신설 (현 `/post-it` — self-pruning lifecycle 로 진화) — 사용자 통제 layer 와 자동 메모리 분리 |
