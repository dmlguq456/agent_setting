---
aspect: coding_convention
owner: 사용자
mode: init
updated: 2026-05-26
source: code repo 2 (TF_Restormer / SR_CorrNet)
consensus: 3-instance (run A/B/C, 강한 일치)
---

# 07. 코딩 컨벤션

> speech model 연구 코드 패턴. per-project `experiment_conventions.md` 가 1순위, 본 파일은 cross-project fallback. 개발팀·기획팀·메인 Claude(autopilot-code 4원칙 prepend) 참조.

## 1. 폴더 구조 — "한 모델 = 한 폴더" 강제 (3/3)

```
<pkg>/models/<Variant>/
  model.py        # class Model (진입 클래스명 항상 Model)
  engine.py       # class Engine(object) — train loop
  engine_eval.py  # 평가
  engine_infer.py # 추론
  main.py         # def main(args)
  main_infer.py
  loss.py
  dataset.py      # get_dataloaders
  modules/
    module.py     # 조립 블록
    network.py    # primitive layer
  configs/*.yaml
```

- 루트 `run.py` 가 `importlib` 동적 dispatch (`resolve_module_path`) — variant 추가 시 run.py 무수정.
- `modules/` 2분할: `module.py`(조립 블록) + `network.py`(primitive layer).
- 패키지 packaging: `pyproject.toml` + **uv** + setuptools. CUDA 버전별 explicit index(`pytorch-cu124` 등) + extra conflicts, 기능별 잘게 쪼갠 optional-deps(`metrics-intrusive`/`metrics-neural`/`train`/`mamba`/`hub`). py ≥ 3.10.
- 공개 라이브러리 API: `{SE,SS,CSS}Inference` + `_BaseInference`, `from_pretrained(checkpoint_path=...)` HF Hub 연동. `library_examples/` 폴더로 사용 예시 제공.

## 2. Config 메커니즘 (3/3)

- **순수 YAML + PyYAML `safe_load`** — hydra 미사용.
- 최상위 **단일 `config:` 키** 강제. `&var_*`/`*var_*` **YAML anchor 를 변수 선언 메커니즘**으로 적극 사용 (Key Variables 블록 → 본문 주입). ASCII 배너 주석(`# ====== STFT ======`)으로 섹션 구획.
- `model:` 섹션 = `Model(**config["model"])` 1:1 언팩. argparse 는 실행 제어(engine_mode/device 등)만.
- alias 정규화: `_config.py` 의 `_VARIANT_MAP`/`_VARIANT_ALIASES` + `importlib.resources`. TF_Restormer 는 `testsets.yaml` catalog deep-merge.
- config 파일명에 **실험 조건 인코딩** (SR_CorrNet 다중 setting 한정): `{ch}ch_{dataset}_{spk}` 식 (`UMA_7ch_varying_0_3spk.yaml`, `AMI_8ch_fix_2spk.yaml`). TF_Restormer 는 baseline/streaming/testsets 소수 config.

## 3. 변형 prefix / 분기 패턴 (3/3)

- **task 분기 = 폴더/클래스 suffix**: `SR_CorrNet_{CSS,SE,SS}`.
- **fine-tune = flag**: `--engine_mode train_ft`.
- **train phase = config enum**: `train_phase: pretrain | adversarial` (TF_Restormer G/D 적대 학습).
- **online/offline = config bool**: `online: False`(TF-Locoformer offline) / `True`(Mamba streaming).
- 버전은 클래스명 아닌 path/주석에만.

## 4. Preferred layer — 도메인 layer set (3/3)

- 입력 도메인: 복소 STFT `(B,F,T,2)` real/imag. **Conv2d(2→d_model) head** 로 임베딩.
- **RoPE** 필수 (`rotary-embedding-torch`).
- **TF dual-path** time/freq block (Locoformer 계열), **Linformer-style attention**(`Ekv` 공유) 또는 직접 구현 MHSA(`scaled_dot_product_attention` + sdp_kernel).
- **ConvFFN**(Conv1d/Conv2d + gate).
- norm·activation 이 repo 간 진화: TF_Restormer = **LayerNorm + GLU**, SR_CorrNet = **주로 RMSNorm + SwiGLU**(신컨벤션 — cross-attn KV 등 일부 LayerNorm 잔존). SwiGLU 는 SR 전역 일관.
- **Mamba/SSM = online/streaming 모드 전용 옵션** (`mamba` extra). SSL feature-matching loss(WavLM 등).

## 5. Framework (3/3)

- **pure PyTorch**(`>=2.6`) — lightning/accelerate 미사용. 손수 `class Engine(object)` train loop.
- `torch.compile` 사용 (ckpt 에서 `_orig_mod.` prefix strip).
- 로깅: **loguru** + `@logger_wraps()` 데코레이터.

## 6. Metric set (3/3)

