#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/hooks/artifact-guard.sh"
GIT="$ROOT/hooks/git-state-guard.sh"
MEM="$ROOT/hooks/builtin-memory-guard.sh"
CODEX="$ROOT/adapters/codex/bin/preflight.sh"
CODEX_PROJECTION="$ROOT/codex_setting/bin/preflight.sh"
CODEX_DISTILL="$ROOT/adapters/codex/bin/distill-worker.sh"
OPENCODE="$ROOT/adapters/opencode/bin/preflight.sh"
OPENCODE_PROJECTION="$ROOT/opencode_setting/bin/preflight.sh"
OPENCODE_DISTILL="$ROOT/adapters/opencode/bin/distill-worker.sh"
DESIGN="$ROOT/hooks/design-postwrite.sh"
MARK="$ROOT/hooks/spec-read-marker.sh"
SPEC="$ROOT/hooks/spec-skill-gate.sh"
FLOW="$ROOT/utilities/workflow-guard-hook.sh"
TOGGLE="$ROOT/utilities/workflow-toggle.sh"
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
mkdir -p "$TMP/codex_pointer_home/.codex"
ln -s "$ROOT" "$TMP/codex_pointer_home/.codex/agent-harness"
if env -u AGENT_HOME HOME="$TMP/codex_pointer_home" "$ROOT/adapters/codex/utilities/agent-home.sh" >/tmp/codex_agent_home.out 2>/tmp/codex_agent_home.err \
  && grep -q "^$TMP/codex_pointer_home/.codex/agent-harness$" /tmp/codex_agent_home.out; then
  ok "codex agent-home wrapper resolves runtime pointer"
else
  bad "codex agent-home wrapper should resolve runtime pointer"
fi
if AGENT_HOME="$TMP/not-agent-home" HOME="$TMP/codex_pointer_home" "$ROOT/adapters/codex/utilities/agent-home.sh" >/tmp/codex_agent_home_invalid.out 2>/tmp/codex_agent_home_invalid.err \
  && grep -q "^$TMP/codex_pointer_home/.codex/agent-harness$" /tmp/codex_agent_home_invalid.out; then
  ok "codex agent-home wrapper ignores invalid AGENT_HOME"
else
  bad "codex agent-home wrapper should ignore invalid AGENT_HOME"
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
if "$CODEX" route autopilot-code "$TMP/specproj" testsid >/tmp/codex_route.out 2>/tmp/codex_route.err \
  && grep -q '^runtime_surface=codex-userprompt-hook-signal$' /tmp/codex_route.out \
  && grep -q '^capability=autopilot-code$' /tmp/codex_route.out \
  && grep -q '^compat_reference=not-projected$' /tmp/codex_route.out \
  && grep -q '^pipeline_contract=code-plan>code-execute>code-test>code-report$' /tmp/codex_route.out; then
  ok "codex route wrapper combines prompt signal, capability-info, and spec gate"
else
  bad "codex route wrapper should combine prompt signal, capability-info, and spec gate"
fi
if "$CODEX" capability nope-capability "$TMP/specproj" testsid >/tmp/codex_bad_capability_gate.out 2>/tmp/codex_bad_capability_gate.err; then
  bad "codex capability wrapper should reject unknown capabilities"
else
  rc=$?
  if [ "$rc" -eq 64 ] \
    && grep -q '^check=failed$' /tmp/codex_bad_capability_gate.out \
    && grep -q '^reason=unknown-capability$' /tmp/codex_bad_capability_gate.out; then
    ok "codex capability wrapper rejects unknown capabilities"
  else
    bad "codex capability wrapper unknown capability output wrong"
  fi
fi

echo "== workflow signal CLI =="
mkdir -p "$TMP/flowproj/.agent_reports"
if "$FLOW" --event prompt --cwd "$TMP/flowproj" --session testsid --format text >/tmp/flow.out 2>/tmp/flow.err \
  && grep -q 'tracked' /tmp/flow.out; then
  ok "workflow signal emits tracked text"
else
  bad "workflow signal should emit tracked text"
fi
oldflag="$TMP/flowproj/.agent_reports/.untracked.oldsid"
: > "$oldflag"
touch -d '2026-06-10 00:00:00' "$oldflag"
if "$CODEX" start "$TMP/flowproj" testsid >/tmp/start.out 2>/tmp/start.err \
  && [ ! -e "$oldflag" ]; then
  ok "codex start wrapper cleans stale untracked flags"
else
  bad "codex start wrapper should clean stale untracked flags"
fi
mkdir -p "$TMP/codex-artifact/.agent_reports/spec"
if "$CODEX" write "$TMP/codex-artifact/.agent_reports/spec/prd.md" testsid >/tmp/codex-artifact.out 2>/tmp/codex-artifact.err; then
  bad "codex write wrapper should fail missing research"
else
  rc=$?
  if [ "$rc" -eq 2 ] \
    && grep -q 'preflight.sh track' /tmp/codex-artifact.err \
    && ! grep -q '/track' /tmp/codex-artifact.err; then
    ok "codex write wrapper adapts artifact toggle hint"
  else
    bad "codex write wrapper should adapt artifact toggle hint"
  fi
fi
if "$TOGGLE" --cwd "$TMP/flowproj" --session testsid --set untracked >/tmp/toggle.out 2>/tmp/toggle.err \
  && grep -q 'untracked mode' /tmp/toggle.out \
  && [ -f "$TMP/flowproj/.agent_reports/.untracked.testsid" ]; then
  ok "workflow toggle CLI enables untracked mode"
else
  bad "workflow toggle CLI should enable untracked mode"
fi
if "$TOGGLE" --cwd "$TMP/flowproj" --session testsid --set tracked >/tmp/toggle.out 2>/tmp/toggle.err \
  && grep -q 'tracked mode' /tmp/toggle.out \
  && [ ! -f "$TMP/flowproj/.agent_reports/.untracked.testsid" ]; then
  ok "workflow toggle CLI restores tracked mode"
else
  bad "workflow toggle CLI should restore tracked mode"
fi
if "$CODEX" track "$TMP/flowproj" testsid >/tmp/track.out 2>/tmp/track.err \
  && grep -q 'untracked mode' /tmp/track.out \
  && [ -f "$TMP/flowproj/.agent_reports/.untracked.testsid" ]; then
  ok "codex track wrapper enables untracked mode"
else
  bad "codex track wrapper should enable untracked mode"
fi
if "$CODEX" mode "$TMP/flowproj" testsid >/tmp/flow.out 2>/tmp/flow.err \
  && grep -q 'untracked' /tmp/flow.out \
  && grep -q 'preflight.sh track' /tmp/flow.out \
  && ! grep -q '/track' /tmp/flow.out; then
  ok "codex mode wrapper emits untracked text"
else
  bad "codex mode wrapper should emit untracked text"
fi
if "$CODEX" track "$TMP/flowproj" testsid >/tmp/track.out 2>/tmp/track.err \
  && grep -q 'tracked mode' /tmp/track.out \
  && [ ! -f "$TMP/flowproj/.agent_reports/.untracked.testsid" ]; then
  ok "codex track wrapper restores tracked mode"
else
  bad "codex track wrapper should restore tracked mode"
fi
if "$CODEX" memory "$TMP/flowproj" >/tmp/mem_inject.out 2>/tmp/mem_inject.err; then
  ok "codex memory wrapper exits cleanly"
else
  bad "codex memory wrapper should exit cleanly"
fi
if MEM_STORE="$TMP/codex_launcher_store" "$ROOT/adapters/codex/tools/memory/mem.py" stats >/tmp/codex_mem_launcher.out 2>/tmp/codex_mem_launcher.err \
  && grep -q '^# store stats$' /tmp/codex_mem_launcher.out; then
  ok "codex memory launcher ignores invalid non-harness AGENT_HOME"
else
  bad "codex memory launcher should fall back from invalid AGENT_HOME"
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
mkdir -p "$TMP/notes/cards" "$TMP/notes/_layer2/notes" "$TMP/board/.cache" "$TMP/board-wt"
printf 'card\n' > "$TMP/notes/cards/demo.md"
printf 'note\n' > "$TMP/notes/_layer2/notes/demo.md"
if AGENT_NOTES_ROOT="$TMP/notes" WORKLOG_BOARD_APP="$TMP/board" WORKLOG_BOARD_WT="$TMP/board-wt" \
  "$CODEX" worklog "$TMP/flowproj" >/tmp/worklog.out 2>/tmp/worklog.err \
  && grep -q "^agent-notes-root=$TMP/notes$" /tmp/worklog.out \
  && grep -q "^worklog-board-app=$TMP/board$" /tmp/worklog.out \
  && grep -q '^notes.cards.files=1$' /tmp/worklog.out \
  && grep -q '^notes._layer2/notes.files=1$' /tmp/worklog.out \
  && grep -q '^note=read-only inventory;' /tmp/worklog.out; then
  ok "codex worklog wrapper reports read-only state"
else
  bad "codex worklog wrapper should report read-only state"
fi
if env -u AGENT_NOTES_ROOT -u WORKLOG_NOTES_ROOT -u WORKLOG_BOARD_APP -u WORKLOG_BOARD_WT \
  "$CODEX" worklog "$TMP/flowproj" >/tmp/worklog-default.out 2>/tmp/worklog-default.err \
  && grep -q '^agent-notes-root=unset$' /tmp/worklog-default.out \
  && grep -q '^worklog-board-app=unset$' /tmp/worklog-default.out \
  && grep -q '^worklog-board-wt=unset$' /tmp/worklog-default.out \
  && ! grep -q '/.claude/worklog-board' /tmp/worklog-default.out; then
  ok "codex worklog wrapper has no Claude runtime defaults"
else
  bad "codex worklog wrapper should not default to Claude runtime paths"
fi
printf 'T\topen\t/r\t/r-wt/a\tjob-a\tcap\nT\tdone\t/r\t/r-wt/b\tjob-b\tcap\n' > "$TMP/status_jobs.log"
if AGENT_NOTES_ROOT="$TMP/notes" WORKLOG_BOARD_APP="$TMP/board" WORKLOG_BOARD_WT="$TMP/board-wt" AGENT_DISPATCH_JOBS="$TMP/status_jobs.log" \
  "$CODEX" status "$TMP/flowproj" testsid >/tmp/codex_status.out 2>/tmp/codex_status.err \
  && grep -q '^adapter=codex$' /tmp/codex_status.out \
  && grep -q '^headless_open_jobs=1$' /tmp/codex_status.out \
  && grep -q '^headless_open_slugs=job-a$' /tmp/codex_status.out \
  && grep -q '^runtime_surface=adapter-owned-harness-status$' /tmp/codex_status.out \
  && grep -q '^artifact_root_exists=1$' /tmp/codex_status.out \
  && grep -q '^workflow_state=tracked$' /tmp/codex_status.out \
  && grep -q '^git_repo=0$' /tmp/codex_status.out \
  && grep -q "^agent_notes_root=$TMP/notes$" /tmp/codex_status.out \
  && grep -q '^note=read-only snapshot;' /tmp/codex_status.out; then
  ok "codex status wrapper reports harness snapshot"
else
  bad "codex status wrapper should report harness snapshot"
fi
mkdir -p "$TMP/donebranch"
git -C "$TMP/donebranch" init -q
git -C "$TMP/donebranch" config user.email t@t
git -C "$TMP/donebranch" config user.name t
git -C "$TMP/donebranch" checkout -q -b main
echo x > "$TMP/donebranch/f"; git -C "$TMP/donebranch" add f; git -C "$TMP/donebranch" commit -q -m x
git -C "$TMP/donebranch" checkout -q -b topic
git -C "$TMP/donebranch" branch -q --set-upstream-to=main topic 2>/dev/null
if "$CODEX" status "$TMP/donebranch" testsid >/tmp/codex_done.out 2>/tmp/codex_done.err \
  && grep -q '^git_upstream=main$' /tmp/codex_done.out \
  && grep -q '^git_ahead=0$' /tmp/codex_done.out \
  && grep -q '^git_branch_done=1$' /tmp/codex_done.out; then
  ok "codex status flags a merged dead branch (DONE-BRANCH risk)"
else
  bad "codex status should flag a merged dead branch"
fi
if "$CODEX" prompt-signal "$TMP/flowproj" testsid >/tmp/codex_prompt_signal_tracked.out 2>/tmp/codex_prompt_signal_tracked.err \
  && grep -q '^workflow_state=tracked$' /tmp/codex_prompt_signal_tracked.out \
  && grep -q '^autopilot_route=autopilot-required-for-spec-and-nontrivial-work$' /tmp/codex_prompt_signal_tracked.out \
  && grep -q '^routing_contract=core/WORKFLOW.md$' /tmp/codex_prompt_signal_tracked.out \
  && grep -q '^routing_action=read-workflow-and-select-codex-skill$' /tmp/codex_prompt_signal_tracked.out \
  && grep -q '^capability_entrypoints=codex-native-skills-plugin$' /tmp/codex_prompt_signal_tracked.out \
  && grep -q '^hook_boundary=shell-read-write-unsupported-use-explicit-preflight$' /tmp/codex_prompt_signal_tracked.out; then
  ok "codex prompt signal carries tracked autopilot routing contract"
else
  bad "codex prompt signal should carry tracked autopilot routing contract"
fi
if "$CODEX" permissions >/tmp/codex_permissions.out 2>/tmp/codex_permissions.err \
  && grep -q '^adapter=codex$' /tmp/codex_permissions.out \
  && grep -q '^runtime_surface=codex-native-approval-sandbox$' /tmp/codex_permissions.out \
  && grep -q '^permission_model=approval-policy+sandbox$' /tmp/codex_permissions.out \
  && grep -q '^claude_allowed_tools=unsupported$' /tmp/codex_permissions.out \
  && grep -q '^guard_contract=preflight-write-hooks-and-explicit-tool-contracts$' /tmp/codex_permissions.out \
  && grep -q '^structured_write_hooks=Write,Edit,MultiEdit,apply_patch,functions.apply_patch$' /tmp/codex_permissions.out \
  && grep -q '^shell_read_write_hooks=unsupported$' /tmp/codex_permissions.out; then
  ok "codex permissions wrapper reports native approval/sandbox contract"
else
  bad "codex permissions wrapper should report native approval/sandbox contract"
fi
if "$CODEX" headless >/tmp/codex_headless.out 2>/tmp/codex_headless.err \
  && grep -q '^adapter=codex$' /tmp/codex_headless.out \
  && grep -q '^runtime_surface=codex-exec-headless$' /tmp/codex_headless.out \
  && grep -q '^tool_contract=headless-dispatch$' /tmp/codex_headless.out \
  && grep -q '^strict_tool_contract_check=adapters/codex/bin/preflight.sh headless --check --require-hook-trust <worktree>$' /tmp/codex_headless.out \
  && grep -q '^runtime_projection_requires=agent-harness,AGENTS.md,hooks.json,native-skills,native-agents,native-modes$' /tmp/codex_headless.out \
  && grep -q '^runtime_projection_strict_requires=complete-codex-hook-trust$' /tmp/codex_headless.out \
  && grep -q '^claude_headless=unsupported$' /tmp/codex_headless.out \
  && grep -q '^liveness_surface=codex-session-jsonl-mtime$' /tmp/codex_headless.out \
  && grep -q '^liveness_check=adapters/codex/bin/preflight.sh liveness \[jobs.log\]$' /tmp/codex_headless.out \
  && grep -q '^dispatch_prompt_contract=codex-harness-autopilot-prompt$' /tmp/codex_headless.out \
  && grep -q '^dispatch_input_validation=capability-info,mode-info,qa-level$' /tmp/codex_headless.out \
  && grep -q '^constraints=main-only,max-depth-1,register-open-job,explicit-capability-mode-qa,transcript-liveness-required$' /tmp/codex_headless.out; then
  ok "codex headless wrapper reports dispatch contract"
else
  bad "codex headless wrapper should report dispatch contract"
fi
if grep -q 'adapters/codex/bin/preflight.sh liveness \[jobs.log\]' "$ROOT/core/OPERATIONS.md" \
  && grep -q 'adapters/opencode/bin/preflight.sh liveness \[jobs.log\]' "$ROOT/core/OPERATIONS.md" \
  && grep -q 'adapter liveness wrapper' "$ROOT/core/OPERATIONS.md" \
  && ! grep -q '능동 점검한다\\*\\*: `bash <agent-home>/utilities/dispatch-liveness.sh`' "$ROOT/core/OPERATIONS.md"; then
  ok "portable operations routes headless liveness through adapter wrappers"
else
  bad "portable operations should route headless liveness through adapter wrappers"
fi
if "$CODEX" headless --check "$TMP/missing-worktree" >/tmp/codex_headless_missing.out 2>/tmp/codex_headless_missing.err; then
  bad "codex headless wrapper should fail missing worktree"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^reason=worktree-not-found$' /tmp/codex_headless_missing.out; then
    ok "codex headless wrapper reports missing worktree"
  else
    bad "codex headless wrapper should report missing worktree"
  fi
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$TMP/codex_headless_home" "$ROOT/adapters/codex/bin/install-runtime-projection.sh" >/tmp/codex_headless_install.out 2>/tmp/codex_headless_install.err \
  && CODEX_HOME="$TMP/codex_headless_home" "$CODEX" headless --check "$TMP/repo" >/tmp/codex_headless_check.out 2>/tmp/codex_headless_check.err \
  && grep -q '^runtime_projection=ok$' /tmp/codex_headless_check.out \
  && grep -q '^check=hook-trust:review-needed' /tmp/codex_headless_check.out \
  && grep -q '^check=ok$' /tmp/codex_headless_check.out; then
  ok "codex headless check validates runtime projection"
else
  bad "codex headless check should validate runtime projection"
fi
if CODEX_HOME="$TMP/codex_headless_home" "$CODEX" headless --check --require-hook-trust "$TMP/repo" >/tmp/codex_headless_strict.out 2>/tmp/codex_headless_strict.err; then
  bad "codex headless strict check should fail when hook trust is incomplete"
else
  grep -q '^check=hook-trust:review-needed' /tmp/codex_headless_strict.out && ok "codex headless strict check requires complete hook trust" || bad "codex headless strict check missing trust output wrong"
fi
if "$CODEX" dispatch --dry-run --worktree "$TMP/repo" --slug codex-dispatch --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" --jobs "$TMP/codex-dispatch.log" >/tmp/codex_dispatch.out 2>/tmp/codex_dispatch.err \
  && grep -q '^adapter=codex$' /tmp/codex_dispatch.out \
  && grep -q '^status=dry-run$' /tmp/codex_dispatch.out \
  && grep -q '^registered=0$' /tmp/codex_dispatch.out \
  && grep -q '^started=0$' /tmp/codex_dispatch.out \
  && grep -q '^command=codex exec ' /tmp/codex_dispatch.out \
  && ! grep -q -- '--ask-for-approval' /tmp/codex_dispatch.out \
  && [ ! -e "$TMP/codex-dispatch.log" ]; then
  ok "codex dispatch wrapper dry-runs headless command without registry write"
else
  bad "codex dispatch wrapper should dry-run headless command without registry write"
fi
if "$CODEX" dispatch --dry-run --worktree "$TMP/repo" --slug codex-bad-cap --capability nope-capability --mode dev/backend --qa standard --prompt-text "do work" --jobs "$TMP/codex-bad-cap.log" >/tmp/codex_bad_cap.out 2>/tmp/codex_bad_cap.err; then
  bad "codex dispatch wrapper should fail invalid capability"
else
  rc=$?
  if [ "$rc" -eq 64 ] \
    && grep -q '^reason=invalid-dispatch-capability$' /tmp/codex_bad_cap.out \
    && grep -q '^capability=nope-capability$' /tmp/codex_bad_cap.out \
    && [ ! -e "$TMP/codex-bad-cap.log" ]; then
    ok "codex dispatch wrapper validates capability before registry write"
  else
    bad "codex dispatch wrapper should validate capability before registry write"
  fi
fi
if "$CODEX" dispatch --dry-run --worktree "$TMP/repo" --slug codex-bad-mode --capability autopilot-code --mode dev/nope --qa standard --prompt-text "do work" --jobs "$TMP/codex-bad-mode.log" >/tmp/codex_bad_mode.out 2>/tmp/codex_bad_mode.err; then
  bad "codex dispatch wrapper should fail invalid mode"
