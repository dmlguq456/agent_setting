#!/usr/bin/env python3
"""fleet — cross-harness live agent dashboard (entry point).

Zero external deps (stdlib curses/sqlite3/json/subprocess/re/os/time only). Pure external
observer: reads process table + on-disk state artifacts, injects nothing (PRD §0.5). The one
write in the whole system lives in adapters/claude/statusline.sh (§5), never here.

Modes:
  (default)  curses full-screen, re-collect + redraw every --interval seconds
  --once     single snapshot; plain stdout when not a TTY / curses unavailable
  --json     collectors' result as JSON to stdout (pipe / debug / test)
"""
import argparse
import json
import os
import sys

# Support both `python3 fleet.py` (script) and `python3 -m fleet.fleet` (module).
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from fleet.collectors import collect_all
    from fleet.collectors import procscan
else:
    from .collectors import collect_all
    from .collectors import procscan


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="fleet",
        description="Cross-harness live agent-session + dispatch dashboard (external observer).",
    )
    p.add_argument("--interval", type=float, default=2.0,
                   help="live tick interval in seconds (default 2)")
    p.add_argument("--once", action="store_true",
                   help="render one snapshot then exit (plain text if not a TTY)")
    p.add_argument("--no-tmux", action="store_true",
                   help="run the TUI directly (this flag is honored by fleet.sh, not fleet.py)")
    p.add_argument("--section", choices=["fleet", "dispatch", "both"], default="both",
                   help="which section(s) to show (default both)")
    p.add_argument("--harness", default=None,
                   help="comma list to restrict harnesses, e.g. claude,codex")
    p.add_argument("--json", action="store_true",
                   help="emit collected state as JSON to stdout")
    return p.parse_args(argv)   # argparse exits 2 on bad args (matches PRD §3 exit codes)


def _harness_filter(spec):
    if not spec:
        return None
    hs = set(h.strip() for h in spec.split(",") if h.strip())
    unknown = hs - set(procscan.HARNESSES)
    if unknown:
        sys.stderr.write("warning: unknown harness(es) ignored: %s\n" % ", ".join(sorted(unknown)))
    hs &= set(procscan.HARNESSES)
    return hs or None


def _snapshot_json(sessions, jobs):
    counts = {}
    for s in sessions:
        counts[s.harness] = counts.get(s.harness, 0) + 1
    return json.dumps({
        "sessions": [s.to_dict() for s in sessions],
        "jobs": [j.to_dict() for j in jobs],
        "summary": {
            "session_count": len(sessions),
            "by_harness": counts,
            "dispatch_count": len(jobs),
        },
    }, ensure_ascii=False, indent=2)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    hfilter = _harness_filter(args.harness)

    if args.json:
        sessions, jobs = collect_all(harness_filter=hfilter)
        print(_snapshot_json(sessions, jobs))
        return 0

    # curses / --once path (render module) — resolved lazily so --json needs no curses.
    try:
        if __package__ in (None, ""):
            from fleet import render
        else:
            from . import render
    except Exception as e:  # pragma: no cover
        sys.stderr.write("render init failed: %s\n" % e)
        return 1

    if args.once:
        return render.render_once(collect_all, hfilter, args.section)
    return render.run_live(collect_all, hfilter, args.section, args.interval)


if __name__ == "__main__":
    sys.exit(main())
