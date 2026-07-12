# headroomlabs-ai/headroom (RTK) — tool-output 압축 proxy/MCP

**Type**: repo
**URL**: https://github.com/headroomlabs-ai/headroom
**분류축1 (메커니즘)**: input-context-reduction (tool output/logs/files/RAG chunk 를 LLM 도달 전 압축)
**절감 claim**: 60-95% fewer tokens, "same answers". 실workload: code search 92%, incident 92%,
issue triage 73%, codebase exploration 47%.
**실측/검증**: 저자 benchmark(GSM8K accuracy delta ~0, TruthfulQA +0.030). **but codepointer replay 는
rtk+headroom+caveman 합산 실절감 3.7%** — code-search 류가 실 트래픽에서 작은 비중이라는 workload
mismatch. 58.7k star 는 self-reported(미검증).
**신호->레버 매핑**: 명시 없음(도구 출력이 크면 압축, 정적). 레버=tool output 압축률.
**하네스 시사점**: 도구 호출 결과가 큰 로그/파일일 때의 입력 절감 레버 — 하네스가 도구 출력 truncation/
요약을 token-budget 신호에 따라 조절하는 자리에 대응. 단 세션 전체 효과는 codepointer 반증대로 제한적.

## Summary
tool output·logs·files·RAG chunk 를 LLM 에 도달하기 전 압축하는 library/proxy/MCP server. MCP tools:
`headroom_compress`, `headroom_retrieve`, `headroom_stats`. Hackenberger "Ultimate Stack"의 RTK 구성
요소. code search/incident debugging 처럼 반복·구조적 출력에서 90%대 절감 주장.

품질 유지 주장(GSM8K delta ~0, TruthfulQA +0.030)은 벤치 상 그럴듯하나, codepointer 반증의 workload
mismatch·pricing structure gap 이 정확히 이 도구군을 겨냥 — 압축된 토큰이 싼 cache_read 로 떨어져
청구 지배 항목(cache_create·output)을 못 건드림. axis 2 에서 "벤치 정확성 ≠ 세션 절감"의 사례.

**Figures**: (none extracted)
