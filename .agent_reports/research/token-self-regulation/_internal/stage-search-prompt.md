# Stage: search (depth-2 headless, technology mode)

너는 autopilot-research 파이프의 **search stage** 담당 depth-2 세션이다. 이전 대화 컨텍스트 없음 — 아래 정보만으로 작업.

## Artifact 경로
- artifact_dir: `/home/Uihyeop/agent_setting-wt/research-token-self-regulation/.agent_reports/research/token-self-regulation`
- 원본 skill reference: `/home/Uihyeop/agent_setting/skills/autopilot-research/references/pipeline-search-analysis.md` (Step 2, technology mode 섹션 참조)

## Query 목록 (이미 확장됨 — Step 2a 완료 상태로 진행)
```
queries = [
  "caveman claude skill token compression output caveman-compress caveman-stats JuliusBrussee",
  "ponytail lazy senior dev decision ladder claude code skill DietrichGebert",
  "LLM coding agent token budget self-regulation context compression skill ruleset",
  "wilpel caveman-compression semantic compression method",
  "Headroom RTK TokenSave LLM agent token saving stack Hackenberger Ultimate Token-Saving Stack",
  "openagentskill skillsllm catalog token saving compression skill"
]
original_query = "caveman·ponytail 심층 분석 — 에이전트 토큰 사용 자기조절 메커니즘 설계 입력"
```

## Mode: technology
- Search sources: WebSearch (GitHub repo README/블로그/기술 게시물), WebFetch (GitHub repo raw README, 관련 블로그/리포트), arXiv (보조 — 관련 있으면), Hugging Face (관련 있으면, 대부분 무관할 것)
- **핵심**: 이 조사 대상은 학술 논문이 아니라 **GitHub 리포지토리(스킬/도구)와 기술 블로그 글**이다. `search_results.json` 의 `papers` 배열에 논문 대신 "발견물"(리포지토리/블로그/카탈로그 항목)을 동일 스키마로 채워 넣는다:
  - `title`: 리포지토리명 또는 글 제목
  - `authors`: 작성자/org (예: `["JuliusBrussee"]`)
  - `year`: 확인 가능하면 (release/commit 연도), 없으면 null
  - `venue`: "GitHub" / "Blog" / "Catalog" 등
  - `url`: 실제 URL (GitHub repo, 블로그 포스트, README)
  - `discovery_count`: 몇 개 쿼리에서 발견됐는지
  - `oa_url`: GitHub raw README URL (accessible 판정용)
  - 논문이 아니므로 `arxiv_id`/`openalex_id`/`referenced_works`는 null 허용

## 필수 확인 대상 (반드시 실제 접근 시도)
1. `github.com/JuliusBrussee/caveman` — README, `/caveman-compress`·`/caveman-stats` 커맨드 설명, 압축 방식, 절감 수치 claim, 비판/이슈(세션 전체 효과 4-5% 라는 비판이 어디서 나왔는지 — GitHub issue/comment/블로그 포함)
2. `github.com/DietrichGebert/ponytail` — README, ruleset 전문(decision ladder 단계들), "lazy senior dev" 컨셉 설명, 코드 작성량 억제 논리
3. `wilpel/caveman-compression` (또는 유사 org) — semantic compression 방법론 문서
4. Headroom(RTK), TokenSave 등 token-saving 스택 — 공식 리포/문서
5. Hackenberger 의 "Ultimate Token-Saving Stack" 관련 글/리포 — 여러 도구 조합 사례
6. openagentskill / skillsllm 류 카탈로그 — 유사 token-saving skill 목록 (검색으로 카탈로그 페이지 자체를 찾아서 나열)

## Output
- Routing: raw 결과 → `{artifact_dir}/_internal/search_results.json`
- 최소 목표: 15개 이상의 고유 발견물 (리포지토리/블로그/카탈로그 항목), 위 6개 필수 대상은 반드시 discovery_count>=1 로 포함
- `_internal/search_results.json` schema:
```json
{
  "query": "caveman·ponytail 토큰 자기조절 조사",
  "date": "2026-07-13",
  "sources_used": ["WebSearch", "WebFetch", ...],
  "total_papers": <int>,
  "papers": [ ... 위 스키마 ... ]
}
```

## Timeout / 에러 처리
- 단일 소스 3분 초과 시 skip 하고 다음으로.
- WebFetch 실패(404/paywall 등) → 다른 소스(google cache, 블로그 미러 등) 시도 후 그래도 실패면 abstract-only(제목+URL만)로 기록.

## 완료 후
- `search_results.json` 유효 JSON, `papers` 비어있지 않음, 각 항목 `title` 필수 확인.
- **Status 파일**: `{artifact_dir}/_internal/stage-search-status.json` 작성:
```json
{"stage": "search", "status": "done", "total_found": <int>, "notes": "<1-2줄 한국어 요약>"}
```
- 실패 시 `"status": "failed"` + `"reason"`.
- 마지막 응답(반환 텍스트)은 파일 경로 + 3-5줄 한국어 요약만. 본문 전체를 반환하지 말 것.
