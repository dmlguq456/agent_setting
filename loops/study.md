# 연수 (주간 자율 audit — 외부 동향 × 현 세팅 대조)

어떤 지침·설정 파일도 직접 수정하지 않는다. 산출은 제안서 1개뿐 — 채택은 사용자 서명, 적용 후 검증은 모의훈련(drill).

## 절차

1. **이전 연수 복기**: `/home/nas/user/Uihyeop/notes/study/` 의 최근 보고 1~2개 Read — 같은 제안 반복 금지, 미채택 항목은 "재상정 가치 있을 때만" 한 줄 갱신.
2. **외부 동향 조사** (WebSearch·WebFetch):
   - 현재 주 runtime adapter 관련 공식 changelog·engineering 글 (Claude Code adapter 사용 중이면 Anthropic/Claude Code 자료 포함)
   - agent engineering 실무 패턴 신간 (harness·context·loop engineering, 멀티에이전트, eval)
   - 커뮤니티에서 자리 잡는 컨벤션 (헛소문·과장 글은 출처 품질로 거름)
3. **현 세팅 대조**: `<agent-home>/core/CORE.md`·runtime adapter bootstrap(현재 Claude Code: `adapters/claude/CLAUDE.md`)·`core/CONVENTIONS.md`(특히 §5.8~5.10)·`loops/README.md`·`hooks/` 목록을 Read 하고, 조사 결과와 비교 — 우리가 이미 하는 것 / 빠진 것 / 더 잘하는 것 구분.
4. **내부 위생 (가볍게)**: `loops/drill/metrics.csv` 의 g0_overhead in_tok 추세 (세팅 세금 증감) + 지침 문서 간 모순·비대 후보 1~2건 + **의도 불명 지침** (왜·날짜·계기 주석 없는 규칙 — CONVENTIONS §3.6 위반) 후보 1~2건. **상한 경보**: g0 in_tok 45k 초과 시 ⚠️ 다이어트 권고 (2026-06-11 기준선 ~40k; context 파일 과다는 성능 역효과 — 매뉴얼 1부 Tension ④ 반례 데이터).
5. **주간 사용 결산 (재무)**: `loops/*.log` 의 지난 7일 run 횟수·소요시간, `loops/drill/metrics.csv` cost 합산, `<agent-home>/.dispatch/jobs.log` 의 주간 job 수 — 표 한 개로. 이상 급증(전주 대비 2배+)만 ⚠️ 플래그. 절대액 평가는 하지 않는다 (구독 사용량이라 — 추세·쏠림만).

## 제안서 — `/home/nas/user/Uihyeop/notes/study/<날짜 YYYY-MM-DD>.md`

제안별로: **무엇을** / **왜** (출처 링크) / **우리 세팅 어디에** (파일·절) / **예상 비용** (구현 + 세팅 세금 영향) / **우선순위** (🔴지금·🟡다음·🟢참고). 제안 0 건이어도 파일은 남긴다 — `# 연수 — <날짜>\n신규 제안 없음 (조사 N건 검토)` (heartbeat).

과장 금지 — "도입하면 좋다"가 아니라 "우리 세팅의 어느 마찰을 줄이나"로만 정당화. 마찰 불명이면 🟢참고로 격하.

### 자동 초안 (🔴 우선순위 한정 — Hermes `skill_manage` self-edit 벤치마킹, T2)

> 제안을 _설명_ 에서 멈추지 않고, 사용자가 _서명만 하면 바로 적용_ 할 수 있게 **구체 edit 초안**까지 붙인다. 단 출구는 여전히 _초안 제안_ — 직접 적용·커밋은 절대 하지 않는다 (불변식: 결정은 사용자).

🔴 우선순위 제안에 한해(노이즈·환각 방지 위해 🟡🟢 은 설명만), 제안 끝에 `> 자동 초안` 블록:
- **대상 파일·절** 명시 + 적용 _전/후_ 텍스트 (붙여넣기 가능한 diff 또는 before→after 인용). 추측이면 명시.
- 적용 후 **검증 경로** 한 줄 (지침 변경 → `loops/drill/run.sh`, 새 스크립트 → autopilot-spec→code).
- 초안 작성 시 대상 파일을 실제 Read 해 _현재 텍스트_ 기준으로 — stale 인용 금지. 확신 없으면 초안 생략하고 "초안 보류 (대상 텍스트 불확실)" 로 표기.
- 자동 초안은 _제안서 안_ 에만 존재 — 실제 파일은 건드리지 않는다. drift 위험 있으면 차라리 설명만.
