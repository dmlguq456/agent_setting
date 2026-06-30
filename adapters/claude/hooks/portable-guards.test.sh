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
if AGENT_MODEL_FAST=fast-model AGENT_REASONING_FAST=low "$CODEX" role fast reviewer >/tmp/role.out 2>/tmp/role.err \
  && grep -q '^family=fast$' /tmp/role.out \
  && grep -q '^adapter=codex$' /tmp/role.out \
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
  && grep -q '^native_skill=1$' /tmp/cap.out \
  && grep -q '^native_skill_path=adapters/codex/skills/autopilot-code/SKILL.md$' /tmp/cap.out \
  && grep -q '^native_plugin=1$' /tmp/cap.out \
  && grep -q '^native_plugin_skill_path=adapters/codex/plugins/agent-harness-codex/skills/autopilot-code/SKILL.md$' /tmp/cap.out \
  && grep -q '^realization=codex-native-skill-plugin$' /tmp/cap.out \
  && grep -q '^status=instruction-only$' /tmp/cap.out; then
  ok "codex capability wrapper reports native skill and plugin realization"
else
  bad "codex capability wrapper should report native skill and plugin realization"
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
  if CODEX_HOME="$TMP/codex_plugin_home" codex plugin marketplace add "$ROOT/codex_setting/codex-plugin-marketplace" --json >/tmp/codex_plugin_marketplace.out 2>/tmp/codex_plugin_marketplace.err \
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
mkdir -p "$TMP/codex_hook_home/.codex"
ln -s "$ROOT" "$TMP/codex_hook_home/.codex/agent-harness"
ln -s "$ROOT/codex_setting/codex-hooks/hooks.json" "$TMP/codex_hook_home/.codex/hooks.json"
if python3 -m json.tool "$TMP/codex_hook_home/.codex/hooks.json" >/tmp/codex_hook_json.out 2>/tmp/codex_hook_json.err \
  && grep -q 'sessionstart-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q 'userprompt-lifecycle.py' /tmp/codex_hook_json.out \
  && grep -q 'pretooluse-write-guard.py' /tmp/codex_hook_json.out \
  && grep -q 'posttooluse-design-check.py' /tmp/codex_hook_json.out \
  && printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo/f" "$TMP/repo" \
    | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_hook.out 2>/tmp/codex_hook.err \
  && [ ! -s /tmp/codex_hook.out ]; then
  ok "codex native hook projection bridges clean writes to preflight"
else
  bad "codex native hook projection should bridge clean writes to preflight"
fi
if printf '{"session_id":"testsid","cwd":"%s"}\n' "$TMP/repo" \
  | MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/sessionstart-lifecycle.py" >/tmp/codex_session_hook.out 2>/tmp/codex_session_hook.err \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_session_hook.out /tmp/codex_session_hook.err; then
  ok "codex native hook projection bridges session start lifecycle"
else
  bad "codex native hook projection should bridge session start lifecycle"
fi
if "$CODEX" track "$TMP/flowproj" promptlifecyclesid >/tmp/codex_prompt_toggle.out 2>/tmp/codex_prompt_toggle.err \
  && printf '{"prompt":"remember this project context","session_id":"promptlifecyclesid","cwd":"%s"}\n' "$TMP/flowproj" \
  | MEM_STORE="$TMP/codex_hook_mem" HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/userprompt-lifecycle.py" >/tmp/codex_prompt_hook.out 2>/tmp/codex_prompt_hook.err \
  && grep -q 'untracked' /tmp/codex_prompt_hook.out \
  && ! grep -q 'adapters/claude\|claude_setting\|statusline.sh' /tmp/codex_prompt_hook.out /tmp/codex_prompt_hook.err; then
  ok "codex native hook projection bridges prompt lifecycle"
else
  bad "codex native hook projection should bridge prompt lifecycle"
fi
if printf '{"tool_name":"Write","tool_input":{"file_path":"%s"},"session_id":"testsid","cwd":"%s"}\n' "$TMP/runtime/projects/abc/memory/MEMORY.md" "$TMP/runtime" \
  | HOME="$TMP/codex_hook_home" python3 "$TMP/codex_hook_home/.codex/agent-harness/adapters/codex/hooks/pretooluse-write-guard.py" >/tmp/codex_hook_block.out 2>/tmp/codex_hook_block.err \
  && grep -q '"decision": "block"' /tmp/codex_hook_block.out \
  && grep -q 'memory' /tmp/codex_hook_block.out; then
  ok "codex native hook projection blocks guarded writes"
