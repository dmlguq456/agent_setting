---
aspect: coding_convention
last_init: 2026-05-26
version: 2.5
---

# 코딩 컨벤션 (cross-project default·fallback)

> **per-project 1순위 — 본 파일 침범 X**: `<cwd>/.claude_reports/analysis_project/code/experiment_conventions.md` 가 per-project source of truth. 본 파일은 _부재 / 신규 repo 시작 / 사용자 의도 추정_ 자리만 default. 충돌 자리는 per-project 우선.

> 갱신 — `/analyze-user coding_convention` (전체 재추출) / `/notes --scope user coding_convention <text>` (한 줄 메모 append).

## 1. Model 폴더 구조

신규 repo default — 한 모델 = 한 폴더 + 표준 파일 묶음. variant 추가 = _폴더 복사 + `_VARIANT_MAP` dict 한 줄_.

```
<package>/
├── _config.py            # resolve_config / _VARIANT_MAP
├── inference.py          # public API + _BaseInference + subclass
├── export.py             # HF upload/download/export (선택)
├── run.py                # CLI entry (importlib dispatch)
├── models/<ModelName>/
│   ├── __init__.py
│   ├── main.py / main_infer.py     # entry (train / inference)
│   ├── engine.py / engine_infer.py # train/valid loop / chunk-level infer
│   ├── model.py / dataset.py / loss.py
│   ├── configs/*.yaml
│   └── modules/
│       ├── module.py     # model-level building block
│       └── network.py    # 더 저수준 layer
└── utils/                # 횡단 utility 단일 저장소
```

- 패키지 root 에 `_config.py` (private 접두) + `inference.py` (public API) + `export.py` (HF 선택). variant 는 `models/<Variant>/` 아래 표준 파일 셋으로 묶음.
- 폴더명 `PascalCase_with_underscore` (`TF_Restormer`, `SR_CorrNet_SS`), package level `snake_case` (`tf_restormer`, `sr_corrnet`). spelling 동일, case 만 다름.
- variant 추가 비용 _폴더 복사 + `_VARIANT_MAP` dict 한 줄_ 수준. 단일 variant 자리 (`TF_Restormer`) 든 세 variant 평행 (`SE` / `SS` / `CSS`) 든 같은 골격.
- variant 간 helper 중복 (`sinusoids` / `_multiframe` / `filtering`) 허용 — _변형 독립성_ 우선, DRY 강제 X. 한 변형 수정해도 다른 변형 안 깨짐.
- `utils/` 한 자리에 횡단 helper 몰아넣음 (`util_engine.PBAR_FMT`, `util_engine.format_pbar`, `utils.decorators.logger_wraps`, `utils.dnsmos_models/`, `utils.NISQA_models/`, `utils.km/`).

```python
_VARIANT_MAP = {
    "TF_Restormer": "tf_restormer.models.TF_Restormer",
}
```

## 2. Config 메커니즘 (yaml + anchor + ${VAR})

- pure YAML (PyYAML `safe_load`). hydra·dynaconf X.
- argparse 는 entry point 5-7 인자만, 나머지 hyperparameter 는 전부 yaml.
- anchor `&var_*` + alias `*var_*` 적극. 상단 `# ==== Key Variables ====` 또는 `# ⚡⚡⚡ key variables ⚡⚡⚡` 박스 안 anchor 정의 + 본문 alias 참조 = central tuning surface.
- section 사이 `# ------------------- #` separator 또는 박스 주석 일관.
- yaml `model:` 키가 `Model.__init__` 인자와 1:1 — `Model(**config["model"])` 한 줄로 동작.
- magic 값 옆 단위·의미 inline 주석 — 예 `N_h: 150 # ~1.2s at frame_shift=64, fs=8000`, `taps_freq: [1,1] # [Future, Past]`.
- 최상단 두 줄 — `project: "[Project] ..."` (변경 금지 표시) + `notes: "..."` (변경 기록 표시).
- `engine.optimizer.name` 한 줄 선택 (`"AdamW"`) + 각 optimizer 별 sub-block (미사용 옵션도 yaml 안 참조용 유지).
- `${VAR}` env placeholder 지원 (`expand_env_vars`), 미설정 시 `ValueError`. 확장은 dataset 객체 생성 시점까지 지연 (lazy).
- CLI override 는 `--gpuid` 만 yaml 위 in-place mutate. 그 외 CLI 인자는 yaml 안 덮어쓰기 X.
- `_VARIANT_ALIASES` 표 + `_normalize_variant()` 로 제한 alias 만 허용 (`"tf_restormer"` / `"tfrestormer"` / `"tf-restormer"` 셋). wildcard fuzzy match X — typo silent 통과 방지.
- `testsets.yaml` 카탈로그 deep-merge 패턴 — `load_config()` 가 YAML 한 파일 + `testsets.yaml` 카탈로그 deep-merge (TF_Restormer 자리 자세).

