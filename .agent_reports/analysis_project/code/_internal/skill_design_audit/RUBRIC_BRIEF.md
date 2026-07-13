# Skill-Design Audit — Judgment Rubric Brief (Pocock 4-axis)

> SoT = `.agent_reports/research/skill-design-principles/` (06_implementation §3 8-Step, 02_standards, 04_technical_deep_dive, analysis_summary §7). This brief compresses it for per-skill judgment. Do NOT invent criteria.

**Root virtue = Predictability** — the agent takes the *same process* every run (NOT same output). All 4 axes are levers toward this.

## 4 canonical axes (label verbatim)

- **① Invocation** — how the skill is reached. `model-invoked` (description resident, ~100 tok/skill always-loaded → *context load*; needs a **"Use when…" trigger** to auto-activate) vs `user-invoked` (`disable-model-invocation: true` → zero context load, but *cognitive load*). Sub-skills that are only ever called by a pipeline/parent skill (never by user or model auto-activation) arguably should be `user-invoked` or at least carry no auto-trigger burden — resident model-invoked descriptions for pipeline-internal skills spend context budget for no reachability gain.
- **② Information Hierarchy** — 3-rung immediacy ladder: in-skill step → in-skill reference → external ref behind a **context pointer**. `references/` should be 1-depth. Sprawl = needless inline bulk. **variance bug** = a *must-have* asset sits behind a *weak* pointer ("필요하면 볼 수도 있다") → coin-flip loading. A strong pointer names the file + when to read + that it is mandatory.
- **③ Steering** — runtime-behavior levers: **Leading Word** (a pretrained-prior term that anchors behavior in one token, e.g. *vertical slice*, *tracer bullet*; self-coined words recruit no prior), **Completion Criterion** (must be *checkable* + *exhaustive*), **Post-Completion-Steps hiding** (visible future steps pull the agent to a "done" state → premature completion; only effective behind a real context boundary = subagent/user hand-off), **Negation** (don't-X frames X → rewrite as positive).
- **④ Pruning** — keep lean. **Single Source of Truth** (each meaning lives in one authority; repeating a cross-skill rule = SoT violation), **Relevance** (does the line still act on the task?), **No-Op test** (does the model already do this by default? if yes → delete whole sentence, "Be aggressive").

## Step→check mapping (judge each skill)

- **Step 0 (Predictability)**: does the SKILL.md state/enforce *same-process* reproduction (invariants, stage contracts, completion criterion)? Or does it only say "this skill does X"?
- **Step 3 (Pruning failure flags)**: no-op sentences (model already does it), cross-skill **duplication** (same rule restated instead of pointer), **sediment** (stale/inactive lines), **sprawl** (needless inline).
- **Step 4 (Steering / premature completion)**: is completion criterion checkable+exhaustive? any rush signal? are post-completion steps behind a real context boundary (not inline)?
- **Step 5 (leading word / negation)**: weak verb phrases that a leading word would sharpen? any negation ("~하지 마라") to flip positive?
- **Step 6 (pointer robustness / variance bug)**: any must-have reference behind a weak/conditional pointer?

## Failure-mode flag vocabulary (use these exact tokens)

`no-op` · `sediment` · `duplication` · `sprawl` · `premature-completion` · `negation` · `variance-bug`

(canonical 6 = no-op/sediment/duplication/sprawl/premature-completion/negation; variance-bug = IH-axis separate 7th)

## Harness nuance (apply, don't re-litigate)

- ALL 28 skills are currently `model-invoked` with a **Korean blurb description and NO English "Use when…" trigger**. Per 02_standards §3 the description-wording norm is **soft** in our harness because auto-activation is ~50% unreliable and we compensate with hook-forced routing (workflow-guard-hook, CLAUDE.md §0 autopilot-* routing). So: a missing "Use when" is a *real but moderate* Invocation gap — weight it by whether the skill actually relies on auto-activation. Entry routers (autopilot-*, analyze-*, audit) benefit most from a trigger; pure pipeline sub-skills (code-execute/plan/report/test, design-* subs, draft-refine) are called by parent skills and their resident model-invoked description mostly just spends context budget.
- `references/` 1-depth is satisfied everywhere it exists; several skills have no references/ at all (inline-only) — judge whether that inlining is sprawl or appropriately lean for a short skill.

## Output format (per skill, markdown)

For EACH assigned skill output exactly this block:

```
### <skill-name>
- **Step0 Predictability**: 🟢|🟡|🔴 — <one-line reason>
- **① Invocation**: 🟢|🟡|🔴 — <reason; is model-invoked right? trigger adequate? sub-skill mis-classified?>
- **② Info Hierarchy**: 🟢|🟡|🔴 — <3-rung/sprawl/pointer; cite file:line if variance-bug>
- **③ Steering**: 🟢|🟡|🔴 — <completion criterion checkable+exhaustive? leading word? negation? premature-completion?>
- **④ Pruning**: 🟢|🟡|🔴 — <no-op/dup/sediment/sprawl/SoT>
- **flags**: [comma-separated failure-mode tokens, or "none"]
- **top gap**: <single most impactful fix> (`skills/<name>/SKILL.md:<line>`)
```

🟢 = conforms / 🟡 = minor gap / 🔴 = material gap. Cite `skills/<name>/SKILL.md:<line>` for every 🔴 and every flag. Read the actual SKILL.md (and its references/ if present) before judging — do not judge from the name.
