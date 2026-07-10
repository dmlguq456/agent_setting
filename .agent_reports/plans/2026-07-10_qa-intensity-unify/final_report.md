# qa-intensity-unify — final report (2026-07-10)

## 요지
사용자-facing `--qa` 축을 폐지하고 검증 rigor 를 `--intensity` 파생 단일 경로로 일원화했다.
CONVENTIONS §1.1 파생 테이블을 SoT 로 승격, external adversary 게이트를 `intensity=adversarial` 로
바인딩 이전했다. **검증 프로세스·스테이지는 하나도 제거하지 않았다**(decision_74ca88 계승) — 선택 knob만 접었다.

## QA-OPEN-1 판정: 완전 폐지 (반례 없음)
census 결과 shape 독립 heavy-rigor override 의 실존 반례 부재. 문서 파이프 always-on factual detector
(autopilot-draft Step 4b / autopilot-refine Stage B.5)는 unconditional-and-cheap(regex+cards grep)이라
`--qa` knob 없이 존속하고, heavy fact-check 는 이미 intensity(quick→skip, standard+→run)에 묶여 있어
독립 override 가 아니다. autopilot-spec update 는 오히려 quick 권장. → 내부 전용 rigor 파라미터 잔존 불필요.

## 변경 파일 (104개 = adapter 52 + root skills/ 미러 52)
### core (6)
- `core/CONVENTIONS.md` — §1 intro·§1 override 절 폐지·§1.1 "Verification Rigor Tiers (intensity-derived, canonical SoT)" 재서술 + `Derived from intensity` 컬럼·derivation 순서·external adversary→intensity 바인딩·§2.1 role·§1 스테이지표·§3 invariant #1/#5.
- `core/WORKFLOW.md` — §1.1(L51)·L74·§4(L166).
- `core/DESIGN_PRINCIPLES.md` — L128·§5(L176).
- `core/ADAPTATION.md` — L103 adaptation-point 라벨.
### adapter bootstrap·wrapper (5 + README)
- `adapters/claude/CLAUDE.md` — §0(B) high-stakes→intensity 상향·공통 플래그·함정.
- `adapters/claude/bin/dispatch-headless.py`, `adapters/codex/bin/dispatch-headless.py`, `adapters/opencode/bin/dispatch-headless.py` — `--qa` optional/derived(`QA_FROM_INTENSITY` 파생), jobs.log `qa=` 유지, boundary-asserted 문자열 불변.
- `adapters/claude/README.md` — external adversary·rigor tier 매핑 문구.
### skills 표면 (44 SKILL/README/references) + `sync-skills/references/cross-doc-invariants.md`
- 전 autopilot-*·code-*·draft-*·design-handoff·analyze-user·audit SKILL.md argument-hint 에서 `--qa` 제거, defaults·본문·references 를 intensity-파생 서술로. root `skills/` byte-equal 미러.
- `analyze-user` 는 원래 `--qa` flag 없음 — "adversarial 고정" → "intensity=adversarial 고정" 표현 이전, 4-reviewer QA phase 불변.
- `code-report` `qa_level` frontmatter 는 derived-plumbing(logging)으로 유지, 사용자 `--qa` flag 언급만 제거.

## 검증 결과
| 스위트 | 결과 |
|---|---|
| `hooks/portable-guards.test.sh` | PASS=313 **FAIL=12 = clean baseline 과 byte-identical**(BAD 셋 diff 0). 전부 환경 의존(`rg` 미설치 8건 + dispatch-liveness mtime flake 4건, P-28) — 비회귀. |
| `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` | 3종 PASS |
| `utilities/dispatch-wait.test.sh` | PASS |
| `utilities/dispatch-liveness.test.sh` | PASS |
| `utilities/usage-check.test.sh` | PASS |
| `tools/check-adaptation-boundary.sh` | **신규 FAIL 0.** 잔존 5건 = 전부 `adapters/claude/tools/fleet/*`(titles.py·refresh_title.py·test_f14/f15/f17) missing — fleet 소유 pre-existing baseline(범위 외, 미변경). ※ dispatch 지시의 "잔존 2건" 추정과 실측 5건 차이 — 모두 fleet baseline. |
| wrapper 파생 단위 | `QA_FROM_INTENSITY`: thorough→thorough, direct→light, standard/strong→standard 확인. `--qa` 미지정 시 파생, 명시 시 그대로(sd15 explicit `--qa` 통과). |
| skills/ ↔ adapters/claude/skills byte-equality | OK |
| `__pycache__` | 커밋 전 정리 완료 |

## 범위 외 / 후속
- `loops/**`(drill 케이스 `--qa`/`qa=` 잔존) · `tools/fleet/**`(`check:<qa>` 라벨) — dispatch 지시로 미변경. optional/derived 강등으로 explicit-`--qa` 케이스 하위호환 유지 → 비회귀. fleet `check:<qa>` 라벨 의미 변화는 handoff 통지 대상.
- codex/opencode preflight `qa-policy`·capability-map `dispatch_contract --qa <level>` — derived-plumbing 으로 유지(boundary-check 가 assert, PRD 가 보존 명시).
- `qa_level` frontmatter: code track(code-report)은 유지, doc track(draft/research)은 워커가 `intensity` 로 통일 — track별 독립 frontmatter라 비강제, 어떤 test 도 미검사.

## git
브랜치 `qa-intensity-unify` 에만 커밋. main 머지·worktree 정리는 메인 오케스트레이터 몫.
