"""manifest.py — hash-manifest 기록·drift 감지·reapply (PRD "hash-manifest + reapply").

대상은 installer 가 runtime home 에 **복사**한 파일만 (settings.json·keybindings·Windows
copy 분기) — symlink 는 그 자체가 canonical 이라 제외, plugin cache 는 런타임 소유라 제외.
스키마는 harness-layer-sync(HLS) 와 공유(PRD §1 interlock) — `tools/build-manifest.py` 증분
포맷을 재사용할지는 구현 단계에서 확정한다.

## 디렉터리 레이아웃 (모두 `<runtime_home>/.harness/` 아래, `paths.harness_state_dir()`)

- `manifest.json` — 설치본 hash 등재부:
  ```json
  {"schema": 1, "runtime": "claude", "scope": "global",
   "version": "<repo git SHA at install>", "timestamp": "<iso8601>",
   "files": {"settings.json": "<sha256hex>", "keybindings.json": "<sha256hex>"}}
  ```
- `pristine/<relpath>` — 설치 시점 repo-canonical 바이트 그대로의 스냅샷 (3-way merge 의
  base). 다음 설치가 성공적으로 재적용되기 전까지는 불변 — drift 가 미해결인 채로
  최신 릴리스 사본으로 덮어쓰지 않는다 (impl-inputs §A 함정 #3407).
- `local-patches/<relpath>` — 사용자가 수정한 파일을 wipe 하기 직전에 뜬 전체 파일 백업
  (impl-inputs §A 채택안: per-runtime 단일 디렉터리로 통합).
- `local-patches/backup-meta.json` — 백업 메타:
  ```json
  {"from_version": "<sha>", "pristine_hashes": {"<relpath>": "<sha256>"}}
  ```

## cycle 1 스코프

manifest 대상은 **copy-once 파일만** — Claude 의 `settings.json`, `keybindings.json`
(+ `install-windows.sh` 가 만드는 Windows 사본). symlink 는 그 자체가 canonical 이라 제외.
OpenCode `opencode.json` 은 merge-managed 파일로 별도 취급 — cycle 1 에서는 harness 가
관리하는 fragment 존재 여부만 기록하고, 전체 merge-manifest 는 이후 사이클로 미룬다
(Risks 항목으로 남김).

hash 알고리즘은 SHA-256 hex 로 GSD/HLS 와 동일 — 별도 알고리즘으로 갈라지지 않는다.
키 이름은 겹치는 부분에서 `tools/build-manifest.py` 컨벤션을 따른다.

⚠️ 구현 선행 게이트 (PRD "hash-manifest + reapply" 절, HLS §3.2 공유): GSD `bin/install.js`
실코드를 line 단위로 정독하기 전에는 아래 함수들의 실 hash/merge 로직을 채우지 않는다.
research 카드 서술을 그대로 이식 금지 — 지금은 시그니처와 반환 shape, 그리고 위 스키마
문서만 확정한 stub (Phase 2 에서 실 로직 구현).
"""


import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import paths


_CHUNK_SIZE = 65536


def _sha256(path):
    """path 를 스트리밍으로 읽어 SHA-256 hex digest 를 돌려준다."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _manifest_path(runtime, scope):
    return paths.harness_state_dir(runtime, scope) / "manifest.json"


def _pristine_path(runtime, scope, relpath):
    return paths.harness_state_dir(runtime, scope) / "pristine" / relpath


def _backup_path(runtime, scope, relpath):
    return paths.harness_state_dir(runtime, scope) / "local-patches" / relpath


def _safe_relpath(rel):
    """manifest 유래 relpath 를 디스크 접근 전 검증한다.

    절대경로 / `..` 세그먼트 / NUL byte / zip-slip 류 경로 이탈을 거부한다.
    위반 시 ValueError.
    """
    if "\x00" in rel:
        raise ValueError(f"relpath 에 NUL byte 포함: {rel!r}")

    p = Path(rel)
    if p.is_absolute():
        raise ValueError(f"relpath 는 절대경로일 수 없다: {rel!r}")

    if any(part == ".." for part in p.parts):
        raise ValueError(f"relpath 에 '..' 세그먼트 포함(경로 이탈 시도): {rel!r}")

    base = Path("/__manifest_safe_base__").resolve()
    resolved = (base / p).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise ValueError(f"relpath 가 base 경로를 벗어난다(zip-slip 류): {rel!r}")

    return rel


def _load_manifest(path):
    path = Path(path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_manifest(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _atomic_write_bytes(path, data):
    """temp+rename 로 write_bytes — 크래시 시 대상 파일이 부분 쓰기로 남지 않게 한다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_bytes(data)
    os.replace(tmp_path, path)


