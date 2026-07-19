# evidence-autobind 사이클 결과 보고 (최종 상태: FAIL)

## 무엇을 만들었고 어디에 있는가

브랜치 `evidence-autobind`(base `5972a61d`) 위에 커밋 `1685cd3d` 하나로 구현되어 있습니다.
워크트리는 `/home/Uihyeop/agent_setting-wt/evidence-autobind`이고, **main에는 병합·push되지 않았습니다.**

목표는 depth-2 분사(`--start`)가 자격 증거(evidence) 플래그 없이도 통과하도록, 두 경로로 증거를 자동으로 채워 넣는 것이었습니다.

1. `utilities/dispatch-node.py` — route record 안의 이미 검증된(checked) 증거 튜플을 찾아서, 그 값을 자동으로 각 어댑터 래퍼의 인자(`--launch-authority`, `--parent-harness`, `--parent-transport`, `--parent-sandbox`, `--nested-eligibility`, `--eligibility-source`, 필요시 `--eligibility-failure-class`)로 넘겨줍니다. 호출자가 같은 값을 명시하면 통과시키고, 값이 다르면 실행 전에 에러로 멈춥니다.
2. 세 어댑터 래퍼(`adapters/claude/codex/opencode/bin/dispatch-headless.py`) — 증거 플래그가 비어 있는 depth-2 `--start`에서는 래퍼 내부에서 자격 판정 프로브(`utilities/nested-dispatch-eligibility.py`)를 직접 돌려서 그 결과를 채워 넣습니다.

새 테스트 `utilities/dispatch_node.test.py`(17개)와 세 래퍼의 SD-45 테스트 확장(8개씩, 총 24개)을 포함해 커밋되어 있고, 기존 회귀 스위트(dispatch_contract, sd15, stage_dispatch_fallback, nested_dispatch_eligibility, dispatch-route) 전체가 실제로 통과함을 test 단계에서 확인했습니다.

## 왜 FAIL인가 — 확인된 결함 3건

test 단계(codex 하네스)가 정규 회귀 스위트를 모두 통과시킨 뒤, "게이트를 약화시키지 않았는가"를 별도로 적대적 검증했고, 여기서 확정된 문제 3건을 찾았습니다. 이 결함들은 "정상 경로가 깨졌다"가 아니라 "자격이 없어야 할 상황에서도 통과해버릴 수 있다"는 종류의 문제라 FAIL로 판정됐습니다.

**결함 1 — 프로브가 실패해도 "지원됨"으로 오인될 수 있음**
위치: `adapters/claude/bin/dispatch-headless.py:662-690`, `adapters/codex/bin/dispatch-headless.py:875-903`, `adapters/opencode/bin/dispatch-headless.py:754-782`
자격 판정 프로브를 실행한 뒤 그 프로세스의 종료 코드(`returncode`)는 확인하지 않고 JSON 안의 `status` 값만 봅니다. 그래서 프로브가 실제로는 실패(`exit 69`)했는데 반환한 JSON이 우연히 신원(identity) 필드는 일치하면서 `status=supported`라고 되어 있으면, 그대로 "지원됨"으로 받아들여 다음 단계(런칭 게이트)까지 통과해버립니다. 세 어댑터 모두에서 재현되었습니다.
**고쳐야 할 방향**: `status=supported`를 인정하려면 프로세스 종료 코드도 함께 성공(정상 종료)이어야 합니다. 다만 기존에 이미 있던 "checked unsupported/unknown을 rc 69로 받는" 처리는 그대로 유지해야 합니다 — 실패를 실패로 인식하는 경로는 건드리지 않고, "성공"만 종료 코드와 함께 이중으로 확인하면 됩니다.

**결함 2 — "명시적으로 unknown"과 "아예 안 준 것"을 구분하지 못함**
위치: 세 어댑터 각각 파서 기본값 부분(예: claude `:158-159`)과 프로브 트리거 조건 부분(예: claude `:652-655`)
사용자가 `--nested-eligibility unknown`을 명시적으로 줬을 때와, 아예 그 옵션을 주지 않았을 때가 파서 상태로는 똑같이 보입니다(둘 다 기본값 `unknown` + 빈 source). 그런데 원래 합의된 규칙은 "명시적으로 준 증거(설령 unknown이라도)는 절대 내부 프로브로 덮어쓰지 않는다"였습니다. 지금 구현은 이 둘을 구분하지 못해서, 사용자가 일부러 "모르겠다"고 명시한 값을 내부 프로브가 "지원됨"으로 덮어써버릴 수 있습니다.
**고쳐야 할 방향**: 파서에서 "이 옵션이 실제로 argv에 나타났는지" 출처(provenance)를 별도로 추적해야 합니다. 단순히 최종 값이 기본값과 같은지가 아니라, 사용자가 그 플래그를 실제로 입력했는지를 기억하는 방식이 필요합니다.

