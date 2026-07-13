# Skill-Design Audit — 28스킬 per-skill verdict (T2 상세)

> mode: code · date: 2026-07-13 · rubric SoT: `.agent_reports/research/skill-design-principles/` (06_implementation §3 8-Step)
> 종합·매트릭스·Step7 우선순위 = T1 [`skill_design_audit.md`](skill_design_audit.md). 본 파일은 스킬별 4축 verdict 근거(file:line)만.
> 판정 = in-session 연구팀 5개 병렬 배치(그룹 A~E) + 메인 spot-verify. 범례: 🟢 정합 / 🟡 minor gap / 🔴 material gap.

## 그룹 A — entry routers (7)

### analyze-project
- **Step0 Predictability**: 🟢 — mode auto-detect 표(:43-54) + Output Directories(:56-64) + Phase 위임이 same-process 재현 강제.
- **① Invocation**: 🟡 — model-invoked 적절(user·model 양쪽 도달 entry). description(:3) "Use when" 없고 본문 trigger 절도 없어 auto-activation이 description 한 줄+hook에만 의존. entry router라 gap 비중 높음.
- **② Info Hierarchy**: 🟢 — 3-rung 깔끔, 포인터가 파일명+시점 명시(:78-81), variance-bug 없음.
- **③ Steering**: 🟡 — 표면 completion criterion 없이 Phase 5 QA로 위임(:72). leading/negation 경미.
- **④ Pruning**: 🟡 — Required Reads(:76-81)와 Reference Map(:83-88)이 동일 4개 reference 이중 서술; `<artifact-root>` 스니펫(:21) cross-skill 중복.
- **flags**: duplication
- **top gap**: description에 "Use when…" 트리거 추가 (`skills/analyze-project/SKILL.md:3`)

### analyze-user
- **Step0 Predictability**: 🟢 — Core Invariants(:53-59: QA adversarial 고정 / DB 출력 / two-writer / read-back "불일치→큰 소리로 fail" / 하드코딩 path 금지)가 강하게 못박음.
- **① Invocation**: 🟡 — cross-project라 auto-activation 의존 낮음. Default Invocation Rule+Trigger(:24-31) 본문 보완하나 description(:3) "Use when" 없음.
- **② Info Hierarchy**: 🟢 — 3-rung + 강한 명명 포인터(:90-92), 1-depth.
- **③ Steering**: 🟡 — read-back이 checkable completion 역할 우수. "하드코딩 path 금지"(:59)·"raw query 금지"(:57)·"파일 Write X"(:56) don't-X negation 다수.
- **④ Pruning**: 🟡 — Required Reads(:88-92) vs Reference Map(:94-98) 동일 3개 재서술; Override(:39-45) 장황.
- **flags**: duplication, negation
- **top gap**: Required Reads/Reference Map reference 서술 중복 통합 (`skills/analyze-user/SKILL.md:94`)

### audit
- **Step0 Predictability**: 🟢 — Stage A→E + Dual-perspective(P1/P2, :33-47) + read-only invariant(:88-95).
- **① Invocation**: 🟡 — Cadence 표(:49-57)·When NOT(:96-101) 보완하나 description(:3) "Use when" 없음.
- **② Info Hierarchy**: 🟢 — Process 표(:79-86)가 Stage↔reference 1:1, 강한 포인터, 1-depth.
- **③ Steering**: 🟢 — completion "read-only 보고서 + Stage E dispatch"로 checkable. "never modify"(:90)는 정당한 hard safety. 수정은 별도 skill dispatch = 실제 context 경계.
- **④ Pruning**: 🟡 — Required Reads(:103-108) vs Reference Map(:110-115) 동일 4개 재서술; `<artifact-root>`(:17) 중복.
- **flags**: duplication
- **top gap**: description에 "Use when…" 트리거 추가 (`skills/audit/SKILL.md:3`)

