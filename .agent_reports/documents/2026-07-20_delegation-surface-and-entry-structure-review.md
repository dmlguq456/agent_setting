# 위임 표면 경계 · 엔트리 스킬 구조 통합 검토

> 작성: 2026-07-20 main 세션. 사용자 요청 두 축을 통합 검토.
> ① "역할별로 부트스트랩이 최적화된 서브 세션 분사"(표면 A)와 "역할이 명시된 서브 에이전트 호출"(표면 B)의 경계가 애매하다.
> ② 거의 모든 작업이 autopilot-code로 수렴하는 느낌 — 엔트리 레벨 스킬 구조 자체를 함께 점검.
> 반영 사례: `.agent_reports/documents/2026-07-20_depth1-surface-terminology-fix.md` (depth-1 표면 용어 혼동 handoff).
>
> **결론 미리:** 세 concern(① A/B 경계 애매, ② autopilot-code 편중, ③ 단일-primary 강제의 경직 — code+design 동시 사용 불가)은 하나의 구조적 뿌리에서 나온다 — **하네스는 "한 capability 안의 스테이지"만 오케스트레이션하고 "capability들"을 동료로 오케스트레이션하지 않는다.** **(⚠ §0 정정 참조)** 처음엔 "표면 A ≈ autopilot-code, 나머지 native 전용"으로 봤으나 이는 capability **산문**만 본 오진이다 — 실제 실행 모델 `topologies.json`은 **모든** capability에 등록 staged topology를 이미 부여했고 design이 라이브로 그것을 돌린다. genuine gap으로 남는 건 (i) 산문 용어 혼동, (ii) 라우터가 primary 하나를 강요하는 합성 부재뿐이며, 편중은 대체로 산문상 착시 + 실제 워크로드(하네스=code)다.
>
> **사용자 결정(2026-07-20):** §6B fork는 **옵션 3 하이브리드** 선택. 추가로 §9(capability 합성)를 세 번째 축으로 정식 포함 — 하이브리드는 owner 안을, 합성은 owner들 사이를 다스리며 층이 달라 포개진다.

## 0. 정정 (2026-07-20 grounding 후) — 아래 진단의 핵심 수정

`capabilities/topologies.json`(실제 실행 모델) + 라이브 `jobs.log` 확인 결과, §5·§9·§11이 처음 주장한 **"표면 A(등록 depth-2 스테이지)는 code에만, 나머지 native 전용"은 capability `.md` 산문만 본 오진**이다:

