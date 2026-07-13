# Test Adequacy Review

Status: PASS after independent read-only review and one correction round.

Independent findings and resolution:

1. Persisted cumulative-counter decrease was not surfaced by `kv`/`json`: fixed by recording the normal baseline and consulting session state in all formats.
2. Staleness followed file mtime rather than the event: fixed by preferring the token-count event timestamp and testing a fresh file containing an old event.
3. Prompt-hook lookup was unbounded: fixed with a one-second default, clamped override, process-group termination, and static contract assertion.
4. POSIX-only `fcntl` reduced utility portability: replaced with a bounded atomic directory lock; state failures remain fail-open.
5. Docs overstated the whole utility as read-only: narrowed to read-only `kv`/`json` and explicit XDG writes for `hook`.

No P0/P1 finding remains.

Covered risk axes:

- active context vs cumulative counter separation;
- Codex formula boundary 69/70/84/85;
- missing, malformed, stale, ambiguous exact-session lookup;
- three collector mappings and mirror parity via full Fleet suite;
- session-isolated transition state, same-band zero output, native/decreasing fail-open;
- <=240-byte one-line directive and required-work/safety/input wording;
- Codex preflight + UserPromptSubmit behavior;
- portable intensity/dispatch/safety invariant and adapter projection boundary;
- repository doctor and current installed-runtime mismatch separation.

Final evidence: 12 focused tests, 202 full Fleet tests, 343 portable guards, adaptation boundary, manifest, native projection checks, mirror parity, `git diff --check`, and repository doctor all pass.