**결함 3 — record의 실패 사유가 비어 있으면 충돌 검사를 건너뜀**
위치: `utilities/dispatch-node.py:136-142`(`bind_dispatch_evidence`)
route record 쪽의 `failure_class`가 비어 있을 때는 애초에 비교 대상에서 빠져버려서, 호출자가 `--eligibility-failure-class forged` 같은 임의의 값을 명시적으로 넘겨도 충돌로 잡히지 않고 그대로 통과합니다. (`--eligibility-failure-class forged`로 재현 확인.)
**고쳐야 할 방향**: 이 플래그도 항상 비교 대상에 포함시키되, 양쪽이 모두 비어 있을 때만 출력에서 생략하면 됩니다. "비교하지 않음"과 "비교했는데 둘 다 비었음"은 다른 얘기입니다.

## 참고 — 이번 결함과 무관한, 이미 있던 환경 문제

`AGENT_DISPATCH_JOBS` 관련해서 SD-45 테스트 스위트 중 1개가 rc 73으로 실패하는 현상이 있었는데, 이건 이번 구현과 무관합니다. 이 report 워커 자신이 depth-2 중첩 워커라서 전역 `AGENT_DISPATCH_JOBS` 레지스트리를 이미 물려받은 상태이고, 테스트가 자체 `--jobs` fixture 경로를 쓰려다 그 전역 값과 충돌하는 구조적 문제입니다. base 커밋(`5972a61d`)의 순수 사본으로도 똑같이 재현되어, 이번 변경이 만든 회귀가 아니라 사전에 존재하던 환경 문제임을 확인했습니다.

## 잔여 리스크 — 문제 아님으로 판단

depth-2 route 노드라면 `--action`(dry-run/register 포함)과 무관하게 항상 증거 바인딩을 시도하는 부분은, 현재 `capability-route.py`의 compile/verify 계약상 depth-2 노드는 항상 checked 증거 체인을 갖고 있어야 하므로 실질적으로 문제가 되지 않는다고 test 단계가 판단했습니다. 앞으로 컴파일러가 non-start 액션에 대해 의도적으로 증거를 생략하는 방향으로 바뀐다면 그때 맞춰 조정이 필요하지만, 지금 시점에는 안전한 fail-loud입니다.

## FIX-FORWARD 순서 (depth-0 main에서 진행)

1. 세 어댑터 래퍼의 내부 프로브 결과 수용 조건에 `subprocess.run(...).returncode` 확인을 추가해 "성공적으로 완료된 프로브의 supported"만 인정하도록 수정 (결함 1).
2. 세 어댑터 래퍼 파서에 `--nested-eligibility`/`--eligibility-source`가 argv에 실제로 나타났는지 출처를 추적하는 로직을 추가해, 명시적 `unknown`이 내부 프로브에 덮어써지지 않도록 수정 (결함 2).
3. `utilities/dispatch-node.py`의 `bind_dispatch_evidence`에서 `--eligibility-failure-class`를 항상 비교 대상에 포함시키고, 둘 다 빈 값일 때만 출력에서 생략하도록 수정 (결함 3).
4. 위 3건 수정 후 test 단계가 사용한 적대적 검증 3종(프로브 rc 69 + supported JSON, 명시적 unknown 유지 여부, 빈 record failure_class + 명시적 값 충돌)을 재실행해 확정 통과를 확인.
5. 정규 회귀 스위트 전체(dispatch_node.test.py, dispatch_contract.test.py, 세 어댑터 sd15/sd45, stage_dispatch_fallback, nested_dispatch_eligibility, dispatch-route) 재통과 확인 — `AGENT_DISPATCH_JOBS`는 unset 상태로 실행.
6. 이 사이클에서는 실행하지 않은 g10 드릴(evidence 플래그 없는 depth-2 fixture)을 depth-0 통합 검증에서 실행해 수용 기준을 최종 확인.

## 재시도하지 않고 여기서 마감하는 이유

execute 단계는 `source_commit 5972a61d` 정확 일치에 고정(pin)되어 있는데, 지금 워크트리 HEAD는 구현 커밋 `1685cd3d`로 이미 이동했습니다. 이 상태에서 같은 사이클 안에서 execute를 재시도하면 worker-route-guard가 구조적으로 거부하고, `git reset --hard`로 되돌리는 것도 금지되어 있습니다. 그래서 이번 사이클은 재시도 대신 위 fix-forward 목록으로 정직하게 FAIL 마감하고, 실제 수정은 depth-0 main에서 진행합니다.
