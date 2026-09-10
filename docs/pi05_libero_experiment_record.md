# Pi 0.5 LIBERO 实验记录

更新时间：2026-09-06

## 实验信息

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-09-05 |
| 工作区 | `E:\projects\robot` |
| 机器 | NVIDIA GeForce RTX 4090, 24GB VRAM |
| OS | Windows |
| Python / Torch | Python 3.12.13, Torch 2.11.0+cu128 |
| 框架 | LeRobot 0.6.2 / Pi 0.5 |
| 数据集 | `lerobot/libero` |
| 任务 | task 10: `put the bowl on the plate` |
| 训练方式 | Behavior Cloning, expert-only |
| 基座模型 | `E:\projects\robot\models\pi05_libero_base` |
| 最终 checkpoint | `E:\projects\robot\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model` |

## 数据质检

| 项 | 结果 |
| --- | --- |
| 数据集本地路径 | `E:\projects\robot\data\lerobot_libero` |
| 总 episodes / frames / tasks | 1693 / 273465 / 40 |
| 选中任务 episodes | 49 |
| 训练 / 测试 split | 39 / 10 |
| action / state 维度 | 7 / 8 |
| camera | `observation.images.image` + `observation.images.image2`, 256x256 RGB video |
| NaN / Inf | action=0, state=0 |
| 物理数据重写 | 未重写；通过 episode 列表过滤，避免重复视频数据 |
| QC 文件 | `artifacts/libero_qc.json`, `artifacts/libero_task10/summary.json` |
| split 文件 | `artifacts/libero_task10_split/split.json` |

## 训练配置

| 参数 | 值 |
| --- | --- |
| job_name | `pi05_libero_task10_4090_utf8` |
| output_dir | `outputs\pi05_libero_task10_4090_utf8` |
| pretrained_path | `models\pi05_libero_base` |
| batch_size | 1 |
| steps | 30000 |
| save_freq | 5000 |
| n_action_steps | 10 |
| dtype | bfloat16 |
| gradient_checkpointing | true |
| freeze_vision_encoder | true |
| train_expert_only | true |
| optimizer | AdamW, lr=2.5e-05, weight_decay=0.01, grad_clip_norm=1.0 |
| seed | 1000 |

## 训练结果

| step | loss | grad_norm | lr | mem_gb | 备注 |
| --- | --- | --- | --- | --- | --- |
| 200 | 2.144 | 8.218 | 2.5e-06 | 12.85 | early training |
| 5000 | 0.186 | 2.067 | 2.4e-05 | 12.85 | checkpoint saved |
| 10000 | 0.161 | 1.861 | 1.9e-05 | 12.85 | checkpoint saved |
| 15000 | 0.131 | 1.933 | 1.4e-05 | 12.85 | checkpoint saved |
| 20000 | 0.127 | 1.981 | 8.2e-06 | 12.85 | checkpoint saved |
| 25000 | 0.116 | 2.051 | 4.1e-06 | 12.85 | checkpoint saved |
| 30000 | 0.114 | 2.065 | 2.5e-06 | 12.85 | final checkpoint saved |

解析后的 loss 日志包含 150 个点，覆盖 200 到 30000，每 200 step 一条。loss 从 2.144 快速下降到 1k step 的 0.311，之后缓慢收敛；最后 10 个点平均 loss 为 0.1153，最后 20 个点平均 loss 为 0.1182，最低记录值为 0.108。

产物：

- `artifacts/train_pi05_task10_utf8.log`
- `artifacts/train_pi05_task10_loss.csv`
- `artifacts/train_pi05_task10_loss.png`

## 测试集可视化检查

已生成 held-out test split，测试 episodes 为：

`718, 726, 727, 749, 750, 768, 770, 801, 803, 806`

人工检查的预览：

| 文件 | 检查结果 |
| --- | --- |
| `artifacts/libero_task10_split/test_episode_718.jpg` | agent view 与 wrist view 正常，能看到碗移动到盘子附近 |
| `artifacts/libero_task10_split/test_episode_726.jpg` | 视角正常，任务过程清晰 |
| `artifacts/libero_task10_split/test_episode_727.jpg` | 视角正常，任务过程清晰 |
| `artifacts/libero_task10_split/test_episode_749.jpg` | agent view 可见完成过程；wrist view 后段遮挡更明显，但图片文件正常 |

