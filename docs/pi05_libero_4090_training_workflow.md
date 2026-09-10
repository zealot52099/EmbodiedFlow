# 基于 Pi 0.5 的单任务机器人训练流程

更新时间：2026-09-05

本文给出一套可在单卡 RTX 4090 上落地的 Pi 0.5 训练任务流程，覆盖数据选择、清洗、4090 可行性判断、训练策略、是否做 RL、无本体评测方式和执行命令。

## 1. 结论先行

推荐任务：使用 `lerobot/libero` 中的 `LIBERO-Spatial` 家居桌面操控数据，训练一个“根据语言指令完成桌面物体取放/摆放”的 Pi 0.5 策略。它不是工业臂真实采集数据，但和真实生活高度相关，覆盖“拿起物体、放到指定位置、空间关系摆放”等基础家庭服务机器人技能，并且有官方仿真评测闭环。

推荐训练路线：

1. 先做行为克隆 / 模仿学习：Pi 0.5 + LIBERO demonstrations。
2. 当前机器先不做 RL 主流程：没有真实机器人时，RL 必须依赖仿真环境或世界模型；LIBERO 可做仿真 RL，但 Pi 0.5 级别 VLA 的 RL 通常需要 8-16 张 GPU 才比较像业内可复现实验。
3. 如后续需要 RL：在 BC checkpoint 达到稳定成功率后，用 LIBERO / RLinf 做 PPO 或 GRPO 仿真微调。

4090 可行性：

| 训练方式 | 单卡 4090 是否建议 | 原因 |
| --- | --- | --- |
| Pi 0.5 全参微调 | 不建议 | OpenPI 官方给出的全参微调显存需求为 70GB+，4090 只有 24GB |
| Pi 0.5 LoRA 微调 | 可行 | OpenPI 官方给出的 LoRA 微调显存需求为 22.5GB+，4090 勉强可跑，需要 batch 降低和梯度检查点 |
| Pi 0.5 expert-only 微调 | 推荐首选 | LeRobot 文档说明冻结 VLM、只训练 action expert/projection 可显著降低显存 |
| 若 Pi 0.5 仍 OOM | 备用方案 | 改用 `pi0_fast`、SmolVLA、ACT 或 Diffusion Policy 做同一数据集基线 |

## 2. 数据集选择

主数据集：`lerobot/libero`

选择理由：

1. 官方 Pi 0.5 / LeRobot 文档直接支持。
2. 数据量约 1.9GB，单机可下载。
3. 观测键与 Pi 0.5 对齐：`observation.images.image`、`observation.images.image2`、`observation.state`、`action`。
4. 动作为 7 维连续控制：6DoF 末端位姿 delta + gripper，符合真实机械臂操作的常见接口。
5. 可用 LIBERO 仿真做无本体评测，成功率是行业常用指标。

任务边界：

默认使用 `LIBERO-Spatial`，它包含 10 个空间摆放任务，可视作同一类“桌面物体取放/摆放”任务族。若你严格只要一个自然语言指令，可以在下载后用 `scripts/check_lerobot_dataset.py --task-filter "<task text>"` 做子集质检，但不建议只用单个 50-demo 任务训练 Pi 0.5；数据会偏少，更适合 sanity check，不适合严肃微调。

## 3. 数据后处理和清洗

`lerobot/libero` 是 LeRobot 发布的处理后数据，通常不需要重新标注；仍建议执行以下 QC：

1. 检查元数据：任务列表、episode 数量、总帧数。
2. 检查关键字段是否存在：双相机、state、action。
3. 检查数值异常：NaN、Inf、全零动作比例、过短 episode。
4. 检查 normalization：Pi 0.5 默认可能使用 quantile stats，若数据缺 `q01/q99`，要么 recompute stats，要么按官方 LIBERO 配置改用 `MEAN_STD`。

本仓库已提供质检脚本：

```powershell
python .\scripts\check_lerobot_dataset.py `
  --dataset-root "$env:USERPROFILE\.cache\huggingface\lerobot\lerobot\libero" `
  --output .\artifacts\libero_qc.json
```

如果你使用 LeRobot CLI 直接从 Hugging Face 读取数据，首次训练会自动下载；也可以先用：

```powershell
hf download lerobot/libero --repo-type dataset
```

## 4. 环境准备

优先使用 WSL2 Ubuntu 22.04 或原生 Ubuntu。OpenPI 官方说明测试环境是 Ubuntu 22.04；Windows 原生 Python/JAX/CUDA 组合容易踩坑。

必须先完成：

1. 安装 NVIDIA Driver、CUDA 可用环境。
2. 安装 `uv` 或 Python 3.11 环境。
3. 登录 Hugging Face，并接受 `google/paligemma-3b-pt-224` gated tokenizer/model 许可。

```powershell
hf auth login
```

安装 LeRobot 路线：

```powershell
pip install "lerobot[pi]"
```

或安装官方 OpenPI 路线：

```bash
git clone --recurse-submodules https://github.com/Physical-Intelligence/openpi.git
cd openpi
GIT_LFS_SKIP_SMUDGE=1 uv sync
GIT_LFS_SKIP_SMUDGE=1 uv pip install -e .
```

## 5. 4090 默认训练命令

首选：LeRobot Pi 0.5 expert-only 行为克隆。它冻结 VLM，只训练 action expert 和 projection，是单 4090 更稳的选择。

