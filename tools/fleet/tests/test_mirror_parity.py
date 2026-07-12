"""Mirror-drift guard: adapters/claude/tools/fleet must byte-match tools/fleet.

The Claude adapter surface (~/.claude/tools/fleet) is a deliberate *concrete*
projection of the canonical runtime-neutral tools/fleet (commit 8d00b7f chose a
copy over a symlink for Windows Git Bash support). A copy drifts silently the
moment canonical changes without a resync — observed 2026-07-11: the mirror was
stale from F-16 through F-19 (last sync e872ad0). This suite runs in every
fleet dev cycle, so the cycle that edits canonical fails here until it resyncs:

    rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
"""
import unittest
from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[1]           # tools/fleet
MIRROR = CANONICAL.parents[1] / "adapters" / "claude" / "tools" / "fleet"
SKIP_DIRS = {"__pycache__"}


def _tree(root: Path) -> dict:
    files = {}
    for p in root.rglob("*"):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        files[str(p.relative_to(root))] = p.read_bytes()
    return files


class TestMirrorParity(unittest.TestCase):
    def test_mirror_matches_canonical(self):
        if not MIRROR.is_dir():
            self.skipTest("adapter mirror absent (non-repo install layout)")
        canon, mirror = _tree(CANONICAL), _tree(MIRROR)
        missing = sorted(set(canon) - set(mirror))
        extra = sorted(set(mirror) - set(canon))
        differing = sorted(k for k in set(canon) & set(mirror) if canon[k] != mirror[k])
        problems = []
        if missing:
            problems.append(f"mirror에 없음: {missing}")
        if extra:
            problems.append(f"mirror에만 있음: {extra}")
        if differing:
            problems.append(f"내용 상이: {differing}")
        self.assertFalse(
            problems,
            "adapter fleet mirror drift — 재동기 필요 "
            "(rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/): "
            + "; ".join(problems),
        )


if __name__ == "__main__":
    unittest.main()
