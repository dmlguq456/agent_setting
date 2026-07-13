#!/bin/bash
# g7 static-assert: skill-design 정량 규범(CONVENTIONS §5.6a) 회귀 게이트 (SD-4).
# live skills/ 에 tools/skill-conformance/scan.sh 를 돌려 정량 규범 위반 0 을 강제한다.
# 사용자 turn 없음 (config AXIS=static) — run.sh 가 adapter 실행을 건너뛰고 이 assert 만 돈다.
set -u
# ROOT = harness repo root (production 또는 worktree — 스크립트 자기 경로 기준).
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../../.." && pwd)
cd "$ROOT" || { echo "FAIL: repo root 해석 실패 ($ROOT)"; exit 1; }
[ -x tools/skill-conformance/scan.sh ] || { echo "FAIL: tools/skill-conformance/scan.sh 부재/비실행 (CORE-4 이전 상태?)"; exit 1; }

TSV=$(bash tools/skill-conformance/scan.sh skills 2>/dev/null) || { echo "FAIL: scan.sh 실행 오류"; exit 1; }
fail=0

# 헤더 스키마 drift 방어 (컬럼 인덱스 가정 보호)
hdr=$(printf '%s\n' "$TSV" | head -1)
[ "$(printf '%s\n' "$hdr" | cut -f1)" = "name" ] || { echo "FAIL: scan.sh TSV 스키마 변경 (헤더 첫 컬럼 name 아님)"; fail=1; }

body=$(printf '%s\n' "$TSV" | tail -n +2)

# (a) body_lines < 500 : line_ok=N 행 0
bad_len=$(printf '%s\n' "$body" | awk -F'\t' '$3=="N"{print $1}')
[ -n "$bad_len" ] && { echo "FAIL: SKILL.md ≥500 lines (line_ok=N): $bad_len — CONVENTIONS §5.6a"; fail=1; }

# (b) references/ 1-depth : ref_depth_ok=N 행 0 ('-' = references 없음 → 무관)
bad_depth=$(printf '%s\n' "$body" | awk -F'\t' '$9=="N"{print $1}')
[ -n "$bad_depth" ] && { echo "FAIL: references/ 2-depth (ref_depth_ok=N): $bad_depth — CONVENTIONS §5.6a"; fail=1; }

# (c) invocation frontmatter : disable_model 컬럼이 결정론적으로 파싱되는지 (true/false 만).
#     TODO(Cluster 1): flip 후 순수 sub-skill 13개(code-*·design-*·draft-refine·draft-strategy)의
#     disable_model=true 를 강제로 상향한다. 현재 stage(flip 전)에선 컬럼 파싱 무결성만 검증 —
#     이 assertion 은 flip 전(전부 false)에도, flip 후(sub-skill true)에도 자연히 PASS 한다.
bad_disable=$(printf '%s\n' "$body" | awk -F'\t' '$4!="true" && $4!="false"{print $1"="$4}')
[ -n "$bad_disable" ] && { echo "FAIL: disable_model 컬럼 파싱 불가 (true/false 아님): $bad_disable"; fail=1; }

[ "$fail" = 0 ] && echo "PASS: skill-conformance 정량 규범 (line_ok · ref_depth_ok · disable_model 파싱) 통과"
exit $fail
