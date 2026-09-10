# Pi 0.5 LIBERO 4090 Quickstart

目标：用单卡 RTX 4090 跑通 Pi 0.5 在 `lerobot/libero` 上的单任务族行为克隆训练，并用 LIBERO 仿真做无本体评测。

项目当前路径：

```text
E:\projects\robot
```

可选：把项目映射成短路径，规避训练框架对中文路径的兼容问题。

```powershell
powershell -ExecutionPolicy Bypass -File E:\projects\robot\scripts\setup_project_drive.ps1
cd /d R:\
```

## 1. 检查机器

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\pi05_4090_check.ps1
```

当前机器已验证到：

```text
GPU: NVIDIA GeForce RTX 4090, 24564 MiB
Python: 3.10.12
torch: ok
lerobot: ok
huggingface_hub: ok
```

建议正式训练前使用 Python 3.11 环境。

## 2. 登录和下载数据

先登录 Hugging Face，并确认已接受 `google/paligemma-3b-pt-224` 的模型许可。

```powershell
hf auth login
powershell -ExecutionPolicy Bypass -File .\scripts\download_libero_dataset.ps1
```

如果 Hugging Face SDK/CLI 在文件 HEAD 阶段失败，使用直连下载器：

```powershell
conda run -p E:\Project\lerobot_experiment\envs\lerobot312 powershell -ExecutionPolicy Bypass -File .\scripts\download_libero_direct.ps1
```

## 3. 数据质检

下载后执行：

```powershell
python .\scripts\check_lerobot_dataset.py `
  --dataset-root "$env:USERPROFILE\.cache\huggingface\lerobot\lerobot\libero" `
  --output .\artifacts\libero_qc.json
```

同时检查模型权重是否完整：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_pi05_task.ps1
```

如果模型正在下载，观察 `model.safetensors` 大小：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch_pi05_download.ps1
```

若本地缓存目录不同，把 `--dataset-root` 换成实际的 `lerobot/libero` 数据目录。

## 4. 训练

默认使用 4090 友好的 expert-only BC：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_4090.ps1
```

链路验证可以先跑 1 step：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_smoke_train_pi05.ps1
```

当前训练入口已经验证能启动，并且会使用单任务 episode 子集。若报 `google/paligemma-3b-pt-224` 或 `model.safetensors` 缺失，需要先补齐 Pi0.5 base checkpoint 和 PaliGemma tokenizer 缓存。

也可以用总控脚本串起校验、smoke train 和正式训练：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_pi05_full_pipeline.ps1 -TrainBatchSize 8 -TrainSteps 30000
```

若 OOM：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_4090.ps1 -BatchSize 4
```

## 5. 评测

先小样本 smoke test：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_lerobot.ps1 -Episodes 10
```

正式记录建议跑 500 episodes，并把结果填到：

```text
docs/pi05_libero_experiment_record.md
```

## 6. 产物说明

| 文件 | 用途 |
| --- | --- |
| `docs/pi05_libero_4090_training_workflow.md` | 完整技术方案 |
| `docs/pi05_libero_quickstart.md` | 执行顺序 |
| `docs/pi05_libero_experiment_record.md` | 实验记录模板 |
| `scripts/pi05_4090_check.ps1` | 本机环境检查 |
| `scripts/download_libero_dataset.ps1` | 下载 Hugging Face 数据 |
| `scripts/check_lerobot_dataset.py` | 数据 QC |
| `scripts/train_pi05_libero_4090.ps1` | 4090 默认训练 |
| `scripts/eval_pi05_libero_lerobot.ps1` | LeRobot 仿真评测 |
| `scripts/eval_pi05_libero_openpi.sh` | OpenPI Docker 评测参考 |