else
  bad "codex native hook projection should block guarded writes"
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
if "$CODEX" mode-info design/maker >/tmp/mode.out 2>/tmp/mode.err \
  && grep -q '^status=unsupported$' /tmp/mode.out \
  && grep -q '^realization=adapter-coupled$' /tmp/mode.out \
  && grep -q '^tool_contract=visual-harness$' /tmp/mode.out \
  && grep -q '^tool_contract_check=adapters/codex/bin/preflight.sh visual-harness <file.html>$' /tmp/mode.out \
  && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/mode.out \
  && grep -q '^fallback=reference-only$' /tmp/mode.out; then
  ok "codex mode wrapper marks adapter-coupled design mode unsupported"
else
  bad "codex mode wrapper should mark adapter-coupled design mode unsupported"
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
  && grep -q '^tool_contract=external-claim-verification$' /tmp/mode.out; then
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

echo "== opencode role mapping =="
if AGENT_MODEL_FAST=fast-model AGENT_VARIANT_FAST=low "$OPENCODE" role fast reviewer >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^family=fast$' /tmp/opencode_role.out \
  && grep -q '^adapter=opencode$' /tmp/opencode_role.out \
  && grep -q '^model=fast-model$' /tmp/opencode_role.out \
  && grep -q '^variant=low$' /tmp/opencode_role.out; then
  ok "opencode role wrapper maps fast portable role"
else
  bad "opencode role wrapper should map fast portable role"
fi
if "$OPENCODE" role external adversary >/tmp/opencode_role.out 2>/tmp/opencode_role.err \
  && grep -q '^available=0$' /tmp/opencode_role.out \
  && grep -q '^status=unavailable$' /tmp/opencode_role.out; then
  ok "opencode role wrapper marks external adversary unavailable by default"
else
  bad "opencode role wrapper should mark external adversary unavailable by default"
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
await plugin["tool.execute.before"]({ tool: { name: "write" }, sessionID: "testsid" }, { args: { filePath: "$TMP/repo/f" } })
EOF
then
  ok "opencode native plugin write hook bridges to preflight"
else
  bad "opencode native plugin write hook should bridge to preflight"
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
  await plugin["tool.execute.before"]({ tool: { name: "write" }, sessionID: "testsid" }, { args: { filePath: "$TMP/runtime/projects/abc/memory/MEMORY.md" } })
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
await plugin["tool.execute.after"]({ tool: { name: "write" }, sessionID: "testsid" }, { args: { filePath: "$TMP/repo/spec/design/preview.html" } })
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
if "$OPENCODE" mode-info design/maker >/tmp/opencode_mode.out 2>/tmp/opencode_mode.err \
  && grep -q '^status=unsupported$' /tmp/opencode_mode.out \
  && grep -q '^realization=adapter-coupled$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract=visual-harness$' /tmp/opencode_mode.out \
  && grep -q '^tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness <file.html>$' /tmp/opencode_mode.out \
  && grep -q '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode_mode.out \
  && grep -q '^fallback=reference-only$' /tmp/opencode_mode.out; then
  ok "opencode mode wrapper marks adapter-coupled design mode unsupported"
else
  bad "opencode mode wrapper should mark adapter-coupled design mode unsupported"
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
  && grep -q '^tool_contract=external-claim-verification$' /tmp/opencode_mode.out; then
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
if "$OPENCODE_DISTILL" opencodesid "$TMP/flowproj" >/tmp/opencode_distill.out 2>/tmp/opencode_distill.err \
  && [ ! -s /tmp/opencode_distill.out ]; then
  ok "opencode distill worker is disabled by default"
else
  bad "opencode distill worker should no-op unless enabled"
fi
if OPENCODE_DISTILL_ENABLE=1 "$OPENCODE" distill-propose opencodesid "$TMP/flowproj" >/tmp/opencode_distill.out 2>/tmp/opencode_distill.err; then
  bad "opencode distill proposal should report tool-contract while worker contract is unverified"
else
  [ "$?" -eq 69 ] && ok "opencode distill proposal exits 69 for worker tool-contract" || bad "opencode distill proposal wrong exit"
fi

printf 'PASS=%s FAIL=%s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
