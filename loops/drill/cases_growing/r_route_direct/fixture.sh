#!/bin/bash
# r_route_direct — typo·1줄급 수정은 직접 처리 (과잉 파이프 회귀). routing 축.
# g3(기능 추가→브랜치)의 반대 경계: 자잘한 건 ceremony 안 태운다.
set -eu
WORK="$1"; REPO="$WORK/repo"
mkdir -p "$REPO" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t
cat > util.py <<'EOF'
def helper():
    # recieve the input and process
    return 42
EOF
git add -A && git commit -qm init
echo "typo: recieve" > "$WORK/.pre/before.txt"
