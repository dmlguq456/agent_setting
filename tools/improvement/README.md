# Improvement Proposal Inbox

`proposals.py` records incidents, evidence, approval references, and
version-bound runtime realization state. It is an offline evidence tool, not a
self-edit or activation tool.

Default state:

```text
${XDG_STATE_HOME:-~/.local/state}/agent-harness/improvement/
  proposals/<id>/record.json
  proposals/<id>/evidence/*
```

The store is rejected when it resolves inside the harness source, managed
release data, Claude/Codex/OpenCode runtime homes, or a symlinked store root.

## Context

Every incident starts from a strict JSON context:

```json
{
  "source_revision": "git:abc123",
  "source_dirty": false,
  "portable_fingerprint": "sha256:...",
  "runtimes": [
    {
      "name": "codex",
      "version": "0.144.3",
      "plugin": {
        "name": "agent-harness-codex",
        "version": "1.0.0",
        "fingerprint": "sha256:..."
      }
    }
  ],
  "docs_fingerprint": "sha256:...",
  "fixture_fingerprints": [],
  "active_providers": {
    "skill:autopilot-code": "native-symlink"
  }
}
```

## Commands

```bash
python3 tools/improvement/proposals.py observe \
  --actor loop:oncall \
  --incident-key runtime-projection:generated-installed-divergence \
  --title "plugin/runtime conflict" \
  --summary "generated and installed content disagree" \
  --context context.json \
  --evidence incident.md

python3 tools/improvement/proposals.py transition <id> reproduced \
  --actor loop:oncall \
  --context context.json \
  --evidence reproduction.md

python3 tools/improvement/proposals.py transition <id> reviewed \
  --context context.json \
  --evidence review.md \
  --actor human:owner \
  --approval-ref session:review-42

python3 tools/improvement/proposals.py check <id> --context current-context.json
python3 tools/improvement/proposals.py list
```

Approval references are provenance, not authentication. They make an explicit
human decision auditable; they do not give this tool permission to edit source
or activate a plugin. Actual adoption uses the normal spec/code/release cycle.

Named automated collectors such as `loop:oncall` must provide a semantic
`--incident-key`. Exact-key recurrence appends bounded evidence and increments
the occurrence count while preserving the existing proposal state, title,
summary, and base context. Different keys create different proposals; ambiguous
duplicate keys fail closed. Collector automation may stop at `proposed` only;
the CLI rejects any other collector target and will not let a collector resume
a proposal that has crossed the human-review boundary. Human review remains the
only path to reviewed or terminal states. Recurrence alone preserves the
original base fingerprint. A named collector must bind `reproduced` to a current
`--context`; that explicit reproduction is the only eligible pre-review step
that rebases the proposal for later freshness checks.

## Deliberate omissions

The CLI has no command for applying a patch, editing settings, installing or
enabling plugins, changing hooks, mutating generated output, committing, or
releasing. The on-call agent may invoke only the evidence-ingestion and bounded
pre-review transitions described above; no cron or runtime hook calls an apply
or activation path.

## Verification

```bash
bash tools/improvement/proposals.test.sh
```

The durable test replaces HOME and XDG roots with temporary directories and
fails if the real runtime config or harness-specific plugin state changes.
