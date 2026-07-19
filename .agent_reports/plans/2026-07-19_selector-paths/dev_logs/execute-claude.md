# code-execute log — selector-paths

worktree: `/home/Uihyeop/agent_setting-wt/selector-paths` (branch `selector-paths`)
commit: `35d60fc1`

## Diff

```diff
diff --git a/utilities/dispatch-route.sh b/utilities/dispatch-route.sh
index a583e7ec..88700442 100755
--- a/utilities/dispatch-route.sh
+++ b/utilities/dispatch-route.sh
@@ -20,12 +20,21 @@ case "$family" in ''|claude|gpt|unknown) ;; *) echo "dispatch-route: unknown fam
 case "$maker_family" in ''|claude|gpt|unknown) ;; *) echo "dispatch-route: unknown maker family: $maker_family" >&2; exit 64;; esac
 case "$adapter:$family" in claude:gpt|codex:claude|opencode:claude|opencode:gpt) echo 'dispatch-route: adapter/family conflict' >&2; exit 64;; esac
 
+# selector-paths: resolve this script's real location so internal helper
+# lookups work when it is invoked through the adapters/<harness>/utilities/
+# symlink projection. readlink -f canonicalizes the symlink to the true
+# utilities/ dir; if readlink lacks -f (non-GNU) it fails and we keep the
+# prior $0-based dirname path.
+real_self=$(readlink -f "$0" 2>/dev/null) || real_self=$0
+self_dir=$(CDPATH= cd -- "$(dirname -- "$real_self")" && pwd)
+repo_root=$(CDPATH= cd -- "$self_dir/.." && pwd)
+
 # SD-66: profiles/dispatch-defaults.yaml is the user-declared source for
 # stage-affinity (SD-22 cascade step 3). Validate unconditionally so a
 # malformed config fails loud even when an explicit --adapter/--family
 # already decides this call; resolution honors DISPATCH_DEFAULTS_CONFIG for
 # fixtures via utilities/dispatch-defaults.py.
-defaults_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/dispatch-defaults.py"
+defaults_script="$self_dir/dispatch-defaults.py"
 python3 "$defaults_script" validate >/dev/null || { echo 'dispatch-route: invalid dispatch-defaults config' >&2; exit 64; }
 config_affinity=$(python3 "$defaults_script" affinity --capability "$capability" --stage "$stage")
 
@@ -35,7 +44,7 @@ case "$stage" in
   *) default_role='deep orchestrator'; affinity=neutral;;
 esac
 [ -n "$role" ] || role=$default_role
-usage_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/usage-check.sh"
+usage_script="$self_dir/usage-check.sh"
 if [ -n "$jobs" ]; then usage=$($usage_script --harness all --jobs "$jobs"); else usage=$($usage_script --harness all); fi
 state() { printf '%s\n' "$usage" | awk -v h="$1" '$1==h {print $2}'; }
 bias=$(printf '%s\n' "$usage" | awk '$1=="bias" {print $2; exit}')
@@ -100,8 +109,8 @@ if ! eligible "$choose"; then
   fi
 fi
 case "$choose" in
-  codex) map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/codex/bin/model-map.sh";;
-  claude) map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/claude/bin/model-map.sh";;
+  codex) map="$repo_root/adapters/codex/bin/model-map.sh";;
+  claude) map="$repo_root/adapters/claude/bin/model-map.sh";;
 esac
 mapped=$($map "$role")
 get() { printf '%s\n' "$mapped" | awk -F= -v k="$1" '$1==k {sub(/^[^=]*=/, ""); print; exit}'; }
diff --git a/utilities/dispatch-route.test.sh b/utilities/dispatch-route.test.sh
index ca6e5e2d..7db4437b 100755
--- a/utilities/dispatch-route.test.sh
+++ b/utilities/dispatch-route.test.sh
@@ -163,4 +163,24 @@ export DISPATCH_DEFAULTS_CONFIG="$cfg"
 before=$(sha256sum "$jobs"); route --capability autopilot-code --stage execute >/dev/null; after=$(sha256sum "$jobs"); [ "$before" = "$after" ]
 unset DISPATCH_DEFAULTS_CONFIG
 
+# ---- selector-paths: adapter-projection surface resolves helpers ----
+# Invoking through each adapters/<h>/utilities/ symlink must resolve the
+# internal helpers (dispatch-defaults.py, usage-check.sh, model-map.sh) the
+# same as the real utilities/ path. 'adapter=' is only emitted after model-map
+# resolves, so asserting it proves the repo-root climb (L103-104) is fixed.
+# Fixture isolation preserved via an explicit DISPATCH_DEFAULTS_CONFIG.
+: > "$jobs"
+for h in claude codex opencode; do
+  proj="$root/adapters/$h/utilities/dispatch-route.sh"
+  out=$(DISPATCH_DEFAULTS_CONFIG="$cfg" AGENT_HOME="$tmp" "$proj" --jobs "$jobs" \
+        --stage test --capability autopilot-code --maker-family gpt)
+  assert "$out" 'status=eligible'
+  printf '%s\n' "$out" | grep -q '^adapter=' \
+    || { echo "projection $h did not reach adapter= output" >&2; exit 1; }
+done
+# plan stage once through a projection exercises the codex model-map branch.
+out=$(DISPATCH_DEFAULTS_CONFIG="$cfg" AGENT_HOME="$tmp" \
+      "$root/adapters/claude/utilities/dispatch-route.sh" --jobs "$jobs" --stage plan)
+assert "$out" 'adapter=codex'; assert "$out" 'role=deep maker'
+
 echo 'dispatch-route: PASS'
```

