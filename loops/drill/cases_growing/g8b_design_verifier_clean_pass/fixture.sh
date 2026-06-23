#!/bin/bash
# g8b_design_verifier_clean_pass: 정상적인(깨지지 않은) 디자인 HTML 을 빌드한다.
#   verifier 가 clean fixture 에 과잉 실패(breakage / needs_work)를 반환하면 FAIL.
#   g8 의 대칭 제어 케이스 — "깨진 걸 잡는가" 의 반대편: "멀쩡한 걸 통과시키는가".
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo"
cd "$WORK/repo"

git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill

# --- clean preview.html: 에러 없음, 레이아웃 정상 ---
cat > preview.html <<'HTML_EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clean Design Preview</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
      margin: 0;
      padding: 2rem;
      background: #f8f9fa;
      color: #212529;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    .header {
      background: #343a40;
      color: #fff;
      padding: 1.5rem 2rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
    }
    .header h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
    }
    .card {
      background: #fff;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    .card h2 {
      margin: 0 0 0.75rem;
      font-size: 1.1rem;
      color: #495057;
    }
    .card p {
      margin: 0;
      line-height: 1.6;
      color: #6c757d;
    }
    .badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 1rem;
      font-size: 0.8rem;
      font-weight: 600;
      background: #e9ecef;
      color: #495057;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>디자인 산출물 (정상)</h1>
    </div>
    <div class="card">
      <h2>프로젝트 개요 <span class="badge">완료</span></h2>
      <p>이 디자인 산출물은 콘솔 에러, 레이아웃 overflow, 요소 겹침, 0px-height 없이 올바르게 렌더링됩니다.</p>
    </div>
    <div class="card">
      <h2>기능 목록</h2>
      <p>정상적인 박스 모델, 명확한 시각 계층, 적절한 contrast 비율을 갖춘 깨끗한 레이아웃입니다.</p>
    </div>
  </div>
  <!-- 스크립트 없음 — 콘솔 에러 발생 원인 전무 -->
</body>
</html>
HTML_EOF

# --- design_state.yaml ---
mkdir -p .claude_reports/spec
cat > .claude_reports/spec/design_state.yaml <<'YAML_EOF'
phase: review
artifact: preview.html
design_files:
  - preview.html
phases:
  design_init: done
  scaffolding: done
  iteration: done
  review: in_progress
YAML_EOF

cat > .claude_reports/spec/pipeline_state.yaml <<'YAML_EOF'
mode: [app]
phases:
  spec: done
  dev: done
  design: in_progress
YAML_EOF

cat > _design_rules.md <<'MD_EOF'
# Design Rules

## 원칙
1. 콘솔 에러 0 건 — pageerror · console.error · request failed 모두 차단
2. 레이아웃 overflow 없음
3. 요소 겹침(overlap) 없음
4. 0px-height container 없음
MD_EOF

git add -A && git commit -q -m "fixture: clean design HTML (no errors, no layout breakage)"

# --- pre-state: 정상 기준 마커 동적 캡처 ---
# 에러 유발 코드가 없음을 확인
no_error_line=$(grep -n "스크립트 없음" preview.html | head -1 | cut -d: -f1)
echo "clean_comment_line=$no_error_line" > "$WORK/.pre/refs"
echo "expected=PASS_no_breakage"        >> "$WORK/.pre/refs"

# enc_cwd: run.sh cleanup 보조
enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
echo "$enc" > "$WORK/.pre/enc_cwd"
