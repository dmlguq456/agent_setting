# Phase C — Code & Model Search 요약

`code_search_available: true`. technology mode 로 Phase C 활성, 핵심 3개 repo 를 실제 clone·열람.

## 실제 열람한 소스

| repo | clone 경로 | 열람 파일 | 메커니즘 계층 |
|---|---|---|---|
| JuliusBrussee/caveman | `code_resources/JuliusBrussee_caveman/` | `skills/caveman/SKILL.md`, `docs/HONEST-NUMBERS.md`, benchmarks/ | 출력 표면 압축 (system-prompt) |
| DietrichGebert/ponytail | `code_resources/DietrichGebert_ponytail/` | `skills/ponytail/SKILL.md`, `benchmarks/results/{cost-verification, caveman-vs-ponytail}.md` | 행동 억제 (decision ladder) |
| wilpel/caveman-compression | `code_resources/wilpel_caveman-compression/` | `prompts/compression.txt`, `SPEC.md`, `caveman_compress*.py` | 입력/컨텍스트 알고리즘 압축 |

발췌·해설은 `code_resources/EXCERPTS.md` 에 정리. 세 repo 전체 트리는 clone 그대로 보존.

## Phase C 핵심 발견 (메커니즘 3계층이 코드로 확인됨)

1. **caveman = system-prompt 지시문**이지 알고리즘 아님. SKILL.md 5KB 가 매 turn context 에
   재주입 → 이게 net-negative 의 근본 원인(저자 스스로 HONEST-NUMBERS 에 명시). ultra intensity
   에서 "invented abbreviation(cfg/impl) 은 tokenizer 가 같게 쪼개 절감 0" 이라 명시적으로 금지 —
   토큰 절감 메커니즘에 대한 이례적으로 정확한 이해.
2. **caveman 의 Auto-Clarity 섹션이 self-regulation 을 이미 내장** — 위험/모호 신호에서 압축 강도
   자동 해제. 하네스의 token-budget 축 설계에 직접 재사용 가능한 패턴.
3. **ponytail 의 decision ladder = 7-rung 게이트**. 출력이 아니라 "작업을 할지/얼마나 할지"를
   억제. safety rail(validation/security/a11y 불가침)이 명시. 이는 하네스 intensity 축(난이도·중요도)
   과 겹치는 부분 — ladder 의 "necessity check" 는 사실 intensity 판단에 가깝고, "shortest diff"
   는 token-budget 판단에 가까움. 두 축의 간섭 지점을 코드로 예시.
4. **저자 벤치가 재주입 오버헤드 비판을 자체 재현**: ponytail cost-verification 이 reasoning model
   (gpt-5.4-mini +26%, gpt-5.5 +39% more expensive)에서 always-on ruleset 이 절감을 역전시킴을
   측정. caveman-vs-ponytail 벤치는 minimal task 에서 ~3k "skill-read tax" 를 측정 → floor effect
   실증.

## 부차 생태계 (코드 미열람, 카드는 search notes 기반)

headroom(tool-output 압축 proxy/MCP), tokensave(AST code-intelligence MCP), claw-compactor
(deterministic 14-stage 압축), token-optimizer(skill/memory audit skill) — 모두 입력/컨텍스트
절감 또는 도구-출력 절감 계층. 소스는 GitHub 에 있으나 본 stage 에서 clone 우선순위는 caveman/
ponytail/wilpel 3종(clarified intent 핵심 대상)에 집중.
