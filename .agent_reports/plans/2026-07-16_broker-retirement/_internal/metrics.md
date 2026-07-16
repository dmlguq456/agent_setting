# Metrics and Exceptions

- intensity: standard
- topology: root inline implementation + native read-only verifier
- inline exception: the task retires the broker that standard+ stage dispatch currently requires. Using that broker to mutate itself would preserve the circular dependency and exercise the surface being removed. Root owns implementation; verifier owns independent review.
- no replacement daemon: required
- source start: `b50e4524`
- spec commit: `b50e4524`
- route contract: v3 direct-only
- live recursive headless: PASS (`OUTER_CONFIRMED_NESTED_HEADLESS_OK_7F3A`)
- portable guards: 368 passed, 0 failed after latest-main integration
- Fleet canonical: 565 passed, 0 failed
- Fleet Claude mirror dispatch: 69 passed, 0 failed
- adaptation boundary: PASS
- source commit: `952f777c`
- integration head: `6ee5bf55`
- independent verifier: PASS, no merge blocker
