# Lumos FastUMI 具身数据技术调研

调研日期：2026-08-20

## 1. 一句话结论

FastUMI 是鹿明机器人对 UMI 路线的工程化升级。它用标准化手持夹爪、多模态传感器、实时位姿追踪、硬件时间同步和机器人本体解耦，把人类真实操作快速转化为可训练的机器人操作数据。其核心价值是降低具身数据采集成本，提高采集效率，并缓解不同机器人本体之间的数据孤岛问题。

## 2. FastUMI 解决的问题

传统机器人数据采集主要依赖真机遥操作，但存在三个瓶颈：

- 成本高：需要占用真实机器人、工程师和安全场地。
- 效率低：真机动作慢，调试和复位耗时。
- 数据孤岛：不同机器人本体的关节、夹爪、控制接口不同，数据难复用。

FastUMI 的思路是把“数据采集”和“机器人本体”解耦：

```text
人手持 FastUMI 设备完成任务
    ↓
记录第一视角视觉、深度/点云、IMU、夹爪状态、末端轨迹
    ↓
生成标准化 demonstration trajectory
    ↓
后续再适配到不同机器人训练和执行
```

## 3. 与原始 UMI 的关系

UMI 即 Universal Manipulation Interface，核心思想是用一个类似机器人夹爪的手持采集设备，让人类在真实环境中演示操作，再将演示轨迹转化为机器人可学习的数据。

FastUMI 延续了 UMI 的基本路线，但更强调工程化、规模化和实时化：

- 采集设备模块化。
- 硬件与机器人本体解耦。
- 集成轻量实时 tracking system。
- 多模态数据同步。
- 标准化数据格式。
- 更适合大规模数据生产。

FastUMI-100K 论文称，FastUMI 通过模块化、硬件解耦的机械设计和集成轻量追踪系统，提升了数据采集的可扩展性、灵活性和跨本体适配性。

## 4. 典型采集流程

FastUMI 的采集流程可以概括为：

```text
1. 任务定义
   定义任务，例如“把杯子放进抽屉”“打开柜门”“整理桌面”。

2. 人手持 FastUMI 设备
   采集者像使用一个机器人夹爪一样完成任务。

3. 多模态同步采集
   记录 RGB、ToF 点云/深度、IMU、夹爪宽度、末端位姿轨迹、时间戳。

4. 实时位姿追踪
   采集过程中计算手持夹爪在空间中的轨迹。

5. 轨迹与视觉对齐
   将图像帧、点云、IMU、夹爪状态、轨迹对齐到同一时间轴。

6. 质量检查
   检查轨迹是否平滑、是否丢帧、是否同步、任务是否完成。

7. 数据标准化
   输出为可训练格式，例如 LeRobot 格式或自定义 episode schema。

8. 模型训练
   用于 BC、Diffusion Policy、ACT、VLA fine-tuning、skill learning 等。
```

## 5. 采集数据内容

公开资料和 FastUMI-100K 论文提到的数据模态包括：

- end-effector states
- single-arm trajectories
- dual-arm trajectories
- multi-view wrist-mounted fisheye images
- textual annotations
- gripper width sequence
- RGB video
- ToF point cloud / depth
- fused pose trajectory

一个 episode 可以抽象为：

```text
{
  task_instruction,
  timestamps,
  wrist_images,
  depth_or_point_cloud,
  end_effector_pose,
  gripper_width,
  action_sequence,
  textual_annotations,
  success_or_failure,
  metadata
}
```

## 6. 关键技术 1：无本体采集

传统遥操作数据采集强依赖目标机器人：

```text
机器人 A 的数据只能直接训练机器人 A
机器人 B 需要重新采集或大量适配
```

FastUMI 的设计目标是：

```text
采集端不绑定具体机器人
数据以更通用的末端轨迹、视觉、夹爪状态形式保存
部署时再映射到目标机器人
```

这可以降低采集成本，也可以提高数据复用性。

## 7. 关键技术 2：手持夹爪与统一末端接口

FastUMI 使用类似机器人末端执行器的手持设备，而不是直接用裸手视频。

这样做的好处：

- 视觉视角更接近机器人 wrist camera。
- 夹爪开合可以直接记录。
- 末端轨迹更接近机器人 action。
- 比纯 egocentric video 更容易迁移到 robot policy。

但这并不能完全消除 embodiment gap，因为人手持设备仍然比机器人灵活，人的移动、避障、速度和接触控制都和机器人不同。

## 8. 关键技术 3：相对轨迹动作表示

UMI 系列方案常使用 relative trajectory action representation。

含义是：模型不直接学习绝对世界坐标，也不只学习单步 delta，而是学习相对于当前末端坐标系的一段未来轨迹。

形式上可以理解为：

```text
当前末端位姿：T0
未来位姿：T1, T2, T3 ...
相对轨迹：T0^-1*T1, T0^-1*T2, T0^-1*T3 ...
```

优点：

- 减少对全局坐标、相机外参、桌面位置的依赖。
- 比绝对轨迹更容易跨场景。
- 比单步 delta 更能表达未来动作形状。
- 对延迟和局部误差更鲁棒。

局限：

- 仍然需要目标机器人能通过 IK 或控制器执行这些末端轨迹。
- 对复杂接触、力控、灵巧手动作仍然不充分。

## 9. 关键技术 4：延迟匹配

训练时，采集数据中的图像、位姿和动作往往可以严格对齐；部署时，机器人系统会有相机延迟、模型推理延迟、控制器延迟和执行延迟。

如果不处理延迟，就会出现：

```text
模型看到的是 100ms 前的画面
输出动作 150ms 后才真正执行
快速操作任务中动作和观测错位
```

UMI 论文提出 inference-time latency matching。核心思路是：

- 估计部署时的观测延迟、推理延迟和执行延迟。
- 模型输出一段未来动作序列。
- 已经过期的动作丢弃。
- 只执行在真实时间轴上仍然有效的未来动作。

这对 toss、快速移动、动态接触类任务尤其重要。

## 10. 关键技术 5：多模态硬件同步

具身数据对时间同步非常敏感。FastUMI Pro 官网强调硬件级时间戳同步，目标是让 RGB、ToF、IMU、夹爪宽度和位姿轨迹对齐。

同步错误会造成严重训练噪声：

```text
图像显示还没接触杯子
轨迹显示已经夹住并抬起
```

高质量同步是 FastUMI 从研究原型走向数据生产系统的关键。

## 11. 关键技术 6：实时追踪与采完即用

原始 UMI 或传统视频采集通常需要大量离线后处理：

```text
采集视频
    ↓
离线 SLAM / VIO
    ↓
轨迹重建
    ↓
多模态对齐
    ↓
质量检查
```

FastUMI-100K 论文和公开报道都强调 FastUMI 采用集成轻量 tracking system，把一部分轨迹计算前置到采集阶段，使数据更接近“采完即可用”。

这样可以提升规模化生产效率。

## 12. FastUMI Pro、FastUMI Go、FastUMI Ego

公开报道中，鹿明将 FastUMI 做成了系列化设备。

### 12.1 FastUMI Pro

定位：无本体、多模态、高质量 manipulation data collection。

适合：

- 桌面操作。
- 单臂/双臂 manipulation。
- 真实物体操作数据。
- 机器人策略训练数据生产。

### 12.2 FastUMI Go

定位：背包式、可移动、开放环境采集。

它解决的是 UMI 设备走出实验室的问题，使采集人员可以进入工厂、家庭、酒店、餐馆、商场、办公等真实场景。

适合：

- 大规模真实场景数据采集。
- 移动采集。
- 非固定工位任务。

注意：Go 可以支持人在环境中移动采集，但它不等于完整采集人形机器人的全身控制数据。移动底盘、腿部运动、全身动力学仍需要额外数据模态或单独策略。

### 12.3 FastUMI Ego

定位：第一视角空间数据采集。

它更偏环境、空间、上下文信息采集。

与 UMI 的互补关系：

```text
UMI：记录精细操作、手部轨迹、夹爪状态、操作动作
Ego：记录环境、空间关系、任务上下文、第一视角理解
```

## 13. FastUMI-100K 数据集

FastUMI-100K 是理解 FastUMI 技术路线的重要资料。

公开论文信息：

- 超过 100K 条 demonstration trajectories。
- 覆盖 54 个任务。
- 覆盖数百种真实场景物体。
- 包括单臂和双臂轨迹。
- 包括多视角腕部鱼眼图像。
- 包括 end-effector states。
- 包括文本标注。
- 每条轨迹长度约 120 到 500 帧。
- 数据标准化到 LeRobot v2.1 格式。

