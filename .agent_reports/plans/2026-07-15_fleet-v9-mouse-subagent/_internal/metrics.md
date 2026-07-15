# metrics — fleet v9 사이클 (2026-07-15)

## 스테이지 분사 기록 (OPERATIONS §5.10 · SD-17/SD-49/SD-50)

conductor = `fleet-v9-mouse-subagent` (depth 1, claude, opus/high).
route = `rt-9ff8199b5372cfdb` (`/tmp/fleet-v9-route.json`, staged, 4 노드).
registry = `/home/Uihyeop/agent_setting/.dispatch/jobs.log` (상속된 `AGENT_DISPATCH_JOBS`).

### SD-50 fallback 근거 (전 노드 공통)

`utilities/nested-dispatch-eligibility.py` 실측 6튜플 (2026-07-15T08:55Z):

| launch_authority | child | status | 비고 |
|---|---|---|---|
| conductor | claude / codex / opencode | `unknown` | `unprobed-tuple` — fail-closed, 부적격 |
| ancestor-broker | claude | **`supported`** | `ancestor-broker-command-check` — **선택** |
| ancestor-broker | codex | `unsupported` | codex 런타임 프로젝션 18건 실패 |
| ancestor-broker | opencode | `supported` | 미선택(동일 하네스 우선) |

→ ordinal 1 same-harness-headless 안에서 conductor hop은 `unknown`으로 부적격, ancestor-broker hop이 유일한 검증 적격 튜플. 전 스테이지 `launch_authority=ancestor-broker,fallback_ordinal=1`. native-subagent·inline 하위 hop 미도달.

### 분사된 스테이지 (4/4 — 인라인 실행 0)

| 노드 | slug | model_role | pid | 결과 |
|---|---|---|---|---|
| plan | `fleet-v9-plan` | deep maker / opus | 3029896 | plan.md 6스텝 + plan-check 2R 전 조건 해소 |
| execute | `fleet-v9-execute` | fast implementer / sonnet | 3143195 | 6스텝, 416→468 |
| test | `fleet-v9-test` | deep reviewer / opus | 3294145 | 전 영역 PASS + 결함 4건 |
| report | `fleet-v9-report` | fast writer / sonnet | — | final_report.md |

전 row는 수확 직후 `done`으로 in-place 마감(§5.10 registry duty).

## 인라인 실행 예외 1건 — 기록 의무 이행 (SD-17)

**대상**: F-29 서브에이전트 글리프 `🔬` → `⚡` 되돌림 (`render.py` 2곳: `_ICON_SUBAGENT` 상수 1줄 + 독스트링 1줄) + 미러 rsync.

**인라인 사유**: §5.10 인라인 예외 중 "the stage is so small that dispatch overhead clearly exceeds it". 수정 표면이 단일 파일 2줄이고 테스트는 `_ICON_SUBAGENT` 상수를 참조해 하드코딩 결합이 없음(`grep -rn 🔬 tools/fleet/` = 소스 4건 전부 `render.py`, 테스트 0건). depth-2 세션 1회의 스폰·프롬프트·수확 비용이 수정 자체를 명백히 초과.

**근거의 독립성**: 이 되돌림은 conductor의 재량 판단이 아니라 **독립 검증자(code-test)의 판정을 conductor가 직접 재현 확인한 결과**다.
- code-test 판정: "충돌 주장은 거짓 — fleet은 `⚡`를 한 번도 렌더하지 않음", "plan.md:347이 이미 '`⚡`는 신규 — 충돌 없음'으로 판정했고 execute는 이를 인용·반박 없이 뒤집음", 권고 = `⚡` 복귀.
- conductor 재현: `grep -rn ⚡ tools/fleet/` → 산문 주석(:613,:616) + `_WIDE` 집합(:2118)뿐, 렌더 경로 0. `_gate_word`는 단어만 반환(`"untracked"`). 60/120/168 `--once` 실렌더 `⚡` 출현 **0회**. `🔬`의 `_WIDE` 등재는 HEAD에서 이미 존재(v9 잔여물 아님 — 유지).

**검증**: 되돌림 후 `python3 -m unittest discover -s tools/fleet/tests -q` → **Ran 468, OK**. `diff -r tools/fleet adapters/claude/tools/fleet` → 무출력(바이트 일치). `--json` → `subagents` 키 유지, top keys 불변.

**결과**: 코드가 PRD prd.md:293의 `└⚡<agent-type>` 계약과 다시 일치 — v9가 방금 해소한 spec drift의 재도입을 차단. PRD 개정 불요, minor-log 항목 불요.
