#!/usr/bin/env python3
"""Apply the locked stage-dispatch v22 transaction and repair v20/v21 snapshots."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


if os.environ.get("AGENT_SPEC_LOCK_HELD") != "1":
    raise SystemExit("spec lock is required")

spec_root = Path(os.environ["AGENT_SPEC_ROOT"]).resolve()
if spec_root.name != "stage-dispatch":
    raise SystemExit(f"unexpected spec root: {spec_root}")

prd_path = spec_root / "prd.md"
state_path = spec_root / "pipeline_state.yaml"
summary_path = spec_root / "pipeline_summary.md"
prd_v21 = prd_path.read_text(encoding="utf-8")
state_v21 = state_path.read_text(encoding="utf-8")
summary_v21 = summary_path.read_text(encoding="utf-8")

header_anchor = (
    "> · **v21 2026-07-22** (strong+ 2-way cross-harness replica-and-merge route 컴파일 — "
    "recipe `replication` 선언·compiler 확장·conductor verdict-merge, SD-76; "
    "2026-07-21 core 강화 9b4e81b2의 실행 배선 사후 spec-sync)\n"
    "> 컴포넌트:"
)
header_replacement = (
    "> · **v21 2026-07-22** (strong+ 2-way cross-harness replica-and-merge route 컴파일 — "
    "recipe `replication` 선언·compiler 확장·conductor verdict-merge, SD-76; "
    "2026-07-21 core 강화 9b4e81b2의 실행 배선 사후 spec-sync)\n"
    "> · **v22 2026-07-23** (parent-bound teardown — exact parent attempt 봉인·owner 사망 시 "
    "직접 자식 bounded cascade reconcile·Codex/Claude wrapper parity, SD-77)\n"
    "> 컴포넌트:"
)
if prd_v21.count(header_anchor) != 1:
    raise SystemExit("v21 header anchor mismatch")

decision = r'''
## 13.13 v22 — parent-bound teardown와 orphan-free convergence (2026-07-23)

> 근거: `plans/2026-07-22_codex-headless-context-parity` 실측에서 depth-1 owner
> 로그가 `turn.completed` 없이 plan-refine foreground 대기 중 끊겼고, SD-64/71
> watcher는 계약대로 owner만 `dead-parent-orphaned`로 닫아 depth-2 row가 수동
> exact-process audit 전까지 open으로 남았다. 2026-07-23 사용자 지시: orphan이
> 생기지 않도록 대책을 구현하고 Codex/Claude Code parity를 함께 검증한다.
> 공식 런타임 경계는 Codex native subagent thread 및 Claude subagent/background
> session과 별도인 `codex exec`/`claude -p` registered process surface다. 따라서
> parent-death ownership은 portable harness가 동일하게 제공한다.

### 13.13.1 SD-77 — exact parent binding과 bounded child cascade

- 신규 dispatch-depth-2 attempt는 claim 전에 같은 repo/worktree의 open
  dispatch-depth-1 owner를 정확히 하나 해석하고 `parent_attempt_id`와 parent
  PID/start identity를 봉인한다. parent 부재·사망·모호성은 child row/spawn 0으로
  실패한다. slug만 같은 과거 owner retry에 결합하지 않는다.
- child spawn은 namespace-visible PID/start와 `/proc`가 제공하는 outer-namespace
  PID/start를 attempt row에 기록한다. 새 row의 direct-parent binding과 process-group
  identity는 immutable parent axes + mutable launch evidence로 분리한다.
- owner post-exit watcher는 기존 orphan 분류를 재검증한 뒤 exact completion marker와
  typed terminal handoff를 먼저 보존하고, owner를 `dead-parent-orphaned`로 닫은 다음
  그 `parent_attempt_id`에 봉인된 open direct child만 한 번 cascade reconcile한다.
  host-visible live group은 PID/start 및 `pgid == pid`를 다시 확인한 뒤
  SIGTERM → bounded grace → 필요 시 SIGKILL로 회수하고 row를
  `dead-parent-terminated`로 닫는다. 이미 사라진 process나 parent namespace와 함께
  소실된 row는 별도 typed note로 닫는다.
- PID reuse, identity 누락, group-leader 불일치, route tuple 충돌, legacy live row는
  신호를 보내지 않고 fail-closed로 남겨 Fleet/depth-0가 볼 수 있게 한다. marker나
  terminal evidence가 signal/close와 경합하면 terminal evidence가 우선한다.
- watcher는 replacement conductor, retry, successor launch, completion marker 생성,
  route advance를 수행하지 않는다. resume boundary와 재개 여부는 계속 depth-0
  의미 판단이다. unrelated/sibling attempt는 byte-identical이고 재실행은 idempotent다.
- Codex와 Claude registered-headless wrapper는 같은 shared parent-binding/cascade
  primitive와 closed note vocabulary를 사용한다. native subagent, Claude agent teams,
  `claude agents` supervisor/background session은 이 계약의 parity 증거가 아니다.

**acceptance**: ① owner 사망+live direct child fixture가 bounded 시간 내 owner/child
terminal·실제 child process 0으로 수렴 ② parent retry/route conflict/PID reuse/non-group-
leader/missing identity는 signal 0·무관 row mutation 0 ③ marker/FAIL/BLOCKED terminal
race는 기존 exact terminal 결과 우선 ④ namespace-local row는 outer identity가 있을
때만 signal하고 legacy unverifiable row는 계속 visible ⑤ Codex·Claude wrapper가
`parent_attempt_id`와 outer PID evidence를 동형 기록 ⑥ 기존 lifecycle/registry/
liveness/wait/harvest/Fleet/adaptation suite 회귀 0 ⑦ 실제 두 CLI의 terminal envelope는
각 공식 headless 표면으로 확인하되 runtime-native registry 지원으로 과장하지 않는다.

'''
if "## 13.13 v22" in prd_v21 or prd_v21.count("## 14. 의미↔규칙 경계 체크") != 1:
    raise SystemExit("v22 decision anchor mismatch")

prd_v22 = prd_v21.replace(header_anchor, header_replacement)
prd_v22 = prd_v22.replace("## 14. 의미↔규칙 경계 체크", decision + "## 14. 의미↔규칙 경계 체크")
rule_anchor = (
    "- **v20 추가**: quick `registered-headless` 단일 surface allowlist, namespace별 closed vocabulary, exact compile/runtime failure enum, one-node/at-most-one-live-attempt cardinality, qualified dispatch-depth fields, node topology↔attempt surface 분리, four-surface terminology, legacy read-only migration은 전부 compiler/schema/conformance fixture로 강제한다. SD-19 quick fallback과 bare current terminology는 superseded다. direct/standard+ 보존과 multi-capability composition 비추가는 회귀 fixture 대상이다.\n"
)
rule_v22 = (
    rule_anchor
    + "- **v22 추가**: exact parent-attempt binding, parent live preclaim, outer PID/start + process-group revalidation, terminal-evidence precedence, bounded direct-child cascade, typed closure와 idempotence는 결정론 fixture 대상이다. 실제 route를 재개할지와 unverifiable legacy row를 사람이 종료할지는 depth-0 의미 판단으로 남는다.\n"
)
if prd_v22.count(rule_anchor) != 1:
    raise SystemExit("rules anchor mismatch")
prd_v22 = prd_v22.replace(rule_anchor, rule_v22)

if state_v21.count("version: 20") != 1 or state_v21.count("last_updated: 2026-07-20") != 1:
    raise SystemExit("pipeline state version anchor mismatch")
state_v22 = state_v21.replace("version: 20", "version: 22")
state_v22 = state_v22.replace("last_updated: 2026-07-20", "last_updated: 2026-07-23")
state_v22 = state_v22.replace(
    "  spec: done              # PRD v20 — quick registered-headless-only, qualified dispatch-depth namespace, four execution surfaces. previous v19 snapshot = _internal/versions/v19/",
    "  spec: done              # PRD v22 — parent-bound child teardown + prior v21 strong replica wiring. snapshots repaired through _internal/versions/v21/",
)
locked_anchor = "decisions_locked:\n"
if state_v22.count(locked_anchor) != 1:
    raise SystemExit("decisions_locked anchor mismatch")
state_v22 = state_v22.replace(
    locked_anchor,
    locked_anchor
    + "  - 'SD-77(v22): depth-2 claim은 one live exact parent_attempt_id에 봉인. owner death watcher는 terminal evidence를 우선한 뒤 exact direct child만 PID/start/PGID 재검증하여 bounded TERM→KILL cascade; unverifiable legacy는 signal 없이 visible, 자동 재개/재분사 없음; Codex/Claude wrapper 동형'\n",
)

summary_addition = r'''

## v22 update (2026-07-23) — exact parent binding + bounded orphan cascade

- `codex-headless-context-parity` 실측에서 owner가 `turn.completed` 없이 끊긴 뒤
  detection-only SD-64/71이 child row를 의도적으로 남긴 원인을 계약 갭으로 확정했다.
- SD-77은 신규 depth-2 attempt를 exact live `parent_attempt_id`에 봉인하고, owner
  post-exit watcher가 marker/typed terminal을 우선한 뒤 direct child process group과
  row를 bounded cascade로 회수하도록 확정한다. PID reuse·route conflict·legacy
  unverifiable row는 신호 없이 fail-closed다.
- Codex native subagent/Claude subagent·agent-view와 registered `codex exec`/`claude -p`
  process를 분리했다. portable parent-death contract는 두 wrapper에 동형 적용한다.
- v21 update가 PRD만 고치고 v20 snapshot/pipeline state를 누락한 drift를 함께 수리:
  git의 v20 본문과 transaction 직전 v21 본문을 각각 `_internal/versions/v20|v21/`
  아래 보존하고 current state를 v22로 전진시켰다.
'''
if "## v22 update" in summary_v21:
    raise SystemExit("pipeline summary already contains v22")
summary_v22 = summary_v21.rstrip() + summary_addition + "\n"

v20 = subprocess.run(
    ["git", "show", "a09cba9d^:.agent_reports/spec/stage-dispatch/prd.md"],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout
versions = spec_root / "_internal" / "versions"
snapshots = {versions / "v20" / "prd.md": v20, versions / "v21" / "prd.md": prd_v21}
for path, expected in snapshots.items():
    if path.exists() and path.read_text(encoding="utf-8") != expected:
        raise SystemExit(f"snapshot conflict: {path}")

for path in snapshots:
    path.parent.mkdir(parents=True, exist_ok=True)
for path, content in snapshots.items():
    path.write_text(content, encoding="utf-8")
prd_path.write_text(prd_v22, encoding="utf-8")
state_path.write_text(state_v22, encoding="utf-8")
summary_path.write_text(summary_v22, encoding="utf-8")
