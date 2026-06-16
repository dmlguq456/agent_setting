#!/usr/bin/env python3
"""Unified Memory System — `mem`  (DB-as-SoT 재구현)

SQLite `memory.db` (WAL) 가 진실원천(SoT). 기존 markdown-SoT 를 완전 대체.
텍스트 덤프 mirror (`dump.jsonl`) = git 추적 대상. FTS5 (unicode61 + trigram CJK) 내장.
spec: ~/.claude/.claude_reports/spec/prd.md (Unified Memory System v3).

설계 불변식:
  - SQLite DB 가 진실원천. dump.jsonl 은 결정론적 텍스트 mirror.
  - 기억 저장 = 자동(품질필터만, 사람 승인 게이트 없음).
  - 외부 의존 0 (stdlib: sqlite3/argparse/json/hashlib/...). rg 있으면 회상 가속.
"""
import argparse, datetime, hashlib, json, os, re, sqlite3, subprocess, sys
from pathlib import Path

HOME = Path.home()
STORE = Path(os.environ.get("MEM_STORE", HOME / ".claude" / "memory"))
DB = STORE / "memory.db"
DUMP = STORE / "dump.jsonl"
PROJECTS = Path(os.environ.get("MEM_PROJECTS", HOME / ".claude" / "projects"))
USER_PROFILE = Path(os.environ.get("MEM_PROFILE", HOME / ".claude" / "user_profile"))

TIERS = ("working", "durable")
SCOPES = ("project", "global")
WORKING_TTL_DAYS = 21
FM_ORDER = ["id", "tier", "scope", "type", "cwd_origin", "created", "updated",
            "expires", "source", "tags", "links"]

# 12 컬럼 정규 순서 (export/import round-trip 결정성 기반)
RECORD_COLS = ("id", "tier", "scope", "type", "cwd_origin", "created", "updated",
               "expires", "source", "tags", "links", "body")

# injection / secret 가드
INJECTION_PAT = re.compile(
    r"(ignore (all |the )?previous|disregard (all|previous)|you must now|"
    r"system prompt|<\|.*?\|>|act as (an? )?(admin|root)|override (the )?instruction)", re.I)
SECRET_PAT = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-]{12,})", re.I)

# 모듈 레벨 FTS / trigram 가용성 캐시 (get_con() 최초 호출 시 설정)
_FTS_OK = None     # FTS5 unicode61 가용 여부
_TRIG_OK = None    # trigram 토크나이저 가용 여부


# ---------- 순수 헬퍼 ----------
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


# ---------- frontmatter (migration source 읽기 / projection 출력 용) ----------
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


