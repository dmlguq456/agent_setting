# Open-Source Agent-Memory Landscape (2025H2–2026) — Stream 4

Date: 2026-07-22. Scope: survey of current open-source agent-memory systems and the adoption cut for this harness (local SQLite + shell hooks + `mem.py` profiles + memory-scout, no cloud dependency).

Method: web survey (WebSearch/WebFetch), July 2026. All claims cite public sources; star counts and benchmark numbers are as reported by the cited pages, not independently reproduced.

---

## 1. System-by-system survey

### 1.1 Letta (MemGPT lineage)

- **Architecture**: agent-platform, not a memory API. Memory is part of agent state: in-context "memory blocks" (labeled context sections with char limits) + external archival/recall storage. Distinctive feature: **sleep-time compute** — a paired background agent owns the memory-editing tools and reorganizes/consolidates the primary agent's memory blocks during idle turns, so the primary agent never edits its own core memory ([Letta sleep-time docs](https://docs.letta.com/guides/agents/architectures/sleeptime/), [memory-blocks blog](https://www.letta.com/blog/memory-blocks/)).
- **Retrieval trigger**: memory blocks are always-in-context; archival memory is tool-call (`archival_memory_search`).
- **Profile/preference**: the "human" block is effectively a continuously rewritten user profile.
- **Multi-agent**: memory blocks can be **shared between multiple agents** — sleep-time learnings propagate to sibling agents ([sleep-time docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)).
- **Local-first**: Apache-2.0; pip install defaults to **SQLite**, Postgres+pgvector recommended for production ([Letta DB config](https://docs.letta.com/guides/selfhosting/postgres), [PyPI](https://pypi.org/project/letta/)). Viable local, but it wants to *be* the agent runtime — heavy as a bolt-on to Claude Code.
- **Maturity**: high; the reference "memory-first stateful agent" platform in 2026 comparisons ([Dev Genius 2026 comparison](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)).

### 1.2 Mem0

- **Architecture**: drop-in memory layer; three-tier scoping (**user / session / agent**), vector store (Qdrant default) + SQL history, optional graph store; 2026 algorithm emphasizes single-pass extraction, entity linking, multi-signal retrieval, temporal reasoning ([opentechhub overview](https://www.opentechhub.io/mem0/), [Mem0 state-of-memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)).
- **Retrieval trigger**: explicit API/tool calls (`add`/`search`); the app decides when to inject.
- **Profile handling**: user-scope memories serve as an implicit profile; no compiled-profile artifact like ours.
- **Multi-agent**: agent-scope + user-scope tiers give a sharing story, but it is ID-based scoping, not governed sharing.
- **Local-first**: Apache-2.0, self-hostable, but **graph memory is gated to the paid platform** in OSS mode ([mem0 discussion #4020](https://github.com/mem0ai/mem0/discussions/4020)). ~48K stars, YC-backed, very active ([Dev Genius comparison](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)).
- **Benchmark caveat**: loses to Zep by ~15pts on LongMemEval (49.0 vs 63.8, GPT-4o) per third-party testing ([vectorize.io mem0-vs-zep](https://vectorize.io/articles/mem0-vs-zep)).

### 1.3 Zep + Graphiti (temporal knowledge graph)

- **Architecture**: Graphiti (Apache-2.0, ~20–27K stars) builds a **temporal KG**: episodes → entities/edges, every edge carries a **validity window (`valid_at`/`invalid_at`)**; contradicted facts are **automatically superseded (edge invalidation), not deleted** ([Zep paper arXiv:2501.13956](https://arxiv.org/abs/2501.13956), [Zep TKG explainer](https://www.getzep.com/ai-agents/temporal-knowledge-graph/), [graphiti repo](https://github.com/getzep/graphiti)).
- **Retrieval trigger**: API search (hybrid semantic + BM25 + graph traversal); app-controlled injection.
- **Profile**: entity summaries on the user node act as a derived profile.
- **Multi-agent**: graph is shared per group/user id; concurrent writers supported.
- **Local-first**: needs a graph DB — Neo4j, FalkorDB (Docker), or **FalkorDB Lite: embedded, file-based, no server** (`pip install graphiti-core[falkordblite]`, Python 3.12+); Kuzu backend deprecated ([Graphiti install docs](https://getzep-graphiti.mintlify.app/installation), [graphiti issue #1240](https://github.com/getzep/graphiti/issues/1240), [FalkorDBLite blog](https://www.falkordb.com/blog/falkordblite-embedded-python-graph-database/)). LLM-in-the-loop ingestion makes writes expensive.
- **Maturity**: strong; 63.8% LongMemEval, best-in-class temporal reasoning claims ([RockB review](https://baeseokjae.github.io/posts/zep-ai-agent-memory-review-2026/)).

### 1.4 LangMem (LangChain)

- **Architecture**: lightweight SDK, three memory types — episodic, semantic, and **procedural (agent rewrites its own system-prompt instructions from feedback)**; core API is storage-agnostic but is designed around LangGraph BaseStore ([LangMem launch](https://www.langchain.com/blog/langmem-sdk-launch)).
- **Retrieval trigger**: both patterns — "hot path" tool calls and background extraction after conversations.
- **Local-first**: MIT-family, pip-installable, works over any store.
- **Maturity**: survived the LangChain 1.0 transition but **still pre-1.0 (0.0.30, Oct 2025)**, ~1.5K stars, less battle-tested ([atlan 2026 ranking](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/), [db0 on deprecated LangChain memory](https://db0.ai/blog/langchain-memory-deprecated)). Interesting for its taxonomy, not its runtime.

### 1.5 Cognee

- **Architecture**: graph-native "memory control plane"; **ECL pipeline (Extract–Cognify–Load)** unifying relational + vector + graph storage; ontology support ([cognee guide](https://www.cognee.ai/blog/guides/open-source-memory-frameworks-llm-agents), [WeavAI review](https://weavai.app/blog/en/2026/05/09/cognee-2026-review-graphrag-ontology-ai-memory-layer/)).
- **Local-first**: Apache-2.0; runs graph+vector+session memory on a **single self-hosted Postgres**; no paid-tier feature gating ([Dev Genius comparison](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)).
- **Maturity**: ~12K stars, $7.5M seed, 70+ production deployments claimed ([cognee seed announcement](https://www.cognee.ai/blog/cognee-news/cognee-raises-seven-million-five-hundred-thousand-dollars-seed)). More document/knowledge-graph RAG than conversational preference memory — adjacent, not core, to our problem.

### 1.6 Memobase

- **Architecture**: **user-profile-first**. Capture → batch Process → Structure into a typed **User Profile + chronological Event Timeline** → **Inject into system prompt**. Explicitly not embedding-retrieval-centric ([memobase repo](https://github.com/memodb-io/memobase), [memobase.io](https://www.memobase.io/)).
- **Retrieval trigger**: profile is compiled offline (batch) and injected wholesale — the closest OSS analog to our 7 `mem.py profile` docs + briefing-inject hook.
- **Local-first**: Apache-2.0, self-hostable backend.
- **Maturity**: smaller project; notable mostly as **independent validation of the compiled-profile + briefing-injection design** this harness already uses.

### 1.7 A-MEM (agentic memory, NeurIPS 2025 → code)

- **Architecture**: Zettelkasten-style notes: each memory gets LLM-generated context/keywords/tags, is **linked to related memories, and new memories can trigger evolution (rewriting) of old ones**; ChromaDB (+ NetworkX typed-edge variants in community MCP servers) ([paper arXiv:2502.12110](https://arxiv.org/abs/2502.12110), [WujiangXu/A-mem-sys](https://github.com/WujiangXu/A-mem-sys/), [a-mem-mcp-server](https://github.com/tobs-code/a-mem-mcp-server)).
- **Maturity**: research code with community forks; pattern source, not an adoptable runtime.

### 1.8 claude-mem (Claude-Code-adjacent)

- **Architecture**: the direct architectural cousin of this harness. Claude Code plugin using **five lifecycle hooks (SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd)**; observations compressed via agent-sdk into semantic summaries; storage = **local SQLite (WAL) + FTS5 + Chroma vectors**; SessionStart injects a compressed project-tagged summary; also runs a worker service (port 37777) with web UI and MCP search tools ([claude-mem architecture docs](https://docs.claude-mem.ai/architecture/overview), [Augment writeup](https://www.augmentcode.com/learn/claude-mem-persistent-memory-claude-code), [review](https://andrew.ooo/posts/claude-mem-persistent-memory-claude-code/)).
- **Maturity**: reported 46–65K stars trajectory in 2026 coverage (treat with salt, but clearly very popular).
- **Relevance**: validates hooks+SQLite as the right substrate; its **FTS5 + vector hybrid search and per-project observation tagging** exceed what our recall.sh does today.

### 1.9 Newer entrants (2025H2–2026)

- **Hindsight (vectorize-io, MIT)**: "retain / recall / reflect" over epistemically distinct **memory banks**; entities + relationships + time series with sparse+dense vectors; **four retrieval strategies (semantic, BM25, graph, temporal) + cross-encoder reranker**, all self-hosted free, MCP server, Docker; reported 91.4% LongMemEval ([hindsight repo](https://github.com/vectorize-io/hindsight), [paper arXiv:2512.12818](https://arxiv.org/pdf/2512.12818), [Dev Genius comparison](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)).
- **MemOS (MemTensor)**: "memory OS" — hybrid retrieval, cross-task skill reuse, scheduler over parametric/activation/plaintext memory tiers; strong reported numbers (LoCoMo 88.83, LongMemEval 89.20) ([MemOS repo](https://github.com/MemTensor/MemOS), [paper arXiv:2507.03724](https://arxiv.org/pdf/2507.03724)).
- **Memvid**: single-file `.mv2` memory (data+embeddings+index in one file), no database daemon ([Dev Genius comparison](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)).
- **Eval side**: LongMemEval (500 Qs: knowledge update, multi-session reasoning, preference recall, temporal reasoning) is the de-facto benchmark; **LongMemEval-V2** (arXiv:2605.12493) extends to agent-colleague abilities (workflow knowledge, environment gotchas, premise awareness) and ships a pluggable **evaluation harness** (`evaluation/harness.py --memory-config-path`) ([LongMemEval-V2 repo](https://github.com/xiaowu0162/LongMemEval-V2), [Mem0 benchmark survey](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)).
- **Research currents relevant to us**: governed shared memory for multi-agent systems (access-gated writes, schema-grounded mutation) ([arXiv:2606.24535](https://arxiv.org/html/2606.24535v1)); forgetting/decay literature converging on **passive decay (Ebbinghaus/Weibull relevance downweighting) + active supersede/invalidate on contradiction + TTL by semantic category** ([survey arXiv:2602.06052](https://arxiv.org/pdf/2602.06052), [Oblivion arXiv:2604.00131](https://arxiv.org/html/2604.00131v2), [forgetting-problem essay](https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability)); local-first event-sourced memory for coding agents ([PROJECTMEM arXiv:2606.12329](https://arxiv.org/pdf/2606.12329)).

---

## 2. Cross-cutting comparison

| System | Model | Storage | Trigger | Profiles | Multi-agent | Local-first | License |
|---|---|---|---|---|---|---|---|
| Letta | agent platform, memory blocks + sleep-time agent | SQLite/Postgres+pgvector | always-in-context blocks + tool archival | human block | shared blocks | good (heavy) | Apache-2.0 |
| Mem0 | extraction memory layer | vector+SQL (+gated graph) | tool/API | user-scope tier | 3-tier scoping | good, graph gated | Apache-2.0 |
| Zep/Graphiti | temporal KG, edge validity windows | Neo4j/FalkorDB(-Lite) | API search | entity summaries | shared graph | OK (FalkorDB Lite) | Apache-2.0 |
| LangMem | episodic/semantic/procedural SDK | any store (LangGraph-native) | hot-path tool + background | semantic profiles | via store | good | MIT-family |
| Cognee | ECL graph+vector control plane | Postgres unified | API | weak | shared graph | good | Apache-2.0 |
| Memobase | compiled user profile + event timeline | SQL backend | batch compile → prompt inject | **core feature** | per-user | good | Apache-2.0 |
| A-MEM | Zettelkasten notes, link+evolve | ChromaDB | agentic | none | none | research code | research |
| claude-mem | CC lifecycle hooks → compressed observations | SQLite WAL+FTS5+Chroma | hook auto-inject + MCP tools | none | per-project tags | **native fit** | OSS plugin |
| Hindsight | banks, retain/recall/reflect | pg + sparse/dense vectors | API/MCP | per-bank | banks | good (Docker) | MIT |

Consensus stack across all serious 2026 systems: (1) LLM-side **extraction** at write time, (2) **hybrid retrieval** (lexical + dense, often graph/temporal), (3) **background consolidation** ("sleep-time" / reflect / batch-process), (4) **temporal validity** rather than deletion, (5) **eval against LongMemEval-class benchmarks**.

---

## 3. Adoption cut for this harness

Context: our stack = 602MB live SQLite + `recall.sh` + inject/distill hooks + 7 compiled profiles + memory-scout agent. The stream-1/2 concern: relocating domain constants (e.g. spectrogram window sizes) out of `roles/units/` into memory is only safe if recall is reliable on demand.

### Adopt (ranked)

1. **Memory-as-explicit-tool for workers (Mem0/Hindsight/LangMem "hot-path" pattern).** Today workers get no memory lifecycle (core/MEMORY.md excludes them). Every surveyed system exposes `search/recall` as a plain tool callable mid-task. Exposing `recall.sh` (or a thin MCP wrapper à la claude-mem/Hindsight) to dispatched workers is the single prerequisite for moving domain knowledge out of unit files — otherwise relocation breaks depth-1/2 workers who never receive briefings. Low effort: the tool exists; only the exposure and the unit-file pointer ("recall profile 05 before X") are missing.

2. **Retrieval eval harness (LongMemEval-V2 pattern, miniaturized).** Before any relocation, build a small fixed query set ("what STFT window for 16kHz ASR figures?", one per profile + per fossilized fact found in stream 1) and assert recall.sh returns the governing item top-k. This is exactly the harness.py --memory-config-path pattern from [LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2) at repo scale, and it converts "VERY STRONG audit" from one-time to regression-tested. Fits our tests/ dir; pure read-only against the DB.

3. **Temporal invalidation / supersede-on-contradiction (Graphiti edge-validity pattern).** Our memory files already show manual supersession (v2 fix docs, user corrections). Adopt the *policy*, not the graph DB: every stored feedback/fact gets `valid_from`, and a distill action that stores a contradicting item must mark the older one superseded rather than leaving peers ([Zep TKG](https://www.getzep.com/ai-agents/temporal-knowledge-graph/)). Implementable as columns + apply-distill-actions.py logic in SQLite.

4. **Profile compilation into injected briefings — keep and sharpen (Memobase validation).** [Memobase](https://github.com/memodb-io/memobase) independently converges on exactly our design (batch-compiled profile + timeline → prompt injection); the delta worth stealing is **typed profile slots with per-slot update rules** instead of free-form documents, which makes the stream-1 relocation target concrete: "speech-domain constants" land in profile 05 as typed entries, recallable individually.

5. **Hybrid FTS5+vector recall (claude-mem pattern).** If the audit (stream 2) finds recall.sh misses paraphrased queries, the local-first fix is SQLite FTS5 + a small embedding table — proven at scale by [claude-mem](https://docs.claude-mem.ai/architecture/overview) on the identical substrate (Claude Code hooks + SQLite WAL). Adopt only if eval (#2) shows lexical recall failing; don't add a vector daemon preemptively.

Honorable mention: **sleep-time consolidation** (Letta) maps to our existing distill-dispatch hook; the upgrade would be periodic *reorganization* (dedupe, merge, decay-flag) not just append — but do it only after #2 exists to measure regressions.

### Anti-fits

- **Adopting a full platform (Letta, MemOS, Cognee, Zep server)**: all want to own the runtime or add a daemon; conflicts with local-first shell-hook architecture and the no-resident-daemon rule (broker prohibition).
- **Graph database backends** (Neo4j/FalkorDB, even Lite): operational surface + LLM-ingestion cost unjustified at single-user repo scale; steal the temporal semantics (#3) in SQLite instead.
- **Always-inject-everything / auto-observation firehose** (claude-mem's PostToolUse observation capture): our contract is deliberate distillation with user-visible corrections; wholesale observation logging would bloat the 602MB DB and dilute curated memories.
- **Aggressive automatic decay/forgetting**: research-stage ([Oblivion](https://arxiv.org/html/2604.00131v2), [FSFM](https://arxiv.org/pdf/2604.20300)); with user-correction-grade memories ("사용자 질책") silent decay is dangerous. Prefer explicit supersession (#3) + human-reviewed archive.
- **Mem0 as a dependency**: its OSS/paid feature split (graph gated) is a governance red flag for a harness that must stay fully local.

---

## 4. Sources (primary)

- https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8
- https://atlan.com/know/best-ai-agent-memory-frameworks-2026/
- https://vectorize.io/articles/mem0-vs-zep
- https://docs.letta.com/guides/agents/architectures/sleeptime/ · https://www.letta.com/blog/memory-blocks/ · https://docs.letta.com/guides/selfhosting/postgres
- https://github.com/mem0ai/mem0/discussions/4020 · https://www.opentechhub.io/mem0/ · https://mem0.ai/blog/state-of-ai-agent-memory-2026 · https://mem0.ai/blog/ai-memory-benchmarks-in-2026
- https://arxiv.org/abs/2501.13956 · https://github.com/getzep/graphiti · https://getzep-graphiti.mintlify.app/installation · https://github.com/getzep/graphiti/issues/1240 · https://www.getzep.com/ai-agents/temporal-knowledge-graph/
- https://www.langchain.com/blog/langmem-sdk-launch · https://db0.ai/blog/langchain-memory-deprecated
- https://www.cognee.ai/blog/guides/open-source-memory-frameworks-llm-agents · https://www.cognee.ai/blog/cognee-news/cognee-raises-seven-million-five-hundred-thousand-dollars-seed
- https://github.com/memodb-io/memobase · https://www.memobase.io/
- https://arxiv.org/abs/2502.12110 · https://github.com/WujiangXu/A-mem-sys/ · https://github.com/tobs-code/a-mem-mcp-server
- https://docs.claude-mem.ai/architecture/overview · https://www.augmentcode.com/learn/claude-mem-persistent-memory-claude-code · https://andrew.ooo/posts/claude-mem-persistent-memory-claude-code/
- https://github.com/vectorize-io/hindsight · https://arxiv.org/pdf/2512.12818
- https://github.com/MemTensor/MemOS · https://arxiv.org/pdf/2507.03724
- https://github.com/xiaowu0162/LongMemEval-V2 · https://arxiv.org/abs/2605.12493
- https://arxiv.org/html/2606.24535v1 · https://arxiv.org/pdf/2602.06052 · https://arxiv.org/html/2604.00131v2 · https://arxiv.org/pdf/2606.12329 · https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability
