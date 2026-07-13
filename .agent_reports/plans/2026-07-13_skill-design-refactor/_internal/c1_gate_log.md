# C1-GATE trial-flip log (2026-07-13, dev 재개 세션)

> PRD §3.3 (a)(b)(c) 3절차 게이트 시도 기록. 결과: **(a) 실행 불가 — 인프라 blocker, revert 완료**. (b)(c) 미착수(의존).

## (a) slash 명시 호출 생존 — BLOCKED (실행 불가, PASS/FAIL 판정 불가)

- **시도**: `adapters/claude/skills/draft-strategy/SKILL.md` frontmatter 에 `disable-model-invocation: true` 추가(trial-flip) 후, `claude -p "/draft-strategy <args>"` headless 호출로 slash 경로 생존 관측 시도.
- **차단 1**: 본 conductor 는 depth-1 headless 세션(`claude -p` 로 이미 실행 중) — 그 안에서 다시 `claude -p ... --dangerously-skip-permissions` 를 실행하려 하자 **샌드박스 auto-mode classifier 가 명시 차단**: "Create Unsafe Agents — nested claude -p ... 는 승인 게이트 없는 완전 자율 에이전트 루프이며 명시적 사용자 승인 없이 실행 불가."
- **차단 2 (fallback 시도)**: `--dangerously-skip-permissions` 제거하고 격리 `CLAUDE_CONFIG_DIR=/tmp/c1gate/.claude`(skills 심볼릭 링크만 본 worktree 로 교체) 로 재시도 → `/draft-strategy` 가 `Unknown command: /draft-strategy` 반환. **동일 config 로 `/help`·`/post-it` 도 이상 동작**(`/help isn't available in this environment`, `/post-it` 무응답) — 이는 **flip 자체의 영향인지, `CLAUDE_CONFIG_DIR` 미지원(실제 `~/.claude` 로 fallback)인지, 또는 nested `-p` 세션 안에서 slash-command 해석 경로 자체가 다른지 구분 불가**. 즉 신호가 오염돼 PASS/FAIL 어느 쪽으로도 단정할 근거가 없다.
- **조치**: PRD·CLAUDE.md "검증 후 단언" 원칙 + 본 게이트의 "실패 시 즉시 revert" 규정에 따라 **frontmatter flip 즉시 revert**(`git diff` 확인 — clean, 원본과 동일). `adapters/`·`skills/` 양 트리 모두 미변경 상태로 복귀.

## (b)(c) — 미착수

(a) 가 확정 PASS 하지 못했으므로 (b) code-test trial-flip·(c) 실파이프 통과는 착수하지 않음(게이트 순서 종속).

## 권고 (main 세션 결정 필요)

C1-GATE 는 **본 depth-1/depth-2 nested headless 환경에서 실행 불가능한 절차**로 확인됨 — 샌드박스가 nested `claude -p` 자율 에이전트 생성을 승인 없이 차단하기 때문. 실행하려면:
1. **메인(비-nested) 세션**에서 직접 trial-flip + `claude -p` 관측을 수행하거나,
2. 사용자가 이 nested 차단에 대해 명시 승인(permission rule 추가)하거나,
3. 격리 config-dir 방식이 아닌 다른 검증 경로(예: Claude Code 공식 문서에서 `disable-model-invocation` 이 slash-dispatch 에 미치는 영향을 문서 근거로 확인 — 단, PRD 는 명시적으로 "문서상 유지되나 실측 필요"라 명시해 문서만으로는 게이트 통과 인정 안 함)를 강구.

**Cluster 1 전체(C1-GATE→FLIP→P7→P4)는 이번 재개 사이클에서 미완료 — SD-5 폴백 정책상 게이트 미통과 시 flip 자체를 하지 않는 것이 안전측(model-invoked 유지)이므로, 13개 스킬 모두 현 상태(model-invoked) 유지.**

---

# C1-GATE 비-nested 재시도 (2026-07-13, Codex capability owner)