### autopilot-code
- **Step0 Predictability**: 🟢 — Quick Contract(:16-22) + Critical Gates(6개 checkable, :61-67) + Stage Graph(:44-52), depth-2 분사(:52)로 스테이지 경계 결정론화.
- **① Invocation**: 🟡 — CLAUDE.md §0 코드 라우팅의 高-traffic entry인데 description(:3) "Use when" 없고 trigger가 reference(:71)로 밀림 — auto-routing 의존 최고라 상대적 material, hook 보완으로 🟡.
- **② Info Hierarchy**: 🟢 — 라우터/계약만, 세부는 5개 reference 위임, 포인터 강함(:24-30), 1-depth.
- **③ Steering**: 🟢 — Critical Gates exhaustive+checkable. "무조건 병렬화하지 않는다"(:21)·"중단한다"(:20) 경미 negation.
- **④ Pruning**: 🟡 — Required Reads(:24-30) vs Reference Map(:69-75) 동일 5개 재서술.
- **flags**: duplication
- **top gap**: description에 "Use when…" 트리거 추가(코드 auto-routing 의존 최고) (`skills/autopilot-code/SKILL.md:3`)

### autopilot-draft
- **Step0 Predictability**: 🟢 — First Principle(:16-24 산출물=cheatsheet/mutation plan) invariant + pipeline 표(:87-98) + Safety Essentials(:104-110). "축소·정리 시에도 표면 유지"(:24) sediment 방지까지.
- **① Invocation**: 🟡 — Default Invocation Rule + mode별 Trigger(:34-48) 강한 본문 보완. description(:3) "Use when" 부재.
- **② Info Hierarchy**: 🟢 — 3-rung + pipeline 표 stage↔reference(:87-98), conventions/ single source(:100), 1-depth.
- **③ Steering**: 🟢 — First Principle 강한 leading-concept. reviewer point 미응답=critical error(:108) checkable. "날조하지 않는다"(:106) hard safety.
- **④ Pruning**: 🟡 — Required Reads(:112-117) vs Reference Map(:119-124) 동일 4개 재서술; `<artifact-root>`(:68) 중복.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 중복 통합(본문 trigger 이미 충분) (`skills/autopilot-draft/SKILL.md:119`)

### autopilot-research
- **Step0 Predictability**: 🟢 — stage 계약(search→analyze→report) + Re-Entry/Resume 분기(:82-86) + concrete Safety Rules(rate limit·MERGE 단조증가·context budget :103-110).
- **① Invocation**: 🟡 — Default Invocation Rule + mode별 Trigger(:26-37) 본문 보완. description(:3) "Use when" 부재.
- **② Info Hierarchy**: 🟢 — Pipeline 표 stage↔reference(:92-98), raw metadata `_internal/` 격리(:16)로 sprawl 억제, 1-depth.
- **③ Steering**: 🟢 — Safety Rules concrete·checkable(수치·pkill chromium :111). "Do NOT fabricate citations"(:103) hard safety.
- **④ Pruning**: 🟡 — Required Reads(:112-117) vs Reference Map(:119-124) 동일 4개 재서술; `<artifact-root>`(:18) 중복.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 중복 통합 (`skills/autopilot-research/SKILL.md:119`)

### autopilot-spec
- **Step0 Predictability**: 🟢 — "update mode = 유일 경로"(:85) + prd.md single-source + Intake 게이트(:15) + 버전 snapshot(:86) + 동시성 lock(:88).
- **① Invocation**: 🟡 — Default Invocation Rule + mode별 Trigger 표(:53-62) 본문 보완. description(:3) "Use when" 부재.
- **② Info Hierarchy**: 🟢 — 흐름 다이어그램(:35-45), 게이트 개요+강한 포인터(:83-89), 1-depth.
- **③ Steering**: 🟢 — update mode canonical/Intake gate/Forbidden Zones checkable invariant. 구현은 autopilot-code로 경계 분리(:31).
- **④ Pruning**: 🟡 — Required Reads(:91-96) vs Reference Map(:98-103) 동일 4개 재서술; `<artifact-root>`(:13) 중복.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 중복 통합 (`skills/autopilot-spec/SKILL.md:98`)

