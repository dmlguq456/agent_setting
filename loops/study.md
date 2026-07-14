# Study — Weekly Autonomous Audit of External Developments Against the Harness

Do not modify any instruction or settings file. Produce exactly one proposal report. Adoption requires user sign-off, and applied changes are verified through a drill.

## Procedure

1. **Review prior study reports:** read the latest one or two files under `/home/nas/user/Uihyeop/notes/study/`. Do not repeat the same proposal. Update a previously declined item in one line only when it is worth reconsidering.
2. **Research external developments** with web search and fetch tools:
   - **First priority—benchmark new built-in harness capabilities and internalize the useful invariant:** inspect changelogs and release notes for newly updated features in major harnesses such as Claude Code and Codex. Prioritize proposals that reproduce the useful behavior in this portable harness through Skills, agents, hooks, or loops. Ask which local friction it reduces and whether the behavior can remain cross-runtime rather than binding the harness to one product. One precedent is adapting a Claude Code design capability into the portable design role.
   - Official changelogs and engineering posts for the runtime adapter in use.
   - Recent practical work on harness, context, loop, multi-agent, and evaluation engineering.
   - Emerging community conventions, filtered aggressively for source quality and hype.
3. **Compare against the current harness:** read `<agent-home>/core/CORE.md`, the active runtime adapter bootstrap, `core/CONVENTIONS.md`—especially §§5.8–5.10—`loops/README.md`, and the hook catalog. Distinguish what the harness already does, what is missing, and what it does better.
4. **Light internal hygiene:** inspect the `g0_overhead` input-token trend in `loops/drill/metrics.csv`, one or two contradictions or bloat candidates across instruction documents, and one or two rules with unclear intent because they lack rationale, date, or incident context under `CONVENTIONS §3 item 8`. Warn about instruction dieting when `g0` exceeds 45k input tokens; the 2026-06-11 baseline was about 40k, and excessive context can reduce performance.
5. **Weekly usage accounting:** make one table from the last seven days of `loops/*.log` run counts and durations, summed drill cost in `loops/drill/metrics.csv`, and weekly job count in `<agent-home>/.dispatch/jobs.log`. Flag only a suspicious increase of at least 2× week over week. Do not judge absolute spend because usage is subscription-based; report trends and concentration.

## Proposal Report

Write `/home/nas/user/Uihyeop/notes/study/<YYYY-MM-DD>.md` in the user's established communication language. For every proposal include:

- **what** should change;
- **why**, with source links;
- **where** in the harness, including file and section;
- **expected cost**, covering implementation and instruction-context overhead;
- **priority:** 🔴 now, 🟡 next, or 🟢 reference.

Always write the heartbeat file. If there are no proposals, use an equivalent of `# Study — <date>\nNo new proposals after reviewing N sources.` in the user's communication language.

Do not justify a proposal merely by saying it would be nice to adopt. State the concrete harness friction it removes. Downgrade an item with no clear friction to 🟢 reference.

### Automatic Draft for Critical Proposals

For 🔴 items only, extend the proposal from an explanation into a concrete edit draft that can be applied after sign-off. This follows the Hermes `skill_manage` self-edit benchmark while preserving the invariant that the user decides: never apply or commit the draft directly.

Add an `> Automatic draft` block that:

- names the target file and section and gives paste-ready before/after text or a diff; label uncertain material explicitly;
- gives one verification path, such as `loops/drill/run.sh` for an instruction change or `autopilot-spec` → `autopilot-code` for a new script;
- is based on an actual read of the target's current text so quotations cannot be stale;
- is omitted in favor of `Draft deferred: target text is uncertain` when confidence is insufficient;
- exists only inside the proposal report and never mutates the target file.

Keep 🟡 and 🟢 items explanatory only to reduce noise and hallucination risk.
