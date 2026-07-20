#!/usr/bin/env python3
"""Apply the stage-dispatch v19 component-spec transaction under the shared lock."""

from __future__ import annotations

import os
from pathlib import Path
import shutil


SPEC_ROOT = Path(os.environ["AGENT_SPEC_ROOT"]).resolve()
EXPECTED_ROOT = Path(
    "/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch"
).resolve()
if os.environ.get("AGENT_SPEC_LOCK_HELD") != "1" or SPEC_ROOT != EXPECTED_ROOT:
    raise SystemExit("stage-dispatch spec lock/root contract missing")
if os.environ.get("AGENT_SPEC_NEXT_VERSION") != "18":
    raise SystemExit("expected stage-dispatch snapshot v18")

prd_path = SPEC_ROOT / "prd.md"
state_path = SPEC_ROOT / "pipeline_state.yaml"
summary_path = SPEC_ROOT / "pipeline_summary.md"
prd = prd_path.read_text(encoding="utf-8")
state = state_path.read_text(encoding="utf-8")
summary = summary_path.read_text(encoding="utf-8")

marker = "## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)"
if prd.count(marker) != 1 or "## 13.11 v19 — transient PID namespace lifecycle" in prd:
    raise SystemExit("unexpected stage-dispatch PRD v18 shape")

section = """## 13.11 v19 — transient PID namespace lifecycle (2026-07-20)

> 근거: Codex depth-1 tool-call PID namespace에서 detached depth-2 worker가
> wrapper 반환과 동시에 2~4 JSONL event만 남기고 세 차례 사망했다. exit-77
> guard는 silent death를 차단했지만 checked Codex→Codex 및 Codex→Claude
> stage path를 완주시키지 못했다.

### 13.11.1 SD-72 — namespace-safe automatic lifecycle selection

- `dispatch-chain`은 실제 launcher scope에서 PID namespace를 판정한다.
  transient namespace이면 Codex/Claude child wrapper에
  `launch_lifecycle=foreground-scoped`를 자동 선택하고, wrapper call을 child
  terminal까지 유지한다. namespace 밖에서는 기존 `detached` launch를 보존한다.
- `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1`은 namespace가 tool-call보다 오래
  산다는 명시적 checked assertion이며 이 경우 detached를 유지한다.
- foreground-scoped wrapper는 child process group에 SIGINT/SIGTERM을 전달하고,
  bounded timeout이면 group을 TERM→KILL 순으로 종료한다. nonzero exit, signal,
  timeout은 exact attempt row 하나만 typed `dead-*`로 마감한다. exit 0은
  completion-marker harvest가 row를 마감하도록 open 상태를 보존한다.
- checked Codex `headless/workspace-write` parent 안의 foreground Codex child는
  unsupported nested mount setup을 피하려고 inner runtime sandbox만
  `danger-full-access`로 선택한다. outer workspace-write가 권한 경계로 유지되며
  wrapper output/attempt row에 effective runtime sandbox를 기록한다.
- standard+ Codex owner의 outer sandbox에는 기존 harness `.core-grounding`과
  Claude `session-env` scratch directory만 추가로 writable하게 투영한다. 따라서
  adapter write gate와 Codex→Claude Bash 초기화가 동작하되 두 runtime home의
  나머지 영역이나 depth-2 network 권한은 넓어지지 않는다.
- wrapper는 자신의 exact slug를 child 환경에 내보내고 `dispatch-chain`은 이를
  parent 기본값으로 사용한다. explicit parent 불일치는 등록 전에 거부한다.
  Fleet는 과거·malformed unmatched depth-2 row도 orphan으로 표시해 숨기지 않는다.
- wrapper machine output과 attempt row는 stable vocabulary
  `launch_lifecycle ∈ {detached,foreground-scoped}`를 기록한다. same-harness와
  cross-harness가 같은 selector를 소비하며 native subagent는 대체 경로가 아니다.
- registry attempt identity, heartbeat/watchdog, capacity failover,
  completion-marker binding, fallback order는 lifecycle 선택과 직교하며 불변이다.

**acceptance**: ① host/remounted-proc namespace fixture에서 lifecycle 판정이
결정론적이다 ② namespace 밖과 long-lived override는 detached를 유지한다
③ Codex/Claude wrapper foreground success가 child exit까지 반환하지 않고 output/row에
foreground-scoped를 기록한다 ④ timeout/signal/nonzero가 exact row만 typed closure한다
⑤ Codex depth-1→Codex depth-2 및 Codex depth-1→Claude depth-2 live attempt가 artifact,
typed handoff, exact marker, terminal row까지 완주한다 ⑥ parent mismatch가 등록 전
거부되고 unmatched depth-2 row가 Fleet orphan으로 표시된다 ⑦ 기존 dispatch/route/
liveness/Fleet/projection/boundary suite가 회귀 없이 통과한다.

"""
new_prd = prd.replace(marker, section + marker)

