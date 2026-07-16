# Skill-Design Refactor — Pipeline Summary

## 2026-07-16 · v5 GREEN

v4의 main-context ownership을 worker 입출력까지 확장한다. portable worker
bootstrap은 one kernel + exactly one type + assigned contract이며, worker의
마지막 출력은 `artifact/verdict/blocker` 세 줄로 고정한다. changed files,
commands, logs, reasoning은 artifact에 남겨 main이 verbose body를 다시 받지
않는다.

Claude masked profile은 하네스 조립 입력을 실제로 줄이고, Codex/OpenCode는
명시적 full-bootstrap read를 제거한다. 다만 runtime이 project instruction을
자동 상속하는 부분은 physical masking으로 주장하지 않고 checked fallback으로
기록한다. 정적 bootstrap bytes만 측정하며 total-token/cost 절감률은 주장하지
않는다.

공통 kernel은 1,571 bytes이고 type 포함 입력은 support 1,862, review 1,878,
stage 1,906, owner 2,028 bytes다. custom prompt wrapping, route consumer,
artifact-root shadow guard, profile activation/build, three adapter dispatch,
generated projections, Skill conformance, adapter boundary, Codex/OpenCode
runtime doctor, strict context footprint가 통과했다.

## 2026-07-16 · v4 GREEN

primary entry routing을 `model proposal → user confirmation → capability-owned
execution`으로 닫았다. `WORKFLOW §0.4`의 agent-filled five-field 카드는 material
work 전에 한 번만 표시되고, read-only orientation은 제외되며, 이미 승인된
route/scope는 반복하지 않는다. 승인 후에는 depth-1 owner가 entry contract를,
depth-2 worker가 stage contract만 읽는다.

`harness-manifest.json` schema 2가 27개 capability의 invocation class와
`use_when`/`not_for`를 소유한다. 생성 분류는 entry-router 13,
parent-invoked 13, model-support 1이며 hand-owned TSV는 generated projection으로
전환됐다. generic/circular trigger와 top-level boundary 누락은 deterministic
conformance failure다.

Codex/OpenCode generated entry body는 full portable detail을 선행 투영하지
않는다. 대표적으로 Codex `autopilot-code`는 134줄/9,146자에서
46줄/2,687자로 줄었고 parent stage detail은 유지됐다. 구체적 trigger/boundary
때문에 full metadata는 6,019자, active Codex builder metadata는 3,205자로
증가했으나 7,000자 예산과 duplicate 0을 지켰다. 이는 main-context isolation과
정적 footprint 결과이며 token·billing·총 작업량 절감률 주장이 아니다.

generated projection, four-tree Skill conformance, strict context footprint,
clean-worktree adapter boundary, Codex/OpenCode installed runtime projection,
Claude metadata/plugin freshness가 모두 PASS하여 v4 상태는 GREEN이다.

## 2026-07-16 · v4 implementation started

Pocock의 user control과 harness의 semantic auto-routing을 `model proposal → user confirmation → capability-owned execution`으로 절충했다. 모든 material entry work는 agent-filled five-field 실행 확인을 한 번 거치며, 승인 이후 내부 stage는 재확인 없이 진행한다. read-only orientation/status/explanation은 제외하고 `direct`는 침묵하는 no-route가 아니라 명시적 예외로 표시한다.

최우선 optimization target은 aggregate token이 아니라 depth-0 main session context다. main은 compact entry metadata와 route/state/integration만 소유하고, full capability/Skill detail은 depth-1 owner와 depth-2 worker가 읽는다. v4 dev는 core response/workflow 계약, manifest-owned routing metadata, generated invocation policy, three-adapter metadata projection, conformance 및 active-context verification을 같은 cycle에서 닫는다.

## 2026-07-15 · v3 GREEN

portable source를 상위 의미 계층으로 복원하고 Claude·Codex·OpenCode를 동급 sibling adapter로 닫았다. 세 런타임은 모두 같은 `builder` 프로필(14 capabilities, 7 portable roles, 26 modes)로 활성화됐고 freshness는 `fresh`, duplicate discovery는 0이다. Codex의 구형 전체 투영 진단도 프로필 인식형으로 전환해 Claude 전체 트리를 암묵적 기준으로 삼지 않는다.

always-loaded bootstrap 합계는 동일 UTF-8 byte 기준 55,163에서 18,323으로 36,840 bytes(66.8%) 줄었다. 일반/unknown/repeated 훅 주입은 0 bytes이고 활성 Codex native Skill metadata는 정규화 기준 1,946 chars이다. 이는 정적 context footprint 결과이며 토큰·cache·청구액 절감률 주장이 아니다. 실제 절감 채택 판단은 세 런타임별 production paired sessions `n>=30`과 품질 비열화 확인 뒤에만 가능하다.

## 2026-07-15 · v3 back-jump

사용자 진단에 따라 v2의 완료 판정을 재개방했다. Pocock 원칙의 portable tenet와 Claude realization은 완료됐지만, Codex/OpenCode 활성 표면과 초기 컨텍스트 비용이 같은 기준으로 닫히지 않았으므로 전체 상태를 `GREEN`에서 `PARTIAL / dev in_progress`로 변경했다.

v3는 `core/`·`capabilities/`·`roles/`를 유일한 의미 정본으로 두고 Claude·Codex·OpenCode를 동급 sibling adapter로 정의한다. 구현 cycle은 세 adapter의 semantic outcome, runtime fallback/discoverability, bootstrap·skill metadata·hook injection budget을 함께 검증한다. 정적 footprint 감소는 즉시 보고하되, 실제 토큰/비용 절감률은 production paired sessions `n≥30` 전에는 주장하지 않는다.
