#!/usr/bin/env python3
"""Unified Memory System — `mem`  (Hermes 메모리 벤치마킹의 store/write 층 구현)

하나의 포터블 store(`~/.claude/memory/`, git추적 markdown 원본) + 파생 SQLite FTS5 색인 +
하네스 주입 projection. 모든 기억을 tier(working/durable) × scope(project/global) × type 로 통합.
spec: ~/.claude/.claude_reports/spec/prd.md (Unified Memory System).

설계 불변식:
  - markdown 원본이 진실(SoT). 색인·projection 은 언제든 재생성 가능한 부산물.
  - 기억 저장 = 자동(품질필터만, 사람 승인 게이트 없음). 세팅·원칙 변경은 본 모듈 영역 아님.
  - 외부 의존 0 (stdlib: sqlite3/argparse/...). rg 있으면 회상 가속.
"""
import argparse, datetime, hashlib, os, re, sqlite3, subprocess, sys
from pathlib import Path

HOME = Path.home()
STORE = Path(os.environ.get("MEM_STORE", HOME / ".claude" / "memory"))
INDEX = STORE / ".index.db"
PROJECTS = Path(os.environ.get("MEM_PROJECTS", HOME / ".claude" / "projects"))
USER_PROFILE = Path(os.environ.get("MEM_PROFILE", HOME / ".claude" / "user_profile"))

TIERS = ("working", "durable")
SCOPES = ("project", "global")
WORKING_TTL_DAYS = 21
FM_ORDER = ["id", "tier", "scope", "type", "cwd_origin", "created", "updated",
            "expires", "source", "tags", "links"]

# injection / secret 가드 (자동 write 라 필수 — 데이터로만 취급, 실행 지시 해석 금지)
INJECTION_PAT = re.compile(
    r"(ignore (all |the )?previous|disregard (all|previous)|you must now|"
    r"system prompt|<\|.*?\|>|act as (an? )?(admin|root)|override (the )?instruction)", re.I)
SECRET_PAT = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-]{12,})", re.I)


def today():
    return datetime.date.today().isoformat()


def enc_cwd(path):
    return re.sub(r"[/._]", "-", str(path))


def slugify(text, n=4):
    words = re.findall(r"[A-Za-z0-9가-힣]+", text.lower())[:n]
    s = "-".join(words) or "note"
    return s[:48]


def norm_body(body):
    return re.sub(r"[\s\W_]+", " ", body.lower()).strip()