```python
# entry: argparse 5-7 인자, 나머지 yaml
parser.add_argument("--model", required=True)
parser.add_argument("--engine_mode", choices=["train", "train_ft", "inference", "test"])
parser.add_argument("--config", required=True)
parser.add_argument("--input"); parser.add_argument("--output"); parser.add_argument("--gpuid")
```

## 3. 변형 prefix / version naming

변형 분리는 _config 파일명_. ad-hoc python file prefix X.

- 같은 architecture 안 옵션 분기 — config 파일명 prefix (`baseline.yaml` 오프라인 vs `streaming.yaml` 온라인). 동일 `Model` + 동일 `Engine` 사용, 차이는 yaml `model.online: True/False` flag 하나 + dependent anchor.
- 데이터셋·STFT·tap 분기 — config 파일명에 dataset 슬러그 박음 (`1ch_WSJ_fix_2spk.yaml` vs `1ch_WHAMR.yaml`).
- fine-tune resume — `_ft<NN>_<base>.yaml` 한 줄 규칙. `_ft01_baseline.yaml` 자리 자동 resume.
- train phase 분기 — config 안 `train_phase` 키 (`pretrain` → `adversarial` 2 단계). 두 phase 가 같은 `Engine` class 공유, 분기는 yaml flag 한 자리.
- log 디렉토리 — `log/log_{train_phase}_{config_name}` (또는 `log/log_{config_name}` 자리). config 이름이 곧 trial id.
- HF Hub repo ID 슬러그 — `shinuh/<package-slug>-<variant>-<config-slug>` (`shinuh/tf-restormer-baseline`, `shinuh/sr-corrnet-ss-1ch-wsj-fix-2spk`).
- backward-compat fallback — `resolve_log_base()` 가 신규 naming → 구 `_to48k` naming 순으로 디렉토리 존재 확인 (TF_Restormer 자리).

## 4. Preferred layer

본 절은 per-project 1순위 침범 X. cross-project 공통 default:

- norm — `nn.LayerNorm` 기반. RMSNorm 보조 가능 (output 직전 한 번 일관).
- block — pre-norm (`y = LN(x); y = block(y); return x + y`).
- `nn.Module` subclass + 명시 forward. `nn.Sequential` 은 짧은 MLP / 짧은 임베딩 자리만.
- nested local class 패턴 — 외부 노출 X 자리 부모 class 안 정의 (`TF_Block` 안 `FreqModule` / `TimeModule` local class).
- `@torch.no_grad()` 데코레이터 — grad 불필요 분리 가능 자리 (correlation 계산 자리 등).

**TF_Restormer per-project 자료 (참고)**:
- norm — `nn.LayerNorm` + `nn.InstanceNorm2d` (`ConvBlock`).
- 2D feature path 입구 — `nn.Conv2d(2, d_model, (3,3), padding=(1,1))`.
- attention — `F.scaled_dot_product_attention` + RoPE (`rotary_embedding_torch`).
- K/V 압축 — Linformer 스타일 learned projection `Ekv` (`F_Linear`, `kv_shared` 옵션).
- Macaron-style FFN-wrap — `ffn → sa(+ca) → ffn`.
- `ConvFFN` — LayerNorm + Conv1d + SiLU GLU split + Conv1d → 0.5 residual.
- online 자리 Mamba (`mamba-ssm` 의 `Mamba`).

**SR_CorrNet per-project 자료 (참고)**:
- norm — LayerNorm + RMSNorm (output 직전 한 번).
- 단발 helper 는 nested class / nested function (`_collate` 의 `prepare_*`, `loss.A_RI_loss`, `Encoder.get_correlation`) — 노출 최소화 + 맥락 근접.

신규 layer 도입은 명시 컨펌 필요.

## 5. Framework 선호 (pure PyTorch)

