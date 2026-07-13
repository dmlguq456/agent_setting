# README product-surface reference brief

> 조사일: 2026-07-13 · 용도: root `README.md` 정보 구조 설계 · 복제 금지, 패턴만 참고

## 채택할 패턴

1. **첫 화면은 제품 판단에만 쓴다.** 이름, 한 줄 가치, 설치/시작 링크를 먼저 둔다.
2. **설치 뒤에 즉시 사용 예시를 둔다.** 내부 아키텍처보다 “무엇을 말하면 무엇이 일어나는가”를 먼저 보여준다.
3. **여러 surface는 역할을 분리해 설명한다.** 제품 전체와 CLI/plugin/IDE/adapter를 같은 것으로 뭉개지 않는다.
4. **긴 카탈로그는 deep docs로 보낸다.** README에는 기능군과 대표 흐름만 남긴다.
5. **검증 가능한 명령을 제공한다.** 소개 문구와 별개로 설치·상태·검증의 구체 명령을 보여준다.

## GitHub 참고 프로젝트

| 프로젝트 | 참고한 점 | 이 저장소에 적용 |
|---|---|---|
| [openai/codex](https://github.com/openai/codex) | 짧은 정체성 → quickstart/install → docs | hero와 설치 진입을 압축 |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | 가치 제안 뒤 get started, plugin을 별도 확장 표면으로 설명 | harness와 runtime plugin을 구분 |
| [obra/superpowers](https://github.com/obra/superpowers) | multi-harness 설치 분기, how it works, workflow 중심 설명 | 가장 가까운 구조 참고; runtime별 배포 차이를 표로 명시 |
| [astral-sh/uv](https://github.com/astral-sh/uv) | 명확한 가치와 실제 명령/출력 중심 | `harness install`/`verify`를 전면 배치 |
| [vercel/ai](https://github.com/vercel/ai) | provider-agnostic 포지셔닝과 짧은 사용 예시 | portable/runtime-neutral 메시지 강화 |
| [ollama/ollama](https://github.com/ollama/ollama) | “바로 만들기”를 첫 행동으로 유도 | 자연어 사용 예시를 설치 직후 배치 |
| [cline/cline](https://github.com/cline/cline) | CLI/IDE/SDK surface matrix | Claude/Codex/OpenCode 채널 차이를 숨기지 않음 |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 핵심 기능과 getting started의 빠른 연결 | 기능을 capability 전수표 대신 효익 단위로 요약 |
| [biomejs/biome](https://github.com/biomejs/biome) | 설치/사용/문서가 선명한 짧은 구조 | deep docs 링크 계층 단순화 |
| [zed-industries/zed](https://github.com/zed-industries/zed) | 제품 문장과 설치 경로의 절제 | 내부 디렉터리 트리 제거 |
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 구성요소를 배포하는 플랫폼이라는 포지셔닝 | “단일 plugin”이 아니라 “runtime별 native projection을 배포하는 harness”로 표현 |

## 공식 runtime 근거

- [Codex plugins overview](https://learn.chatgpt.com/docs/plugins#overview), [plugin structure](https://learn.chatgpt.com/docs/build-plugins#plugin-structure): plugin은 skills/apps/MCP/hooks를 묶는 배포 단위이며 `.codex-plugin/plugin.json`을 요구한다. 이 저장소의 Codex projection 설명은 이 범위 안에서만 한다.
- [Claude Code plugin discovery](https://code.claude.com/docs/en/discover-plugins), [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [reference](https://code.claude.com/docs/en/plugins-reference): marketplace 추가와 plugin 설치는 별도 단계이고 plugin cache/content 경계가 있다.
- [OpenCode skills](https://opencode.ai/docs/skills): skill discovery는 convention path 기반이다. 공식 marketplace bundle이 있다는 식으로 표현하지 않는다.

## 비채택

- 거대한 hero image, sponsor wall, badge wall: 현재 저장소에는 검증된 브랜드 asset/release metric이 없다.
- README 자동 생성: 의미 순서와 가치 제안은 정적 정의로부터 안전하게 생성할 수 없다.
- 모든 capability/agent/mode의 root README 전수표: `capabilities/README.md`, `roles/README.md`, `roles/MODES.md`가 이미 소유한다.