这说明 FastUMI 的目标不是采少量实验室演示，而是构建可以支撑数据驱动机器人操作学习的大规模数据集。

## 14. 效率和成本

多篇公开报道提到，FastUMI Pro 相比传统遥操作采集：

- 单条数据采集时间从约 50 秒缩短到约 10 秒。
- 效率提升约 5 倍。
- 综合成本降至传统方案的五分之一。
- 可快速适配数十种机械臂和夹爪。

效率提升主要来自：

- 人手持设备操作更快。
- 不占用真实机器人本体。
- 不需要频繁调试机器人。
- 数据采集和轨迹计算更实时。
- 多模态同步减少后处理。
- 标准化输出降低数据工程成本。

## 15. 优势

- 成本低于真机遥操作。
- 采集效率高。
- 真实场景覆盖能力强。
- 数据与机器人本体解耦。
- 比纯 egocentric video 更接近机器人动作数据。
- 可用于单臂、双臂、长时序 manipulation。
- 适合作为 VLA / policy learning 的大规模 demonstration 数据来源。

## 16. 局限

- 人手持设备和真实机器人仍有 embodiment gap。
- 人可以自然移动、避障和调整姿态，机器人未必能做到。
- 接触力、摩擦、动力学信息不完整。
- 对灵巧手、全身人形机器人、腿足移动控制覆盖有限。
- 轨迹 retargeting 到不同机器人仍需要 IK、控制器和可达性检查。
- 对复杂力控任务，单靠视觉和末端轨迹可能不够。

## 17. 与传统方案对比

| 方案 | 优点 | 缺点 | 适合阶段 |
|---|---|---|---|
| 真机遥操作 | action 最真实，直接训练目标机器人 | 成本高，慢，跨本体差 | 高质量模仿学习、目标机器人微调 |
| 原始 UMI | 低成本，真实环境，动作可映射 | 后处理较重，工程化不足 | 研究验证、操作数据采集 |
| FastUMI | 更工程化、实时化、规模化，本体解耦 | 仍有 embodiment gap | 大规模 manipulation 数据生产 |
| Egocentric video | 规模最大，场景丰富 | 无真实 robot action | 预训练、任务理解 |
| 仿真数据 | 便宜、标签准确、可控 | sim-to-real gap | RL、评测、失败恢复 |

## 18. 与 NexCore 的关系

FastUMI 是数据入口，NexCore 是数据到技能的闭环平台。

```text
FastUMI / Ego / 遥操作 / 真机日志
        ↓
数据资产平台
        ↓
模型训练
        ↓
仿真和真机评测
        ↓
技能封装
        ↓
机器人部署
        ↓
任务日志和失败样本回流
```

也就是说：

- FastUMI 解决“高质量数据怎么低成本来”。
- NexCore 解决“数据怎么变成技能并持续进化”。

## 19. 对外表达建议

如果需要对 FastUMI 做技术表达，可以这样概括：

> FastUMI 的本质是把机器人操作数据采集从真机遥操作中解耦出来。它通过手持夹爪、多模态传感器、实时位姿追踪和硬件时间同步，把人类真实操作转换成包含视觉、点云、末端轨迹、夹爪状态和文本标注的 demonstration episode。相比纯 egocentric video，它更接近机器人可执行 action；相比真机遥操作，它成本更低、效率更高、场景覆盖更广。它最大的价值在于成为 VLA 和机器人 policy 训练的大规模真实操作数据来源。

## 20. 参考资料

- Lumos FastUMI Pro 产品页：https://www.lumosbot.tech/products/fastumi-pro/
- FastUMI-100K 论文：https://arxiv.org/abs/2510.08022
- FastUMI-100K HTML：https://arxiv.org/html/2510.08022v1
- FastUMI-100K GitHub：https://github.com/MrKeee/FastUMI-100K
- 科创板日报采访：https://www.cls.cn/detail/2255912
- 新华社 FastUMI 无本体数采报道：https://www.news.cn/tech/20260314/e81f7585b7c94e1281f94cd4eb59202e/c.html
- Lumos 官方网站：https://www.lumosbot.tech/

