# §Common — 모든 mode 적용

> autopilot-draft 의 모든 mode (`paper` / `presentation` / `doc`) 에 공통 적용되는 룰. mode 별 conventions (`paper.md` / `presentation.md` / `doc.md`) 의 _기본 위계_.

- **Paragraph Cohesion 4-step Pre-Check** — 모든 paste-ready / 본문 작성 전 적용. (a) substance 중복 / (b) paragraph axis (motivation→design→formalization, claim→evidence→caveat 등) / (c) cross-section redundancy / (d) EDIT·REPLACE·INSERT·DROP 분류. INSERT 보다 EDIT·REPLACE 우선.
- **Anchor 정책** — 모든 cross-reference 는 _식별자_ (section / label / paragraph / slide title / page number) 기반. line number 박지 X (편집 시 drift). `anchor: L###` 형태로만 _보조_ 표시.
- **약자 정책** — 첫 등장 시 풀어쓰기 1 회, 이후 약어. 신규 약자는 abstract / opening single introduction.
- **LLM-flavor 어휘 회피** — instantiation / operator / load-bearing / via gradient withholding 등. plain word 우선.
- **편집팀 (editorial-team) 마지막 다듬기** — 모든 사용자 향 markdown 산출은 _최종 1회_ 편집팀이 점검·다듬기. 판교체 회피 + 표기 일관성 + 한 호흡 단위 가독성. (`<agent-home>/agents/editorial-team.md`)
- **언어 결정** — mode × genre 별 primary language 표 (SKILL.md Step 4.1 Mode × genre primary language table 참조). 사용자 작업 언어와 primary 가 같으면 mirror 생략, 다르면 Step 4-KO 가 mirror 생성.
