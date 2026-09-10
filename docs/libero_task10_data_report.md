# LIBERO 单任务数据说明：put the bowl on the plate

更新时间：2026-09-05

本项目实际使用的数据位于：

```text
E:\projects\robot\data\lerobot_libero
```

本次后处理后的单任务产物位于：

```text
E:\projects\robot\artifacts\libero_task10
```

## 1. 任务

选定任务：

```text
task_index = 10
instruction = put the bowl on the plate
```

这是一个真实生活相关的桌面操作任务：机械臂需要根据语言指令观察桌面场景，移动到碗的位置，抓取碗，并放置到盘子上。它对应家庭服务机器人中很基础的“取物 + 放置 + 空间关系满足”能力。

## 2. 原始数据规模

`lerobot/libero` 原始数据集：

| 项 | 值 |
| --- | --- |
| robot_type | `panda` |
| total_episodes | 1693 |
| total_frames | 273465 |
| total_tasks | 40 |
| fps | 10 |
| parquet files | 377 |
| video files | 74 |
| camera | `observation.images.image`, `observation.images.image2` |

## 3. 后处理后的单任务数据

本次筛选结果：

| 项 | 值 |
| --- | --- |
| task_index | 10 |
| episodes | 49 |
| sampled frames for stats | 4563 |
| min episode length | 79 |
| max episode length | 126 |
| numeric NaN | 0 |
| numeric Inf | 0 |

生成文件：

| 文件 | 含义 |
| --- | --- |
| `artifacts/libero_task10/episodes.txt` | LeRobot 训练用 episode id 列表 |
| `artifacts/libero_task10/episodes.json` | JSON 格式 episode id |
| `artifacts/libero_task10/summary.json` | 后处理统计报告 |
| `artifacts/libero_task10/visual_contact_sheet.jpg` | 双相机抽帧可视化 |

## 4. Schema

逐帧数据字段：

| 字段 | 类型 / shape | 含义 |
| --- | --- | --- |
| `observation.state` | `float32[8]` | 机器人状态，包含末端位姿/夹爪等 proprioception 信息 |
| `action` | `float32[7]` | 连续动作，通常表示 6DoF 末端控制量 + gripper |
| `timestamp` | `float32[1]` | 时间戳，fps 为 10 |
| `frame_index` | `int64[1]` | episode 内帧编号 |
| `episode_index` | `int64[1]` | episode 编号 |
| `index` | `int64[1]` | 全局帧索引 |
| `task_index` | `int64[1]` | 语言任务编号 |

视频字段在 `meta/info.json` 中定义，不直接嵌入逐帧 parquet：

| 视频键 | shape | 含义 |
| --- | --- | --- |
| `observation.images.image` | `256 x 256 x 3` | 主视角 / agentview RGB 视频 |
| `observation.images.image2` | `256 x 256 x 3` | 腕部或第二视角 RGB 视频 |

## 5. 后处理内容

本次做了四类必要后处理：

1. 单任务筛选：从 40 个任务中筛出 `task_index=10` 的所有 episode。
2. 训练子集清单：生成 `episodes.txt`，训练时通过 `--dataset.episodes=[...]` 使用，不复制 2GB 原始视频。
3. 数值质检：检查 `action` 和 `observation.state` 的 NaN / Inf，并统计均值、方差、最小值、最大值。
4. 可视化抽查：从双相机视频中抽帧生成 contact sheet，用于人工确认任务画面和视频可读性。

没有重写原始 parquet/video 文件。原因是 LeRobot 原生支持 episode 过滤；保持源数据不可变更利于复现，也避免重复存储大视频。

## 6. 后处理前后对比

| 项 | 后处理前 | 后处理后 |
| --- | --- | --- |
| 任务数量 | 40 | 1 |
| episode 数 | 1693 | 49 |
| frame 数 | 273465 | 4563 sampled / 约 4563 for selected task |
| 训练输入 | 全任务混合 | 单任务 episode list |
| 数据文件 | 原始 LeRobot v3 | 原始数据 + 子集 manifest |
| QC 状态 | 全集 QC 通过 | 单任务 QC 通过 |

## 7. 单任务统计

`action` 统计：

```text
shape = [4563, 7]
mean = [0.199001, 0.014003, -0.187586, -0.007733, 0.006465, -0.008739, -0.025641]
std  = [0.465289, 0.139198, 0.54494, 0.030242, 0.058817, 0.034195, 0.999671]
min  = [-0.830357, -0.546429, -0.9375, -0.117857, -0.257143, -0.181071, -1.0]
max  = [0.9375, 0.479464, 0.9375, 0.1725, 0.204643, 0.132857, 1.0]
NaN / Inf = 0 / 0
```

`observation.state` 统计：

```text
shape = [4563, 8]
mean = [-0.051379, 0.030356, 1.01847, 3.085907, -0.105641, -0.121642, 0.02189, -0.022355]
std  = [0.079441, 0.016449, 0.085999, 0.052975, 0.153947, 0.126856, 0.017043, 0.016582]
min  = [-0.224802, -0.012051, 0.909943, 2.889414, -0.631252, -0.618051, 0.001172, -0.039907]
max  = [0.089897, 0.071659, 1.188387, 3.200747, 0.407944, 0.249242, 0.039955, -0.001799]
NaN / Inf = 0 / 0
```

## 8. 可视化

生成图：

```text
E:\projects\robot\artifacts\libero_task10\visual_contact_sheet.jpg
```

该图展示了同一单任务 episode 中不同时间点的双相机 RGB 帧，用于确认视频可读、场景确实是桌面碗盘操作，并且两路相机能正常解码。
