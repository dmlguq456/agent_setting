# aovestdipaperino/tokensave — code-intelligence MCP (AST 심볼 질의)

**Type**: repo
**URL**: https://github.com/aovestdipaperino/tokensave
**분류축1 (메커니즘)**: input-context-reduction (전체 파일 dump 대신 심볼 단위 질의로 입력 절감)
**절감 claim**: (Hackenberger stack) 구조적 discovery 60-80% reduction
**실측/검증**: 미검증(독립 검증 없음). CodeGraph(원본 TS by @colbymchenry)의 Rust port.
**신호->레버 매핑**: 명시 없음. 레버=파일 전체 읽기 대신 call graph/impact/dead-code 등 심볼 질의로 대체.
**하네스 시사점**: "코드 탐색 시 파일 통째로 읽지 말고 심볼만 질의" — 하네스가 Read/Grep 대신 구조적
질의로 입력을 줄이는 도구 레버. token-budget 압박 시 탐색 전략 전환 신호→레버에 대응.

## Summary
40+ tools / 30+ languages code-intelligence MCP server. Rust port of CodeGraph. ~25MB binary,
50+ tree-sitter grammar, 80+ symbol-level MCP tool(call graph, impact analysis, dead code
detection, complexity ranking), 100% local, 9 agent 통합.

메커니즘은 caveman/ponytail 과 다른 계층: 출력·행동이 아니라 **에이전트의 탐색 방식** 을 바꿔 입력을
절감. 파일 전체를 컨텍스트에 넣는 대신 심볼 단위로 질의. Hackenberger stack 의 "TokenSave" 와 이름 겹침
— 동일 프로젝트 여부는 report stage 에서 재확인 필요(브랜드명 충돌). token-budget 축의 "탐색 레버" 예시.

**Figures**: (none extracted)
