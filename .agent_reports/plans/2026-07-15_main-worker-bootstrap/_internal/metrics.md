# Metrics and topology decision

- Selected graph: strong, inline code-plan/code-execute/code-test/code-report.
- Dispatch exception: this change modifies dispatch bootstraps and automatic
  model lifecycle itself. Launching workers through the surface under repair
  would exercise the precise recursive-cost risk being removed. The existing
  jobs registry also contains stale/open rows. Per OPERATIONS §5.10 SD-17,
  `STAGE_DISPATCH_INLINE_OK` is justified for this boundary-coupled edit.
- User explicitly prohibited neither registered dispatch nor native subagents,
  but repository policy for this session forbids spawning subagents unless
  explicitly requested. No subagents are used.
- Model calls during implementation/verification: 0 actual.
- Runtime surfaces audited: Claude hooks/settings/dispatch, Codex native hooks
  and preflight/dispatch, OpenCode plugin/preflight/dispatch, Fleet title
  refresher, loop and drill runners, all distill workers.
- External scheduled surface audited: worklog-board cron/note/hub/feedback Claude
  launchers; committed and pushed as `72e96dd`.
- Verification topology: focused deterministic suites only after the unclean
  00:45 server reboot; the interrupted full portable suite was not restarted.
