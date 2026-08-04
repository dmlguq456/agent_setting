"""Fail-soft collector for indexed resource-runner registries."""
import sys
from pathlib import Path

from ..model import ResourceJob, project_of


def _shared():
    root = Path(__file__).resolve().parents[3]
    utilities = str(root / "utilities")
    if utilities not in sys.path:
        sys.path.insert(0, utilities)
    import resource_run_registry
    return resource_run_registry


def collect(index_path=None):
    rows = []
    diagnostics = []
    try:
        raw, diagnostics = _shared().scan(index_path=index_path)
        for item in raw:
            try:
                item["project"] = project_of(item.get("cwd"))
                rows.append(ResourceJob(**item))
            except Exception as exc:
                diagnostics.append({
                    "kind": "resource-row-projection",
                    "run_id": str(item.get("run_id")),
                    "error": str(exc),
                })
    except Exception as exc:
        diagnostics.append({"kind": "resource-collector", "error": str(exc)})
    collect.last_diagnostics = diagnostics
    collect.last_malformed = len(diagnostics)
    return rows


collect.last_diagnostics = []
collect.last_malformed = 0