# ---------- frontmatter ----------
def parse_record(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta, body = {}, parts[2].lstrip("\n")
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        elif v in ("null", ""):
            v = None
        meta[k] = v
    return meta, body


def serialize_record(meta, body):
    lines = ["---"]
    for k in FM_ORDER:
        if k not in meta or meta[k] is None:
            if k in ("expires", "source", "tags", "links"):
                continue
        v = meta.get(k)
        if isinstance(v, list):
            v = "[" + ", ".join(v) + "]"
        elif v is None:
            v = "null"
        lines.append(f"{k}: {v}")
    lines += ["---", "", body.rstrip(), ""]
    return "\n".join(lines)


def record_path(meta):
    return STORE / meta["tier"] / meta["scope"] / f"{meta['id']}.md"


def iter_records():
    for p in STORE.rglob("*.md"):
        if p.name == "MEMORY.md":
            continue
        try:
            meta, body = parse_record(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("id"):
            meta["_path"] = p
            yield meta, body


# ---------- write (gate · dedup · injection) ----------
def quality_ok(body):
    b = body.strip()
    if len(b) < 15:
        return False, "too short (재발견 가능·trivial)"
    if re.fullmatch(r"[\s\W_]+", b):
        return False, "no content"
    return True, ""


def sanitize(body):
    flags = []
    if INJECTION_PAT.search(body):
        flags.append("injection-pattern")
    masked = SECRET_PAT.sub(lambda m: m.group(0)[:4] + "***REDACTED***", body)
    if masked != body:
        flags.append("secret-masked")
    return masked, flags


def find_dup(tier, scope, body):
    nb = norm_body(body)
    h = hashlib.sha256(nb.encode()).hexdigest()[:16]
    for meta, b in iter_records():
        if meta.get("tier") == tier and meta.get("scope") == scope:
            if hashlib.sha256(norm_body(b).encode()).hexdigest()[:16] == h:
                return meta["id"]
    return None


def write_record(tier, scope, rtype, body, cwd_origin=None, tags=None, links=None,
                 source=None, quiet=False):
    assert tier in TIERS and scope in SCOPES
    ok, why = quality_ok(body)
    if not ok:
        if not quiet:
            print(f"[skip] {why}")
        return None
    body, flags = sanitize(body)
    dup = find_dup(tier, scope, body)
    if dup:
        if not quiet:
            print(f"[dedup] 기존 레코드와 동일 → {dup}")
        return dup
    if cwd_origin is None:
        cwd_origin = enc_cwd(Path.cwd()) if scope == "project" else "global"
    base = slugify(f"{rtype} {body}")
    sid = f"{rtype}_{base}_{hashlib.sha256((body+today()).encode()).hexdigest()[:6]}"
    meta = {"id": sid, "tier": tier, "scope": scope, "type": rtype,
            "cwd_origin": cwd_origin, "created": today(), "updated": today(),
            "tags": tags or [], "links": links or []}
    if tier == "working":
        meta["expires"] = (datetime.date.today() +
                           datetime.timedelta(days=WORKING_TTL_DAYS)).isoformat()
    if source:
        meta["source"] = source
    p = record_path(meta)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(serialize_record(meta, body), encoding="utf-8")
    if not quiet:
        fl = f"  ({'·'.join(flags)})" if flags else ""
        print(f"[write] {tier}/{scope}/{rtype} → {sid}{fl}")
    return sid


# ---------- SQLite FTS5 index ----------
def _fts_available(con):
    try:
        con.execute("CREATE VIRTUAL TABLE temp.t USING fts5(x)")
        con.execute("DROP TABLE temp.t")
        return True
    except sqlite3.OperationalError:
        return False


def index_build(rebuild=False):
    if rebuild and INDEX.exists():
        INDEX.unlink()
    STORE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(INDEX)
    fts = _fts_available(con)
    con.execute("DROP TABLE IF EXISTS records")
    con.execute("""CREATE TABLE records(id TEXT PRIMARY KEY, tier TEXT, scope TEXT,
                   type TEXT, cwd_origin TEXT, created TEXT, updated TEXT,
                   expires TEXT, path TEXT, body TEXT)""")
    if fts:
        con.execute("DROP TABLE IF EXISTS records_fts")
        con.execute("CREATE VIRTUAL TABLE records_fts USING fts5("
                    "id UNINDEXED, body, tokenize='unicode61')")
    n = 0
    for meta, body in iter_records():
        con.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (meta["id"], meta.get("tier"), meta.get("scope"), meta.get("type"),
                     meta.get("cwd_origin"), meta.get("created"), meta.get("updated"),
                     meta.get("expires"), str(meta["_path"]), body))
        if fts:
            con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (meta["id"], body))
        n += 1
    con.commit()
    con.close()
    print(f"[index] {n} records → {INDEX}  (FTS5={'on' if fts else 'off, LIKE fallback'})")
    return n


