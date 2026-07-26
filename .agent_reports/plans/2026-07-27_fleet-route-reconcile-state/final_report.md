# Final report

Fleet no longer presents the exact completion-marker reconciliation window as a route failure.
The node stays incomplete and visible as yellow `…`/`…gate`, then becomes done only when the
valid marker appears. Unrelated stale/dead/killed evidence remains red `✕`.

Source commit: `8615482f`; main lineage merge: `fc932666`.

The isolated worktree passed the guarded cleanup check and was removed. The branch remains as
the configured rollback point.