else
  rc=$?
  if [ "$rc" -eq 64 ] \
    && grep -q '^reason=invalid-dispatch-mode$' /tmp/codex_bad_mode.out \
    && grep -q '^mode=dev/nope$' /tmp/codex_bad_mode.out \
    && [ ! -e "$TMP/codex-bad-mode.log" ]; then
    ok "codex dispatch wrapper validates mode before registry write"
  else
    bad "codex dispatch wrapper should validate mode before registry write"
  fi
fi
if "$CODEX" dispatch --dry-run --worktree "$TMP/repo" --slug codex-bad-qa --capability autopilot-code --mode dev/backend --qa extreme --prompt-text "do work" --jobs "$TMP/codex-bad-qa.log" >/tmp/codex_bad_qa.out 2>/tmp/codex_bad_qa.err; then
  bad "codex dispatch wrapper should fail invalid QA level"
else
  rc=$?
  if [ "$rc" -eq 64 ] \
    && grep -q '^reason=invalid-dispatch-qa$' /tmp/codex_bad_qa.out \
    && grep -q '^qa=extreme$' /tmp/codex_bad_qa.out \
    && grep -q '^allowed_qa=quick,light,standard,thorough,adversarial$' /tmp/codex_bad_qa.out \
    && [ ! -e "$TMP/codex-bad-qa.log" ]; then
    ok "codex dispatch wrapper validates QA level before registry write"
  else
    bad "codex dispatch wrapper should validate QA level before registry write"
  fi
fi
if "$CODEX" dispatch --dry-run --worktree "$TMP/repo" --slug codex-default-home --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" >/tmp/codex_dispatch_default.out 2>/tmp/codex_dispatch_default.err \
  && grep -Fxq "job_registry=$ROOT/.dispatch/jobs.log" /tmp/codex_dispatch_default.out \
  && grep -Fxq "prompt_file=$ROOT/.dispatch/logs/codex-default-home.codex.prompt.txt" /tmp/codex_dispatch_default.out \
  && [ ! -e "$AGENT_HOME/.dispatch/jobs.log" ]; then
  ok "codex dispatch wrapper defaults to validated harness root"
else
  bad "codex dispatch wrapper should not trust invalid AGENT_HOME for default registry"
fi
if AGENT_HOME="$TMP/not-agent-home" python3 "$ROOT/adapters/codex/bin/dispatch-headless.py" --dry-run --worktree "$TMP/repo" --slug codex-direct-home --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" >/tmp/codex_dispatch_direct.out 2>/tmp/codex_dispatch_direct.err \
  && grep -Fxq "job_registry=$ROOT/.dispatch/jobs.log" /tmp/codex_dispatch_direct.out \
  && grep -Fxq "prompt_file=$ROOT/.dispatch/logs/codex-direct-home.codex.prompt.txt" /tmp/codex_dispatch_direct.out; then
  ok "codex dispatch script ignores invalid AGENT_HOME"
else
  bad "codex dispatch script should validate AGENT_HOME"
fi
mkdir -p "$TMP/codex-stubbin"
cat > "$TMP/codex-stubbin/codex" <<'EOF'
#!/usr/bin/env sh
printf '%s\n' "$*" > "$CODEX_STUB_ARGV"
EOF
chmod +x "$TMP/codex-stubbin/codex"
if PATH="$TMP/codex-stubbin:$PATH" CODEX_HOME="$TMP/codex_headless_home" CODEX_STUB_ARGV="$TMP/codex-start.argv" \
  "$CODEX" dispatch --start --worktree "$TMP/repo" --slug nested/codex-start --capability autopilot-code --mode dev/backend --qa standard --prompt-text "nested work" --jobs "$TMP/codex-start.log" --log-dir "$TMP/codex-logs" >/tmp/codex_dispatch_start.out 2>/tmp/codex_dispatch_start.err \
  && grep -q '^status=start$' /tmp/codex_dispatch_start.out \
  && grep -q '^started=1$' /tmp/codex_dispatch_start.out \
  && [ -f "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" ] \
  && grep -q 'Read adapters/codex/AGENTS.md first' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh route autopilot-code . codex-headless' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh mode-info dev/backend' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh qa-policy standard code' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'Autopilot-code execution contract' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'code-plan -> code-execute -> code-test -> code-report' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh mode-info qa/plan-review' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh mode-info qa/test' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'preflight.sh role fast reviewer' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'pipeline_summary.md' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'Do not claim independent QA delegation' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'Do not use adapters/claude' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt" \
  && grep -q 'nested work' "$TMP/codex-logs/nested/codex-start.codex.prompt.txt"; then
  for _ in $(seq 1 20); do
    [ -f "$TMP/codex-start.argv" ] && break
    sleep 0.1
  done
  if grep -q -- '--cd' "$TMP/codex-start.argv" 2>/dev/null; then
    ok "codex dispatch wrapper starts nested slug after runtime projection check"
  else
    bad "codex dispatch wrapper should launch codex exec after projection check"
  fi
else
  bad "codex dispatch wrapper should start nested slug after runtime projection check"
fi
if PATH="$TMP/codex-stubbin:$PATH" CODEX_HOME="$TMP/codex_headless_home" CODEX_STUB_ARGV="$TMP/codex-strict-start.argv" \
  "$CODEX" dispatch --start --require-hook-trust --worktree "$TMP/repo" --slug codex-strict-start --capability autopilot-code --mode dev/backend --qa standard --prompt-text "strict work" --jobs "$TMP/codex-strict-start.log" --log-dir "$TMP/codex-strict-logs" >/tmp/codex_dispatch_strict_start.out 2>/tmp/codex_dispatch_strict_start.err; then
  bad "codex dispatch strict start should fail when hook trust is incomplete"
else
  if grep -q '^check=hook-trust:review-needed' /tmp/codex_dispatch_strict_start.out \
    && [ ! -e "$TMP/codex-strict-start.log" ] \
    && [ ! -e "$TMP/codex-strict-logs/codex-strict-start.codex.prompt.txt" ]; then
    ok "codex dispatch strict start fails before registry writes when hook trust is incomplete"
  else
    bad "codex dispatch strict start should fail before registry writes"
  fi
fi
if "$CODEX" dispatch --register --worktree "$TMP/repo" --slug codex-dispatch --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" --jobs "$TMP/codex-dispatch.log" >/tmp/codex_dispatch.out 2>/tmp/codex_dispatch.err \
  && grep -q '^status=register$' /tmp/codex_dispatch.out \
  && grep -q '^registered=1$' /tmp/codex_dispatch.out \
  && grep -q '^started=0$' /tmp/codex_dispatch.out \
  && grep -q $'open\t.*/repo\t.*/repo\tcodex-dispatch\tcapability=autopilot-code,mode=dev/backend,qa=standard' "$TMP/codex-dispatch.log"; then
  ok "codex dispatch wrapper registers open headless job"
else
  bad "codex dispatch wrapper should register open headless job"
fi
if "$CODEX" harvest --jobs "$TMP/codex-dispatch.log" --slug codex-dispatch >/tmp/codex_harvest.out 2>/tmp/codex_harvest.err \
  && grep -q '^adapter=codex$' /tmp/codex_harvest.out \
  && grep -q '^runtime_surface=codex-dispatch-harvest$' /tmp/codex_harvest.out \
  && grep -q '^matched=1$' /tmp/codex_harvest.out \
  && grep -q '^marked_done=0$' /tmp/codex_harvest.out \
  && grep -q '^job_status=open$' /tmp/codex_harvest.out \
  && grep -q '^merge_action=unsupported$' /tmp/codex_harvest.out; then
  ok "codex harvest wrapper reports open registry jobs"
else
  bad "codex harvest wrapper should report open registry jobs"
fi
if "$CODEX" harvest --jobs "$TMP/codex-dispatch.log" --slug codex-dispatch --mark-done >/tmp/codex_harvest_done.out 2>/tmp/codex_harvest_done.err \
  && grep -q '^marked_done=1$' /tmp/codex_harvest_done.out \
  && grep -q $'done\t.*/repo\t.*/repo\tcodex-dispatch\tcapability=autopilot-code,mode=dev/backend,qa=standard' "$TMP/codex-dispatch.log"; then
  ok "codex harvest wrapper marks selected jobs done"
else
  bad "codex harvest wrapper should mark selected jobs done"
fi
mkdir -p "$TMP/codex-live-sessions/2026/06/30"
cat > "$TMP/codex-live-sessions/2026/06/30/rollout-live-codex.jsonl" <<EOF
{"timestamp":"2026-06-30T00:00:00.000Z","type":"session_meta","payload":{"id":"live-codex","cwd":"$TMP/flowproj"}}
EOF
touch "$TMP/codex-live-sessions/2026/06/30/rollout-live-codex.jsonl"
printf '2026-06-30T00:00:00Z\topen\t%s\t%s\tlive-codex\t-\n' "$TMP/repo" "$TMP/flowproj" > "$TMP/codex-jobs.log"
if CODEX_SESSIONS="$TMP/codex-live-sessions" DISPATCH_STALE_MIN=60 "$CODEX" liveness "$TMP/codex-jobs.log" >/tmp/codex_liveness.out 2>/tmp/codex_liveness.err \
  && grep -q '^ALIVE    live-codex ' /tmp/codex_liveness.out \
  && grep -q '^open 1 ; alive 1 ; suspect/dead 0$' /tmp/codex_liveness.out; then
  ok "codex liveness wrapper matches worktree to session transcript"
else
  bad "codex liveness wrapper should match worktree to session transcript"
fi
printf '2026-06-30T00:00:00Z\topen\t%s\t%s\tdead-codex\t-\n' "$TMP/repo" "$TMP/missing-live-wt" > "$TMP/codex-dead-jobs.log"
if CODEX_SESSIONS="$TMP/codex-live-sessions" "$CODEX" liveness "$TMP/codex-dead-jobs.log" >/tmp/codex_liveness_dead.out 2>/tmp/codex_liveness_dead.err; then
  bad "codex liveness wrapper should fail dead jobs"
else
  rc=$?
  if [ "$rc" -eq 3 ] \
    && grep -q '^DEAD     dead-codex ' /tmp/codex_liveness_dead.out \
    && grep -q '^open 1 ; alive 0 ; suspect/dead 1$' /tmp/codex_liveness_dead.out; then
    ok "codex liveness wrapper reports dead jobs"
  else
    bad "codex liveness wrapper should report dead jobs"
  fi
fi
if "$CODEX" mcp >/tmp/codex_mcp.out 2>/tmp/codex_mcp.err \
  && grep -q '^adapter=codex$' /tmp/codex_mcp.out \
  && grep -q '^runtime_surface=codex-native-mcp$' /tmp/codex_mcp.out \
  && grep -q '^mcp_surface=codex mcp$' /tmp/codex_mcp.out \
  && grep -q '^design_mcp_projection=unsupported$' /tmp/codex_mcp.out \
  && grep -q '^claude_settings_mcp=unsupported$' /tmp/codex_mcp.out; then
  ok "codex mcp wrapper reports native MCP contract"
else
  bad "codex mcp wrapper should report native MCP contract"
fi
if "$CODEX" mcp --check >/tmp/codex_mcp_check.out 2>/tmp/codex_mcp_check.err \
  && grep -q '^check=ok$' /tmp/codex_mcp_check.out; then
  ok "codex mcp wrapper checks native MCP CLI"
else
  bad "codex mcp wrapper should check native MCP CLI"
fi
if "$CODEX" ui-info >/tmp/codex_ui.out 2>/tmp/codex_ui.err \
  && grep -q '^adapter=codex$' /tmp/codex_ui.out \
  && grep -q '^runtime_surface=codex-native-ui-boundary$' /tmp/codex_ui.out \
  && grep -q '^statusline_surface=codex-native-footer-config$' /tmp/codex_ui.out \
  && grep -q '^statusline_custom_dynamic_fields=unsupported$' /tmp/codex_ui.out \
  && grep -q '^statusline_fragment=codex_setting/codex-config/tui-statusline.toml$' /tmp/codex_ui.out \
  && grep -q '^harness_status_surface=adapter-owned-preflight-status$' /tmp/codex_ui.out \
  && grep -q '^autopilot_entrypoints=codex-native-skills-plugin$' /tmp/codex_ui.out \
  && grep -q '^autopilot_auto_routing=instruction-guided-not-claude-slash-router$' /tmp/codex_ui.out \
  && grep -q '^subagent_auto_spawn=explicit-or-main-dispatched$' /tmp/codex_ui.out; then
  ok "codex ui-info reports native UI and parity boundaries"
else
  bad "codex ui-info should report native UI and parity boundaries"
fi
TUIHOME="$TMP/codex-tui-home"
rm -rf "$TUIHOME"; mkdir -p "$TUIHOME"
cat > "$TUIHOME/config.toml" <<'EOF'
model = "keep-me"

[tui]
status_line = ["old"]

[hooks.state]
"example" = "keep"
EOF
if AGENT_HOME="$ROOT" CODEX_HOME="$TUIHOME" "$CODEX" tui-config >/tmp/codex_tui.out 2>/tmp/codex_tui.err \
  && grep -q '^status=ok$' /tmp/codex_tui.out \
  && grep -q '^changed=yes$' /tmp/codex_tui.out \
  && grep -Fq 'status_line = ["project-name", "git-branch", "context-used", "current-dir", "model-with-reasoning", "five-hour-limit", "weekly-limit"]' "$TUIHOME/config.toml" \
  && grep -Fq 'status_line_use_colors = true' "$TUIHOME/config.toml" \
  && grep -Fq 'model = "keep-me"' "$TUIHOME/config.toml" \
  && grep -Fq '[hooks.state]' "$TUIHOME/config.toml" \
  && [ -f "$TUIHOME/config.toml.pre-harness-tui" ]; then
  ok "codex tui-config applies only harness statusline keys"
else
  bad "codex tui-config should apply only harness statusline keys"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$TUIHOME" "$CODEX" tui-config >/tmp/codex_tui2.out 2>/tmp/codex_tui2.err \
  && grep -q '^changed=no$' /tmp/codex_tui2.out; then
  ok "codex tui-config is idempotent"
else
  bad "codex tui-config should be idempotent"
fi
if "$CODEX" loop-info oncall >/tmp/codex_loop_oncall.out 2>/tmp/codex_loop_oncall.err \
  && grep -q '^adapter=codex$' /tmp/codex_loop_oncall.out \
  && grep -q '^loop=oncall$' /tmp/codex_loop_oncall.out \
  && grep -q '^source=loops/oncall.md$' /tmp/codex_loop_oncall.out \
  && grep -q '^status=manual-contract$' /tmp/codex_loop_oncall.out \
  && grep -q '^runtime_surface=codex-loop-guidance$' /tmp/codex_loop_oncall.out \
  && grep -q '^executable_projection=unsupported-runtime-script$' /tmp/codex_loop_oncall.out; then
  ok "codex loop wrapper reports oncall manual contract"
else
  bad "codex loop wrapper should report oncall manual contract"
fi
if "$CODEX" loop-info drill >/tmp/codex_loop_drill.out 2>/tmp/codex_loop_drill.err \
  && grep -q '^source=loops/drill/README.md$' /tmp/codex_loop_drill.out \
  && grep -q '^status=manual-contract$' /tmp/codex_loop_drill.out \
  && grep -q '^trigger=manual-only$' /tmp/codex_loop_drill.out \
  && grep -q '^auto_run=unsupported$' /tmp/codex_loop_drill.out \
  && grep -q '^fallback=report-drill-would-be-useful$' /tmp/codex_loop_drill.out; then
  ok "codex loop wrapper prevents automatic drill execution"
else
  bad "codex loop wrapper should prevent automatic drill execution"
fi
if "$CODEX" loop-info study >/tmp/codex_loop_study.out 2>/tmp/codex_loop_study.err \
  && grep -q '^source=loops/study.md$' /tmp/codex_loop_study.out \
  && grep -q '^status=manual-contract$' /tmp/codex_loop_study.out \
  && grep -q '^action=proposal-report-only$' /tmp/codex_loop_study.out \
  && grep -q '^fallback=read-source-and-draft-proposal-in-main-session$' /tmp/codex_loop_study.out; then
  ok "codex loop wrapper reports study proposal contract"
else
  bad "codex loop wrapper should report study proposal contract"
fi
if "$CODEX" loop-info note >/tmp/codex_loop_note.out 2>/tmp/codex_loop_note.err \
  && grep -q '^loop=note$' /tmp/codex_loop_note.out \
  && grep -q '^status=unsupported$' /tmp/codex_loop_note.out \
  && grep -q '^runtime_surface=missing-native-loop$' /tmp/codex_loop_note.out \
  && grep -q '^related_capability=autopilot-note$' /tmp/codex_loop_note.out \
  && grep -q '^native_capability_surface=codex-native-skill-plugin$' /tmp/codex_loop_note.out \
  && grep -q '^scheduler_surface=external-worklog-board$' /tmp/codex_loop_note.out \
  && grep -q '^fallback=worklog-board-or-manual-post-it-flow$' /tmp/codex_loop_note.out; then
  ok "codex loop wrapper marks missing note loop unsupported"
else
  bad "codex loop wrapper should mark missing note loop unsupported"
fi
if AGENT_MODEL_FAST=fast-model AGENT_REASONING_FAST=low "$CODEX" role fast reviewer >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^family=fast$' /tmp/role.out \
  && grep -q '^adapter=codex$' /tmp/role.out \
  && grep -q '^source=roles/README.md$' /tmp/role.out \
  && grep -q '^model=fast-model$' /tmp/role.out \
  && grep -q '^reasoning=low$' /tmp/role.out; then
  ok "codex role wrapper maps fast portable role"
else
  bad "codex role wrapper should map fast portable role"
fi
if "$CODEX" role variable reviewer >/tmp/role_set.out 2>/tmp/role_set.err \
  && grep -q '^role=variable reviewer$' /tmp/role_set.out \
  && grep -q '^family=role-set$' /tmp/role_set.out \
  && grep -q '^role_set=fast reviewer,deep reviewer,external adversary$' /tmp/role_set.out \
  && grep -q '^reasoning=select-by-mode$' /tmp/role_set.out \
  && "$CODEX" role 'deep maker plus fast tool worker' >/tmp/role_set_material.out 2>/tmp/role_set_material.err \
  && grep -q '^role_set=deep maker,fast tool worker$' /tmp/role_set_material.out; then
  ok "codex role wrapper reports mixed role sets"
else
  bad "codex role wrapper should report mixed role sets"
fi
if AGENT_MODEL_ORCHESTRATOR=orchestrator-model AGENT_REASONING_ORCHESTRATOR=medium "$CODEX" role external adversary orchestrator >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^family=orchestrator$' /tmp/role.out \
  && grep -q '^adapter=codex$' /tmp/role.out \
  && grep -q '^model=orchestrator-model$' /tmp/role.out \
  && grep -q '^reasoning=medium$' /tmp/role.out \
  && grep -q '^available=1$' /tmp/role.out \
  && grep -q '^status=configured$' /tmp/role.out; then
  ok "codex role wrapper maps external adversary orchestrator role"
else
  bad "codex role wrapper should map external adversary orchestrator role"
fi
if "$CODEX" role external adversary >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^available=0$' /tmp/role.out \
  && grep -q '^status=unavailable$' /tmp/role.out; then
  ok "codex role wrapper marks external adversary unavailable by default"
else
  bad "codex role wrapper should mark external adversary unavailable by default"
fi
if AGENT_MODEL_EXTERNAL=external-model AGENT_REASONING_EXTERNAL=high "$CODEX" role external adversary >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^family=external$' /tmp/role.out \
  && grep -q '^available=1$' /tmp/role.out \
  && grep -q '^status=configured$' /tmp/role.out \
  && grep -q '^model=external-model$' /tmp/role.out \
  && grep -q '^reasoning=high$' /tmp/role.out; then
  ok "codex role wrapper maps configured external adversary model"
else
  bad "codex role wrapper should map configured external adversary model"