- 기본: **SI-SNR/SI-SNRi, SDR/SDRi, PESQ, STOI** + PIT(permutation invariant).
- TF_Restormer 는 **registry dispatcher**(`compute_metric`, lazy import + device cache)로 5-family 계층화: intrusive(PESQ/STOI/SDR/LSD/MCD) / nonintrusive(DNSMOS/NISQA) / neural(UTMOS/WVMOS) / semantic(SpeechBLEU/BERTScore) / asr(WER/CER). config `metrics` 리스트로 토글.
- SR_CorrNet 은 `util_metric.py` 함수 직접 구현(SISNR/SDR/PESQ/STOI + PIT permutations). → TF 가 SR 모음을 registry 로 진화.
- differentiable perceptual loss: torch-pesq / torch-stoi / utmosv2.
- PESQ 호출 패턴 두 repo 공통 재사용: `pesq.pesq_batch(fs, ..., 'wb', n_processor=20)`.

## 7. Log·ckpt 자리 (3/3)

- 로그·ckpt 가 **모델 폴더 내부**: `models/<Variant>/log/log_{phase}_{config}/{weights,tensorboard}/`.
- ckpt: `epoch.{:04d}.pth` (4자리) + `best_model.pth`. 주기 ckpt 는 `torch.save` 직접 write, **atomic write(`.tmp`→`os.replace`)는 `best_model.pth` 에만** (util_engine.py). dict 키 `{model_state_dict, optimizer_state_dict, epoch}`. 로드 시 `weights_only=True` + `_orig_mod.` strip.
- writer: **tensorboardX `SummaryWriter` 상속 래퍼**(`TBWriter`), wandb 보조.

## 8. Seed / reproducibility (관찰 3/3 — 단 이건 **모방 대상 아님**)

- 관찰: 두 repo 모두 **전역 seed/`cudnn.deterministic` 고정 코드 부재** (비-test 코드 grep 0건). 재현성은 YAML config 스냅샷 + ckpt resume + wandb 로깅에 의존. seed 고정은 테스트 코드(`random.seed`)에만.
- **신규 코드 의무**: train loop 에 seed 고정(`torch/numpy/random` + `cudnn.deterministic`) **추가**할 것 — 기존 부재를 따라하지 말 것.

## 9. Naming convention (3/3)

- 함수·패키지 `snake_case`, 클래스 `PascalCase`(진입 클래스 항상 `Model`), `_` prefix 내부 함수.
- **도메인 약자 대문자 보존**: `MHSA`, `RoPE`, `TF_Block`, `RMSNorm`. 변수 약어 `d_model`/`n_head`/`fs`/`estim`/`N_h,N_c,N_f`.
- prefix 관습: `util_` 모듈, `var_` anchor.
- `from __future__ import annotations` + PEP604(`X | None`). **Google-style docstring** + `# NOTE:`/`Design note:`/invariant 주석. 에러 메시지에 **행동 가능한 안내** 동봉.

## repo 간 진화 (신규 코드 권장 기준)

| | TF_Restormer (더 성숙) | SR_CorrNet |
|---|---|---|
| norm | LayerNorm | **RMSNorm** |
| activation | GLU | **SwiGLU** |
| metric | **registry dispatcher** + lazy import | 함수 직접 |
| infra | `_config.py` alias 정규화 · testsets catalog · adversarial G/D · 친절 에러 | flash_attention |

> 신규 코드는 **TF_Restormer 성숙 인프라(registry/lazy/alias 정규화/친절 에러)** + **SR_CorrNet 최신 layer(RMSNorm/SwiGLU)** 조합 권장.

## 10. 테스트·품질 메타 (관찰 제한 — 미관찰 자리 명시)

- 테스트: `pytest`(dev extra), `tests/test_*.py` (TF_Restormer 에 AB-comparison·migration 테스트 존재). 체계적 unit test 컨벤션은 관찰 범위 밖 — 신규 코드엔 smoke→functional 테스트 추가 권장.
- type-check/lint 도구(ruff/mypy 등) 설정은 source 에 미관찰. 새 라이브러리화 시 도입 권장.

## Open Questions

- 전역 seed 고정이 의도적 부재인지 누락인지 — 새 연구 코드엔 seed 고정 추가 권장(§8).
- type-check/lint·체계적 테스트 컨벤션 미관찰 — per-project `experiment_conventions.md` 가 1순위.

## 사용자 수동 메모

- 브랜치/PR 머지는 Claude가 선별 책임 (사용자 직접 리뷰 X). 머지 전 `git diff main...<branch>`로 실내용 확인 → 이미 main에 진전됐거나 회귀/중복이면 머지 안 함 → 충돌은 양쪽 의도로 해결(자동채택·`--force` 금지), 애매하거나 확정본 되돌리면 멈추고 질문 → 빌드 검증 후 커밋. "전부 합쳐"=선별 머지. 위임 범위는 _머지 신호·수확 자리_ 한정 — 자기 turn 본작업의 같은 turn self-merge 는 범위 밖 (2026-06-11 golden g3 확정).