replacements = {
    "version: 18": "version: 19",
    "last_updated: 2026-07-19": "last_updated: 2026-07-20",
    "  spec: done              # PRD v18 — conductor 생존, Codex no-commit mutation, exact marker↔attempt 결합. v17 snapshot = _internal/versions/v17/":
        "  spec: done              # PRD v19 — namespace-safe foreground stage lifecycle, parent/Fleet visibility, Codex→Claude runtime scratch projection. v18 snapshot = _internal/versions/v18/",
    "  dev: in_progress        # v18 구현 사이클: Claude one-shot hardening/Stop probe, SD-64 orphan reconcile, Codex no-commit+spec-grounding, exact marker↔attempt close":
        "  dev: in_progress        # v19 구현 사이클: foreground-scoped Codex/Claude depth-2, exact parent/Fleet visibility, scoped nested runtime writes",
}
new_state = state
for old, new in replacements.items():
    if new_state.count(old) != 1:
        raise SystemExit(f"unexpected pipeline_state v18 shape: {old}")
    new_state = new_state.replace(old, new)

input_anchor = "  - '운영 실측 2026-07-16 (v15 minor #1): plans/2026-07-16_spec-gate-multi-spec — r1 conductor 배경 대기 턴 종료 사망(지침-단독 불충분 실증), dispatch-node eligibility 증거 미전달 fail-closed, r2 BLOCKED(source_commit 정확 일치 × execute 커밋 계약 모순)'\n"
new_input = (
    input_anchor
    + "  - '운영 실측 2026-07-20 (v19): plans/2026-07-20_namespace-safe-stage-dispatch — transient PID namespace에서 detached depth-2 3회 조기 사망; foreground-scoped Codex·Claude live PASS, Fleet unmatched-parent 누락과 Claude session-env EROFS 확인'\n"
)
if new_state.count(input_anchor) != 1:
    raise SystemExit("pipeline_state input anchor missing")
new_state = new_state.replace(input_anchor, new_input)

decision_anchor = "decisions_locked:\n"
decision = (
    decision_anchor
    + "  - 'SD-72(v19): transient PID namespace에서는 dispatch-chain이 Codex/Claude wrapper를 foreground-scoped로 유지하고 signal/timeout/exact-row closure를 감독한다. Codex inner mount sandbox는 checked outer workspace-write 안에서만 비활성화하며, owner는 .core-grounding·Claude session-env만 추가 writable projection한다. exact self-parent를 강제하고 Fleet는 unmatched depth-2를 orphan으로 표시한다'\n"
)
if new_state.count(decision_anchor) != 1:
    raise SystemExit("pipeline_state decision anchor missing")
new_state = new_state.replace(decision_anchor, decision)

summary_note = """
## v19 update (2026-07-20) — namespace-safe depth-2 + Fleet visibility

- transient tool-call PID namespace에서 detached child가 wrapper 반환 직후 죽던 원인을
  `foreground-scoped` lifecycle로 닫았다. Codex→Codex와 Codex→Claude 실제 depth-2
  worker가 artifact, exact completion marker, terminal row까지 완주했다.
- checked Codex outer `workspace-write` 안의 Codex child는 inner mount sandbox만
  비활성화하고, standard+ owner에는 `.core-grounding`과 Claude `session-env`만
  추가 writable root로 연다. depth-2 network나 runtime home 전체 권한은 넓히지 않는다.
- wrapper self slug를 parent identity의 기준으로 삼아 mismatch를 등록 전에 거부한다.
  Fleet renderer는 unmatched depth-2 row를 orphan으로 표시하여 live row를 숨기지 않는다.
- 구현 증거: `plans/2026-07-20_namespace-safe-stage-dispatch/_internal/plan_reviews/`
  Codex·Claude PASS, 집중 dispatch/Fleet 테스트 및 adaptation boundary PASS.
"""
if "## v19 update (2026-07-20)" in summary:
    raise SystemExit("pipeline_summary already contains v19")
new_summary = summary.rstrip() + "\n\n" + summary_note.lstrip()

snapshot_dir = SPEC_ROOT / "_internal" / "versions" / "v18"
if snapshot_dir.exists():
    raise SystemExit("stage-dispatch snapshot v18 already exists")

staged: list[tuple[Path, Path]] = []
for target, content in (
    (prd_path, new_prd),
    (state_path, new_state),
    (summary_path, new_summary),
):
    temp = target.with_name(f".{target.name}.v19.tmp")
    temp.write_text(content, encoding="utf-8")
    staged.append((temp, target))

snapshot_dir.mkdir(parents=True)
shutil.copy2(prd_path, snapshot_dir / "prd.md")
for temp, target in staged:
    os.replace(temp, target)