## 그룹 B — autopilot pipe / misc entries (6)

### autopilot-apply
- **Step0**: 🟢 — 4-stage(Preflight→Apply→Verify→Handback) + apply_state.yaml `--from` + 6 hard invariants(:164-169).
- **① Invocation**: 🟡 — model-invoked 적절(실 source 편집 ceremony entry). Korean trigger 예시(:31-34)만, "Use when" 없음.
- **② Info Hierarchy**: 🟡 — 190줄 inline·no references/, 대체로 정당(self-contained git+compile). `$BUILD_OUT` 근거 문단(:78)이 reference성.
- **③ Steering**: 🟢 — completion checkable("새 에러 0→통과" :110-113); git merge는 user hand-off 경계(:116-118)로 지연, premature 없음. "빈칸>잘못 채우기" 긍정 프레임.
- **④ Pruning**: 🟡 — 라우팅 제외 목록 3회 재서술(Scope NOT-for :54-57 / Override :43-46 / When NOT :186-190).
- **flags**: duplication, sprawl
- **top gap**: 3중 제외 목록을 한 authority로 통합 (`skills/autopilot-apply/SKILL.md:186`)

### autopilot-design 🔴 (유일 double-🔴)
- **Step0**: 🟢 — Phase 0-5 + per-phase CONFIRM Gate + design_state.yaml + stage-worker mapping(:127-138).
- **① Invocation**: 🟡 — model-invoked 적절(entry + autopilot-spec Phase 2 auto-delegate). Korean trigger(:20-27)만, "Use when" 없음.
- **② Info Hierarchy**: 🔴 — 315줄(28개 중 최장)·no references/, 6개 phase를 3중 문서화: Pipeline Overview(:114-123) → Stage-worker 표(:127-138) → Pipeline Execution 전개(:183-271). 하네스 표(:149-162)·시각검증 loop(:164-181, 스스로 `_design_rules.md` 소유라면서 요약 inline)·paper-figure 정책(:140-147)이 reference급 bulk.
- **③ Steering**: 🟢 — per-phase CONFIRM 4-branch(:176-181) 실제 user 경계라 premature 아님, Return format checkable(:301-308).
- **④ Pruning**: 🔴 — 3중 phase 서술 material duplication + 시각검증 loop이 `_design_rules.md` 소유 내용 요약(SoT 긴장, :164-171).
- **flags**: sprawl, duplication
- **top gap**: Phase 0-5 Execution 본문 + 하네스 표 + 시각검증 loop을 references/로 추출(phase 목록은 mapping 표로 이미 완결) (`skills/autopilot-design/SKILL.md:187`)

### autopilot-lab
- **Step0**: 🟢 — setup⏳→[user trains]→eval✅ + `_RUNLOG` + canonical worktree+branch(:61-81) + 4원칙 + Forbidden Zones + `--from` resume.
- **① Invocation**: 🟡 — model-invoked 적절(setup/eval + `--parent` 계보). Trigger 예시(:110-120)만.
- **② Info Hierarchy**: 🟢 — references/ 1-depth, Required Reads 강한 의무 포인터("매 호출 시 먼저 로드" :14-20). variance-bug 없음.
- **③ Steering**: 🟢 — CONFIRM + REPORT.md self-contained; leading words(worktree/fine-tune/baseline/계보); graduation은 autopilot-code 경계(:58,:78).
- **④ Pruning**: 🟡 — Required Reads(:14-20) vs Reference Map(:196-201) 동일 5개 재서술.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 통합 (`skills/autopilot-lab/SKILL.md:196`)