# ---------- recall ----------
def recall(query, tier=None, scope=None, cwd=None, sessions=False, limit=20):
    print(f"# recall: \"{query}\"  [tier={tier or '*'} scope={scope or '*'} "
          f"cwd={'현재' if cwd else '전체'}]")
    hits = []
    if INDEX.exists():
        con = sqlite3.connect(INDEX)
        has_fts = con.execute(
            "SELECT name FROM sqlite_master WHERE name='records_fts'").fetchone()
        try:
            if has_fts:
                rows = con.execute(
                    "SELECT r.id,r.tier,r.scope,r.type,r.path,snippet(records_fts,1,'»','«','…',12) "
                    "FROM records_fts f JOIN records r ON r.id=f.id "
                    "WHERE records_fts MATCH ? ORDER BY rank LIMIT ?",
                    (query, limit * 3)).fetchall()
            else:
                rows = con.execute(
                    "SELECT id,tier,scope,type,path,substr(body,1,160) FROM records "
                    "WHERE body LIKE ? LIMIT ?", (f"%{query}%", limit * 3)).fetchall()
        except sqlite3.OperationalError:
            rows = con.execute(
                "SELECT id,tier,scope,type,path,substr(body,1,160) FROM records "
                "WHERE body LIKE ? LIMIT ?", (f"%{query}%", limit * 3)).fetchall()
        con.close()
        for rid, rt, rs, rtype, path, snip in rows:
            if tier and rt != tier:
                continue
            if scope and rs != scope:
                continue
            if cwd and rs == "project" and Path(path).parts[-2] != "project":
                pass  # cwd filter via record meta below
            hits.append((rt, rs, rtype, path, snip.replace("\n", " ")))
    else:
        for meta, body in iter_records():
            if query.lower() not in body.lower():
                continue
            if tier and meta.get("tier") != tier:
                continue
            if scope and meta.get("scope") != scope:
                continue
            hits.append((meta.get("tier"), meta.get("scope"), meta.get("type"),
                         str(meta["_path"]), body[:160].replace("\n", " ")))
    # cwd filter (project scope → cwd_origin must match)
    if cwd:
        encc = enc_cwd(Path.cwd())
        kept = []
        for h in hits:
            m, _ = parse_record(Path(h[3]).read_text(encoding="utf-8"))
            if m.get("scope") == "global" or m.get("cwd_origin") == encc:
                kept.append(h)
        hits = kept
    hits = hits[:limit]
    if not hits:
        print("(store 매칭 없음)")
    for rt, rs, rtype, path, snip in hits:
        print(f"  [{rt}/{rs}/{rtype}] {Path(path).name}: {snip}")
    if sessions:
        print(f"\n# raw 세션 transcript: \"{query}\"  (미정제)")
        _recall_sessions(query, cwd)
    return hits


def _recall_sessions(query, cwd):
    base = PROJECTS / enc_cwd(Path.cwd()) if cwd else PROJECTS
    if not base.exists():
        print(f"(세션 기록 없음: {base})")
        return
    rg = subprocess.run(["bash", "-c", "command -v rg"], capture_output=True).returncode == 0
    if rg:
        cmd = ["rg", "-i", "-oP", "-n", "--no-heading", "-g", "*.jsonl",
               r".{0,40}\Q" + query + r"\E.{0,140}", str(base)]
    else:
        cmd = ["grep", "-i", "-rn", "--include=*.jsonl", query, str(base)]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()[:30]
    print("\n".join(out) if out else "(세션 매칭 없음)")