fi
if AGENT_EXTERNAL_CMD="sh -c" "$CODEX" role external adversary >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^available=1$' /tmp/role.out \
  && grep -q '^status=configured$' /tmp/role.out \
  && grep -q '^model=external-command$' /tmp/role.out \
  && grep -q '^external_command=sh -c$' /tmp/role.out; then
  ok "codex role wrapper accepts external adversary command with args"
else
  bad "codex role wrapper should accept external adversary command with args"
fi
if AGENT_EXTERNAL_CMD="missing-external-adversary-command --review" "$CODEX" role external adversary >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^available=0$' /tmp/role.out \
  && grep -q '^status=unavailable$' /tmp/role.out \
  && grep -q '^reason=AGENT_EXTERNAL_CMD not found: missing-external-adversary-command$' /tmp/role.out; then
  ok "codex role wrapper reports missing external adversary command"
else
  bad "codex role wrapper should report missing external adversary command"
fi
if "$CODEX" qa-policy adversarial code >/tmp/codex_qa_policy.out 2>/tmp/codex_qa_policy.err \
  && grep -q '^runtime_surface=codex-qa-policy$' /tmp/codex_qa_policy.out \
  && grep -q '^source=core/CONVENTIONS.md$' /tmp/codex_qa_policy.out \
  && grep -q '^qa_level=adversarial$' /tmp/codex_qa_policy.out \
  && grep -q '^qa_track=code$' /tmp/codex_qa_policy.out \
  && grep -q '^fact_checker=skip-code-track$' /tmp/codex_qa_policy.out \
  && grep -q '^external_adversary=1x-external-adversary$' /tmp/codex_qa_policy.out \
  && grep -q '^codex_role_checks=.*preflight.sh role external adversary' /tmp/codex_qa_policy.out \
  && grep -q '^independent_delegation_policy=claim-only-if-separate-codex-agent-headless-or-external-pass-ran$' /tmp/codex_qa_policy.out; then
  ok "codex qa-policy maps QA level to reviewer and fallback contract"
else
  bad "codex qa-policy should map QA level to reviewer and fallback contract"
fi
if "$CODEX" capability-info autopilot-code >/tmp/cap.out 2>/tmp/cap.err \
  && grep -q '^capability=autopilot-code$' /tmp/cap.out \
  && grep -q '^adapter=codex$' /tmp/cap.out \
  && grep -q '^native_skill=1$' /tmp/cap.out \
  && grep -q '^native_skill_path=adapters/codex/skills/autopilot-code/SKILL.md$' /tmp/cap.out \
  && grep -q '^native_plugin=1$' /tmp/cap.out \
  && grep -q '^native_plugin_skill_path=adapters/codex/plugins/agent-harness-codex/skills/autopilot-code/SKILL.md$' /tmp/cap.out \
  && grep -q '^realization=codex-native-skill-plugin$' /tmp/cap.out \
  && grep -q '^compat_reference=not-projected$' /tmp/cap.out \
  && ! grep -q '^compat_reference=skills/' /tmp/cap.out \
  && grep -q '^status=instruction-only$' /tmp/cap.out \
  && grep -q '^pipeline_contract=code-plan>code-execute>code-test>code-report$' /tmp/cap.out \
  && grep -q '^optional_pipeline_step=code-refine$' /tmp/cap.out \
  && grep -q '^artifact_contract=plans/<date>_<slug>:plan.md,checklist.md,pipeline_summary.md,dev_logs/,test_logs/$' /tmp/cap.out \
  && grep -q '^role_contract=planning=plan-team,implementation=dev-team,verification=qa-team,report=editorial-team$' /tmp/cap.out \
  && grep -q '^dispatch_contract=preflight.sh dispatch --capability autopilot-code --mode <family/mode> --qa <level>$' /tmp/cap.out; then
  ok "codex capability wrapper reports native skill and plugin realization"
else
  bad "codex capability wrapper should report native skill and plugin realization"
fi
if "$CODEX" capability-info code-test >/tmp/cap_code_test.out 2>/tmp/cap_code_test.err \
  && grep -q '^capability=code-test$' /tmp/cap_code_test.out \
  && grep -q '^native_skill=1$' /tmp/cap_code_test.out \
  && grep -q '^native_plugin=1$' /tmp/cap_code_test.out \
  && grep -q '^status=tool-contract$' /tmp/cap_code_test.out \
  && grep -q '^tool_contract=verification-runner$' /tmp/cap_code_test.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh verification-runner --check -- <command>$' /tmp/cap_code_test.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/cap_code_test.out \
  && grep -q '^artifact_contract=plans/<date>_<slug>:test_logs/,pipeline_summary.md$' /tmp/cap_code_test.out \
  && grep -q '^role_contract=verification=qa-team,review=qa-team$' /tmp/cap_code_test.out \
  && grep -q 'graduated verification' "$ROOT/adapters/codex/skills/code-test/SKILL.md" \
  && grep -q 'verification-runner' "$ROOT/adapters/codex/plugins/agent-harness-codex/skills/code-test/SKILL.md"; then
  ok "codex code-test capability reports verification-runner contract"
else
  bad "codex code-test capability should report verification-runner contract"
fi
if "$CODEX" capability-info design-review >/tmp/cap.out 2>/tmp/cap.err \
  && grep -q '^capability=design-review$' /tmp/cap.out \
  && grep -q '^native_skill=1$' /tmp/cap.out \
  && grep -q '^native_plugin=1$' /tmp/cap.out \
  && grep -q '^realization=codex-native-skill-plugin$' /tmp/cap.out \
  && grep -q '^status=tool-contract$' /tmp/cap.out \
  && grep -q '^tool_contract=visual-harness$' /tmp/cap.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh visual-harness <file.html>$' /tmp/cap.out \
  && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/cap.out \
  && grep -q '^fallback=preflight.sh visual-harness <file.html>$' /tmp/cap.out; then
  ok "codex design capability reports visual harness contract"
else
  bad "codex design capability should report visual harness contract"
fi
if "$CODEX" visual-harness >/tmp/codex_visual.out 2>/tmp/codex_visual.err; then
  if grep -q '^adapter=codex$' /tmp/codex_visual.out \
    && grep -q '^status=tool-contract$' /tmp/codex_visual.out \
    && grep -q '^tool_contract=visual-harness$' /tmp/codex_visual.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/codex_visual.out \
    && ! grep -q 'adapters/claude\|claude_setting\|settings.json\|statusline.sh' /tmp/codex_visual.out; then
    ok "codex visual harness reports adapter-native tool-contract"
  else
    bad "codex visual harness should report adapter-native tool-contract"
  fi
else
  bad "codex visual harness should report adapter-native tool-contract"
fi
cat >"$TMP/codex-preview.html" <<'EOF'
<!doctype html><html><body><h1>Codex visual harness</h1></body></html>
EOF
if "$CODEX" visual-harness "$TMP/codex-preview.html" --out "$TMP/codex-visual" >/tmp/codex_visual_file.out 2>/tmp/codex_visual_file.err; then
  if grep -q '^adapter=codex$' /tmp/codex_visual_file.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/codex_visual_file.out \
    && grep -q '^status=ok$' /tmp/codex_visual_file.out \
    && grep -q '^console_errors=0$' /tmp/codex_visual_file.out \
    && [ -f "$TMP/codex-visual/codex-preview-html.png" ]; then
    ok "codex visual harness renders HTML when checker dependencies exist"
  else
    bad "codex visual harness should render HTML when checker dependencies exist"
  fi
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=codex$' /tmp/codex_visual_file.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/codex_visual_file.out \
    && grep -q '^status=tool-contract$' /tmp/codex_visual_file.out \
    && grep -q '^reason=playwright-unavailable$' /tmp/codex_visual_file.out; then
    ok "codex visual harness reports unavailable checker dependency"
  else
    bad "codex visual harness should render or report unavailable checker dependency"
  fi
fi
cat >"$TMP/codex-data-script.py" <<'EOF'
import sys

print("rows=3")
print("args=" + ",".join(sys.argv[1:]))
EOF
if "$CODEX" data-script --check "$TMP/codex-data-script.py" >/tmp/codex_data_script.out 2>/tmp/codex_data_script.err \
  && grep -q '^adapter=codex$' /tmp/codex_data_script.out \
  && grep -q '^tool_contract=data-script$' /tmp/codex_data_script.out \
  && grep -q '^runtime_surface=adapter-owned-data-script$' /tmp/codex_data_script.out \
  && grep -q '^check=python-compile$' /tmp/codex_data_script.out \
  && grep -q '^status=ok$' /tmp/codex_data_script.out; then
  ok "codex data-script wrapper checks Python analysis scripts"
else
  bad "codex data-script wrapper should check Python analysis scripts"
fi
if "$CODEX" claim-verify >/tmp/codex_claim_verify.out 2>/tmp/codex_claim_verify.err \
  && grep -q '^adapter=codex$' /tmp/codex_claim_verify.out \
  && grep -q '^tool_contract=external-claim-verification$' /tmp/codex_claim_verify.out \
  && grep -q '^runtime_surface=adapter-owned-claim-verify$' /tmp/codex_claim_verify.out \
  && grep -q '^status=tool-contract$' /tmp/codex_claim_verify.out; then
  ok "codex claim-verify wrapper reports tool contract"
else
  bad "codex claim-verify wrapper should report tool contract"
fi
if "$CODEX" claim-verify --check "model X is state of the art" >/tmp/codex_claim_unavailable.out 2>/tmp/codex_claim_unavailable.err; then
  bad "codex claim-verify wrapper should report unavailable provider by default"
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=codex$' /tmp/codex_claim_unavailable.out \
    && grep -q '^reason=claim-verify-provider-unavailable$' /tmp/codex_claim_unavailable.out; then
    ok "codex claim-verify wrapper reports unavailable provider"
  else
    bad "codex claim-verify wrapper should report unavailable provider"
  fi
fi
if "$CODEX" figure-gen >/tmp/codex_figure_gen.out 2>/tmp/codex_figure_gen.err \
  && grep -q '^adapter=codex$' /tmp/codex_figure_gen.out \
  && grep -q '^tool_contract=figure-gen$' /tmp/codex_figure_gen.out \
  && grep -q '^runtime_surface=adapter-owned-figure-gen$' /tmp/codex_figure_gen.out \
  && grep -q '^status=tool-contract$' /tmp/codex_figure_gen.out; then
  ok "codex figure-gen wrapper reports tool contract"
else
  bad "codex figure-gen wrapper should report tool contract"
fi
if "$CODEX" figure-gen --check "$TMP/missing-figure.py" >/tmp/codex_figure_missing.out 2>/tmp/codex_figure_missing.err; then
  bad "codex figure-gen wrapper should fail missing script"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^adapter=codex$' /tmp/codex_figure_missing.out \
    && grep -q '^reason=file-not-found$' /tmp/codex_figure_missing.out; then
    ok "codex figure-gen wrapper reports missing script"
  else
    bad "codex figure-gen wrapper should report missing script"
  fi
fi
if "$CODEX" browser-fetch >/tmp/codex_browser_fetch.out 2>/tmp/codex_browser_fetch.err \
  && grep -q '^adapter=codex$' /tmp/codex_browser_fetch.out \
  && grep -q '^tool_contract=browser-fetch$' /tmp/codex_browser_fetch.out \
  && grep -q '^runtime_surface=adapter-owned-browser-fetch$' /tmp/codex_browser_fetch.out \
  && grep -q '^status=tool-contract$' /tmp/codex_browser_fetch.out; then
  ok "codex browser-fetch wrapper reports tool contract"
else
  bad "codex browser-fetch wrapper should report tool contract"
fi
if "$CODEX" browser-fetch --check not-a-url >/tmp/codex_browser_bad_url.out 2>/tmp/codex_browser_bad_url.err; then
  bad "codex browser-fetch wrapper should fail bad URL"
else
  rc=$?
  if [ "$rc" -eq 65 ] \
    && grep -q '^adapter=codex$' /tmp/codex_browser_bad_url.out \
    && grep -q '^reason=bad-url$' /tmp/codex_browser_bad_url.out; then
    ok "codex browser-fetch wrapper reports bad URL"
  else
    bad "codex browser-fetch wrapper should report bad URL"
  fi
fi
if "$CODEX" pdf-extract >/tmp/codex_pdf_extract.out 2>/tmp/codex_pdf_extract.err \
  && grep -q '^adapter=codex$' /tmp/codex_pdf_extract.out \
  && grep -q '^tool_contract=pdf-extract$' /tmp/codex_pdf_extract.out \
  && grep -q '^runtime_surface=adapter-owned-pdf-extract$' /tmp/codex_pdf_extract.out \
  && grep -q '^status=tool-contract$' /tmp/codex_pdf_extract.out; then
  ok "codex pdf-extract wrapper reports tool contract"
else
  bad "codex pdf-extract wrapper should report tool contract"
fi
if "$CODEX" pdf-extract --check "$TMP/missing.pdf" >/tmp/codex_pdf_missing.out 2>/tmp/codex_pdf_missing.err; then
  bad "codex pdf-extract wrapper should fail missing PDF"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^adapter=codex$' /tmp/codex_pdf_missing.out \
    && grep -q '^reason=file-not-found$' /tmp/codex_pdf_missing.out; then
    ok "codex pdf-extract wrapper reports missing PDF"
  else
    bad "codex pdf-extract wrapper should report missing PDF"
  fi
fi
if "$CODEX" web-image-search >/tmp/codex_web_image.out 2>/tmp/codex_web_image.err \
  && grep -q '^adapter=codex$' /tmp/codex_web_image.out \
  && grep -q '^tool_contract=web-image-search$' /tmp/codex_web_image.out \
  && grep -q '^runtime_surface=adapter-owned-web-image-search$' /tmp/codex_web_image.out \
  && grep -q '^status=tool-contract$' /tmp/codex_web_image.out; then
  ok "codex web-image-search wrapper reports tool contract"
else
  bad "codex web-image-search wrapper should report tool contract"
fi
if "$CODEX" web-image-search --check "speech enhancement timeline" >/tmp/codex_web_image_unavailable.out 2>/tmp/codex_web_image_unavailable.err; then
  bad "codex web-image-search wrapper should report unavailable provider by default"
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=codex$' /tmp/codex_web_image_unavailable.out \
    && grep -q '^reason=web-image-search-provider-unavailable$' /tmp/codex_web_image_unavailable.out; then
    ok "codex web-image-search wrapper reports unavailable provider"
  else
    bad "codex web-image-search wrapper should report unavailable provider"
  fi
fi
if "$CODEX" verification-runner --check -- python3 >/tmp/codex_verify_check.out 2>/tmp/codex_verify_check.err \
  && grep -q '^adapter=codex$' /tmp/codex_verify_check.out \
  && grep -q '^tool_contract=verification-runner$' /tmp/codex_verify_check.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/codex_verify_check.out \
  && grep -q '^check=command-available$' /tmp/codex_verify_check.out \
  && grep -q '^status=ok$' /tmp/codex_verify_check.out; then
  ok "codex verification runner checks explicit commands"
else
  bad "codex verification runner should check explicit commands"
fi
if "$CODEX" verification-runner --timeout 5 -- python3 -c 'print("verify-ok")' >/tmp/codex_verify_run.out 2>/tmp/codex_verify_run.err \
  && grep -q '^adapter=codex$' /tmp/codex_verify_run.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/codex_verify_run.out \
  && grep -q '^status=ok$' /tmp/codex_verify_run.out \
  && grep -q '^exit_code=0$' /tmp/codex_verify_run.out \
  && grep -q 'verify-ok' /tmp/codex_verify_run.out; then
  ok "codex verification runner executes explicit commands"
else
  bad "codex verification runner should execute explicit commands"
fi
if grep -q '## Projected Portable Details' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'spec-significance' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'pipeline_summary.md' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'code-plan' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'code-execute' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'code-test' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'code-report' "$ROOT/adapters/codex/skills/autopilot-code/SKILL.md" \
  && grep -q 'spec-significance' "$ROOT/adapters/codex/plugins/agent-harness-codex/skills/autopilot-code/SKILL.md"; then
  ok "codex native skill projection carries portable autopilot-code procedure"
else
  bad "codex native skill projection should carry portable autopilot-code procedure"
fi
if command -v codex >/dev/null 2>&1; then
  mkdir -p "$TMP/codex_bootstrap_home"
  ln -s "$ROOT/codex_setting/AGENTS.md" "$TMP/codex_bootstrap_home/AGENTS.md"
  if CODEX_HOME="$TMP/codex_bootstrap_home" codex debug prompt-input 'bootstrap check' >/tmp/codex_bootstrap.out 2>/tmp/codex_bootstrap.err \
    && grep -q 'AGENTS.md — Codex Adapter Bootstrap' /tmp/codex_bootstrap.out \
    && grep -q 'adapters/codex/bin/preflight.sh capability-info' /tmp/codex_bootstrap.out \
    && grep -q 'codex_setting/codex-hooks' /tmp/codex_bootstrap.out \
    && ! grep -q 'adapters/claude/CLAUDE.md.*portable bootstrap' /tmp/codex_bootstrap.out; then
    ok "codex bootstrap projection is discoverable without Claude bootstrap"
  else
    bad "codex bootstrap projection should be discoverable without Claude bootstrap"
  fi
else
  ok "codex bootstrap runtime discovery skipped (codex not installed)"
