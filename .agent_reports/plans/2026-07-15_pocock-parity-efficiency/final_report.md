# 최종 보고서 — portable Pocock parity와 context efficiency

## 결론

계층을 `core/capabilities/roles → {Claude, Codex, OpenCode}`로 복원하고 세 adapter를 동급 sibling으로 구현·활성화했다. Pocock/Ponytail의 output 압박만으로 절감을 주장하지 않고, 먼저 always-loaded bootstrap, 중복 discovery, 반복 훅 주입을 줄이는 전략으로 전환했다.

현재 결과는 **정적 context footprint GREEN**이다. 실제 token·cache·비용 절감률은 아직 미증명이다.

## 바뀐 구조

- 공유 의미, 호출 그래프, 품질·안전·비용 불변식은 portable core가 소유한다.
- Claude, Codex, OpenCode는 각 runtime 문법으로 같은 portable capability를 구현한다. Claude projection은 다른 adapter의 생성 원본이나 완료 대리자가 아니다.
- 세 runtime 모두 공통 `builder` 프로필을 사용한다: 14 capabilities, 7 portable roles, 26 modes.
- 활성 surface 하나라도 미검증이거나 필요한 fallback이 없으면 전체를 `PARTIAL`로 유지하는 규칙을 guard에 반영했다.

## 정적 footprint 결과

| Surface | 이전 | 현재 | 변화 |
|---|---:|---:|---:|
| Claude bootstrap | 11,821 B | 4,632 B | -60.8% |
| Codex bootstrap | 26,189 B | 7,646 B | -70.8% |
| OpenCode bootstrap | 17,153 B | 6,045 B | -64.8% |
| 합계 | 55,163 B | 18,323 B | -36,840 B / -66.8% |

- 활성 Codex native Skill metadata: 정규화 1,946 chars, runtime path 포함 2,338 chars, duplicate names 0.
- 보수적으로 27개 전체 tree를 재도 각 adapter metadata budget 7,000 chars 이하이다.
- normal/unknown/repeated/UserPromptSubmit 기본 훅 주입은 0 chars이다.
- 저장 baseline보다 5%를 넘는 증가는 strict check가 실패시킨다.
- repository에는 guard·projection·측정 코드가 늘었지만, 이 파일 수/디스크 크기는 always-loaded prompt 크기와 다른 지표다.

## 런타임 동등성

| Runtime | Profile | Active state | Duplicate | 적용 시점 |
|---|---|---|---:|---|
| Claude | builder / 14 | fresh | 0 | 새 세션·Skill reinvoke |
| Codex | builder / 14 | fresh | 0 | 새 세션·auto-detect reinvoke |
| OpenCode | builder / 14 | fresh | 0 | runtime restart |

Codex의 native+plugin 이중 discovery는 제거했다. plugin은 배포용 generated artifact로 검증하되 활성 runtime에는 native builder profile만 둔다. 구형 전체 투영이 남긴 profile 밖 agent link도 안전하게 탐지·제거하며 사용자 소유 파일은 보존한다.

## 왜 이것만으로 실제 절감률을 말할 수 없는가

기존 진단처럼 output-side 압박은 전체 세션 비용 중 일부만 건드린다. input context와 cache creation이 지배적인 세션에서는 output 감소가 희석될 수 있고, reasoning model에서는 짧게 쓰라는 압박이 재시도나 내부 추론 비용을 늘릴 수도 있다. 따라서 code line, byte, directive count를 token이나 청구액으로 환산하지 않는다.

이번 변경은 “손해를 막는 바닥”을 넘어 고정 입력 자체를 줄였지만, 효과 크기는 실제 세션으로만 판정한다.

## 다음 절감·효율화 전략

1. **고정 입력 우선**: 이번 bootstrap 축소와 공통 builder profile을 기준 상태로 고정한다. 전체 capability는 설치하되 필요한 pack만 discovery하게 한다.
2. **progressive disclosure 강화**: runtime 시작 시 이름·description·path만 노출하고 Skill body, mode 상세, edge case는 선택 후 읽는다. core 문서는 읽기 빈도를 측정한 뒤 cold reference만 추가 분리한다.
3. **cache 친화성**: bootstrap/source order를 안정적으로 유지하고 세션마다 변하는 값은 고정 prefix 뒤로 보낸다. cache-create/read를 별도 측정해 문서 압축보다 큰 레버인지 판정한다.
4. **반복 주입 금지**: ordinary turn은 0 bytes를 유지한다. 검증된 tight/critical transition에서만 1회 240 bytes 이하 directive를 허용하며 intensity, model role, dispatch, QA, safety는 낮추지 않는다.
5. **production paired experiment**: Claude·Codex·OpenCode 각각 최소 30 paired sessions를 같은 task·model role·intensity로 교차 실행한다. uncached input, cache create/read, output, total billable tokens/cost, latency, retry, completion quality를 분리한다.
6. **채택 기준**: quality·required-tool·test·safety 비열화를 먼저 배제한 뒤 runtime별 순절감과 신뢰구간을 보고한다. 통합 평균으로 특정 runtime의 회귀를 숨기지 않는다.

## 검증

- portable guards: 355/0.
- adapter boundary negative controls, generated projection, routing, Skill conformance, context strict 통과.
- profile activation과 transaction/rollback/recovery suite 통과.
- Claude/Codex/OpenCode strict runtime doctor 통과; Codex adapter doctor와 OpenCode native projection check 통과.
- drill은 token을 소비하므로 자동 실행하지 않았다.

## 공식 runtime 근거

- Codex Skills와 progressive disclosure: https://learn.chatgpt.com/docs/build-skills.md
- Codex `AGENTS.md` instruction discovery: https://learn.chatgpt.com/docs/agent-configuration/agents-md.md
- Claude Skill progressive disclosure: https://docs.claude.com/es/docs/agents-and-tools/agent-skills/best-practices
- OpenCode native Skills/rules: https://opencode.ai/docs/skills · https://opencode.ai/docs/rules