### autopilot-note
- **Step0**: 🟢 — Routing Rules 5-갈래 표(:43-53) + Idempotency(date+source hash) + Constraints(L1 카드 불변, 원본 read-only :59-69).
- **① Invocation**: 🟡 — ceremony-small immediate-invoke라 trigger 비중 낮으나 Korean 발화(:20) auto-activate, "Use when" 없음.
- **② Info Hierarchy**: 🟢 — 그룹 최청결: 85줄 라우터가 6개 reference 강한 포인터 위임(:71-77). exemplary 3-rung, no sprawl.
- **③ Steering**: 🟢 — routing rule별 자동/자동(제안)/triage 라벨 checkable; Constraints exhaustive invariant.
- **④ Pruning**: 🟡 — Required Reads(:71-77) vs Reference Map(:79-85) 동일 6개 near-identical.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 단일 index화 (`skills/autopilot-note/SKILL.md:79`)

### autopilot-refine
- **Step0**: 🟢 — Major/Minor 3-criteria gate + Mode Forms + intensity rigor 표 + Stage A→E version-snapshot invariant(:30-47,:105-115).
- **① Invocation**: 🟡 — model-invoked 적절(doc-track post-creation), major-level auto-invoke rule(:24-28). "Use when" 없음.
- **② Info Hierarchy**: 🟢 — references/ + 강한 명명 포인터, rigor tier는 CONVENTIONS §1.1을 SoT로 지시(재서술 X, :68). 3-rung clean.
- **③ Steering**: 🟢 — Mode Forms + rigor 표 checkable; STRUCT-halt escape; post-apply review는 scope-out 경계(:78)로 premature 회피.
- **④ Pruning**: 🟡 — Required Reads(:117-121) vs Reference Map(:123-127) 동일 3개 재서술.
- **flags**: duplication
- **top gap**: Required Reads/Reference Map 통합 (`skills/autopilot-refine/SKILL.md:123`)

### autopilot-ship
- **Step0**: 🟢 — Context Auto-Detection + Step 1-5(1.5 pre-deploy gate) + single-file ship.md changelog append + Forbidden Zones + CONFIRM(:56-71,:161-169).
- **① Invocation**: 🟡 — model-invoked 적절(app-track deploy entry). Korean trigger(:39-44)만.
- **② Info Hierarchy**: 🟡 — 241줄 inline·no references/, 대체로 정당(self-contained checklist, ship.md 템플릿=산출물). Examples 3개(:207-238)가 reference급 bulk, 발화→자리 표 2곳 inline. variance-bug 없음.
- **③ Steering**: 🟢 — completion checkable(Return+CONFIRM); Forbidden Zones(:182-189) 강한 negation이나 배포 safety guardrail; 실배포는 user(:133) 경계라 premature 없음.
- **④ Pruning**: 🟡 — 발화→자리 표 재서술(:64-71,:93-95,:165-169), "배포 명령 사용자 직접" ~3회(:51,:133,:184), Examples sprawl.
- **flags**: duplication, sprawl
- **top gap**: 발화→자리 표·"deploy=user" 3중 서술 dedupe (`skills/autopilot-ship/SKILL.md:182`)

## 그룹 C — code-* pipeline sub-skills (5)

> 공통: 순수 pipeline sub-skill(autopilot-code stage-dispatch·`/code-*` slash 전용). resident model-invoked description이 도달성 gain 없이 context 지불 → 연구팀 C는 Invocation을 🔴(user-invoked 권장)로 판정. 종합에서는 축 severity를 그룹 D/E(동일 근거로 🟡)와 harmonize하되, 이 dissent와 aggregate 영향을 Step7 상위로 승격(§ T1 참조). Plan Resolution 블록은 헤더가 "canonical — keep in sync with code-execute/code-test/code-report/code-refine/autopilot-code" — 5-way 물리 복제 = SoT 위반 자백.