- pure PyTorch. Lightning·accelerate·fabric 같은 wrapper X. multi-GPU 도 직접 처리.
- core deps 안 lightning / accelerate 없음.
- `Engine.__init__` 가 model.to(device) / optimizer / scheduler / dataloader / writer / ckpt loader 직접 wiring.
- batch loop 는 raw `for batch in dataloader: zero_grad / backward / step` 패턴.
- `clip_grad_norm_` 직접 호출 (`clip_norm` 값 있을 때만).
- GPU 수동 — `gpuid = tuple(map(int, config["engine"]["gpuid"].split(',')))` + `torch.device(f'cuda:{gpuid[0]}')`.
- 보조 라이브러리 통일 — `loguru` 로거, `tqdm` progress bar, `tensorboardX` training log.
- PyTorch pin — `torch>=2.6,<2.10`. `requires-python = ">=3.10"`.

```python
self.device = torch.device(f'cuda:{gpuid[0]}')
self.model = model.to(self.device)
for batch in dataloader:
    self.optimizer.zero_grad()
    loss = ...
    loss.backward()
    if clip_norm:
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), clip_norm)
    self.optimizer.step()
```

## 6. Metric set (domain §6 와 짝)

도메인별 분기. cross-project default 없음, task 별 별도 정의. task 가 달라 metric / loss 묶음을 cross-project default 로 추출 불가.

- signal fidelity — `SI-SDR / SI-SDRi` (`PIT_SISNR_time`, `PIT_SISNR_mag`, `SISNRi`), `LSD / PESQ-WB·NB / STOI / ESTOI`.
- perceptual quality — `DNSMOS` (onnx, `utils/dnsmos_models/`), `NISQA` (`utils/NISQA_models/`), `UTMOS / UTMOSv2`, `sBERT` (SpeechBERTScore).
- pretrained metric 모델 묶음 — `utils/dnsmos_models/` (onnx) / `utils/NISQA_models/` / `utils/km/` (k-means).
- 다중 metric 합산 — yaml `loss_weight` block, e-notation 가독성 (`se: 1.0, ssl: 1.0e+2, gan: 1.0e-3, fm: 0.1, pesq: 1.0e-4`).
- PIT 자리 — main loss 에서 best perm idx 반환 → aux loss 가 같은 perm 으로 계산 (permutation consistency).
- training-time loss 예 — `SSL_FM_Loss` (Wav2Vec2 feature matching), `MS_STFT_Gen_SC_Loss` (multi-scale STFT spectral convergence, log-compression `tau=1e-4`), `Time_Domain_L1`, `HF_Loss` (high-freq), `torch-pesq`, `torch-stoi`, `utmosv2`.
- task 별 loss 묶음 — SE 자리 `MSE_complex` + `TimePlusMultiResTFL1Loss`. SS 자리 `PIT_SISNR_time` + `PIT_SISNR_mag` + `SISNRi`. CSS 자리 `MSE_complex` + multi-task BCE (main + aux + residual + VAD + LOC + presence).
- BSS metric 옵션 — `mir_eval` 자리 `eval_SDRi` flag.

## 7. Log·ckpt

- 디렉토리 base — `log/log_{train_phase}_{config_name}/{weights,tensorboard}/`. model 폴더 안 생성, `runs/{run-id}/` 같은 trial id 디렉토리 X.
- adversarial 변형 자리 discriminator 별도 `weights_D/`.
- ckpt 파일명 — `epoch.NNNN.pth` (4 자리 zero-pad) + `best_model.pth`.
- root log dump — `models/{model}/log/system_log.log` (loguru `mode="w"` 매 실행 덮어쓰기).
- TensorBoard scalar key — 슬래시 prefix (`Loss/train`, `Loss/{part}`, `SISNRi/{part}`, `Pres_acc/{part}`, `LR`) 일관.
- progress bar 색 — `YELLOW` (train) / `RED` (valid) / `WHITE` (test).
- `pbar.set_postfix(util_engine.format_pbar(dict_loss))` — loss dict 한 helper 일관 포매팅.

**Logging library** — loguru + tqdm:

- `from loguru import logger` 한 줄. 사용자 정의 logger X, `print()` X.
- 레벨 — `logger.info()` 메인 흐름, `logger.warning()` fallback, `logger.debug()` 내부 detail.
- `@logger_wraps()` 데코레이터 (`<package>.utils.decorators`) 가 main / dataset / loss 클래스에 일관 적용 — 진입/종료 자동 로그.
- 일부 핵심 class 자리는 `# @logger_wraps()` 주석 처리 상태 유지 — 필요 시 켜는 toggle.
- `logger.disable("<package>")` + `logger.enable("<package>")` — 사용자 향 inference factory 자리 silence 의무.
- tqdm `bar_format=util_engine.PBAR_FMT` 고정, `dynamic_ncols=True`.
- 변형마다 `log/system_log.log` 별도 append (`logger.add(..., mode="w")`).

**HF Hub first-class**:

- `sync_checkpoint_to_home(checkpoint_path, variant_short, config_name)` — 매 epoch 끝 home 디렉토리 sync.
- export → upload → download → `from_pretrained(repo_id=...)` 한 사이클이 `export.py` 한 모듈에 정리.
- `.upload_hash` SHA256 캐시로 미변경 ckpt 재업로드 skip (`force=True` override).
- repo_id 자동 슬러그 — `shinuh/<package-slug>-<variant>-<config-slug>`.
- 배포용 ckpt 형태 — `checkpoints/{config_stem}/model.pt` + `config.yaml` 동봉 (config 옆에 같이 배포).
- `_strip_profiling_keys()` 가 ptflops/thop inject 한 zero-tensor 제거. `_MODEL_TOPLEVEL_PREFIXES` 상수로 compiled-model state_dict prefix 정규화 (TF_Restormer 자리 자세).
- `from_pretrained` 가 HF Hub repo ID / 로컬 디렉토리 / 로컬 파일 / None (default path) 네 경로를 한 메서드로 받음 — 사용자 입력 형식 유연성.

## 8. Seed / reproducibility

- `torch.manual_seed` / `np.random.seed` / `random.seed` / `torch.use_deterministic_algorithms` 호출 X.
- augmentation 마다 stdlib `random` 직접 호출 — 매 epoch · 매 worker 마다 결과 다름이 의도 (다양성 augmentation 목적).
- dataset split 은 SCP (Kaldi-style script) 파일로 freeze — `data/create_scp/create_scp_*.py` 한 번 생성 후 고정.
- 재현 contract — _exact-bitwise reproducibility_ 가 아니라 _distributional reproducibility_ (config + seed-less augmentation 의 통계적 동등성).
- 데이터 augmentation 비결정성 자리 — RIR convolution / diffuse noise / circular array rotation 같은 비결정 augmentation 이 multi-channel SS 자리에서도 같은 정신.
- 신규 repo 자리 사용자 명시 요청 없으면 default = no explicit seed. 고정 필요 자리는 명시 컨펌 후 도입.

## 9. Naming convention

- 함수·변수·module file = snake_case (`get_dataloaders`, `load_config`, `apply_cli_gpuid`, `_strip_profiling_keys`, `frame_length`, `fs_in`, `_extractor`, `calculate_loss`).
- private 접두 `_` = 내부 호출 전용 (외부 API 노출 X).
- class = PascalCase 또는 PascalCase + underscore (`SEInference`, `EngineInfer`, `MultiHeadSelfAttention`, `LinformerAttention`, `ConvFFN`, `MambaV1Block`).
- 도메인 약자는 대문자 보존 — class 안에서도 약자 안 깨짐. `TF_Encoder`, `TF_Decoder`, `MHSA`, `LinMHSA`, `MS_STFT_Gen_SC_Loss`, `SSL_FM_Loss`, `HF_Loss`, `STFT`, `iSTFT`, `RoPE`, `FFN`, `F_Linear`.
- variable 약자도 보존 — `Ekv`, `kv_shared`, `fs_src`, `fs_in`, `n_head`, `d_model`, `d_hidden`, `d_state`, `tau`, `alpha`, `beta`, `gamma`, `proj_len`, `seq_len`, `B / M / F / T / N / L / K / C`.
- 짧은 변수명 + 도메인 약자 우선. 한두 글자 (`i / j / k / b / s / t`) 짧은 scope 안 허용.
- 한국어 변수명·주석 X. 코드 안 주석은 모두 영어. 한국어는 paper 본문·메모 자리만.

**도메인 약자 묶음**:

- TF / FT (time-frequency) / freq / time
- MHSA / SA / CA / MHCA / FFN / RoPE
- PIT / SISNR / SDR / SDRi / SISNRi / SS / SE / CSS / VAD / DOA / LOC
- STFT / iSTFT / PESQ / STOI / DNSMOS / NISQA / MOS / UTMOS / sBERT
- SSL / FM / GAN / HF / km (k-means) / Mamba / SSM
- Ekv / kv_shared / `n_head` / `d_model` / `d_hidden` / `d_state` / `d_conv`

**Shape 주석** — inline `# B, F, T` 패턴, docstring 보다 inline 우선. 매 reshape / permute / unfold 다음 줄 shape 주석. complex ↔ RI-stack 변환 명시 (내부 complex, 출력 RI 마지막 차원 stack). list-of-tensor 자리 `*N` 표기 (`# [B, F, T]*N`).

```python
# x : (B), 2M, F, T
if len(x.shape) == 3:
    x = x.unsqueeze(0)
x_r, x_i = x.chunk(2, dim=1)
x = torch.complex(x_r, x_i)        # B, M, F, T
x_mf = self._multiframe(...)        # B, L, M, F, T
```

**Import 순서** — 표준 → 외부 → 로컬, 그룹 사이 빈 줄. `from __future__ import annotations` 는 type hint 있는 module 상단에 적극 (PEP 604 `int | None` 활성 목적).

**일관성 어긋남 (TF_Restormer 자리)** — `import torch` 와 `import torch as th` 둘 다 두고 한 파일 안 혼용 (`th.empty`, `torch.Tensor`). 의도된 단축.

**Type hint (per-project 분기)** — 신규 작업 default = TF_Restormer 후속 패턴 (PEP 604 `int | None`, `tuple[Tensor, ...]` + `from __future__ import annotations`). 기존 repo 안 작업은 그 repo hint 강도 유지 (SR_CorrNet 자리는 type hint 거의 X, 문자열 forward-ref `'Optional[torch.Tensor]'`).

**Inline 주석 표기** — `#!` 강조 / `#*` 주의 (`#! Truncate`, `#* B, T, F, C`, `#! VAD frame ratio < 10% -> no speech assumed`). 긴 함수 (8 단계 이상) 자리 box-style 주석 (`# ── N. 제목 ──...──`).

**Docstring 비대칭** — public-facing 모듈 (`inference.py`, `export.py`) 자리 풀 Google-style + reST 혼용 (Args / Returns / Raises / Note / Example). internal engine / model / module 자리 짧은 한 줄 또는 shape comment 만. _독자별 cost 차별화_ — 사용자 향 자리만 자세.

**함수 길이** — 50-100 라인 표준. `_train()` 100 라인 안팎, `_validate()` 80 라인 안팎. 한 함수 안에 데이터 전처리 → forward → loss → backward → pbar → logging 직렬 박음. helper 추출 자제. 학습 흐름이 두 단계 이상 복잡해질 때만 helper 분리 (`_downsample_8k`, `_discriminator_step`, `_generator_step` 같은 자리).

**상수 / module top-level** — `_` prefix + ALL_CAPS (`_MODEL_TOPLEVEL_PREFIXES = ("input_embed", ...)`, `_DEFAULT_CKPT_HOME = Path(__file__).resolve().parent / "checkpoints"`, `_FALLBACK_FS_SRC = 48000`). 읽기 전용 + private (모듈 외 노출 X).

## 10. Dependency 관리

- `setuptools` build backend + `uv` lock + `pyproject.toml` PEP 621 `[project]` + 다수 optional extra.
- `requires-python = ">=3.10"` 고정. PyTorch pin `torch>=2.6,<2.10` (upper bound 명시).
- `requirements.txt` X — `uv sync --extra ...` 가 표준 install command.
- PyTorch wheel routing — `[tool.uv.sources]` + 6 explicit index (cpu / cu118 / cu124 / cu126 / cu128 / cu130).
- `[tool.uv] conflicts` 가 accelerator extra 간 동시 선택 차단. `[[tool.uv.index]] explicit = true` transitive 회피.

**Extra 그룹**:

- core (no extra) — inference-only deps
- `cpu` / `cu118` / `cu124` / `cu126` / `cu128` / `cu130` — PyTorch wheel 선택
- `train` — tensorboard / wandb / torchinfo / ptflops / thop + augmentation + metrics
- `metrics-*` (per-project) — `metrics-intrusive` (pesq / pystoi / mir-eval / pysptk / pyworld / fastdtw / joblib) / `metrics-nonintrusive` (DNSMOS onnxruntime) / `metrics-neural` / `metrics-semantic` / `metrics-all`
- `hub` — `huggingface-hub`
- `dev` — train + pytest
- `full` — train + mamba + cu126/cu124 + hub 합집합