## Commands run and results

1. `sh -n utilities/dispatch-route.sh && dash -n utilities/dispatch-route.sh && sh -n utilities/dispatch-route.test.sh && dash -n utilities/dispatch-route.test.sh` → `SYNTAX_OK`
2. `sh utilities/dispatch-route.test.sh` → `dispatch-route: PASS`
3. Manual 3-adapter projection: `adapters/{claude,codex,opencode}/utilities/dispatch-route.sh --stage test --capability autopilot-code --maker-family gpt` → all `status=eligible`, `adapter=claude` (diverse affinity + maker_family gpt + bias claude → claude chosen; matches non-projected baseline logic, not a regression — the fix only corrects path resolution, not the cascade).
4. Manual plan projection: `adapters/claude/utilities/dispatch-route.sh --stage plan` → `status=eligible`, `adapter=codex`, `role=deep maker`.
5. `find adapters -name __pycache__ -type d -prune -exec rm -rf {} +` → cleaned.
6. `bash tools/check-adaptation-boundary.sh` → `OK: adaptation boundary checks passed`, exit 0.
7. `python3 utilities/dispatch_contract.test.py` → 10 tests, OK.
8. `python3 utilities/dispatch_node.test.py` → 17 tests, OK.
9. `python3 adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` → each has 1 pre-existing failure (`test_route_consumer_and_*_refusal`, `returncode 73 != 0`) **unrelated to this change**: reproduced identically on baseline via `git stash` + rerun of `adapters/claude/bin/dispatch-headless.sd45.test.py` (same single failure, same assertion, before any selector-paths edit was applied). Not a regression introduced by this fix.
10. `bash adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` → all 3: PASS.

## Scope

Two files changed, ~10 net logic lines (plus test block): `utilities/dispatch-route.sh`, `utilities/dispatch-route.test.sh`. `utilities/dispatch-defaults.py` untouched. No cascade/output/exit-code change — verified identical output shape and field values across projected vs. real invocation paths.

## Notes

- The sd45 failures (`dispatch-headless.sd45.test.py` for all three adapters) are pre-existing on branch `selector-paths` prior to this commit (confirmed via `git stash`). Flagged for visibility but out of scope for this plan (SD-23 read-only boundary; `usage-check.sh`/`model-map.sh` internal logic and worker-route-guard are explicitly out of scope per plan §5).
