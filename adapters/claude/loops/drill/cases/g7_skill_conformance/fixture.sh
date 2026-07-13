#!/bin/bash
# g7 static-assert: 사용자 turn 없음 (AXIS=static). live tree 검사와 함께
# invocation checker의 양방향 failure control을 WORK 아래에 만든다.
set -eu
WORK=$1
ROOT=$(git -C "$(dirname -- "$0")" rev-parse --show-toplevel 2>/dev/null) || exit 1
mkdir -p "$WORK/repo" "$WORK/broken-parent/code-plan" \
  "$WORK/broken-user/manual-probe" "$WORK/good-user/manual-probe"

cp "$ROOT/skills/code-plan/SKILL.md" "$WORK/broken-parent/code-plan/SKILL.md"
sed -i '/^name: code-plan$/a disable-model-invocation: true' "$WORK/broken-parent/code-plan/SKILL.md"

cat > "$WORK/broken-user/manual-probe/SKILL.md" <<'EOF'
---
name: manual-probe
description: Manual-only invocation fixture.
---
Manual fixture.
EOF
cat > "$WORK/good-user/manual-probe/SKILL.md" <<'EOF'
---
name: manual-probe
description: Manual-only invocation fixture.
disable-model-invocation: true
---
Manual fixture.
EOF
printf 'code-plan\tparent-invoked\tfixture\n' > "$WORK/parent-policy.tsv"
printf 'manual-probe\tuser-only\tfixture\n' > "$WORK/user-policy.tsv"
