# Stage-dispatch metrics — token-self-regulation (SD-17 separability 기록)

## Durable stage 분사 (depth-2 headless)
| stage | slug | model-role | 소요(대략) | verdict |
|---|---|---|---|---|
| search | tsr-search | fast implementer (sonnet/medium) | ~9분 | done — 25 발견물, 필수 6대상 전부 확보 |
| analyze | tsr-analyze | deep maker (opus/high) | ~38분 | done — 22 cards + code_resources(3종 실 clone) |
| report | tsr-report | deep maker (opus/high) | ~20분 | done — 8 files, QA round1 🔴0, unresolved 없음 |

## Inline micro-step (conductor 직접 처리 — SD-17 근거)
- **Step 1 (intake)**: topic/mode/depth/intensity 는 depth-0 세션에서 이미 합의(clarified_intent) — 비분리, 파일 1개(pipeline_state.yaml) 생성뿐.
- **Step 2d 상당 (search 결과 검증)**: `search_results.json` JSON 유효성·papers 비어있지 않음 확인은 conductor 가 dispatch-wait 수확 직후 즉시 확인(별도 세션 불필요).
- **Step 3 상당 (analyze 결과 검증)**: `stage-analyze-status.json` + cards 수 확인, conductor inline.
- **Step 5·6 (pipeline_summary·briefing)**: 산출물 종합·서술이라 report stage 산출물을 읽고 conductor 가 직접 작성 — 별도 depth-2 세션을 새로 열 만큼 분리되지 않음 (report stage 가 이미 8개 파일+QA 로 컨텍스트를 다 씀).

## depth 3+ 없음 확인
- report stage 세션 내부에서 Agent(연구팀)/Agent(편집팀) in-session 호출은 stage session 안의 정상 Agent tool 사용 — 별도 headless 재분사 아님. dispatch-headless.py 재호출은 conductor(depth 1)→stage(depth 2) 3회(search/analyze/report)뿐.

## 동시 상한
- 순차 파이프(search→analyze→report), 동시 활성 최대 conductor(1)+stage(1)=2 ≤ 5.