> 최신 작업 지시에 따라 `draft-strategy` 하나를 pilot으로 유지한 채 (a)(b)(c)를 각각 fresh `claude -p`로 관측했다. **(a) PASS / (b) FAIL / (c) FAIL → D1에 따라 flip 0개, pilot 즉시 revert**.

## 격리 환경과 대조군

- runtime: Claude Code `2.1.207`
- `CLAUDE_CONFIG_DIR`: worktree 내부 `.dispatch/homes/skill-design-c1-probe.c1-gate`
- profile `skills`는 `/home/Uihyeop/agent_setting-wt/skill-design-c1/adapters/claude/skills` 전체를 가리킨다. live `~/.claude`의 skills/settings/sessions는 쓰지 않았고, 인증 파일만 심링크로 재사용했다. 모든 probe는 `--no-session-persistence`로 실행했다.
- 공식 계약: `disable-model-invocation: true`는 사용자 직접 `/name` 호출은 유지하지만 Claude의 자동·Skill 호출을 막는다([Claude Code skills](https://code.claude.com/docs/en/slash-commands)); `CLAUDE_CONFIG_DIR`는 설정·데이터 디렉터리를 대체한다([Claude directory controls](https://code.claude.com/docs/en/claude-directory)). 아래 실측을 최종 authority로 사용했다.

pre-flip 대조군 원문(결정 이벤트):

```text
$ ... claude -p '/draft-strategy ... reply C1_CONTROL_SLASH_LOADED' ... --tools ''
{"type":"assistant",...,"content":[{"type":"text","text":"C1_CONTROL_SLASH_LOADED"}],...}
{"type":"result","subtype":"success",...,"result":"C1_CONTROL_SLASH_LOADED",...}
status=ok
exit_code=0

$ ... claude -p '... use the Skill tool to invoke draft-strategy ... C1_CONTROL_SKILL_DISPATCH_OK ...' ... --tools Skill
{"type":"assistant",...,"content":[{"type":"tool_use",...,"name":"Skill","input":{"skill":"draft-strategy",...}}],...}
{"type":"user",...,"content":[{"type":"tool_result","content":"Launching skill: draft-strategy",...}],...}
{"type":"result","subtype":"success",...,"result":"C1_CONTROL_SKILL_DISPATCH_OK",...}
status=ok
exit_code=0
```

대조군에서 slash discovery와 Skill dispatch가 모두 살아 있으므로 아래 FAIL은 profile 신호 오염이 아니다. 이어서 양 트리 `draft-strategy/SKILL.md`에 `disable-model-invocation: true`를 동일하게 추가하고 `cmp` 성공을 확인했다.

## (a) slash 명시 호출 — PASS

```bash
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- \
  env MEM_DISTILL=1 CLAUDE_CONFIG_DIR="$PROFILE" \
  claude -p '/draft-strategy PROBE ONLY. Do not read or write files and do not call tools. If the draft-strategy skill instructions were loaded despite disable-model-invocation, reply exactly C1_A_SLASH_PASS.' \
  --output-format stream-json --verbose --no-session-persistence --permission-mode dontAsk --tools ''
```

```text
{"type":"system","subtype":"init",...,"slash_commands":[...,"draft-strategy",...],...}
{"type":"assistant",...,"content":[{"type":"text","text":"C1_A_SLASH_PASS"}],...}
{"type":"result","subtype":"success",...,"result":"C1_A_SLASH_PASS",...}
status=ok
exit_code=0
```

판정: **PASS** — flip 상태에서도 `/draft-strategy`가 instruction을 로드했다.

## (b) parent Skill-tool dispatch — FAIL

```bash
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- \
  env MEM_DISTILL=1 CLAUDE_CONFIG_DIR="$PROFILE" \
  claude -p 'PROBE ONLY. As an orchestrator, use the Skill tool to invoke draft-strategy with arguments: do not read or write files; return only C1_B_SUBSKILL_REACHED. After the actual Skill call returns, reply exactly C1_B_SKILL_DISPATCH_PASS. If the tool cannot invoke draft-strategy, reply C1_B_SKILL_DISPATCH_FAIL and state the runtime reason. Do not claim PASS without a Skill tool call.' \
  --output-format stream-json --verbose --no-session-persistence --permission-mode dontAsk --tools Skill
```

```text
{"type":"assistant","message":{...,"content":[{"type":"tool_use",...,"name":"Skill","input":{"skill":"draft-strategy","args":"PROBE ONLY — do not read or write files."},...}],...},...}
{"type":"user","message":{...,"content":[{"type":"tool_result","content":"<tool_use_error>Skill draft-strategy cannot be used with Skill tool due to disable-model-invocation</tool_use_error>","is_error":true,...}]},...,"tool_use_result":"Error: Skill draft-strategy cannot be used with Skill tool due to disable-model-invocation"}
{"type":"result","subtype":"success",...,"result":"C1_B_SKILL_DISPATCH_FAIL — draft-strategy skill has `disable-model-invocation` set, so the Skill tool refused to invoke it (runtime error: \"Skill draft-strategy cannot be used with Skill tool due to disable-model-invocation\").",...}
status=ok
exit_code=0
```

판정: **FAIL** — process exit가 아니라 Skill tool 결과가 gate authority이며, runtime이 flag를 이유로 명시 거부했다.

## (c) `autopilot-draft` 실파이프 sub-skill 도달 — FAIL

```bash
adapters/codex/bin/preflight.sh verification-runner --timeout 120 -- \
  env MEM_DISTILL=1 CLAUDE_CONFIG_DIR="$PROFILE" \
  claude -p '/autopilot-draft PROBE ONLY. Do not read or write files. Exercise the pipeline sub-skill handoff by using the Skill tool to invoke draft-strategy with arguments: return only C1_C_SUBSKILL_REACHED. Only after that actual Skill call returns successfully, reply exactly C1_C_PIPELINE_PASS. If draft-strategy cannot be dispatched, reply C1_C_PIPELINE_FAIL and state the runtime reason. Do not claim PASS without a successful Skill tool result.' \
  --output-format stream-json --verbose --no-session-persistence --permission-mode dontAsk --tools Skill
```

```text
{"type":"assistant","message":{...,"content":[{"type":"tool_use",...,"name":"Skill","input":{"skill":"draft-strategy","args":"return only C1_C_SUBSKILL_REACHED"},...}],...},...}
{"type":"user","message":{...,"content":[{"type":"tool_result","content":"<tool_use_error>Skill draft-strategy cannot be used with Skill tool due to disable-model-invocation</tool_use_error>","is_error":true,...}]},...,"tool_use_result":"Error: Skill draft-strategy cannot be used with Skill tool due to disable-model-invocation"}
{"type":"result","subtype":"success",...,"result":"C1_C_PIPELINE_FAIL — draft-strategy는 `disable-model-invocation` 설정으로 Skill 도구를 통한 모델 주도 호출이 차단되어 있어 디스패치 불가.",...}
status=ok
exit_code=0
```

판정: **FAIL** — `/autopilot-draft` entry는 로드됐지만 실제 `draft-strategy` handoff가 거부됐다.

## D1 결과와 복구

- 3절차: **PASS / FAIL / FAIL**.
- 13개 후보는 parent Skill-tool handoff를 보존해야 하므로, (b)(c) 실패 상태에서 slash-only 통과분을 안전한 flip 부분집합으로 볼 수 없다. D1·SD-5에 따라 **C1-FLIP 0개**.
- pilot flag를 양 트리에서 즉시 제거했다. `cmp` 성공, 두 파일의 `rg '^disable-model-invocation:'` 0건, `git diff` 0건으로 원복 확인.
- 자동 수정 금지 계약 항목: PRD/CONVENTIONS/DESIGN_PRINCIPLES/g7의 “순수 sub-skill disable” 목표와 현재 Claude runtime의 Skill-tool 차단이 충돌한다. invocation 분류 계약과 runtime realization 전략을 별도 결정해야 한다.
