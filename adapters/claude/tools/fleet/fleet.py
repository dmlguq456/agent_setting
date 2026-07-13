#!/usr/bin/env python3
"""fleet — cross-harness live agent dashboard (entry point).

Zero external deps (stdlib curses/sqlite3/json/subprocess/re/os/time only). Pure external
observer: reads process table + on-disk state artifacts and injects nothing (PRD §0.5).
The live TUI may schedule the fleet-owned title refresher, which writes only neutral local
state; ``--json`` and ``--once`` remain side-effect-free snapshots.

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
                   help="row-type filter within each project group: fleet=session rows only, "
                        "dispatch=dispatch rows only, both=full group (default both)")
    p.add_argument("--harness", default=None,
                   help="comma list to restrict harnesses, e.g. claude,codex")
    p.add_argument("--json", action="store_true",
                   help="emit collected state as JSON to stdout")
    p.add_argument("--all", dest="show_all", action="store_true",
                   help="include stale/dead sessions in the fleet list (hidden by default)")
    p.add_argument("--demo", action="store_true",
                   help="render synthetic fixture data (all harnesses + states) for rendering checks")
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


def _collect_memory():
    # F-19: additive, best-effort — a collector import/read failure must never break --json.
    try:
        if __package__ in (None, ""):
            from fleet.collectors import memory as memcol
        else:
            from .collectors import memory as memcol
        return memcol.collect()
    except Exception:
        return None


def _snapshot_json(sessions, jobs):
    counts = {}
    for s in sessions:
        counts[s.harness] = counts.get(s.harness, 0) + 1
    out = {
        "sessions": [s.to_dict() for s in sessions],
        "jobs": [j.to_dict() for j in jobs],
        "summary": {
            "session_count": len(sessions),
            "by_harness": counts,
            "dispatch_count": len(jobs),
        },
    }
    mem = _collect_memory()
    if mem is not None:
        out["memory"] = mem
    return json.dumps(out, ensure_ascii=False, indent=2)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    hfilter = _harness_filter(args.harness)

    collector = collect_all
    if args.demo or os.environ.get("FLEET_DEMO"):   # flag OR env (env works through any launcher/alias)
        if __package__ in (None, ""):
            from fleet import demo
        else:
            from . import demo

        def collector(harness_filter=None):      # LIVE real data + injected demo fixtures (merged)
            rs, rj = collect_all(harness_filter=harness_filter)
            ds, dj = demo.collect(harness_filter=harness_filter)
            return rs + ds, rj + dj

    if args.json:
        sessions, jobs = collector(harness_filter=hfilter)
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

    render.set_show_all(args.show_all)
    if args.once:
        return render.render_once(collector, hfilter, args.section)
    render.reset_scroll()   # fresh launch starts scrolled to top (belt-and-suspenders)

    base_collector = collector

    def live_collector(harness_filter=None):
        sessions, jobs = base_collector(harness_filter=harness_filter)
        try:
            if __package__ in (None, ""):
                from fleet import refresh_title
            else:
                from . import refresh_title
            refresh_title.schedule_sessions(sessions)
        except Exception:
            pass                              # title refresh must never break observation
        return sessions, jobs

    return render.run_live(live_collector, hfilter, args.section, args.interval)


if __name__ == "__main__":
    sys.exit(main())
