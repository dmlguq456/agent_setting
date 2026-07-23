#!/usr/bin/env python3
"""Apply stage-dispatch v23 implementation-closure transaction."""

from __future__ import annotations

import os
from pathlib import Path


if os.environ.get("AGENT_SPEC_LOCK_HELD") != "1":
    raise SystemExit("spec lock is required")

spec_root = Path(os.environ["AGENT_SPEC_ROOT"]).resolve()
if spec_root.name != "stage-dispatch":
    raise SystemExit(f"unexpected spec root: {spec_root}")

prd_path = spec_root / "prd.md"
state_path = spec_root / "pipeline_state.yaml"
summary_path = spec_root / "pipeline_summary.md"
prd_v22 = prd_path.read_text(encoding="utf-8")
state_v22 = state_path.read_text(encoding="utf-8")
summary_v22 = summary_path.read_text(encoding="utf-8")

header = (
    "> · **v22 2026-07-23** (parent-bound teardown — exact parent attempt 봉인·owner 사망 시 "
    "직접 자식 bounded cascade reconcile·Codex/Claude wrapper parity, SD-77)\n"
    "> 컴포넌트:"
)
header_v23 = (
    "> · **v22 2026-07-23** (parent-bound teardown — exact parent attempt 봉인·owner 사망 시 "
    "직접 자식 bounded cascade reconcile·Codex/Claude wrapper parity, SD-77)\n"
    "> · **v23 2026-07-23** (SD-77 implementation closure — parent-check/spawn/PID publish 원자화·"
    "PID reuse no-signal exact closure·Claude result liveness/harvest parity)\n"
    "> 컴포넌트:"
)
if prd_v22.count(header) != 1:
    raise SystemExit("v22 header anchor mismatch")
prd_v23 = prd_v22.replace(header, header_v23)

spawn_anchor = (
    "- child spawn은 namespace-visible PID/start와 `/proc`가 제공하는 outer-namespace\n"
    "  PID/start를 attempt row에 기록한다. 새 row의 direct-parent binding과 process-group\n"
    "  identity는 immutable parent axes + mutable launch evidence로 분리한다.\n"
)
spawn_v23 = spawn_anchor + (
    "- claim 뒤 실제 launch 직전 parent identity를 다시 확인하고, child spawn과\n"
    "  PID/start/PGID publish를 같은 jobs lock 안에서 끝낸다. 따라서 watcher가 보는\n"
    "  exact-bound row는 process 0 또는 완전한 group identity 중 하나이며, PID가 없는\n"
    "  registered/claimed row는 spawn 0으로 증명되어 `dead-parent-exited`로 닫힌다.\n"
)
if prd_v23.count(spawn_anchor) != 1:
    raise SystemExit("spawn anchor mismatch")
prd_v23 = prd_v23.replace(spawn_anchor, spawn_v23)

unsafe_anchor = (
    "- PID reuse, identity 누락, group-leader 불일치, route tuple 충돌, legacy live row는\n"
    "  신호를 보내지 않고 fail-closed로 남겨 Fleet/depth-0가 볼 수 있게 한다. marker나\n"
    "  terminal evidence가 signal/close와 경합하면 terminal evidence가 우선한다.\n"
)
unsafe_v23 = (
    "- PID reuse는 절대 신호하지 않는다. start mismatch는 기록된 exact process의 종료를\n"
    "  증명하므로 unrelated replacement를 건드리지 않고 그 child row만\n"
    "  `dead-parent-exited`로 닫는다. live/unverifiable process의 identity 누락,\n"
    "  group-leader 불일치, route tuple 충돌, outer identity 없는 namespace-local row,\n"
    "  legacy live row는 signal/close 없이 Fleet/depth-0에 남긴다. marker나 terminal\n"
    "  evidence가 signal/close와 경합하면 terminal evidence가 우선한다.\n"
)
if prd_v23.count(unsafe_anchor) != 1:
    raise SystemExit("unsafe identity anchor mismatch")
prd_v23 = prd_v23.replace(unsafe_anchor, unsafe_v23)