- **모든 엔트리 capability가 이미 완전한 등록 depth-2 staged topology를 가진다** — apply(apply→verify→handback), code(plan→execute→test→report), design(refs→build→visual-review→handoff), draft(material-strategy→draft-production→review-refine→finalize), lab setup(scaffold→smoke→full-run), lab eval(eval-run→metrics→media→report→independent-verify→sync), note(scan→route-apply), refine(review→transaction), research(retrieval→synthesis→report→claim-verify), ship(release-setup→security/release-review), spec(research→review→prd-transaction). **code 전용이 아니다.**
- **하이브리드 표면 규칙(§6B-3)은 이미 구현되어 있다** — 각 노드 `transport`가 `["headless"(등록 A), "native-subagent"(B), "inline-fallback"]` 우선순위로 표면을 규정하고(대개 review/map 워커만 native 허용), SD-50 fallback chain이 실행한다. "옵션 3 하이브리드"는 신규 설계가 아니라 **현행 모델**이다.
- **라이브 증거:** grounding 시점 `jobs.log`에 `autopilot-design` depth-1 owner + depth-2 `refs`(completion_gate=design-refs, write_scope=shards/refs/**)가 실제 등록 dispatch 중.

**따라서 회귀 위험이 큰 "표면 A 일반화/재구축"은 불필요 — 이미 되어 있다.** 실제 남은 gap(좁음):

1. **[genuine·좁음·unowned] 산문 용어 혼동** — depth-1/native 혼동은 모델이 아니라 산문(OPERATIONS §5.10 불릿, 8개 capability 보일러플레이트, WORKFLOW)에 있다. 참조 handoff 타깃. 메모리 `quick-depth1-registered-dispatch`는 **산문에서 미해소**. → 이번 실작업.
2. **[genuine·사소·unowned] capability `.md`가 topology를 안 가리킴** — 그래서 산문만 읽으면 native-only로 오독. topology 포인터 1줄이면 "다 code 같다"는 착시 해소. → 이번 실작업(경량).
3. **[novel·부분해결·spec/조율]** 다중-capability 합성 route — topologies.json은 capability별 단일 route만 컴파일. "code+design 한 route"는 없음. **그러나 depth-0 main의 다중 depth-1 owner 동시 분사는 이미 됨(라이브 증명)** → "불가능을 가능케"가 아니라 route 객체화·Fleet 과정 뷰·§0.4 카드 개선 문제. 긴급도 낮음.
4. **[owned·hands-off]** Fleet 과정 뷰 — agent-fleet-dashboard PRD v10 **F-30 "과정 뷰 — topology/route 착륙" 이미 spec done**, scaffolding 이월. `hub-design` worktree 활발히 작업 중. → 소유 경계, 본 세션 미개입(메모리 `dont-implement-codex-owned-work`).

**재스코핑:** "상당 규모"의 대부분은 이미 구축·라이브. 회귀 최소화상 본 세션 실작업 = **(1)산문 용어 정밀화 + (2)topology 포인터**로 한정. (3)합성·(4)Fleet은 제안·조율이지 재구축 아님. 이하 §1–§11은 정정 이전 추론 흔적으로 보존하되 §5·§9·§11의 비대칭 주장은 본 §0이 대체한다.

---

## 1. 두 표면 정밀 정의와 올바른 중첩 관계

| 축 | 표면 A — 등록 dispatch 세션 | 표면 B — native subagent |
|---|---|---|
| 실체 | 별도 프로세스 `claude -p`/`codex exec`, checked adapter wrapper 경유 | 세션 내부 위임: Claude Agent tool, Codex `multi_agent`/`spawn_agent` |
| 부트스트랩 | `roles/worker-bootstrap.md` + `roles/worker-types/{owner,stage,review,support}.md` 1개 + 배정 capability/stage 계약 | `adapters/claude/agents/*.md`(role profile) + `roles/modes/<family>/<mode>.md` 페르소나 |
| 등록·가시성 | `jobs.log` 행, liveness 계약, Fleet 노출, governor 통과 | 레지스트리 없음, depth 없음, Fleet 비노출 |
| depth 회계 | quick=depth-1, standard+=depth-1 owner+depth-2 worker | **depth 밖** ("adds no depth" — CONVENTIONS route invariants) |
| 억제되는 것 | (해당 없음 — 이게 완전한 세션) | main-only 라이프사이클(response policy·memory·merge·push·cleanup·UI) 없음 |
| 근거 | `core/OPERATIONS.md:92,98`, `roles/worker-bootstrap.md` | `core/OPERATIONS.md:98,120`, `roles/README.md` |

**올바른 관계는 배타가 아니라 중첩이다.** 표면 B는 표면 A **안에서** 돈다. `core/WORKFLOW.md:290`가 명시: "For every durable stage at `standard+`, use an independent headless session … the named team roles run **inside** that session." 정상 형태:

```
depth-0 main
 └─ depth-1 owner        (등록 A, worker-type=owner)
     ├─ depth-2 code-execute (등록 A, worker-type=stage)
     │    └─ dev-team        (native B, depth 없음)   ← 실제 도메인 작업
     └─ depth-2 code-test    (등록 A, worker-type=review)
          └─ qa-team         (native B, depth 없음)
```

참조 사고는 이 중첩을 **붕괴**시킨 것이다: quick에서 depth-1 등록 세션(A)을 건너뛰고 native 팀(B)을 직접 부르며 그 B를 "depth-1 one-shot worker"라 명명 → A가 있어야 할 자리에 B를 놓고, 거기에 A의 depth 어휘를 붙였다.

## 2. 'role' 과부하 — 경계 애매성의 개념적 뿌리

사용자가 "경계선이 애매"라 느끼는 근본 이유: **두 표면을 가르는 말이 똑같이 "역할(role)"이지만, 서로 다른 축을 가리킨다.**

- **worker-type role** (`owner`/`stage`/`review`/`support`) = **구조적 위치**. dispatch 트리에서 내가 무엇인가(지휘자? 스테이지? 검증자? 보조?). 표면 A의 **부트스트랩을 최적화**한다. → 사용자 문장의 "역할에 따라 부트스트랩이 최적화되는 경우".
- **team/profile role** (`dev-team`/`qa-team`/`design-team`/…) = **도메인 전문성**. 무슨 분야 작업인가(백엔드? QA? 디자인?). 표면 B의 **명시된 서브에이전트를 지명**한다. → 사용자 문장의 "역할이 명시된 서브 에이전트".

이 둘은 **직교**한다(구조적 위치 × 도메인 전문성). 그런데 공용어 "role"이 그 직교성을 가린다. 그래서 "QA 리뷰가 필요하다"는 요구가 표면을 결정하지 못한다 — `review`형 등록 depth-2 worker(A)도, `qa-team` native subagent(B)도 둘 다 read-only QA를 한다. **표면을 결정하는 건 도메인이 아니라 intensity/분리가능성/등록필요성이다.** 이 사실이 어디에도 양성(positive) 규칙으로 서술되어 있지 않다.

## 3. 계약 문언상 blur 지점 (증거)

- **B1 — 지배적 문구가 애매한 채로 반복.** "`quick` is a depth-1 one-shot worker …"가 8개 capability 파일(`autopilot-{draft,spec,research,note,refine,design,lab,ship}.md`의 "Pipeline intensity follows …" 문단)에 **수기로 복제**되어 있는데(생성물 아님 — `tools/generate.py`가 이 문장을 emit하지 않고 GENERATED 마커는 line 6 Contract 표에만 적용), 어디에서도 "= 등록 dispatch 세션, native 팀이 아님"을 못박지 않는다. 가장 많이 반복되는 문구가 정확히 그 애매한 문구다.
- **B2 — quick 티어가 구조적 충돌점.** quick = "하나의 depth-1 등록 세션, depth-2 없음"이면서 동시에 quick = "small/fast" = 표면 B("Light team delegation … only for small, fast iterations", `OPERATIONS.md:120`)의 허용 조건과 정확히 겹친다. quick에서 두 서술이 동시에 발화 → 세션이 자연스레 더 가벼운 B로 손이 감. 참조 사고가 빠진 함정이 이 지점.
- **B3 — 인접 불릿이 B를 quick의 실현으로 읽히게 함.** `OPERATIONS.md:120-121`에서 "Light team delegation" 불릿과 "Quick one-shot" 불릿이 바로 이웃하고 둘을 가르는 문장이 없다.
- **B4 — 선택 축이 오도됨.** 두 표면은 도메인 능력에서 겹치므로(§2) "무슨 작업"은 표면을 못 고른다. 오직 intensity/분리가능성/등록필요성이 고른다. 그러나 이 선택 규칙이 양성 절차로 없고, `OPERATIONS.md:98`의 "Delegation surfaces are distinct"는 **방어적**으로만("한 표면의 제한을 다른 표면에 확장 말라") 서술된다. 규칙의 존재가 사고 사후에 붙은 부정형뿐이라, 사전 선택에 쓰이지 않는다.

## 4. 참조 handoff(용어 수정안) 평가

**맞다, 그러나 용어에 국한된다.** handoff는 B1/B3를 정확히 겨냥해 "등록 세션 ≠ native subagent, depth는 등록 표면 전용" 한정어와 CONVENTIONS route-invariant 상호 인용을 삽입한다. 인용 라인(`OPERATIONS.md:86,97,103-104,120-121` 등)은 2026-07-20 현재 유효함을 확인했다. "규범 신설 금지 · native 팀 위임 금지 아님 · dispatch 구현 불변"의 비목표도 옳다.

**빠진 것 (사용자가 지금 가리키는 더 깊은 뿌리):**
- **§2의 'role' 과부하를 다루지 않는다.** depth-어휘 혼동은 고치지만 role-어휘 혼동은 남는다.
- **양성 선택 규칙(B4)이 없다.** quick이 무엇이 *아닌지*(native 팀 아님)는 말하나, 일반적 "언제 A vs B" 결정 절차를 주지 않는다.
- **중복 자체를 줄이지 않는다.** 8개 복제 문단에 한정어를 덧붙이는 대신, 애매한 문구가 번지게 만든 그 중복을 단일 canonical 문장으로 접는 편이 근본적이다(생성-소유권 확인 완료: 수기 중복이므로 접기 안전).
- **concern-2(편중)와의 연결이 없다** — 아래 §5가 그 연결이며, handoff 범위 밖이었다.

→ **처분:** handoff의 용어 수정은 유효하니 폐기하지 않되, 본 검토의 더 넓은 처분(§6)에 **흡수·확장**한다.

## 5. concern-2 — autopilot-code 편중, 그리고 표면 비대칭이라는 공통 뿌리

**측정 결과 (capability 파일 본문의 등록-스테이지 신호 vs 팀-역할 신호):**

| 엔트리 capability | 등록 depth-2 스테이지 신호 | native 팀 역할 신호 |
|---|---|---|
| **autopilot-code** | **9** | 8 |
| autopilot-lab | 0† | 1 |
| autopilot-spec | 0 | 6 |
| autopilot-design | 0 | 1 |
| autopilot-draft | 0 | 1 |
| autopilot-refine | 0 | 1 |
| autopilot-research | 0 | 9 |
| autopilot-ship | 0 | 1 |

† lab의 등록 dispatch(eval 스테이지 워커)는 capability 본문이 아니라 `WORKFLOW.md:287`에만 서술됨.

**진단 A (구조적, 실재):** 구체적 등록 depth-2 스테이지 파이프라인(plan→execute→test→report)을 계약 본문에 가진 엔트리 capability는 **autopilot-code 하나뿐**이다. 나머지는 전부 native 팀 내부 라우팅(예: `autopilot-research.md:54-58` "Minimum role mapping"은 전부 research/material/QA/editorial/planning **role** — 등록 스테이지 없음). 즉 **표면 A ≈ autopilot-code, 표면 B ≈ 나머지 전부**.

**진단 B (라우팅, 부분적 실재):** `WORKFLOW.md:207-210`의 4개 트랙 중 3개([research·experiment], [library·CLI], [apps])가 autopilot-code를 임계 경로에 두고, [documents]만 우회한다. 게다가 **이 하네스 저장소 자체가 code 프로젝트** — core/capabilities/adapters/hooks/tools 편집은 문자 그대로 code/instruction 작업이라 autopilot-code로 라우팅된다(선택 효과). 사용자가 최근 하네스 개발을 해왔다면 "거의 code"는 부분적으로 실제 워크로드다.

**진단 C (느껴지는 효과):** A ≈ code이므로, "제대로 분사·스케줄·오케스트레이션되는" 일은 code 프레이밍으로 끌린다. 비-code capability는 얇은 native-팀 래퍼처럼 느껴진다.

**공통 뿌리:** `WORKFLOW.md:290`는 "모든 standard+ durable stage는 독립 headless 세션을 쓴다"고 **균일하게** 주장하지만, capability 파일들은 code 말고는 이를 실현하지 않는다 — **계약(균일) vs 실현(code 편중)의 간극**. 이 간극이 concern-1의 경계 애매성(A/B 규칙에 code 외 worked example이 없음)과 concern-2의 편중(A ≈ code)을 **동시에** 만든다.

## 6. 통합 처분안

### 6A. 명확한 수정 — fork와 무관하게 즉시 적용 가능 (권장: 승인 시 착수)

세 항목 모두 세 갈래 fork(§6B) 어느 결과에서도 참인 불변식이라 선행 적용 가능.

1. **용어 정밀화 (handoff 흡수).** "등록 dispatch 세션 ≠ native subagent, depth는 등록 표면 전용" 한정어를 `OPERATIONS.md:86,98,103-104,120-121`에 handoff 제안대로 삽입. `adapters/claude/CLAUDE.md`·`WORKFLOW.md:336`·해당 skill 미러도 동형 반영.
2. **중복 문단 단일화 (footprint 감소).** 8개 capability의 "Pipeline intensity follows …" 복제 문단을 `CONVENTIONS §1`의 단일 canonical 문장 참조로 축약하고, 그 canonical 문장이 "quick = 하나의 **등록** depth-1 세션(native 팀 아님)" 바인딩을 **한 번** 담게 한다. → 애매 문구를 8곳에서 고치는 대신 1곳으로 수렴시켜 재발 표면을 제거.
3. **'role' 축 명시 (개념 뿌리).** `CONVENTIONS` route-invariant + `roles/README.md`에 1–2문장: **worker-type role = 구조적 위치(표면 A 부트스트랩 최적화) vs team role = 도메인 전문성(표면 B 지명)** — 직교하며 공용어 "role"이 표면을 결정하지 않음을 명문화.

### 6B. 설계 분기 — 사용자 결정 필요 (표면 A를 비-code로 어떻게 처리할 것인가)

이것이 concern-2의 근본이며, 결과가 6A 이후의 capability-파일 수정 방향을 바꾼다.

- **옵션 1 — 편중 수용 + 라우팅 정리.** A는 code/lab 중심이 정당하다 인정, 비-code capability는 "native-team-first가 설계"라 명문화. 대신 (a) `WORKFLOW.md:290`의 균일 주장을 현실에 맞게 좁히고, (b) autopilot-code 트리거를 spec/lab/refine/audit 대비 더 좁게 경계지어 편중의 라우팅 성분을 줄인다. 비용 최소, 야망 최소.
- **옵션 2 — 표면 A 전면 일반화.** 비-code standard+ capability에도 실제 등록 depth-2 스테이지 그래프 부여(research: survey→verify→synth, draft: strategy→draft→verify→edit …). 오케스트레이션이 code 전용이 아니게 됨. 비용: capability별 topology·dispatch 계약 확장(큼).
- **옵션 3 — 하이브리드 (권장).** 두 표면을 **capability가 아니라 intensity/분리가능성 축**으로만 가르는 단일 규칙을 canonical하게 명문화(`OPERATIONS §5.10` "Delegation surfaces are distinct" **확장**, 신설 아님)하고 모든 capability가 상속: *standard+ separable stage = 등록 세션(A), 그 안 도메인 작업 = native 팀(B), quick = 단일 등록 세션, direct/light = inline 또는 native 팀.* 스테이지 그래프의 **구체 수준**은 capability마다 달라도(코드 4스테이지, 리서치 2~3) **표면 선택 규칙은 하나**. → 편중은 "code만 스테이지가 많다"는 자연스러운 차이로 환원되고, 경계 규칙은 capability 무관하게 단일화. `WORKFLOW.md:290`이 이미 균일하게 주장하던 바를 **양성 규칙 + 간극 봉합**으로 실현하므로 신설 규범이 가장 적다.

**권장 근거:** 옵션 3은 (i) B4의 부재한 양성 선택 규칙을 정확히 채우고, (ii) 기존 구조(§5.10, WORKFLOW:290)를 확장할 뿐 신설하지 않으며(무분별한 규범 신설 금지 원칙 부합), (iii) 무거운 파이프라인을 안 맞는 곳에 강제하지 않으면서도 비-code 작업이 진짜로 분리가능할 때 표면 A에 오를 경로를 준다.

## 7. 실행 시 주의 (승인 후)

- 다파일 행동-지침 변경 → **브랜치 + clean worktree**(`<repo>-wt/<slug>`). 가드류는 primary가 아닌 worktree에서 실행(primary 실행은 live 회전 유발 이력).
- 편집 후 `python3 tools/generate.py --check` + `sh tools/check-adaptation-boundary.sh` 녹색. 6A-2의 문단 단일화가 생성 파이프라인과 충돌하지 않는지(마커 스코프) 먼저 확인.
- 행동-지침 변경이므로 **drill 대상**: 관련 케이스 또는 `drill/run.sh --sample`. worktree 검증 시 `AGENT_HOME`·`DRILL_HOME`을 worktree로 명시(아니면 조용히 primary 검증).
- `skills/` 미러 byte-identical 강제 — canonical 수정 후 동기화 경로로 정렬.

## 8. 비목표

- native 팀 위임 **금지 아님** — 표면 B는 표면 A 안 도메인 작업으로 존치. 두 표면 제약 비확장(양방향)도 그대로.
- dispatch 구현(broker/launch-authority 등) 변경 없음 — 문서·계약 문언 작업. broker 부활 없음.
- 6A는 신설 규범이 아니라 기존 문언 정밀화·중복 제거·직교 축 명시.

## 9. 세 번째 축 — capability 합성(composability)과 spec 척추

**문제(concern-3):** 라우터(`WORKFLOW §0.2/§0.4/§5`)가 primary 하나를 강요해 "code와 design을 한번에" 같은 공동 실행이 표현되지 않는다. 나머지 capability는 종속 secondary이거나 primary 사이클 안 native로 흡수될 뿐 → 단일-primary 강제가 **편중의 원인**이자 **경직의 정체**. 최초 사용자 비전("스킬을 유기적으로 분사·스케줄·orchestration")은 capability-**오케스트레이션**인데 현 라우터는 capability-**선택**에 머문다.

**좋은 소식:** 실행 인프라는 이미 지원한다 — depth-0 main은 여러 depth-1 owner를 동시 분사 가능(depth 모델·cap Σ≤5·jobs.log·liveness 모두 capability 무관), 아티팩트 소유 disjoint(§0.2.6) + pipeline lock(§5.8)이 동시 실행을 안전화. 막힌 건 오직 라우팅/계획 계층(다중-capability 계획을 제안·표현).

**방향:** 라우터를 "단일 primary 선택" → "**capability 수준 소형 DAG(공동 primary 허용)**"로 진화. 보존 불변식: 확인은 **카드 하나**(메뉴 아님, main이 분해 결정, §0.4 ergonomic 유지), 순서 제약은 DAG 의존성으로 존치(무제한 병렬 아님), cap Σ≤5.

**spec 척추(사용자 지적 반영):** spec은 대칭 peer가 아니라 **상류 계약 허브** — 하류가 분기하는 전제조건(no code without spec)이자 drift 시 되점프하는 sync-back 타깃(§4, §5.8 잠금). 합성(공동 primary)은 **spec을 소비하는 하류 실행 capability(code∥design∥lab)에** 적용되고 spec이 분기·수렴점. DAG spine:

```
autopilot-spec (spec/ 척추)
  ├─▶ design-owner (spec/design/·tokens) ──tokens──▶ code-owner (plans/) ──▶ ship
  └───────────────────── drift sync-back ◀───────────┘
```

하이브리드(표면 규칙)는 owner **안**을, 합성은 owner**들 사이**를 다스려 층이 달라 포개진다.

## 10. 네 번째 축 — Fleet 관측 (앞 결정의 귀결)

**요구(사용자):** Fleet에서 워크플로우·위임·분사 과정이 잘 보여야 한다. **종착 목표는 분사·서브에이전트 처리 과정 시각화**(메모리).

**현재 Fleet가 못 보는 3가지:**
1. **capability DAG = 워크플로우 객체 자체** — route가 capability별 컴파일이라 다중-capability 워크플로우 객체가 없음. §9 합성 계층이 이 객체를 생성해야 렌더 가능.
2. **공동 primary 간 흐름·의존성** (design→code tokens 엣지 등).
3. **세션 안 native 팀 위임(B)** — 설계상 registry 밖이라 완전히 비가시. depth-2가 개발팀에 위임 중이어도 registered 스켈레톤만 보임. **핵심 gap이자 기존 인지 문제**(메모리: 등록 아니면 Fleet 비노출).

**화해책:** native를 depth/registry에 넣지 않되(불변식·broker 부활 금지 보존), **별도 activity 채널**로 within-session 위임을 emit → 흐름은 가시화, native는 여전히 무-depth·비-registered. registered/native 경계 유지 + 관측만 획득.

**순서:** Fleet 가시성은 §9(합성)+표면규칙의 귀결 — DAG 객체가 생겨야 워크플로우 렌더, A/B가 명확해야 위임 채널 정의. 현재 `render.py` 대비 정확한 델타는 render 현행을 직접 열어 확정(메모리: 시각 작업은 render 현행+기각 이력 우선, 흰 바·reverse 배지 재도입 금지).

## 11. 통합 모델 (4축)

| 계층 | 범위 | 상태 |
|---|---|---|
| 합성(§9) | main이 capability DAG 소유, spec 척추, 하류 공동 primary | 신규(라우터 진화) |
| 표면 규칙(하이브리드, §6B-3) | 각 owner 안, intensity/분리가능성이 A/B 선택 | 확장(§5.10) |
| 용어·역할축(§6A) | 등록≠native, depth=등록전용, worker-type⊥team | 정밀화 |
| 관측(§10) | registered 트리 + DAG 워크플로우 + native 위임 채널 | 귀결(앞 축 의존) |

불변: 확인 카드 하나, cap Σ≤5, 아티팩트 소유 disjoint+lock, native≠registered 경계, broker 부활 없음.

## 12. 실행 기록 (2026-07-20)

**실행함 — 산문 용어 정밀화 (genuine·unowned·회귀안전):** worktree `agent_setting-wt/depth1-surface-terminology`, 커밋 `7094c92b`. `quick depth-1 one-shot = 등록 dispatch 세션(native subagent 아님), depth는 등록 세션만 계수` 바인딩을 8줄로 삽입 — canonical(CONVENTIONS §1:37) + 운영(OPERATIONS §5.10: depth-model 리스트 :86, Light-team-delegation :120, Quick-one-shot :121) + 라우팅(WORKFLOW §5:290) + 어댑터 부트스트랩 3개(claude/CLAUDE.md, codex/AGENTS.md, opencode/AGENTS.md; *_setting은 심링크로 자동 반영). 모델·dispatch·생성물 변경 없음.

- **검증:** `generate.py --check`(manifest·hub·13 projection 정합) + `check-adaptation-boundary.sh` green; **core-first 게이트 훅이 정상 발화**(core 수정 후 adapter 편집 차단→재독 후 통과)해 크로스하네스 순서 준수 실증. 무거운 행동 drill(`loops/drill/run.sh`, 실제 depth-1/2 세션 분사)은 순수 산문 변경에 비례성 어긋나고 라이브 design job과 `.dispatch` 충돌 위험이라 의도적 생략 — 프로즈 변경엔 위 3중 결정론 검증이 비례적·충분.
- **메모리 해소:** `quick-depth1-registered-dispatch`의 산문 gap 닫힘. 신규 navigation 메모리 `topologies-json-is-execution-truth` 추가(오진 재발 방지).
- **push/main 병합:** 사용자 신호 대기(§5.10.3 self-merge 금지). 브랜치는 롤백 포인트로 보존.

**미실행 — 제안·조율 (owned/spec'd, 재구축 아님):**
- (3) 다중-capability 합성 route: `capability-route.py`가 단일 capability만 컴파일(`compile_route(capability)`, scalar `"capability"`, intra-recipe `depends_on`만). 확장점 = `topologies.json` recipe 스키마 + `capability_topology.py` 검증 + `capability-route.py` 컴파일러 + consumers(`dispatch-node.py`, `stage-dispatch-fallback.py`). governed by **stage-dispatch PRD**(1022줄, v19/v20, spec-significant). 단 depth-0 main의 다중 depth-1 owner 동시 분사는 이미 되므로(라이브 증명) 긴급도 낮음 — route 객체화·Fleet 과정 뷰·§0.4 카드 개선의 문제.
- (4) Fleet cross-capability workflow DAG + subagent 의존구조: native 위임은 **F-29로 이미 가시**(`render.py:1768` `⚡` strip). 미완 = 단일 route 카드 간 엣지·cross-capability 컨테이너. governed by **agent-fleet-dashboard PRD F-30**("과정 뷰 — topology/route 착륙", spec done, scaffolding 이월). 확장점 `route.py:250/342`, `render.py:1864/1977/2149`. `hub-design` worktree 활발 작업 중 → **소유자와 조율**, 중복·재구축 금지.