fi
if command -v codex >/dev/null 2>&1; then
  mkdir -p "$TMP/codex_home/skills"
  for d in "$ROOT"/codex_setting/codex-skills/*; do
    [ -d "$d" ] || continue
    ln -s "$d" "$TMP/codex_home/skills/$(basename "$d")"
  done
  if CODEX_HOME="$TMP/codex_home" codex debug prompt-input 'autopilot-code' >/tmp/codex_skills.out 2>/tmp/codex_skills.err \
    && grep -q -- '- autopilot-code:' /tmp/codex_skills.out \
    && grep -q 'Read the portable capability spec and run the Codex preflight wrapper' /tmp/codex_skills.out \
    && ! grep -q '/.claude/skills' /tmp/codex_skills.out; then
    ok "codex native skill projection is discoverable without Claude skill paths"
  else
    bad "codex native skill projection should be discoverable without Claude skill paths"
  fi
else
  ok "codex native skill runtime discovery skipped (codex not installed)"
fi
if command -v codex >/dev/null 2>&1; then
  mkdir -p "$TMP/codex_plugin_home"
  if [ -f "$ROOT/codex_setting/codex-plugin-marketplace/.agents/plugins/marketplace.json" ] \
    && [ -L "$ROOT/codex_setting/codex-plugin-marketplace/plugins/agent-harness-codex" ] \
    && [ ! -e "$ROOT/codex_setting/codex-plugin-marketplace/bin" ] \
    && [ ! -e "$ROOT/codex_setting/codex-plugin-marketplace/hooks" ] \
    && CODEX_HOME="$TMP/codex_plugin_home" codex plugin marketplace add "$ROOT/codex_setting/codex-plugin-marketplace" --json >/tmp/codex_plugin_marketplace.out 2>/tmp/codex_plugin_marketplace.err \
    && CODEX_HOME="$TMP/codex_plugin_home" codex plugin list --available --json >/tmp/codex_plugin_list.out 2>/tmp/codex_plugin_list.err \
    && grep -q '"pluginId": "agent-harness-codex@agent-harness"' /tmp/codex_plugin_list.out \
    && CODEX_HOME="$TMP/codex_plugin_home" codex plugin add agent-harness-codex@agent-harness --json >/tmp/codex_plugin_add.out 2>/tmp/codex_plugin_add.err \
    && CODEX_HOME="$TMP/codex_plugin_home" codex debug prompt-input 'autopilot-code' >/tmp/codex_plugin_prompt.out 2>/tmp/codex_plugin_prompt.err \
    && grep -q -- '- agent-harness-codex:autopilot-code:' /tmp/codex_plugin_prompt.out \
    && ! grep -q 'adapters/claude/skills' /tmp/codex_plugin_prompt.out; then
    ok "codex native plugin projection is installable and discovers generated skills"
  else
    bad "codex native plugin projection should be installable and discover generated skills"
  fi
else
  ok "codex native plugin runtime discovery skipped (codex not installed)"
fi
mkdir -p "$TMP/codex_agent_home/agents"
for f in "$ROOT"/codex_setting/codex-agents/*.toml; do
  [ -f "$f" ] || continue
  ln -s "$f" "$TMP/codex_agent_home/agents/$(basename "$f")"
done
if python3 - "$TMP/codex_agent_home/agents" >/tmp/codex_agents.out 2>/tmp/codex_agents.err <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
agents = sorted(root.glob("*.toml"))
if len(agents) != 8:
    raise SystemExit(f"expected 8 Codex agents, got {len(agents)}")
for agent in agents:
    body = agent.read_text(encoding="utf-8")
    for key in ("name", "description"):
        if not re.search(rf'^{key} = "[^"]+"$', body, re.MULTILINE):
            raise SystemExit(f"{agent.name}: missing {key}")
    if not re.search(r'^developer_instructions = """\n.+\n"""$', body, re.MULTILINE | re.DOTALL):
        raise SystemExit(f"{agent.name}: missing developer_instructions")
    forbidden = ("adapters/claude/agents", "claude_setting", "adapters/opencode", "opencode_setting")
    if any(item in body for item in forbidden):
        raise SystemExit(f"{agent.name}: leaked non-Codex adapter path")
PY
then
  ok "codex native agent projection has valid custom agent TOML without Claude paths"
else
  bad "codex native agent projection should have valid custom agent TOML without Claude paths"
fi
if grep -q 'Read-only role: do not edit, write, or mutate source files or artifacts' "$TMP/codex_agent_home/agents/qa-team.toml" \
  && grep -q 'Stay depth-one: do not spawn nested agents' "$TMP/codex_agent_home/agents/qa-team.toml" \
  && grep -q 'preflight.sh qa-policy <level> <track>' "$TMP/codex_agent_home/agents/qa-team.toml" \
  && grep -q 'preflight.sh mode-info qa/test' "$TMP/codex_agent_home/agents/qa-team.toml" \
  && grep -q 'report unavailable instead of simulating independence inline' "$TMP/codex_agent_home/agents/external-adversary.toml" \
  && grep -q 'Codex cannot attach the same shell read/write hooks' "$TMP/codex_agent_home/agents/dev-team.toml"; then
  ok "codex native agent projection enforces role-specific runtime boundaries"
else
  bad "codex native agent projection should encode role-specific runtime boundaries"
fi
if grep -q 'Codex role-map inputs: `fast reviewer, deep reviewer, external adversary`' "$TMP/codex_agent_home/agents/qa-team.toml" \
  && grep -q 'Codex role-map inputs: `fast fact checker, deep reviewer, external adversary`' "$TMP/codex_agent_home/agents/research-team.toml" \
  && grep -q 'Codex role-map inputs: `deep maker, fast tool worker`' "$TMP/codex_agent_home/agents/material-team.toml" \
  && grep -q 'Codex role-map inputs: `deep maker, fast reviewer`' "$TMP/codex_agent_home/agents/editorial-team.toml" \
  && grep -q 'select the concrete role by mode/QA policy' "$TMP/codex_agent_home/agents/qa-team.toml"; then
  ok "codex native agent projection preserves mixed role sets"
else
  bad "codex native agent projection should preserve mixed role sets"
fi
if [ -L "$ROOT/codex_setting/codex-modes" ] \
  && [ "$(readlink "$ROOT/codex_setting/codex-modes")" = "../adapters/codex/modes" ] \
  && "$ROOT/adapters/codex/bin/sync-native-modes.py" --check >/tmp/codex_modes_sync.out 2>/tmp/codex_modes_sync.err \
  && python3 - "$ROOT" >/tmp/codex_modes.out 2>/tmp/codex_modes.err <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
sources = sorted((root / "roles" / "modes").glob("*/*.md"))
modes = sorted((root / "codex_setting" / "codex-modes").glob("*/*.md"))
if len(modes) != len(sources):
    raise SystemExit(f"expected {len(sources)} Codex modes, got {len(modes)}")
for source in sources:
    rel = source.relative_to(root / "roles" / "modes")
    mode = rel.with_suffix("").as_posix()
    native = root / "codex_setting" / "codex-modes" / rel
    body = native.read_text(encoding="utf-8")
    required = [
        f"roles/modes/{mode}.md",
        f"adapters/codex/bin/preflight.sh mode-info {mode}",
        f"adapters/codex/modes/{mode}.md",
        "not a legacy runtime mode copy",
        "Projected Portable Mode Contract",
    ]
    for item in required:
        if item not in body:
            raise SystemExit(f"{rel}: missing {item}")
    forbidden = ("adapters/claude", "claude_setting", "settings.json", "statusline.sh", "CLAUDE.md", "agent-modes", "allowedTools", "Design MCP", "mcp__design__", "tools/design-mcp", "getConsoleLogs", "eval_js")
    if any(item in body for item in forbidden):
        raise SystemExit(f"{rel}: leaked non-Codex runtime surface")
PY
then
  ok "codex native mode projection covers portable modes without Claude paths"
else
  bad "codex native mode projection should cover portable modes without Claude paths"
fi
if [ -L "$ROOT/codex_setting/scaffolds" ] \
  && [ "$(readlink "$ROOT/codex_setting/scaffolds")" = "../adapters/codex/scaffolds" ] \
  && [ -f "$ROOT/codex_setting/scaffolds/deck_stage/deck_stage.html" ] \
  && [ -f "$ROOT/codex_setting/scaffolds/tweaks_panel/tweaks_panel.html" ] \
  && grep -q 'adapter visual harness' "$ROOT/codex_setting/scaffolds/deck_stage/deck_stage.html" \
  && cmp -s "$ROOT/scaffolds/tweaks_panel/tweaks_panel.html" "$ROOT/codex_setting/scaffolds/tweaks_panel/tweaks_panel.html" \
  && ! rg -q 'adapters/claude|claude_setting|~/.claude|Design MCP|design-mcp' "$ROOT/codex_setting/scaffolds"; then
  ok "codex scaffold projection exposes shared design assets without Claude runtime paths"
else
  bad "codex scaffold projection should expose shared design assets without Claude runtime paths"
fi
if grep -q 'Test Levels (execute in order, stop on failure)' "$ROOT/codex_setting/codex-modes/qa/test.md" \
  && grep -q 'Level 5b: Behavioral runtime observation' "$ROOT/codex_setting/codex-modes/qa/test.md" \
  && grep -q 'verification-runner' "$ROOT/codex_setting/codex-modes/qa/test.md" \
  && grep -q 'Codex visual harness' "$ROOT/codex_setting/codex-modes/design/maker.md" \
  && grep -q 'preflight.sh visual-harness <file.html>' "$ROOT/codex_setting/codex-modes/design/maker.md" \
  && grep -q 'preflight.sh visual-harness <file.html>' "$ROOT/codex_setting/codex-modes/design/verifier.md" \
  && grep -q 'adapter skill projections' "$ROOT/codex_setting/codex-modes/research/plan-review.md"; then
  ok "codex native mode projection embeds sanitized portable mode contracts"
else
  bad "codex native mode projection should embed sanitized portable mode contracts"
fi
mkdir -p "$TMP/codex_hook_home/.codex"
ln -s "$ROOT" "$TMP/codex_hook_home/.codex/agent-harness"
ln -s "$ROOT/codex_setting/codex-hooks/hooks.json" "$TMP/codex_hook_home/.codex/hooks.json"
if python3 -m json.tool "$TMP/codex_hook_home/.codex/hooks.json" >/tmp/codex_hook_json.out 2>/tmp/codex_hook_json.err \
  && grep -q 'sessionstart-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q 'sessionend-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q '"Stop"' /tmp/codex_hook_json.out \
  && grep -q 'userprompt-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q 'permissionrequest-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q 'pretooluse-write-guard.py' /tmp/codex_hook_json.out \
  && grep -q 'posttooluse-read-marker.py' /tmp/codex_hook_json.out \
  && grep -q 'posttooluse-design-check.py' /tmp/codex_hook_json.out \
  && grep -Fq 'Write|Edit|MultiEdit|apply_patch|functions\\.apply_patch' /tmp/codex_hook_json.out \
  && printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/f" "$TMP/repo" \
    | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_hook.out 2>/tmp/codex_hook.err \
  && [ ! -s /tmp/codex_hook.out ]; then
  ok "codex native hook projection bridges clean writes to preflight"
else
  bad "codex native hook projection should bridge clean writes to preflight"
fi
if printf '{"tool_name":"Bash","tool_input":{"command":"printf x > %s"},"session_id":"shellwritesid","cwd":"%s"}\n' "$TMP/runtime/projects/abc/memory/SHELL.md" "$TMP/runtime" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_shell_write_hook.out 2>/tmp/codex_shell_write_hook.err \
  && [ ! -s /tmp/codex_shell_write_hook.out ]; then
  ok "codex native hook projection documents shell write boundary as explicit preflight"
else
  bad "codex native hook projection should not pretend to guard shell write targets"
fi
if printf '{"tool":"Write","input":{"path":"%s"},"session_id":"nestedpayloadsid","cwd":"%s"}\n' "$TMP/repo/nested-f" "$TMP/repo" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_hook_nested.out 2>/tmp/codex_hook_nested.err \
  && [ ! -s /tmp/codex_hook_nested.out ]; then
  ok "codex native hook projection accepts string-tool nested input payloads"
else
  bad "codex native hook projection should accept string-tool nested input payloads"
fi
codex_hook_command=$(python3 - "$TMP/codex_hook_home/.codex/hooks.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
print(data["hooks"]["PreToolUse"][0]["hooks"][0]["command"])
PY
)
if printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/f" "$TMP/repo" \
  | AGENT_HOME="$ROOT" HOME="$TMP/no-codex-home" sh -c "$codex_hook_command" >/tmp/codex_hook_agent_home.out 2>/tmp/codex_hook_agent_home.err \
  && [ ! -s /tmp/codex_hook_agent_home.out ]; then
  ok "codex hook command resolves harness through AGENT_HOME"
else
  bad "codex hook command should resolve harness through AGENT_HOME"
fi
if printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/f" "$TMP/repo" \
  | AGENT_HOME="$TMP/not-agent-home" HOME="$TMP/codex_hook_home" sh -c "$codex_hook_command" >/tmp/codex_hook_invalid_agent_home.out 2>/tmp/codex_hook_invalid_agent_home.err \
  && [ ! -s /tmp/codex_hook_invalid_agent_home.out ]; then
  ok "codex hook command ignores invalid AGENT_HOME"
else
  bad "codex hook command should ignore invalid AGENT_HOME"
fi
if printf '{"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo" \
  | MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/sessionstart-lifecycle.py" >/tmp/codex_session_hook.out 2>/tmp/codex_session_hook.err \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_session_hook.out /tmp/codex_session_hook.err; then
  ok "codex native hook projection bridges session start lifecycle"
else
  bad "codex native hook projection should bridge session start lifecycle"
fi
if printf '{"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo" \
  | MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/sessionend-lifecycle.py" >/tmp/codex_session_end_hook.out 2>/tmp/codex_session_end_hook.err \
  && grep -q '^# sync (projects' /tmp/codex_session_end_hook.out \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_session_end_hook.out /tmp/codex_session_end_hook.err; then
  ok "codex native hook projection bridges session end lifecycle"
else
  bad "codex native hook projection should bridge session end lifecycle"
fi
codex_stop_command=$(python3 - "$TMP/codex_hook_home/.codex/hooks.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
print(data["hooks"]["Stop"][0]["hooks"][0]["command"])
PY
)
if printf '{"session_id":"stopsid","cwd":"%s"}\n' "$TMP/repo" \
  | MEM_STORE="$TMP/codex_hook_mem_stop" HOME="$TMP/codex_hook_home" sh -c "$codex_stop_command" >/tmp/codex_stop_hook.out 2>/tmp/codex_stop_hook.err \
  && grep -q '^# sync (projects' /tmp/codex_stop_hook.out \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_stop_hook.out /tmp/codex_stop_hook.err; then
  ok "codex native hook projection aliases Stop to session end lifecycle"
else
  bad "codex native hook projection should alias Stop to session end lifecycle"
fi
if "$CODEX" track "$TMP/flowproj" promptlifecyclesid >/tmp/codex_prompt_toggle.out 2>/tmp/codex_prompt_toggle.err \
  && printf '{"prompt":"remember this project context","session_id":"promptlifecyclesid","cwd":"%s"}\n' "$TMP/flowproj" \
  | MEM_NUDGE_INTERVAL=1 MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/userprompt-lifecycle.py" >/tmp/codex_prompt_hook.out 2>/tmp/codex_prompt_hook.err \
  && grep -q '^hook_event=UserPromptSubmit$' /tmp/codex_prompt_hook.out \
  && grep -q '^hook_scope=runtime-hook$' /tmp/codex_prompt_hook.out \
  && grep -q '^workflow_state=untracked$' /tmp/codex_prompt_hook.out \
  && grep -q '^autopilot_route=optional-direct-work-allowed$' /tmp/codex_prompt_hook.out \
  && grep -q '^routing_contract=untracked-direct-work$' /tmp/codex_prompt_hook.out \
  && grep -q 'untracked' /tmp/codex_prompt_hook.out \
  && grep -q '^0$' "$TMP/codex_hook_mem/.codex-turn-state-promptlifecyclesid" \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_prompt_hook.out /tmp/codex_prompt_hook.err; then
  ok "codex native hook projection bridges prompt lifecycle"
else
  bad "codex native hook projection should bridge prompt lifecycle"
fi
if printf '{"context":{"cwd":"%s","session_id":"permissionsid"}}\n' "$TMP/flowproj" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/permissionrequest-lifecycle.py" >/tmp/codex_permission_hook.out 2>/tmp/codex_permission_hook.err \
  && grep -q '^runtime_surface=adapter-owned-harness-status$' /tmp/codex_permission_hook.out \
  && grep -q "^cwd=$TMP/flowproj$" /tmp/codex_permission_hook.out \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_permission_hook.out /tmp/codex_permission_hook.err; then
  ok "codex native hook projection bridges permission requests to harness status"
else
  bad "codex native hook projection should bridge permission requests to harness status"
fi
if (cd "$TMP/flowproj" && MEM_STORE="$TMP/codex_hook_mem" python3 "$ROOT/tools/memory/mem.py" add durable thread "지난번 결정론 우선 설계가 핵심이라고 배웠다" >/tmp/codex_nested_prompt_seed.out 2>/tmp/codex_nested_prompt_seed.err) \
  && printf '{"input":{"messages":[{"role":"user","content":[{"type":"text","text":"지난번 결정론 내용을 다시 확인"}]}]},"session_id":"nestedpromptsid","cwd":"%s"}\n' "$TMP/flowproj" \
  | MEM_NUDGE_INTERVAL=100 MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/userprompt-lifecycle.py" >/tmp/codex_nested_prompt_hook.out 2>/tmp/codex_nested_prompt_hook.err \
  && grep -q '우선 설계가 핵심' /tmp/codex_nested_prompt_hook.out; then
  ok "codex native prompt hook extracts nested message content for recall"
else
  bad "codex native prompt hook should extract nested message content for recall"
fi
mkdir -p "$TMP/repo/.agent_reports/spec" "$TMP/codex_marker_home"
printf 'prd\n' > "$TMP/repo/.agent_reports/spec/prd.md"
if printf '{"tool_name":"Read","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/.agent_reports/spec/prd.md" "$TMP/repo" \
  | AGENT_HOME="$TMP/codex_marker_home" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-read-marker.py" >/tmp/codex_read_hook.out 2>/tmp/codex_read_hook.err \
  && find "$TMP/codex_marker_home/.spec-grounding" -type f -name 'testsid__*' -print -quit | grep -q . \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_read_hook.out /tmp/codex_read_hook.err; then
  ok "codex native hook projection records spec read markers"
else
  bad "codex native hook projection should record spec read markers"
fi
if printf '{"tool_name":"Bash","tool_input":{"command":"cat .agent_reports/spec/prd.md"},"session_id":"shellreadsid","cwd":"%s"}\n' "$TMP/repo" \
  | AGENT_HOME="$TMP/codex_marker_home" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-read-marker.py" >/tmp/codex_shell_read_hook.out 2>/tmp/codex_shell_read_hook.err \
  && ! find "$TMP/codex_marker_home/.spec-grounding" -type f -name 'shellreadsid__*' -print -quit | grep -q .; then
  ok "codex native read hook documents shell read boundary as explicit preflight"
else
  bad "codex native read hook should not pretend to mark shell reads"
fi
if printf '{"tool":{"name":"Read","input":{"path":"%s"}},"session_id":"nestedreadsid","cwd":"%s"}\n' "$TMP/repo/.agent_reports/spec/prd.md" "$TMP/repo" \
  | AGENT_HOME="$TMP/codex_marker_home" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-read-marker.py" >/tmp/codex_read_hook_nested.out 2>/tmp/codex_read_hook_nested.err \
  && find "$TMP/codex_marker_home/.spec-grounding" -type f -name 'nestedreadsid__*' -print -quit | grep -q .; then
  ok "codex native read hook accepts nested tool input payloads"
else
  bad "codex native read hook should accept nested tool input payloads"
fi
if printf '{"tool_name":"Read","tool_input":{"file_path":".agent_reports/spec/prd.md"},"session":{"id":"nestedctxreadsid"},"workspace":{"cwd":"%s"}}\n' "$TMP/repo" \
  | AGENT_HOME="$TMP/codex_marker_home" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-read-marker.py" >/tmp/codex_read_hook_nested_context.out 2>/tmp/codex_read_hook_nested_context.err \
  && find "$TMP/codex_marker_home/.spec-grounding" -type f -name 'nestedctxreadsid__*' -print -quit | grep -q .; then
  ok "codex native read hook resolves nested cwd/session payloads"
else
  bad "codex native read hook should resolve nested cwd/session payloads"
fi
if printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/runtime/projects/abc/memory/MEMORY.md" "$TMP/runtime" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_hook_block.out 2>/tmp/codex_hook_block.err \
  && grep -q '"decision": "block"' /tmp/codex_hook_block.out \
  && grep -q 'memory' /tmp/codex_hook_block.out; then
  ok "codex native hook projection blocks guarded writes"
else
  bad "codex native hook projection should block guarded writes"
fi
if printf '{"tool_name":"Write","tool_input":{"file_path":"projects/abc/memory/NESTED.md"},"session":{"id":"nestedcontextsid"},"context":{"cwd":"%s"}}\n' "$TMP/runtime" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_nested_context_block.out 2>/tmp/codex_nested_context_block.err \
  && grep -q '"decision": "block"' /tmp/codex_nested_context_block.out \
  && grep -q 'memory' /tmp/codex_nested_context_block.out; then
  ok "codex native write hook resolves nested cwd/session payloads"
else
  bad "codex native write hook should resolve nested cwd/session payloads"
fi
if printf '{"tool_name":"MultiEdit","tool_input":{"file_path":"%s","edits":[]},"session_id":"testsid","cwd":"%s"}\n' "$TMP/runtime/projects/abc/memory/MEMORY.md" "$TMP/runtime" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_multiedit_block.out 2>/tmp/codex_multiedit_block.err \
  && grep -q '"decision": "block"' /tmp/codex_multiedit_block.out \
  && grep -q 'memory' /tmp/codex_multiedit_block.out; then
  ok "codex native hook projection blocks guarded MultiEdit writes"
else
  bad "codex native hook projection should block guarded MultiEdit writes"
fi
codex_qualified_patch_payload=$(python3 - "$TMP/runtime/projects/abc/memory/PATCHED.md" "$TMP/runtime" <<'PY'
import json
import sys

print(json.dumps({
  "tool_name": "functions.apply_patch",
  "input": f"*** Begin Patch\n*** Add File: {sys.argv[1]}\n+blocked\n*** End Patch\n",
  "session_id": "testsid",
  "cwd": sys.argv[2],
}))
PY
)
if printf '%s\n' "$codex_qualified_patch_payload" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_qualified_patch_block.out 2>/tmp/codex_qualified_patch_block.err \
  && grep -q '"decision": "block"' /tmp/codex_qualified_patch_block.out \
  && grep -q 'memory' /tmp/codex_qualified_patch_block.out; then
  ok "codex native hook projection blocks qualified apply_patch writes"
