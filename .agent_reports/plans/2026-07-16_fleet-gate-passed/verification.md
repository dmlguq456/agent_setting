# 검증 로그 — fleet gate-통과 표시 (2026-07-16)

브랜치 `fleet-gate-passed` / worktree `/home/Uihyeop/agent_setting-wt/fleet-gate-passed`

## 1. 신규 테스트 — `tools/fleet/tests/test_f30_gate_passed.py` (36건)

```
$ python3 -m unittest discover -s tools/fleet/tests -t . -p "test_f30_gate_passed.py"
Ran 36 tests in 0.038s
OK
```

픽스처는 **실물**이다: `fixtures/completion/rt-5fd84b9bcf8a799c/`(SD-56이 남긴 저장소 최초
실사용 marker 4건 verbatim 복사) + `fixtures/route/real_sd13_staged.json`(그 marker들이 실제로
쓰여진 route record = `.dispatch/logs/stage-dispatch-v13.route.json`). 통과 경로는 프로덕션
바이트로, 무주장 경로는 그 실물을 tempdir에서 최소 변형해 증명한다.

| 요구 케이스 | 테스트 | 결과 |
|---|---|---|
| 통과 marker 픽스처 | `test_real_markers_all_pass` (4노드 subTest) | True |
| route_id 불일치 | `test_route_id_mismatch_is_no_claim_not_failure` | None (False 아님) |
| hash 불일치 | `test_route_hash_mismatch_is_no_claim` | None |
| 부재 | `test_absent_marker_is_no_claim`, `test_absent_route_dir_is_no_claim` | None |
| garbage json | `test_garbage_json_never_raises` (6종 subTest) | None, 무예외 |
| 이력 최신 우선 | `test_canonical_outranks_stale_history`, `test_history_latest_wins_when_canonical_absent`, `test_history_sequence_is_numeric_not_lexical` | 최신만 authoritative |

추가로 pin한 것:

- `test_optional_writer_fields_are_not_required` — 실물 marker에 `sequence`/`completed_at`/
  `schema_version`이 **없음**을 assert. writer(`capability-route.py:241`)는 앞 둘을 쓰는데
  실물엔 없다 → 필수로 요구했다면 이 기능이 읽으려는 증거 자체를 거부했을 것.
- `test_gate_passed_is_independent_of_state` — marker 있는 `pending` 노드는 통과로,
  marker 없는 `done` 노드는 무주장으로. 두 차원이 서로 파생 아님을 증명.
- `test_build_views_does_no_io` — `os.stat`/`open`을 예외로 패치한 채 `build_views` 호출.
  PURE 계약 유지(마커 읽기는 `resolve_gate_marks`로 분리).
- `test_read_only_no_writes_to_completion_tree` — 호출 전후 mtime_ns 동일.
- `test_node_id_never_traverses` — `../../plan` 거부.
- `test_mark_width_is_accounted_when_cropping` — 아래 §5 참조.

## 2. 전체 fleet 회귀

```
$ python3 -m unittest discover -s tools/fleet/tests -t .
Ran 555 tests in 17.403s
OK
```

기준선 519 → 555 (= 519 + 신규 36). **회귀 0.**

중간에 `test_mirror_parity`가 1건 실패했고(예상된 mirror drift), rsync 동기 후 해소됨.

## 3. `--json` 스모크 — 기존 키 불변 + additive

새/구 코드의 전체 키 경로 집합을 비교(구 코드 = `git archive HEAD`로 `/tmp/head_tree`에 추출):

```
removed (must be empty): []
added   (must be gate_passed only): ['/route[]/nodes[]/gate_passed']
```

live 상태 실측 — route 7건 중 marker를 가진 `rt-5fd84b9bcf8a799c`만 4노드 전부
`gate_passed: true`, 나머지 6건은 전부 `null`(무주장). `done` 상태인데 marker 없는 노드가
`false`로 새지 않음을 실데이터로 확인.

## 4. 실렌더 (live, 접힘 해제)

```
▾ [code·dev·standard] rt-5fd84b9b — 4/4 nodes
  plan ✓ ⊸ › execute ✓ ⊸ › test ✓ ⊸ › report ✓ ⊸
    mark segs: [(' ⊸', 'gate_t'), (' ⊸', 'gate_t'), (' ⊸', 'gate_t'), (' ⊸', 'gate_t')]
  gates: code-plan ⊸, code-execute ⊸, code-test ⊸, code-report ⊸    # a 토글에서만
```

표식은 **별도 세그먼트**이고 색 키가 `gate_t`(green-dim) — 노드 텍스트의 `dim`과 다른 차원.
이 route는 4/4 done이라 §5.4 기본 접힘(`▸`) 대상이므로 `--once` 기본 출력엔 안 보이고,
펼쳤을 때만 나온다(설계대로).

## 5. 폭 검사 — `COLUMNS={60,120,168} --view process --once`

| COLUMNS | 넘침 |
|---|---|
| 60 | 2 (**기존**, 아래) |
| 120 | 0 |
| 168 | 0 |

60열의 2줄은 `git archive HEAD` 기준선에서 **동일하게 재현**된다:

```
'  fleet ⠋ 4 working   ● 5 idle   ○ 1 detached   ↳ 1 job (1 working)'   (67열)
'  🧠 mem  +35 added(15w·20d) · 31 expired · 3 pruned · last distill 4m'  (70열)
```

둘 다 pulse/mem **헤더 행**이며 route 카드가 아니다 — 이번 변경의 기여분은 0이고, 이번
스코프(gate 표식) 밖의 기존 결함이다. 정직하게 "넘침 0"이 아니라 "신규 넘침 0"으로 보고한다.

표식 폭 회계는 별도로 pin했다(`test_mark_width_is_accounted_when_cropping`): 같은 flow가
표식 없이 33열/표식 포함 37열이므로 36열에서 갈린다 — 표식을 폭 계산에서 뺐다면 folder가
`plan`을 유지한 뒤 36열 카드에 37열을 그렸을 것(표식당 1열 조용한 넘침). 이 경계를 실제로
assert한다.

## 6. mirror parity

```
$ rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
$ diff -r --exclude=__pycache__ tools/fleet/ adapters/claude/tools/fleet/
(무출력 = 바이트 동일)
```

## 7. 금지 사항 준수

- **live `.dispatch/completion/` 쓰기 없음** — 작업 전후 mtime 동일:
  `plan 09:53:21 / execute 10:56:14 / test 11:19:20 / report 11:24:07` (최초 조사 시점과 일치).
- **route record 쓰기 없음** — `stage-dispatch-v13.route.json` mtime `09:19:23` 불변.
- **route.py read-only 정적 게이트** (docstring이 선언한 불변식) 직접 실행:
  ```
  $ grep -nE "open\([^)]*[\"'][rbt]*[wax]|\.write\(|\.writelines\(|os\.replace|os\.rename|
             shutil\.(copy|move)|mkdir|makedirs|unlink|remove\(" tools/fleet/route.py
  (none — read-only invariant holds)
  ```
  `open()`은 2곳 모두 읽기 모드.
- **실세션 스폰·signal 없음**, depth-2 분사 없음.
- 산출물은 전부 artifact_root 아래에만 작성(worktree에 산출물 없음).
