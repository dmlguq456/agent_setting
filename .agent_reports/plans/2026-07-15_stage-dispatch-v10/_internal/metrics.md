# Pipeline metrics

- intensity: strong
- requested graph: code-plan → code-execute → SD-45 risk review → code-test → code-report
- route: `_internal/route.json` (`rt-fda0402b695fb63c`)
- inline exception: `runtime-unavailable`
- evidence: initial runtime home was read-only; isolated runtime then started a Codex thread, but the headless response websocket/API failed with `Operation not permitted` under the workspace network sandbox.
- assurance fallback: inline plan/execute/test/report; separate native Codex SD-45 risk review completed and passed after two findings were fixed. It is never labeled headless.
