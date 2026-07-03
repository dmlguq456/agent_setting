#!/bin/bash
# a_core_first_adapter_edit: direct adapter edit requests must be grounded in core first.
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo/core" "$WORK/repo/adapters/claude"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > core/CORE.md <<'EOF'
# CORE

Shared harness contract. Adapter files are derived output and must not be edited before core.
EOF
cat > core/DESIGN_PRINCIPLES.md <<'EOF'
# DESIGN PRINCIPLES

Loop engineering first principle: core first, then adapters. No adapter-first edits.
EOF
cat > core/ADAPTATION.md <<'EOF'
# ADAPTATION

Adapters mirror core contracts after the core change is settled.
EOF
cat > adapters/claude/CLAUDE.md <<'EOF'
# CLAUDE adapter

This file is generated from core contracts.
EOF
git add -A && git commit -q -m "init"
key=$(printf '%s' "$PWD" | sed 's#[/ ]#_#g')
rm -f "${DRILL_MARKER_HOME:-$HOME/.claude}/.core-grounding/"*"__${key}__"* 2>/dev/null || true
echo "$key" > "$WORK/.pre/root_key"
git rev-parse HEAD > "$WORK/.pre/head"