# ---------- migration source 파일 읽기 (구 SoT md 파일 → iter) ----------
def iter_md_files(root, exclude=()):
    """migration source 용 md 파일 이터레이터. DB-SoT 코드에서는 사용 안 함."""
    exclude_set = set(exclude)
    for p in Path(root).rglob("*.md"):
        if p.name in exclude_set:
            continue
        if "_projection" in p.parts:
            continue
        try:
            meta, body = parse_record(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        meta["_path"] = p  # migration 전용 — DB-path 코드에서는 없음
        yield meta, body


# ---------- DB 연결 · 스키마 ----------
def _fts_available(con):
    try:
        con.execute("CREATE VIRTUAL TABLE temp.t USING fts5(x)")
        con.execute("DROP TABLE temp.t")
        return True
    except sqlite3.OperationalError:
        return False


def _ensure_schema(con):
    global _FTS_OK, _TRIG_OK
    con.execute("""CREATE TABLE IF NOT EXISTS records(
        id          TEXT PRIMARY KEY,
        tier        TEXT NOT NULL,
        scope       TEXT NOT NULL,
        type        TEXT NOT NULL,
        cwd_origin  TEXT,
        created     TEXT,
        updated     TEXT,
        expires     TEXT,
        source      TEXT,
        tags        TEXT,
        links       TEXT,
        body        TEXT NOT NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_records_scope ON records(scope, cwd_origin, tier)")

    fts = _fts_available(con)
    _FTS_OK = fts
    if fts:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5("
                    "id UNINDEXED, body, tokenize='unicode61')")
        # trigram 보조 테이블 (CJK substring 매칭)
        # MEM_NO_TRIGRAM 테스트 훅: 설정 시 강제 unavailable
        if os.environ.get("MEM_NO_TRIGRAM"):
            _TRIG_OK = False
        else:
            try:
                con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_trig USING fts5("
                            "id UNINDEXED, body, tokenize='trigram')")
                _TRIG_OK = True
            except sqlite3.OperationalError:
                _TRIG_OK = False
    else:
        _TRIG_OK = False


def get_con():
    """DB 접속 단일 진입점. schema 보장 후 반환."""
    STORE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(con)
    return con


# ---------- DB 행 ↔ meta 변환 ----------
def _row_to_meta(row):
    """sqlite3 row tuple → (meta_dict, body). tags/links JSON 디코드."""
    d = dict(zip(RECORD_COLS, row))
    body = d.pop("body")
    # tags / links: 항상 list
    for k in ("tags", "links"):
        v = d.get(k)
        if v is None:
            d[k] = []
        else:
            try:
                d[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                d[k] = []
    return d, body


def _meta_to_params(meta, body):
    """meta dict + body → 12-tuple for INSERT.
    None → NULL passthrough 규칙: expires/source/cwd_origin 은 None → SQL NULL (절대 "" 다운그레이드 X).
    tags/links: 항상 list → JSON 텍스트 (None 이면 []).
    """
    tags = meta.get("tags") or []
    links = meta.get("links") or []
    return (
        meta["id"],
        meta["tier"],
        meta["scope"],
        meta["type"],
        meta.get("cwd_origin"),    # None → SQL NULL
        meta.get("created"),
        meta.get("updated"),
        meta.get("expires"),       # None → SQL NULL
        meta.get("source"),        # None → SQL NULL
        json.dumps(tags, ensure_ascii=False),
        json.dumps(links, ensure_ascii=False),
        body,
    )


def db_iter_records(con=None, where=None, params=()):
    """DB-SoT 핵심 읽기 프리미티브.
    con=None 이면 get_con() 자체 개통; con 전달 시 재사용(새 연결 X).
    """
    own_con = False
    if con is None:
        con = get_con()
        own_con = True
    sql = f"SELECT {', '.join(RECORD_COLS)} FROM records"
    if where:
        sql += f" WHERE {where}"
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        if own_con:
            con.close()
    for row in rows:
        yield _row_to_meta(row)


# ---------- write gate · dedup ----------
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


def find_by_source(tier, scope, rtype, source, con):
    """source-keyed lookup — (tier, scope, type, source) 동일 레코드 id 반환 (없으면 None).
    type 도 매칭 — 같은 source 가 다른 type 행을 cross-overwrite 하는 것 방지 (source↔type 1:1 컨벤션 강제)."""
    if not source:
        return None
    row = con.execute(
        "SELECT id FROM records WHERE tier=? AND scope=? AND type=? AND source=? "
        "ORDER BY rowid DESC LIMIT 1", (tier, scope, rtype, source)).fetchone()
    return row[0] if row else None


def find_dup(tier, scope, body, con=None):
    """dedup 검사. con 전달 시 재사용(write_record 내 단일 트랜잭션 유지)."""
    nb = norm_body(body)
    h = hashlib.sha256(nb.encode()).hexdigest()[:16]
    for meta, b in db_iter_records(con, "tier=? AND scope=?", (tier, scope)):
        if hashlib.sha256(norm_body(b).encode()).hexdigest()[:16] == h:
            return meta["id"]
    return None


def write_record(tier, scope, rtype, body, cwd_origin=None, tags=None, links=None,
                 source=None, quiet=False):
    """DB write 프리미티브. one write = one connection = one transaction."""
    assert tier in TIERS and scope in SCOPES
    ok, why = quality_ok(body)
    if not ok:
        if not quiet:
            print(f"[skip] {why}")
        return None
    body, flags = sanitize(body)

    # 단일 연결로 dedup + INSERT + FTS mirror 를 하나의 트랜잭션으로
    con = get_con()
    try:
        # source-keyed UPSERT: 동일 (tier, scope, type, source) 면 in-place UPDATE (id 보존)
        existing = find_by_source(tier, scope, rtype, source, con)
        if existing:
            # NOTE(🟡-2): in-place UPDATE 는 기존 행의 cwd_origin/created/type/source 를 보존 —
            # cwd_origin 재계산 주입하지 않음 (UPDATE SET 목록에서 의도적으로 제외).
            # NOTE(expires): UPSERT 는 tier 기준 expires 갱신 — working 은 today+TTL 로 수명 연장,
            # 그 외(durable 등)는 None. source-keyed durable(profile)은 모델상 expires=None 이라 NULL 유지
            # (기존 non-null durable expires 보존은 의도적으로 안 함 — 현 모델에 해당 케이스 없음).
            new_expires = None
            if tier == "working":
                new_expires = (datetime.date.today() +
                               datetime.timedelta(days=WORKING_TTL_DAYS)).isoformat()
            con.execute(
                "UPDATE records SET body=?, updated=?, expires=?, tags=?, links=? WHERE id=?",
                (body, today(), new_expires,
                 json.dumps(tags or [], ensure_ascii=False),
                 json.dumps(links or [], ensure_ascii=False), existing))
            if _FTS_OK:
                con.execute("DELETE FROM records_fts WHERE id=?", (existing,))
                con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (existing, body))
            if _TRIG_OK:
                con.execute("DELETE FROM records_trig WHERE id=?", (existing,))
                con.execute("INSERT INTO records_trig(id, body) VALUES(?,?)", (existing, body))
            con.commit()
            if not quiet:
                print(f"[upsert] {tier}/{scope} source={source} → {existing}")
            return existing
        dup = find_dup(tier, scope, body, con=con)
        if dup:
            if not quiet:
                print(f"[dedup] 기존 레코드와 동일 → {dup}")
            return dup
        if cwd_origin is None:
            cwd_origin = enc_cwd(Path.cwd()) if scope == "project" else "global"
        base = slugify(f"{rtype} {body}")
        # FIX 1: tier/scope/cwd_origin 을 해시 seed 에 포함해 namespace 충돌 방지
        # (동일 body+type 이라도 tier/scope 가 다르면 다른 id → INSERT OR REPLACE 가 앞 행 파괴하지 않음)
        seed = f"{tier}|{scope}|{cwd_origin}|{body}|{today()}"
        sid = f"{rtype}_{base}_{hashlib.sha256(seed.encode()).hexdigest()[:6]}"
        meta = {
            "id": sid, "tier": tier, "scope": scope, "type": rtype,
            "cwd_origin": cwd_origin, "created": today(), "updated": today(),
            "tags": tags or [], "links": links or [],
            "expires": None, "source": source,
        }
        if tier == "working":
            meta["expires"] = (datetime.date.today() +
                               datetime.timedelta(days=WORKING_TTL_DAYS)).isoformat()

        con.execute(
            f"INSERT OR REPLACE INTO records VALUES({','.join(['?']*12)})",
            _meta_to_params(meta, body)
        )
        # FTS mirror: replace 시 중복 행 방지 → DELETE 후 INSERT
        if _FTS_OK:
            con.execute("DELETE FROM records_fts WHERE id=?", (sid,))
            con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (sid, body))
        if _TRIG_OK:
            con.execute("DELETE FROM records_trig WHERE id=?", (sid,))
            con.execute("INSERT INTO records_trig(id, body) VALUES(?,?)", (sid, body))
        con.commit()
        if not quiet:
            fl = f"  ({'·'.join(flags)})" if flags else ""
            print(f"[write] {tier}/{scope}/{rtype} → {sid}{fl}")
        return sid
    finally:
        con.close()


# ---------- index ----------
def index_build(rebuild=False):
    """FTS 가상테이블을 records 테이블에서 재구축. 별도 .index.db 없음(DB 내장)."""
    global _FTS_OK, _TRIG_OK
    con = get_con()
    try:
        if rebuild:
            con.execute("DROP TABLE IF EXISTS records_fts")
            if _TRIG_OK is not False:  # 있을 수 있으면 시도
                try:
                    con.execute("DROP TABLE IF EXISTS records_trig")
                except Exception:
                    pass
            # 재생성
            _ensure_schema(con)
        # records 에서 FTS 재채우기
        n = 0
        if _FTS_OK:
            con.execute("DELETE FROM records_fts")
            if _TRIG_OK:
                con.execute("DELETE FROM records_trig")
            rows = con.execute("SELECT id, body FROM records").fetchall()
            for rid, body in rows:
                con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (rid, body))
                if _TRIG_OK:
                    con.execute("INSERT INTO records_trig(id, body) VALUES(?,?)", (rid, body))
                n += 1
        else:
            n = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        con.commit()
    finally:
        con.close()
    print(f"[index] {n} records  (FTS5={'on' if _FTS_OK else 'off, LIKE fallback'})")
    return n


# ---------- recall ----------
def _has_cjk(s):
    return bool(re.search(r"[　-鿿가-힯]", s))


def recall(query, tier=None, scope=None, cwd=None, sessions=False, limit=20):
    print(f"# recall: \"{query}\"  [tier={tier or '*'} scope={scope or '*'} "
          f"cwd={'현재' if cwd else '전체'}]")
    hits = []
    if not DB.exists():
        print("(store 없음 — mem index 또는 mem sync 먼저)")
        if sessions:
            print(f"\n# raw 세션 transcript: \"{query}\"  (미정제)")
            _recall_sessions(query, cwd)
        return hits

    con = get_con()
    try:
        encc = enc_cwd(Path.cwd()) if cwd else None

        # WHERE 절 구성
        def build_where(base_cond=None):
            conds, p = [], []
            if base_cond:
                conds.append(base_cond[0]); p.extend(base_cond[1])
            if tier:
                conds.append("r.tier=?"); p.append(tier)
            if scope:
                conds.append("r.scope=?"); p.append(scope)
            if encc:
                conds.append("(r.scope='global' OR r.cwd_origin=?)"); p.append(encc)
            return (" AND ".join(conds) if conds else "1"), p

        has_fts = con.execute(
            "SELECT name FROM sqlite_master WHERE name='records_fts'").fetchone()

        def _fts_literal(q):
            """FTS5 연산자(NEAR/*/:/"등) 가 query 에 포함돼도 리터럴 phrase 로 처리.
            FIX 4: raw query 를 MATCH 에 그대로 넘기면 FTS5 query 문법이 적용돼 무음 오검색 발생."""
            return '"' + q.replace('"', '""') + '"'

        if has_fts:
            try:
                where, params = build_where(("records_fts MATCH ?", [_fts_literal(query)]))
                sql = (f"SELECT r.id, r.tier, r.scope, r.type, r.cwd_origin, "
                       f"snippet(records_fts,1,'»','«','…',12) "
                       f"FROM records_fts f JOIN records r ON r.id=f.id "
                       f"WHERE {where} ORDER BY bm25(records_fts) LIMIT ?")
                rows = con.execute(sql, params + [limit * 3]).fetchall()
                seen_ids = {r[0] for r in rows}

                # CJK boost via trigram
                if _has_cjk(query) and _TRIG_OK:
                    has_trig = con.execute(
                        "SELECT name FROM sqlite_master WHERE name='records_trig'").fetchone()
                    if has_trig:
                        try:
                            where2, params2 = build_where(("records_trig MATCH ?", [_fts_literal(query)]))
                            sql2 = (f"SELECT r.id, r.tier, r.scope, r.type, r.cwd_origin, "
                                    f"snippet(records_trig,1,'»','«','…',12) "
                                    f"FROM records_trig t JOIN records r ON r.id=t.id "
                                    f"WHERE {where2} ORDER BY bm25(records_trig) LIMIT ?")
                            trig_rows = con.execute(sql2, params2 + [limit * 3]).fetchall()
                            for tr in trig_rows:
                                if tr[0] not in seen_ids:
                                    rows.append(tr)
                                    seen_ids.add(tr[0])
                        except sqlite3.OperationalError:
                            pass
                elif _has_cjk(query) and not _TRIG_OK:
                    # trigram 불가 → LIKE fallback for CJK
                    where_l, params_l = build_where()
                    where_l = (where_l + " AND r.body LIKE ?") if where_l != "1" else "r.body LIKE ?"
                    sql_l = (f"SELECT r.id, r.tier, r.scope, r.type, r.cwd_origin, "
                             f"substr(r.body,1,160) FROM records r "
                             f"WHERE {where_l} LIMIT ?")
                    like_rows = con.execute(sql_l, params_l + [f"%{query}%", limit * 3]).fetchall()
                    for lr in like_rows:
                        if lr[0] not in seen_ids:
                            rows.append(lr)
                            seen_ids.add(lr[0])
            except sqlite3.OperationalError:
                # FTS MATCH 실패 시 LIKE fallback
                where_l, params_l = build_where()
                where_l = (where_l + " AND r.body LIKE ?") if where_l != "1" else "r.body LIKE ?"
                sql_l = (f"SELECT r.id, r.tier, r.scope, r.type, r.cwd_origin, "
                         f"substr(r.body,1,160) FROM records r WHERE {where_l} LIMIT ?")
                rows = con.execute(sql_l, params_l + [f"%{query}%", limit * 3]).fetchall()
        else:
            # FTS 없음 → LIKE
            where_l, params_l = build_where()
            where_l = (where_l + " AND r.body LIKE ?") if where_l != "1" else "r.body LIKE ?"
            sql_l = (f"SELECT r.id, r.tier, r.scope, r.type, r.cwd_origin, "
                     f"substr(r.body,1,160) FROM records r WHERE {where_l} LIMIT ?")
            rows = con.execute(sql_l, params_l + [f"%{query}%", limit * 3]).fetchall()
    finally:
        con.close()

    for rid, rt, rs, rtype, cwd_orig, snip in rows[:limit]:
        hits.append((rt, rs, rtype, rid, snip.replace("\n", " ")))

    if not hits:
        print("(store 매칭 없음)")
    for rt, rs, rtype, rid, snip in hits:
        print(f"  [{rt}/{rs}/{rtype}] {rid}: {snip}")
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


# ---------- export / import ----------
def export_dump(target_path=None):
    """DB → dump.jsonl (git mirror). 결정론적: id 정렬 + sort_keys + 12 컬럼 전부."""
    dest = Path(target_path) if target_path else DUMP
    con = get_con()
    try:
        sql = f"SELECT {', '.join(RECORD_COLS)} FROM records ORDER BY id"
        rows = con.execute(sql).fetchall()
    finally:
        con.close()

    tmp = dest.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            rec = {}
            for k, v in zip(RECORD_COLS, row):
                if k in ("tags", "links"):
                    rec[k] = json.loads(v) if v else []
                else:
                    rec[k] = v  # None → JSON null (sort_keys 출력에서도 null)
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(tmp, dest)
    print(f"[export] {len(rows)} records → {dest.name}")
    return len(rows)


def import_dump(path):
    """dump.jsonl → DB 완전 복원 (exact restore).
    FIX 2: 기존 records 를 먼저 DELETE 한 뒤 dump 를 replay → dump 상태와 1:1 일치.
    stale 행(덤프에 없는 행) 자동 소거. NULL round-trip: JSON null → Python None → SQL NULL.
    FTS 재구축도 같은 connection 안에서 수행(nested 2nd connection DDL 충돌 제거).
    """
    global _FTS_OK, _TRIG_OK
    path = Path(path)
    con = get_con()
    n = 0
    try:
        # exact restore: 기존 records + FTS mirror 를 완전히 비우고 replay
        con.execute("DELETE FROM records")
        if _FTS_OK:
            con.execute("DELETE FROM records_fts")
        if _TRIG_OK:
            try:
                con.execute("DELETE FROM records_trig")
            except Exception:
                pass

        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                # body 꺼내기
                body = rec.get("body", "")
                meta = {k: rec.get(k) for k in RECORD_COLS if k != "body"}
                # tags/links: JSON null → [] 로 보정 (list 보장)
                for k in ("tags", "links"):
                    if meta[k] is None:
                        meta[k] = []
                con.execute(
                    f"INSERT OR REPLACE INTO records VALUES({','.join(['?']*12)})",
                    _meta_to_params(meta, body)
                )
                rid = meta.get("id", "")
                if _FTS_OK:
                    con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (rid, body))
                if _TRIG_OK:
                    try:
                        con.execute("INSERT INTO records_trig(id, body) VALUES(?,?)", (rid, body))
                    except Exception:
                        pass
                n += 1
        con.commit()
    finally:
        con.close()
    print(f"[import] {n} records ← {Path(path).name}")
    return n


# ---------- 공유 aspect 추출 규칙 (export_profile + inject 공용) ----------
def _derive_aspect(meta, body):
    """profile 레코드에서 aspect 이름 추출.
    우선순위: source=user-profile:<stem> → <stem>
              body의 aspect: 마커 → 그 값
              마지막 수단: meta["id"]
    해석 불가 → None (호출자가 [skip] 처리).
    """
    src = meta.get("source") or ""
    if src.startswith("user-profile:"):
        stem = src[len("user-profile:"):]
        if stem:
            return stem
    # body aspect: 마커
    for line in body.splitlines():
        if line.startswith("aspect:"):
            val = line.split(":", 1)[1].strip()
            if val:
                return val
    return None  # 해석 불가


def export_profile(apply=False):
    """profile 레코드 → user_profile/*.md 생성.
    기본 dry-run (print 만). apply=True 이고 MEM_PROFILE 오버라이드 시만 실제 파일 write.

    IMPORTANT: --apply 없이는 디스크에 아무것도 쓰지 않습니다.
    """
    con = get_con()
    try:
        records = list(db_iter_records(con, "type='profile'"))
    finally:
        con.close()

    written, skipped = 0, 0
    for meta, body in records:
        aspect = _derive_aspect(meta, body)
        if aspect is None:
            print(f"[skip] aspect unknown: {meta['id']}")
            skipped += 1
            continue
        dest = USER_PROFILE / f"{aspect}.md"
        first_line = body.splitlines()[0][:80] if body.splitlines() else ""
        if not apply:
            print(f"[dry-run] → {dest}  ({first_line})")
        else:
            # FIX 3: MEM_PROFILE 환경변수 미설정 시 실 ~/.claude/user_profile 보호
            if "MEM_PROFILE" not in os.environ:
                print("[abort] export --target profile --apply 는 MEM_PROFILE 명시 설정 필요 (실 ~/.claude/user_profile 보호)")
                return
            USER_PROFILE.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
            print(f"[profile] → {dest}")
            written += 1
    if not apply:
        print(f"[dry-run] {len(records)-skipped}개 예정 · skip {skipped}  (--apply 없으면 미기록)")
    else:
        print(f"[profile] {written}개 생성 · skip {skipped}")


# ---------- profile (read-only) ----------
def profile(aspect, list_mode=False):
    """DB type=profile 레코드의 aspect body 를 stdout 으로 출력.

    READ-ONLY INVARIANT: 이 함수는 zero RECORD writes (write_record 호출 없음 / con.commit 없음).
    get_con() 의 schema-ensure (CREATE TABLE/INDEX IF NOT EXISTS) 는 멱등 실행되어 데이터를 변경하지 않는다.

    aspect 해석 우선순위 (first-match wins):
      (a) 완전 stem 일치  (b) 숫자 prefix 2자리 일치  (c) alias (collision-checked)
    ambiguous alias 는 stderr + sys.exit(2). no-match 도 stderr + sys.exit(2).
    """
    # rowid 를 명시적으로 읽어야 한다 — db_iter_records 는 RECORD_COLS 만 SELECT 하므로
    # rowid 가 포함되지 않음. 별도 쿼리로 (rowid, meta, body) 를 취득한다.
    cols = ", ".join(RECORD_COLS)
    con = get_con()
    try:
        rows_raw = con.execute(
            f"SELECT rowid, {cols} FROM records WHERE type='profile'"
        ).fetchall()
    finally:
        con.close()

    # (rowid, meta, body) 튜플 리스트로 변환
    rows = []
    for r in rows_raw:
        rowid = r[0]
        meta, body = _row_to_meta(r[1:])   # r[1:] 이 RECORD_COLS 순 tuple
        rows.append((rowid, meta, body))

    # 결정론적 newest-wins tie-break: created DESC, rowid DESC (단조 삽입 순)
    # — db_iter_records 에 ORDER BY 없음 (line 227), VACUUM 후 row 순서 보장 안됨.
    # — id 는 body-slug+hash 라 lexical 정렬 시 stale body 가 이길 수 있음 (🟡-A).
    # — rowid 는 단조증가 INSERT 순서이므로 same-day 업데이트도 정확히 최신을 선택.
    rows.sort(key=lambda r: (r[1].get("created", ""), r[0]), reverse=True)

    # stem → (meta, body) 사전: setdefault 로 최신(첫 번째) 행만 등록
    lookup = {}
    for rowid, meta, body in rows:
        stem = _derive_aspect(meta, body)
        if stem is None:
            continue
        lookup.setdefault(stem, (meta, body))

    stems = sorted(lookup.keys())

    # ── alias 맵 빌드 (deterministic, DB 기반 — 하드코딩 금지) ──────────────────
    # 각 stem 의 suffix = 숫자 prefix 제거 후 나머지 토큰들
    # (e.g. "01_paper_figure_style" → ["paper","figure","style"])
    # primary alias = suffix 토큰 중 전체 7 stem 의 토큰 multiset 에서 유일한 첫 토큰.
    # alias→[stems] 맵: full_suffix + 각 개별 토큰 모두 후보로 등록.
    # 해석: "ambiguous aliases error out, unambiguous ones resolve"
    # (충돌 없음을 보장하는 게 아니라, 충돌 시 오류 처리)

    def _suffix_tokens(stem):
        """'07_coding_convention' → ['coding','convention']"""
        s = re.sub(r"^\d+_", "", stem)
        return s.split("_") if s else []

    # 전체 토큰 multiset: 각 토큰이 몇 개의 stem 에 나타나는지
    token_to_stems = {}
    for stem in stems:
        for tok in _suffix_tokens(stem):
            token_to_stems.setdefault(tok, [])
            if stem not in token_to_stems[tok]:
                token_to_stems[tok].append(stem)
    # full suffix 도 후보 (e.g. "coding_convention")
    for stem in stems:
        suf = re.sub(r"^\d+_", "", stem)
        if suf:
            token_to_stems.setdefault(suf, [])
            if stem not in token_to_stems[suf]:
                token_to_stems[suf].append(stem)

    # primary alias per stem: suffix 토큰 왼쪽부터 순회, 첫 유일 토큰
    stem_to_alias = {}
    for stem in stems:
        for tok in _suffix_tokens(stem):
            if len(token_to_stems.get(tok, [])) == 1:
                stem_to_alias[stem] = tok
                break

    # ── --list 모드 ────────────────────────────────────────────────────────────
    if list_mode:
        for stem in stems:
            alias_label = stem_to_alias.get(stem, "-")
            _, body = lookup[stem]
            print(f"{stem}  [{alias_label}]  {len(body)} chars")
        sys.exit(0)

    # ── aspect 없이 --list 도 없으면 오류 ──────────────────────────────────────
    if aspect is None:
        sys.stderr.write("가용 aspect 목록:\n")
        for stem in stems:
            alias_label = stem_to_alias.get(stem, "-")
            sys.stderr.write(f"  {stem}  [{alias_label}]\n")
        sys.exit(2)

    # ── aspect 해석: (a) exact stem  (b) numeric prefix  (c) alias ────────────
    resolved = None

    # (a) 완전 stem 일치
    if aspect in lookup:
        resolved = aspect

    # (b) 숫자 prefix 2자리 일치 (e.g. "07" → "07_coding_convention")
    if resolved is None and re.fullmatch(r"\d{2}", aspect):
        for stem in stems:
            if stem.startswith(aspect + "_") or stem == aspect:
                resolved = stem
                break

    # (c) alias 일치 (collision-checked convenience path)
    if resolved is None:
        candidates = token_to_stems.get(aspect, [])
        if len(candidates) == 1:
            resolved = candidates[0]
        elif len(candidates) > 1:
            sys.stderr.write(
                f"[profile] 모호한 alias '{aspect}' — 후보 stems:\n"
            )
            for c in sorted(candidates):
                sys.stderr.write(f"  {c}\n")
            sys.exit(2)

    # ── 매칭 없음 ──────────────────────────────────────────────────────────────
    if resolved is None:
        sys.stderr.write(f"[profile] aspect '{aspect}' 를 찾을 수 없습니다. 가용 목록:\n")
        for stem in stems:
            alias_label = stem_to_alias.get(stem, "-")
            sys.stderr.write(f"  {stem}  [{alias_label}]\n")
        sys.exit(2)

    _, body = lookup[resolved]
    print(body)
    sys.exit(0)


# ---------- migrate ----------
def migrate(apply=False):
    print(f"# migrate  ({'APPLY' if apply else 'dry-run'})")
    created, skipped = 0, 0

    # 멱등성 키: DB에 이미 있는 source 값
    if DB.exists():
        con = get_con()
        try:
            rows = con.execute(
                "SELECT DISTINCT source FROM records WHERE source IS NOT NULL").fetchall()
            existing_src = {r[0] for r in rows}
        finally:
            con.close()
    else:
        existing_src = set()

    # 1) auto-memory: projects/<cwd>/memory/*.md
    try:
        for mp in PROJECTS.glob("*/memory/*.md"):
            if mp.name == "MEMORY.md":
                continue
            src = f"auto-memory:{mp.parent.parent.name}/{mp.name}"
            if src in existing_src:
                skipped += 1
                continue
            try:
                meta, body = parse_record(mp.read_text(encoding="utf-8"))
                rtype = meta.get("type", "project")
                scope = "global" if rtype == "user" else "project"
                cwd_origin = mp.parent.parent.name
                if apply:
                    write_record("durable", scope, rtype, body, cwd_origin=cwd_origin,
                                 source=src, quiet=True)
                created += 1
            except Exception as e:
                sys.stderr.write(f"[migrate] skip {mp}: {e}\n")
                continue
    except Exception as e:
        sys.stderr.write(f"[migrate] auto-memory source 실패(계속): {e}\n")

    # 2) post-it: 레지스트리 + 현 cwd
    POST_SECT = {"Open Threads": "thread", "Decisions": "decision",
                 "Next Session Hints": "hint", "Conventions": "convention",
                 "External Resources": "reference"}
    try:
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
            try:
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
            except Exception as e:
                sys.stderr.write(f"[migrate] skip {pi}: {e}\n")
                continue
    except Exception as e:
        sys.stderr.write(f"[migrate] post-it source 실패(계속): {e}\n")

    # 3) user_profile/*.md → durable/global/profile
    try:
        if USER_PROFILE.exists():
            for up in sorted(USER_PROFILE.glob("*.md")):
                if up.name == "README.md":
                    continue
                src = f"user-profile:{up.stem}"
                if src in existing_src:
                    skipped += 1
                    continue
                try:
                    if apply:
                        write_record("durable", "global", "profile",
                                     up.read_text(encoding="utf-8", errors="ignore"),
                                     cwd_origin="global", source=src, quiet=True)
                    created += 1
                except Exception as e:
                    sys.stderr.write(f"[migrate] skip {up}: {e}\n")
                    continue
    except Exception as e:
        sys.stderr.write(f"[migrate] user_profile source 실패(계속): {e}\n")

    # 4) 구 markdown SoT: STORE/**/*.md (iter_md_files)
    try:
        for meta, body in iter_md_files(STORE, exclude={"MEMORY.md", "README.md"}):
            p = meta.get("_path", Path(""))
            # memory.db / dump.jsonl 등 비md 는 glob 에서 제외됨. _projection 디렉토리도 제외됨.
            rel = str(p.relative_to(STORE)) if p and STORE in p.parents else str(p)
            src = f"md-file:{rel}"
            if src in existing_src:
                skipped += 1
                continue
            try:
                if meta.get("id"):
                    # 구 SoT 레코드 — tier/scope/type/cwd_origin 보존
                    rid_tier = meta.get("tier", "durable")
                    rid_scope = meta.get("scope", "project")
                    rid_type = meta.get("type", "project")
                    rid_cwd = meta.get("cwd_origin")
                    if apply:
                        write_record(rid_tier, rid_scope, rid_type, body,
                                     cwd_origin=rid_cwd, source=src, quiet=True)
                else:
                    # frontmatter 없는 md → durable/project note
                    if apply:
                        write_record("durable", "project", "project", body,
                                     source=src, quiet=True)
                created += 1
            except Exception as e:
                sys.stderr.write(f"[migrate] skip md-file {rel}: {e}\n")
                continue
    except Exception as e:
        sys.stderr.write(f"[migrate] md-file source 실패(계속): {e}\n")

    print(f"  → {'생성' if apply else '생성 예정'} {created} · 기존 skip {skipped}")
    return created


# ---------- lifecycle ----------
def lifecycle(apply=False):
    print(f"# lifecycle  ({'APPLY' if apply else 'report'})")
    con = get_con()
    try:
        # 만료된 working 레코드
        expired_rows = list(db_iter_records(
            con, "tier='working' AND expires IS NOT NULL AND expires < ?", (today(),)))
        # durable near-dup 플래깅
        seen = {}
        for meta, body in db_iter_records(con):
            key = (meta.get("tier"), meta.get("scope"), norm_body(body)[:80])
            seen.setdefault(key, []).append(meta["id"])
        dups = [ids for ids in seen.values() if len(ids) > 1]

        for meta, body in expired_rows:
            print(f"  [expire] {meta['id']} (expires {meta.get('expires')})")
            if apply:
                try:
                    con.execute("DELETE FROM records WHERE id=?", (meta["id"],))
                    if _FTS_OK:
                        con.execute("DELETE FROM records_fts WHERE id=?", (meta["id"],))
                    if _TRIG_OK:
                        con.execute("DELETE FROM records_trig WHERE id=?", (meta["id"],))
                except Exception as e:
                    sys.stderr.write(f"[lifecycle] 삭제 실패(계속): {meta['id']}: {e}\n")
        if apply:
            con.commit()

        for ids in dups:
            print(f"  [dup-flag] {ids}  (consolidate 후보 — 자동삭제 X)")

        print(f"  → 만료 {len(expired_rows)}{'(삭제)' if apply else ''} · dup-flag {len(dups)}")
    finally:
        con.close()
    return [m for m, _ in expired_rows], dups


# ---------- delete ----------
def delete_record(rid, quiet=False):
    """단건 결정론 삭제 — records + FTS + trig 3-table DELETE (lifecycle 만료 로직 재사용)."""
    con = get_con()
    try:
        row = con.execute("SELECT id FROM records WHERE id=?", (rid,)).fetchone()
        if not row:
            if not quiet:
                print(f"[delete] id 없음: {rid}")
            return False
        con.execute("DELETE FROM records WHERE id=?", (rid,))
        if _FTS_OK:
            con.execute("DELETE FROM records_fts WHERE id=?", (rid,))
        if _TRIG_OK:
            try:
                con.execute("DELETE FROM records_trig WHERE id=?", (rid,))
            except Exception as e:
                sys.stderr.write(f"[delete] trig 미러 삭제 실패(계속): {rid}: {e}\n")
        con.commit()
        if not quiet:
            print(f"[delete] {rid}")
        return True
    finally:
        con.close()


# ---------- projection ----------
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
    for meta, body in db_iter_records(
            None, "(scope='global' OR cwd_origin=?)", (encc,)):
        (proj / f"{meta['id']}.md").write_text(
            serialize_record(meta, body), encoding="utf-8")
        idx.append(f"- [{meta['id']}](_projection/{meta['id']}.md) "
                   f"[{meta.get('tier')}/{meta.get('type')}]")
        n += 1
    (dest / "MEMORY.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"[project] {n} records → {dest}")
    return n


def stats():
    print("# store stats")
    if not DB.exists():
        print(f"  (DB 없음: {DB})")
        return
    con = get_con()
    try:
        rows = con.execute(
            "SELECT tier, scope, COUNT(*) FROM records GROUP BY tier, scope").fetchall()
    finally:
        con.close()
    total = 0
    for t, s, n in sorted(rows):
        print(f"  {t}/{s}: {n}")
        total += n
    print(f"  total: {total}  ({STORE}/memory.db)")


def register_postit(path):
    """post-it.md 경로를 레지스트리에 등록."""
    STORE.mkdir(parents=True, exist_ok=True)
    reg = STORE / ".postit-roots"
    p = str(Path(path).resolve())
    # FIX 5: strip 후 비교 — trailing newline·CRLF·빈 줄 혼입 시 중복 등록 방지
    existing = {l.strip() for l in reg.read_text(encoding="utf-8").splitlines() if l.strip()} if reg.exists() else set()
    if p in existing:
        print(f"[register] 이미 등록: {p}")
        return
    try:
        with reg.open("a", encoding="utf-8") as f:
            f.write(p + "\n")
    except Exception as e:
        sys.stderr.write(f"[register] 레지스트리 write 실패: {e}\n")
        return
    print(f"[register] {p}")


# ---------- inject ----------
def _first_line(body):
    for l in body.splitlines():
        s = l.strip()
        if s and not s.startswith("---") and not s.startswith("#"):
            return s
    return body.strip()[:160]


def inject(max_working=40, max_durable=40, hook=False):
    """SessionStart 주입용 — DB 에서 working(cwd) + durable/project(cwd) + profile(global) 블록.
    hook=True 면 settings.json SessionStart additionalContext JSON 으로 감싼다.
    """
    def emit(block):
        if hook:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                     "additionalContext": block}},
                              ensure_ascii=False))
        else:
            print(block)

    if not DB.exists():
        return

    con = get_con()
    try:
        encc = enc_cwd(Path.cwd())
        # profile: rowid 를 명시적으로 SELECT — db_iter_records 는 RECORD_COLS 만 반환해 rowid 미포함.
        # profile() 의 newest-wins 로직과 동일하게 per-stem dedup 적용 (read-side coherence).
        cols = ", ".join(RECORD_COLS)
        prof_raw = con.execute(
            f"SELECT rowid, {cols} FROM records WHERE type='profile'"
        ).fetchall()
        work = list(db_iter_records(
            con, "tier='working' AND cwd_origin=? AND (expires IS NULL OR expires >= ?)",
            (encc, today())))
        dur  = list(db_iter_records(
            con, "tier='durable' AND scope='project' AND cwd_origin=? AND (expires IS NULL OR expires >= ?)",
            (encc, today())))
    finally:
        con.close()

    # profile newest-wins dedup: (rowid, meta, body) 로 변환 후 created DESC, rowid DESC 정렬,
    # stem → first-seen(newest) 기록. profile() 과 동일 로직 — 두 read path 가 같은 body 를 쓰도록.
    prof_rows = []
    for r in prof_raw:
        rowid = r[0]
        meta, body = _row_to_meta(r[1:])
        prof_rows.append((rowid, meta, body))
    prof_rows.sort(key=lambda r: (r[1].get("created", ""), r[0]), reverse=True)
    prof_lookup = {}  # stem → (meta, body) newest-only
    for rowid, meta, body in prof_rows:
        stem = _derive_aspect(meta, body)
        if stem is None:
            # aspect 해석 불가 레코드: 기존 동작 그대로 포함 (id 를 aspect 로)
            prof_lookup.setdefault(meta["id"], (meta, body))
        else:
            prof_lookup.setdefault(stem, (meta, body))
    prof = list(prof_lookup.items())  # [(aspect_key, (meta, body))]

    if not (work or dur or prof):
        return

    out = ["# 🧠 통합 기억 (mem store — 세션 시작 주입)", ""]
    if work:
        out.append("## 단기 작업기억 (working — 이 프로젝트, 자동 만료)")
        for m, b in sorted(work, key=lambda x: x[0].get("updated", ""), reverse=True)[:max_working]:
            out.append(f"- {_first_line(b)[:180]}")
        out.append("")
    if dur:
        out.append("## 장기 — 이 프로젝트 (durable)")
        for m, b in sorted(dur, key=lambda x: x[0].get("updated", ""), reverse=True)[:max_durable]:
            out.append(f"- [{m.get('type')}] {_first_line(b)[:160]}")
        out.append("")
    if prof:
        out.append("## 장기 — 사용자 특성 (user profile)")
        for aspect_key, (m, b) in prof:
            out.append(f"- {aspect_key}: {_first_line(b)[:140]}")
        out.append("")
    out.append("> 상세 회상: `bash ~/.claude/tools/memory/recall.sh \"<query>\"` (store+세션 전체 FTS)")
    emit("\n".join(out))