### code-execute
- **Step0**: 🟢 — write class(:12) + safety-checkpoint `$SAFETY_COMMIT` + QA-scaling→rollback ladder + 체크리스트 `[x]/[FAIL]/[SKIP-DEP]` exhaustive.
- **① Invocation**: 🟡 (연구팀 dissent 🔴) — 선언상 sub-skill(:3), stage-dispatch entry(:12). resident description = context 낭비. → user-invoked 권장(파이프 slash/explicit 경로 생존 확인 후).
- **② Info Hierarchy**: 🟡 — 142줄(그룹 max) inline 정당(복잡 orchestration)이나 QA-Scaling 표(:79-95)가 Change-Log/Phase-Review(:96-122) 부분 재서술.
- **③ Steering**: 🟡 — completion exhaustive("모든 step [x]/[FAIL]까지" :77); leading words(safety checkpoint/restore point/rollback); negation("Do NOT change code outside scope" :127, "Do NOT proceed" :34) flip 여지.
- **④ Pruning**: 🟡 — Plan Resolution 자백 중복(:14) + Language Rule(:23-24) 재서술.
- **flags**: duplication, negation
- **top gap**: Plan Resolution을 autopilot-code SoT 포인터로 대체(+invocation user-invoked 검토) (`skills/code-execute/SKILL.md:14`)

### code-plan
- **Step0**: 🟢 — plan status별 Pre-Check 분기(:19-24) + 위임 계약 + intensity plan-check tier + mirror rule.
- **① Invocation**: 🟡 (dissent 🔴) — sub-skill(:3), stage entry(:14). user-invoked 권장.
- **② Info Hierarchy**: 🟢 — 89줄 lean, 위임/mirror 프롬프트 inline은 subagent 전달용, rigor tier가 CONVENTIONS §1.1 SoT 인용(:47). Plan Resolution 중복 없음(Pre-Check 사용).
- **③ Steering**: 🟡 — bounded completion("at most one correction pass" :55, "Do not loop merely…" :62) 우수하나 negation(:22,:41).
- **④ Pruning**: 🟢 — rigor 표는 SoT 위 정당 특화; Language Rule(:16-17) residue만.
- **flags**: negation
- **top gap**: user-invoked 재분류 (`skills/code-plan/SKILL.md:3`)

### code-refine
- **Step0**: 🟢 — dual-file(plan↔plan_ko) resolution + memo-format taxonomy(:35-41) + in-place update+sync+memo 제거 + intensity review budget.
- **① Invocation**: 🟡 (dissent 🔴) — sub-skill(:3), "not an automatic stage in direct/quick"(:48) = caller 전용. user-invoked 권장.
- **② Info Hierarchy**: 🟢 — 61줄 최소, memo taxonomy inline=core spec, rigor 표 §1.1 포인터.
- **③ Steering**: 🟡 — completion 명확(memo 반영+제거+sync+return); negation "Do NOT treat…prose as a memo"(:41).
- **④ Pruning**: 🟡 — Plan Resolution 자백 중복(:12) + Language Rule(:23-24).
- **flags**: duplication, negation
- **top gap**: user-invoked 재분류 + Plan Resolution 포인터화 (`skills/code-refine/SKILL.md:12`)

### code-report
- **Step0**: 🟢 — 고정 report 구조(:81-94) + `git diff --stat` doc-edit 확인(:75) + line-number 재검(:74)의 checkable determinism guard.
- **① Invocation**: 🟡 (dissent 🔴) — sub-skill(:3), stage entry(:12). user-invoked 권장.
- **② Info Hierarchy**: 🟡 — 145줄(그룹 max); 생성 프롬프트(:42-104) inline은 writer subagent 전달용이나 doc-topic 매핑(:63-73)이 sprawl 쪽.
- **③ Steering**: 🟡 — completion exhaustive(reconciliation over numbers/line/follow-up/deviation :111-116); "reconcile" leading word; negation stack(:77,:97,:103).
- **④ Pruning**: 🟡 — Plan Resolution 자백 중복(:14); Model&QA rationale(:26-37)은 정당(왜 QA 없나 설명); Language Rule(:23-24).
- **flags**: duplication, negation
- **top gap**: user-invoked 재분류 + Plan Resolution 포인터화 (`skills/code-report/SKILL.md:14`)

