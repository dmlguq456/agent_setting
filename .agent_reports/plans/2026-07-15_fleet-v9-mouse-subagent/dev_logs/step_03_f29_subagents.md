# Step 3 — F-29 서브에이전트 관측

## 변경
- `model.py`: `SubAgent` dataclass 신설(`agent_type`/`active`/`started_at`/`source`) + `Session.subagents: Optional[list] = None`(additive-only). `classify_session`은 `subagents`를 참조하지 않음(백본 불가침, `test_session_existence_unaffected_by_subagents`로 고정).
- `collectors/opencode.py`: `_child_sessions(con, sid)` 신설(`parent_id=?` SELECT, 예외 시 `None`). `enrich()`가 **`_query`가 고른 row가 진짜 top-level일 때만**(`row[-1] is None` = `parent_id IS NULL`) 자식 조회 — R3-2(fallback이 자식이면 손자 조회 방지) 완화. 이미 열린 커넥션 재사용(추가 connect 0).
- `collectors/claude.py`: `_tail_subagents(path)` 신설 — `_tail_ai_title`과 동일한 역방향 성장 스캔(×8) + 독립 `_SUBAGENT_CACHE`((mtime,size) 키). `tool_use`(name=="Task")↔`tool_result`(`tool_use_id`) 짝짓기: 미짝 `tool_use`=활성, 짝 있음=완료(`active=False`). R3-1 재평가대로 "미짝 tool_use=활성"은 역방향 tail의 append-only 구조상 정확 — 창 안의 tool_use 뒤에 오는 tool_result는 필연적으로 창 안.
- `collectors/codex.py`: **무변경** — 확정 소스 없음, 코드 추가 없음(정직한 결손, `—`).
- `render.py`: `_ICON_SUBAGENT`(★ PRD 제안 `⚡`는 기존 `⚡untracked` 게이트 배지와 충돌해 `🔬`로 교체 — 아래 "PRD 이탈" 참조) · `_active_subagent_count` · `_subagent_row`(`└🔬<type> ⏳<경과>`) 신설. `_build_lines` 세션 루프에서 세션 자기 행 직후, dispatch 자식 행 이전에 서브에이전트 행 삽입(활성=항상, 완료=`_SHOW_ALL`에서만 — F-18b dim 계열). `_session_row` suffix 체인에 `🔬N` 배지(`▾N`과 같은 예약 순서, name zone 침범 안 함). legend에 `🔬N sub-agents` 등장 시만 노출(F-12). pulse 라인(`fleet ... working/idle`)은 무변경 — 서브에이전트 카운트 혼입 없음.
- `fleet.py`/`--json`: 별도 코드 변경 없음 — `Session.to_dict()`가 `dataclasses.asdict()`를 쓰므로 `subagents`(SubAgent 리스트)가 자동으로 additive 직렬화됨.

## PRD 이탈 사항 (기록 필수)
prd.md:232가 "🧠는 이미 두 의미로 포화, ⚡는 신규 — 충돌 없음"이라 전제했으나 **실코드 확인 결과 `⚡`는 이미 render.py의 스펙게이트 `⚡untracked` 배지로 사용 중**이었다(grep 실측). PRD 전제가 틀렸으므로 그대로 채택하면 `🧠`와 같은 이중 의미 문제를 새로 만든다 — `_WIDE`에 이미 등록돼 있고 미사용인 `🔬`로 대체했다. 단일 상수(`_ICON_SUBAGENT`)로 격리해 추후 교체 용이(R3-4 완화 그대로 적용).

## 검증
```
python3 -m unittest discover -s tools/fleet/tests -q
→ Ran 451 tests. FAILED(failures=1) — 유일한 실패는 test_mirror_parity(render.py/model.py/collectors/{claude,opencode}.py + 신규 tests/test_f29_subagents.py 미러 드리프트, Step 6에서 rsync). 그 외 450건 OK, 신규 실패 0.

python3 -m unittest tools.fleet.tests.test_f29_subagents -v   → Ran 14 tests, OK (OpenCodeSubagentTest×5, ClaudeSidechainTest×4, NoRegressionTest×5)

for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once; done   → 3폭 정상 렌더 (현재 실 서브에이전트 없어 서브 행 미노출 — 정상)
python3 tools/fleet/fleet.py --json > /tmp/v9_step3.json && python3 -c "...'subagents' in s..."   → subagents key present: True
```

fixture 세션(활성 2 + 완료 1)으로 `_build_lines` 직접 호출해 `/tmp/v9_step3_{60,120,168}.txt`에 프리뷰 부록(`--once`의 실 데이터에는 서브에이전트가 없어 실물 렌더가 안 보이므로).

## 디자인팀 critic
`/tmp/v9_step3_{60,120,168}.txt` (프리뷰 부록 포함) → critic 요청. 결과는 `_internal/dev_reviews/design_critic_step3.md`에 별도 기록.

**반영**: critic §2(트리 커넥터) 수용 — `_subagent_row(sa, is_last)`로 확장, 마지막 행만 `└` 나머지는 `├`(연결된 그룹으로 판독). 신규 테스트 `test_stacked_subagent_rows_use_connected_tree_branches`로 고정. critic §5(폭 미리플로우 우려)는 재검증 결과 **프리뷰 스크립트가 `layout=_layout_mode(w)`를 누락**한 결함으로 판명(실 `--once`/`_draw` 경로는 정상) — `layout` 포함 재검증(v2 프리뷰, 같은 파일에 부록) 및 `▾N`+`🔬N` 결합 케이스로 폭 60/120/168 전부 미초과 확인. §1·3·4는 코드 변경 불요.

## acceptance
- A3-1(백본 불가침): `test_session_existence_unaffected_by_subagents`, `test_parse_failure_omits_subrow_entirely`.
- A3-2(소스 순서 · Codex 미확정 시 `—`): OpenCode 자식 조회 구현, Claude sidechain 구현, Codex 무변경(코드 자체가 "추측 없음"의 증거).
- A3-3(`└🔬` 서브 행 + `🔬N` 배지 + `a` 토글 dim + pulse 혼입 0): `test_source_absent_omits_subrow_entirely`, `test_subagents_never_enter_pulse_counts`, render.py 구현.
- A3-4(zero-injection · `--json` additive · 소스 부재 → 서브 행 생략): `test_json_key_is_additive`, `test_db_without_agent_column_degrades_to_none`.

## 안전 규칙 준수 (§0)
실세션 스폰·시그널 0. sqlite DB/jsonl transcript는 전부 `tempfile.TemporaryDirectory` fixture, `OPENCODE_DB`/`CLAUDE_CONFIG_DIR` env override로 실 상태 완전 격리.
