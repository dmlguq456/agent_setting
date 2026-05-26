# 코딩 컨벤션 (Ui-Hyeop Shin)

> 사용자의 cross-project 코드 일관 패턴 — model 폴더 / config / prefix / preferred layer / framework / metric / log / seed. `/analyze-user coding_convention` 가 사용자가 명시한 코드 폴더 (cwd 자동 발견 + `--source <path>` 콤마 분리 복수) 스캔으로 추출·갱신. analyze-project doc mode 와 같은 패턴 — 하드코딩 path X, 사용자가 첫 호출 자리에 source 명시. autopilot-lab / autopilot-spec / autopilot-code / 개발팀 _new-lib_ 가 작업 시작 자리에서 default 로 Read.
>
> **우선순위**: 본 파일은 _cross-project default · fallback_ 자리. **개별 프로젝트의 컨벤션 (`.claude_reports/analysis_project/code/experiment_conventions.md`) 이 1순위 source of truth** — 본 파일은 per-project 부재·빈 자리만 보강. 충돌 자리는 per-project 우선, 본 파일이 _개별 프로젝트 컨벤션을 침범 X_.
>
> 갱신 — `/analyze-user coding_convention` (전체 재추출) / `/notes --scope user coding_convention <text>` (한 줄 메모 append).

## 모델 폴더 구조

(analyze-user 가 채울 자리 — sample 예시)
- 한 모델 = `model/{model_name}/` 한 폴더 묶음 단위
- 한 폴더 안 — `model.py` · `config.yaml` · `train.py` · `README.md` (선택)
- 여러 모델 = 같은 `model/` 안 별 폴더 — `model/TF_Restormer/` · `model/SR_CorrNet/`

## Config 메커니즘

- yaml 1순위 — `config.yaml` 위치는 모델 폴더 안
- argparse 보조 — config path / resume / output 같은 _런타임_ 옵션만
- hydra / dynaconf 미사용 (분석 결과로 보강)

## 변형 prefix 패턴

- base 옆 prefix 파일 — `_ft01_<variant>.{py,yaml}` · `_ft02_...` (fine-tuning 변형)
- 새 base = 새 모델 폴더 (별도 자리)
- prefix 의미 — `_ft<NN>_` 자리는 _현 모델 base 의 N 번째 fine-tuning 변형_

## Preferred layer (cross-project 빈출)

(analyze-user 가 채울 자리 — sample)
- TF / image restoration — MDTA / GDFN / LayerNorm2d
- Image SR — CorrAttention / ResBlock
- ASR (예정) — Conformer block (MHSA / Conv / FFN)
- Generic — `nn.LayerNorm` / `nn.Linear` / `nn.Conv2d`

새 layer 도입은 _명시 컨펌_ 필요 — 본 list 외 자리 추가 시 사용자에 한 줄 안내.

## Framework 선호

(analyze-user 가 채울 자리)
- PyTorch base — `torch >= 2.0`
- 학습 — pure PyTorch loop 또는 lightning 중 무엇이 cross-project 빈출인지 분석 후 보강
- distributed — accelerate / DDP / 단일 GPU 자리 분류

## Metric set (도메인별)

- TF restoration — PSNR / SSIM / SI-SDR / PESQ / STOI
- Image SR — PSNR / SSIM / LPIPS
- ASR (예정) — WER / CER
- 일반 — Acc / F1 / AUROC

## Log · ckpt 자리

- log — `runs/{run-id}/` 안 `metrics.json` + `log.txt` (또는 tensorboard / wandb)
- ckpt — `runs/{run-id}/ckpt/` 안 `best.pt` · `last.pt`
- run-id 형식 — `{date}_{slug}` 또는 단순 increment (분석 후 보강)

## Reproducibility 패턴

- seed — train.py 의 첫 자리에서 `torch.manual_seed(seed)` / `np.random.seed(seed)` / `random.seed(seed)` 묶음
- git hash — log 또는 config 에 한 줄 기록
- 데이터 split — `train.csv` / `val.csv` / `test.csv` 고정 (또는 split 함수의 seed)

## Naming convention

- 변수·함수 — snake_case (PyTorch 자리 자연)
- class — PascalCase
- 파일 — snake_case
- 모델 폴더 — PascalCase 또는 약자 대문자 (예: `TF_Restormer` / `SR_CorrNet`)

## 코드 수정 4 원칙 (autopilot-* 의 sub-agent 호출 자리에 자동 prepend)

1. **최소 수정** — 기존 모델 폴더 복사 후 변형, 새 layer 도입 default X
2. **원래 layer 1순위** — 위 _Preferred layer_ list 가 1순위. 새 layer 도입은 명시 컨펌 필요
3. **마이너 변경 = config** — `model.py` 직접 수정 X, `config.yaml` 가능한 자리는 config 로
4. **변형 prefix** — fine-tuning 변형은 위 _prefix 패턴_ 따라

## 사용자 수동 메모

(여기는 사용자 영역 — `/notes --scope user coding_convention <text>` 로 append)

## 갱신 이력

- 2026-05-26 : skeleton 신설 (analyze-user 로 채워야 함 — 사용자가 `/analyze-user coding_convention` 호출)
