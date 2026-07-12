# DietrichGebert/ponytail — "laziest senior dev" decision ladder, 코드 작성량 억제

**Type**: repo
**URL**: https://github.com/DietrichGebert/ponytail
**분류축1 (메커니즘)**: behavior-suppression (작업량 축소, 주) + budget-directive-self-monitoring
**절감 claim**: up to 94% less code, ~54% mean code reduction(12 tasks). cost 47-77% cheaper(README).
**실측/검증**: **저자 자체 재현** (`benchmarks/results/2026-06-17-cost-verification.md`) — Claude 에서만
42-75% cheaper(Haiku 63/Sonnet 74.5/Opus 42.3, 30 reps), correctness 100%. **OpenAI reasoning model
에서 역전: gpt-5.4-mini +26%, gpt-5.5 +39% more expensive** (always-on ruleset 오버헤드). 74k-star·
54% 는 secondary blog 출처(라이브 repo 미검증).
**신호->레버 매핑**: 작업 필요성/복잡도(신호) → decision ladder 로 범위 축소·되묻기(레버). 7-rung:
YAGNI→reuse→stdlib→native→existing-dep→one-liner→minimal. safety(validation/security/a11y)는 불가침.
**하네스 시사점**: 출력이 아닌 **행동(작업량)** 을 조절하는 레버 — 우리 하네스의 intensity 축과 겹침
주의. ladder rung1(necessity)은 intensity(중요도) 판단, "shortest diff"는 token-budget 판단 →
두 축의 간섭 지점을 코드로 예시. safety rail 은 어느 축에서도 불가침이어야 함을 시사.

## Summary
caveman 이 "how you talk"이면 ponytail 은 "what you build"을 규율하는 coding-task skill (저자가
"pair with Caveman"이라 명시, 직교). SKILL.md 의 decision ladder 는 첫 성립 rung 에서 멈추는 reflex —
speculative need skip, 이미 있는 helper reuse, stdlib/native 우선, one-line 우선. 규칙: unrequested
abstraction 금지, deletion>addition, `ponytail:` 주석으로 의도적 corner-cut 표기.

핵심 안전장치: "When NOT to be lazy" — input validation, error handling(데이터 손실 방지), security,
accessibility, 명시 요청은 절대 축소 금지. "Never lazy about understanding the problem. The ladder
shortens the solution, never the reading." → 억제 레버가 이해·검증을 훼손하지 않게 하는 명시적 경계.

벤치 교훈(직접 열람): v1 은 코드는 최소지만 "skipped on purpose" 산문이 토큰을 먹어 caveman 에 4% 뒤짐
→ output cap 으로 개선. minimal task 는 두 skill 모두 ~3k "skill-read tax". reasoning model 에서
ruleset 재주입이 절감을 역전. 이 자체 벤치가 axis 2 재주입 오버헤드 비판의 독립 재현.

**Figures**: (none extracted)