### code-test
- **Step0**: 🟢 — graduated Level 1→5 "in order, first-failure stop"(:35,42,49) + CRITICAL test-log 형식(:53-65) + read-only invariant 2회(:78,83) + verdict-relay.
- **① Invocation**: 🟡 (dissent 🔴) — sub-skill(:3), stage entry(:12). `/code-test` slash 경로는 disable-model-invocation에서도 유지되나, autopilot-code conductor의 depth-2 **Skill-tool dispatch** 경로가 disable flag 하에 생존하는지는 P1 검증 대상 — flip 전 확인 필요.
- **② Info Hierarchy**: 🟢 — 93줄 lean, arg-branch 프롬프트+test-log=core inline spec.
- **③ Steering**: 🟡 — completion checkable+exhaustive(level-ordered, first-fail stop); read-only 경계; negation(:78,:83) load-bearing safety; commit/fix는 caller 위임(:82-83)라 premature 없음.
- **④ Pruning**: 🟡 — Plan Resolution 자백 중복(:14) + Language Rule(:25-26).
- **flags**: duplication, negation
- **top gap**: user-invoked 재분류 + Plan Resolution 포인터화 (`skills/code-test/SKILL.md:14`)

## 그룹 D — design-* pipeline sub-skills (6)

> 공통: autopilot-design가 부르는 순수 sub-skill. Invocation 동일 근거로 🟡(user-invoked 권장). 시각 self-verify loop(`preview→screenshot→view_image` + scope 표)이 design-components/design-review/design-tokens 동형 3중 복제(design-tokens는 specimen-verify 맥락 흡수 변형) = 최고가치 dedup.

### design-components
- **Step0**: 🟢 — Pre-Check + 5 stage + completion write(`components: done`+`verified_visually: true` :147); render-before-done(:116).
- **① Invocation**: 🟡 — pure sub, resident description 낭비. user-invoked 권장.
- **② Info Hierarchy**: 🟡 — maker.md/`_design_rules.md`(:118)·web-bundle(:139) 포인터 강하나 시각검증 flow 재inline(:120, 3중 복제). scope-dispatch 프롬프트(:36-103) bulky. variance-bug 없음.
- **③ Steering**: 🟡 — completion checkable(:147); leading("scaffold 매칭","렌더해서 본 것으로만 완료" :116); negation("바퀴 재발명 금지" :30, "마크다운만으로 끝내지 않음" :70).
- **④ Pruning**: 🟡 — 시각검증 loop 3중 복제 + scope-dispatch inline sprawl.
- **flags**: duplication, sprawl, negation
- **top gap**: 3중 시각 self-verify loop을 공유 ref로 hoist (`skills/design-components/SKILL.md:120`)

### design-handoff
- **Step0**: 🟢 — Pre-Check가 `review: done` gate·`failed` 거부(:21-22); 4 stage + `handoff: done`(:160).
- **① Invocation**: 🟡 — pure sub(autopilot-spec/design 호출). user-invoked 권장.
- **② Info Hierarchy**: 🟡 — ~94줄 inline handoff.md 템플릿(:50-144)은 산출물이라 정당하나 大. 포인터 존재(02_tokens/tokens.md :94, web-bundle :76).
- **③ Steering**: 🟢 — completion checkable; caller-branch(:146-156) concrete. `#F97316`/`TaskRow`는 템플릿 placeholder(sediment 아님).
- **④ Pruning**: 🟡 — 핵심 토큰(Brand/Inter/spacing :89-94)+token-version(:87)을 design-tokens SoT(DESIGN_PRINCIPLES §9) 대신 inline 재서술.
- **flags**: duplication, sprawl
- **top gap**: inline "핵심 토큰"을 canonical token 파일 포인터로 대체 (`skills/design-handoff/SKILL.md:89`)

### design-init
- **Step0**: 🟢 — idempotent Pre-Check(기존 design_state.yaml→stop :17-19) + self-provision + 전체 yaml schema completion 계약(:82-108).
- **① Invocation**: 🟡 — pipeline entry sub, parent-invoked. user-invoked 권장.
- **② Info Hierarchy**: 🟢 — bootstrap bash probe+yaml schema inline 정당, spec §0.5 포인터(:29). scope 표(:51-58) relevant.
- **③ Steering**: 🟢 — 긍정 프레임("환경 부재로 중단하지 않는다" :29); checkable(smoke 7/7 :47, `visual_verify_ready` :96). negation·rush 없음.
- **④ Pruning**: 🟢 — lean, 전 줄이 bootstrap/inventory에 관여.
- **flags**: none
- **top gap**: user-invoked 재분류(resident description 비용 제거) (`skills/design-init/SKILL.md:3`)

