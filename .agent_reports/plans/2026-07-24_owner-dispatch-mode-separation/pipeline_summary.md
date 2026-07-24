# Pipeline summary

Status: complete; implementation integrated and pushed to `main`.

재현은 owner bootstrap의 표현 불완전성과 validator 누락을 동시에 확인했다.
수정은 capability mode를 owner 행동 knob로, portable unit/worker mode를 depth-2
specialization으로 분리하며, 기존 `mode`는 legacy read-only 호환으로 한정한다.

stage-dispatch v28(SD-84), dispatch-profiles v3(DP-18/19), Fleet v23(F-40)을
canonical lock transaction으로 갱신하고 각 직전 버전 snapshot을 보존했다.

shared validator와 Claude/Codex/OpenCode wrapper는 canonical
`--capability-mode`/`--worker-mode`를 지원하고 legacy `--mode`를 shape에 따라
호환 해석한다. owner의 stage mode 오염과 non-owner의 owner unit 사용은 registry,
prompt, spawn 이전에 fail-closed한다. Fleet는 정상 owner에 capability mode만 보이고
오염된 legacy slash-mode는 `mode!` conflict로 표시한다.

검증은 portable guards 358/358, Fleet 871/871, focused cross-adapter suites,
generated projection, adaptation boundary, 실제 Codex runtime projection과 doctor를
모두 통과했다. 구현 커밋은 `89b59d72`이며 격리 worktree cleanup도 완료했다.
