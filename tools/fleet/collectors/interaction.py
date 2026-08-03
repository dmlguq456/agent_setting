"""Neutral Fleet interaction-wait enrichment (read-only, fail open)."""

from .. import interaction


def enrich(sess, now=None):
    session_id = getattr(sess, "session_id", None)
    harness = getattr(sess, "harness", None)
    if not session_id or not harness:
        return
    record = interaction.pending_wait(
        session_id,
        harness,
        session_start=getattr(sess, "started_at", None),
        activity_since=getattr(sess, "_interaction_activity", None),
        now=now,
    )
    if not record:
        return
    candidate = {
        "kind": record["kind"],
        "source": record["source"],
        "waiting_since": record["waiting_since"],
    }
    existing = getattr(sess, "interaction_state", None)
    if (
        isinstance(existing, dict)
        and isinstance(existing.get("waiting_since"), (int, float))
        and existing["waiting_since"] > candidate["waiting_since"]
    ):
        return
    sess.interaction_state = candidate
