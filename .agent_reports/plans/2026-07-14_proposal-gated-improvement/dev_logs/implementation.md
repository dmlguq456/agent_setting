# Implementation Log

## Source

- Added `tools/improvement/proposals.py` as an offline XDG-state lifecycle.
- Added strict context validation and canonical SHA-256 freshness checks.
- Added separate portable proposal and runtime realization state machines.
- Added explicit human actor plus approval-reference gates for review, terminal
  decisions, and active/retired realization states.
- Added bounded opaque evidence copies, no-symlink files, atomic writes, and an
  exclusive mutation lock.
- Rejected stores under the repo, managed release data, or Claude/Codex/OpenCode
  runtime homes.

## Contract

- Added the core source-category and proposal-gated adaptation rule.
- Added the trust-root and version-bound realization design principle.
- Narrowed D-25 so reversible maintenance does not authorize harness policy edits.
- Added an operational loop guide and tool README.

## Activation boundary

No hook, cron, runtime CLI, plugin manager, runtime config, generated adapter,
installer activation, commit automation, or release path was added to the tool.

## Adapter projection decision

The first adaptation check correctly rejected an unclassified portable tool.
Claude receives collapsed symlinks for the runtime-neutral files and its
concrete loop projection. Codex and OpenCode explicitly defer native tool
projection in v1; the tool remains available from the harness source/release
but is not runtime-discovered or activated.