## 评测结果

已在 Windows 环境中完成 LIBERO simulator 单任务评测。训练数据集 task 10 `put the bowl on the plate` 对应 simulator suite 为 `libero_goal`，`task_id=8`。

- 修正 `E:\projects\lerobot_experiment\envs\lerobot312\Lib\site-packages\__editable__.lerobot-0.6.2.pth`，将 LeRobot editable install 从迁移前的 `E:\Project\...` 指向当前 `E:\projects\...`。
- 安装 Windows 可运行的 LIBERO 依赖主体：`hf_libero==0.1.4`、`robosuite==1.4.0`、`bddl==1.0.1`、`mujoco==3.3.7`、`robomimic==0.2.0` 等；跳过无法在 Windows 构建的 `hf-egl-probe` / `egl_probe`。
- 下载 `lerobot/libero-assets` 到 `E:\projects\robot\data\libero_assets`，并将其 junction 到 `site-packages\libero\libero\assets`。
- 修正 robosuite Windows 运行问题：复制 `mujoco\mujoco.dll` 到 `robosuite\utils\mujoco.dll`，并将 `robosuite\macros.py` 的 `MUJOCO_GPU_RENDERING` 设为 `False`，避免 Windows 被强制切到 Linux-only 的 `egl`。
- 修正 Pi0.5 checkpoint 加载日志中的非 ASCII checkmark 输出，避免 GBK 控制台编码异常被误捕获成加载失败。
- 修正 `scripts/eval_pi05_libero_lerobot.ps1`，默认 policy 改为最终 checkpoint，默认任务改为 `libero_goal` / `task_id=[8]`，并改用 `python -m lerobot.scripts.lerobot_eval` 绕过失效的 `lerobot-eval.exe` launcher。

最终评测命令：

```powershell
.\scripts\eval_pi05_libero_lerobot.ps1 `
  -PolicyPath ".\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model" `
  -Tasks "libero_goal" `
  -TaskIds "[8]" `
  -Episodes 10 `
  -OutputDir ".\eval_logs\pi05_libero_task10_goal8_10ep"
```

评测输出确认：

- `Loaded state dict from model.safetensors`
- `All keys loaded successfully!`

| suite | task_id | task | episodes | success_rate | avg_sum_reward | eval_s |
| --- | --- | --- | --- | --- | --- | --- |
| `libero_goal` | 8 | `put the bowl on the plate` | 10 | 100.0% | 1.0 | 104.87 |

成功明细：10/10 success。

产物：

- `eval_logs/pi05_libero_task10_goal8_10ep/eval_info.json`
- `eval_logs/pi05_libero_task10_goal8_10ep/videos/libero_goal_8/eval_episode_0.mp4` 到 `eval_episode_9.mp4`
- `artifacts/eval_pi05_task10_goal8_10ep_stdout.log`
- `artifacts/eval_pi05_task10_goal8_10ep_stderr.log`

另有一次 `libero_spatial` 全 10 task、每 task 1 episode 的探路评测，但该任务组不对应本次训练单任务，且首次运行时曾因编码问题未正确加载 checkpoint；不作为本实验成功率。

如需复现实验环境，assets 下载脚本为：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
& E:\projects\lerobot_experiment\envs\lerobot312\python.exe `
  scripts\download_libero_assets.py `
  --endpoint https://hf-mirror.com `
  --output-dir data\libero_assets
```

## 结论

单卡 RTX 4090 可以完成本次 Pi 0.5 单任务 BC 微调，但需要保守训练策略：batch size 1、bf16、gradient checkpointing、冻结视觉编码器并只训练 expert 相关参数。训练 loss 已稳定收敛，数据、checkpoint、测试集可视化和 LIBERO 单任务仿真评测产物完整；当前 10 episode simulator success rate 为 100.0%。下一步可扩大到更多 seeds 或完整 `libero_goal` suite，检查这个单任务结果是否稳定。
