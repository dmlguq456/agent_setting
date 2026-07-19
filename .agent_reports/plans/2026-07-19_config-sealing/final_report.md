# Final Report — SD-68 dispatch-defaults config를 route record에 컴파일 시점 스냅샷으로 봉인

route: `rt-d57cbb149952fd3d` · spec: `spec/stage-dispatch/prd.md` §13.9.2 SD-68 · base: `ecd3acd8`

## 1. 무엇을 배선했나

`dispatch-defaults.yaml`을 selector(`dispatch-route.sh`)가 런타임에 재로드하는 SD-66 1단계와
별개로, `capability-route.py compile`이 config를 **컴파일 시점 스냅샷으로 route record에
봉인**하도록 2단계(SD-68)를 완성했다.

- `capability-route.py compile`: 각 depth-2 stage 노드에 `harness_affinity`
  (`claude|codex|opencode|diverse|unspecified`)를 스탬프하고, record 상단에
  `dispatch_defaults_digest`(정규화 파싱 config의 canonical-JSON sha256, 부재 시 `null`)를
  기록한다. 두 필드 모두 기존 `route_hash` 계산 **이전**에 삽입되므로 `route_hash`가 그대로
  두 필드를 봉인한다 — 별도 해시 로직 불필요.
- `verify_route`: 어휘 유효성 + digest 포맷만 검사한다. **config를 재로드하지 않는다** — 스탬프된
  route는 사후 config 변경에도 계속 verify를 통과한다(불변식 = hash 봉인).
- `dispatch-node.py` + 3개 wrapper(`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`):
  노드의 `harness_affinity`를 `--harness-affinity` 플래그로 registry row까지 passthrough한다.
  순수 메타데이터 기록이며 게이트가 아니다 — explicit `--adapter`가 affinity와 달라도 아무
  비교·거부 없이 통과한다(soft).
- `core/OPERATIONS.md` §5.10: record affinity 소비 규칙(soft·차단 없음, verify 재로드 금지,
  `registry_digest`와 분리)을 한 문장으로 현행화.

## 2. 커밋

Base `ecd3acd8` 위에 core-first 순서로 2개 커밋:

1. `3fbbd1e3` — spec: SD-68 record affinity 소비 규칙 한 문장 현행화 (`core/OPERATIONS.md` §5.10)
2. `9130c437` — feat(dispatch): SD-68 dispatch-defaults config를 route record에 컴파일 시점
   스냅샷으로 봉인 (utilities 3개 파일 + wrapper 3종 + tests)

지침(계약)이 구현보다 먼저 문서화되어야 한다는 spec 명시 요구에 따라 core 커밋이 utilities
커밋보다 앞선다.

## 3. Acceptance 판정 (①~⑤ 전부 PASS)

| # | 내용 | 판정 | 근거 |
|---|---|---|---|
| ① | compile 산출 route의 depth-2 노드 전부에 유효 어휘 `harness_affinity` 존재 | PASS | `capability_route.test.py` 18건 + 라이브 스모크: `plan=unspecified, execute=codex, test=diverse, report=claude` |
| ② | config 값 변경 → 신규 compile의 `route_hash` 변화 | PASS | `report: claude→codex` 변경 시 `route_hash`와 스탬프 값 모두 변화. **주석만** 바꾼 config는 `route_hash` 불변 — 정규화 digest 결정이 입증됨 |
| ③ | 스탬프된 기존 route는 config 사후 변경에도 verify 통과 | PASS | config A로 컴파일한 route를 env를 config B로 바꾼 뒤 `verify_route` — hash 봉인만 검사, 재로드 없음 |
| ④ | dispatch-node 경유 row에 `harness_affinity` 기록 | PASS | `dispatch_node.test.py` 20건 — argv에 `--harness-affinity <값>` 전달, 필드 없는 구 route는 미포함(불변) |
| ⑤ | explicit `--adapter`가 affinity와 달라도 launch 통과(soft) + 회귀 0 | PASS | `--adapter claude` vs `harness_affinity=codex` — 비교·거부 없이 통과. 기존 스위트 회귀 없음(§4) |

### Canonicalization 결정: 정규화 파싱 digest (원시 바이트 아님)

