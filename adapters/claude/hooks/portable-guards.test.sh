#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v git >/dev/null 2>&1 && ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi
ART="$ROOT/hooks/artifact-guard.sh"
GIT="$ROOT/hooks/git-state-guard.sh"
MEM="$ROOT/hooks/builtin-memory-guard.sh"
CODEX="$ROOT/adapters/codex/bin/preflight.sh"
CODEX_PROJECTION="$ROOT/codex_setting/bin/preflight.sh"
CODEX_DISTILL="$ROOT/adapters/codex/bin/distill-worker.sh"
DESIGN="$ROOT/hooks/design-postwrite.sh"
MARK="$ROOT/hooks/spec-read-marker.sh"
SPEC="$ROOT/hooks/spec-skill-gate.sh"
FLOW="$ROOT/utilities/workflow-guard-hook.sh"
RECALL="$ROOT/hooks/mem-recall-inject.sh"
BRIEF="$ROOT/hooks/mem-briefing-inject.sh"

PASS=0
FAIL=0
ok() { PASS=$((PASS+1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  BAD %s\n' "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export AGENT_HOME="$TMP/agent_home"

echo "== artifact guard CLI =="
mkdir -p "$TMP/proj/.agent_reports/spec"
if "$ART" --file "$TMP/proj/.agent_reports/spec/prd.md" >/tmp/art.out 2>/tmp/art.err; then
  bad "new spec without research should fail"
else
  [ "$?" -eq 2 ] && ok "new spec without research exits 2" || bad "new spec wrong exit"
fi
mkdir -p "$TMP/proj/.agent_reports/research/seed"
if "$ART" --file "$TMP/proj/.agent_reports/spec/prd.md" --session test >/tmp/art.out 2>/tmp/art.err; then
  ok "new spec with research passes"
else
  bad "new spec with research should pass"
fi

echo "== git state guard CLI =="
mkdir -p "$TMP/repo"
(
  cd "$TMP/repo" || exit 1
  git init -q
  git config user.email test@example.com
  git config user.name Test
  printf 'a\n' > f
  git add f
  git commit -q -m init
)
if "$GIT" --file "$TMP/repo/f" >/tmp/git.out 2>/tmp/git.err; then
  ok "clean repo passes"
else
  bad "clean repo should pass"
fi
git -C "$TMP/repo" checkout --detach -q HEAD
if "$GIT" --file "$TMP/repo/f" >/tmp/git.out 2>/tmp/git.err; then
  bad "detached repo should fail"
else
  [ "$?" -eq 2 ] && ok "detached repo exits 2" || bad "detached repo wrong exit"
fi

echo "== codex preflight wrapper =="
git -C "$TMP/repo" switch -q -c work
if "$CODEX" write "$TMP/repo/f" testsid >/tmp/codex.out 2>/tmp/codex.err; then
  ok "codex preflight passes clean write"
else
  bad "codex preflight should pass clean write"
fi
mkdir -p "$TMP/runtime/projects/abc/memory"
if "$MEM" --file "$TMP/runtime/projects/abc/memory/MEMORY.md" >/tmp/mem.out 2>/tmp/mem.err; then
  bad "builtin memory guard should fail memory file write"
else
  [ "$?" -eq 2 ] && ok "builtin memory guard exits 2" || bad "builtin memory guard wrong exit"
fi
if "$CODEX" write "$TMP/runtime/projects/abc/memory/MEMORY.md" testsid >/tmp/codex.out 2>/tmp/codex.err; then
  bad "codex preflight should block memory file write"
else
  [ "$?" -eq 2 ] && ok "codex preflight blocks memory file write" || bad "codex preflight memory wrong exit"
fi
if AGENT_HOME="$ROOT" bash "$DESIGN" --file "$TMP/not-design.txt" >/tmp/design.out 2>/tmp/design.err \
  && "$CODEX" design "$TMP/not-design.txt" >/tmp/design.out 2>/tmp/design.err; then
  ok "design postwrite wrappers no-op on non-html"
else
  bad "design postwrite wrappers should no-op on non-html"
fi
if "$CODEX_PROJECTION" capability-info audit >/tmp/codex_projection.out 2>/tmp/codex_projection.err \
  && grep -q '^capability=audit$' /tmp/codex_projection.out \
  && grep -q '^adapter=codex$' /tmp/codex_projection.out; then
  ok "codex projection preflight resolves harness root"
else
  bad "codex projection preflight should resolve harness root"
fi

echo "== spec read gate CLI =="
mkdir -p "$TMP/specproj/.agent_reports/spec"
printf 'prd\n' > "$TMP/specproj/.agent_reports/spec/prd.md"
if "$SPEC" --skill autopilot-code --cwd "$TMP/specproj" --session testsid >/tmp/spec.out 2>/tmp/spec.err; then
  bad "spec-backed capability without read marker should fail"
else
  [ "$?" -eq 2 ] && ok "spec-backed capability without read marker exits 2" || bad "spec-backed capability wrong exit"
fi
if "$SPEC" --skill audit --cwd "$TMP/specproj" --session testsid >/tmp/spec.out 2>/tmp/spec.err; then
  ok "non spec-changing capability passes"
else
  bad "non spec-changing capability should pass"
fi
if "$MARK" --file "$TMP/specproj/.agent_reports/spec/prd.md" --session testsid >/tmp/spec.out 2>/tmp/spec.err \
  && "$SPEC" --skill autopilot-code --cwd "$TMP/specproj" --session testsid >/tmp/spec.out 2>/tmp/spec.err; then
  ok "read marker allows spec-changing capability"
else
  bad "read marker should allow spec-changing capability"
fi
sleep 1
printf 'prd updated\n' > "$TMP/specproj/.agent_reports/spec/prd.md"
if "$SPEC" --skill autopilot-code --cwd "$TMP/specproj" --session testsid >/tmp/spec.out 2>/tmp/spec.err; then
  bad "updated prd after marker should fail"
else
  [ "$?" -eq 2 ] && ok "updated prd after marker exits 2" || bad "updated prd wrong exit"
fi
if "$CODEX" read "$TMP/specproj/.agent_reports/spec/prd.md" testsid >/tmp/codex.out 2>/tmp/codex.err \
  && "$CODEX" capability autopilot-code "$TMP/specproj" testsid >/tmp/codex.out 2>/tmp/codex.err; then
  ok "codex read+capability wrapper passes spec gate"
else
  bad "codex read+capability wrapper should pass spec gate"
fi

echo "== workflow signal CLI =="
mkdir -p "$TMP/flowproj/.agent_reports"
if "$FLOW" --event prompt --cwd "$TMP/flowproj" --session testsid --format text >/tmp/flow.out 2>/tmp/flow.err \
  && grep -q 'tracked' /tmp/flow.out; then
  ok "workflow signal emits tracked text"
else
  bad "workflow signal should emit tracked text"
fi
touch "$TMP/flowproj/.agent_reports/.untracked.testsid"
if "$CODEX" mode "$TMP/flowproj" testsid >/tmp/flow.out 2>/tmp/flow.err \
  && grep -q 'untracked' /tmp/flow.out; then
  ok "codex mode wrapper emits untracked text"
else
  bad "codex mode wrapper should emit untracked text"
fi
if "$CODEX" memory "$TMP/flowproj" >/tmp/mem_inject.out 2>/tmp/mem_inject.err; then
  ok "codex memory wrapper exits cleanly"
else
  bad "codex memory wrapper should exit cleanly"
fi
if "$RECALL" --prompt "일반 질문" --cwd "$TMP/flowproj" --format text >/tmp/recall.out 2>/tmp/recall.err \
  && [ ! -s /tmp/recall.out ]; then
  ok "recall wrapper no-ops without signal word"
else
  bad "recall wrapper should no-op without signal word"
fi
if "$CODEX" recall "전에 결정한 내용 뭐였지" "$TMP/flowproj" >/tmp/recall.out 2>/tmp/recall.err; then
  ok "codex recall wrapper exits cleanly"
else
  bad "codex recall wrapper should exit cleanly"
fi
if bash "$BRIEF" --cwd "$TMP/flowproj" --format text >/tmp/brief.out 2>/tmp/brief.err \
  && [ ! -s /tmp/brief.out ]; then
  ok "briefing wrapper no-ops outside agent desk"
else
  bad "briefing wrapper should no-op outside agent desk"
fi
if "$CODEX" briefing "$TMP/flowproj" >/tmp/brief.out 2>/tmp/brief.err; then
  ok "codex briefing wrapper exits cleanly"
else
  bad "codex briefing wrapper should exit cleanly"
fi
if AGENT_MODEL_FAST=fast-model AGENT_REASONING_FAST=low "$CODEX" role fast reviewer >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^family=fast$' /tmp/role.out \
  && grep -q '^model=fast-model$' /tmp/role.out \
  && grep -q '^reasoning=low$' /tmp/role.out; then
  ok "codex role wrapper maps fast portable role"
else
  bad "codex role wrapper should map fast portable role"
fi
if "$CODEX" role external adversary >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^available=0$' /tmp/role.out \
  && grep -q '^status=unavailable$' /tmp/role.out; then
  ok "codex role wrapper marks external adversary unavailable by default"
else
  bad "codex role wrapper should mark external adversary unavailable by default"
fi
if "$CODEX" capability-info autopilot-code >/tmp/cap.out 2>/tmp/cap.err \
  && grep -q '^capability=autopilot-code$' /tmp/cap.out \
  && grep -q '^adapter=codex$' /tmp/cap.out \
  && grep -q '^native_skill=0$' /tmp/cap.out \
  && grep -q '^realization=portable-instructions$' /tmp/cap.out; then
  ok "codex capability wrapper reports instruction-only realization"
else
  bad "codex capability wrapper should report instruction-only realization"
fi
if "$CODEX" mode-info dev/backend >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=portable$' /tmp/mode.out \
  && grep -q '^realization=portable-persona$' /tmp/mode.out; then
  ok "codex mode wrapper maps portable mode"
else
  bad "codex mode wrapper should map portable mode"
fi
if "$CODEX" mode-info design/maker >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=unsupported$' /tmp/mode.out \
  && grep -q '^realization=adapter-coupled$' /tmp/mode.out; then
  ok "codex mode wrapper marks adapter-coupled design mode unsupported"
else
  bad "codex mode wrapper should mark adapter-coupled design mode unsupported"
fi
mkdir -p "$TMP/codex_sessions/2026/06/29"
cat > "$TMP/codex_sessions/2026/06/29/rollout-2026-06-29T00-00-00-codexsid.jsonl" <<'EOF'
{"timestamp":"2026-06-29T00:00:00.000Z","type":"event_msg","payload":{"type":"user_message","message":"hello"}}
{"timestamp":"2026-06-29T00:00:01.000Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"world"}]}}
{"timestamp":"2026-06-29T00:00:02.000Z","type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"call_1"}}
EOF
if CODEX_SESSIONS="$TMP/codex_sessions" python3 "$ROOT/tools/memory/mem.py" distill codexsid --source codex >/tmp/codex_delta.out 2>/tmp/codex_delta.err \
  && grep -q '^\[user\] hello' /tmp/codex_delta.out \
  && grep -q '^\[assistant\] world' /tmp/codex_delta.out \
  && grep -q '^\[assistant\] \[tool:exec_command\]' /tmp/codex_delta.out; then
  ok "codex session source distills transcript"
else
  bad "codex session source should distill transcript"
fi
if "$CODEX_DISTILL" codexsid "$TMP/flowproj" >/tmp/codex_distill.out 2>/tmp/codex_distill.err \
  && [ ! -s /tmp/codex_distill.out ]; then
  ok "codex distill worker is disabled by default"
else
  bad "codex distill worker should no-op unless enabled"
fi
mkdir -p "$TMP/stubbin"
cat > "$TMP/stubbin/codex" <<'EOF'
#!/usr/bin/env sh
printf '%s\n' "$@" > "$CODEX_STUB_ARGV"
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--output-last-message" ]; then
    shift
    printf '{"action":"add","tier":"working","type":"context","body":"stub codex distill memory record"}\n' > "$1"
  fi
  shift || break
done
exit 0
EOF
chmod +x "$TMP/stubbin/codex"
if CODEX_DISTILL_ENABLE=1 CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv" \
  "$CODEX" distill-propose codexsid "$TMP/flowproj" >/tmp/codex_distill.out 2>/tmp/codex_distill.err \
  && grep -q -- '--sandbox' "$TMP/codex_argv" \
  && grep -q -- 'read-only' "$TMP/codex_argv" \
  && grep -q -- '--ask-for-approval' "$TMP/codex_argv" \
  && grep -q -- 'never' "$TMP/codex_argv" \
  && grep -q -- '--ephemeral' "$TMP/codex_argv" \
  && grep -q -- '--ignore-rules' "$TMP/codex_argv" \
  && grep -q '"action":"add"' /tmp/codex_distill.out; then
  ok "codex distill proposal uses constrained exec"
else
  bad "codex distill proposal should use constrained exec"
fi
if CODEX_DISTILL_ENABLE=1 CODEX_DISTILL_APPLY=1 CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store_apply" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv_apply" \
  "$CODEX" distill-propose codexsid "$TMP/flowproj" >/tmp/codex_distill_apply.out 2>/tmp/codex_distill_apply.err \
  && MEM_STORE="$TMP/store_apply" python3 "$ROOT/tools/memory/mem.py" stats >/tmp/codex_stats.out 2>/tmp/codex_stats.err \
  && grep -q 'total: 1' /tmp/codex_stats.out; then
  ok "codex distill proposal can explicitly apply through shared applier"
else
  bad "codex distill explicit apply should create one memory record"
fi

printf 'PASS=%s FAIL=%s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
