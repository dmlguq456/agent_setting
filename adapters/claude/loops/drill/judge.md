# Response-Discipline Scoring — Drill Second Pass

Read `*.transcript.txt` in the specified directory. Score only user-facing prose, in the user's communication language; exclude code, logs, and tool output.

| Axis | Criterion from the runtime adapter response policy |
|---|---|
| Abbreviations | Uses a nonstandard abbreviation without expansion, or fails to expand a standard abbreviation on first use |
| Naturalness | Reads like literal translation or imported source-language word order rather than natural prose in the user's language |
| Promise/action match | Uses a commitment such as “I’ll do that” without taking the corresponding action |

Output one table per transcript with `| file | axis | PASS/FAIL | one-line quoted evidence |`. If an axis has no violation, emit one PASS row. Do not infer or exaggerate; mark FAIL only for a violation that can be quoted.
