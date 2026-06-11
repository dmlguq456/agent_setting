# 연수 (주간 자율 audit — 외부 동향 × 현 세팅 대조)

어떤 지침·설정 파일도 직접 수정하지 않는다. 산출은 제안서 1개뿐 — 채택은 사용자 서명, 적용 후 검증은 모의훈련(golden).

## 절차

1. **이전 연수 복기**: `/home/nas/user/Uihyeop/notes/study/` 의 최근 보고 1~2개 Read — 같은 제안 반복 금지, 미채택 항목은 "재상정 가치 있을 때만" 한 줄 갱신.
2. **외부 동향 조사** (WebSearch·WebFetch):
   - Anthropic engineering 블로그·Claude Code changelog 신규 글/기능
   - agent engineering 실무 패턴 신간 (harness·context·loop engineering, 멀티에이전트, eval)
   - 커뮤니티에서 자리 잡는 컨벤션 (헛소문·과장 글은 출처 품질로 거름)
3. **현 세팅 대조**: `~/.claude/CLAUDE.md`·`CONVENTIONS.md`(특히 §5.8~5.10)·`loops/README.md`·`hooks/` 목록을 Read 하고, 조사 결과와 비교 — 우리가 이미 하는 것 / 빠진 것 / 더 잘하는 것 구분.
4. **내부 위생 (가볍게)**: `loops/golden/metrics.csv` 의 g0_overhead in_tok 추세 (세팅 세금 증감) + 지침 문서 간 모순·비대 후보 1~2건만.

## 제안서 — `/home/nas/user/Uihyeop/notes/study/<날짜 YYYY-MM-DD>.md`

제안별로: **무엇을** / **왜** (출처 링크) / **우리 세팅 어디에** (파일·절) / **예상 비용** (구현 + 세팅 세금 영향) / **우선순위** (🔴지금·🟡다음·🟢참고). 제안 0 건이어도 파일은 남긴다 — `# 연수 — <날짜>\n신규 제안 없음 (조사 N건 검토)` (heartbeat).

과장 금지 — "도입하면 좋다"가 아니라 "우리 세팅의 어느 마찰을 줄이나"로만 정당화. 마찰 불명이면 🟢참고로 격하.
