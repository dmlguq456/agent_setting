# depth-2 stage worker — code-plan (harness-installer 사이클 3)

당신은 depth-2 stage worker 입니다. worktree `/home/Uihyeop/agent_setting-wt/harness-installer-hooks` (브랜치 `harness-installer-hooks`) 에서 **code-plan** 스테이지만 수행하고 산출물 파일만 남긴 뒤 종료합니다. depth-3 분사 금지.

## 배경

`agent_setting` repo — 포터블 에이전트 하네스를 Claude Code/Codex/OpenCode 에 배포하는 installer 작업. 현재 `.agent_reports/spec/harness-installer/prd.md` (v2) 가 spec. 사이클 1·2 로 Claude plugin 채널이 완결됐고(`adapters/claude/bin/sync-native-plugin.py` — skills 28 + agents 9 + hooks 2 채택), **INST-D-6** 이 이월시킨 spec 파이프 hook 3종의 `${CLAUDE_PLUGIN_DATA}` 재기준이 이번 사이클(사이클 3) 스코프입니다.

**먼저 Read 하세요** (spec-read 게이트 — `autopilot-code`/`autopilot-spec` 은 세션 내 실제 Read 없으면 hook 이 deny 합니다):
- `.agent_reports/spec/harness-installer/prd.md` (특히 §"plugin 채널 — 런타임별 스펙" 의 Claude 절 "postinstall 부재… `${CLAUDE_PLUGIN_DATA}`" 문단, §INST-OPEN-1 이력)
- `.agent_reports/spec/harness-installer/pipeline_state.yaml` (INST-D-6, dev: 이월 항목)
- `.agent_reports/plans/2026-07-13_harness-installer-impl2/final_report.md` §4 (INST-OPEN-1 확정 목록 — defer 3 사유: "`$AGENT_HOME/.spec-grounding` 에 write → `${CLAUDE_PLUGIN_DATA}` 재기준 배선 필요. cycle 2 self-contained 원칙을 흐리므로 별도 사이클.")
- `adapters/claude/bin/sync-native-plugin.py` (Claude plugin content generator — `HOOK_ADOPT`, `_HOOK_MATCHERS`, `_HOOK_SHELLS`, `hooks_json()`, `sync()`, `check()`, `check_file()`. 이 파일을 확장해 defer 3종을 포함시키는 게 핵심 산출물)
- 대상 hook 소스 3개 (canonical, repo-root `hooks/`):
  - `hooks/spec-skill-gate.sh` — PreToolUse(Skill). `AGENT_HOME` 을 `"$SCRIPT_DIR/../utilities/agent-home.sh"` 로 해석해 `$AGENT_HOME/.spec-grounding/${sid}__${key}` 마커를 **읽는다**(POSIX sh, `--agent-home` CLI 오버라이드 존재).
  - `hooks/spec-read-marker.sh` — PostToolUse(Read). 같은 `$AGENT_HOME/.spec-grounding/${sid}__${key}` 에 mtime 을 **쓴다**(`--agent-home` CLI 오버라이드 존재).
  - `hooks/spec-sync-nudge.sh` — PostToolUse(Edit|Write|MultiEdit). `AGENT_HOME` 은 python 헬퍼 실행 경로 해석에만 쓰고(파일 write 없음, read-only), spec-backed cwd 판정은 cwd 기준 `.agent_reports|.claude_reports/spec/pipeline_state.yaml` 탐색 — **이 hook 은 상태 파일을 안 씀** (read-only 불변식, 자체 주석에 명시). PLUGIN_DATA 재기준이 필요 없을 수 있음 — 직접 확인해서 판단하세요.
- `adapters/claude/settings.json` 의 세 hook 등록 라인(matcher: spec-skill-gate=Skill, spec-sync-nudge=PostToolUse Edit|Write|MultiEdit, spec-read-marker=PostToolUse Read) — plugin `hooks/hooks.json` 이식 시 이 matcher 를 그대로 반영.
- Claude Code 공식 문서 currentness: plugin 이 실행 시 노출하는 env 변수 `${CLAUDE_PLUGIN_ROOT}`(plugin 설치 경로, cache 내부·버전-ephemeral) 와 `${CLAUDE_PLUGIN_DATA}`(`~/.claude/plugins/data/<plugin-id>/` — 업데이트 생존, 영속 상태 저장용). WebFetch 로 `code.claude.com/docs/en/plugins-reference` 재확인해 두 변수의 정확한 의미·hook 실행 시점 노출 여부를 검증하세요(사이클 2 는 이미 이 문서를 근거로 `${CLAUDE_PLUGIN_ROOT}` 를 hooks.json command 경로에 썼음 — `hooks_json()` 참조).

## 이번 사이클 스코프 (PLUGIN_DATA 재기준)

