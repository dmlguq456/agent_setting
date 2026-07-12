"""F-17 live-title sidecar helper (zero-dep, stdlib only).

fleet-owned sidecar per session: <config_home>/.fleet-titles/<sid>.json
  { "title": str, "ts": float(epoch), "source": str, "offset": int }
Shared single source for collectors/claude.py (read) and refresh_title.py (write).
tolerant: missing/malformed → None (harmless slug fallback, PRD §4.6 F-17).
"""
import json, os, tempfile, time

_FRESH_SEC = 24 * 3600          # PRD §4.6: sidecar "신선 <24h" wins over ai-title
_STALE_SWEEP_SEC = 7 * 24 * 3600   # mtime >7d 삭제 (§5 per-session tap stale-cleanup 선례 mirror)


def _config_home():
    # collectors/claude.py:_home() 과 동일 규약 (CLAUDE_CONFIG_DIR override).
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def titles_dir():
    return os.path.join(_config_home(), ".fleet-titles")


def sidecar_path(sid):
    return os.path.join(titles_dir(), sid + ".json")


def read(sid):
    """Full sidecar dict or None (tolerant: missing/unreadable/malformed → None)."""
    if not sid:
        return None
    try:
        with open(sidecar_path(sid), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def fresh_title(sid, now=None, max_age=_FRESH_SEC):
    """Title string iff sidecar exists, ts within max_age, and title non-empty printable.
    Empty title ('' = 워커가 시도했으나 salient 없음) → None (slug fallback, debounce 는 유지)."""
    d = read(sid)
    if not d:
        return None
    ts = d.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    now = time.time() if now is None else now
    if now - ts > max_age:
        return None
    t = d.get("title")
    return t if isinstance(t, str) and t.strip() else None


def write(sid, title, source="refresher", offset=0, now=None):
    """Atomic write (temp + os.replace). title='' 허용(시도-무산 기록 → debounce 전진)."""
    d = {"title": title or "", "ts": (time.time() if now is None else now),
         "source": source, "offset": int(offset)}
    dirp = titles_dir()
    os.makedirs(dirp, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirp, prefix="." + sid, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, sidecar_path(sid))     # atomic → 동시 reader 가 half-write 안 봄
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass


def sweep(now=None, max_age=_STALE_SWEEP_SEC):
    """mtime > max_age 인 sidecar·잔여 tmp 삭제 (디렉토리 폭증 방지). 반환: 삭제 수."""
    now = time.time() if now is None else now
    n = 0
    try:
        for name in os.listdir(titles_dir()):
            p = os.path.join(titles_dir(), name)
            try:
                if now - os.path.getmtime(p) > max_age:
                    os.unlink(p); n += 1
            except OSError:
                pass
    except OSError:
        pass
    return n
