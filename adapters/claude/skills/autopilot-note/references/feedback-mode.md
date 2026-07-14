## Lightweight feedback mode (`--feedback` — bidirectional worklog-board review loop, PRD §16)

Through v48, the worklog-board review queue supported only a one-way _agent proposal → human approval_ flow. v49–v50 add a **human-to-agent feedback channel** that closes the loop; see worklog-board PRD §16. Feedback submitted from the app accumulates in the `<target>/_feedback/<id>.md` queue (written by the app as a filesystem sidecar, analogous to `_triage`, and scheduled for DB migration). This mode consumes that queue, processes each branch, and **surfaces the result back in the review queue for user approval**.

> **Invariant: every application passes through review approval; there is no automatic application.** User feedback expresses _intent_; review approval makes it _final_. This mode stops at regenerating proposals or preparing code changes. DB writes and merges belong to the approval or harvest step.

This is a lightweight, per-item path rather than the full Stage A–F pipeline. It defaults to light-tier, with verification rigor derived from `--intensity`, and should remain immediate and inexpensive. Trigger it immediately after app submission (PRD §16.5 Q1) or through short polling.

### Input

Read `status: pending` items under `<target>/_feedback/`. Frontmatter contains `kind` (`proposal` or `ui-code`), `screen`, `proposal_id` for proposals, and the user's feedback in the body. `listPendingFeedback()` in worklog-board `lib/feedback.ts` is the entry point.

### Routing (feedback branch plus Q4 risk split)

**A. Proposal feedback** (`kind: proposal` with `proposal_id`) — regenerate the corresponding `_triage/<proposal_id>.md` proposal after applying the feedback:

- Read the feedback and produce a **revised payload**, such as a corrected title, project reassignment, or adjusted note links.
- Call `reviseProposal({ proposalId, revisedPayload, feedbackId })` in worklog-board `scripts/process-feedback.ts`. Update only the `_triage` file and perform **zero DB writes**. Preserve the original proposal in `revised_from` for the overlay's original/revised toggle, and replace `payload` with the revision so the existing approval path consumes it unchanged.
- Keep the operation idempotent: reruns preserve the first original in `revised_from`. Surface a `수정됨` badge on the proposal row in the review hierarchy.
- Process immediately without an extra verification gate; this only regenerates staged data.

**B. UI-code feedback** (`kind: ui-code`, general screen feedback) — split into three risk levels (PRD §16.5 Q4):

- **Visual polish, low risk** — fix it on a worktree branch, have `Agent(디자인팀 verifier)` inspect the real screen in light, dark, and mobile modes, then create a **change-review** entry in the worklog-board `lib/change-review.ts` queue (`_change_review/<id>.md`, `risk: visual`) with the diff and screenshots. Approval marks it `approved-for-merge`; the agent harvest step performs the merge under PRD §16.5 Q2. Rejection marks the worktree for disposal.
- **Component structure, medium risk** — **do not modify automatically**. Create only a `_change_review` entry with `risk: structure` and a confirmation-required marker. Start `autopilot-code` only after user confirmation. The design-team render gate can catch visual regressions but cannot validate structural or data intent.
- **DB, enum, or API specification, high risk** — this conflicts with the zero-DB-write invariant from v45–v48 and **must go through the specification**. Do not touch code. Create a `_change_review` item with `risk: db` and confirmation required, and state in the report that it must escalate through an `autopilot-spec` update and then `autopilot-code`.

### After processing

Use the state transition in `lib/feedback.ts` to mark each processed `_feedback` item as `status: processed`. Reruns must not process it again. Both proposal regeneration in A and change-review creation in B are staged proposals; review approval remains the point of confirmation.

### Boundaries

- **Do not merge.** An `approved-for-merge` mark is only a signal. The Claude session at the merge-signal step harvests the actual worktree under §5.10 and PRD §16.5 Q2.
- **Perform zero DB writes.** A regenerates only `_triage` files; B writes code or queue files. New columns, enums, and migrations go through the specification.
- Invoke `scripts/process-feedback.ts`, `lib/feedback.ts`, and `lib/change-review.ts` from the worklog-board working directory. `_feedback`, `_triage`, and `_change_review` are siblings under the parent of `CARDS_DIR`.
