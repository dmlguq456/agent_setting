# codepointer — rtk/headroom/caveman 실사용 replay 반증 (3.7% critique)

**Type**: blog
**URL**: https://codepointer.substack.com/p/cutting-llm-token-costs-with-rtk
**분류축1 (메커니즘)**: (비판 대상: output-compression + input-context-reduction 도구 전반)
**절감 claim**: (비판) 광고 60-90% vs 실측
**실측/검증**: **본 연구 axis 2 의 핵심 반증**. 500 sampled 실 Claude Code 세션(2,182 세션·13 project·
614M tok·$926.31 baseline)에서 rtk+headroom+caveman 를 turn-by-turn counterfactual replay →
**합산 실절감 3.7%** (광고 60-90% 대비).
**신호->레버 매핑**: N/A (반증 분석)
**하네스 시사점**: 절감 claim 은 반드시 **세션 전체 denominator·실제 pricing 구조** 로 환산해 평가.
하네스 token-budget 축은 per-payload % 가 아니라 세션 청구액 기준 목표를 세워야 함.

## Summary
token-saving 도구 생태계에 대한 가장 강한 실증 반증. 광고 수치가 실사용에서 무너지는 **3중 gap** 을
데이터로 규명:

1. **denominator mismatch** — 광고 %는 per-payload(압축 대상 페이로드 한정), 실제 청구는 세션 전체이며
   다른 비용이 지배. 압축이 건드리는 부분은 청구의 일부일 뿐.
2. **workload mismatch** — 도구는 synthetic/repetitive 데이터에서 가장 잘 압축되는데, 실 트래픽에서
   그런 데이터 비중은 작음.
3. **pricing structure** — 압축된 토큰은 싼 cache_read($0.50/M)로 떨어지는데, 청구는 cache_create
   (42%)·output(29%)이 지배하고 이들은 압축 도구가 못 건드림.

Hackenberger "Ultimate Stack" 홍보글의 정반대 카운터파트. caveman HONEST-NUMBERS 의 self-critique
와 독립적으로 같은 결론(session-level 효과 미미)에 도달 → 교차 검증된 반증.

**Figures**: (none extracted)