else
  bad "codex native hook projection should block qualified apply_patch writes"
fi
mkdir -p "$TMP/repo/spec/design"
printf '<!doctype html><title>ok</title>\n' > "$TMP/repo/spec/design/preview.html"
if printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/spec/design/preview.html" "$TMP/repo" \
  | DESIGN_POSTWRITE_HOOK=0 HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-design-check.py" >/tmp/codex_design_hook.out 2>/tmp/codex_design_hook.err \
  && [ ! -s /tmp/codex_design_hook.out ] \
  && [ ! -s /tmp/codex_design_hook.err ]; then
  ok "codex native hook projection bridges design post-write checks"
else
  bad "codex native hook projection should bridge design post-write checks"
fi
if printf '{"toolUse":{"name":"Write","input":{"path":"%s"}},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/spec/design/preview.html" "$TMP/repo" \
  | DESIGN_POSTWRITE_HOOK=0 HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-design-check.py" >/tmp/codex_design_hook_nested.out 2>/tmp/codex_design_hook_nested.err \
  && [ ! -s /tmp/codex_design_hook_nested.out ] \
  && [ ! -s /tmp/codex_design_hook_nested.err ]; then
  ok "codex native design hook accepts toolUse input payloads"
else
  bad "codex native design hook should accept toolUse input payloads"
fi
if printf '{"tool_name":"MultiEdit","tool_input":{"file_path":"%s","edits":[]},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/spec/design/preview.html" "$TMP/repo" \
  | DESIGN_POSTWRITE_HOOK=0 HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-design-check.py" >/tmp/codex_design_hook_multiedit.out 2>/tmp/codex_design_hook_multiedit.err \
  && [ ! -s /tmp/codex_design_hook_multiedit.out ] \
  && [ ! -s /tmp/codex_design_hook_multiedit.err ]; then
  ok "codex native design hook accepts MultiEdit payloads"
else
  bad "codex native design hook should accept MultiEdit payloads"
fi
codex_design_patch_payload=$(python3 - "$TMP/repo" <<'PY'
import json
import sys

print(json.dumps({
  "tool_name": "functions.apply_patch",
  "input": "*** Begin Patch\n*** Update File: spec/design/preview.html\n@@\n <!doctype html><title>ok</title>\n*** End Patch\n",
  "session_id": "testsid",
  "cwd": sys.argv[1],
}))
PY
)
if printf '%s\n' "$codex_design_patch_payload" \
  | DESIGN_POSTWRITE_HOOK=0 HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/posttooluse-design-check.py" >/tmp/codex_design_hook_qualified_patch.out 2>/tmp/codex_design_hook_qualified_patch.err \
  && [ ! -s /tmp/codex_design_hook_qualified_patch.out ] \
  && [ ! -s /tmp/codex_design_hook_qualified_patch.err ]; then
  ok "codex native design hook accepts qualified apply_patch payloads"
else
  bad "codex native design hook should accept qualified apply_patch payloads"
fi
if "$CODEX" mode-info dev/backend >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=portable$' /tmp/mode.out \
  && grep -q '^realization=portable-persona$' /tmp/mode.out; then
  ok "codex mode wrapper maps portable mode"
else
  bad "codex mode wrapper should map portable mode"
fi
if "$CODEX" mode-info qa/security-review >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=portable$' /tmp/mode.out \
  && grep -q '^realization=portable-persona$' /tmp/mode.out \
  && grep -q 'read-only security review with Codex file and git diff tools' /tmp/mode.out \
  && ! grep -q '^tool_contract=' /tmp/mode.out; then
  ok "codex mode wrapper treats security-review as portable read-only guidance"
else
  bad "codex mode wrapper should treat security-review as portable read-only guidance"
