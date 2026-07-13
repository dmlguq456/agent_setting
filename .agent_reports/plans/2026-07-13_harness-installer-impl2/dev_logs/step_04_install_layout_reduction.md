# Phase 4 — `INSTALL_LAYOUT.md` reduction (INST-OPEN-3)

**File changed**: `INSTALL_LAYOUT.md` (514 → 225 lines).

## Implementation (matches plan Step 4.1–4.3)

- **Header note (4.3)**: added a blockquote at the top stating the manual
  recipe/verification is superseded by `harness install`/`harness verify`,
  pointing at the PRD as the SoT for the surface×channel matrix and
  plugin-channel per-runtime spec, and noting this doc keeps only its own
  local facts (Windows specifics, fleet contract) plus a summary.
- **4.1 Projection sections** — Claude/Codex/OpenCode:
  - Removed every copy-pasteable `ln -sfn ...` enumeration and replaced each
    with a one-line `harness install <runtime>` call.
  - Replaced the removed recipe with a **"Contract, not recipe"** table per
    runtime (표면 → 배선 → 계약) that keeps every why/contract fact the plan
    called out to preserve: Claude's copy-once rationale (atomic settings
    writes replace a symlink, so link-once-never-relink), Claude plugin's
    INST-D-5 parity note (plugin can't carry general settings keys, so
    symlink projection always runs alongside `--plugin`), Codex's "plugin
    can't carry agents .toml/prompts/config fragment/AGENTS.md → symlink
    projection still required" note, Codex's statusline
    `config.toml`-is-runtime-owned / fragment-only note, OpenCode's
    non-destructive-merge behavior and the INST-OPEN-4 plural-dir drift
    caveat (kept verbatim as its own callout, explicitly marked "이 사이클
    미변경" — plan's explicit out-of-scope item, not silently dropped).
  - Windows Projection (46-86 in the old numbering) and the fleet CLI section
    (87-103) were **left substantively unchanged** — the plan only asked to
    replace the `ln -sfn` *pointer-recipe* enumerations in the
    Claude/Codex/OpenCode projection sections, not the Windows-specific
    install-windows.sh delegate call or the fleet launcher symlink (both are
    already single-purpose commands, not per-runtime lists, and plan Step
    4.1 explicitly scoped the replacement to "the literal `ln -sfn
    $AGENT_HOME/..._setting/$p ~/.<rt>/$p` recipe lists"). Added one
    sentence noting `harness install claude` now invokes the Windows
    delegate automatically, since that's a genuine behavior fact from the
    Phase 2/cycle-1 driver, not scope creep.
- **4.2 Migration Order (239-514)** — replaced the ~275-line manual
  verification battery (the enormous `preflight.sh`/`rg`/`test` command
  block) with a "Migration / Verification" section: `harness install
  [runtime]` + `harness verify [runtime] --json` as the mechanized
  replacement, plus prose-only invariants that are contract facts, not
  runnable steps:
  - **Exit code table** (0/1/2/3/4/64) sourced from
    `tools/install/installer.py`'s `EXIT_*` constants and the PRD `[cli]`
    "### Exit code" table — confirmed the PRD explicitly documents exit `3`
    (BLOCKED) as "대상 런타임 프로세스 활성 등 안전 정지 (INSTALL_LAYOUT
    Migration Order 2 계승)", i.e. the PRD itself names the *old* Migration
    Order step 2 ("stop long-running runtime processes first") as exit 3's
    lineage — so this is the one Migration Order fact that had to survive
    as prose, per the plan's explicit callout. Verified by reading
    `tools/install/installer.py` L33-37 and
    `.agent_reports/spec/harness-installer/prd.md` L58-67 directly rather
    than assuming from the plan's paraphrase.
  - "never overwrite runtime-owned state" (the `status:"blocked"` refusal
    behavior already implemented in `drivers/claude.py`/`drivers/codex.py`).
  - hash-manifest drift handling (copied files only, symlinks/plugin cache
    excluded, `local-patches/` backup + `--reapply`, 3-way conflict reported
    not auto-merged) — restated from the removed section's implicit
    behavior, now stated as a standing contract rather than embedded in a
    step-by-step recipe.
  - Plugin registration checks are always read-only — ties back to Phase 3's
    `_plugin_registered` design (never calls `marketplace add`/`plugin
    install` from `checks()`).
  - Runtime-currentness gate pointer to `core/ADAPTATION.md` §2.2 (verify
    live CLI/docs before wiring a driver, not assumed from another
    adapter) — this is exactly the gate this cycle's Phase 1-3 work followed
    in practice (dev_logs/step_01, step_02).
  - Final drill-caution sentence retained verbatim, updated only to say "run
    a targeted drill only after `harness verify` reports clean" instead of
    "after the symlink projection is confirmed" (more precise now that
    `verify` is the actual mechanized confirmation step).

## Deviation from plan draft

None substantive. One small addition beyond the plan's literal wording: the
Claude Code Projection contract table's plugin row explicitly states the
`sync-native-plugin.py` generator binding (self-contained cache model, `../`
reference ban) — this wasn't separately called out in plan Step 4.1's bullet
list but is a direct, load-bearing fact from this cycle's own Phase 1/PRD
plugin-channel spec, and omitting it would have left the strongest new
"why" fact (why a generator exists at all) out of the one document meant to
carry contract-level why's.

## Verification

- `wc -l INSTALL_LAYOUT.md` → 225 (was 514).
- `grep -n "ln -sfn" INSTALL_LAYOUT.md` → only 2 hits: one inside the
  Windows-projection *prose* explaining what the installer does (not a
  copy-paste command), and the fleet-launcher one-liner explicitly kept per
  plan Step 4.1 ("Keep the fleet CLI section (87-103)"). Zero per-runtime
  `ln -sfn` enumeration blocks remain.
- No `preflight.sh`/`rg '^...$'` manual verification battery remains —
  confirmed via `grep -c "^rg "` → 0 (was ~80 in the old file).
- Manually diffed section-by-section against the old content (read via git
  show of the pre-edit blob) to confirm every contract-level fact listed in
  plan Step 4.1/4.2's "Keep" bullets is present somewhere in the new text —
  copy-once rationale, Windows HOME/symlink specifics, Codex plugin-carriage
  limits, OpenCode non-destructive-merge + INST-OPEN-4 caveat, fleet
  section, exit-code semantics, BLOCKED-on-active-process lineage.
- Editorial-team `review` mode pass completed (Korean/English mixed-prose
  consistency check on the new tables and Migration/Verification section) —
  **not applied here**, per the plan's own note ("code-report stage should
  route it through the editorial team polish pass"); findings handed off
  for code-report:
  1. **표기 통일 필요**: "projection" 은 영어로 통일(음차 "프로젝션" 혼용 제거,
     L126/L130); "merge"/"머지" 도 같은 행(L164) 안에서 흔들림 — 하나로 통일.
  2. **표 셀 과다 길이**: L41/42/128/130 계약 칸이 2~4문장 단락 — 표 밖 각주나
     하위 bullet 로 분리하면 "한눈 대조" 가독성 회복.
  3. **소소한 code-switch**: L8 "why"→"왜", L41 "재-link"→"다시 링크",
     L126 "생성 projection 경유" 명사 적층 풀어쓰기.
  4. **양호 판정**: 실행(CLI 블록) vs 설계(계약 표) 구조 분리는 잘 되어 있음;
     영어 prose 자체엔 판교체 없음(혼용은 전부 한국어 표 셀 속 영어 용어
     방향). 상단 콜아웃(L5-12)만 실행 안내와 설계 안내를 시각적으로
     분리하면 개선.

**Done-when (plan Phase 4)**: met — no copy-pasteable `ln -sfn` per-runtime
recipe list, no manual Migration Order step battery; Target Layout, copy-once
rationale, Windows specifics, Codex/OpenCode 특기, fleet contract, exit-code
semantics, and INST-OPEN-4 caveat are all retained and each points at
`harness install`/`harness verify`.
