# v20 research shard — quick headless invariant and dispatch-surface terminology

Date: 2026-07-20  
Stage: `research` (`autopilot-spec`, strong, `dispatch_depth=2` stage worker)  
Canonical PRD input: `spec/stage-dispatch/prd.md` v19  
Route: `rt-24a883963a582a4a`, node `research`  
Scope: specification delta only; no repository source or canonical spec was changed.

## 1. Executive synthesis

The v20 delta should make one execution invariant machine-enforceable: every route whose `effective_intensity` is `quick` runs as exactly one registered headless capability-worker session. A quick route has no native-subagent or inline fallback. If registered headless execution is unavailable, route compilation fails closed instead of changing transport, intensity, or execution location.

This supersedes SD-19, whose current Codex-only preference/fallback ladder permits `native-subagent` and then main-inline execution at `dispatch_depth=0`. It does not change direct routes (`direct` remains main-inline at `dispatch_depth=0`), and it does not remove the checked same-harness, cross-harness, native-subagent, and inline fallback behavior of `standard+` routes.

The same v20 transaction should remove the collision between portable dispatch nesting and runtime-native agent nesting. New portable fields and prose use `dispatch_depth` / `max_dispatch_depth` (and `owner_dispatch_depth` where applicable). Codex `agents.max_depth` remains a runtime-native subagent setting and is never a synonym for portable dispatch depth. Claude subagents, Claude agent-team teammate sessions, and registered headless worker sessions are three distinct execution surfaces.

## 2. Evidence synthesis

### 2.1 Verified facts from the assigned inputs

The statements in this subsection are verified against the three assigned artifacts. Official-runtime claims are verified *as recorded by the audit*; this research stage did not independently browse or re-probe vendor documentation.

1. The v19 PRD currently defines `quick` using the historical bare terms “depth-1” one-shot capability worker and no “depth-2” children (SD-18), but SD-19 allows Codex quick to fall back from headless to a native subagent and then to main-inline execution.
2. The audit deterministically reproduced successful quick compilation with both `--transport native-subagent` and an arbitrary transport string. It attributes the gap to the topology registry allowing broad transports and the compiler copying caller-provided direct/quick transport without closed-vocabulary or quick-specific validation.
3. The audit records that current Codex documentation uses `agents.max_depth` for Codex native-subagent nesting. It therefore identifies bare portable `depth` / `max_depth` as collision-prone.
4. The audit records the Claude runtime distinction: a Claude subagent runs within one session and reports to its caller, while an agent-team teammate is a separate full Claude Code session with peer communication. A teammate is not a subagent.
5. The assigned route record demonstrates the current portable schema vocabulary: top-level `owner_depth`, per-node `depth`, and node transport arrays that include `headless`, `native-subagent`, and `inline-fallback`. The record is strong/standard+, not quick, so it is evidence of current schema shape rather than evidence that the approved quick invariant is already implemented.
6. V19 already distinguishes Codex native subagents from nested `codex exec` headless execution and defines the canonical route transport labels as `headless|interactive` in SD-72. The v20 delta can build on that separation rather than invent a new runtime surface.
7. V19's route compiler and topology registry are the machine-enforcement points (SD-33/34). Prose-only edits would not close the reproduced compiler acceptance gap.
8. The audit found unrelated multi-capability composition language internally contradictory and without a durable compiler contract. The approved delta explicitly excludes multi-capability composition.

### 2.2 Approved decision treated as binding input

The following is not an inference from v19; it is the approved v20 policy supplied with this assignment:

- Every `effective_intensity=quick` route uses a registered headless worker session.
- `native-subagent`, `inline-fallback`, and unknown/arbitrary transports fail closed for quick during route compilation.
- Direct-inline and standard+ fallback semantics are preserved.
- Portable nesting is named `dispatch_depth` / `max_dispatch_depth` so it cannot collide with Codex `agents.max_depth`.
- Claude subagents, Claude agent-team teammate sessions, and registered headless worker sessions are explicitly distinguished.
- Multi-capability composition is not added.

## 3. Proposed normative decisions for PRD v20

Everything in this section is proposed normative wording for the v20 PRD update. It is not a claim about current implementation.

### SD-73 — quick routes require one registered headless worker (supersedes SD-19)

**Normative decision**

1. A route with `effective_intensity=quick` **MUST** compile to exactly one capability-owner worker session using canonical transport `headless` and **MUST** be registered in the canonical attempt/jobs registry before launch.
2. The quick recipe **MUST** declare:
   - `owner_dispatch_depth=1`
   - `max_dispatch_depth=1`
   - exactly one capability-owner node
   - `allowed_transports=["headless"]`
   - no child node and no `dispatch_depth=2` fan-out.
