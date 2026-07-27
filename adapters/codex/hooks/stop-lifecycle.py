#!/usr/bin/env python3
"""Silent Codex Stop boundary with no completion or lifecycle authority."""


def main() -> int:
    # Stop is a turn boundary, not SessionEnd and not a completion callback.
    # Keeping this bridge as an explicit no-op replaces previously trusted
    # blocking definitions without creating a continuation or background job.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
