# Stream 1 — Legacy Domain-Content Sweep (전수)

Date: 2026-07-22. Read-only investigation. Scope actually read (full text):
all 44 files under `roles/units/**` (27 units + 7 `_NOTES` + `_voice` + `_design-rules`
+ 4 `_shared` + `_schema`), all 5 `profiles/fragments/*.md`, all 5 `loops/*.md`,
and `skills/*/references/*.md` via a full-corpus domain-signal grep
(kHz/PESQ/spectrogram/LibriCSS/CHiME/STFT/SepRe/CorrNet/Restormer/speech/booktabs/
crimson/Sogang/venue names/ar5iv/Playwright/PyMuPDF/DPI/…) plus full reads of every
hit-bearing file (convention-paper/-presentation/-doc/-common, paper-figure-policy,
pipeline-steps, delegate-prompt, pipeline-phases, mode-code, data-contract,
eval-procedure, pipeline-search-analysis, process-stages, prd-authoring,
operations-and-examples, nudge-and-boundaries, invocation-and-args, outputs-and-examples,
setup-procedure, owner-execution(lab), examples-and-checklist, resolution, data-model).
All 7 mem profiles were dumped in full via `mem.py profile` (read-only) for dedup
comparison. `tools/figure-semantic-verify.py` was inspected to establish which rules are
actually deterministic-tool-backed.

Bucket doctrine applied (existing split): style/preference/recipe → mem profiles;
enforceable integrity gates backed by a deterministic tool, and true harness behavior
(routing, I/O contracts, generic engineering doctrine, illustrative examples) → harness.

## Headline totals

| Bucket | Count |
|---|---|
| A KEEP-IN-HARNESS | 14 |
| B RELOCATE → mem profile | 10 |
| C RELOCATE → memory item(s) | 4 |
| D AMBIGUOUS (needs user) | 7 |
| **Total findings** | **35** |

Cross-cutting: 4 contradiction flags (F-22 stale hex vs profile 01 §A7; F-23 wrong-domain
TF_Restormer example vs profiles 05/07; F-1 window-triple EN/KO divergence, values still
unconfirmed; F-8 bold/underline table-emphasis tension between data-script and profile 03).
5 duplication clusters (profile-preload block ×7+, PPTX output rule ×3, figure-layout-guide
policy ×3, DPI policy ×2, ar5iv ladder ×2).

---

## Classification table

Verdict column key — dedup-vs-profile: NEW (profile lacks it), DUP (profile already says it),
PARTIAL (profile covers part; merge delta), CONFLICT (catalog text disagrees with profile).

### material family