3. If no explicit transport is supplied, the compiler **MUST** derive `headless` for quick. If the caller or registry supplies `native-subagent`, `inline-fallback`, an unknown string, or any value other than `headless`, compilation **MUST** fail before route emission, registry claim, or child launch.
4. If current runtime eligibility cannot establish a registered headless worker path, compilation **MUST** fail with a structured error such as `quick-headless-unavailable`. The compiler and runtime **MUST NOT** silently lower quick to direct, run quick inline, substitute a native subagent, or mutate `effective_intensity`.
5. A quick route **MUST NOT** contain a fallback chain to `native-subagent` or `inline-fallback`. Those transports remain available only where another intensity's recipe explicitly permits them.
6. The transport vocabulary is closed at compilation. Unknown/arbitrary transport values **MUST** fail for every route. The quick-specific allowlist is stricter than the global vocabulary.
7. The registered-headless requirement is harness-neutral. `headless` means a repo-registered worker session with immutable route/node identity, canonical attempt row, liveness evidence, and completion-gate linkage; it does not mean “any background or child agent.”

**Compatibility rule**

- `direct` remains main-inline at `dispatch_depth=0` and does not acquire a worker session.
- `standard+` retains its existing checked fallback order and eligibility semantics, including same-harness headless, cross-harness headless, native-subagent, and inline fallback where the capability recipe permits them.
- Existing quick route artifacts compiled under the old SD-19 rule may remain readable as historical evidence, but new compilation must not emit the superseded fallback forms.

### SD-74 — portable dispatch depth and runtime-native nesting are separate namespaces

**Normative decision**

1. New portable topology schemas, route records, generated projections, tests, and prose **MUST** use:
   - `dispatch_depth` instead of bare `depth`
   - `max_dispatch_depth` instead of bare `max_depth`
   - `owner_dispatch_depth` instead of bare `owner_depth`.
2. `dispatch_depth` describes the portable registered-dispatch ownership level: `dispatch_depth=0` main, `dispatch_depth=1` registered capability owner, and bounded `dispatch_depth=2` registered stage/support worker. It **MUST NOT** be described as, inferred from, or configured through a runtime-native agent nesting limit.
3. Codex `agents.max_depth` applies only to Codex native-subagent nesting. It **MUST NOT** validate, cap, or advertise support for registered headless `dispatch_depth`, and a Codex native-subagent check **MUST NOT** serve as headless-dispatch eligibility evidence.
4. A standard+ route node may retain its intended portable `dispatch_depth` as route ownership metadata while evaluating fallback transports. A native-subagent or inline fallback attempt **MUST** identify its actual execution surface separately and **MUST NOT** claim that the runtime-native agent or inline execution itself is a registered worker at that dispatch depth.
5. New schema output **MUST NOT** emit ambiguous bare nesting fields. Legacy route records may be read through an explicitly versioned compatibility path, but new compilation and validation use the qualified names.

### SD-75 — execution-surface terminology

**Normative decision**

The PRD and all portable/adapter projections **MUST** use the following nouns consistently:

| Term | Normative meaning | Registry/dispatch implication |
|---|---|---|
| **Claude subagent** | A Claude runtime-native child agent operating within one Claude session and reporting to its caller. | Not a registered headless worker merely because it is a child agent; runtime-native nesting rules apply. |
| **Claude agent-team teammate session** | A separate full Claude Code session participating in an agent team with peer communication. It is not a Claude subagent. | Not a registered headless worker unless it separately enters the repo-owned registration/route contract; team membership alone supplies no dispatch-depth evidence. |
| **registered headless worker session** | A harness-neutral worker launched through the repo-owned headless dispatch contract and bound to canonical route, node, attempt, liveness, and completion evidence. | Carries portable `dispatch_depth`; canonical transport is `headless`. |

Additional wording rules:

- “Runtime-native subagent” may be used as a cross-runtime category only when it does not include Claude agent-team teammates.
- “Worker,” “session,” or “agent” alone is insufficient where the surface changes routing, depth, Fleet visibility, or ceremony guarantees.
- A full standalone process is not automatically a registered headless worker; registration and route binding are the defining properties.

## 4. PRD sections and decision IDs to amend or add

### Required amendments

