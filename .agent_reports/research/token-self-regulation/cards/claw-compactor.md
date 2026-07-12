# open-compress/claw-compactor — deterministic 14-stage 압축 파이프라인

**Type**: catalog/repo
**URL**: https://github.com/open-compress/claw-compactor
**분류축1 (메커니즘)**: input-context-reduction (결정론적·비-LLM·reversible)
**절감 claim**: up to 97% token cost reduction
**실측/검증**: 미검증(독립 검증 없음). 97%는 up-to 상한값 — codepointer 반증 논리(per-payload vs
session-wide)가 그대로 적용될 개연성.
**신호->레버 매핑**: 명시 없음(정적 파이프라인). AST-aware, reversible 이라 decompression 가능.
**하네스 시사점**: LLM 없이 결정론적으로 압축·복원 → 재현성·감사 가능성 측면에서 프로덕션 친화. 단
97% 는 압축 대상 payload 한정치이며 세션 절감은 별개(axis 2 반복 교훈).

## Summary
OpenClaw 워크스페이스 전용, **결정론적(no-LLM) 14-stage fusion** 압축 파이프라인(초기 5-layer 설계에서
진화). AST-aware, reversible. `pip install claw-compactor`. up to 97% cost reduction 주장.

비-LLM·reversible 이라는 점이 caveman(LLM 문체) / wilpel-LLM 모드와 차별 — 압축이 결정론적이라 원본
복원이 보장. 그러나 "up to 97%"는 전형적 per-payload 상한이고, codepointer 3중 gap(denominator·
workload·pricing)이 그대로 적용될 수 있어 세션 절감은 훨씬 작을 것으로 추정(독립 검증 없음).

**Figures**: (none extracted)