- non-PyPI source — `utmosv2 = { git = "..." }` 같이 `[tool.uv.sources]` 명시.
- `[tool.setuptools.package-data]` — variant 의 `configs/*.yaml` + ckpt / model 파일 wheel 안 포함 (config 는 코드 옆에 코드와 같이 배포).
- pyproject 상단 주석 — `# After modifying dependencies, run: uv lock` 평어로 박음 (유지보수 동선이 파일 자체에 안내).

**Error handling**:

- 표준 예외 `KeyError` / `FileNotFoundError` / `ValueError` / `RuntimeError` / `ImportError`.
- 메시지 안 다음 단계 (해결법) 같이 박음:

```python
raise ValueError(
    f"Environment variable '${{{var_name}}}' is not set. "
    "Set it via `export VAR=...` in your shell, "
    "or use direct paths (db_root / rir_dir) in your YAML config."
)
raise ImportError(
    f"Install with: uv sync --extra hub  (or: pip install tf-restormer[hub])"
) from None
```

- `raise ... from exc` 체인 명시, `from None` 자리 자체 traceback 숨김.
- ImportError 메시지에 정확한 `uv sync --extra ...` 박음 — user-facing diagnostic 이 dep 묶음 설계와 짝.
- 두 단계 fallback 패턴 — `weights_only=True` 먼저 시도, 실패 시 키워드 자리 문제일 때만 fallback + warning (TF_Restormer 자리 자세).

## 운영 동선이 코드에 박힘 (보조 원칙)

- `_ft<NN>_<base>.yaml` 한 줄 fine-tune resume 자동 규칙.
- `best_model.pth` / `epoch.NNNN.pth` 우선순위로 ckpt 자동 탐색.
- README 의 filename convention + resume vs fresh start + folder semantics 굵게 강조 + bullet 정리. "왜" 같이 박음 (`pretrain_weights/` 는 read-only origin).
- variant-specific quirk 자리 분기 + warning — `_VARIANT.endswith("_SS")` runtime 분기 + `logger.warning` 자동 안내.
- backward-compat 처리 — `resolve_log_base()` 가 신규 → 구 naming 순으로 디렉토리 존재 fallback.
- **사용자 입력 형식 유연성** — `from_pretrained` / `process_*` 가 여러 입력 경로 한 메서드로 받음. 5 단 추상화 사다리 (`process_file > process_waveform > process_stft > process_stft_chunk > create_session.feed`) 자리 사용자가 제어 수준 선택.

→ 코드 자체가 운영 가이드 역할 — 사용자가 별도 cheatsheet 없이 코드만 보고 다음 단계 알 수 있게 박음.

## 코드 수정 4 원칙 (autopilot-* prepend)

1. **최소 수정** — 기존 폴더 복사 후 변형. 새 layer 도입 default X.
2. **원래 layer 1순위** — §4 list 우선. 새 layer 는 명시 컨펌.
3. **마이너 변경 = config** — `model.py` 직접 수정 X, `config.yaml` 가능 자리는 config 로.
4. **변형 prefix** — fine-tune 변형은 §3 패턴 (`_ft<NN>_<base>.yaml` / train_phase suffix).

## 사용자 수동 메모

> 본 절은 사용자 영역. `/notes --scope user coding_convention <text>` 가 append. analyze-user 는 읽기만 함.

_(아직 비어 있음 — `/notes --scope user coding_convention add ...` 로 첫 항목 추가)_

## 갱신 이력

- 2026-05-26 : v2.5 — 중간 복원. v3 ~4.5K 다이어트 자리에서 draft 의 근거·repo 분기·코드 anchor 보강해 ~7-10K 목표. 10 절 구조 + 평어 단정형 + 4 원칙 + 수동 메모 절 유지, 운영 동선 보조 절 신설.
- 2026-05-26 : v3 — 다이어트 (~8.1K → ~4.5K tokens). 11 절 → 10 절 (Open Questions 절 제거, 본문 평어 fragment 압축).
- 2026-05-26 : v2 — analyze-user phase 5 본문 작성. 4 QA axis 통과.
- 2026-05-26 : v1 skeleton 신설.