```powershell
lerobot-train `
  --dataset.repo_id=lerobot/libero `
  --policy.type=pi05 `
  --policy.pretrained_path=lerobot/pi05_libero_base `
  --policy.normalization_mapping='{"ACTION": "MEAN_STD", "STATE": "MEAN_STD", "VISUAL": "IDENTITY"}' `
  --policy.n_action_steps=10 `
  --policy.empty_cameras=1 `
  --policy.freeze_vision_encoder=true `
  --policy.train_expert_only=true `
  --policy.gradient_checkpointing=true `
  --policy.dtype=bfloat16 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --output_dir=.\outputs\pi05_libero_spatial_4090 `
  --job_name=pi05_libero_spatial_4090 `
  --batch_size=8 `
  --num_workers=4 `
  --steps=30000 `
  --save_freq=5000 `
  --seed=1000
```

说明：

1. 官方 LeRobot 示例使用 batch size 64，目标是 80GB GPU；4090 建议从 4 或 8 开始。
2. 若 OOM，依次降低 `--batch_size=4`、`--num_workers=2`，保留 gradient checkpointing。
3. 若仍 OOM，不建议硬扛 Pi 0.5；切到 `pi0_fast` / SmolVLA / ACT 建 baseline。

## 6. OpenPI 官方路线

如果走 OpenPI JAX 训练，先计算归一化统计：

```bash
uv run scripts/compute_norm_stats.py --config-name pi05_libero
```

再启动 LoRA / LIBERO 微调：

```bash
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi05_libero --exp-name=pi05_libero_spatial_4090 --overwrite
```

注意：OpenPI 的 `pi05_libero` 是官方 benchmark config，默认更偏完整复现实验。4090 上需要检查该 config 是否启用 LoRA、batch 是否过大；若不是 LoRA，应复制 config 并改为 LoRA/低 batch 后再训。

## 7. 是否做 RL

业内常见流程确实是：

1. 大规模预训练。
2. 目标机器人/任务上行为克隆或 SFT。
3. 仿真或真机 rollout。
4. 用成功/失败、人工偏好、reward model 或稀疏任务成功信号做 RL / DAgger / RLAIF。
5. 再评测、回灌 hard cases。

但本项目当前没有本体，所以 RL 只能依赖：

| RL 来源 | 是否可用 | 评价 |
| --- | --- | --- |
| 真机在线 RL | 不可用 | 无本体，不能 rollout |
| 人类遥操作 DAgger | 暂不可用 | 需要机器人或遥操作采集接口 |
| LIBERO 仿真 RL | 可用但不作为默认 | 有 MuJoCo / robosuite 环境和稀疏成功 reward，但 VLA+RL 训练成本高 |
| 离线 RL | 不推荐默认 | 单一 demonstration 数据通常 reward 稀疏，容易不稳定；工程收益低于先做好 BC |

因此默认交付：BC/SFT + 仿真成功率评测。可选增强：当 BC 在 LIBERO 达到可复现成功率后，用 RLinf 的 LIBERO PPO/GRPO recipe 继续微调。

## 8. 无本体评测

主评测：LIBERO simulation success rate。

官方 OpenPI 推荐 Docker 化评测：

```bash
cd openpi
git submodule update --init --recursive
SERVER_ARGS="--env LIBERO policy:checkpoint --policy.config pi05_libero --policy.dir ./checkpoints/pi05_libero/pi05_libero_spatial_4090/30000" \
CLIENT_ARGS="--args.task-suite-name libero_spatial" \
docker compose -f examples/libero/compose.yml up --build
```

指标：

1. `success_rate`：核心指标。
2. 每个 task 的成功率：定位泛化短板。
3. rollout 视频：抽查失败模式，如 grasp miss、place drift、camera mismatch。
4. 行为克隆 loss：仅作训练健康度参考，不能替代仿真成功率。

参考目标：

1. 先跑官方 `pi05_libero` checkpoint，确认本地评测环境正常。
2. 再跑自己的 checkpoint。
3. 若 expert-only 4090 微调低于官方 full/LoRA 结果，不一定说明流程错，可能是显存约束下可训练参数更少。

## 9. 一键脚本

环境检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\pi05_4090_check.ps1
```

数据下载：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_libero_dataset.ps1
```

训练：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_4090.ps1
```

LeRobot 仿真评测：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_lerobot.ps1 `
  -PolicyPath .\outputs\pi05_libero_spatial_4090\checkpoints\last\pretrained_model `
  -Tasks libero_spatial `
  -Episodes 10
```

质检：

```powershell
python .\scripts\check_lerobot_dataset.py --help
```

实验记录模板：

```text
docs/pi05_libero_experiment_record.md
```

## 10. 参考来源

1. OpenPI 官方仓库说明：4090 支持 LoRA 微调，Pi 0.5 全参微调需要 70GB+，并提供 `pi05_libero` 训练/评测命令。https://github.com/Physical-Intelligence/openpi
2. LeRobot Pi 0.5 文档：`lerobot/libero` 数据集、Pi 0.5 输入输出键、80GB 示例训练命令、expert-only 低显存训练说明。https://huggingface.co/docs/lerobot/en/pi05
3. OpenPI LIBERO README：Docker 化评测、`libero_spatial` / `libero_10` suite 参数和官方 Pi 0.5 LIBERO 参考成功率。https://github.com/Physical-Intelligence/openpi/blob/main/examples/libero/README.md
4. LIBERO 项目页：lifelong robot learning benchmark 设定。https://libero-project.github.io/main.html
5. RLinf LIBERO 文档：LIBERO 上 VLA+PPO/GRPO 的仿真 RL 路线和资源需求。https://rlinf.readthedocs.io/en/latest/rst_source/examples/embodied/libero.html
