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
  --title "plugin/runtime conflict" \
  --summary "generated and installed content disagree" \
  --context context.json \
  --evidence incident.md

python3 tools/improvement/proposals.py transition <id> reproduced \
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

## Deliberate omissions

The CLI has no command for applying a patch, editing settings, installing or
enabling plugins, changing hooks, mutating generated output, committing, or
releasing. It is not connected to cron or runtime session hooks.

## Verification

```bash
bash tools/improvement/proposals.test.sh
```

The durable test replaces HOME and XDG roots with temporary directories and
fails if the real runtime config or harness-specific plugin state changes.