fi
codex_design_modes_ok=1
for mode_file in "$ROOT"/roles/modes/design/*.md; do
  mode_name=$(basename "$mode_file" .md)
  [ "$mode_name" = "_design_rules" ] && continue
  mode="design/$mode_name"
  if ! "$CODEX" mode-info "$mode" >/tmp/mode.out 2>/tmp/mode.err \
    || ! grep -q '^status=tool-contract$' /tmp/mode.out \
    || ! grep -q '^realization=codex-native-mode-with-tool-contract$' /tmp/mode.out \
    || ! grep -q '^tool_contract=visual-harness$' /tmp/mode.out \
    || ! grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh visual-harness <file.html>$' /tmp/mode.out \
    || ! grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/mode.out \
    || ! grep -q "^native_mode_path=adapters/codex/modes/design/$mode_name.md$" /tmp/mode.out \
    || ! grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
    codex_design_modes_ok=0
    break
  fi
done
if [ "$codex_design_modes_ok" -eq 1 ]; then
  ok "codex mode wrapper maps design modes to native visual-harness contract"
else
  bad "codex mode wrapper should map design modes to native visual-harness contract"
fi
if "$CODEX" mode-info material/data-script >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=data-script$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh data-script --check <script.py>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-data-script$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports material data-script contract surface"
else
  bad "codex mode wrapper should report material data-script contract surface"
fi
if "$CODEX" mode-info material/figure-gen >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=figure-gen$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh figure-gen --check <script.py>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-figure-gen$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports material figure-gen contract surface"
else
  bad "codex mode wrapper should report material figure-gen contract surface"
fi
if "$CODEX" mode-info material/pdf-extract >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=pdf-extract$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh pdf-extract --check <file.pdf>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-pdf-extract$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports material pdf-extract contract surface"
else
  bad "codex mode wrapper should report material pdf-extract contract surface"
fi
if "$CODEX" mode-info qa/test >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=verification-runner$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh verification-runner --check -- <command>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports qa test verification runner surface"
else
  bad "codex mode wrapper should report qa test verification runner surface"
fi
if "$CODEX" mode-info material/browser-fetch >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=browser-fetch$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh browser-fetch --check <url>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-browser-fetch$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports material browser-fetch contract surface"
else
  bad "codex mode wrapper should report material browser-fetch contract surface"
fi
if "$CODEX" mode-info material/web-image-search >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=web-image-search$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh web-image-search --check <query>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-web-image-search$' /tmp/mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/mode.out; then
  ok "codex mode wrapper reports material web-image-search contract surface"
else
  bad "codex mode wrapper should report material web-image-search contract surface"
fi
if "$CODEX" mode-info research/claim-verify >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=tool-contract$' /tmp/mode.out \
  && grep -q '^tool_contract=external-claim-verification$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh claim-verify --check <claim>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-claim-verify$' /tmp/mode.out; then
  ok "codex mode wrapper reports named claim verification contract"
else
  bad "codex mode wrapper should report named claim verification contract"
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
if "$CODEX" distill-propose codexsid "$TMP/flowproj" >/tmp/codex_distill.out 2>/tmp/codex_distill.err; then
  bad "codex distill-propose should report tool-contract until explicitly enabled"
else
  if [ "$?" -eq 69 ] \
    && grep -q '^status=tool-contract$' /tmp/codex_distill.out \
    && grep -q '^reason=distill-proposal-disabled$' /tmp/codex_distill.out \
    && grep -q '^enable=CODEX_DISTILL_ENABLE=1$' /tmp/codex_distill.out; then
    ok "codex distill-propose reports disabled tool-contract by default"
  else
    bad "codex distill-propose should exit 69 with disabled tool-contract"
  fi
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
  && ! grep -q -- '--ask-for-approval' "$TMP/codex_argv" \
  && grep -q -- '--ephemeral' "$TMP/codex_argv" \
  && grep -q -- '--ignore-rules' "$TMP/codex_argv" \
  && grep -q -- '--skip-git-repo-check' "$TMP/codex_argv" \
  && grep -q '"action":"add"' /tmp/codex_distill.out; then
  ok "codex distill proposal uses constrained exec"
else
  bad "codex distill proposal should use constrained exec"
fi
if CODEX_DISTILL_ENABLE=1 CODEX_DISTILL_APPLY=1 CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store_apply_blocked" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv_apply" \
  "$CODEX" distill-propose codexsid "$TMP/flowproj" >/tmp/codex_distill_apply.out 2>/tmp/codex_distill_apply.err; then
  bad "codex distill apply should require accepted no-tools/action contract"
else
  [ "$?" -eq 69 ] && ok "codex distill apply requires accepted no-tools/action contract" || bad "codex distill apply wrong exit"
fi
if CODEX_DISTILL_ENABLE=1 CODEX_DISTILL_APPLY=1 CODEX_DISTILL_CONTRACT_ACCEPTED=1 CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store_apply" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv_apply_accepted" \
  "$CODEX" distill-propose codexsid "$TMP/flowproj" >/tmp/codex_distill_apply.out 2>/tmp/codex_distill_apply.err \
  && MEM_STORE="$TMP/store_apply" python3 "$ROOT/tools/memory/mem.py" stats >/tmp/codex_stats.out 2>/tmp/codex_stats.err \
  && grep -q 'total: 1' /tmp/codex_stats.out; then
  ok "codex distill explicit apply works after accepted contract"
else
  bad "codex distill explicit apply should require and obey accepted contract"
fi
# session-end auto-distillation is enabled by default after the tool-free proof
if CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store_session_end" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv_se" \
  "$CODEX" session-end "$TMP/flowproj" codexsid >/tmp/codex_se.out 2>/tmp/codex_se.err \
  && MEM_STORE="$TMP/store_session_end" python3 "$ROOT/tools/memory/mem.py" stats 2>/dev/null | grep -q 'total: 1'; then
  ok "codex session-end auto-distills and applies by default"
else
  bad "codex session-end should auto-distill and apply by default"
fi
# recursion guard: MEM_DISTILL=1 makes the whole session-end pipeline a no-op
if MEM_DISTILL=1 CODEX_SESSIONS="$TMP/codex_sessions" MEM_STORE="$TMP/store_session_end_guard" \
  PATH="$TMP/stubbin:$PATH" CODEX_STUB_ARGV="$TMP/codex_argv_se_guard" \
  "$CODEX" session-end "$TMP/flowproj" codexsid >/tmp/codex_se_guard.out 2>/tmp/codex_se_guard.err \
  && ! { MEM_STORE="$TMP/store_session_end_guard" python3 "$ROOT/tools/memory/mem.py" stats 2>/dev/null | grep -q 'total: 1'; }; then
  ok "codex session-end no-ops under MEM_DISTILL=1 recursion guard"
else
  bad "codex session-end must no-op under MEM_DISTILL=1 recursion guard"
fi
RPHOME="$TMP/codex-runtime-home"
rm -rf "$RPHOME"; mkdir -p "$RPHOME"
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" "$ROOT/adapters/codex/bin/check-runtime-projection.sh" >/tmp/codex_rp0.out 2>/tmp/codex_rp0.err; then
  bad "codex check-runtime-projection should fail on an unwired home"
else
  grep -q '^status=failed' /tmp/codex_rp0.out && ok "codex check-runtime-projection reports an unwired home as failed" || bad "codex check-runtime-projection unwired output wrong"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" "$ROOT/adapters/codex/bin/install-runtime-projection.sh" >/tmp/codex_rp1.out 2>/tmp/codex_rp1.err \
  && grep -q '^status=ok' /tmp/codex_rp1.out \
  && AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" "$ROOT/adapters/codex/bin/check-runtime-projection.sh" >/tmp/codex_rp2.out 2>/tmp/codex_rp2.err \
  && grep -q '^check=agent-harness:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-harness-readme:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-capabilities:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-roles:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-bin:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-tools:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-utilities:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-config:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-scaffolds:ok' /tmp/codex_rp2.out \
  && grep -q '^check=hook-trust:review-needed' /tmp/codex_rp2.out \
  && grep -q '^check=hooks-json:ok' /tmp/codex_rp2.out \
  && grep -q '^check=skill-link:autopilot-code:ok' /tmp/codex_rp2.out \
  && grep -q '^check=skills-linked:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agent-link:plan-team.toml:ok' /tmp/codex_rp2.out \
  && grep -q '^check=agents-linked:ok' /tmp/codex_rp2.out \
  && grep -q '^status=ok' /tmp/codex_rp2.out; then
  ok "codex install-runtime-projection wires the home and the checker passes"
else
  bad "codex install-runtime-projection + checker should wire and validate the runtime home"
fi
RPBAD="$TMP/codex-runtime-home-bad"
rm -rf "$RPBAD"; mkdir -p "$RPBAD"
if AGENT_HOME="$ROOT" CODEX_HOME="$RPBAD" "$ROOT/adapters/codex/bin/install-runtime-projection.sh" >/tmp/codex_rp_bad_install.out 2>/tmp/codex_rp_bad_install.err \
  && ln -sfn "$TMP" "$RPBAD/skills/autopilot-code" \
  && ln -sfn "$TMP" "$RPBAD/agents/plan-team.toml" \
  && ! AGENT_HOME="$ROOT" CODEX_HOME="$RPBAD" "$ROOT/adapters/codex/bin/check-runtime-projection.sh" >/tmp/codex_rp_bad.out 2>/tmp/codex_rp_bad.err \
  && grep -q '^check=skill-link:autopilot-code:failed' /tmp/codex_rp_bad.out \
  && grep -q '^check=agent-link:plan-team.toml:failed' /tmp/codex_rp_bad.out \
  && grep -q '^status=failed' /tmp/codex_rp_bad.out; then
  ok "codex check-runtime-projection rejects miswired skill and agent links"
else
  bad "codex check-runtime-projection should reject miswired skill and agent links"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" runtime-projection >/tmp/codex_rp3.out 2>/tmp/codex_rp3.err \
  && grep -q '^check=agent-capabilities:ok' /tmp/codex_rp3.out \
  && grep -q '^check=agent-tools:ok' /tmp/codex_rp3.out \
  && grep -q '^check=agent-config:ok' /tmp/codex_rp3.out \
  && grep -q '^status=ok' /tmp/codex_rp3.out; then
  ok "codex preflight runtime-projection validates installed runtime wiring"
else
  bad "codex preflight runtime-projection should validate installed runtime wiring"
fi
cat > "$RPHOME/config.toml" <<EOF
[hooks.state]
[hooks.state."$RPHOME/hooks.json:session_start:0:0"]
trusted_hash = "sha256:test"
[hooks.state."$RPHOME/hooks.json:session_end:0:0"]
trusted_hash = "sha256:test"
[hooks.state."$RPHOME/hooks.json:user_prompt_submit:0:0"]
trusted_hash = "sha256:test"
[hooks.state."$RPHOME/hooks.json:permission_request:0:0"]
trusted_hash = "sha256:test"
[hooks.state."$RPHOME/hooks.json:pre_tool_use:0:0"]
trusted_hash = "sha256:test"
[hooks.state."$RPHOME/hooks.json:post_tool_use:0:0"]
trusted_hash = "sha256:test"
EOF
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" runtime-projection >/tmp/codex_rp_stop_trust.out 2>/tmp/codex_rp_stop_trust.err \
  && grep -q '^check=hook-trust:review-needed missing=stop$' /tmp/codex_rp_stop_trust.out \
  && grep -q '^status=ok' /tmp/codex_rp_stop_trust.out; then
  ok "codex runtime-projection requires distinct Stop hook trust"
else
  bad "codex runtime-projection should require distinct Stop hook trust"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" runtime-projection --require-hook-trust >/tmp/codex_rp_strict_missing.out 2>/tmp/codex_rp_strict_missing.err; then
  bad "codex strict runtime-projection should fail when hook trust is missing"
else
  grep -q '^check=hook-trust:review-needed missing=stop$' /tmp/codex_rp_strict_missing.out && ok "codex strict runtime-projection requires complete hook trust" || bad "codex strict runtime-projection missing trust output wrong"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_REQUIRE_HOOK_TRUST=1 CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" runtime-projection >/tmp/codex_rp_trust.out 2>/tmp/codex_rp_trust.err; then
  bad "codex runtime-projection should fail when hook trust is required but missing"
else
  grep -q '^check=hook-trust:review-needed' /tmp/codex_rp_trust.out && ok "codex runtime-projection can require hook trust" || bad "codex runtime-projection required hook trust output wrong"
fi
cat >> "$RPHOME/config.toml" <<EOF
[hooks.state."$RPHOME/hooks.json:stop:0:0"]
trusted_hash = "sha256:test"
EOF
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" doctor --runtime >/tmp/codex_doctor_runtime.out 2>/tmp/codex_doctor_runtime.err \
  && grep -q '^check=runtime-projection:ok' /tmp/codex_doctor_runtime.out \
  && grep -q '^status=ok' /tmp/codex_doctor_runtime.out; then
  ok "codex doctor --runtime includes runtime projection validation"
else
  bad "codex doctor --runtime should include runtime projection validation"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT=2 "$CODEX" doctor --runtime-strict >/tmp/codex_doctor_runtime_strict.out 2>/tmp/codex_doctor_runtime_strict.err \
  && grep -q '^check=runtime-projection:ok' /tmp/codex_doctor_runtime_strict.out \
  && grep -q '^status=ok' /tmp/codex_doctor_runtime_strict.out; then
  ok "codex doctor --runtime-strict requires and accepts complete hook trust"
else
  bad "codex doctor --runtime-strict should require and accept complete hook trust"
fi
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" "$ROOT/adapters/codex/bin/install-runtime-projection.sh" >/dev/null 2>&1 \
  && AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME" "$ROOT/adapters/codex/bin/check-runtime-projection.sh" >/dev/null 2>&1; then
  ok "codex install-runtime-projection is idempotent"
else
  bad "codex install-runtime-projection should be idempotent"
fi
RPHOME2="$TMP/codex-runtime-home2"
rm -rf "$RPHOME2"; mkdir -p "$RPHOME2"; printf '{"old":1}\n' > "$RPHOME2/hooks.json"
if AGENT_HOME="$ROOT" CODEX_HOME="$RPHOME2" "$ROOT/adapters/codex/bin/install-runtime-projection.sh" >/dev/null 2>&1 \
  && [ -f "$RPHOME2/hooks.json.pre-harness" ] && [ -L "$RPHOME2/hooks.json" ]; then
  ok "codex install-runtime-projection backs up a pre-existing hooks.json"
else
  bad "codex install-runtime-projection should back up a pre-existing hooks.json"
fi

echo "== opencode preflight wrapper =="
git -C "$TMP/repo" switch -q -c opencode-work
if "$OPENCODE" write "$TMP/repo/f" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err; then
  ok "opencode preflight passes clean write"
else
  bad "opencode preflight should pass clean write"
fi
if "$OPENCODE" write "$TMP/runtime/projects/abc/memory/MEMORY.md" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err; then
  bad "opencode preflight should block memory file write"
else
  [ "$?" -eq 2 ] && ok "opencode preflight blocks memory file write" || bad "opencode preflight memory wrong exit"
fi
if AGENT_HOME="$ROOT" bash "$DESIGN" --file "$TMP/not-design.txt" >/tmp/design.out 2>/tmp/design.err \
  && "$OPENCODE" design "$TMP/not-design.txt" >/tmp/design.out 2>/tmp/design.err; then
  ok "opencode design postwrite wrappers no-op on non-html"
else
  bad "opencode design postwrite wrappers should no-op on non-html"
fi
if "$OPENCODE_PROJECTION" capability-info audit >/tmp/opencode_projection.out 2>/tmp/opencode_projection.err \
  && grep -q '^capability=audit$' /tmp/opencode_projection.out \
  && grep -q '^adapter=opencode$' /tmp/opencode_projection.out; then
  ok "opencode projection preflight resolves harness root"
else
  bad "opencode projection preflight should resolve harness root"
fi
mkdir -p "$TMP/opencode_pointer_home/.config/opencode"
ln -s "$ROOT" "$TMP/opencode_pointer_home/.config/opencode/agent-harness"
if env -u AGENT_HOME HOME="$TMP/opencode_pointer_home" "$ROOT/adapters/opencode/utilities/agent-home.sh" >/tmp/opencode_agent_home.out 2>/tmp/opencode_agent_home.err \
  && grep -q "^$TMP/opencode_pointer_home/.config/opencode/agent-harness$" /tmp/opencode_agent_home.out; then
  ok "opencode agent-home wrapper resolves runtime pointer"
else
  bad "opencode agent-home wrapper should resolve runtime pointer"
fi
if AGENT_HOME="$TMP/not-agent-home" HOME="$TMP/opencode_pointer_home" "$ROOT/adapters/opencode/utilities/agent-home.sh" >/tmp/opencode_agent_home_invalid.out 2>/tmp/opencode_agent_home_invalid.err \
  && grep -q "^$TMP/opencode_pointer_home/.config/opencode/agent-harness$" /tmp/opencode_agent_home_invalid.out; then
  ok "opencode agent-home wrapper ignores invalid AGENT_HOME"
else
  bad "opencode agent-home wrapper should ignore invalid AGENT_HOME"
fi

echo "== opencode spec read gate =="
if "$OPENCODE" read "$TMP/specproj/.agent_reports/spec/prd.md" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err \
  && "$OPENCODE" capability autopilot-code "$TMP/specproj" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err; then
  ok "opencode read+capability wrapper passes spec gate"
else
  bad "opencode read+capability wrapper should pass spec gate"
fi

echo "== opencode workflow signal CLI =="
oldflag="$TMP/flowproj/.agent_reports/.untracked.oldopen"
: > "$oldflag"
touch -d '2026-06-10 00:00:00' "$oldflag"
if "$OPENCODE" start "$TMP/flowproj" opencodesid >/tmp/opencode_start.out 2>/tmp/opencode_start.err \
  && [ ! -e "$oldflag" ]; then
  ok "opencode start wrapper cleans stale untracked flags"
else
  bad "opencode start wrapper should clean stale untracked flags"
fi
mkdir -p "$TMP/opencode-artifact/.agent_reports/spec"
if "$OPENCODE" write "$TMP/opencode-artifact/.agent_reports/spec/prd.md" opencodesid >/tmp/opencode_artifact.out 2>/tmp/opencode_artifact.err; then
  bad "opencode write wrapper should fail missing research"
else
  rc=$?
  if [ "$rc" -eq 2 ] \
    && grep -q 'preflight.sh track' /tmp/opencode_artifact.err \
    && ! grep -q '/track' /tmp/opencode_artifact.err; then
    ok "opencode write wrapper adapts artifact toggle hint"
  else
    bad "opencode write wrapper should adapt artifact toggle hint"
  fi
fi
if "$OPENCODE" mode "$TMP/flowproj" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err \
  && grep -q 'tracked' /tmp/opencode.out; then
  ok "opencode mode wrapper emits tracked text"
else
  bad "opencode mode wrapper should emit tracked text"
fi
if "$OPENCODE" track "$TMP/flowproj" opencodesid >/tmp/opencode_track.out 2>/tmp/opencode_track.err \
  && grep -q 'untracked mode' /tmp/opencode_track.out \
  && [ -f "$TMP/flowproj/.agent_reports/.untracked.opencodesid" ]; then
  ok "opencode track wrapper enables untracked mode"
else
  bad "opencode track wrapper should enable untracked mode"
fi
if "$OPENCODE" mode "$TMP/flowproj" opencodesid >/tmp/opencode.out 2>/tmp/opencode.err \
  && grep -q 'untracked' /tmp/opencode.out \
  && grep -q 'preflight.sh track' /tmp/opencode.out \
  && ! grep -q '/track' /tmp/opencode.out; then
  ok "opencode mode wrapper emits untracked text"
else
  bad "opencode mode wrapper should emit untracked text"
fi
if "$OPENCODE" track "$TMP/flowproj" opencodesid >/tmp/opencode_track.out 2>/tmp/opencode_track.err \
  && grep -q 'tracked mode' /tmp/opencode_track.out \
  && [ ! -f "$TMP/flowproj/.agent_reports/.untracked.opencodesid" ]; then
  ok "opencode track wrapper restores tracked mode"
else
  bad "opencode track wrapper should restore tracked mode"
fi
if "$OPENCODE" memory "$TMP/flowproj" >/tmp/opencode_mem.out 2>/tmp/opencode_mem.err; then
  ok "opencode memory wrapper exits cleanly"
else
  bad "opencode memory wrapper should exit cleanly"
fi
if MEM_STORE="$TMP/opencode_launcher_store" "$ROOT/adapters/opencode/tools/memory/mem.py" stats >/tmp/opencode_mem_launcher.out 2>/tmp/opencode_mem_launcher.err \
  && grep -q '^# store stats$' /tmp/opencode_mem_launcher.out; then
  ok "opencode memory launcher ignores invalid non-harness AGENT_HOME"
else
  bad "opencode memory launcher should fall back from invalid AGENT_HOME"
fi
if "$OPENCODE" recall "전에 결정한 내용 뭐였지" "$TMP/flowproj" >/tmp/opencode_recall.out 2>/tmp/opencode_recall.err; then
  ok "opencode recall wrapper exits cleanly"
else
  bad "opencode recall wrapper should exit cleanly"
fi
if "$OPENCODE" briefing "$TMP/flowproj" >/tmp/opencode_brief.out 2>/tmp/opencode_brief.err; then
  ok "opencode briefing wrapper exits cleanly"
else
  bad "opencode briefing wrapper should exit cleanly"
fi
if AGENT_NOTES_ROOT="$TMP/notes" WORKLOG_BOARD_APP="$TMP/board" WORKLOG_BOARD_WT="$TMP/board-wt" \
  "$OPENCODE" worklog "$TMP/flowproj" >/tmp/opencode_worklog.out 2>/tmp/opencode_worklog.err \
  && grep -q "^agent-notes-root=$TMP/notes$" /tmp/opencode_worklog.out \
  && grep -q '^note=read-only inventory;' /tmp/opencode_worklog.out; then
  ok "opencode worklog wrapper reports read-only state"
else
  bad "opencode worklog wrapper should report read-only state"
fi
if env -u AGENT_NOTES_ROOT -u WORKLOG_NOTES_ROOT -u WORKLOG_BOARD_APP -u WORKLOG_BOARD_WT \
  "$OPENCODE" worklog "$TMP/flowproj" >/tmp/opencode_worklog_default.out 2>/tmp/opencode_worklog_default.err \
  && grep -q '^agent-notes-root=unset$' /tmp/opencode_worklog_default.out \
  && ! grep -q '/.claude/worklog-board' /tmp/opencode_worklog_default.out; then
  ok "opencode worklog wrapper has no Claude runtime defaults"
else
  bad "opencode worklog wrapper should not default to Claude runtime paths"
fi
if AGENT_NOTES_ROOT="$TMP/notes" WORKLOG_BOARD_APP="$TMP/board" WORKLOG_BOARD_WT="$TMP/board-wt" \
  "$OPENCODE" status "$TMP/flowproj" opencodesid >/tmp/opencode_status.out 2>/tmp/opencode_status.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_status.out \
  && grep -q '^runtime_surface=adapter-owned-harness-status$' /tmp/opencode_status.out \
  && grep -q '^artifact_root_exists=1$' /tmp/opencode_status.out \
  && grep -q '^workflow_state=tracked$' /tmp/opencode_status.out \
  && grep -q '^git_repo=0$' /tmp/opencode_status.out \
  && grep -q "^agent_notes_root=$TMP/notes$" /tmp/opencode_status.out \
  && grep -q '^note=read-only snapshot;' /tmp/opencode_status.out; then
  ok "opencode status wrapper reports harness snapshot"
else
  bad "opencode status wrapper should report harness snapshot"
fi
if "$OPENCODE" permissions >/tmp/opencode_permissions.out 2>/tmp/opencode_permissions.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_permissions.out \
  && grep -q '^runtime_surface=opencode-native-permission-config$' /tmp/opencode_permissions.out \
  && grep -q '^permission_model=permission-allow-ask-deny$' /tmp/opencode_permissions.out \
  && grep -q '^claude_allowed_tools=unsupported$' /tmp/opencode_permissions.out \
  && grep -q '^guard_contract=preflight-write-plugin-and-explicit-tool-contracts$' /tmp/opencode_permissions.out; then
  ok "opencode permissions wrapper reports native permission contract"
else
  bad "opencode permissions wrapper should report native permission contract"
fi
if "$OPENCODE" headless >/tmp/opencode_headless.out 2>/tmp/opencode_headless.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_headless.out \
  && grep -q '^runtime_surface=opencode-run-headless$' /tmp/opencode_headless.out \
  && grep -q '^tool_contract=headless-dispatch$' /tmp/opencode_headless.out \
  && grep -q '^claude_headless=unsupported$' /tmp/opencode_headless.out \
  && grep -q '^liveness_surface=opencode-sqlite-session-mtime$' /tmp/opencode_headless.out \
  && grep -q '^liveness_check=adapters/opencode/bin/preflight.sh liveness \[jobs.log\]$' /tmp/opencode_headless.out \
  && grep -q '^constraints=main-only,max-depth-1,register-open-job,explicit-capability-mode-qa,transcript-liveness-required$' /tmp/opencode_headless.out; then
  ok "opencode headless wrapper reports dispatch contract"
else
  bad "opencode headless wrapper should report dispatch contract"
fi
if "$OPENCODE" headless --check "$TMP/missing-worktree" >/tmp/opencode_headless_missing.out 2>/tmp/opencode_headless_missing.err; then
  bad "opencode headless wrapper should fail missing worktree"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^reason=worktree-not-found$' /tmp/opencode_headless_missing.out; then
    ok "opencode headless wrapper reports missing worktree"
  else
    bad "opencode headless wrapper should report missing worktree"
  fi
fi
mkdir -p "$TMP/opencode_headless_home/.config/opencode/agent" \
  "$TMP/opencode_headless_home/.config/opencode/command" \
  "$TMP/opencode_headless_home/.config/opencode/plugins"
ln -s "$ROOT" "$TMP/opencode_headless_home/.config/opencode/agent-harness"
ln -s "$ROOT/opencode_setting/opencode-skills" "$TMP/opencode_headless_home/.config/opencode/agent-skills"
ln -s "$ROOT/opencode_setting/opencode-agents/qa-team/qa-team.md" "$TMP/opencode_headless_home/.config/opencode/agent/qa-team.md"
ln -s "$ROOT/opencode_setting/opencode-commands/autopilot-code.md" "$TMP/opencode_headless_home/.config/opencode/command/autopilot-code.md"
ln -s "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js" "$TMP/opencode_headless_home/.config/opencode/plugins/agent-harness-guards.js"
if HOME="$TMP/opencode_headless_home" XDG_CONFIG_HOME="$TMP/opencode_headless_home/.config" \
  "$OPENCODE" headless --check "$TMP/repo" >/tmp/opencode_headless_check.out 2>/tmp/opencode_headless_check.err \
  && grep -q '^runtime_projection=ok$' /tmp/opencode_headless_check.out \
  && grep -q '^check=ok$' /tmp/opencode_headless_check.out; then
  ok "opencode headless check validates runtime projection"
else
  bad "opencode headless check should validate runtime projection"
fi
mkdir -p "$TMP/opencode_headless_config_home/.config/opencode/agent" \
  "$TMP/opencode_headless_config_home/.config/opencode/command" \
  "$TMP/opencode_headless_config_home/.config/opencode/plugins"
ln -s "$ROOT" "$TMP/opencode_headless_config_home/.config/opencode/agent-harness"
ln -s "$ROOT/opencode_setting/opencode-agents/qa-team/qa-team.md" "$TMP/opencode_headless_config_home/.config/opencode/agent/qa-team.md"
ln -s "$ROOT/opencode_setting/opencode-commands/autopilot-code.md" "$TMP/opencode_headless_config_home/.config/opencode/command/autopilot-code.md"
ln -s "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js" "$TMP/opencode_headless_config_home/.config/opencode/plugins/agent-harness-guards.js"
if OPENCODE_CONFIG_CONTENT='{"skills":{"paths":["/tmp/opencode-\u0073kills"]}}' \
  HOME="$TMP/opencode_headless_config_home" XDG_CONFIG_HOME="$TMP/opencode_headless_config_home/.config" \
  "$OPENCODE" headless --check "$TMP/repo" >/tmp/opencode_headless_config_check.out 2>/tmp/opencode_headless_config_check.err \
  && grep -q '^runtime_projection=ok$' /tmp/opencode_headless_config_check.out \
  && grep -q '^check=ok$' /tmp/opencode_headless_config_check.out; then
  ok "opencode headless check accepts JSON-configured native skills path"
else
  bad "opencode headless check should accept JSON-configured native skills path"
fi
if "$OPENCODE" dispatch --dry-run --worktree "$TMP/repo" --slug opencode-dispatch --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" --jobs "$TMP/opencode-dispatch.log" >/tmp/opencode_dispatch.out 2>/tmp/opencode_dispatch.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_dispatch.out \
  && grep -q '^status=dry-run$' /tmp/opencode_dispatch.out \
  && grep -q '^registered=0$' /tmp/opencode_dispatch.out \
  && grep -q '^started=0$' /tmp/opencode_dispatch.out \
  && grep -q '^command=opencode run ' /tmp/opencode_dispatch.out \
  && grep -q 'opencode-dispatch.opencode.prompt.txt' /tmp/opencode_dispatch.out \
  && grep -q 'cat -- ' /tmp/opencode_dispatch.out \
  && ! grep -q 'do work' /tmp/opencode_dispatch.out \
  && [ ! -e "$TMP/opencode-dispatch.log" ]; then
  ok "opencode dispatch wrapper dry-runs headless command without registry write"
else
  bad "opencode dispatch wrapper should dry-run headless command without registry write"
fi
mkdir -p "$TMP/opencode-stubbin"
cat > "$TMP/opencode-stubbin/opencode" <<'EOF'
#!/usr/bin/env sh
printf '%s\n' "$*" > "$OPENCODE_STUB_ARGV"
EOF
chmod +x "$TMP/opencode-stubbin/opencode"
if PATH="$TMP/opencode-stubbin:$PATH" OPENCODE_STUB_ARGV="$TMP/opencode-start.argv" \
  HOME="$TMP/opencode_headless_home" XDG_CONFIG_HOME="$TMP/opencode_headless_home/.config" \
  "$OPENCODE" dispatch --start --worktree "$TMP/repo" --slug nested/opencode-start --capability autopilot-code --mode dev/backend --qa standard --prompt-text "nested work" --jobs "$TMP/opencode-start.log" --log-dir "$TMP/opencode-logs" >/tmp/opencode_dispatch_start.out 2>/tmp/opencode_dispatch_start.err \
  && grep -q '^status=start$' /tmp/opencode_dispatch_start.out \
  && grep -q '^started=1$' /tmp/opencode_dispatch_start.out \
  && grep -q 'cat -- ' /tmp/opencode_dispatch_start.out \
  && [ -f "$TMP/opencode-logs/nested/opencode-start.opencode.prompt.txt" ]; then
  for _ in $(seq 1 20); do
    [ -f "$TMP/opencode-start.argv" ] && break
    sleep 0.1
  done
  if grep -q 'nested work' "$TMP/opencode-start.argv" 2>/dev/null; then
    ok "opencode dispatch wrapper starts nested slug from prompt file"
  else
    bad "opencode dispatch wrapper should pass nested prompt content to opencode"
  fi
else
  bad "opencode dispatch wrapper should start nested slug from prompt file"
fi
if "$OPENCODE" dispatch --dry-run --worktree "$TMP/repo" --slug opencode-default-home --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" >/tmp/opencode_dispatch_default.out 2>/tmp/opencode_dispatch_default.err \
  && grep -Fxq "job_registry=$ROOT/.dispatch/jobs.log" /tmp/opencode_dispatch_default.out \
  && grep -Fxq "prompt_file=$ROOT/.dispatch/logs/opencode-default-home.opencode.prompt.txt" /tmp/opencode_dispatch_default.out \
  && [ ! -e "$AGENT_HOME/.dispatch/jobs.log" ]; then
  ok "opencode dispatch wrapper defaults to validated harness root"
else
  bad "opencode dispatch wrapper should not trust invalid AGENT_HOME for default registry"
fi
if AGENT_HOME="$TMP/not-agent-home" python3 "$ROOT/adapters/opencode/bin/dispatch-headless.py" --dry-run --worktree "$TMP/repo" --slug opencode-direct-home --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" >/tmp/opencode_dispatch_direct.out 2>/tmp/opencode_dispatch_direct.err \
  && grep -Fxq "job_registry=$ROOT/.dispatch/jobs.log" /tmp/opencode_dispatch_direct.out \
  && grep -Fxq "prompt_file=$ROOT/.dispatch/logs/opencode-direct-home.opencode.prompt.txt" /tmp/opencode_dispatch_direct.out; then
  ok "opencode dispatch script ignores invalid AGENT_HOME"
else
  bad "opencode dispatch script should validate AGENT_HOME"
fi
if "$OPENCODE" dispatch --register --worktree "$TMP/repo" --slug opencode-dispatch --capability autopilot-code --mode dev/backend --qa standard --prompt-text "do work" --jobs "$TMP/opencode-dispatch.log" >/tmp/opencode_dispatch.out 2>/tmp/opencode_dispatch.err \
  && grep -q '^status=register$' /tmp/opencode_dispatch.out \
  && grep -q '^registered=1$' /tmp/opencode_dispatch.out \
  && grep -q '^started=0$' /tmp/opencode_dispatch.out \
  && grep -q $'open\t.*/repo\t.*/repo\topencode-dispatch\tcapability=autopilot-code,mode=dev/backend,qa=standard' "$TMP/opencode-dispatch.log"; then
  ok "opencode dispatch wrapper registers open headless job"
else
  bad "opencode dispatch wrapper should register open headless job"
fi
if "$OPENCODE" harvest --jobs "$TMP/opencode-dispatch.log" --slug opencode-dispatch >/tmp/opencode_harvest.out 2>/tmp/opencode_harvest.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_harvest.out \
  && grep -q '^runtime_surface=opencode-dispatch-harvest$' /tmp/opencode_harvest.out \
  && grep -q '^matched=1$' /tmp/opencode_harvest.out \
  && grep -q '^marked_done=0$' /tmp/opencode_harvest.out \
  && grep -q '^job_status=open$' /tmp/opencode_harvest.out \
  && grep -q '^merge_action=unsupported$' /tmp/opencode_harvest.out; then
  ok "opencode harvest wrapper reports open registry jobs"
else
  bad "opencode harvest wrapper should report open registry jobs"
fi
if "$OPENCODE" harvest --jobs "$TMP/opencode-dispatch.log" --slug opencode-dispatch --mark-done >/tmp/opencode_harvest_done.out 2>/tmp/opencode_harvest_done.err \
  && grep -q '^marked_done=1$' /tmp/opencode_harvest_done.out \
  && grep -q $'done\t.*/repo\t.*/repo\topencode-dispatch\tcapability=autopilot-code,mode=dev/backend,qa=standard' "$TMP/opencode-dispatch.log"; then
  ok "opencode harvest wrapper marks selected jobs done"
else
  bad "opencode harvest wrapper should mark selected jobs done"