def _git_head_or_unknown():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(paths.agent_home()),
        )
        if result.returncode == 0:
            sha = result.stdout.strip()
            if sha:
                return sha
    except Exception:
        pass
    return "unknown"


def _three_way_merge(ours, base, theirs):
    """`git merge-file -p --diff3 ours base theirs` 를 실행한다.

    반환: (ok: bool, merged_bytes: bytes|None, had_conflict_markers: bool, tool_missing: bool)
    ok=True 는 "충돌 없이 병합됨" 을 의미(리턴코드 0). tool_missing=True 면 git 부재.
    """
    try:
        result = subprocess.run(
            ["git", "merge-file", "-p", "--diff3", str(ours), str(base), str(theirs)],
            capture_output=True,
        )
    except FileNotFoundError:
        return (False, None, False, True)

    merged_bytes = result.stdout
    conflict_markers = any(
        marker in merged_bytes for marker in (b"<<<<<<<", b"=======", b">>>>>>>")
    )
    ok = result.returncode == 0 and not conflict_markers
    return (ok, merged_bytes, conflict_markers, False)


def record(runtime, files, scope="global", version=None):
    """설치 직후 각 복사 파일의 hash 를 등재한다.

    `files` = [{"relpath", "source_abs", "dest_abs"}, ...] (projector copy_once 액션 유래).
    pristine 스냅샷은 부재 시에만 채운다 — anti-clobber invariant (성공적으로 검증된
    reapply 이후에만 갱신, plain record() 호출로는 절대 덮어쓰지 않는다).
    """
    manifest_path = _manifest_path(runtime, scope)
    existing = _load_manifest(manifest_path) or {}
    files_map = dict(existing.get("files", {}))

    for entry in files:
        relpath = _safe_relpath(entry["relpath"])
        source_abs = Path(entry["source_abs"])
        dest_abs = Path(entry["dest_abs"])

        pristine_path = _pristine_path(runtime, scope, relpath)
        if not pristine_path.exists():
            _atomic_write_bytes(pristine_path, source_abs.read_bytes())

        files_map[relpath] = _sha256(dest_abs)

    if version is None:
        version = _git_head_or_unknown()

    manifest = {
        "schema": 1,
        "runtime": runtime,
        "scope": scope,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": files_map,
    }
    _write_manifest(manifest_path, manifest)
    return manifest


def check_drift(runtimes, scope="global"):
    """등재된 hash 와 현재 파일을 비교해 사용자 수정(drift) 목록을 돌려준다.

    반환 shape: [{"runtime": str, "path": str, "detail": str}, ...].
    manifest 자체가 없는 runtime(설치된 적 없음)은 조용히 건너뛴다 — drift 로 취급 X.
    """
    drift = []
    for rt in runtimes:
        manifest = _load_manifest(_manifest_path(rt, scope))
        if manifest is None:
            continue

        files_map = manifest.get("files", {})
        for relpath in sorted(files_map.keys()):
            relpath = _safe_relpath(relpath)
            recorded_hash = files_map[relpath]
            dest_abs = paths.runtime_home(rt, scope) / relpath

            if not dest_abs.exists():
                drift.append({"runtime": rt, "path": relpath, "detail": "file missing"})
                continue

            current_hash = _sha256(dest_abs)
            if current_hash != recorded_hash:
                drift.append({"runtime": rt, "path": relpath, "detail": "hash mismatch"})

    return drift


