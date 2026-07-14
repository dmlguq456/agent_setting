# Inline Code Review

## Scope

`tools/improvement/proposals.py`, its tests, on-call/core contracts, governance
specs, and the concrete Claude loop projection.

## Review

- Authority: no apply, activation, runtime, plugin, network, Git, or memory
  mutation command was added. Existing human gates still own reviewed and
  terminal states.
- Deduplication: semantic identity remains agent-owned; code compares exact keys
  only, under the mutation lock, and rejects ambiguous legacy duplicates.
- State safety: recurrence records a same-state event. Reviewed or terminal
  records cannot be reopened through observation.
- Freshness: incoming recurrence cannot silently replace the approved base.
  Explicit current-context reproduction is required before a pre-review rebase.
- Bounds: evidence/history growth is capped; recurrence stores the incoming
  fingerprint rather than duplicating the full context object.
- Projection: canonical and Claude loop files are byte-identical. No
  runtime-owned setting or installed plugin is part of the diff.

## Residual judgment boundary

The quality and stability of an incident key cannot be decided mechanically.
The on-call agent must inspect current evidence and use one semantic identity;
ambiguous stored identities stop automation for human inspection.

## Verdict

No blocking finding. This is an inline review only, not an independent reviewer
pass.