fi
OPENCODE_DB="$TMP/opencode.db" python3 - <<EOF
import sqlite3, time
con = sqlite3.connect("$TMP/opencode.db")
now = int(time.time() * 1000)
con.executescript("""
CREATE TABLE session (id text PRIMARY KEY, project_id text NOT NULL, workspace_id text, parent_id text, slug text NOT NULL, directory text NOT NULL, path text, title text NOT NULL, version text NOT NULL, share_url text, summary_additions integer, summary_deletions integer, summary_files integer, summary_diffs text, metadata text, cost real DEFAULT 0 NOT NULL, tokens_input integer DEFAULT 0 NOT NULL, tokens_output integer DEFAULT 0 NOT NULL, tokens_reasoning integer DEFAULT 0 NOT NULL, tokens_cache_read integer DEFAULT 0 NOT NULL, tokens_cache_write integer DEFAULT 0 NOT NULL, revert text, permission text, agent text, model text, time_created integer NOT NULL, time_updated integer NOT NULL, time_compacting integer, time_archived integer);
CREATE TABLE message (id text PRIMARY KEY, session_id text NOT NULL, time_created integer NOT NULL, time_updated integer NOT NULL, data text NOT NULL);
CREATE TABLE part (id text PRIMARY KEY, message_id text NOT NULL, session_id text NOT NULL, time_created integer NOT NULL, time_updated integer NOT NULL, data text NOT NULL);
CREATE TABLE session_message (id text PRIMARY KEY, session_id text NOT NULL, type text NOT NULL, seq integer NOT NULL, time_created integer NOT NULL, time_updated integer NOT NULL, data text NOT NULL);
CREATE TABLE session_input (id text PRIMARY KEY, session_id text NOT NULL, prompt text NOT NULL, delivery text NOT NULL, admitted_seq integer NOT NULL, promoted_seq integer, time_created integer NOT NULL);
""")
con.execute("INSERT INTO session (id, project_id, workspace_id, parent_id, slug, directory, path, title, version, time_created, time_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("ses_live", "proj", None, None, "live-open", "$TMP/flowproj", "", "title", "1", now - 1000, now - 1000))
con.execute("INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)", ("msg_live", "ses_live", now - 900, now - 800, "{}"))
con.commit()
EOF
printf '2026-06-30T00:00:00Z\topen\t%s\t%s\tlive-opencode\t-\n' "$TMP/repo" "$TMP/flowproj" > "$TMP/opencode-jobs.log"
if OPENCODE_DB="$TMP/opencode.db" DISPATCH_STALE_MIN=60 "$OPENCODE" liveness "$TMP/opencode-jobs.log" >/tmp/opencode_liveness.out 2>/tmp/opencode_liveness.err \
  && grep -q '^ALIVE    live-opencode ' /tmp/opencode_liveness.out \
  && grep -q '^open 1 ; alive 1 ; suspect/dead 0$' /tmp/opencode_liveness.out; then
  ok "opencode liveness wrapper matches worktree to session DB"
else
  bad "opencode liveness wrapper should match worktree to session DB"
fi
printf '2026-06-30T00:00:00Z\topen\t%s\t%s\tdead-opencode\t-\n' "$TMP/repo" "$TMP/missing-opencode-wt" > "$TMP/opencode-dead-jobs.log"
if OPENCODE_DB="$TMP/opencode.db" "$OPENCODE" liveness "$TMP/opencode-dead-jobs.log" >/tmp/opencode_liveness_dead.out 2>/tmp/opencode_liveness_dead.err; then
  bad "opencode liveness wrapper should fail dead jobs"
else
  rc=$?
  if [ "$rc" -eq 3 ] \
    && grep -q '^DEAD     dead-opencode ' /tmp/opencode_liveness_dead.out \
    && grep -q '^open 1 ; alive 0 ; suspect/dead 1$' /tmp/opencode_liveness_dead.out; then
    ok "opencode liveness wrapper reports dead jobs"
  else
    bad "opencode liveness wrapper should report dead jobs"
  fi
fi
if "$OPENCODE" mcp >/tmp/opencode_mcp.out 2>/tmp/opencode_mcp.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_mcp.out \
  && grep -q '^runtime_surface=opencode-native-mcp$' /tmp/opencode_mcp.out \
  && grep -q '^mcp_surface=opencode mcp$' /tmp/opencode_mcp.out \
  && grep -q '^design_mcp_projection=unsupported$' /tmp/opencode_mcp.out \
  && grep -q '^claude_settings_mcp=unsupported$' /tmp/opencode_mcp.out; then
  ok "opencode mcp wrapper reports native MCP contract"
else
  bad "opencode mcp wrapper should report native MCP contract"
fi
if "$OPENCODE" mcp --check >/tmp/opencode_mcp_check.out 2>/tmp/opencode_mcp_check.err \
  && grep -q '^check=ok$' /tmp/opencode_mcp_check.out; then
  ok "opencode mcp wrapper checks native MCP CLI"
else
  bad "opencode mcp wrapper should check native MCP CLI"
fi
if "$OPENCODE" loop-info oncall >/tmp/opencode_loop_oncall.out 2>/tmp/opencode_loop_oncall.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_loop_oncall.out \
  && grep -q '^loop=oncall$' /tmp/opencode_loop_oncall.out \
  && grep -q '^source=loops/oncall.md$' /tmp/opencode_loop_oncall.out \
  && grep -q '^status=manual-contract$' /tmp/opencode_loop_oncall.out \
  && grep -q '^runtime_surface=opencode-loop-guidance$' /tmp/opencode_loop_oncall.out \
  && grep -q '^executable_projection=unsupported-runtime-script$' /tmp/opencode_loop_oncall.out; then
  ok "opencode loop wrapper reports oncall manual contract"
else
  bad "opencode loop wrapper should report oncall manual contract"
fi
if "$OPENCODE" loop-info drill >/tmp/opencode_loop_drill.out 2>/tmp/opencode_loop_drill.err \
  && grep -q '^source=loops/drill/README.md$' /tmp/opencode_loop_drill.out \
  && grep -q '^status=manual-contract$' /tmp/opencode_loop_drill.out \
  && grep -q '^trigger=manual-only$' /tmp/opencode_loop_drill.out \
  && grep -q '^auto_run=unsupported$' /tmp/opencode_loop_drill.out \
  && grep -q '^fallback=report-drill-would-be-useful$' /tmp/opencode_loop_drill.out; then
  ok "opencode loop wrapper prevents automatic drill execution"
else
  bad "opencode loop wrapper should prevent automatic drill execution"
fi
if "$OPENCODE" loop-info study >/tmp/opencode_loop_study.out 2>/tmp/opencode_loop_study.err \
  && grep -q '^source=loops/study.md$' /tmp/opencode_loop_study.out \
  && grep -q '^status=manual-contract$' /tmp/opencode_loop_study.out \
  && grep -q '^action=proposal-report-only$' /tmp/opencode_loop_study.out \
  && grep -q '^fallback=read-source-and-draft-proposal-in-main-session$' /tmp/opencode_loop_study.out; then
  ok "opencode loop wrapper reports study proposal contract"
else
  bad "opencode loop wrapper should report study proposal contract"
fi
if "$OPENCODE" loop-info note >/tmp/opencode_loop_note.out 2>/tmp/opencode_loop_note.err \
  && grep -q '^loop=note$' /tmp/opencode_loop_note.out \
  && grep -q '^status=unsupported$' /tmp/opencode_loop_note.out \
  && grep -q '^runtime_surface=missing-native-loop$' /tmp/opencode_loop_note.out \
  && grep -q '^related_capability=autopilot-note$' /tmp/opencode_loop_note.out \
  && grep -q '^native_capability_surface=opencode-native-skill-command$' /tmp/opencode_loop_note.out \
  && grep -q '^scheduler_surface=external-worklog-board$' /tmp/opencode_loop_note.out \
  && grep -q '^fallback=worklog-board-or-manual-post-it-flow$' /tmp/opencode_loop_note.out; then
  ok "opencode loop wrapper marks missing note loop unsupported"
else
  bad "opencode loop wrapper should mark missing note loop unsupported"
fi

echo "== opencode role mapping =="
if AGENT_MODEL_FAST=fast-model AGENT_VARIANT_FAST=low "$OPENCODE" role fast reviewer >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^family=fast$' /tmp/opencode_role.out \
  && grep -q '^adapter=opencode$' /tmp/opencode_role.out \
  && grep -q '^source=roles/README.md$' /tmp/opencode_role.out \
  && grep -q '^model=fast-model$' /tmp/opencode_role.out \
  && grep -q '^variant=low$' /tmp/opencode_role.out; then
  ok "opencode role wrapper maps fast portable role"
else
  bad "opencode role wrapper should map fast portable role"
fi
if AGENT_MODEL_ORCHESTRATOR=provider/orchestrator-model AGENT_VARIANT_ORCHESTRATOR=medium "$OPENCODE" role external adversary orchestrator >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^family=orchestrator$' /tmp/opencode_role.out \
  && grep -q '^adapter=opencode$' /tmp/opencode_role.out \
  && grep -q '^model=provider/orchestrator-model$' /tmp/opencode_role.out \
  && grep -q '^variant=medium$' /tmp/opencode_role.out \
  && grep -q '^available=1$' /tmp/opencode_role.out \
  && grep -q '^status=configured$' /tmp/opencode_role.out; then
  ok "opencode role wrapper maps external adversary orchestrator role"
else
  bad "opencode role wrapper should map external adversary orchestrator role"
fi
if "$OPENCODE" role external adversary >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^available=0$' /tmp/opencode_role.out \
  && grep -q '^status=unavailable$' /tmp/opencode_role.out; then
  ok "opencode role wrapper marks external adversary unavailable by default"
else
  bad "opencode role wrapper should mark external adversary unavailable by default"
fi
if AGENT_MODEL_EXTERNAL=provider/external-model AGENT_VARIANT_EXTERNAL=high "$OPENCODE" role external adversary >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^family=external$' /tmp/opencode_role.out \
  && grep -q '^available=1$' /tmp/opencode_role.out \
  && grep -q '^status=configured$' /tmp/opencode_role.out \
  && grep -q '^model=provider/external-model$' /tmp/opencode_role.out \
  && grep -q '^variant=high$' /tmp/opencode_role.out; then
  ok "opencode role wrapper maps configured external adversary model"
else
  bad "opencode role wrapper should map configured external adversary model"
fi
if AGENT_EXTERNAL_CMD="sh -c" "$OPENCODE" role external adversary >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^available=1$' /tmp/opencode_role.out \
  && grep -q '^status=configured$' /tmp/opencode_role.out \
  && grep -q '^model=external-command$' /tmp/opencode_role.out \
  && grep -q '^external_command=sh -c$' /tmp/opencode_role.out; then
  ok "opencode role wrapper accepts external adversary command with args"
else
  bad "opencode role wrapper should accept external adversary command with args"
fi
if AGENT_EXTERNAL_CMD="missing-external-adversary-command --review" "$OPENCODE" role external adversary >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^available=0$' /tmp/opencode_role.out \
  && grep -q '^status=unavailable$' /tmp/opencode_role.out \
  && grep -q '^reason=AGENT_EXTERNAL_CMD not found: missing-external-adversary-command$' /tmp/opencode_role.out; then
  ok "opencode role wrapper reports missing external adversary command"
else
  bad "opencode role wrapper should report missing external adversary command"
fi
if "$OPENCODE" role fast reviewer >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^model=opencode-default$' /tmp/opencode_role.out \
  && grep -q '^variant=runtime-default$' /tmp/opencode_role.out; then
  ok "opencode role wrapper reports opencode-default when unconfigured"
else
  bad "opencode role wrapper should report opencode-default when unconfigured"
fi
if command -v opencode >/dev/null 2>&1; then
  mkdir -p "$TMP/opencode_bootstrap_home/.config/opencode" "$TMP/opencode_bootstrap_home/.local/share"
  if OPENCODE_CONFIG_CONTENT="{\"instructions\":[\"$ROOT/opencode_setting/AGENTS.md\"],\"skills\":{\"paths\":[\"$ROOT/opencode_setting/opencode-skills\"]}}" \
    HOME="$TMP/opencode_bootstrap_home" XDG_CONFIG_HOME="$TMP/opencode_bootstrap_home/.config" XDG_DATA_HOME="$TMP/opencode_bootstrap_home/.local/share" \
    opencode debug config --pure >/tmp/opencode_bootstrap.out 2>/tmp/opencode_bootstrap.err \
    && grep -q "$ROOT/opencode_setting/AGENTS.md" /tmp/opencode_bootstrap.out \
    && grep -q "$ROOT/opencode_setting/opencode-skills" /tmp/opencode_bootstrap.out \
    && ! grep -q '/.claude/' /tmp/opencode_bootstrap.out; then
    ok "opencode bootstrap config projects instructions and skills without Claude paths"
  else
    bad "opencode bootstrap config should project instructions and skills without Claude paths"
  fi
else
  ok "opencode bootstrap config runtime discovery skipped (opencode not installed)"
fi
if command -v opencode >/dev/null 2>&1; then
  mkdir -p "$TMP/opencode_home/.config/opencode/agent" "$TMP/opencode_home/.local/share"
  for f in "$ROOT"/opencode_setting/opencode-agents/*/*.md; do
    [ -f "$f" ] || continue
    ln -s "$f" "$TMP/opencode_home/.config/opencode/agent/$(basename "$f")"
  done
  if HOME="$TMP/opencode_home" XDG_CONFIG_HOME="$TMP/opencode_home/.config" XDG_DATA_HOME="$TMP/opencode_home/.local/share" \
    opencode debug agent plan-team --pure >/tmp/opencode_agent.out 2>/tmp/opencode_agent.err \
    && grep -q '"description": "OpenCode-native agent for portable role profile plan-team' /tmp/opencode_agent.out \
    && grep -q 'roles/README.md' /tmp/opencode_agent.out \
    && ! grep -q '/.claude/' /tmp/opencode_agent.out; then
    ok "opencode native agent projection is discoverable without Claude paths"
  else
    bad "opencode native agent projection should be discoverable without Claude paths"
  fi
  if HOME="$TMP/opencode_home" XDG_CONFIG_HOME="$TMP/opencode_home/.config" XDG_DATA_HOME="$TMP/opencode_home/.local/share" \
    opencode debug agent qa-team --pure >/tmp/opencode_agent_qa.out 2>/tmp/opencode_agent_qa.err \
    && python3 - /tmp/opencode_agent_qa.out <<'PY'
import json
import sys

agent = json.load(open(sys.argv[1], encoding="utf-8"))
tools = agent.get("tools", {})
rules = {(r.get("permission"), r.get("action")) for r in agent.get("permission", [])}
assert tools.get("edit") is False, tools
assert tools.get("write") is False, tools
assert tools.get("task") is False, tools
assert ("edit", "deny") in rules, rules
assert ("task", "deny") in rules, rules
PY
  then
    ok "opencode qa agent projection enforces read-only and depth-one tools"
  else
    bad "opencode qa agent projection should disable edit/write/task"
  fi
else
  ok "opencode native agent runtime discovery skipped (opencode not installed)"
fi
if command -v opencode >/dev/null 2>&1; then
  mkdir -p "$TMP/opencode_command_home/.config/opencode/command" "$TMP/opencode_command_home/.local/share"
  for f in "$ROOT"/opencode_setting/opencode-commands/*.md; do
    [ -f "$f" ] || continue
    ln -s "$f" "$TMP/opencode_command_home/.config/opencode/command/$(basename "$f")"
  done
  if HOME="$TMP/opencode_command_home" XDG_CONFIG_HOME="$TMP/opencode_command_home/.config" XDG_DATA_HOME="$TMP/opencode_command_home/.local/share" \
    opencode debug config --pure >/tmp/opencode_command.out 2>/tmp/opencode_command.err \
    && grep -q '"autopilot-code": {' /tmp/opencode_command.out \
    && grep -q '"description": "Run the portable autopilot-code capability through the OpenCode adapter' /tmp/opencode_command.out \
    && ! grep -q '/.claude/' /tmp/opencode_command.out; then
    ok "opencode native command projection is discoverable without Claude paths"
  else
    bad "opencode native command projection should be discoverable without Claude paths"
  fi
else
  ok "opencode native command runtime discovery skipped (opencode not installed)"
fi
if command -v opencode >/dev/null 2>&1; then
  mkdir -p "$TMP/opencode_plugin_project/.opencode/plugins" "$TMP/opencode_plugin_home/.config" "$TMP/opencode_plugin_home/.local/share"
  ln -s "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js" "$TMP/opencode_plugin_project/.opencode/plugins/agent-harness-guards.js"
  if (
    cd "$TMP/opencode_plugin_project" || exit 1
    HOME="$TMP/opencode_plugin_home" XDG_CONFIG_HOME="$TMP/opencode_plugin_home/.config" XDG_DATA_HOME="$TMP/opencode_plugin_home/.local/share" \
      opencode debug config >/tmp/opencode_plugin.out 2>/tmp/opencode_plugin.err
  ) && grep -q 'agent-harness-guards.js' /tmp/opencode_plugin.out \
    && ! grep -q 'adapters/claude/hooks' /tmp/opencode_plugin.out; then
    ok "opencode native plugin projection is discoverable without Claude hooks"
  else
    bad "opencode native plugin projection should be discoverable without Claude hooks"
  fi
else
  ok "opencode native plugin runtime discovery skipped (opencode not installed)"
fi
if node --input-type=module >/tmp/opencode_plugin_hook.out 2>/tmp/opencode_plugin_hook.err <<EOF
import { AgentHarnessGuards } from "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js"
const plugin = await AgentHarnessGuards({ directory: "$TMP/repo", worktree: "$TMP/repo" })
await plugin["tool.execute.before"]({ tool: "write", sessionID: "testsid" }, { args: { filePath: "$TMP/repo/f" } })
EOF
then
  ok "opencode native plugin write hook bridges to preflight"
else
  bad "opencode native plugin write hook should bridge to preflight"
fi
mkdir -p "$TMP/fake_agent_home/adapters/opencode/bin"
cat > "$TMP/fake_agent_home/adapters/opencode/bin/preflight.sh" <<'EOF'
#!/usr/bin/env sh
exit 77
EOF
chmod +x "$TMP/fake_agent_home/adapters/opencode/bin/preflight.sh"
if node --input-type=module >/tmp/opencode_plugin_invalid_home.out 2>/tmp/opencode_plugin_invalid_home.err <<EOF
process.env.AGENT_HOME = "$TMP/fake_agent_home"
const mod = await import("$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js")
const plugin = await mod.AgentHarnessGuards({ directory: "$TMP/repo", worktree: "$TMP/repo" })
await plugin["tool.execute.before"]({ tool: "write", sessionID: "testsid" }, { args: { filePath: "$TMP/repo/f" } })
EOF
then
  ok "opencode native plugin ignores invalid AGENT_HOME"
else
  bad "opencode native plugin should validate AGENT_HOME"
fi
mkdir -p "$TMP/opencode_copied_plugin"
cp "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js" "$TMP/opencode_copied_plugin/agent-harness-guards.js"
if node --input-type=module >/tmp/opencode_plugin_copy.out 2>/tmp/opencode_plugin_copy.err <<EOF
process.env.AGENT_HOME = "$ROOT"
const mod = await import("$TMP/opencode_copied_plugin/agent-harness-guards.js")
const plugin = await mod.AgentHarnessGuards({ directory: "$TMP/repo", worktree: "$TMP/repo" })
await plugin["tool.execute.before"]({ tool: "write", sessionID: "testsid" }, { args: { filePath: "$TMP/repo/f" } })
EOF
then
  ok "opencode native plugin copy resolves harness through AGENT_HOME"
else
  bad "opencode native plugin copy should resolve harness through AGENT_HOME"
fi
if node --input-type=module >/tmp/opencode_plugin_lifecycle.out 2>/tmp/opencode_plugin_lifecycle.err <<EOF
import { AgentHarnessGuards } from "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js"
const plugin = await AgentHarnessGuards({ directory: "$TMP/flowproj", worktree: "$TMP/flowproj" })
await plugin["chat.message"]({ sessionID: "oplifecyclesid" }, { parts: [{ type: "text", text: "remember this project context" }] })
const output = { system: [] }
await plugin["experimental.chat.system.transform"]({ sessionID: "oplifecyclesid", model: {} }, output)
if (!output.system.join("\\n").includes("tracked")) process.exit(1)
if (output.system.join("\\n").includes("adapters/claude") || output.system.join("\\n").includes("statusline.sh")) process.exit(1)
EOF
then
  ok "opencode native plugin prompt lifecycle bridges to preflight"
else
  bad "opencode native plugin prompt lifecycle should bridge to preflight"
fi
if node --input-type=module >/tmp/opencode_plugin_hook_block.out 2>/tmp/opencode_plugin_hook_block.err <<EOF
import { AgentHarnessGuards } from "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js"
const plugin = await AgentHarnessGuards({ directory: "$TMP/runtime", worktree: "$TMP/runtime" })
try {
  await plugin["tool.execute.before"]({ tool: "write", sessionID: "testsid" }, { args: { filePath: "$TMP/runtime/projects/abc/memory/MEMORY.md" } })
  process.exit(1)
} catch (error) {
  if (!String(error.message || error).includes("memory")) process.exit(1)
}
EOF
then
  ok "opencode native plugin write hook blocks guarded writes"
else
  bad "opencode native plugin write hook should block guarded writes"
fi
if DESIGN_POSTWRITE_HOOK=0 node --input-type=module >/tmp/opencode_plugin_design_hook.out 2>/tmp/opencode_plugin_design_hook.err <<EOF
import { AgentHarnessGuards } from "$ROOT/opencode_setting/opencode-plugins/agent-harness-guards.js"
const plugin = await AgentHarnessGuards({ directory: "$TMP/repo", worktree: "$TMP/repo" })
await plugin["tool.execute.after"]({ tool: "write", sessionID: "testsid", args: { filePath: "$TMP/repo/spec/design/preview.html" } }, {})
EOF
then
  ok "opencode native plugin design after hook bridges to preflight"
else
  bad "opencode native plugin design after hook should bridge to preflight"
fi

echo "== opencode capability mapping =="
if "$OPENCODE" capability-info autopilot-code >/tmp/opencode_cap.out 2>/tmp/opencode_cap.err \
  && grep -q '^capability=autopilot-code$' /tmp/opencode_cap.out \
  && grep -q '^adapter=opencode$' /tmp/opencode_cap.out \
  && grep -q '^native_skill=1$' /tmp/opencode_cap.out \
  && grep -q '^native_skill_path=adapters/opencode/skills/autopilot-code/SKILL.md$' /tmp/opencode_cap.out \
  && grep -q '^native_command=1$' /tmp/opencode_cap.out \
  && grep -q '^native_command_path=adapters/opencode/commands/autopilot-code.md$' /tmp/opencode_cap.out \
  && grep -q '^realization=opencode-native-skill-command$' /tmp/opencode_cap.out \
  && grep -q '^compat_reference=not-projected$' /tmp/opencode_cap.out \
  && ! grep -q '^compat_reference=skills/' /tmp/opencode_cap.out \
  && grep -q '^status=instruction-only$' /tmp/opencode_cap.out; then
  ok "opencode capability wrapper reports native skill and command realization"
else
  bad "opencode capability wrapper should report native skill and command realization"
fi
tmp_map_root="$TMP/opencode_map_root"
mkdir -p "$tmp_map_root/adapters/opencode/bin" "$tmp_map_root/capabilities"
cp "$ROOT/adapters/opencode/bin/capability-map.sh" "$tmp_map_root/adapters/opencode/bin/capability-map.sh"
cat >"$tmp_map_root/capabilities/README.md" <<'EOF'
| Capability | Meaning |
|---|---|
| `autopilot-code` | test |
EOF
if "$tmp_map_root/adapters/opencode/bin/capability-map.sh" autopilot-code >/tmp/opencode_cap_missing.out 2>/tmp/opencode_cap_missing.err \
  && grep -q '^native_skill=0$' /tmp/opencode_cap_missing.out \
  && grep -q '^native_command=0$' /tmp/opencode_cap_missing.out \
  && grep -q '^realization=portable-instructions$' /tmp/opencode_cap_missing.out \
  && grep -q '^note=OpenCode has no native Skill/command realization' /tmp/opencode_cap_missing.out; then
  ok "opencode capability wrapper downgrades note when native projections are missing"
else
  bad "opencode capability wrapper should not claim missing native projections"
fi
if "$OPENCODE" capability-info design-review >/tmp/opencode_cap.out 2>/tmp/opencode_cap.err \
  && grep -q '^capability=design-review$' /tmp/opencode_cap.out \
  && grep -q '^native_skill=1$' /tmp/opencode_cap.out \
  && grep -q '^native_command=1$' /tmp/opencode_cap.out \
  && grep -q '^realization=opencode-native-skill-command$' /tmp/opencode_cap.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_cap.out \
  && grep -q '^tool_contract=visual-harness$' /tmp/opencode_cap.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness <file.html>$' /tmp/opencode_cap.out \
  && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_cap.out \
  && grep -q '^fallback=preflight.sh visual-harness <file.html>$' /tmp/opencode_cap.out; then
  ok "opencode design capability reports visual harness contract"
else
  bad "opencode design capability should report visual harness contract"
fi
if "$OPENCODE" visual-harness >/tmp/opencode_visual.out 2>/tmp/opencode_visual.err; then
  if grep -q '^adapter=opencode$' /tmp/opencode_visual.out \
    && grep -q '^status=tool-contract$' /tmp/opencode_visual.out \
    && grep -q '^tool_contract=visual-harness$' /tmp/opencode_visual.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_visual.out \
    && ! grep -q 'adapters/claude\|claude_setting\|settings.json\|statusline.sh' /tmp/opencode_visual.out; then
    ok "opencode visual harness reports adapter-native tool-contract"
  else
    bad "opencode visual harness should report adapter-native tool-contract"
  fi
else
  bad "opencode visual harness should report adapter-native tool-contract"
fi
cat >"$TMP/opencode-preview.html" <<'EOF'
<!doctype html><html><body><h1>OpenCode visual harness</h1></body></html>
EOF
if "$OPENCODE" visual-harness "$TMP/opencode-preview.html" --out "$TMP/opencode-visual" >/tmp/opencode_visual_file.out 2>/tmp/opencode_visual_file.err; then
  if grep -q '^adapter=opencode$' /tmp/opencode_visual_file.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_visual_file.out \
    && grep -q '^status=ok$' /tmp/opencode_visual_file.out \
    && grep -q '^console_errors=0$' /tmp/opencode_visual_file.out \
    && [ -f "$TMP/opencode-visual/opencode-preview-html.png" ]; then
    ok "opencode visual harness renders HTML when checker dependencies exist"
  else
    bad "opencode visual harness should render HTML when checker dependencies exist"
  fi
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_visual_file.out \
    && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_visual_file.out \
    && grep -q '^status=tool-contract$' /tmp/opencode_visual_file.out \
    && grep -q '^reason=playwright-unavailable$' /tmp/opencode_visual_file.out; then
    ok "opencode visual harness reports unavailable checker dependency"
  else
    bad "opencode visual harness should render or report unavailable checker dependency"
  fi
fi
cat >"$TMP/opencode-data-script.py" <<'EOF'
import sys

print("rows=3")
print("args=" + ",".join(sys.argv[1:]))
EOF
if "$OPENCODE" data-script --check "$TMP/opencode-data-script.py" >/tmp/opencode_data_script.out 2>/tmp/opencode_data_script.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_data_script.out \
  && grep -q '^tool_contract=data-script$' /tmp/opencode_data_script.out \
  && grep -q '^runtime_surface=adapter-owned-data-script$' /tmp/opencode_data_script.out \
  && grep -q '^check=python-compile$' /tmp/opencode_data_script.out \
  && grep -q '^status=ok$' /tmp/opencode_data_script.out; then
  ok "opencode data-script wrapper checks Python analysis scripts"
else
  bad "opencode data-script wrapper should check Python analysis scripts"
fi
if "$OPENCODE" claim-verify >/tmp/opencode_claim_verify.out 2>/tmp/opencode_claim_verify.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_claim_verify.out \
  && grep -q '^tool_contract=external-claim-verification$' /tmp/opencode_claim_verify.out \
  && grep -q '^runtime_surface=adapter-owned-claim-verify$' /tmp/opencode_claim_verify.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_claim_verify.out; then
  ok "opencode claim-verify wrapper reports tool contract"
else
  bad "opencode claim-verify wrapper should report tool contract"
fi
if "$OPENCODE" claim-verify --check "model X is state of the art" >/tmp/opencode_claim_unavailable.out 2>/tmp/opencode_claim_unavailable.err; then
  bad "opencode claim-verify wrapper should report unavailable provider by default"
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_claim_unavailable.out \
    && grep -q '^reason=claim-verify-provider-unavailable$' /tmp/opencode_claim_unavailable.out; then
    ok "opencode claim-verify wrapper reports unavailable provider"
  else
    bad "opencode claim-verify wrapper should report unavailable provider"
  fi
fi
if "$OPENCODE" figure-gen >/tmp/opencode_figure_gen.out 2>/tmp/opencode_figure_gen.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_figure_gen.out \
  && grep -q '^tool_contract=figure-gen$' /tmp/opencode_figure_gen.out \
  && grep -q '^runtime_surface=adapter-owned-figure-gen$' /tmp/opencode_figure_gen.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_figure_gen.out; then
  ok "opencode figure-gen wrapper reports tool contract"
else
  bad "opencode figure-gen wrapper should report tool contract"
fi
if "$OPENCODE" figure-gen --check "$TMP/missing-figure.py" >/tmp/opencode_figure_missing.out 2>/tmp/opencode_figure_missing.err; then
  bad "opencode figure-gen wrapper should fail missing script"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_figure_missing.out \
    && grep -q '^reason=file-not-found$' /tmp/opencode_figure_missing.out; then
    ok "opencode figure-gen wrapper reports missing script"
  else
    bad "opencode figure-gen wrapper should report missing script"
  fi
fi
if "$OPENCODE" browser-fetch >/tmp/opencode_browser_fetch.out 2>/tmp/opencode_browser_fetch.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_browser_fetch.out \
  && grep -q '^tool_contract=browser-fetch$' /tmp/opencode_browser_fetch.out \
  && grep -q '^runtime_surface=adapter-owned-browser-fetch$' /tmp/opencode_browser_fetch.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_browser_fetch.out; then
  ok "opencode browser-fetch wrapper reports tool contract"
else
  bad "opencode browser-fetch wrapper should report tool contract"
fi
if "$OPENCODE" browser-fetch --check not-a-url >/tmp/opencode_browser_bad_url.out 2>/tmp/opencode_browser_bad_url.err; then
  bad "opencode browser-fetch wrapper should fail bad URL"
else
  rc=$?
  if [ "$rc" -eq 65 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_browser_bad_url.out \
    && grep -q '^reason=bad-url$' /tmp/opencode_browser_bad_url.out; then
    ok "opencode browser-fetch wrapper reports bad URL"
  else
    bad "opencode browser-fetch wrapper should report bad URL"
  fi
fi
if "$OPENCODE" pdf-extract >/tmp/opencode_pdf_extract.out 2>/tmp/opencode_pdf_extract.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_pdf_extract.out \
  && grep -q '^tool_contract=pdf-extract$' /tmp/opencode_pdf_extract.out \
  && grep -q '^runtime_surface=adapter-owned-pdf-extract$' /tmp/opencode_pdf_extract.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_pdf_extract.out; then
  ok "opencode pdf-extract wrapper reports tool contract"
else
  bad "opencode pdf-extract wrapper should report tool contract"
fi
if "$OPENCODE" pdf-extract --check "$TMP/missing.pdf" >/tmp/opencode_pdf_missing.out 2>/tmp/opencode_pdf_missing.err; then
  bad "opencode pdf-extract wrapper should fail missing PDF"
else
  rc=$?
  if [ "$rc" -eq 66 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_pdf_missing.out \
    && grep -q '^reason=file-not-found$' /tmp/opencode_pdf_missing.out; then
    ok "opencode pdf-extract wrapper reports missing PDF"
  else
    bad "opencode pdf-extract wrapper should report missing PDF"
  fi
fi
if "$OPENCODE" web-image-search >/tmp/opencode_web_image.out 2>/tmp/opencode_web_image.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_web_image.out \
  && grep -q '^tool_contract=web-image-search$' /tmp/opencode_web_image.out \
  && grep -q '^runtime_surface=adapter-owned-web-image-search$' /tmp/opencode_web_image.out \
  && grep -q '^status=tool-contract$' /tmp/opencode_web_image.out; then
  ok "opencode web-image-search wrapper reports tool contract"
else
  bad "opencode web-image-search wrapper should report tool contract"
fi
if "$OPENCODE" web-image-search --check "speech enhancement timeline" >/tmp/opencode_web_image_unavailable.out 2>/tmp/opencode_web_image_unavailable.err; then
  bad "opencode web-image-search wrapper should report unavailable provider by default"
else
  rc=$?
  if [ "$rc" -eq 69 ] \
    && grep -q '^adapter=opencode$' /tmp/opencode_web_image_unavailable.out \
    && grep -q '^reason=web-image-search-provider-unavailable$' /tmp/opencode_web_image_unavailable.out; then
    ok "opencode web-image-search wrapper reports unavailable provider"
  else
    bad "opencode web-image-search wrapper should report unavailable provider"
  fi
fi
if "$OPENCODE" verification-runner --check -- python3 >/tmp/opencode_verify_check.out 2>/tmp/opencode_verify_check.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_verify_check.out \
  && grep -q '^tool_contract=verification-runner$' /tmp/opencode_verify_check.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/opencode_verify_check.out \
  && grep -q '^check=command-available$' /tmp/opencode_verify_check.out \
  && grep -q '^status=ok$' /tmp/opencode_verify_check.out; then
  ok "opencode verification runner checks explicit commands"
else
  bad "opencode verification runner should check explicit commands"
fi
if "$OPENCODE" verification-runner --timeout 5 -- python3 -c 'print("verify-ok")' >/tmp/opencode_verify_run.out 2>/tmp/opencode_verify_run.err \
  && grep -q '^adapter=opencode$' /tmp/opencode_verify_run.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/opencode_verify_run.out \
  && grep -q '^status=ok$' /tmp/opencode_verify_run.out \
  && grep -q '^exit_code=0$' /tmp/opencode_verify_run.out \
  && grep -q 'verify-ok' /tmp/opencode_verify_run.out; then
  ok "opencode verification runner executes explicit commands"
else
  bad "opencode verification runner should execute explicit commands"
fi
if command -v opencode >/dev/null 2>&1; then
  if OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
    OPENCODE_CONFIG_CONTENT="{\"skills\":{\"paths\":[\"$ROOT/opencode_setting/opencode-skills\"]}}" \
    opencode debug skill --pure >/tmp/opencode_skills.out 2>/tmp/opencode_skills.err; then
    if grep -q '"name": "autopilot-code"' /tmp/opencode_skills.out \
      && grep -q "$ROOT/opencode_setting/opencode-skills/autopilot-code/SKILL.md" /tmp/opencode_skills.out \
      && ! grep -q '"location": ".*/\\.claude/skills' /tmp/opencode_skills.out; then
      ok "opencode native skill projection is discoverable without Claude compat autoload"
    else
      bad "opencode native skill projection should be discoverable without Claude compat autoload"
    fi
  else
    ok "opencode native skill runtime discovery skipped (opencode unavailable or sandboxed)"
  fi
else
  ok "opencode native skill runtime discovery skipped (opencode not installed)"
fi

echo "== opencode mode mapping =="
if "$OPENCODE" mode-info dev/backend >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=portable$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-persona$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper maps portable mode"
else
  bad "opencode mode wrapper should map portable mode"
fi
if "$OPENCODE" mode-info qa/security-review >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=portable$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-persona$' /tmp/opencode_mode.out \
  && grep -q 'read-only security review with OpenCode file and git diff tools' /tmp/opencode_mode.out \
  && ! grep -q '^tool_contract=' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper treats security-review as portable read-only guidance"
else
  bad "opencode mode wrapper should treat security-review as portable read-only guidance"
fi
opencode_design_modes_ok=1
for mode_file in "$ROOT"/roles/modes/design/*.md; do
  mode_name=$(basename "$mode_file" .md)
  [ "$mode_name" = "_design_rules" ] && continue
  mode="design/$mode_name"
  if ! "$OPENCODE" mode-info "$mode" >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
    || ! grep -q '^status=unsupported$' /tmp/opencode_mode.out \
    || ! grep -q '^realization=adapter-coupled$' /tmp/opencode_mode.out \
    || ! grep -q '^tool_contract=visual-harness$' /tmp/opencode_mode.out \
    || ! grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness <file.html>$' /tmp/opencode_mode.out \
    || ! grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_mode.out \
    || ! grep -q '^fallback=reference-only$' /tmp/opencode_mode.out; then
    opencode_design_modes_ok=0
    break
  fi
done
if [ "$opencode_design_modes_ok" -eq 1 ]; then
  ok "opencode mode wrapper marks every adapter-coupled design mode unsupported"
else
  bad "opencode mode wrapper should mark every adapter-coupled design mode unsupported"
fi
if "$OPENCODE" mode-info material/data-script >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=data-script$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh data-script --check <script.py>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-data-script$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports material data-script contract surface"
else
  bad "opencode mode wrapper should report material data-script contract surface"
fi
if "$OPENCODE" mode-info material/figure-gen >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=figure-gen$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh figure-gen --check <script.py>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-figure-gen$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports material figure-gen contract surface"
else
  bad "opencode mode wrapper should report material figure-gen contract surface"
fi
if "$OPENCODE" mode-info material/pdf-extract >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=pdf-extract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh pdf-extract --check <file.pdf>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-pdf-extract$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports material pdf-extract contract surface"
else
  bad "opencode mode wrapper should report material pdf-extract contract surface"
fi
if "$OPENCODE" mode-info qa/test >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=verification-runner$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh verification-runner --check -- <command>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-verification-runner$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports qa test verification runner surface"
else
  bad "opencode mode wrapper should report qa test verification runner surface"
fi
if "$OPENCODE" mode-info material/browser-fetch >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=browser-fetch$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh browser-fetch --check <url>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-browser-fetch$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports material browser-fetch contract surface"
else
  bad "opencode mode wrapper should report material browser-fetch contract surface"
fi
if "$OPENCODE" mode-info material/web-image-search >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^realization=portable-with-tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=web-image-search$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh web-image-search --check <query>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-web-image-search$' /tmp/opencode_mode.out \
  && grep -q '^fallback=satisfy-tool-contract-or-report-unavailable$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports material web-image-search contract surface"
else
  bad "opencode mode wrapper should report material web-image-search contract surface"
fi
if "$OPENCODE" mode-info research/claim-verify >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=tool-contract$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=external-claim-verification$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh claim-verify --check <claim>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-claim-verify$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper reports named claim verification contract"
else
  bad "opencode mode wrapper should report named claim verification contract"
fi

echo "== opencode distill source =="
cat > "$TMP/opencode-export.json" <<'EOF'
{"messages":[
  {"id":"ou1","role":"user","time":"2026-06-29T00:00:00.000Z","content":[{"type":"text","text":"open hello"}]},
  {"id":"oa1","role":"assistant","time":"2026-06-29T00:00:01.000Z","content":[{"type":"text","text":"open world"}]},
  {"id":"ot1","type":"tool_call","name":"bash","time":"2026-06-29T00:00:02.000Z"}
]}
EOF
if OPENCODE_EXPORT_FILE="$TMP/opencode-export.json" "$OPENCODE" distill-delta opencodesid >/tmp/opencode_delta.out 2>/tmp/opencode_delta.err \
  && grep -q '^\[user\] open hello' /tmp/opencode_delta.out \
  && grep -q '^\[assistant\] open world' /tmp/opencode_delta.out \
  && grep -q '^\[assistant\] \[tool:bash\]' /tmp/opencode_delta.out; then
  ok "opencode export source distills transcript"
else
  bad "opencode export source should distill transcript"
fi
if "$OPENCODE_DISTILL" opencodesid "$TMP/flowproj" >/tmp/opencode_distill.out 2>/tmp/opencode_distill.err; then
  bad "opencode distill worker should report tool-contract until worker contract is verified"
else
  if [ "$?" -eq 69 ] \
    && grep -q '^status=tool-contract$' /tmp/opencode_distill.out \
    && grep -q '^reason=no-tools-worker-unverified$' /tmp/opencode_distill.out; then
    ok "opencode distill worker reports tool-contract by default"
  else
    bad "opencode distill worker should exit 69 with tool-contract by default"
  fi
fi
if OPENCODE_DISTILL_ENABLE=1 "$OPENCODE" distill-propose opencodesid "$TMP/flowproj" >/tmp/opencode_distill.out 2>/tmp/opencode_distill.err; then
  bad "opencode distill proposal should report tool-contract while worker contract is unverified"
else
  [ "$?" -eq 69 ] && ok "opencode distill proposal exits 69 for worker tool-contract" || bad "opencode distill proposal wrong exit"
fi

printf 'PASS=%s FAIL=%s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
