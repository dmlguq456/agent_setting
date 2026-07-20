# Proposal-Gated Improvement Loop

This is the operational boundary between loop engineering and active harness
or plugin settings. It is a guide and inactive local state surface, not a
scheduled loop.

## Flow

```text
observed -> reproduced -> proposed -> reviewed
                                      -> adopted
                                      -> superseded-by-native
                                      -> rejected | deferred

adopted invariant -> runtime realization:
unverified -> active -> needs-revalidation
                         -> active | incompatible | superseded-by-native | retired
```

The first state machine decides whether the portable invariant is worth owning.
The second decides whether one exact runtime/plugin realization is currently
valid. An official update changes the second state, not the first decision.

## Automatic boundary

A loop may:

- record an incident and exact context fingerprint;
- create a minimal candidate fixture in the local inbox;
- run isolated baseline/candidate comparisons;
- draft a source-targeted proposal and rollback path;
- mark an active realization as needing revalidation when its fingerprint changes.

A loop may not:

- apply a candidate diff;
- edit core, adapters, generated output, installed plugins, or runtime config;
- install, enable, disable, update, or reload a plugin;
- mark review, adoption, activation, supersession, rejection, or retirement
  without a human approval reference;
- change its own approval or ownership guard and use the changed guard in the
  same cycle.

## Inbox

Use `tools/improvement/proposals.py`. The default store is:

```text
${XDG_STATE_HOME:-~/.local/state}/agent-harness/improvement
```

It is intentionally outside the repository, runtime homes, managed releases,
plugin caches, and runtime discovery. Candidate evidence becomes a tracked
fixture only after adoption through the normal spec/code cycle.

## On-call source

On-call may use recent memory mutations to discover possible incidents, but it
must read the full entry and corroborate the claim against current local
evidence before calling `observe`. Memory is a lead, never proposal evidence.
Named collectors use a stable `--incident-key`; an exact match appends bounded
recurrence evidence without changing the existing proposal state. A new key
creates `observed`. On-call may advance only through `reproduced` and
`proposed`, and must never supply a `human:*` actor or approval reference.
Reviewed and terminal records keep their state when recurrence evidence lands.
Recurrence does not rebase context by itself. A fresh, context-bound
`reproduced` transition may rebase only a proposal that has never crossed the
human-review boundary, so later human review evaluates the version that was
actually reproduced.

## Reconciliation

When runtime-watch detects an official change:

1. capture a fresh context including runtime/plugin/docs/active-provider fingerprints;
2. run proposal or realization `check`;
3. return stale proposals to reproduction or defer them;
4. run the fixture on the new native behavior;
5. retire a workaround when native behavior satisfies the portable invariant;
6. otherwise propose an adapter update and use the normal release/activation path;
7. escalate semantic conflicts instead of merging them automatically.

The tool records evidence and provenance only. Existing installer and managed
release code remains the sole activation owner.