`dispatch_defaults_digest`는 `load_and_validate()`가 반환한 **검증된 config dict**를
`canonical()`(`json.dumps(sort_keys=True, ...)`)로 직렬화한 바이트의 sha256이다. 원시 파일
바이트의 해시가 아니다.

이 결정이 중요한 이유: 원시 바이트 방식이었다면 `dispatch-defaults.yaml`의 주석 한 줄을 편집하는
것만으로 값이 전혀 안 바뀌었어도 `route_hash`가 흔들려 **의미 변화 없는 봉인 파손(false
churn)**이 발생한다. 정규화 파싱 방식은 주석·공백·키 순서에 무반응하고 검증을 통과한 "효과적
config"만 반영하므로, 손상 config가 digest 계산 이전에 fail-loud되는 이점도 함께 얻는다. 위 ②의
"주석 변경 시 hash 불변" 결과가 이 선택을 직접 입증한다.

## 4. 검증 요약

worktree(`/home/Uihyeop/agent_setting-wt/config-sealing`) 안에서 전량 재실행(conductor
독립 재검증, 아래 §6 참고):

| Suite | 결과 |
|---|---|
| `utilities/capability_route.test.py` | 18 passed |
| `utilities/dispatch_node.test.py` | 20 passed |
| `utilities/dispatch_contract.test.py` | 10 passed (회귀) |
| `utilities/worker_route_guard.test.py` | 13 passed (회귀) |
| `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` | 3종 전부 PASS |
| `utilities/dispatch-route.test.sh` | PASS (selector 1단계 의미 불변 회귀 확인) |
| `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` | 3종 각 8 pass / **1 fail** (`test_route_consumer_and_missing_evidence_refusal`, exit 73) |

sd45 3종의 실패는 **base `ecd3acd8`에서 detached worktree로 재현했을 때도 동일하게 발생**함을
확인했다 — SD-68 diff가 만든 회귀가 아니라 기존 wrapper-subprocess/env fixture 이슈다(회귀 0
성립).

라이브 acceptance 스모크(`compile_route`/`verify_route` 직접 호출)로 ①②③과 "absent config →
digest `None` + 전 노드 `unspecified`" 경로를 추가로 확인했다.

## 5. 운영상 특이사항 (있는 그대로 기록)

- **plan 스테이지**: codex 시도가 read-only spec-marker 가드에서 BLOCKED → claude로 fallback,
  PASS.
- **execute 스테이지**: 설계상 harness는 `execute=codex`(config affinity)였으나 실제 실행은
  claude로 이탈했다. 기록된 사유: Codex의 workspace-write 샌드박스가 linked-worktree의 git
  메타데이터를 read-only로 취급해 커밋이 막힘. SD-68 자신이 배선한 "soft deviation, 사유 기록"
  계약과 부합하는 사례.
- **test 스테이지**: codex(deep reviewer) 시도가 아티팩트 영속화 단계에서 BLOCKED(spec-read/Read-tool
  마커 게이트). conductor가 stdout에서 codex 판정을 salvage하고, 전체 스위트 + baseline 분류 +
  라이브 acceptance 스모크를 독립적으로 재실행해 동일한 PASS 판정에 도달했다(salvage 판정과
  독립 재검증 판정이 일치).
- **미해결로 열어둔 항목(이번 사이클 범위 밖)**: namespace-local dead attempt row 3건
  (plan-codex, plan-claude, test-codex)이 reconcile되지 않은 채 audit 기록으로 남아 있다.
  reconcile이 terminal heartbeat 없는 namespace-local pid에 대해 fail-close하는 알려진 갭 때문이며,
  v18/SD-70-71 영역으로 이번 SD-68 사이클 소관이 아니다.

## 6. 범위 밖으로 확인된 항목 (건드리지 않음)

selector 캐스케이드 의미 변경, `profiles/dispatch-defaults.yaml`의 **값** 변경,
worker-route-guard, wrapper 3종의 신규 검증 게이트, 권한 분류기, `spec/**` 편집 — 전부 diff에
포함되지 않았음을 확인했다.

## 7. 결론

Acceptance ①~⑤ 전부 PASS, 회귀 0(사전 존재 실패는 baseline 동일 확인). 정규화 파싱 digest
결정이 false-churn 방지를 실증적으로 입증했고, soft·차단 없음 계약(SD-22 우선순위 불변)이
유지되었다. SD-68 완료.
