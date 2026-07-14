# Execution metrics

- intensity: standard
- execution: inline
- headless/native delegation: intentionally not used
- separability judgment: Code, tests, specs, and runtime projection are mechanically separable, but this incident was caused by model-backed background dispatch itself. Starting any additional agent/headless model session while containing active token-cost amplification would violate the safety objective and the user's explicit concern. All stages therefore ran in the main session with provider-free stubs; no model worker was launched for implementation or QA.
- observed incident maxima: title chain 216; Claude-family processes 607
- title safety defaults/hard maxima: concurrency 2/4; starts per 600s 4/16
- distill safety defaults/hard maxima: concurrency 2/4; starts per 10m 4/8
- live-provider verification: forbidden for this cycle