runtime_anchor = (
    "- Codex와 Claude registered-headless wrapper는 같은 shared parent-binding/cascade\n"
    "  primitive와 closed note vocabulary를 사용한다. native subagent, Claude agent teams,\n"
    "  `claude agents` supervisor/background session은 이 계약의 parity 증거가 아니다.\n"
)
runtime_v23 = (
    "- Codex와 Claude registered-headless wrapper는 같은 shared parent-binding/cascade\n"
    "  primitive와 closed note vocabulary를 사용한다. Codex는 final agent message 뒤\n"
    "  `turn.completed`, Claude는 `claude -p --output-format stream-json --verbose\n"
    "  --no-session-persistence`의 final `result`를 같은 3-line handoff로 해석하며\n"
    "  liveness와 harvest도 두 source를 모두 보존한다. native subagent, Claude agent\n"
    "  teams, `claude agents` supervisor/background session은 parity 증거가 아니다.\n"
)
if prd_v23.count(runtime_anchor) != 1:
    raise SystemExit("runtime parity anchor mismatch")
prd_v23 = prd_v23.replace(runtime_anchor, runtime_v23)

acceptance_anchor = (
    "terminal·실제 child process 0으로 수렴 ② parent retry/route conflict/PID reuse/non-group-\n"
    "leader/missing identity는 signal 0·무관 row mutation 0 ③ marker/FAIL/BLOCKED terminal\n"
    "race는 기존 exact terminal 결과 우선 ④ namespace-local row는 outer identity가 있을\n"
    "때만 signal하고 legacy unverifiable row는 계속 visible ⑤ Codex·Claude wrapper가\n"
    "`parent_attempt_id`와 outer PID evidence를 동형 기록 ⑥ 기존 lifecycle/registry/\n"
    "liveness/wait/harvest/Fleet/adaptation suite 회귀 0 ⑦ 실제 두 CLI의 terminal envelope는\n"
    "각 공식 headless 표면으로 확인하되 runtime-native registry 지원으로 과장하지 않는다.\n"
)
acceptance_v23 = (
    "terminal·실제 child process 0으로 수렴 ② parent retry/route conflict/non-group-leader/\n"
    "missing identity는 signal 0·무관 row mutation 0, PID reuse는 signal 0 + exact row만\n"
    "`dead-parent-exited` ③ marker/FAIL/BLOCKED terminal race는 기존 exact terminal 결과\n"
    "우선 ④ namespace-local row는 outer identity가 있을 때만 signal하고 legacy\n"
    "unverifiable row는 계속 visible ⑤ Codex·Claude wrapper가 `parent_attempt_id`와 outer\n"
    "PID evidence를 동형 기록 ⑥ claim 후 parent death race는 spawn 0 또는 PID가 게시된\n"
    "reapable group으로만 수렴 ⑦ lifecycle/registry/liveness/wait/harvest/Fleet/adaptation\n"
    "suite 회귀 0 ⑧ 실제 두 CLI의 stdin terminal envelope를 공식 headless 표면으로\n"
    "확인하되 runtime-native registry 지원으로 과장하지 않는다.\n"
)
if prd_v23.count(acceptance_anchor) != 1:
    raise SystemExit("acceptance anchor mismatch")
prd_v23 = prd_v23.replace(acceptance_anchor, acceptance_v23)

closure = r'''
### 13.13.2 v23 implementation closure

- Shared `spawn_claimed_attempt`가 final parent recheck와 spawn identity publish를 같은
  registry lock 아래 수행한다. wrapper crash/parent-death 경계의 PID-less exact row는
  process 0으로만 해석한다.
- owner close와 child cascade 사이 crash는 terminal owner를 다시 받은 watcher가
  idempotent cascade를 재실행해 복구한다. 같은 slug replacement와 sibling attempt는
  byte-identical이다.
- 실제 로컬 Claude Code 2.1.218과 Codex CLI 0.145.0 stdin probe에서 각각 final
  `result`와 `turn.completed`가 같은 PASS handoff로 정규화되었다. 이는 registered
  process envelope parity이며 runtime-native agent lifecycle parity 주장이 아니다.

'''
section14 = "## 14. 의미↔규칙 경계 체크"
if prd_v23.count(section14) != 1 or "### 13.13.2 v23" in prd_v22:
    raise SystemExit("v23 closure anchor mismatch")
prd_v23 = prd_v23.replace(section14, closure + section14)

