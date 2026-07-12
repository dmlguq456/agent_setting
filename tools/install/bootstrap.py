"""bootstrap.py — installer 의 runtime-neutral 보조 기능 (Phase 6).

두 관심사를 다룬다:
  1. `restore_memory` — mem store 에 `memory.db` 가 없고 `dump.jsonl` 만 있을 때
     `tools/memory/mem.py import` 를 호출해 복원한다 (idempotent — DB 있으면 스킵).
  2. `install_launchers` — `~/.local/bin/{harness,fleet}` 심볼릭 링크를 만든다
     (PATH-collision guard 포함, INST-OPEN-2).

installer.py Phase 5 가 이 모듈의 함수들을 cmd_install 안에서 호출할 예정이지만,
본 파일 자체는 그 wiring 과 독립적으로 완결된 helper 모듈이다.
"""

import os
import subprocess
from pathlib import Path

import paths


def restore_memory(mem_store=None):
    """mem store 의 `memory.db` 가 없으면 `dump.jsonl` 로부터 복원을 시도한다.

    Args:
        mem_store: mem store 디렉터리. None 이면 `MEM_STORE` env, 그것도 없으면
            `paths.agent_home() / "memory"`.

    Returns:
        dict — {"action": "skipped"|"imported"|"failed", "detail": str}
    """
    if mem_store is None:
        mem_store = os.environ.get("MEM_STORE")
    if mem_store is None:
        mem_store = paths.agent_home() / "memory"
    mem_store = Path(mem_store)

    db_path = mem_store / "memory.db"
    dump_path = mem_store / "dump.jsonl"

    if db_path.exists():
        return {"action": "skipped", "detail": "memory.db already present"}

    if not dump_path.exists():
        return {
            "action": "skipped",
            "detail": "no dump.jsonl to restore from, and no existing memory.db",
        }

    mem_script = paths.resolve_source("tools/memory/mem.py")
    env = {**os.environ, "MEM_STORE": str(mem_store)}
    result = subprocess.run(
        ["python3", str(mem_script), "import", str(dump_path)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return {"action": "imported", "detail": f"mem import from {dump_path}"}

    # best-effort restore — 실패해도 install 전체를 죽이지 않는다 (mem 복원은 부가 기능).
    return {
        "action": "failed",
        "detail": (
            f"mem import failed: exit={result.returncode} "
            f"stderr={result.stderr[:300]}"
        ),
    }


LAUNCHERS = (
    ("harness", "tools/install/harness.sh"),
    ("fleet", "tools/fleet/fleet.sh"),
)


def _is_our_symlink(target, source):
    """target 이 symlink 이고 그 링크 대상이 정확히 source 인지."""
    if not target.is_symlink():
        return False
    try:
        return target.resolve() == source.resolve()
    except OSError:
        return False


def install_launchers(home=None, dry_run=False):
    """`~/.local/bin/{harness,fleet}` 심볼릭 링크를 만든다 (PATH-collision guard 포함).

    Args:
        home: 대상 home 디렉터리 (Path). None 이면 `Path.home()`.
        dry_run: True 면 디스크를 건드리지 않고 계획만 돌려준다.

    Returns:
        list of dict — [{"name", "target", "source", "status"}, ...]
        status ∈ {"planned", "created", "unchanged", "skipped-collision"}
    """
    if home is None:
        home = Path.home()
    bin_dir = home / ".local" / "bin"

    results = []

    if dry_run:
        for name, rel_source in LAUNCHERS:
            source = paths.resolve_source(rel_source)
            target = bin_dir / name
            results.append({
                "name": name,
                "target": str(target),
                "source": str(source),
                "status": "planned",
            })
        return results

    bin_dir.mkdir(parents=True, exist_ok=True)

    for name, rel_source in LAUNCHERS:
        source = paths.resolve_source(rel_source)
        target = bin_dir / name

        if target.exists() or target.is_symlink():
            if _is_our_symlink(target, source):
                results.append({
                    "name": name,
                    "target": str(target),
                    "source": str(source),
                    "status": "unchanged",
                })
                continue

            # 존재하지만 우리 심볼릭 링크가 아니다 — foreign 파일/다른 링크는 덮어쓰지 않는다.
            results.append({
                "name": name,
                "target": str(target),
                "source": str(source),
                "status": "skipped-collision",
                "detail": f"foreign '{name}' already at {target} — not overwriting",
            })
            continue

        target.symlink_to(source)
        results.append({
            "name": name,
            "target": str(target),
            "source": str(source),
            "status": "created",
        })

    return results
