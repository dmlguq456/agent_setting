# Checklist — selector-paths

## Implement — `utilities/dispatch-route.sh`
- [ ] Insert resolution block after arg validation (after L21, before SD-66 comment):
      `real_self=$(readlink -f "$0" 2>/dev/null) || real_self=$0`
      `self_dir=$(CDPATH= cd -- "$(dirname -- "$real_self")" && pwd)`
      `repo_root=$(CDPATH= cd -- "$self_dir/.." && pwd)`
- [ ] L28 → `defaults_script="$self_dir/dispatch-defaults.py"`
- [ ] L38 → `usage_script="$self_dir/usage-check.sh"`
- [ ] L103 → `map="$repo_root/adapters/codex/bin/model-map.sh"`
- [ ] L104 → `map="$repo_root/adapters/claude/bin/model-map.sh"`
- [ ] No logic/cascade/output-format change; no bashisms; do NOT touch `dispatch-defaults.py`

## Implement — `utilities/dispatch-route.test.sh`
- [ ] Add projection-surface block before final `echo 'dispatch-route: PASS'`
- [ ] Loop claude/codex/opencode projected paths; assert `status=eligible` + `adapter=`
- [ ] One `--stage plan` projected call asserts `adapter=codex` + `role=deep maker`
- [ ] Explicit `DISPATCH_DEFAULTS_CONFIG="$cfg"`/`AGENT_HOME="$tmp"` (fixture isolation)
- [ ] ALL existing assertions retained; `: > "$jobs"` before the block

## Verify (from worktree)
- [ ] `sh -n` + `dash -n` clean: `dispatch-route.sh` AND `dispatch-route.test.sh`
- [ ] `sh utilities/dispatch-route.test.sh` → `dispatch-route: PASS`
- [ ] Manual 3-adapter projection (`--stage test ... --maker-family gpt`) → eligible/`adapter=`
- [ ] Manual `--stage plan` projection → `adapter=codex`
- [ ] `find adapters -name __pycache__ -type d -prune -exec rm -rf {} +`
- [ ] `bash tools/check-adaptation-boundary.sh` → exit 0
- [ ] `python3 utilities/dispatch_contract.test.py` pass
- [ ] `python3 utilities/dispatch_node.test.py` pass
- [ ] sd45 x3: `python3 adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py`
- [ ] sd15 x3: `bash adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh`

## Gate
- [ ] Two files changed only; SD-23 read-only preserved; zero regression