### design-refs
- **Step0**: 🟢 — Design Resolution fallback chain(:15-19) + context-first gate("컨텍스트 없이 시작하지 않는다" :23) + 6 stage + `refs: done`(:105).
- **① Invocation**: 🟡 — pure sub. user-invoked 권장.
- **② Info Hierarchy**: 🟢 — brief.md 템플릿(:67-101)=산출물, spec §1.3(:23)·mem profile(:61) 포인터. lean.
- **③ Steering**: 🟢 — 강한 leading("빈칸이 잘못 채운 brief보다 낫다" :23); 위임 프롬프트 checkable.
- **④ Pruning**: 🟢 — no-op/sediment 없음.
- **flags**: none
- **top gap**: user-invoked 재분류 (`skills/design-refs/SKILL.md:3`)

### design-review
- **Step0**: 🟢 — two-gate(verifier→critic :29) + round caps(:45-48) + deterministic completion mapping(:106-109). 그룹 최강 same-process.
- **① Invocation**: 🟡 — pure sub. user-invoked 권장.
- **② Info Hierarchy**: 🟡 — verifier schema inline 정당, OCD BENCHMARKS 포인터(:48). render flow+scope 표(:63-70)가 components/tokens와 중복.
- **③ Steering**: 🟢 — completion fully checkable+exhaustive(verdict/breakage/vision_passrate); round caps+"강제 done coerce 금지"(:48)가 premature 능동 방지.
- **④ Pruning**: 🟡 — render-flow 중복.
- **flags**: duplication
- **top gap**: 공유 render ref 포인터로 scope render 표 대체 (`skills/design-review/SKILL.md:63`)

### design-tokens
- **Step0**: 🟢 — refs-done gate(:22) + single-token-contract(:25) + specimen-verify-before-consume(:121) + version snapshot + drift-anchor completion(:184-186).
- **① Invocation**: 🟡 — pure sub. user-invoked 권장.
- **② Info Hierarchy**: 🟡 — 그룹 최장(212)로 ~70줄 worked tokens.md 예시(:41-110)+CSS/TS 템플릿(:129-167) sprawl → references/ 포인터行. SoT 포인터 존재(§9 :25, §4 :180).
- **③ Steering**: 🟢 — hard consume gate(:121) checkable; minor/major snapshot(:180) exhaustive. negation/rush 없음.
- **④ Pruning**: 🟡 — inline exemplar sprawl(:41-110); render-flow 중복; token-contract 부분 재서술.
- **flags**: sprawl, duplication
- **top gap**: 70줄 worked tokens.md exemplar를 references/ asset(강한 포인터)로 이동, schema skeleton만 inline (`skills/design-tokens/SKILL.md:41`)

## 그룹 E — draft + misc (4)

### draft-refine
- **Step0**: 🟢 — per-memo ref-grounding 4-step(:82-93) + memo-format taxonomy(:72-78) + changelog invariant("`---` on line 1" :112-114) + QA-scaling+verdict loop max-2(:217-275).
- **① Invocation**: 🟡 — pure sub(autopilot-refine 호출). resident description 낭비. user-invoked 검토.
- **② Info Hierarchy**: 🟡 — 2nd-longest(278)·no references/. 위임 프롬프트 거대 inline(:60-207) + changelog before/after 예시(:103-197 ~95줄) 둘 다 추출가능 → sprawl(sibling draft-strategy는 delegate-prompt를 references/로 밀어냄).
- **③ Steering**: 🟡 — completion checkable+exhaustive(verdict branch + "🔴 2R 후 → `## 미해결 이슈`" :275), parent 경계 반환; negation(:78,:91,:258).
- **④ Pruning**: 🟡 — draft-strategy 포인터(:202,:204) 좋으나 gating question inline 재서술(:205); QA-scaling 표+"Why fast fact-checker"(:217-225)가 draft-strategy `references/qa-review.md` 위임 construct와 cross-skill 중복.
- **flags**: sprawl, negation, duplication
- **top gap**: inline delegate 프롬프트(:60-207)+changelog 예시(:103-197)를 references/로 추출 (`skills/draft-refine/SKILL.md:60`)