| PRD location | Required v20 change |
|---|---|
| Header/version history and input evidence | Add v20 summary: quick registered-headless invariant, qualified dispatch-depth vocabulary, and Claude surface terminology. Record the approved decision and audit as inputs. |
| §0 “one line” | Replace the historical “quick = depth-1 worker” phrase with “quick = one registered headless worker at `dispatch_depth=1`; no native/inline fallback.” Preserve direct and standard+ clauses. |
| §2.3, §3, §6 and other portable depth prose | Mechanically qualify portable nesting as `dispatch_depth`; explicitly state it is unrelated to runtime-native nesting settings. |
| §8 cost/safety and §8.8.1 SD-18 | Retain one-shot/no-child quick topology, but require registered headless transport and use `dispatch_depth` terms. |
| §8.8.2 SD-19 | Mark **superseded by SD-73**. Preserve the historical text as reversal history or replace its normative body with the fail-closed quick rule; do not leave the old fallback ladder normative. |
| §8.8.3 SD-20 | Require the quick Fleet activity to originate from the registered attempt row. Rename metadata `depth=1` to `dispatch_depth=1`; native/inline degradation notes are no longer quick outcomes. |
| §13.1.1 SD-31 | Replace the historical quick “depth-1 one-shot owner” wording with registered headless one-shot owner at `dispatch_depth=1` and compile-failure behavior when unavailable. |
| §13.1.2 SD-32 | Rename portable nesting fields and clarify that `transport` is orthogonal to dispatch ownership. Retain direct inline and standard+ transport choices. |
| §13.1.3 SD-33 | Add closed transport vocabulary validation and quick recipe constraint `allowed_transports=[headless]`; reject quick native/inline/unknown and all unknown transport strings. |
| §13.1.4 SD-34 | Require qualified fields in immutable route records and prevent route emission on quick transport violation. |
| §13.1.6 SD-36 | Keep capability-specific standard+ recipes unchanged; add a cross-cutting note that quick is uniformly one registered headless owner for every capability. |
| §13.1.8 SD-38 | State that Codex `agents.max_depth`, Claude subagents, Claude agent-team teammate sessions, and registered headless workers are independent runtime/portable surfaces. |
| §13.1.14 v9 acceptance | Replace quick-depth wording and add compiler negative fixtures for quick native, inline, arbitrary, and headless-unavailable cases. |
| §13.3.3 SD-50 and §13.7.1 SD-61 | Scope native/inline fallback ladders explicitly to `standard+` (and other recipes that opt in), never quick. Preserve their existing standard+ ordering. |
| §13.11 SD-72 | Keep canonical `headless|interactive` transport vocabulary; qualify every portable depth reference and ensure native subagent is not presented as an alternative dispatch depth. |
| §14 meaning↔rules boundary | Add the quick transport allowlist, closed vocabulary, qualified nesting fields, and surface-term distinctions to the deterministic rule section. |

### New decision IDs

- **SD-73**: quick registered-headless invariant; explicitly supersedes SD-19.
- **SD-74**: `dispatch_depth` / `max_dispatch_depth` namespace and runtime-native nesting separation.
- **SD-75**: Claude subagent / Claude agent-team teammate / registered headless worker terminology contract.

Numbering assumes SD-72 remains the latest existing decision in v19.

## 5. Acceptance criteria for v20

1. **Default quick compilation**: compiling any capability with `effective_intensity=quick` and no explicit transport emits one capability-owner node with `transport=headless`, `owner_dispatch_depth=1`, `max_dispatch_depth=1`, and no children.
2. **Quick transport negatives**: explicit `native-subagent`, `inline-fallback`, `interactive`, empty/unknown, and arbitrary transport fixtures each fail before route file creation, registry claim, or process spawn.
3. **Unavailable headless**: a quick fixture with checked headless ineligibility returns structured `quick-headless-unavailable`; native-subagent and inline attempts are both zero.
4. **Closed vocabulary**: an arbitrary transport is rejected for direct, quick, and standard+ route compilation. Known transports remain recipe-gated rather than globally accepted everywhere.
5. **Direct preservation**: direct all-predicate fixtures remain main-inline at `dispatch_depth=0` and create no registered worker row.
6. **Standard+ preservation**: existing same-harness headless → cross-harness headless → native-subagent → inline fallback fixtures retain their ordering, route node/write scope/completion gate, and evidence requirements.
7. **No quick fan-out**: any quick recipe or route containing a child node, `dispatch_depth=2`, or `max_dispatch_depth>1` fails schema/route validation.
8. **Qualified schema**: new registry/route fixtures contain `dispatch_depth`, `max_dispatch_depth`, and `owner_dispatch_depth`; ambiguous bare fields are absent from newly emitted records and generated portable/adapter projections.
9. **Codex namespace separation**: tests prove changing or probing Codex `agents.max_depth` neither validates nor changes registered headless dispatch depth; native-subagent evidence cannot satisfy headless eligibility.
10. **Claude terminology**: a terminology/conformance fixture rejects any statement that calls an agent-team teammate a subagent or treats either runtime-native surface as a registered headless worker without route/attempt registration.
11. **Fleet evidence**: a live quick activity is backed by exactly one canonical registered attempt row with `dispatch_depth=1`; quick native/inline degradation rows or prose outcomes are impossible.
12. **Legacy read-only compatibility**: if legacy route parsing is retained, old bare-depth/SD-19 records are readable but cannot be resumed or re-emitted as new quick routes without recompilation under v20.
13. **No composition expansion**: no new composition schema, co-primary route, cross-capability DAG, or multi-capability confirmation behavior is added.
14. **Parity**: Claude, Codex, and OpenCode compiler/projection checks independently enforce the same portable quick invariant; unsupported headless execution is reported as failure, not silently substituted by another surface.

