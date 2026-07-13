# Fleet cross-harness session titles

- Date: 2026-07-13
- Mode: dev
- Intensity: strong
- Component: agent-fleet-dashboard
- Spec significance: SPEC-SIGNIFICANT — F-17의 Claude-only 제목 계약과 Codex `slug` 폴백을 교체한다.

## Goal

Codex의 native state DB `threads.title`을 즉시 표시하고 JSONL `thread_name`을
compatibility fallback으로 유지한다. 기존 Haiku no-tools 제목 워커를
Claude/Codex 공용 fleet provider로 승격한다. provider가 없거나 실패해도 native
title 또는 slug로 안전하게 폴백한다.

## Contract

1. title precedence는 `fresh fleet sidecar -> runtime-native title -> slug`다.
2. sidecar는 Claude runtime home이 아니라 neutral local state에
   `<harness>/<sid>.json`으로 저장한다. 기존 Claude sidecar는 read-only migration
   fallback으로 유지한다.
3. Codex native title은 최신 `state_<version>.sqlite`의 `threads.title`을 read-only로
   읽고 `session_index.jsonl`의 `thread_name`을 tolerant fallback으로 쓴다.
4. refresher는 Claude와 Codex transcript를 모두 정규화하며, 기본 provider는 기존
   `claude -p --model haiku --disallowedTools ...`다.
5. `FLEET_TITLE_COMMAND`을 설정하면 shell 없이 argv template로 실행해 GPT 계열 등
   별도 no-tools wrapper로 교체할 수 있다.
6. worker spawn은 live fleet에서만 수행한다. `--json`, `--once`, demo/test 경로는
   관찰 전용으로 남는다.

## Implementation

1. PRD v4 snapshot 후 v5/F-21 계약과 pipeline state/summary를 갱신한다.
2. `titles.py`를 harness namespace + neutral state + Claude legacy fallback으로 확장한다.
3. `refresh_title.py`에 Codex transcript parser, provider command, shared scheduler를 추가한다.
4. Codex collector에 state DB/WAL + JSONL cache/native title/sidecar precedence를 추가한다.
5. Claude collector와 statusline을 neutral shared sidecar 계약으로 전환한다.
6. live fleet collector wrapper에서 shared scheduler를 호출한다.
7. hermetic unit tests, full fleet suite, mirror parity, syntax/smoke를 실행한다.

## Plan check

- 식별자 충돌 방지: sidecar가 harness namespace를 포함하는가? yes.
- provider 실패가 세션 표시를 지우는가? no, native title/slug가 남는다.
- custom provider가 shell injection surface를 여는가? no, `shell=False` argv만 쓴다.
- snapshot/JSON 명령이 worker를 몰래 띄우는가? no, live curses 경로만 schedule한다.
