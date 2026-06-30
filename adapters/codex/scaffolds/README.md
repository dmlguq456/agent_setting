# Codex Scaffold Projection

This directory is the Codex-owned projection of reusable design scaffold HTML
assets. The asset bodies mirror `scaffolds/`, while adapter instructions and
tooling stay Codex-native.

Use these assets through `<agent-home>/scaffolds/` from Codex mode guides.
Rendered design verification is handled by:

```bash
adapters/codex/bin/preflight.sh visual-harness <file.html>
```

Do not project vendor-specific visual tooling files or runtime-home paths here.
