# 최종 보고 — selector-paths: 어댑터 프로젝션 selector 경로 해석 수정

- slug: `selector-paths-report` · intensity: standard · capability: autopilot-code (dev/refactor)
- 커밋: `35d60fc1` · 브랜치: `selector-paths` · 워크트리: `/home/Uihyeop/agent_setting-wt/selector-paths`

## 1. 문제

`utilities/dispatch-route.sh`는 SD-23에 따라 읽기 전용(read-only) selector이며,
`adapters/{claude,codex,opencode}/utilities/` 아래에 **심볼릭 링크**로 프로젝션되어
각 어댑터 표면에서도 동일 스크립트가 호출된다.

이 스크립트는 내부 헬퍼(`dispatch-defaults.py`, `usage-check.sh`, `model-map.sh`) 경로를
`$(dirname -- "$0")` 기반으로 계산했는데, 이 방식은 **심볼릭 링크를 따라가지 않는다.**
따라서 `adapters/<harness>/utilities/dispatch-route.sh` 형태의 프로젝션 경로로 호출되면:

- `dirname "$0"` → `adapters/<h>/utilities` (프로젝션된 디렉터리, 실제 저장소 루트 아님)
- 이 값을 기준으로 한 상위 climb(`../`) → `adapters/<h>` (저장소 루트가 아님)

결과적으로 L103–104의 `model-map.sh` 경로 계산이 하드 브레이크되어
`.../adapters/<h>/adapters/<fam>/bin/model-map.sh: not found`가 발생했고,
`set -e`가 이 커맨드 치환 실패를 잡지 못해 `exact_model_id=`/`adapter=` 값이
**조용히 비어버리는(silent corruption)** 문제였다. L28/L38(`dispatch-defaults.py`,
`usage-check.sh`)은 `utilities/` 전체가 미러 심볼릭 링크된 우연 덕분에 그동안 동작했을 뿐,
동일한 취약점을 안고 있었다.

## 2. 수정 내용 (커밋 `35d60fc1`, 2개 파일)

**`utilities/dispatch-route.sh`**
- 인자 검증 블록 직후에 `$0`의 실제 경로를 한 번 해석하는 블록 추가:
  `readlink -f`로 심볼릭 링크를 정규화하고(`-f` 미지원 시 기존 `$0` 방식으로 폴백),
  `self_dir`(헬퍼 디렉터리)와 `repo_root`(저장소 루트)를 미리 계산.
- L28, L38, L103, L104의 4곳 인라인 경로 계산을 위에서 계산한 `self_dir`/`repo_root`
  참조로 교체.
- POSIX/dash 클린, 로직·cascade·출력 포맷·종료 코드 변경 없음. `dispatch-defaults.py`는
  이미 `os.path.realpath(__file__)`로 자체 해석하므로 손대지 않음(범위 외 유지).

**`utilities/dispatch-route.test.sh`**
- 기존 마지막 `echo 'dispatch-route: PASS'` 직전에 프로젝션 표면 회귀 테스트 블록 추가:
  claude/codex/opencode 3개 프로젝션 경로로 `--stage test --capability autopilot-code
  --maker-family gpt` 호출 후 `status=eligible` + `adapter=` 라인 존재를 검증하고,
  `claude` 프로젝션으로 `--stage plan` 호출해 `adapter=codex` + `role=deep maker`를 검증.
  기존 어서션과 `DISPATCH_DEFAULTS_CONFIG` 픽스처 격리는 모두 보존.

총 변경 규모: 실행 로직 약 10줄 + 테스트 블록. `dispatch-defaults.py`는 무변경.

## 3. 검증 근거 (독립 code-test 스테이지, PASS)

| 항목 | 결과 |
|---|---|
| `sh -n` / `dash -n` (양 파일) | PASS — 모두 exit 0 |
| `sh utilities/dispatch-route.test.sh` | PASS — `dispatch-route: PASS` |
| 3-어댑터 프로젝션 (`--stage test ... --maker-family gpt`) | PASS — 3개 모두 `status=eligible`, `adapter=` 존재, `not found` 없음 |
| 프로젝션 `--stage plan` (claude) | PASS — `adapter=codex`, `role=deep maker` |
| 경계 가드 `tools/check-adaptation-boundary.sh` | PASS — exit 0 (WARN 103건은 기존에 문서화된 허용 항목, 이번 변경과 무관) |
| `dispatch_contract.test.py` | PASS — 10 tests OK |
| `dispatch_node.test.py` | PASS — 17 tests OK |
| sd15 × 3 (claude/codex/opencode) | PASS 전부 |
| sd45 × 3 (claude/codex/opencode) | 각 1건 실패 (`test_route_consumer_and_*_refusal`, rc=73) — 아래 참조 |

검증은 execute 단계 실행(`dev_logs/execute-claude.md`)과는 별도로 독립 `code-test`
스테이지에서 재실행되었으며, 결과가 일치한다.

## 4. sd45 사전 존재 실패 — 회귀 아님 (확인됨)

세 어댑터의 `dispatch-headless.sd45.test.py`에서 각각 1건
(`test_route_consumer_and_{missing_evidence,scope,capability_reselection}_refusal`,
`AssertionError: 73 != 0`)이 실패한다.

독립 test 스테이지가 `git archive HEAD^`로 부모 커밋(`321792e5`, selector-paths 수정 이전)을
격리된 임시 트리로 추출해 동일 커맨드(`adapters/claude/bin/dispatch-headless.sd45.test.py`)를
재현한 결과, **동일한 실패 이름·동일 어서션·동일 rc=73·동일 1건 실패**가 그대로 재현되었다.
즉 이 3건은 selector-paths 변경으로 유발된 회귀가 아니라 기존부터 존재하던 실패이며,
이번 수정 범위(SD-23 read-only 경로 해석) 밖의 사안이다.

## 5. 잔여 리스크

- 이번 변경으로 신규 도입된 리스크는 실질적으로 없음 — 경로 해석만 바뀌었고 cascade/출력/종료
  코드는 프로젝션·비프로젝션 경로 양쪽에서 동일함을 확인.
- sd45의 3건 사전 존재 실패는 이번 사이클 범위 밖이며 별도 후속 작업 대상.
- SD-68(route compile sealing)은 이번 사이클의 계획된 범위 외(out-of-scope) 항목으로,
  다음 사이클로 이월.

## 6. 변경 파일

1. `utilities/dispatch-route.sh` — 경로 해석 블록 추가, 4곳 헬퍼 경로 교체.
2. `utilities/dispatch-route.test.sh` — 프로젝션 표면 회귀 테스트 블록 추가.
