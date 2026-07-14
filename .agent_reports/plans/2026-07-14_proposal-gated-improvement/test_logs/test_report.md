# Test Report

## Target

Proposal-gated improvement spec, CLI, XDG store boundary, Claude collapsed
projection, and existing generated/runtime activation surfaces.

## Graduated verification

| Level | Command | Result |
|---|---|---|
| Syntax | `python3 -m py_compile tools/improvement/proposals.py tools/improvement/test_proposals.py` | PASS |
| Import | `python3 -c 'from tools.improvement import proposals; ...'` | PASS |
| Functional | `bash tools/improvement/proposals.test.sh` | PASS, 11 tests |
| Real-home isolation | durable test before/after runtime config and harness-plugin snapshot | PASS, byte-stable snapshot |
| Generated source | `python3 tools/generate.py --check` | PASS, 8 groups |
| Adaptation | `bash tools/check-adaptation-boundary.sh` | PASS, existing 50-reference warning only |
| Projection integration | `bash tools/generated-projections.test.sh` | PASS |
| Runtime activation | `bash tools/install/runtime-activation.test.sh` | PASS, 19 scenarios |
| Extension lifecycle | `bash tools/install/extension-lifecycle.test.sh` | PASS |
| Managed release | `bash tools/install/release-lifecycle.test.sh` | PASS |
| Diff hygiene | `git diff --check` | PASS |

All executable commands ran through the Codex `verification-runner` contract.

## Failure and correction

The first adaptation pass failed because the new portable `tools/improvement`
and `loops/improvement.md` had no adapter projection decision. Implementation
resumed and added:

- Claude collapsed tool symlinks plus concrete loop projection;
- explicit Codex/OpenCode `improvement` deferral in the projection completeness guard.

The entire verification sequence was then restarted and passed.

## Verdict

PASS — the proposal lifecycle is inactive, isolated from runtime/plugin state,
and compatible with current generation, activation, extension, and managed
release contracts.
