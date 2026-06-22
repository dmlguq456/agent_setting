#!/bin/bash
# g7_semantic_deterministic_boundary: spec 이 "의미 판단"을 명시했는데 구현은 토큰 규칙만인 모순을
#   검출하는가 (worklog-board 참사, 2026-06-22 / DESIGN_PRINCIPLES §0.7).
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill

# spec 파일 — 의미 판단 요구 명시
mkdir -p .claude_reports/spec
cat > .claude_reports/spec/prd.md <<'EOF'
# PRD — Worklog Matcher (api mode)

## [api] 매칭

사용자 입력과 worklog 항목을 **의미상 맞는** 항목으로 매칭한다.
단순 토큰 일치가 아니라 맥락·의미 판단으로 가장 적합한 항목을 반환해야 한다.

### 요구사항

- 입력: 사용자 자연어 질의
- 출력: 의미상 적합한 worklog 항목 목록 (scored)
- 제약: semantic 유사도 기준으로 정렬; 동음이의·약어도 맥락에 따라 올바르게 처리
EOF

# spec 파이프라인 상태 — cwd 를 spec-backed 로 만들기
cat > .claude_reports/spec/pipeline_state.yaml <<'EOF'
mode: [api]
phases:
  spec: done
  dev: in_progress
EOF

# 구현 파일 — 토큰 매칭만 (의미 요구를 규칙으로 떨군 모순)
mkdir -p src
cat > src/match.py <<'EOF'
"""Worklog matcher — token-only matching (no semantic judgment)."""


def match(query: str, entries: list[str]) -> list[str]:
    """Return worklog entries matching the query.

    Implementation: token intersection only.
    """
    q_tokens = set(query.split())
    results = []
    for entry in entries:
        e_tokens = set(entry.split())
        if q_tokens & e_tokens:  # simple token overlap, no semantic reasoning
            results.append(entry)
    return results
EOF

# plans stub — src/match.py 참조
mkdir -p .claude_reports/plans/2026-06-22_worklog-matcher/plan
cat > .claude_reports/plans/2026-06-22_worklog-matcher/plan/plan.md <<'EOF'
# Plan — worklog matcher implementation

target: src/match.py
status: in_progress

## 작업 내용

- match() 함수 구현 (src/match.py)
EOF

git add -A && git commit -q -m init

# pre-state: spec 의미요구 줄 · 토큰매칭 줄을 동적 캡처 (placeholder 하드코딩 금지)
sp=$(grep -n "의미상 맞는" .claude_reports/spec/prd.md | head -1 | cut -d: -f1)
cp=$(grep -n "q_tokens & e_tokens" src/match.py | head -1 | cut -d: -f1)
echo "spec_line=$sp" > "$WORK/.pre/refs"
echo "code_line=$cp" >> "$WORK/.pre/refs"

# cleanup 용 enc_cwd (run.sh cleanup 보조)
enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
echo "$enc" > "$WORK/.pre/enc_cwd"
