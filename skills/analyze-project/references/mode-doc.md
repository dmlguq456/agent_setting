# Mode `doc`

Analyzes miscellaneous doc-creation materials (reviewer comments, format templates, past samples, internal notes, mixed reference packs) and produces structured per-task analysis.

## Phase 1: Input Discovery & Classification

**Input scope resolution** (in priority order):
1. **Positional arg 명시**: 그 folder를 input scope로 (외부 폴더 override).
2. **Default — cwd 자동 발견**: 다음 패턴 grep within cwd + 1-level subdirs:
   - `docs/` / `reviews/` / `templates/` / `reviewer_comments/` / `format/` / `guidelines/` (sub-folder 통째로)
   - root에 흩어진 `*.docx` / `*.pdf` (paper로 분류되지 않는 것) / `*_review.md` / `*_template.*` / `*_sample.*`
3. **Output sub-folder `{name}`**: positional 명시 → 그 folder name (basename) / 자동 발견 → cwd basename 또는 task description-derived

Read input scope. Classify each file by heuristic:

| File pattern | Category | Output target |
|---|---|---|
| Filename contains `review`/`reviewer`/`comment` OR text contains "Reviewer 1:" / scoring | reviewer comments | `reviewers/` |
| Filename contains `template`/`format`/`guideline`/`cfp`/`instructions` | format spec | `formats/` |
| Filename suggests past example (`sample`, `past`, `example`, prior year naming) | sample | `samples/` |
| PDF with academic structure (abstract/citations) | paper-like | (suggest `--mode paper` instead; or include as `samples/`) |
| Other (notes, sketches, mixed) | misc | `misc/` |

If classification is ambiguous → 연구팀에게 위임해 판단.

## Phase 2: Per-Category Analysis

Delegate to 연구팀:

```
Analyze doc-creation materials in this folder: {input_folder}
Output: <artifact-root>/analysis_project/doc/{name}/

For each file in input folder, classify and produce structured analysis:

- reviewers/ : per-reviewer breakdown — score, confidence, summary, key points (severity-tagged), tone
- formats/ : structured format extraction — required sections, length limits, page limits, submission window, sub-types (for rebuttal: meta-only / dialogue / response-with-revision), tone guidelines
- samples/ : key structural patterns and stylistic choices observable in past examples
- misc/ : free-form summary indexing the file's content for later retrieval

Also write 00_overview.md at root of {name}/:
- Inventory of all files in the input folder, with classification
- Key findings per category
- Cross-references useful for autopilot-draft downstream
- "intended for mode": likely autopilot-draft mode this material targets (`paper` / `presentation` / `doc` — `doc` 안 intent 라벨: rebuttal / review / report / proposal)

Use the selected target artifact language for narrative; preserve the source
language for verbatim quotes. Return ONLY paths + a concise summary.
```

## Phase 3: Verify
- Confirm all input files are classified (none silently dropped).
- If classification was ambiguous, prompt user to confirm or override.
- Logged to `<artifact-root>/analysis_project/doc/{name}/_internal/`.

---