# ---------- migrate ----------
def migrate(apply=False):
    print(f"# migrate  ({'APPLY' if apply else 'dry-run'})")
    created, skipped = 0, 0
    existing_src = {m.get("source") for m, _ in iter_records() if m.get("source")}
    # 1) auto-memory: projects/<cwd>/memory/*.md
    for mp in PROJECTS.glob("*/memory/*.md"):
        if mp.name == "MEMORY.md":
            continue
        src = f"auto-memory:{mp.parent.parent.name}/{mp.name}"
        if src in existing_src:
            skipped += 1
            continue
        meta, body = parse_record(mp.read_text(encoding="utf-8"))
        rtype = meta.get("type", "project")
        scope = "global" if rtype == "user" else "project"
        cwd_origin = mp.parent.parent.name
        if apply:
            write_record("durable", scope, rtype, body, cwd_origin=cwd_origin,
                         source=src, quiet=True)
        created += 1
    # 2) post-it: 얕은 find(maxdepth 5)로 전 프로젝트 post-it.md 발견 → working records.
    #    표준 5섹션은 type 매핑, 미지정 섹션(worklog-board 의 ★현재상태·🔴결재대기 등)은 generic 'note' 로 보존.
    POST_SECT = {"Open Threads": "thread", "Decisions": "decision",
                 "Next Session Hints": "hint", "Conventions": "convention",
                 "External Resources": "reference"}
    # post-it 발견 = 레지스트리(~/.claude/memory/.postit-roots, 경로 목록) + 현 cwd.
    #    NAS(네트워크 FS) 재귀 find 는 느리고 불안정(timeout 빈번) → 직접 stat 만. /post-it 가 생성 시 등록.
    postits = set()
    reg = STORE / ".postit-roots"
    if reg.exists():
        for line in reg.read_text(encoding="utf-8").splitlines():
            p = Path(line.strip())
            if p.name == "post-it.md" and p.exists():
                postits.add(p)
    cwd_pi = Path.cwd() / ".claude_reports" / "post-it.md"
    if cwd_pi.exists():
        postits.add(cwd_pi)
    postits = sorted(postits)
    print(f"  post-it 발견: {len(postits)}개 (registry+cwd)")
    for pi in postits:
        cwd_origin = enc_cwd(pi.parent.parent)
        cur = "note"
        for line in pi.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"##\s+(.*)", line)
            if m:
                cur = POST_SECT.get(m.group(1).strip(), "note")
                continue
            b = re.match(r"\s*[-*]\s+(.*)", line)
            if cur and b and len(b.group(1).strip()) > 14:
                src = f"post-it:{cwd_origin}:{hashlib.sha256(b.group(1).encode()).hexdigest()[:8]}"
                if src in existing_src:
                    skipped += 1
                    continue
                if apply:
                    write_record("working", "project", cur, b.group(1).strip(),
                                 cwd_origin=cwd_origin, source=src, quiet=True)
                created += 1
    # 3) user_profile/*.md → durable/global mirror (파일은 source 로 제자리 유지 — 경로참조·analyze-user).
    #    각 aspect 문서 = 1 레코드(type=profile, body=전문). store sync 가 갱신. auto-memory 와 동형 mirror.
    if USER_PROFILE.exists():
        for up in sorted(USER_PROFILE.glob("*.md")):
            if up.name == "README.md":
                continue
            src = f"user-profile:{up.stem}"
            if src in existing_src:
                skipped += 1
                continue
            if apply:
                write_record("durable", "global", "profile",
                             up.read_text(encoding="utf-8", errors="ignore"),
                             cwd_origin="global", source=src, quiet=True)
            created += 1
    print(f"  → {'생성' if apply else '생성 예정'} {created} · 기존 skip {skipped}")
    return created


# ---------- lifecycle ----------
def lifecycle(apply=False):
    print(f"# lifecycle  ({'APPLY' if apply else 'report'})")
    expired, grad, dups = [], [], []
    seen = {}
    for meta, body in iter_records():
        if meta.get("tier") == "working" and meta.get("expires"):
            if meta["expires"] < today():
                expired.append(meta)
        key = (meta.get("tier"), meta.get("scope"), norm_body(body)[:80])
        seen.setdefault(key, []).append(meta["id"])
    for key, ids in seen.items():
        if len(ids) > 1:
            dups.append(ids)
    # working 만료 → 자동 삭제(단기·D-1) ; durable dup → 플래깅(gc 수동)
    for m in expired:
        print(f"  [expire] {m['id']} (expires {m['expires']})")
        if apply:
            Path(m["_path"]).unlink(missing_ok=True)
    for ids in dups:
        print(f"  [dup-flag] {ids}  (consolidate 후보 — 자동삭제 X)")
    print(f"  → 만료 {len(expired)}{'(삭제)' if apply else ''} · dup-flag {len(dups)}")
    return expired, dups