1. **대상 확정**: `spec-skill-gate.sh`·`spec-read-marker.sh`·`spec-sync-nudge.sh` 3종 중 실제로 상태 파일을 읽고/쓰는 것이 무엇인지 코드로 재확인(위 소스 요약이 맞는지 직접 검증). `spec-sync-nudge.sh` 가 정말 read-only 라면 PLUGIN_DATA 재기준이 불필요할 수 있음 — 이 경우 이유를 plan 에 명시하고 스코프에서 제외 여부를 판단(단, hooks.json 이식 대상에서는 제외하지 않음 — 3종 모두 plugin 탑재 대상).
2. **경로 재기준 설계**:
   - hook 자신·헬퍼(`utilities/agent-home.sh` 등) 참조 경로는 plugin 안에서 `${CLAUDE_PLUGIN_ROOT}` 기준이 되도록(hooks.json 의 command 문자열이 이미 `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 형태 — 사이클 2 `hooks_json()` 참조. `agent-home.sh` 같은 상대 참조(`$SCRIPT_DIR/../utilities/`)가 plugin 트리 안에 실존해야 함 — `sync-native-plugin.py` 가 `utilities/` 도 같이 복사해야 하는지 확인).
   - **세션 marker 상태**(`.spec-grounding/*`) 는 plugin 실행 시 `$AGENT_HOME` 대신 `${CLAUDE_PLUGIN_DATA}` 를 써야 함(cache 는 버전-ephemeral 이라 세션 마커가 업데이트마다 날아가면 게이트가 매번 재-Read 를 강제하는 것 자체는 안전하지만, 의도는 "설치 생존 상태"이므로 PLUGIN_DATA 가 맞는 자리 — plan 에서 왜 CACHE 가 아니라 DATA 인지 한 줄 근거 남기기).
   - **wrapper 방식 검토**: canonical `hooks/spec-skill-gate.sh`·`spec-read-marker.sh` 본체를 직접 수정하지 않고(비스코프 — "canonical 본체 의미 변경" 금지), plugin 이식 시 `--agent-home` CLI 플래그(이미 존재!)를 활용해 plugin 용 hooks.json command 가 `--agent-home "${CLAUDE_PLUGIN_DATA}"` 를 넘기는 방식이 가능한지 확인. 이게 되면 canonical 스크립트 무수정으로 재기준 완료(우선 이 경로를 시도). 안 되면(예: stdin-JSON 모드는 `--agent-home` 인자를 못 받음 — 코드로 확인) 최소 diff 로 canonical 에 fail-open 유지하며 사유 기록.
3. **이중 발화 안전성 검토(필수, plan 에 명시 섹션)**: 같은 머신에서 settings.json 경로(HOME 배선, `$AGENT_HOME/.spec-grounding/` 사용)와 plugin 경로(`${CLAUDE_PLUGIN_DATA}/.spec-grounding/` 사용)가 **동시에 활성**이면(dev symlink 설치 + plugin 도 설치) marker 네임스페이스가 다른 디렉토리라 서로 안 밟는지, 혹은 같은 세션에서 두 hook 이 각각 등록되어 두 번 실행되면(`spec-skill-gate` 가 settings.json 에도 있고 plugin hooks.json 에도 있으면 Claude 가 중복 매처로 두 번 실행할 수 있음 — 확인) 멱등한지(두 번 deny 검사해도 부작용 없음 — read-only 검사라 안전할 가능성 높음, 확인해서 명시).
4. **fail-open 불변식 재확인**: `${CLAUDE_PLUGIN_DATA}` 가 plugin 미설치 소비자 환경엔 애초에 없음(plugin 실행 컨텍스트에서만 env 로 노출) — settings.json 배선(비-plugin)에서 이 값이 unset 이면 canonical 스크립트의 기존 `agent-home.sh` fallback(AGENT_HOME→CLAUDE_HOME→`$HOME/agent_setting`→`$HOME/.claude`)이 그대로 동작해야 함(회귀 없음).

## sync-native-plugin.py 갱신 (핵심 산출물)

- `HOOK_ADOPT` 에 3종 추가(또는 `HOOK_ADOPT`/새 리스트로 이월분을 구분 — 사유는 판단해서 plan 에 기록. 사이클 2 주석 "adopt set (_internal/hooks_inventory.md)… spec-pipeline trio deferred" 도 갱신 필요).
- `_HOOK_MATCHERS`·`_HOOK_SHELLS` 에 3종 추가(settings.json 실측 matcher/shell 반영 — 위 참조).
- `hooks_json()` 이 `PreToolUse`(spec-skill-gate) + `PostToolUse`(spec-read-marker, spec-sync-nudge) 두 이벤트 그룹을 모두 생성하도록 확장(현재는 `PreToolUse` 만 하드코딩돼 있음 — 코드 확인).
- `sync()`/`check()` 의 hooks 복사·drift 감지 루프가 새 3개 파일 + (필요시) `utilities/agent-home.sh` 동반 복사까지 커버하는지 반영.
- **비스코프 재확인**: canonical `hooks/*.sh` 본체 의미 변경은 최소·사유 기록만 — 이식은 wrapper/생성 변환(어떤 인자를 hooks.json command 에 실어 넘기는지)이 우선.

## 산출물

`.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/plan.md` + `plan/checklist.md` 를 작성하세요. 사이클 2 plan 폴더(`.agent_reports/plans/2026-07-13_harness-installer-impl2/plan/`) 를 형식 선례로 참고(Phase 구조·체크리스트 넘버링 컨벤션 동일하게). Phase 는 대략: 1) hook 3종 재확인+wrapper 가능성 판정, 2) `${CLAUDE_PLUGIN_DATA}` 재기준 배선(canonical 무수정 우선, 필요시 최소 diff), 3) `sync-native-plugin.py` 확장(HOOK_ADOPT+matchers+hooks_json 다중이벤트+check), 4) 이중발화·fail-open 검증 시나리오를 code-test 스테이지에 넘길 테스트 계획 명세(직접 실행은 code-execute/code-test 몫 — 이 스테이지는 계획만).

**주의**: 이 스테이지는 계획 작성만 합니다. 코드 수정·테스트 실행은 하지 마세요(code-execute/code-test 스테이지가 이어받습니다). 완료 후 산출물 경로만 짧게 보고하고 종료하세요.
