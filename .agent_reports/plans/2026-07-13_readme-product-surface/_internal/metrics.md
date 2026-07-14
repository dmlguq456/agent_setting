# Pipeline metrics and dispatch notes

- intensity: strong
- topology: depth-1 capability owner; depth-2 stage dispatch attempted
- separability: stage outputs are separable by ownership, while the retirement source edits are semantically boundary-coupled and remain a single code-execute mutation set.
- dispatch attempt: `2026-07-13_readme-product-surface-code-plan`
- result: registered, then Codex headless exited before a stage session started with `failed to initialize in-process app-server client: Read-only file system`.
- fallback: adapter-declared `manual-main-session`; stages remain sequential and preserve class-scoped write ownership.
- independent QA claim: none. Code-test used the explicit inline fallback.
- patch fallback: the Codex `apply_patch` target detector could not resolve qualified targets; explicit preflight plus shell `apply_patch` preserved the write gate.