### draft-strategy
- **Step0**: 🟢 — Argument Parsing→Pre-Check→5-step Delegation(:43-49), 각 stage 절차를 named reference 위임.
- **① Invocation**: 🟡 — pipeline sub(autopilot-draft가 3→6 mode 변환 호출). resident description 낭비, 직접 `/draft-strategy`는 부차.
- **② Info Hierarchy**: 🟢 — textbook 3-rung: 64줄 body, references/ 1-depth×3, 강한 포인터(파일+시점 :51-55). no sprawl.
- **③ Steering**: 🟢 — mode 이름 leading anchor; checkable completion(QA verdict max-2)을 `references/qa-review.md` 강한 포인터 위임; body negation 없음.
- **④ Pruning**: 🟡 — Required Reads(:51-55) vs Reference Map(:57-61) 동일 3개 이중 서술.
- **flags**: duplication
- **top gap**: Required Reads를 Reference Map에 통합 (`skills/draft-strategy/SKILL.md:51`)

### post-it
- **Step0**: 🟢 — 4개 중 최강 invariant framing: fire-and-forget(:18) + lifecycle "졸업하거나 만료 — 영구 누적 금지"(:27) + 7-sub-action taxonomy. SoT/steering exemplar.
- **① Invocation**: 🟡 — 확인된 긴장: :14 "사용자가 명시적으로 `/post-it` 호출할 때만 변경"(user-invoked 계약)이나 frontmatter는 model-invoked·disable flag 없음(:1-3). proactive-nudge auto-record(references/nudge-and-boundaries.md)가 model-invoked를 부분 정당화 → wording/등록 불일치(hard 오분류 아님), 단 :14가 "호출할 때만"을 과장.
- **② Info Hierarchy**: 🟢 — 58줄 lean, references/ 1-depth×3, 강한 Required-Reads(:33-35). 3-rung 정확.
- **③ Steering**: 🟢 — leading anchor("fire-and-forget","사용자는 들여다보지 않는다"); Confirm+completion을 references/sub-actions.md 위임. negation(:16,:27) 의도적 invariant.
- **④ Pruning**: 🟡 — 동일 3개 reference 3중 열거(Quick Contract :26-29, Required Reads :33-35, Reference Map :39-41).
- **flags**: duplication
- **top gap**: :14 user-invoked 계약 wording을 실제 model-invoked+proactive-nudge와 정합(문구 완화 or disable flag 추가) (`skills/post-it/SKILL.md:14`)

### sync-skills
- **Step0**: 🟢 — Pipeline Step 표(:60-65) + Safety Rules(:81-85) + anti-drift "본문에 카운트·명단 hardcode 안 함"(:39) + self-hashing(:85).
- **① Invocation**: 🟡 — ops skill, 편집 후 의도 호출(or Stop hook), auto-activation 의존 낮음. resident description 낭비.
- **② Info Hierarchy**: 🟢 — 88줄 라우터, references/ 1-depth×4, Step→reference 매핑 표(:60-65). 3-rung 정확.
- **③ Steering**: 🟢 — leading("Source of Truth","drift"); Safety Rules checkable(manual-edit abort, --check, SHA-skip). negation(:25,:39) safety invariant.
- **④ Pruning**: 🟡 — Step→reference 3중 표현(Pipeline :60-65, Required Reads :67-72, Reference Map :74-79).
- **flags**: duplication
- **top gap**: 3중 Step→reference 열거를 단일 매핑으로 통합 (`skills/sync-skills/SKILL.md:67`)