## 6. Non-goals

- Designing or implementing multi-capability composition, co-primary routing, or cross-route DAG envelopes.
- Removing native-subagent or inline fallback from standard+ routes.
- Changing direct from main-inline execution at `dispatch_depth=0`.
- Configuring or editing Codex `agents.max_depth` or any user-owned runtime setting.
- Reclassifying Claude agent-team teammate sessions as subagents or automatically treating them as registered headless workers.
- Selecting concrete models, reasoning effort, or harness affinity.
- Implementing compiler, registry, Fleet, adapter, or generated-surface changes in this research stage.
- Revisiting unrelated v19 lifecycle, broker-retirement, retry, capacity, composition, or cleanup decisions.

## 7. Risks and ambiguities for review

1. **Canonical label**: existing records use transport value `headless`; approved prose says “registered headless worker session.” Recommendation: keep machine value `headless` and define the longer phrase as its normative meaning. Introducing `registered-headless` would create unnecessary migration work.
2. **Route node versus fallback attempt depth**: standard+ nodes currently carry logical nesting while a fallback may execute natively or inline. V20 should preserve node ownership metadata but prohibit prose or evidence from claiming the native/inline *attempt* is a registered worker at that depth. Review should ensure the schema has a clear node/attempt distinction.
3. **Legacy field migration**: renaming `depth` fields affects registry schema, route hashes, wrappers, jobs rows, Fleet collectors, fixtures, and generated prose. A versioned read-only compatibility path is safer than silently accepting both names in new records.
4. **Fail-closed quick availability**: the approved rule means a small task can fail to compile even when native or inline execution is technically possible. This is intended policy, but the structured error and user-facing recovery path should be explicit. Recovery requires a new route/intensity decision by the owner, not compiler fallback.
5. **Interactive as a quick transport**: SD-72 names `headless|interactive` as canonical transport labels. The approved rule implies `interactive` is invalid for quick even though it is known globally; tests should distinguish “known but disallowed by recipe” from “unknown.”
6. **Agent-team registration edge case**: a Claude teammate could hypothetically invoke a repo-owned registered wrapper. Classification should be by the actual launch/registration contract: team membership remains a separate runtime property, and only the wrapped child attempt is registered headless.
7. **Scope of terminology census**: the PRD contains extensive historical sections. Review should decide whether historical quotations retain old bare terms with an explicit historical label or are mechanically qualified. Normative/current prose and generated projections must have zero ambiguity even if preserved history remains verbatim.

## 8. QA policy evidence and stage assurance

The required `standard/general` QA policy command returned:

```text
qa_level=standard
qa_track=general
quality_reviewers=1x-deep-reviewer+2x-fast-reviewers
fact_checker=1x-fast-fact-checker
external_adversary=skip
max_round=1
assurance_scope=plan-check:selected-independent-pass:final-verify
independent_delegation_policy=claim-only-if-separate-codex-agent-headless-or-external-pass-ran
fallback=report-inline-review-if-independent-agent-unavailable
```

This shard is the assigned deep-maker research input for the subsequent review node. It does not claim an independent reviewer or fact-checker pass. The audit input reports one deep review plus official-source fact verification and deterministic local checks, with no separate reviewer process; it explicitly used the policy's inline fallback. The next stage should review SD-73~75 wording and the node-versus-attempt depth distinction before the PRD transaction.

## 9. Guard/evidence notes

- All durable output is under the canonical artifact root.
- No repository source, core, capability, adapter, generated projection, or canonical PRD was modified.
- The assigned route already records tracked gate evidence as satisfied (`spec_read=stage-dispatch-prd-v19`, `drift_verdict=SPEC-SIGNIFICANT: SD-19 quick fallback policy`, `artifact_guard=preflight-write-pass`).
- The Codex read-marker command was attempted after reading the PRD but could not create its marker under `.spec-grounding` because that runtime path was read-only. This does not change the route's prevalidated tracked-gate evidence; it is recorded here as an unsupported runtime write detail for the review stage.
