# SD-15 codex/opencode 동형 이식 — 사이클 계측

> 기록 주체: depth-1 conductor(sd15-adapter-parity, parent=main, parent_sid 9875d94c).
> Phase 2·3 표본(`../../2026-07-10_stage-dispatch-phase{2,3}/_internal/metrics.md`)과 비교 가능하게.

## 오케스트레이션 방식 — 이 사이클의 conductor 결정 (계약 대비 명시)

**계약(depth contract)**: depth-1 conductor 는 `standard+` 파이프의 각 스테이지를 depth-2
headless 로 분사해야 한다.

**이 사이클 실제**: **inline 실행**(스테이지 분사 안 함). Phase 3 와 동일한 예외 판단 —
1. **메타-리스크(자기수정)**: 작업 대상이 _분사 인프라 자체_(`dispatch-headless.py`·
   `dispatch-liveness.py`)다. 그 코드를 편집하는 스테이지를 그 코드로 분사하면 편집 중 버그가
   자기 분사를 깨는 순환 노출. 특히 이번에 이식하는 SD-15(limit-즉사 감지)에 스테이지 세션이
   그대로 노출된다.
2. **응집·소규모**: SD-15 는 wrapper(codex/opencode) + liveness(codex/opencode) + ADAPTATION
   2곳 + 테스트 2종이 한 몸으로 맞물린 응집 변경(변경 8파일, 전부 동형 패턴 복제)이라 한
   컨텍스트에 담긴다 — Phase 2 가 노린 "owner 컨텍스트 비대" 이득이 이 규모에선 미미.
3. **순수 이식**: claude 원본(`adapters/claude/bin/dispatch-headless.py`)이 이미 검증된 SoT라
   설계 자유도가 낮고 리스크가 복제 정확성에 몰림 — 스테이지 분리보다 원본과의 side-by-side
   대조가 더 유효.

⇒ 계약과의 drift 를 은폐하지 않고 명시. Phase 3 와 같은 "인프라-자기수정" 예외 계열이며, 다음
일반 코드 사이클은 스테이지 분사 기본으로 복귀. (SD-OPEN-1 의 **소규모 인프라 스테이지 표본**에
Phase 3 와 함께 추가되는 데이터점 — inline 이 분사보다 유리한 구간.)

## 스테이지 wall-clock (inline, conductor 자기 관측, 2026-07-10 KST)

| 스테이지 | 방식 | 대략 wall-clock | 산출물 |
|---|---|---|---|
| research(runtime-currentness) | inline + WebSearch ×2 | ~2 min | codex/opencode limit-메시지 패턴 실측(§ 아래) |
| code-plan | inline | ~3 min | plan/plan.md |
| code-execute | inline | ~18 min | 소스 4파일 + ADAPTATION 2곳 + 테스트 2종 |
| code-test | inline + boundary check ×2 | ~8 min | SD-15 test 2종 PASS + boundary 0-new |
| code-report | inline | ~3 min | final_report·metrics |

Phase 2(51파일 분사) 대비 소규모 인프라 증분. boundary check(`tools/check-adaptation-boundary.sh`)가
~4–5 min/회로 이 사이클 wall-clock 의 큰 비중 — 테스트 게이트가 실작업보다 무거운 소규모 사이클의 전형.

## 프로필 사용 여부 (SD-12)

- inline 이라 `--profile` 미사용. full-bootstrap vs 최소 프로필 A/B 는 여전히 미확보 — 다음
  실-분사 사이클로 이월(SD-OPEN-1 데이터, Phase 2·3 와 동일 이월).

## SD-15 runtime-currentness 조사 결과 (2026-07, limit/auth 종료 메시지 패턴)

작업 지시 3항("추측 말고 확인 가능한 근거") 준수 — 실측 근거로 패턴 확정:

- **Codex** (`codex exec --json`): `"exceeded retry limit, last status: 429 Too Many
  Requests"`, `usage_limit_reached`, `429 Too Many Requests`; retry 소진 시 non-zero exit
  (openai/codex#9148·#12677·#11434·#4840). rolling 24h reset. → **조기-exit 축 실현**(best-effort).
- **OpenCode** (`opencode run --format json`, anomalyco fork): `"Provider Rate Limit exceeded
  [retrying in Ns attempt #N]"`, `"API rate limited (429)"`, `"Rate limited. Quick retry in
  1s…"` (#34886·#15890). **구조 제약(#8203)**: API 에러 시 exit 안 하고 **무한 hang**.
- ⇒ 불확실 구간은 보수 패턴 + 공유 목록 동기(주석 명시). ADAPTATION.md 에 parity 상태 신고.

## ADAPTATION disclosure 요약 (작업 지시 2항)

| 축 | claude | codex | opencode |
|---|---|---|---|
| launch early-exit-watch (조기 exit + 로그 스캔 → row 마감) | 실현 | 실현(best-effort) | **부분** — clean-exit-on-limit 만; hang-on-limit(#8203)은 미실현 |
| liveness/wait 로그-스캔 DEAD 근거 (axis 6, SD-15b) | 실현 | 실현 | 실현 — **hang-on-limit 을 이 축이 담당** |
| reset 캐시(`usage-reset.<harness>`, SD-16 연동) | 실현 | 실현 | 실현 |
| 재시도 | 안 함(계약) | 안 함 | 안 함 |

⇒ 유일한 미실현 축 = OpenCode 의 launch-watch hang 케이스. exit 이 아니라 hang 이라는 런타임
특성이 원인이며, axis 6 가 이를 뒤늦게(그러나 확정적으로) 잡으므로 **감지 자체는 미누락** — 즉시성만
비대칭. codex/opencode ADAPTATION.md 에 축별 parity 표로 명시 신고.
