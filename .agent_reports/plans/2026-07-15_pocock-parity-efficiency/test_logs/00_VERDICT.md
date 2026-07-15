# 검증 판정

## 판정: GREEN

portable contract, 세 sibling adapter projection, 공통 `builder` 활성 프로필, context budget, 생성물, negative control이 통합된 메인 트리에서 통과했다. Claude·Codex·OpenCode 중 다른 adapter의 성공으로 대체하거나 미검증으로 남은 행은 없다.

## 증거

- `hooks/portable-guards.test.sh`: `PASS=355 FAIL=0` (verification runner).
- `tools/adaptation-guard.test.sh`: 7개 negative case, 테스트 전 상태 복원, 최종 green 통과.
- `tools/generated-projections.test.sh`: 29개 figure semantic test와 generated projection suite 통과.
- `tools/routing-contract.test.sh`: 전체 routing/bootstrap/delegation check 통과.
- `tools/skill-conformance/check.sh`: portable domain, 네 Skill tree, 26 invocation classification 통과.
- `tools/install/profile-activation.test.sh`: starter/builder/full profile, legacy-extra 제거, user-owned 보존 통과.
- `tools/install/runtime-activation.test.sh`: offline activation, duplicate 탐지, rollback, recovery, scope/source safety 통과.
- `tools/context-footprint.py --strict`: 모든 absolute/regression budget 통과, warning 0.
- 공통 runtime doctor: Claude/Codex/OpenCode 모두 `builder`, 14 capabilities, `fresh`, duplicate 0.
- Codex `preflight.sh doctor --runtime`: `runtime-projection:ok`, 최종 `status=ok`.
- OpenCode `preflight.sh headless --check`: native projection `check=ok`.
- `tools/generate.py --check`, plugin validator, Python `compile()`, `bash -n`, `git diff --check` 통과.

## 한계

- 독립 모델 QA가 아니라 결정론적 source/runtime 검증이다. 실패한 headless 시도와 inline fallback은 metrics에 기록했다.
- 정적 byte/character 감소는 실제 token, cache, 청구액 절감을 증명하지 않는다. 절감률 채택 게이트는 런타임별 production paired experiment `n>=30`과 품질 비열화 검증이다.