# ---------- projection (store → harness 주입 위치) ----------
def project(cwd=None):
    cwd = Path(cwd) if cwd else Path.cwd()
    encc = enc_cwd(cwd)
    dest = PROJECTS / encc / "memory"
    dest.mkdir(parents=True, exist_ok=True)
    proj = dest / "_projection"
    proj.mkdir(exist_ok=True)
    for old in proj.glob("*.md"):
        old.unlink()
    idx, n = ["# MEMORY.md — projection (store 생성, 직접 편집 금지)", ""], 0
    for meta, body in iter_records():
        if meta.get("scope") == "global" or meta.get("cwd_origin") == encc:
            (proj / f"{meta['id']}.md").write_text(
                serialize_record(meta, body), encoding="utf-8")
            idx.append(f"- [{meta['id']}](_projection/{meta['id']}.md) "
                       f"[{meta.get('tier')}/{meta.get('type')}]")
            n += 1
    (dest / "MEMORY.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"[project] {n} records → {dest}")
    return n


def stats():
    from collections import Counter
    c = Counter()
    for meta, _ in iter_records():
        c[(meta.get("tier"), meta.get("scope"))] += 1
    print("# store stats")
    total = 0
    for (t, s), n in sorted(c.items()):
        print(f"  {t}/{s}: {n}")
        total += n
    print(f"  total: {total}  ({STORE})")


def register_postit(path):
    """post-it.md 경로를 레지스트리에 등록 (NAS 스캔 회피 — /post-it 생성 시·시드 호출)."""
    STORE.mkdir(parents=True, exist_ok=True)
    reg = STORE / ".postit-roots"
    p = str(Path(path).resolve())
    existing = set(reg.read_text(encoding="utf-8").splitlines()) if reg.exists() else set()
    if p in existing:
        print(f"[register] 이미 등록: {p}")
        return
    with reg.open("a", encoding="utf-8") as f:
        f.write(p + "\n")
    print(f"[register] {p}")


def sync():
    """하네스가 projects/<cwd>/memory/ 에 쓴 auto-memory 를 store 로 멱등 mirror + 색인 재생성.
    하네스가 메모리 write 를 소유하므로 store 는 source 가 아니라 _포터블 추적 mirror_ — 주기 sync(oncall/note)로 최신 유지."""
    print("# sync (projects → store mirror)")
    n = migrate(apply=True)
    index_build(rebuild=True)
    return n


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(prog="mem", description="Unified Memory System")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="수동 기록")
    a.add_argument("tier", choices=TIERS); a.add_argument("type")
    a.add_argument("body"); a.add_argument("--scope", choices=SCOPES, default="project")
    a.add_argument("--tags", default=""); a.add_argument("--cwd-origin")
    n = sub.add_parser("note", help="working tier 단축 기록")
    n.add_argument("body"); n.add_argument("--type", default="thread")
    r = sub.add_parser("recall", help="회상")
    r.add_argument("query"); r.add_argument("--tier", choices=TIERS)
    r.add_argument("--scope", choices=SCOPES)
    r.add_argument("--all", action="store_true", help="전 cwd (default: 현 cwd)")
    r.add_argument("--sessions", action="store_true")
    ix = sub.add_parser("index", help="FTS5 색인"); ix.add_argument("--rebuild", action="store_true")
    pj = sub.add_parser("project", help="주입 projection"); pj.add_argument("--cwd")
    mg = sub.add_parser("migrate", help="post-it+auto-memory 이주"); mg.add_argument("--apply", action="store_true")
    lc = sub.add_parser("lifecycle", help="working 만료·졸업 / durable dup"); lc.add_argument("--apply", action="store_true")
    sub.add_parser("stats", help="store 통계")
    sub.add_parser("sync", help="projects→store 멱등 mirror + 색인 (oncall/note 주기 호출)")
    rp = sub.add_parser("register-postit", help="post-it.md 경로 레지스트리 등록"); rp.add_argument("path")
    args = ap.parse_args()

    if args.cmd == "add":
        write_record(args.tier, args.scope, args.type, args.body,
                     cwd_origin=args.cwd_origin,
                     tags=[t for t in args.tags.split(",") if t])
    elif args.cmd == "note":
        write_record("working", "project", args.type, args.body)
    elif args.cmd == "recall":
        recall(args.query, tier=args.tier, scope=args.scope,
               cwd=not args.all, sessions=args.sessions)
    elif args.cmd == "index":
        index_build(rebuild=args.rebuild)
    elif args.cmd == "project":
        project(args.cwd)
    elif args.cmd == "migrate":
        migrate(apply=args.apply)
    elif args.cmd == "lifecycle":
        lifecycle(apply=args.apply)
    elif args.cmd == "stats":
        stats()
    elif args.cmd == "sync":
        sync()
    elif args.cmd == "register-postit":
        register_postit(args.path)


if __name__ == "__main__":
    main()
