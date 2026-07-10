# qa-intensity-unify — 구현 plan (2026-07-10)

> 입력 SoT: `.agent_reports/spec/qa-intensity-unify/prd.md` v1
> intensity=standard · qa(파생)=standard · dev mode · 브랜치 `qa-intensity-unify`

## 목표
사용자-facing `--qa` 축 폐지. 검증 rigor = `--intensity` 파생(CONVENTIONS §1.1 매핑 테이블 = SoT).
검증 프로세스·스테이지는 하나도 제거하지 않는다(decision_74ca88 계승) — 선택 knob만 intensity로 접는다.

## 순서 (core-first)
1. **CONVENTIONS §1/§1.1** — "compatibility override" 절 폐지, §1.1 을 "Verification Rigor Tiers (intensity-derived, canonical SoT)" 로 재서술, `Derived from intensity` 컬럼 추가, external adversary 게이트를 `intensity=adversarial` 로 바인딩 이전, §3 invariant #1 재서술.
2. **WORKFLOW §1.1(L51)·§4(L166)·L74** + **DESIGN_PRINCIPLES §5(L176)·L128** + **ADAPTATION L103** — intensity 단일 축 정합.
3. **adapter bootstrap CLAUDE.md** §0(B) high-stakes→intensity 상향, 공통 플래그 목록에서 `--qa` 제거, 함정 라인.
4. **skills 표면** (전 SKILL.md argument-hint + defaults + 본문 + references) — `--qa` argument-hint 제거, rigor=intensity 파생 서술. root `skills/` 미러 byte-equal.
5. **wrapper 3종** (claude/codex/opencode dispatch-headless.py) — `--qa` optional/derived(미지정 시 `QA_FROM_INTENSITY` 파생), jobs.log `qa=` 필드 유지. boundary-asserted 문자열(`invalid-dispatch-qa`, `qa-policy {args.qa}`, dispatch_contract) 불변 보존.
6. **cross-doc-invariants.md** (sync-skills scanner 문서) 정합.

## QA-OPEN-1 census 판정
**완전 폐지 (반례 없음)** — shape 독립 heavy-rigor override 실존 반례 조사 결과 부재.
- 문서 파이프 always-on factual detector(autopilot-draft Step 4b, autopilot-refine Stage B.5)는 *unconditional-and-cheap*(regex+cards grep) — `--qa` knob 없이도 존속, intensity 독립이나 heavy 아님.
- heavy fact-check는 intensity(quick→skip, standard+→run)에 이미 묶임 = scope-gating + intensity-scaling, 독립 override 아님.
- autopilot-spec update는 오히려 quick 권장(heavy-on-quick 반례 아님).
- 유일 signal-based bump(high-stakes)는 intensity 상향으로 완전 표현 가능.
→ 내부 전용 rigor 파라미터 잔존 불필요.

## 제외 (dispatch 지시)
`loops/**`(drill 러너·케이스 파일 포함) · `tools/fleet/**`. drill fixture 정합은 범위 외 — optional/derived `--qa` 로 기존 explicit-`--qa` 케이스는 하위호환 유지되어 비회귀.

## 분사 토폴로지
conductor(depth-1) inline 실행 + in-session Agent 워커. 상세 = `_internal/metrics.md`.
