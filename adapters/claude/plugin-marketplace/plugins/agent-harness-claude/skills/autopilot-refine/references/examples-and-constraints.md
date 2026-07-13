# autopilot-refine — Examples, constraints & checklists

Router(`../SKILL.md`)에서 참조되는 invocation 예시, apply 시 지켜야 할 constraints, when-not-to-use, post-apply checklist.

## Constraints

- **빈칸 > 잘못 채우기** — when Stage B.5 flags an `⚠ Unverified` claim and no ground-truth source confirms it within the artifact's `cards/` (or cross-research `<artifact-root>/research/*/cards/`), prefer to leave the claim **blank or marked `[?]`** in the new_text rather than filling it from inference. Applies even if the prompt seems to require the claim — emit the marker and let the user decide. Cost of a `[?]` placeholder is small; cost of a hallucinated venue/year/task is high (drift compounds over 20+ refine cycles).
- **No silent additions** — Stage D applies only what was shown in Stage C diff (or auto-mode summary). If a new issue is discovered during apply, abort that single edit and note it in the v{N} 변경 사항 section's `Skipped` list, but do NOT propose new edits beyond the original list.
- **Versioning is mandatory** when applying — every apply increments version + creates snapshot. Only `--review-only` skips this (because it doesn't apply).
- **Cards = primary source for research** — for taxonomy/definition/coverage prompts, always re-read `cards/*.md` and cite in reasoning.
- **Don't auto-rename historical citations** — paper titles, baseline names as published, specific challenge names. List these in Stage C as "intentionally untouched" if relevant.
- **Cross-artifact ripple is announced, not auto-propagated** — if a research change affects a downstream doc artifact, surface this in the v{N} 변경 사항 section's `Downstream sync needed` field. The user invokes `/autopilot-refine` again on the doc; this skill never auto-cascades.
- **STRUCT escape hatch** — if changes look structural, halt with a recommendation; don't try to handle structural rewrites in this skill.

---

## Examples

```
# Default — chat-loop with diff preview. Artifact inferred from prompt.
/autopilot-refine "speech-enhancement-trends에서 General Restoration과 Universal SE를 task family로 통합"
# (skill fuzzy-matches "speech-enhancement-trends" → research artifact, shows diff, ends turn)
# user replies: "all"
# → applies, snapshots to _internal/versions/v1/, updates pipeline_summary.md with v2 row + 변경 사항 section

# Auto-apply via prompt signal (no separate flag)
/autopilot-refine "speech-enhancement-trends Year×Paradigm heatmap의 2026년 칸 채우기. 확인 없이 자동 적용."

# Review only — no edits (artifact 식별자는 prompt에 포함)
/autopilot-refine "speech-enhancement-trends에서 최신 카드 5편이 분류표에 누락됐는지 검토" --review-only

# Memo mode — fall back to file-memo for deferred review
/autopilot-refine --memo .../review_memo.md "2026-05-06_se-seminar-tfrestormer 메모 반영"

# Doc artifact (auto-detected from prompt keyword)
/autopilot-refine "se-seminar-tfrestormer draft Slide 4 task family 표를 4행으로 변경"

# Higher rigor — pre-apply reviewer pass (rigor 는 intensity 파생)
/autopilot-refine "se-seminar-tfrestormer 결론 챕터 wording 다듬기" --intensity standard
```

## When NOT to use

- Single-file typo / cosmetic edit → just `Edit`.
- Code artifacts → `/code-refine`, `/code-execute`, `/autopilot-code`.
- Whole-axis structural redesign → `/autopilot-research --from analyze` or `/autopilot-draft --from strategy`.
- Pure deferred review (annotate over hours/days) → this skill's `--memo <file>` form (file-memo). `/draft-refine` 는 autopilot-draft 내부 sub-skill 이라 사용자 직접 호출 X.

## Post-Apply Checklist

After successful apply, suggest to user:
1. If `Downstream sync needed: Yes` → run `/autopilot-refine "{dependent_artifact_name} pipeline_summary v{N} 반영"` for each dependent artifact.
2. Optionally `git add -A && git commit -m "autopilot-refine: {prompt summary}"` if artifact is under git.
3. Run `/sync-skills` if this SKILL.md was just updated (rare — only when user iterates on the skill itself).
