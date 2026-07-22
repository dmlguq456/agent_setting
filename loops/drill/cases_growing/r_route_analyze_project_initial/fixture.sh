#!/bin/bash
# 명시적 분석 요청 + usable analysis 부재. 기대 primary = analyze-project(code).
set -eu
WORK="$1"; REPO="$WORK/repo"
mkdir -p "$REPO/src/sample" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > src/sample/pipeline.py <<'EOF'
class Pipeline:
    def __init__(self, loader, transform):
        self.loader = loader
        self.transform = transform

    def run(self, source):
        records = self.loader.load(source)
        return [self.transform.apply(record) for record in records]
EOF

cat > src/sample/io.py <<'EOF'
class ListLoader:
    def load(self, source):
        return list(source)
EOF

cat > README.md <<'EOF'
# Sample pipeline

`Pipeline` loads records and applies an injected transform.
EOF

git add -A && git commit -qm init
git ls-files -s > "$WORK/.pre/source-index.baseline"
