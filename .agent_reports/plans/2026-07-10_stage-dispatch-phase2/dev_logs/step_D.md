# dev_log — Phase D (SD-12 stage-worker profiles)

- Created 4 fragments `profiles/fragments/code-{plan,execute,test,report}.md` — each a ≤~30-line L2 fragment (specialization / in-session team / input+output write class per OPERATIONS §5.10 ④ / file-only handoff / stay-in-lane no-redispatch). Modeled on `fragments/lab-runner.md`.
- Created 4 declarations `profiles/code-{plan,execute,test,report}.yaml` — `model_role` only (portable; effort supplied by wrapper role map): plan=`deep maker`, execute=`fast implementer`, test=`fast reviewer`, report=`fast writer`. expose = minimal skills + the one team (plan-team/dev-team/qa-team) + `analyze-project` for report.
- Registered 4 rows in `profiles/README.md` catalog.
- **Verify**: `AGENT_HOME=$PWD build-home.py code-<stage> --check` → `check=ok` ×4. Instance build sanity (code-execute, code-report) links all exposed skills/agents with **no projection-target-missing**.
- D4 wiring: the conductor's dispatch line passes `--profile code-<stage>`; wrapper already appends `profile=` to jobs.log (no code change to record). Instrumentation format = Phase J.

Note: model_role is the profile default; the conductor's `--model-role` on the dispatch line still governs per-dispatch (SD-5). Documented in each fragment's stay-in-lane subsection.
