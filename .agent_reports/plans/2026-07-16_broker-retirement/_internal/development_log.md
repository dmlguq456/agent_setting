# Development Log

- Replaced broker-bound route compilation with broker-free dispatch contract v3.
- Changed same/cross-harness hops to one-shot direct adapter wrapper invocation.
- Added lock-protected stable attempt claims; duplicate starts create no second row or child.
- Retained v1/v2 hash verification and Fleet reads while blocking legacy register/start.
- Retired broker ensure/request/serve; status/stop remain for one-release drain compatibility.
- Made Fleet prefer canonical registry rows and exact attempt/PID/start identity, folding terminal retries from the default current view.
- Replaced the fixed nested-Codex denial with current CLI/auth/network/worktree evidence.
- Live probing found that network access alone was insufficient because nested Codex needs writable runtime state. Added an owner-worktree `CODEX_HOME` projection that symlinks existing auth/config without copying or mutating credentials.