def reapply(runtimes, scope="global", sources=None):
    """`update --reapply` — local-patches 백업 위에 새 파일을 재적용한다.

    `sources` = {runtime: {relpath: source_abs}} — 현재 canonical source 경로(호출자/driver 가
    projector plan 의 copy_once 항목에서 제공). 특정 relpath 에 대한 source 가 없으면 병합을
    시도하지 않고 "no canonical source provided" 로 skip 한다.

    3-way 충돌은 자동 머지 강행 금지 — 명시 report 로 그친다 (PRD 원칙).
    반환: {"reapplied": [...], "conflicts": [...], "verify_failed": [...], "missing": [...]}
    """
    sources = sources or {}

    result = {"reapplied": [], "conflicts": [], "verify_failed": [], "missing": []}
    touched_runtimes = set()

    for rt in runtimes:
        rt_sources = sources.get(rt, {})
        rt_drift = check_drift([rt], scope=scope)

        manifest_path = _manifest_path(rt, scope)
        manifest = _load_manifest(manifest_path)
        if manifest is None:
            continue

        for entry in rt_drift:
            relpath = _safe_relpath(entry["path"])
            detail = entry["detail"]

            if detail == "file missing":
                result["missing"].append({"runtime": rt, "path": relpath})
                continue

            dest_abs = paths.runtime_home(rt, scope) / relpath
            pristine_path = _pristine_path(rt, scope, relpath)
            backup_path = _backup_path(rt, scope, relpath)

            # Step 1 — pre-wipe backup.
            _atomic_write_bytes(backup_path, dest_abs.read_bytes())

            backup_meta_path = _backup_path(rt, scope, "backup-meta.json").parent / "backup-meta.json"
            backup_meta = _load_manifest(backup_meta_path) or {
                "from_version": manifest.get("version"),
                "pristine_hashes": {},
            }
            backup_meta["from_version"] = manifest.get("version")
            if pristine_path.exists():
                backup_meta["pristine_hashes"][relpath] = _sha256(pristine_path)
            _write_manifest(backup_meta_path, backup_meta)

            source_abs = rt_sources.get(relpath)
            if source_abs is None:
                result["verify_failed"].append(
                    {"runtime": rt, "path": relpath, "status": "no canonical source provided"}
                )
                continue

            if not pristine_path.exists():
                result["verify_failed"].append(
                    {"runtime": rt, "path": relpath, "status": "no pristine snapshot"}
                )
                continue

            # Step 2 — 3-way merge.
            ok, merged_bytes, had_conflict, tool_missing = _three_way_merge(
                dest_abs, pristine_path, source_abs
            )

            if tool_missing:
                result["conflicts"].append(
                    {"runtime": rt, "path": relpath, "status": "no-git-merge-file"}
                )
                continue

            if not ok:
                result["conflicts"].append({"runtime": rt, "path": relpath, "status": "conflict"})
                continue

            # Step 3 — deterministic post-merge verifier.
            backup_lines = [
                line for line in backup_path.read_bytes().splitlines() if line.strip()
            ]
            verify_ok = all(line in merged_bytes for line in backup_lines)

            if not verify_ok:
                result["verify_failed"].append(
                    {"runtime": rt, "path": relpath, "status": "verify_failed"}
                )
                continue

            # Step 4 — write merged output, refresh pristine, update manifest hash.
            _atomic_write_bytes(dest_abs, merged_bytes)
            _atomic_write_bytes(pristine_path, Path(source_abs).read_bytes())
            manifest.setdefault("files", {})[relpath] = _sha256(dest_abs)
            touched_runtimes.add(rt)

            result["reapplied"].append({"runtime": rt, "path": relpath})

        if rt in touched_runtimes:
            manifest["version"] = _git_head_or_unknown()
            manifest["timestamp"] = datetime.now(timezone.utc).isoformat()
            _write_manifest(manifest_path, manifest)

    return result