| # | Location | Content | Bucket | Target | Dedup-vs-profile verdict |
|---|---|---|---|---|---|
| F-1 | `roles/units/material/figure-gen.md:54-59` | Spectrogram window triple 8k→256 / 16k→512 / 48k→1024 + nearest-rule, labeled "domain LAW" | **D** | after user confirms values: 04_analysis_methodology (or a new deterministic check in figure-semantic-verify) | NEW — no profile states window sizes. `figure-semantic-verify.py` does **not** enforce windows (only 48000 Hz, 0–24000 Hz, shared scale, colormap, dynamic range, claim bands, PNG hash), so this is NOT tool-backed and fails the bucket-A test. Values themselves unconfirmed: `material/_NOTES.md:9-16` records the EN 512/400/256 vs KO 256/512/1024 divergence, resolved editorially to KO. Two decisions needed from user: (1) are 256/512/1024 correct, (2) relocate to profile vs promote into the verifier as a real gate. |
| F-2 | `figure-gen.md:60-62` | No-resampling rule (STFT at native rate; never resample for panel uniformity) | **D** | either keep as harness LAW by adding a `sample_rate_hz`-per-panel check to the verifier, or relocate with F-1 | NEW. Integrity-flavored (honesty of material) but currently prompt-only, tool-unenforced — same limbo as F-1. |
| F-3 | `figure-gen.md:63-67` + `:75-101` (Metric/Display bands, manifest, verify-report gate) | Shared color axis, METRIC_BAND vs FIGURE_BAND separation, semantic manifest, fail-closed `figure-semantic-verify.py` run, PNG visual-review + SHA-256 | **A** | — (this IS the doctrine's model case: deterministic tool + qa/test Level 5c wiring) | Backed line-by-line by the verifier source. Keep. |
| F-4 | `figure-gen.md:32-44` (Branch: paper defaults) | Serif fallback chain (Times→Nimbus→Liberation→DejaVu, STIX math), figsize triples (6.4×2.8 / 4.5×2.8 / 3.5×2.6), coherent-palette guidance (OrRd sequential), grid alpha 0.25/lw 0.5 | **B** | 01_paper_figure_style (new "matplotlib data-figure defaults" subsection) | PARTIAL — profile 01 §A6 covers font roles abstractly (serif math, sans labels, "paper may be all-serif") and §A3 covers curve-plot taste (4-color 주황/노랑/파랑/초록 palette); the concrete matplotlib recipe (fallback chain, inch sizes, alpha values) exists nowhere in profiles. No contradiction, complementary. |
| F-5 | `figure-gen.md:42-43` | `pdf.fonttype=42` + `ps.fonttype=42` (PMLR/ICML validation-safe) | **A** | — | Venue-technical correctness fact tied to output validity, cheap and enforceable-in-principle; harness recipe, not taste. |
| F-6 | `figure-gen.md:110-111`, `pdf-extract.md:73-74`, `web-image-search.md:77-79` | Output rule "(user decision, 2026-05-09): individual PNGs + at most one combined PPTX; never per-figure PPTX wrappers" — stated 3× | **C** | one durable memory item (dated user decision); units keep a one-line pointerless behavioral rule at most once | NEW to profiles. Classic dated-user-correction fossil, triplicated. Note web-image-search variant assigns combined-PPTX to the caller (divergence recorded in `material/_NOTES.md:26-29`) — consolidating into one memory item also resolves the wording variance. |
| F-7 | `figure-gen.md:118-123` | Return example naming the robust-loss family incl. user-private `s-log1p` | **A** | — (illustrative example) | DUP-adjacent: `s-log1p` is documented in profiles 04 §7 / 05 §2; as a mere example it may stay, but genericizing the example would fully de-domain the unit. |
| F-8 | `roles/units/material/data-script.md:33-59` | Paper-table defaults (Params/MACs left, ↑/↓ headers, bold best + underline 2nd, †/‡/* footnotes, ablation subtables) + per-task metric-group table (SE PESQ-WB/…; universal-restoration fidelity-vs-perceptual signature split; separation SI-SNRi+SDRi pair; dereverb CD/SRMR/LLR/SNRfw; BWE LSD/NISQA; SV EER/minDCF Vox1-O/E/H; CSS WER LibriCSS 0S/0L/10-40; ASR WER CHiME-4 dt/et/sim/real) + "signature preference — never evaluate from one group" | **B** | 04_analysis_methodology §1 (merge delta rows) + 01_paper_figure_style §A2 | PARTIAL/CONFLICT — profile 04 §1 already owns the 2-axis fidelity/perceptual split, the metric registry, SI-SNRi/PIT, EER/minDCF, WER; profile 01 §A2 already owns booktabs/↑↓/†‡/cost-column/bold-best. The unit ADDS: underline-2nd-best, `*` footnote, dereverb metric set, VoxCeleb O/E/H eval sets, LibriCSS overlap bins, CHiME-4 splits. Tension: unit says "bold best, underline second"; profile 01 §A2 says bold-only emphasis (음영/화살표 절제), profile 03 §5 says slide tables use "제안 행 bold + 열별 best underline" — three slightly different emphasis schemes; user should confirm which is canonical per surface before merging. The "signature preference" sentence is DUP of 04 §1. |
| F-9 | `data-script.md:61-64` | Pointer: conventions follow `mem profile 04`, terminology `05` | **A** | — | Correct architecture (reference, not restatement). |
| F-10 | `roles/units/material/pdf-extract.md:29-33` (+DUP `skills/autopilot-draft/references/pipeline-steps.md:177,186-190`) | High-resolution policy "standing user directive 2026-05-12: DPI 600-800 default 800; never 72/96 full-page; slide-source 160-180 DPI" | **C** | one memory item for the dated directive; harness keeps the operative numbers in ONE place (unit) and the skill reference points to it | NEW to profiles. Dated user directive fossilized + duplicated across unit and draft skill. |
| F-11 | `pdf-extract.md:34-49` | PyMuPDF caption-aware bbox recipe: caption regex variants, `x0 < 100` + lowest y0 heuristic, clip offsets −5, two-column geometry (612pt page / 234pt column / 26pt gap; crop x0=50,x1=303 / x0=315,x1=562) | **A** | — | General venue-PDF geometry + tool recipe; not user knowledge. (Venue list ICML/NeurIPS/ICASSP/T-ASLP/IS in the geometry line is generic layout fact, acceptable.) |
| F-12 | `roles/units/material/browser-fetch.md:34-49` | Playwright stealth config (launch args, pinned Chrome-120 UA string, webdriver-property override) | **A** | — | Harness tool recipe. Perishable web knowledge; if it starts rotting, the unit's own Memory section ("recurring paywall patterns") is the correct escape hatch — no relocation now. |
| F-13 | `roles/units/material/web-image-search.md:44-59` (+DUP `skills/autopilot-research/references/pipeline-search-analysis.md:237-264`) | ar5iv → arxiv-vanity → pdfimages 3-tier fallback ladder | **A** | — | Harness tool recipe; duplicated at the call site (acceptable as dispatch prompt, but the unit is SoT — flag for single-sourcing). |

### dev / plan / editorial / qa families

| # | Location | Content | Bucket | Target | Verdict |
|---|---|---|---|---|---|
| F-14 | `dev/backend.md:45-49`, `dev/frontend.md:45-48`, `dev/new-lib.md:50-53`, `dev/refactor.md:46-49`, `plan/plan-author.md:46-57`, `research/plan-review.md:50-58`, `research/research-survey.md:41-45`, `design/maker.md:83-91`, `editorial/_voice.md:123-130` | Cross-project profile preload blocks (`mem profile 07/05/04/02/01/03` + precedence: project-local > profile, current-turn > all) — restated 9× with minor wording drift | **A** | — (this is the memory system working as designed: pointers, not content) | Correct pattern; `dev/_NOTES.md` item 7 already flags the 4× dev repetition as a `_shared/` fragment candidate. Recommend one `_shared/profile-preload.md` fragment to kill drift — harness refactor, not relocation. |
| F-15 | `roles/units/editorial/_voice.md:59-82` | Korean-target keep-list: venue-name examples (NeurIPS 2026, ICASSP 2025, Interspeech, T-ASLP), domain-term examples (attention/transformer/cross-attention/**dual-path**), and the rule "previously defined abbreviations, with `mem profile 05_domain_expertise` as the terminology reference" | **A** | — | The RULE is harness behavior and already delegates terminology to profile 05 (correct). The inline examples include user-signature vocabulary (`dual-path`); tolerable as examples. The venue-notation SoT already moved to profile 02 (2026-06-16 audit precedent) — keep it that way. |
| F-16 | `editorial/_NOTES.md:26-33` | mem-upsert hazard: never `mem add --source user-profile:02…` with a partial body (source-keyed upsert REPLACES the full profile); channel must be `/post-it --scope user` | **A** | — but needs a durable home: this is MEMORY-SYSTEM safety doctrine currently stranded in a residue file | NEW — belongs in core/MEMORY.md or the memory tool docs (Stream-2 relevant: a data-loss footgun documented only in `_NOTES`). |
| F-17 | `roles/units/qa/data-curate.md:24-33` | Speech-example audit table (SNR distribution, forced alignment, Hangul mapping, speaker leakage) with explicit "examples generalize to other domains" | **A** | — | Declared illustrative; generalization clause present. No action. |
| F-18 | `roles/units/qa/ml-debug.md:22-33` | Symptom→cause table (NaN/OOM/attention collapse/GAN/DDP) | **A** | — | Generic ML engineering knowledge, not user/domain-specific. |
| F-19 | `roles/units/qa/test.md:73-78` | Level 5c: figure-semantic gate — non-24 kHz max = failure, not skip | **A** | — | Tool-backed (verifier); the qa side of F-3. Keep. |

### research family

| # | Location | Content | Bucket | Target | Verdict |
|---|---|---|---|---|---|
| F-20 | `roles/units/research/research-survey.md:100-115` | Venue-tier ladder (Tier 1 NeurIPS/ICML/ICLR/ICASSP/Interspeech/ACL…/T-ASLP/SPL; Tier 2 ASRU/SLT/WASPAA/ODYSSEY/EUSIPCO/APSIPA/MMSP/Speech Communication/CSL/JASA; Tier 3/4) | **D** | candidate 05_domain_expertise §6 extension — BUT the tier list is a runtime sort input for the search branch (deterministic ranking: discovery_count → venue_tier → citations) | PARTIAL — profile 05 §6 covers the user's venue preferences but not the 4-tier grading. Relocation makes the ranking depend on a profile recall succeeding inside a depth-2 worker; ask user whether tiers are (a) user taste → profile, or (b) pipeline mechanics → stay, with profile 05 cross-referenced. Speech-heavy Tier-2 row is unmistakably user-domain flavored. |
| F-21 | `roles/units/research/fact-check.md:49-58` | Section-heading conflict-pair dictionary: {deep learning}↔{classical/statistical}, {denoising}↔{dereverberation}↔{BWE}↔{GSR/universal SE}, {single-task}↔{universal/multi-task} | **D** | candidate 05_domain_expertise (task-taxonomy section) with the unit keeping the mechanism + reading the dictionary from the profile | NEW — pure speech-task taxonomy fossilized in a near-zero-floor verbatim-matching unit. Its own Memory section already says additions go to memory ("domain-specific conflict-pair dictionary additions"), which concedes the seed dictionary is domain data. Counter-argument for staying: fact-check is intentionally profile-free (`research/_NOTES.md` item 2 scoped profiles away from it). Needs user call. |
| F-22 | `roles/units/research/plan-review.md:71` | Venue-notation drift example ``IS 2024` vs `Interspeech 2024`` inside the style axis (+DUP `skills/autopilot-refine/references/process-stages.md:59-60,99`: model-name examples FRCRN/TF-Locoformer/MP-SENet/IF-CorrNet, venue tags) | **B** | pointer to 02_paper_writing_style "Citation·venue 표기" section (already SoT since 2026-06-16) + 05 §3 | DUP — profile 02 already owns the IS↔Interspeech mapping verbatim. Replace inline examples with a profile pointer where load-bearing; process-stages fuzzy-match examples may stay as examples but should not drift from 02. |
| F-23 | `roles/units/research/plan-review.md:29-48` + `research-survey.md:30-39` | Knowledge Sources authority hierarchy (analysis_project/paper 00_overview → paper/ → research/ → analysis_project/code → agent memory; skip-missing-silently; all-absent disclosure) | **A** | — | Harness artifact-layout doctrine (named as a sweep candidate in the tasking; adjudicated harness): it encodes where *artifacts* live, not what the user knows. Memory is correctly last-priority-but-present. |

### design family

| # | Location | Content | Bucket | Target | Verdict |
|---|---|---|---|---|---|
| F-24 | `roles/units/design/_design-rules.md` (whole file, incl. slop blocklist, OKLCH, WCAG 4.5:1, 24px/44px scale floors) + `design/_NOTES.md:14-28` KO-only font lists/chroma cap | **A** | — | Generic design taste-law (provenance: public DESIGN.md), not user/domain knowledge. The "taste" here is harness-owned doctrine deliberately distinct from profiles 01/03 (which the maker loads separately — correct split). |
| F-25 | `roles/units/design/maker.md:37-45` + `skills/autopilot-design/references/paper-figure-policy.md` (whole) + profile 01 Part B | 2026-05-28 figure-craft policy triplicated: layout-guide-only, user finishes in PPTX, asset library paths `user_profile/assets/figure/svg/` + `figure_ppt/*.pptx` | **B** | 01_paper_figure_style Part B is already the SoT (frontmatter changelog carries the 2026-05-28 decision); harness surfaces should shrink to the routing rule ("layout guide only; see profile 01 §B0") without restating library paths | DUP ×3 — the policy, its date, and the asset paths are stated in the profile, the unit, and the skill reference. Drift risk is live: if the library moves, three surfaces go stale. Also note the underlying decision provenance is C-flavored (dated user rejection of LLM craft) and is already durably held by the profile changelog — no separate memory item needed. |

### skills references

| # | Location | Content | Bucket | Target | Verdict |
|---|---|---|---|---|---|
| F-26 | `skills/autopilot-draft/references/convention-paper.md:19-34` + `skills/draft-strategy/references/delegate-prompt.md:21-40,136-158` | Natural-integration rule + 4-step paragraph-cohesion pre-check, each carrying dated incidents (2026-05-19 M11/M15, 2026-05-20 M8/M9) and verbatim Korean user quotes ("rebuttal 자료를 본문에 그대로 가져다 붙이지 말고…", "그걸 삽입할 단락의 전체 cohesive, coherence를…") | **C** (provenance quotes/incidents) / **A** (the operationalized rule) | incidents+quotes → memory items (they are exactly "dated user feedback, contextual not procedural"); the distilled rule stays in the skill; profile 02 cross-ref exists via memory `[[feedback-paper-body-rewrite-pattern]]` | PARTIAL — profile 01 §A2 already cites the same memory `[[feedback-paper-body-rewrite-pattern]]`; the incident narrative is duplicated across two skill files. Keep the rule, relocate the war story. |
| F-27 | `skills/draft-strategy/references/delegate-prompt.md:14` | Hardcoded "Target venues (for academic modes): NeurIPS, ICML, ICLR, ICASSP, Interspeech, IEEE/ACM T-ASLP" | **B** | 05_domain_expertise §6 (venue preference — already there) | DUP — profile 05 §6 states the same venue set with more nuance (which venue for which work). Replace literal with a profile read or pass-through. |
| F-28 | `delegate-prompt.md:225-234` | Korean administrative-tone register (정부/위원회/산학협력단 detection, 개조식 calm-report constraints, anti-pitch-deck rationale) | **B** | 02_paper_writing_style §6 (국문 보고서 register) — merge/cross-ref | PARTIAL — profile 02 §6 already documents the Korean gov/report register in depth (개조식 종결, 기호 위계, 수치 verbatim, 기관 주어); delegate-prompt re-derives an overlapping style-constraint table for slides. Complementary (detection logic is harness; register description is profile) but should cross-reference 02 rather than restate the register. |
| F-29 | `skills/analyze-user/references/pipeline-phases.md:139-143` | Illustrative profile-record snippet: "block: rounded rectangle, grayscale outline (TF-Restormer Fig.1 / TF-CorrNet Fig.2); color: encoder green **#3F8C5C** / ours red **#A0152A**" | **D** (contradiction fix) | fix or genericize the example | **CONFLICT** — profile 01 §A7 (pptx-XML-extracted, marked "exact, 추정 아님") gives encoder green **#548235/#70AD47** and novelty red **#C00000**; §A7 explicitly says it "replaced the previous ≈ estimates". The example fossilizes the superseded estimates in the very skill that writes profiles — a stale-value reinjection risk. Needs user sign-off to edit (file edit out of scope for this read-only stream). |
| F-30 | `skills/analyze-project/references/mode-code.md:126-181` | Worked examples naming the user's real repos with the WRONG domain: "TF_Restormer — image / TF, MDTA, GDFN, LayerNorm2d, DIV2K/GoPro, PSNR/SSIM; SR_CorrNet — image SR, CorrAttention, ResBlock, DIV2K, PSNR" | **D** | ask user: genericize example names, or correct to the real speech facts | **CONFLICT** — profiles 05/07 establish TF_Restormer/SR_CorrNet as speech restoration/separation repos (STFT input, SI-SNR/PESQ, VCTK/URGENT/WSJ0). The example silently grafts the *image* Restormer's modules (MDTA/GDFN) onto the user's repo name. Any agent cross-reading this against memory gets contradictory "facts" about the user's own codebases. |
| F-31 | `skills/autopilot-lab/references/{owner-execution.md:117, outputs-and-examples.md:27-124, setup-procedure.md:34-105}` + `skills/autopilot-spec/references/{operations-and-examples.md:85-93, prd-authoring.md:150}` + `skills/post-it/references/nudge-and-boundaries.md:45` + `skills/autopilot-note/references/{data-model.md:30-31, resolution.md:45}` + `skills/autopilot-refine/references/examples-and-constraints.md:19-28` + `skills/audit/references/examples-and-checklist.md:11` + `skills/autopilot-apply/references/owner-execution.md:152` + `skills/autopilot-draft/references/{convention-paper.md:58, invocation-and-args.md:15}` + `skills/autopilot-research/references/invocation-and-modes.md:74` | Pervasive use of real user projects (TF_Restormer, SR_CorrNet, speech-enhancement-trends, ICML 2026 camera-ready) as invocation/directory-layout EXAMPLES across 12+ skill references | **A** | — (examples), with a hygiene note | These are illustrative, mostly harmless, and often helpful (they match the user's real world). But they are the long tail of the same fossilization pattern; if the user wants a domain-clean harness, a one-pass genericization is the fix. Not counted per-file. |
| F-32 | `skills/autopilot-draft/references/pipeline-steps.md:315-328` | Step 4c report-figure semantic gate (48 kHz / 0–24 kHz, exit-code semantics) | **A** | — | Tool-backed call-site of F-3; consistent with verifier source. |
| F-33 | `skills/autopilot-lab/references/data-contract.md` + `eval-procedure.md` | metrics.jsonl/run.json contracts; audio/spectrogram playback HTML routing; SI-SDR/PSNR as example metrics | **A** | — | Harness experiment-infrastructure contracts; metric names are schema examples. |

### profiles/fragments + loops

| # | Location | Content | Bucket | Target | Verdict |
|---|---|---|---|---|---|
| F-34 | `profiles/fragments/*.md` (all 5) | Dispatch-stage specializations (read/write classes, no-re-dispatch, RUNLOG convention) | **A** | — | Pure harness. Zero domain content found. |
| F-35 | `loops/*.md` (all 5) | Patrol/study/runtime-watch/improvement procedures; user NAS paths (`/home/nas/user/Uihyeop/notes/...`) and dated incident anchors (2026-06-21 401, 2026-07-13 Codex window) | **A** | — | Harness + environment config. Incident anchors are rationale-with-date per CONVENTIONS §3 practice, correctly placed. No relocation. |

---

## Adjudication of the known candidates (explicit answers)

- **Spectrogram window triple** → F-1, bucket D. Not tool-enforced (verified against `figure-semantic-verify.py`), values still pending user confirmation (EN/KO divergence in `material/_NOTES.md`). Recommend: confirm values → then either promote into the verifier (making it genuinely bucket A) or move to profile 04.
- **pdf-extract DPI / two-column / bbox numbers** → split: DPI directive = C (dated user directive, duplicated); bbox/column geometry = A (tool recipe) (F-10/F-11).
- **data-script speech metric-table (LibriCSS/CHiME rows)** → B into profile 04 §1 as merge-delta; heavy DUP with 04 already; emphasis-scheme conflict with 01/03 flagged (F-8).
- **material Playwright stealth recipes** → A (F-12).
- **ar5iv fallback ladder** → A, dedup the skill-side restatement (F-13).
- **dev spec-check / memory-profile blocks restated 4×** → A, refactor to a `_shared/` fragment (F-14) — this is pointer plumbing INTO memory, which is the desired end-state pattern, just duplicated.
- **design `_design-rules` taste law** → A: generic design doctrine, deliberately separate from user-taste profiles 01/03 which the maker loads via mem (F-24). The user-taste part that WAS in design (figure-craft policy) is the triplicated F-25 → shrink to profile pointer.
- **research Knowledge Sources hierarchy** → A: artifact-layout doctrine, not user knowledge (F-23).
- **editorial Korean-target keep-list** → A: rule is harness; terminology authority already delegated to profile 05 (F-15).

## Relocation-safety dependencies (feed to Stream 2)

Every B/D relocation above converts an always-present instruction into a *recall
dependency*. The specific recall paths that must be proven reliable before moving
anything: (1) `mem profile <name>` availability inside dispatch-depth-2 workers
(research-survey search branch has no MCP and possibly a restricted tool set —
F-20's tier ladder would ride on this); (2) profile-body size growth from F-4/F-8
merges vs the ~7–10K-token profile budget stated in `analyze-user` Phase 5;
(3) the source-keyed upsert footgun (F-16) — any merge into profiles 01/02/04 must
go through `/analyze-user` or `/post-it promote`, never raw `mem add`, or it
destroys the profile it is trying to enrich; (4) the two CONFLICT examples
(F-29, F-30) show that stale copies in instructions actively fight the memory
system — relocation without deleting the fossil is worse than either alone.
