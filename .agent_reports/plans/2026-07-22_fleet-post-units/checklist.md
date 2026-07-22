# Fleet post-unit migration checklist

- [x] Read governing core/capability/role contracts and run capability/route/preflight checks.
- [x] Audit `a132b328^..fec5350a`, Fleet consumers, wrappers, memory journal, tests, and official runtime surfaces.
- [x] Classify drift SPEC-SIGNIFICANT and land Fleet PRD v14 with v13 snapshot under spec transaction.
- [x] Record standard+ registered-headless failure/skips, checked native fallback, reduced parity, and assurance compensation.
- [x] Add optional unit transport to all three wrappers and Fleet jobs/process parsing.
- [x] Preserve route digest/composed/node-unit metadata in summary/JSON.
- [x] Add compact unit visibility without replacing contract/stage identity.
- [x] Preserve legacy worker_role and route/jobs compatibility, including v20 terminal correlation.
- [x] Correct memory `cwd` documentation drift.
- [x] Synchronize generated/mirrored Fleet projection.
- [x] Add focused regression fixtures.
- [x] Pass scoped focused/full Fleet, syntax/compile, mirror, wrapper, CLI, and boundary verification; record external portable-guard/runtime-profile residuals.
- [x] Close dev logs, test logs, pipeline summary, and PRD pipeline state.
- [x] Commit verified source on `codex/fleet-post-units` (`a4f7f040`) and fast-forward it into `main`.
