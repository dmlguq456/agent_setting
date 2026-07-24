# Pipeline summary

Status: prevention contracts landed; source implementation pending.

재현은 owner bootstrap의 표현 불완전성과 validator 누락을 동시에 확인했다.
수정은 capability mode를 owner 행동 knob로, portable unit/worker mode를 depth-2
specialization으로 분리하며, 기존 `mode`는 legacy read-only 호환으로 한정한다.

stage-dispatch v28(SD-84), dispatch-profiles v3(DP-18/19), Fleet v23(F-40)을
canonical lock transaction으로 갱신하고 각 직전 버전 snapshot을 보존했다.
