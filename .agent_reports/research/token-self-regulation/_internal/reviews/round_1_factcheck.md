# Round 1 — Fact-Check (verbatim card 대조)

> subrole: fast fact-check. 대상: 보고서 00~07 의 material domain claims (도구명/저자/URL/venue·arXiv id/year/metric/절감 수치/lineage/4계층 classification). SoT = `cards/*.md` + `code_resources/EXCERPTS.md`.
> 범위: ~30 most material claims (Tier 1 우선). coverage/narrative/roadmap 미논평.

| Report | Section | Claim | Source card (file:line) | Match | Severity |
|---|---|---|---|:---:|:---:|
| 07 | Tier1 | caveman repo = github.com/JuliusBrussee/caveman | caveman-juliusbrussee.md:4 | ✅ | — |
| 03 | 매트릭스 | caveman output 65% avg (22-87%, n=10) | caveman-juliusbrussee.md:6 | ✅ | — |
| 02 | 2(d) | caveman session 14-21% (output-heavy), terse net-negative | caveman-juliusbrussee.md:7-8 / EXCERPTS:35-37 | ✅ | — |
| 00/03 | 재주입 | caveman skill ~1-1.5k input tok/turn | caveman-juliusbrussee.md:8 / EXCERPTS:34 | ✅ | — |
| 04 | 테마1 | invented abbreviation(cfg/impl/req/res/fn) 금지 — tokenizer 동일 분할 | EXCERPTS:16-17 / caveman-juliusbrussee.md:21-22 | ✅ | — |
| 04 | 테마1 | causal arrow(→) 금지 (자체 토큰) | EXCERPTS:18 / caveman-juliusbrussee.md:22 | ✅ | — |
| 04 | 테마1 | intensity lite/full/ultra/wenyan, wenyan 80-90% char 감축 | EXCERPTS:20-21 / caveman-juliusbrussee.md:22-23 | ✅ | — |
| 04 | 테마1 | Auto-Clarity 조건 (security/multi-step/ambiguity/user-ask) | EXCERPTS:24-27 | ✅ | — |
| 02 | 2(d) | "Wanting the rock to work does not make the rock work." | caveman-juliusbrussee.md:27 / EXCERPTS | ✅ | — |
| 07 | Tier1 | ponytail repo = github.com/DietrichGebert/ponytail | ponytail-dietrichgebert.md:4 | ✅ | — |
| 03 | 매트릭스 | ponytail up to 94% less code, ~54% mean | ponytail-dietrichgebert.md:6 | ✅ | — |
| 02 | 2(d) | Claude 42-75% cheaper (Haiku 63/Sonnet 74.5/Opus 42.3, 30 reps) | ponytail-dietrichgebert.md:8 / EXCERPTS:65 | ✅ | — |
| 00/02/03 | reasoning 역전 | OpenAI 역전 gpt-5.4-mini +26%, gpt-5.5 +39% | ponytail-dietrichgebert.md:9 / EXCERPTS:66 (+26.2/+38.7, 반올림) | ✅ | — |
| 03 | 매트릭스 | correctness 100%, baseline Sonnet 76% over-eng | ponytail-dietrichgebert.md / EXCERPTS:69 | ✅ | — |
| 04 | 테마2 | 7-rung ladder YAGNI→reuse→stdlib→native→dep→one-line→minimal | EXCERPTS:49-55 / ponytail-dietrichgebert.md:11-12 | ✅ | — |
| 04/05 | safety rail | validation/error/security/a11y 축소 금지 ("When NOT to be lazy") | EXCERPTS:59 / ponytail-dietrichgebert.md:12,23-24 | ✅ | — |
| 04 | 테마2 | "The ladder shortens the solution, never the reading." | ponytail-dietrichgebert.md:24-25 | ✅ | — |
| 04 | trade-off | v1 산문이 코드 절감 먹어 caveman 에 4% 뒤짐; csv-sum ~3k skill-read tax | EXCERPTS:73-76 | ✅ | — |
| 01 | lineage | caveman 저자 "pair with ponytail" (직교 조합 권장) | ponytail-dietrichgebert.md:18 (ponytail→"pair with Caveman" 방향) | ❌ | 🟡 |
| 07 | Tier1 | wilpel repo = github.com/wilpel/caveman-compression | wilpel-caveman-compression.md:4 | ✅ | — |
| 03/04 | 매트릭스 | LLM 40-58%, NLP(spaCy) 15-30%, MLM(RoBERTa) 20-30% | wilpel-caveman-compression.md:6 / EXCERPTS:97 | ✅ | — |
| 04 | 테마3 | factual 13/13(100%) 주장 | wilpel-caveman-compression.md:6 / EXCERPTS:97-98 | ✅ | — |
| 04 | 테마3 | 모드 지연 LLM ~2s/req · spaCy<100ms 15+langs · RoBERTa 1-5s | wilpel-caveman-compression.md:17-18 | ✅ | — |
| 04 | 테마3 | SPEC.md "Remove only what LLMs can deterministically reconstruct" | EXCERPTS:92-95 / wilpel-caveman-compression.md:20-21 | ✅ | — |
| 01 | lineage | wilpel 저자 = William Peltomäki (Medium) | wilpel-caveman-compression-medium.md:14 | ✅ | — |
| 다수 | CAVEWOMAN | arXiv 2606.24083 | cavewoman-arxiv-2606.24083.md:4 | ✅ | — |
| 다수 | 부호 비대칭 | output 1.4-2.4x(max 3x) / input net-loss ~1.15x(최악 1.8x) | cavewoman-arxiv-2606.24083.md:6-8 | ✅ | — |
| 02 | 2(b) | 5-benchmark, length-control, ~절반만 correct | cavewoman-arxiv-2606.24083.md:8-9 | ✅ | — |
| 02 | 2(a) | codepointer 500 세션 (모집단 2,182·13 proj·614M tok·$926.31 baseline) | codepointer-critique-3.7pct.md:7-8 | ✅ | — |
| 다수 | 핵심 수치 | 합산 실절감 3.7% (rtk+headroom+caveman) | codepointer-critique-3.7pct.md:9 | ✅ | — |
| 02/05 | pricing | cache_read $0.50/M, cache_create 42%, output 29% | codepointer-critique-3.7pct.md:22-23 | ✅ | — |
| 다수 | ContextBudget | arXiv 2604.01664, >1.6x gain (high-complexity), BACM-RL | contextbudget-arxiv-2604.01664.md:4,6-7 | ✅ | — |
| 다수 | SkillReducer | arXiv 2603.29919, desc 48%·body 39%, 품질 +2.8% | skillreducer-arxiv-2603.29919.md:4,6-7 | ✅ | — |
| 02 | 2(c) | SkillReducer 600 skills+SkillsBench, transferability 0.965 (5 model, 4 family) | skillreducer-arxiv-2603.29919.md:8 | ✅ | — |
| 다수 | Active Ctx Comp | arXiv 2601.07190, 22.7%(14.9M→11.5M), max 57%, 6.0회, 3/5 동일 | active-context-compression-arxiv-2601.07190.md:4,6,7 | ✅ | — |
| 01/07 | 미검증지표 | headroom "58.7k star" 미검증, 60-95% fewer tokens | headroom-rtk.md:6,10 | ✅ | — |
| 01/07 | 미검증지표 | token-optimizer 1,610 star / 128 fork, SkillsLLM scan 통과 | token-optimizer-skillsllm.md:7 | ✅ | — |
| 01/07 | 미검증지표 | ponytail "74k star" (secondary blog) | ponytail-dashen-tech-74k.md:7 | ✅ | — |
| 07 | Tier2 | claw-compactor up to 97%, 결정론 14-stage, pip install, reversible | claw-compactor.md:6,14-15 | ✅ | — |
| 07 | Tier2 | tokensave Rust CodeGraph port(@colbymchenry), 60-80%, 80+ symbol MCP | tokensave-aovestdipaperino.md:6-7,13-14 | ✅ | — |
| 01 | classification | 4계층 A/B/C/D 태깅 (caveman=A+D, ponytail=B+D, wilpel=C, ContextBudget=D) | 각 카드 분류축1 라인 전수 일치 | ✅ | — |

## 불일치 상세

**🟡 (1건, minor attribution inversion)**
- `01_landscape.md` lineage 다이어그램(line ~169): JuliusBrussee/caveman 노드 아래 "저자: 'pair with ponytail' (직교 조합 권장)" 으로 표기. 카드 근거는 `ponytail-dietrichgebert.md:18` — **ponytail 저자가 "pair with Caveman"** 이라 명시한 것(방향 ponytail→caveman). 즉 pairing 권고를 카드는 ponytail 측 발화로 문서화했는데 보고서는 caveman 저자 발화로 귀속. orthogonal-pairing 사실 자체는 일치하나 화자 귀속 방향이 반전. caveman 저자가 ponytail 을 명시 권장한다는 별도 카드 근거는 없음 → 단방향 카드 근거를 양방향으로 확장한 minor 과잉귀속.

## 범위 밖 (fabrication 아님, 참고)
- `05_deployment.md:489` 하네스 내부 다이어트 수치(always-on -8.9% / 53,932→49,131 in-tok / skill body -77% / 481k→108k chars)는 도메인 claim 이 아니라 내부 `token-ceremony-audit/*` 참조라 카드 대조 대상 아님 — fact-check 범위 밖으로 통과.
