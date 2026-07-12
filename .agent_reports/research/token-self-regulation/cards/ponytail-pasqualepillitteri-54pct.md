# Ponytail: Cuts 54% of the Code (pasqualepillitteri.it) — 54% 수치 출처

**Type**: blog
**URL**: https://pasqualepillitteri.it/en/news/5720/ponytail-ai-skill-less-code
**분류축1 (메커니즘)**: behavior-suppression
**절감 claim**: ~54% mean code reduction (12 tasks, FastAPI+React 언급)
**실측/검증**: **secondary — repo SKILL.md 에는 벤치 숫자 없음**. 54%는 이 블로그 계열이 출처. repo 의
자체 cost-verification 은 코드량이 아니라 비용 42-75% cheaper(Claude 한정)를 보고 → "54% 코드"와
"42-75% 비용"은 다른 지표.
**신호->레버 매핑**: 명시 없음
**하네스 시사점**: "코드 54% 감축" 같은 headline 은 지표(코드량 vs 토큰 vs 비용)를 혼동하기 쉬움 —
하네스는 절감 목표를 명확히 토큰/비용 기준으로 정의해야 함(axis 2 지표 혼동 경계).

## Summary
secondary 커버리지 중 널리 재인용되는 "54% mean code reduction"의 출처. repo 자체엔 이 숫자가 없고
(SKILL.md 는 벤치 무기재), 저자의 benchmarks/ 는 비용·correctness 중심. 코드 라인 감축과 토큰/비용
절감은 상관은 있으나 동일하지 않다(ponytail v1 은 코드 최소지만 산문이 토큰을 먹어 caveman 에 뒤짐).
지표 혼동을 경계하는 사례.

**Figures**: (none extracted)