# ---------- sync ----------
def sync():
    """SessionEnd: auto-memory → DB migrate + FTS 재구축 + dump.jsonl 재export."""
    print("# sync (projects → store mirror)")
    n = 0
    try:
        n = migrate(apply=True)
    except Exception as e:
        sys.stderr.write(f"[sync] migrate 실패(계속): {e}\n")
    try:
        lifecycle(apply=True)
    except Exception as e:
        sys.stderr.write(f"[sync] lifecycle 실패(계속): {e}\n")
    try:
        index_build(rebuild=True)
    except Exception as e:
        sys.stderr.write(f"[sync] index 실패: {e}\n")
    try:
        export_dump()
    except Exception as e:
        sys.stderr.write(f"[sync] export 실패(계속): {e}\n")
    return n


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(prog="mem", description="Unified Memory System")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="수동 기록")
    a.add_argument("tier", choices=TIERS)
    a.add_argument("type")
    a.add_argument("body")
    a.add_argument("--scope", choices=SCOPES, default="project")
    a.add_argument("--tags", default="")
    a.add_argument("--links", default="")
    a.add_argument("--cwd-origin")
    a.add_argument("--source", default=None)

    n = sub.add_parser("note", help="working tier 단축 기록")
    n.add_argument("body")
    n.add_argument("--type", default="thread")

    r = sub.add_parser("recall", help="회상")
    r.add_argument("query")
    r.add_argument("--tier", choices=TIERS)
    r.add_argument("--scope", choices=SCOPES)
    r.add_argument("--all", action="store_true", help="전 cwd (default: 현 cwd)")
    r.add_argument("--sessions", action="store_true")

    ix = sub.add_parser("index", help="FTS5 색인")
    ix.add_argument("--rebuild", action="store_true")

    pj = sub.add_parser("project", help="주입 projection")
    pj.add_argument("--cwd")

    mg = sub.add_parser("migrate", help="post-it+auto-memory+md파일 이주")
    mg.add_argument("--apply", action="store_true")

    lc = sub.add_parser("lifecycle", help="working 만료·졸업 / durable dup")
    lc.add_argument("--apply", action="store_true")

    dl = sub.add_parser("delete", help="단건 결정론 삭제 (records+FTS 3-table)")
    dl.add_argument("id")

    sub.add_parser("stats", help="store 통계")
    sub.add_parser("sync", help="projects→store 멱등 mirror + 색인 + dump (SessionEnd)")

    ij = sub.add_parser("inject", help="SessionStart 주입 블록")
    ij.add_argument("--hook", action="store_true", help="SessionStart additionalContext JSON")

    rp = sub.add_parser("register-postit", help="post-it.md 경로 레지스트리 등록")
    rp.add_argument("path")

    ex = sub.add_parser("export", help="DB → dump.jsonl 또는 profile md")
    ex.add_argument("--target", choices=["dump", "profile"], default="dump")
    ex.add_argument("--apply", action="store_true", help="profile 실제 파일 write (기본 dry-run)")

    im = sub.add_parser("import", help="dump.jsonl → DB 복원")
    im.add_argument("path")

    pf = sub.add_parser("profile", help="DB type=profile 레코드의 aspect body 출력 (read-only)")
    pf.add_argument("aspect", nargs="?", help="stem '07_coding_convention' / 숫자 '07' / alias 'coding'")
    pf.add_argument("--list", action="store_true", help="가용 aspect 목록 (stem + 라벨 + body 길이); aspect 인자 무시 — 전체 목록 출력")

    args = ap.parse_args()

    if args.cmd == "add":
        write_record(
            args.tier, args.scope, args.type, args.body,
            cwd_origin=args.cwd_origin,
            tags=[t for t in args.tags.split(",") if t],
            links=[l for l in args.links.split(",") if l],
            source=args.source,
        )
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
    elif args.cmd == "delete":
        delete_record(args.id)
    elif args.cmd == "stats":
        stats()
    elif args.cmd == "sync":
        sync()
    elif args.cmd == "inject":
        inject(hook=args.hook)
    elif args.cmd == "register-postit":
        register_postit(args.path)
    elif args.cmd == "export":
        if args.target == "dump":
            export_dump()
        else:
            export_profile(apply=args.apply)
    elif args.cmd == "import":
        import_dump(args.path)
    elif args.cmd == "profile":
        profile(args.aspect, list_mode=args.list)


if __name__ == "__main__":
    main()