rule_anchor = (
    "- **v22 추가**: exact parent-attempt binding, parent live preclaim, outer PID/start + "
    "process-group revalidation, terminal-evidence precedence, bounded direct-child cascade, "
    "typed closure와 idempotence는 결정론 fixture 대상이다. 실제 route를 재개할지와 "
    "unverifiable legacy row를 사람이 종료할지는 depth-0 의미 판단으로 남는다.\n"
)
rule_v23 = rule_anchor + (
    "- **v23 정련**: final parent recheck + spawn + PID/start/PGID publish 원자성, PID-less "
    "exact row의 spawn-0 해석, PID reuse no-signal exact-row closure, Codex/Claude terminal "
    "source의 liveness/harvest 동형성은 결정론 fixture 대상이다.\n"
)
if prd_v23.count(rule_anchor) != 1:
    raise SystemExit("v23 rules anchor mismatch")
prd_v23 = prd_v23.replace(rule_anchor, rule_v23)

if state_v22.count("version: 22") != 1:
    raise SystemExit("pipeline version anchor mismatch")
state_v23 = state_v22.replace("version: 22", "version: 23")
state_v23 = state_v23.replace(
    "  spec: done              # PRD v22 — parent-bound child teardown + prior v21 strong replica wiring. snapshots repaired through _internal/versions/v21/",
    "  spec: done              # PRD v23 — SD-77 implementation closure; v22 snapshot = _internal/versions/v22/",
)
state_v23 = state_v23.replace(
    "  dev: pending            # v20 source implementation은 별도 autopilot-code cycle 소관",
    "  dev: in_progress        # SD-77 parent-bound teardown + Codex/Claude terminal parity realized; unrelated open decisions remain",
)
decision_v22 = (
    "  - 'SD-77(v22): depth-2 claim은 one live exact parent_attempt_id에 봉인. owner death watcher는 terminal evidence를 우선한 뒤 exact direct child만 PID/start/PGID 재검증하여 bounded TERM→KILL cascade; unverifiable legacy는 signal 없이 visible, 자동 재개/재분사 없음; Codex/Claude wrapper 동형'\n"
)
decision_v23 = (
    "  - 'SD-77(v23): final parent recheck+spawn+PID publish는 jobs lock 아래 원자적. PID 없는 exact-bound row는 spawn 0이라 dead-parent-exited; PID reuse는 signal 없이 exact row만 종료. Codex turn.completed와 Claude stream-json result는 liveness/harvest까지 동형'\n"
)
if state_v23.count(decision_v22) != 1:
    raise SystemExit("SD-77 state anchor mismatch")
state_v23 = state_v23.replace(decision_v22, decision_v23)

summary_addition = r'''

## v23 update (2026-07-23) — SD-77 implementation closure

- final parent recheck, process spawn, PID/start/PGID publication을 canonical jobs lock
  아래 원자화해 claim/spawn 경쟁 구간을 닫았다. PID 없는 exact-bound row는 process 0으로
  닫고, live exact group만 재검증 후 bounded TERM/KILL한다.
- PID reuse는 unrelated process에 signal 0을 보장하면서 기록된 exact child row만
  `dead-parent-exited`로 수렴한다. route conflict, non-group leader, outer identity 없는
  namespace-local/legacy live row는 계속 visible fail-closed다.
- Claude Code 2.1.218 `result`와 Codex CLI 0.145.0 `turn.completed` stdin probe를 동일
  handoff로 검증했고, liveness와 Codex-side cross-harness harvest의 Claude 우회를 제거했다.
'''
if "## v23 update" in summary_v22:
    raise SystemExit("pipeline summary already contains v23")
summary_v23 = summary_v22.rstrip() + summary_addition.rstrip() + "\n"

snapshot = spec_root / "_internal" / "versions" / "v22" / "prd.md"
if snapshot.exists() and snapshot.read_text(encoding="utf-8") != prd_v22:
    raise SystemExit(f"snapshot conflict: {snapshot}")
snapshot.parent.mkdir(parents=True, exist_ok=True)
snapshot.write_text(prd_v22, encoding="utf-8")
prd_path.write_text(prd_v23, encoding="utf-8")
state_path.write_text(state_v23, encoding="utf-8")
summary_path.write_text(summary_v23, encoding="utf-8")
