# plan-check round 1 — 독립 리뷰 (품질관리팀 plan-review, read-only)

- **사이클**: 2026-07-15 fleet-v9-mouse-subagent
- **대상**: `plan/plan.md` (초안)
- **rigor**: standard (CONVENTIONS §1.1) → 독립 리뷰 1회 + 교정 최대 1회
- **verdict**: **revise** — 🔴 2건 / 🟡 4건 / 🟢 3건

## 🔴 블로커 2건 (요지)

**🔴1 — §4.4 좌표 반전이 무명(無名) 전제 위에 있다.**
반전 설계 자체는 fail-safe 방향으로 접힌다(확인됨: `confirm`의 `[kill]`(우) → `confirm2`의 `[cancel]`(우) → 같은 자리 연타 = 취소). 그러나 이는 **"click 1 처리 후 다음 `getch` 전에 `_draw`가 반드시 돈다"**에 전적으로 의존한다. `_PROMPT_HITS`는 `_draw` 최상단에서만 재구축되므로(render.py:2504 패턴), 재그리기 없이 click 2가 들어오면 `confirm` 단계의 낡은 맵을 읽어 우측 x를 `"kill"`로 보고 → **prd.md:281의 working 이중 확인이 마우스에서 깨진다.**
플랜 §4.2/R2-2의 "선행 분기"·"한 줄만 선행 삽입" 문구가 안전한 배치(`_PROMPT` 블록 **내부**)와 위험한 배치(블록 **앞** + 자체 `continue`)를 **모두 허용**했다.

**🔴2 — `_CLICK_ROWS` 편집 표면이 틀렸다 → 첫 클릭이 죽는다.**
`_draw`의 기존 `targets`(render.py:2515)는 `_live_targets() if _SELECT_MODE else []` 로 게이트돼 있어 **base 모드(=첫 클릭 시점)에는 항상 `[]`**. rung 3이 절대 안 걸리고 rung 4(해제)로 떨어져 **prd.md:279의 1급 경로 진입 자체가 불가능**.
게이트를 푸는 순진한 수정은 더 나쁨 — `_live_targets()`가 엔트리마다 `is_excluded()` → `_ancestors()`(최대 16회 `/proc/<pid>/stat`) + `_current_session_pid()`(`~/.claude/sessions/` 전체 listdir + 매 파일 `json.load`, 캐시 없음, control.py:118-140)를 호출하고 `_draw`는 **~10fps**(render.py:2585·2647)로 돈다 → 틱당 비용 0인 경로가 초당 수백~수천 회 JSON 파싱으로 변질.

## 🟡 조건 4건

| # | 요지 | 근거 |
|---|---|---|
| 🟡3 | 비겹침 검증이 한 폭이면 불충분 — 버튼 x가 rung 조합에 따라 이동 | `_prompt_segs` 3-rung 사다리 (render.py:2280-2333) |
| 🟡4 | `pick()`은 **안 맞는 마지막 rung도 반환** → 화면 밖 `[kill]` 히트박스 생존 위험 | render.py:2286 `return variants[-1]` |
| 🟡5 | `getmouse()` 예외 시 `mx` **unbound** → `_handle_mouse(mx, my)` 호출 순간 `NameError`로 TUI 크래시 | render.py:2628-2631 (`except`가 `my`만 설정) |
| 🟡6 | 클릭 한 번이 방향키를 가져가는 것이 미결정 + **테스트명이 실제 동작과 반대** | render.py:2598-2601·2363-2368 |

## 🟢 정보 3건

- Step 1 → Step 2 선행 주장 미성립 (실제 사슬 = Step1 → Step5 → Step2의 A2-6 증명).
- R3-1 리스크 **서술이 뒤집힘**(완화책은 옳음) — 역방향 tail에서 `tool_use`가 창 안이면 그 뒤 `tool_result`도 필연적으로 창 안 → "짝 없는 `tool_use` = 활성"은 구조적으로 정확.
- `escalate` 반전은 방어적 잉여(무해, 유지 권장) — `_poll_pending_kill`이 `KILL_GRACE_SEC` 후에만 띄우므로 더블클릭이 `confirm`에서 도달 불가. `_PROFILE_MAX`는 :941.

## 리뷰가 확인한 강점 (실측분만)

- **⛔ 절대 안전 규칙이 실제로 닫혀 있다** — 전 검증 경로 추적 결과 실세션을 요구하는 단계 **없음**. v8 위반의 자진 기록 + "철회된 절차는 규범이 아니다" 명시.
- **§2.1 미러 정정이 실측으로 옳다** — `test_mirror_parity.py`가 `rglob("*")` 전수 바이트 매치 → 신규 테스트 파일까지 동기 대상.
- 인용 안전 앵커 전부 실재(`VerifyTargetTest`:47·`RealSignalTest`:203·`ActionLogTest`:241·`TestRegistryCloseParity`:354), 베이스라인 416/OK 재현.
- 계약 정합에 **발명·누락 없음** — F-27 6동작·F-29 소스 순서/pulse 금지/additive json·D3·스크롤 테스트 전부 prd.md:279-284·290-295·468 추적 가능.
