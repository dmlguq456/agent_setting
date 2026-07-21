# Completion Report Card Policy — Quick Owner Summary

## Outcome

- Verdict: PASS
- Spec significance: within-spec because this edits the harness core response contract and does not change a project PRD.
- Governing PRD: `spec/skill-design-refactor/prd.md`; the change refines its locked SD-28 boundary that main owns user-facing explanation while workers return only the three-line handoff.
- Capability / mode: `autopilot-code` / `dev/refactor`
- Intensity / QA: `quick` / `quick` code track
- Route: `rt-06c3ac07fa7b6382`, node `one-shot`, attempt `att-cc78c4eb6b5248d9a09b47c195c6d347`
- Starting and final source HEAD: `bf5d15cd` (unchanged; no commit or push)

The portable workflow now defines a canonical post-execution completion-report
card with audience-language labels and the ordered Korean fields `작업`, `결과`,
`검증`, `산출물`, and `남은 사항`. It requires one line per value, an honest
completed/partial/failed/blocked status, and `없음` (or its audience-language
equivalent) when no artifact or remaining item exists. The main agent may emit
the card for dispatched or long-running work only after synchronous wait/poll,
harvest, authorized integration, and final verification. A worker handoff alone
is explicitly insufficient. Read-only orientation, simple factual answers, and
status-only replies remain exempt.

## Quick Micro-Plan and Plan-Check-Lite

1. Confirm the canonical owner, exemptions, lifecycle gate, and testable field order.
2. Patch the core workflow policy and make the response policy delegate material-work closure to it.
3. Add a narrow deterministic regression guard and run applicable conformance checks.
4. Record evidence and runtime limitations in this canonical owner artifact.

Plan-check-lite:

1. Canonical owner? `core/WORKFLOW.md`, which already owns the five-field entry card and main/worker flow.
2. Minimal projection impact? `roles/response-policy.md` points to the core card; adapter projections remain unchanged unless conformance fails.
3. Lifecycle ambiguity? The gate names synchronous wait/poll, harvest, authorized integration, and verification, and rejects worker handoff as completion.
4. Exemptions preserved? Yes: read-only orientation, simple factual answers, and status-only replies use concise prose.

## Changed Paths

- `core/WORKFLOW.md` — added §0.5 with the canonical card, status semantics, empty-value convention, lifecycle gate, and exemptions.
- `roles/response-policy.md` — delegated the concise material-work close to §0.5, added the verified-completion clause, and removed the contradictory one-line follow-up close.
- `tools/generated-projections.test.sh` — added deterministic checks for the section, field order, worker-handoff boundary, response-policy delegation, and absence of the conflicting one-line rule.

No adapter projection was changed. The adaptation and Skill conformance checks
passed without requiring a generated or duplicated runtime-surface update.

## Verification Evidence

- `preflight.sh qa-policy quick code` — selected `plan-check:selected-independent-pass:final-verify`; the independent-delegation fallback is inline review because no separate reviewer ran.
- Focused `rg` searches across `core/`, `roles/`, capability contracts, adapter bootstraps, and conformance tooling — confirmed the canonical owners and found the prior `auto-proceed and report in one line` contradiction, which was removed.
- `git diff --check` — PASS.
- `sh -n tools/generated-projections.test.sh` — PASS.
- `preflight.sh verification-runner --timeout 180 -- env -u AGENT_ARTIFACT_ROOT tools/generated-projections.test.sh` — PASS (`generated-projections: PASS`; 29 embedded figure-semantic tests also passed).
- `preflight.sh verification-runner --timeout 300 -- tools/check-adaptation-boundary.sh` — PASS; emitted the existing allowed warning about 110 concrete Claude/model references in portable areas.
- `preflight.sh verification-runner --timeout 120 -- python3 tools/build-manifest.py --check` — PASS (`manifest up-to-date; delta baselines bound`).
- `preflight.sh verification-runner --timeout 180 -- tools/skill-conformance/check.sh` — PASS for the portable domain, all four Skill trees, owner links, routing boundaries, and audience-language neutrality.
- Final semantic search confirmed all five fields, four outcome states, `없음`, wait/poll, harvest, authorized integration, final verification, worker-handoff rejection, exemptions, and response-policy delegation.
- Final source state contains only the three intended modified paths; `HEAD` remained `bf5d15cd`.

The first generated-projections invocation failed because this worker's injected
`AGENT_ARTIFACT_ROOT` overrode the test's legacy-root fixture. The same test was
rerun with only that inherited override unset and passed; no source change was
made to mask the environment-specific failure.

## Guards, Warnings, and Remaining Risks

- The required core documents, response policy, capability contract, Codex mode contracts, and governing PRD were read. `preflight.sh read` marker writes for core files were attempted but the worker sandbox denied `/home/Uihyeop/agent_setting/.core-grounding` as read-only; the governing PRD marker under the writable spec-grounding surface succeeded. Pre-edit `preflight.sh write ... codex-headless` checks succeeded for every edited file.
- Every required `stage-heartbeat` emission was attempted, but the sandbox denied `/home/Uihyeop/agent_setting/.dispatch/watchdog/att-cc78c4eb6b5248d9a09b47c195c6d347.lock` as read-only. This is an unsupported registry-progress surface in the assigned sandbox, not a source-verification failure.
- The task branch is three commits behind `origin/main`; upstream moved during the run. `HEAD` did not move and there was no merge/rebase/cherry-pick state. Main should account for upstream drift before integration.
- No commit, push, merge, cleanup, memory lifecycle, or adapter projection was performed, as assigned.
