# 엔트리 Skill 계층 감사·정비 최종 보고서

상태: **완료**
기준 커밋: `23c86bea`
source 커밋: `22b9fe1b`
primary capability: `autopilot-code` · `dev/thorough`

## 결과

manifest의 주요 엔트리 후보를 정확히 13개로 확정하고, 13개 parent-invoked
stage/helper 및 `post-it` model-support와 분리했다.

- entry-router 13: `analyze-project`, `analyze-user`, `audit`,
  `autopilot-apply`, `autopilot-code`, `autopilot-design`, `autopilot-draft`,
  `autopilot-lab`, `autopilot-note`, `autopilot-refine`,
  `autopilot-research`, `autopilot-ship`, `autopilot-spec`
- parent-invoked 13: `code-*` 5개, `design-*` 6개,
  `draft-refine`, `draft-strategy`
- model-support 1: `post-it`

모든 27개 manifest 설명은 구체적인 영문 `Use when`/`Not for` 또는
parent 전용 `Use only when` 경계를 유지한다. primary routing 후보는 오직
`entry-router` 13개다.

## 구조 변경

1. `core/WORKFLOW.md`, `core/CONVENTIONS.md`,
   `core/DESIGN_PRINCIPLES.md`, `capabilities/README.md`에
   pre-approval metadata → post-approval owner → assigned stage 경계를
   portable 의미로 먼저 반영했다.
2. canonical/Claude 엔트리 `SKILL.md`에는 manifest frontmatter, 승인 경계,
   핵심 owner 계약 포인터, 정확히 하나의 `Reference Index`와 owner edge만
   남겼다. 전체 실행 절차는 승인 후
   `references/owner-execution.md`에서 읽는다.
3. 중복 엔트리 README 6개를 제거했다. `autopilot-draft/conventions/`는
   `references/convention-*.md`로 옮겨 엔트리 Skill 자원을 한 단계
   `references/` 아래로 통일했다.
4. canonical → Claude native → Claude plugin projection을 생성기로
   동기화했다. Codex/OpenCode는 portable capability에서 생성하는
   sibling-native projection을 유지하며 Claude 실행 본문을 복제하지 않는다.
5. 잘못된 CommonMark `](<agent-home>/...)` 포인터를 label + inline
   `<agent-home>` 경로로 정규화하고 재발 방지 검사를 추가했다.

## 정적 크기

| Surface | 변경 전 합계/최대 | 변경 후 합계/최대 |
|---|---:|---:|
| canonical | 115,245 / 11,813 bytes | 29,828 / 2,448 bytes |
| Claude native | 115,245 / 11,813 bytes | 29,828 / 2,448 bytes |
| Claude plugin | 115,245 / 11,813 bytes | 29,828 / 2,448 bytes |
| Codex native | 35,173 / 2,843 bytes | 35,173 / 2,843 bytes |
| OpenCode native | 33,717 / 2,731 bytes | 33,717 / 2,731 bytes |

이는 정적 UTF-8 byte 측정일 뿐이다. tokenizer, 실제 활성 context,
billing, cost, savings 또는 ROI로 해석하지 않는다.

## Runtime support / local projection / masking 경계

| Runtime | 공식 runtime support | local projection | masking 판정 |
|---|---|---|---|
| Claude Code | Skill 설명 기반 선택과 invocation 시 본문 로드, custom agent Skill preload를 지원한다. | canonical router/reference를 Claude native와 plugin에 동일 투영한다. | custom subagent가 user/project `CLAUDE.md` 계층을 상속할 수 있으므로 profile 선택과 물리적 전체 masking을 동일시하지 않는다. |
| Codex | Skill progressive disclosure와 계층형 `AGENTS.md` discovery를 지원한다. | `capabilities/`에서 native Skills/plugin을 생성하며 `capability-info` 13/13이 native Skill을 확인했다. | 검증된 per-worker project-instruction disable switch가 없어 prompt isolation + 명시적 fallback만 주장한다. |
| OpenCode | skill tool의 on-demand load, agent별 Skill permission, rules/instructions 결합을 지원한다. | `capabilities/`에서 native Skills와 commands를 생성하며 `capability-info` 13/13이 native Skill을 확인했다. | 검증된 물리적 project-instruction masking switch가 없어 prompt isolation만 주장한다. |

공식 근거:

- Codex: [Skills](https://learn.chatgpt.com/docs/build-skills.md),
  [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)
- Claude Code: [Skills](https://code.claude.com/docs/en/skills),
  [Subagents](https://code.claude.com/docs/en/sub-agents)
- OpenCode: [Skills](https://opencode.ai/docs/skills/),
  [Rules](https://opencode.ai/docs/rules),
  [Agents](https://opencode.ai/docs/agents)

## 검증

최종 명령과 결과는 `test_logs/final-verification.md`에 기록했다.

- generation, routing, capability topology, entry-layer gate,
  skill-conformance, strict footprint, generated projections: PASS
- adaptation boundary: PASS; 기존 문서화된 concrete Claude/model reference
  91건 경고 유지
- Codex runtime projection 및 hook trust: PASS
- Codex/OpenCode `capability-info`: 각각 13/13 PASS
- 별도 read-only 최종 리뷰: 첫 pass에서 CommonMark 결함 발견·수정 후 PASS
- worker-bootstrap v5 kernel/type 파일: 기준 커밋과 byte-for-byte 동일

## 기존·무관한 실패 분리

- `skill-creator/scripts/quick_validate.py`는 저장소 고유 frontmatter
  `argument-hint`를 허용하지 않는다. `23c86bea`와 최종본이 동일하게
  실패하므로 이번 변경의 회귀가 아니다. 저장소의 27-classification
  conformance가 authoritative gate다.
- 격리된 `/tmp` archive 형태의 과거 projection runner는 기준/변경본 모두
  `legacy artifact root was not selected for orientation`에서 실패했다.
  canonical linked-worktree의 최종 `generated-projections.test.sh`는 PASS다.
- read-only 등록 test worker의 보고서 쓰기는 spec marker sandbox 경계에서
  정체되어 정상 종료했으나, 실행 검증은 PASS였고 이후 별도 reviewer와
  main-session 전체 매트릭스로 재검증했다. source 결과에는 영향이 없다.

## 결론

승인 전에는 축약된 manifest routing metadata만 사용하고, 승인 후 선택된
owner만 단일 owner reference를 읽으며, depth-2 worker는 담당 stage contract만
읽는 구조가 13개 엔트리 전반에 일관되게 적용됐다. worker-bootstrap v5
구조와 runtime-owned 상태는 변경하지 않았다.
