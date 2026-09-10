# π 系列 VLA 模型完整梳理：π0 / π0.5 / π0.6 / π*0.6 / π0.7

适用目标：具身智能 / VLA / Robot Foundation Model / 机器人交互大脑面试准备  
核心问题：π0 是什么，π0.5、π0.6、π*0.6、π0.7 分别改了什么，π0-FAST / OpenPI / Hi Robot 等相关变种分别解决什么问题。

---

## 1. 一句话总览

π0 是 Physical Intelligence 提出的通用机器人 VLA/robot foundation model，核心是用预训练 VLM 理解图像和语言，再用 flow matching action decoder 生成连续机器人动作。π0.5 在 π0 基础上进一步面向开放世界泛化，通过异构数据 co-training，把机器人低层动作、移动操作、高层语义子任务、物体检测、网页/视觉语言数据等混合起来，使模型能在未见过的新家庭环境中执行长链路任务。π0.6 是基于 π0.5 的更强 base model，保留高层子任务预测 + 低层动作生成的层级设计，同时升级 VLM backbone、prompt/metadata 设计和训练数据，使 out-of-the-box 表现更强。π*0.6 则是在 π0.6 基础上用 RECAP 从真实机器人经验、人工纠正和 reward 中继续学习。π0.7 进一步强调 steerable generalist，通过更丰富的 prompt context、metadata、subgoal images 和多源数据，让同一个通用模型更可控地组合技能、跨任务和跨 embodiment 泛化。π0-FAST 是另一条动作建模变体：不用 flow matching 直接生成连续动作，而是用 FAST action tokenizer 把动作序列压缩成离散 token，再用自回归 VLA 预测。

---

## 2. 时间线与版本关系

| 时间 | 名称 | 关键词 | 主要意义 |
| --- | --- | --- | --- |
| 2024-10 | π0 | VLM backbone + flow matching action decoder | 第一个公开展示的通用机器人 policy 原型，强调多机器人、多任务、灵巧操作 |
| 2025-01 | FAST | Efficient action tokenization | 用 DCT 等时间序列压缩思路把连续 action chunk 变成紧凑离散 token |
| 2025-02 | OpenPI / π0-FAST | 开源 π0、π0-FAST | 提供可复现、可微调、可部署的开源 VLA 基线 |
| 2025-02 | Hi Robot | System 2 VLM + π0 System 1 | 把 π0 作为反应式低层 policy，上层 VLM 负责复杂任务分解和交互 |
| 2025-04 | π0.5 | Open-world generalization | 在 π0 基础上通过异构数据 co-training 提升新环境长链路泛化 |
| 2025-06 | Real-Time Action Chunking | 大模型高延迟下的实时执行 | 用 chunk selection/执行调度缓解大 VLA 推理慢和控制频率高之间的矛盾 |
| 2025-09 以后 | OpenPI pi05 / PyTorch / LeRobot | 工程生态 | π0.5、π0-FAST 等进入更方便的开源训练和微调生态 |
| 2025-11 | π0.6 | Stronger base VLA | 基于 π0.5，升级 VLM backbone、prompt/metadata、训练数据，out-of-the-box 更强 |
| 2025-11 | π*0.6 | RECAP / learning from experience | 在 π0.6 基础上用真实部署数据、人工纠正和 reward 做经验学习，提升成功率和吞吐 |
| 2026-04 | π0.7 | Steerable generalist model | 用 richer context conditioning、subgoal images、metadata 和多源数据，让通用模型更可控、更可组合 |

版本关系可以这样记：

```text
π0
  基础 VLA：VLM 表征 + flow matching 连续动作生成

π0-FAST
  π0 的自回归动作 token 变体：FAST tokenizer + next-token prediction

π0.5
  π0 的开放世界泛化升级版：异构数据 co-training + 高层语义任务迁移

π0.6
  π0.5 的更强 base model：更强 VLM backbone + prompt/metadata + 更丰富训练数据

π*0.6
  π0.6 的经验学习版本：RECAP + 真实 rollout + 人工纠正 + reward/advantage conditioning

π0.7
  更可控的通用模型：steerable prompting + subgoal images + metadata + 多源数据组合

Hi Robot
  系统架构变体：上层 VLM 做 System 2，π0 做 System 1

OpenPI / LeRobot
  开源实现和工程生态：用于复现、微调、部署 π0 / π0-FAST / π0.5
```

---

## 3. π0：第一代通用机器人 VLA

### 3.1 它想解决什么问题

传统机器人 policy 往往针对单一机器人、单一任务、单一环境训练，泛化弱；而通用大模型虽然懂语言和视觉，却不能直接控制机器人。π0 试图把二者结合：让机器人 policy 像大语言模型一样从大规模、多任务、多机器人数据里学习，同时继承预训练 VLM 的语义理解能力。

它主要解决四个问题：

1. **多任务泛化**：不是每个任务都训练一个单独 policy。
2. **多机器人数据利用**：把不同 robot embodiment 的数据放到一个通用模型里。
3. **语言指令跟随**：用户用自然语言描述任务，模型能结合视觉状态行动。
4. **连续灵巧动作**：不是只输出离散 skill，而是生成可执行的连续动作片段。

### 3.2 基本架构

π0 的核心结构可以理解为：

```text
输入：
  图像 / 多视角图像
  语言指令
  机器人 proprioception
  历史上下文

        |
        v

预训练 VLM backbone：
  负责视觉-语言语义表征
  继承互联网规模视觉语言知识

        |
        v

Flow Matching Action Decoder：
  从噪声逐步生成连续 action chunk
  输出未来一段时间的机器人动作

        |
        v

机器人执行：
  关节/末端/夹爪等控制信号
```

### 3.3 为什么用 flow matching

机器人动作是连续、时序相关、多峰分布的。比如“拿起杯子”可能有多个可行抓取姿态，动作也要平滑。直接把动作离散成 token 虽然方便复用 LLM 训练范式，但可能带来精度损失、动作抖动和较高 token 长度。Flow matching 的思路是学习一个从噪声到动作轨迹的连续变换，适合生成短时 action chunk。

可以把它类比为：

```text
VLM 负责“知道要做什么”
Flow action decoder 负责“生成一段怎么做的连续轨迹”
```

### 3.4 π0 的贡献

- 把预训练 VLM 与连续机器人动作生成结合起来。
- 强调大规模多任务、多机器人数据对通用 policy 的价值。
- 展示了洗衣、折叠、整理等更灵巧、更长链路的真实机器人任务。
- 让 VLA 从“动作 token”路线扩展到“VLM + continuous action decoder”路线。

### 3.5 π0 的不足

- 对训练数据规模、数据质量、动作对齐要求很高。
- 泛化主要仍集中在训练分布附近，对完全新环境和长链路家庭任务仍有限。
- 模型本身不是完整机器人系统，仍需要硬件控制、安全约束、失败恢复和任务管理。
- 训练与部署成本高，普通团队很难从零复现同等规模。

---

## 4. π0-FAST：动作 token 化变体

### 4.1 它想解决什么问题

π0 用 flow matching 生成连续动作，而 π0-FAST 走另一条路线：把连续动作序列压缩成离散 token，让 VLA 可以像语言模型一样做自回归 next-token prediction。它解决的是“如何把高频连续机器人动作更高效地 token 化”的问题。

### 4.2 FAST 是什么

FAST 是 Efficient Robot Action Tokenization。它使用时间序列压缩思路，例如离散余弦变换 DCT，把一段连续动作轨迹压缩成更短、更密集的离散 action tokens。

粗略链路是：

```text
连续动作序列：
  a1, a2, a3, ... aT

        |
        v

FAST tokenizer：
  时间序列压缩
  离散化
  得到 compressed action tokens

        |
        v

自回归 VLA：
  image + language + proprioception -> action tokens

        |
        v

FAST detokenizer：
  action tokens -> 连续动作序列
```

### 4.3 π0-FAST 与 π0 的区别

| 对比项 | π0 | π0-FAST |
| --- | --- | --- |
| 动作建模 | Flow matching 连续动作生成 | FAST tokenization + 自回归 token 预测 |
| 训练范式 | 更像 diffusion/flow policy | 更像 LLM/VLM next-token prediction |
| 优点 | 连续动作自然、平滑，适合低层控制 | 语言跟随和 token 范式更统一，便于接入自回归 VLA |
| 不足 | 训练和推理实现复杂 | 推理成本可能更高，动作质量依赖 tokenizer |
| 适合 | 灵巧操作、连续控制、action chunk | 想统一文本和动作 token 的 VLA 实验 |

OpenPI 官方说明中，π0-FAST base 使用 FAST tokenizer 进行自回归离散化，语言跟随可能更好，但推理成本更高，官方经验约为 π0 的 4-5 倍。因此它更像研究和工程上的替代路线，而不是简单的 π0 升级版。

### 4.4 FAST / FAST+ 的价值

FAST 的核心价值是把“机器人动作 token 化”从朴素离散化变成更高效的时间序列压缩。后续 FAST+ 进一步尝试做更通用的 action tokenizer，目标是能适配更大规模真实机器人动作数据。

面试中可以这样讲：π0-FAST 说明 VLA 有两条主流动作建模路线，一条是 flow/diffusion 连续生成，一条是 action tokenizer + autoregressive prediction。前者更像机器人 policy，后者更像把动作纳入大语言模型范式。

---

## 5. π0.5：面向开放世界泛化的升级版

### 5.1 它为什么出现

π0 和许多早期 VLA 模型在接近训练环境的任务上表现不错，但真实家庭、办公室、仓库环境更复杂：物体位置、光照、家具布局、用户指令、可操作对象都可能从未见过。π0.5 试图解决这个问题：让 VLA 不只在训练分布内做动作模仿，而是在全新环境中完成长链路、有语义目标的任务。

π0.5 论文标题中的关键词是 **open-world generalization**。

### 5.2 π0.5 的核心改进

π0.5 的关键不是只换一个更大的模型，而是改变训练数据和任务混合方式。它使用 co-training，把多种数据源和任务形式混合到一个模型里：

| 数据 / 任务类型 | 作用 |
| --- | --- |
| 机器人低层 demonstration | 学习真实动作控制 |
| 多机器人/多 embodiment 数据 | 提升跨硬件和跨任务迁移 |
| 移动操作数据 | 支持不只桌面机械臂，而是移动机器人清理房间 |
| 高层语义子任务预测 | 学会把长任务拆成中间步骤 |
| 物体检测 / grounding 数据 | 提升开放词表物体识别和定位 |
| 视觉语言 / web 数据 | 注入更广泛的语义常识 |
| 混合多模态样本 | 把图像、语言、对象、子任务、低层动作统一训练 |

### 5.3 基本链路

```text
用户指令：
  Clean the kitchen / tidy the bedroom

        |
        v

多模态输入：
  当前图像
  移动机器人状态
  语言指令
  历史动作
  可能的对象检测 / 子任务上下文

        |
        v

π0.5：
  VLM 语义理解
  高层子任务预测
  低层动作生成
  异构知识迁移

        |
        v

输出：
  移动、抓取、放置、整理等连续动作

        |
        v

执行与反馈：
  在未见过的新厨房/卧室中完成 10-15 分钟长链路任务
```

### 5.4 π0.5 相比 π0 改了什么

| 对比项 | π0 | π0.5 |
| --- | --- | --- |
| 目标 | 通用机器人 policy 原型 | 开放世界泛化和长链路真实任务 |
| 任务 | 多任务、灵巧操作 | 新家庭环境中的清理、整理等长任务 |
| 数据 | 大规模机器人 demonstration 为主 | 机器人数据 + 高层子任务 + 检测 + web/视觉语言数据 |
| 能力 | 语言条件下的连续动作控制 | 新环境、新物体、长链路、多阶段任务泛化 |
| 关键方法 | VLM backbone + flow matching action decoder | 在 π0 基础上做异构任务 co-training |

### 5.5 π0.5 的贡献

- 把 VLA 从“训练环境附近泛化”推进到“未见过真实环境中的长链路操作”。
- 证明高层语义任务、web 视觉语言知识、物体检测和低层动作数据可以互相迁移。
- 说明机器人 foundation model 不能只堆 teleoperation 数据，还需要语义、对象和任务层监督。
- 为“VLM 负责 embodied reasoning，VLA 负责 action”的融合路线提供了强证据。

### 5.6 π0.5 的不足

- 开放世界泛化仍不是无限泛化，本质上依赖数据覆盖和任务相似性。
- 长链路任务中仍可能发生错误累积，需要外部 memory、planner、safety shield 和 failure recovery。
- 对机器人平台、传感器、动作空间的适配成本高。
- 论文和开源版本能学习很多思路，但真实工业级数据规模和训练细节并不完全透明。
- 对小数据微调未必一定优于 π0，社区 issue 中也有人反馈某些单臂小任务上 π0.5 不一定更好，这说明“更通用”不等于“所有窄域任务都更强”。

---

## 6. π0.6：更强的 base VLA

### 6.1 它为什么出现

π0.5 的重点是 open-world generalization，也就是让模型能在未见过的新环境中做长链路任务。但从模型卡和公开说明看，π0.6 更像是把 π0.5 的方向做成更强的通用 base model：它不是只为了某一个新任务，而是希望作为后续微调、经验学习、部署和下游研究的更强底座。

可以把 π0.6 理解为：

```text
π0.5：
  证明异构 co-training 可以提升开放世界泛化

π0.6：
  把这个路线做得更强、更工程化、更适合作为 base model
```

### 6.2 π0.6 的模型输入与输出

π0.6 仍然是 VLA 模型，输入不是单纯图像和语言，而是更丰富的上下文：

| 输入类型 | 作用 |
| --- | --- |
| 多视角图像 / 当前视觉观测 | 感知环境、物体、空间关系 |
| 自然语言指令 | 表达用户目标或当前子任务 |
| 机器人状态 | 例如关节、末端、夹爪、底盘等 proprioception |
| prompt / metadata | 指定 embodiment、任务类型、控制模式、数据域等 |
| 可选子目标或任务上下文 | 帮助模型知道当前处在长任务的哪个阶段 |

输出通常是未来一段时间的连续动作，即 action chunk，而不是一句自然语言。动作可以对应末端位姿、关节、夹爪、底盘等，具体取决于 robot embodiment 和训练数据格式。

### 6.3 π0.6 相比 π0.5 的主要变化

公开资料没有把所有训练细节完全展开，但可以从模型卡和 OpenPI 生态总结出几个方向：

| 变化方向 | π0.5 | π0.6 |
| --- | --- | --- |
| 目标 | 开放世界泛化验证 | 更强、更通用的 base VLA |
| Backbone | 继承 π0/π0.5 的 VLM + action decoder 思路 | 使用更强 VLM backbone 和更完善的上下文接口 |
| Prompt/metadata | 已开始引入任务和数据混合信息 | 更强调通过 prompt/metadata 区分 embodiment、任务、控制模式 |
| 数据 | 异构 co-training | 更大、更杂、更工程化的数据混合 |
| 用途 | 论文证明 open-world task | 作为 OpenPI 生态里的强 base model 和下游起点 |

### 6.4 π0.6 解决了什么问题

π0.6 主要解决的是“如何让一个 VLA base model 更稳定地作为通用底座使用”。π0.5 证明了方向，但如果要让社区或团队拿来微调、部署、继续强化，就需要一个更强的基础模型：更好的视觉语言理解、更稳的动作生成、更好的 prompt conditioning、更好的 embodiment 区分能力。

面试中可以这样讲：

> π0.6 可以看作 π0.5 之后更工程化的 base VLA。它沿用 VLM backbone + action decoder 的路线，但更重视 prompt、metadata 和多源数据混合，使模型不仅在论文任务上表现好，也更适合作为下游机器人微调和真实部署的基础模型。

### 6.5 π0.6 的不足

- 仍然依赖大量高质量机器人数据，尤其是多 embodiment 数据的统一和对齐。
- prompt/metadata 能提升可控性，但也增加了数据 schema 和部署接口复杂度。
- out-of-the-box 能力变强，不代表新机器人上可以零样本可靠部署。
- 在安全关键任务中仍需要外部 safety shield、运动规划、碰撞检测和异常恢复。

---

## 7. π*0.6：从真实经验中继续学习

### 7.1 π*0.6 和 π0.6 是什么关系

π*0.6 不是一个完全从零设计的新架构，而是在 π0.6 基础上进一步通过真实机器人经验改进的版本。名字里的星号可以理解为“经过经验学习强化后的 π0.6”。

关系可以这样写：

```text
π0.6
  更强 base VLA

        |
        v

RECAP / real-world experience learning
  真实 rollout
  人工纠正
  reward / advantage conditioning
  成功失败数据回流

        |
        v

π*0.6
  更适合真实长时间执行和持续改进的 VLA
```

### 7.2 RECAP 想解决什么问题

VLA 只靠离线 demonstration 有一个根本问题：训练数据里未必覆盖模型自己会犯的错误。真实部署时，模型会进入训练数据没有覆盖的状态，例如抓歪了、物体被推走了、机械臂姿态尴尬、用户临时改变目标。这就是 imitation learning 里的 distribution shift。

RECAP 的思路是让机器人从自己的真实执行经验中学习：

1. 让 π0.6 在真实环境中执行任务。
2. 收集成功、失败、卡住、低效的 rollout。
3. 人类可以接管、纠正或给出偏好/reward。
4. 把这些经验重新组织成训练数据。
5. 用 reward、advantage 或修正轨迹继续训练 policy。

这和 GUI-Agent 的数据闭环非常像：不是只训练成功轨迹，而是把失败页面、无效操作、重规划轨迹也纳入后训练。

### 7.3 π*0.6 的基本链路

```text
Base model：
  π0.6

        |
        v

真实任务执行：
  robot rollout
  成功/失败/中断/人工接管

        |
        v

经验整理：
  失败归因
  人工 correction
  reward / preference
  advantage label

        |
        v

继续训练：
  imitation + reward-conditioned learning
  或类似离线 RL / policy improvement 的流程

        |
        v

π*0.6：
  更高成功率
  更好恢复能力
  更适合真实部署
```

### 7.4 它解决了什么问题

π*0.6 重点解决 VLA 的“离线数据和真实执行之间的落差”。纯离线 VLA 可以学会很多技能，但真实机器人场景里最贵的是失败恢复、长时间稳定性和边界状态处理。π*0.6 通过真实经验闭环，把部署中遇到的失败样本反哺模型，让模型不只是模仿专家，还能从自己的错误中改进。

### 7.5 它的不足

- 真实机器人 rollout 成本高，采集速度慢，还涉及硬件磨损和安全风险。
- 人工纠正和 reward 标注成本高，质量不稳定会影响训练。
- 从真实经验学习容易过拟合某个环境或某台机器人，需要谨慎做数据混合。
- 如果没有安全兜底，在线收集失败经验本身就可能危险。

---

## 8. π0.7：更可控的 steerable generalist

### 8.1 π0.7 的定位

π0.7 可以看作 π 系列从“更强 base model”进一步走向“更可控通用机器人模型”的版本。通用机器人模型光会很多技能还不够，实际部署还需要被明确引导：用哪个机器人、在哪个场景、按哪个风格、执行哪个子目标、遵守哪些约束。π0.7 的关键词可以理解为 steerability，也就是可控泛化。

### 8.2 为什么需要 steerability

通用 VLA 面临一个问题：同一句指令可能有很多合理执行方式。例如“整理桌子”可能是把杯子放左边、把书叠起来、把垃圾丢掉，也可能只是清出一块空地。机器人如果只靠一句自然语言，很容易做出用户没预期的动作。

因此 π0.7 这类方向会更强调 richer conditioning：

| 条件信息 | 作用 |
| --- | --- |
| 详细 prompt | 明确任务目标、约束和风格 |
| metadata | 指定机器人类型、任务域、数据来源、控制接口 |
| subgoal images | 用目标图像告诉模型“最终应该长什么样” |
| 历史上下文 | 告诉模型前面做过什么，避免重复或漂移 |
| 多源数据 | 让模型同时学习低层动作、高层任务和视觉语义 |

### 8.3 π0.7 的基本思想

```text
不是只输入：
  当前图像 + "clean the table"

而是输入：
  当前图像
  语言目标
  机器人类型和动作接口
  任务 metadata
  子目标图像 / 期望状态
  历史执行上下文

        |
        v

π0.7：
  根据 richer context 选择合适技能组合
  生成连续 action chunk
  更可控地执行通用任务
```

### 8.4 π0.7 和 π0.6 的区别

| 对比项 | π0.6 | π0.7 |
| --- | --- | --- |
| 核心定位 | 更强 base VLA | 更可控的 generalist VLA |
| 重点 | base capability、数据混合、prompt/metadata | steerability、subgoal conditioning、技能组合 |
| 解决问题 | 提高 out-of-the-box 和下游适配能力 | 让通用能力更听指挥、更可组合 |
| 面向场景 | 作为强底座微调/部署 | 多任务、多机器人、多约束下的可控泛化 |

### 8.5 π0.7 的不足

- richer context 让模型更可控，也让 prompt/schema 设计更复杂。
- subgoal image 或 metadata 的质量会直接影响动作结果。
- 通用能力和窄域最优性能之间仍有取舍。
- 在长链路任务中，仍需要外部 planner、memory、world model 或执行反馈来避免逻辑漂移。

---

## 9. π 系列的核心技术线索

π 系列可以用四条主线串起来，而不是只记版本号。

### 9.1 主线一：从动作 token 到连续动作生成

RT-2 代表的是 action token 路线，π0 代表的是 VLM + flow action decoder 路线。π0-FAST 又回到 token 路线，但使用更高效的 FAST tokenizer 压缩动作。这里的核心问题是：机器人动作到底应该像语言 token 一样生成，还是像连续轨迹一样生成。

```text
Action token：
  统一 LLM 训练范式
  方便自回归建模
  但连续精度和动作长度有挑战

Flow / diffusion action：
  更自然表达连续动作
  更适合平滑轨迹和多峰动作
  但训练/推理工程更复杂
```

### 9.2 主线二：从单纯 demonstration 到异构 co-training

π0 主要强调大规模机器人 demonstration。π0.5 开始明确把高层子任务、检测、视觉语言数据和机器人数据混合。π0.6/π0.7 继续沿着这条路线走，用 prompt、metadata、subgoal 等方式把异构数据组织进同一个模型。

这背后的判断是：机器人要做开放世界任务，不能只靠“人遥操作机器人”的轨迹。它还需要物体识别、空间语言、任务阶段、常识、目标状态等监督。

### 9.3 主线三：从 base model 到 deployment learning

π0/π0.5/π0.6 更像 base model 或 foundation policy。π*0.6 强调从真实部署经验中继续学习。这个方向对产品很重要，因为真实机器人最难的不是 demo 成功一次，而是连续运行、失败恢复和处理边界状态。

### 9.4 主线四：从通用能力到可控泛化

π0.7 的 steerability 说明一个趋势：通用模型会很多技能还不够，必须让用户、上层 planner 或系统约束能够控制它怎么做。未来 VLA 很可能不是只接一句自然语言，而是接收语言、目标图、机器人 metadata、任务约束、历史执行状态和安全规则。

---

## 10. 版本总表

| 版本 | 本质 | 动作建模 | 主要解决问题 | 主要不足 |
| --- | --- | --- | --- | --- |
| π0 | 第一代 generalist VLA | Flow matching action decoder | 把 VLM 语义和连续机器人动作结合 | 泛化和真实部署仍有限 |
| π0-FAST | 动作 token 化变体 | FAST tokenizer + autoregressive prediction | 高效 action tokenization，统一 LLM 训练范式 | 推理成本高，动作质量依赖 tokenizer |
| π0.5 | 开放世界泛化升级 | 继承 π0 路线 + 异构 co-training | 新环境、长链路、语义任务泛化 | 仍依赖数据覆盖，长任务需外部闭环 |
| π0.6 | 更强 base VLA | VLM + action decoder | 更强 out-of-the-box 和下游适配基础 | 新机器人仍需微调和安全兜底 |
| π*0.6 | 经验学习增强版 | π0.6 + RECAP | 从真实 rollout、纠正和 reward 中提升 | 数据采集和安全成本高 |
| π0.7 | 可控通用模型 | richer conditioning + action generation | steerability、技能组合、跨任务泛化 | prompt/schema 复杂，仍需 planner/memory |
| Hi Robot | 系统架构变体 | System 2 VLM + π0 System 1 | 高层推理与低层执行分工 | 系统复杂度高 |

---

## 11. Hi Robot：π0 作为 System 1 的层级变体

Hi Robot 不是 π0 的模型版本升级，而是一个系统架构变体。它把 π0 当作低层、反应式、擅长熟练动作的 System 1；再用一个高层 VLM 作为 System 2，负责复杂任务的逐步思考、语言交互和人类反馈整合。

基本结构：

```text
System 2：高层 VLM
  理解复杂指令
  自我对话 / 分解任务
  请求或利用人类反馈
  生成中间子目标

        |
        v

System 1：π0 VLA policy
  执行熟练的低层动作
  完成抓取、移动、放置等具体技能

        |
        v

机器人执行与反馈
```

它解决的问题是：单纯 π0 这类 VLA 更擅长短时、反应式技能，但复杂任务需要高层推理和交互。Hi Robot 用 System 2 VLM 把长任务拆成 π0 能执行的中间步骤，类似“VLM planner + VLA executor”的产品化架构。

对你面试最有用的点是：这和 GUI-Agent 的规划-执行-反馈闭环非常像。GUI-Agent 中大模型规划 UI action，执行器点击/滑动并读页面反馈；Hi Robot 中高层 VLM 规划物理子任务，π0 执行动作并读环境反馈。

---

## 12. OpenPI / LeRobot：开源与工程生态

OpenPI 是 Physical Intelligence 开源 π0 系列模型和训练代码的工程项目。它的价值不只是发布权重，更重要是提供了 VLA 训练、微调、部署、数据格式适配的参考实现。

OpenPI / LeRobot 生态中常见名字：

| 名称 | 含义 |
| --- | --- |
| `pi0_base` | π0 基础模型 |
| `pi0_fast_base` | π0-FAST 基础模型，自回归动作 token 路线 |
| `pi05_base` | π0.5 基础模型，开放世界泛化能力更强 |
| `pi0-FAST-DROID` | 基于 DROID 等数据训练/近似复现的 FAST 路线模型 |
| LoRA fine-tuning | 低显存/低成本适配下游机器人和数据集 |
| full fine-tuning | 全量微调，成本更高但适配能力更强 |

工程上要关注几个配置：

- `action_dim`：动作维度，取决于机器人控制接口。
- `action_horizon`：一次预测多少步 action chunk。
- `max_token_len`：提示词、状态 token、动作 token 的总长度限制。
- `proprioception`：是否输入机器人自身状态。
- 数据格式：图像、多视角、语言、动作、时间戳和 episode 元信息。

---

## 13. π0、π0-FAST、π0.5、π0.6 怎么取舍

| 场景 | 推荐优先考虑 | 原因 |
| --- | --- | --- |
| 学习 VLA 基本原理 | π0 | 最能代表 VLM + flow action decoder 的核心路线 |
| 做开源复现和微调 | OpenPI / LeRobot pi0_base | 生态资料较多，适合作为入门基线 |
| 希望更强语言跟随或 token 范式 | π0-FAST | action token 路线与 LLM/VLM 自回归范式一致 |
| 希望开放环境泛化 | π0.5 | co-training 引入高层语义和异构数据，更适合未见环境 |
| 希望更强 base model | π0.6 | 更适合作为 out-of-the-box 基线或下游微调起点 |
| 希望从真实部署经验中学习 | π*0.6 | 通过真实 rollout、人工纠正和 reward 提升稳定性 |
| 希望可控泛化和技能组合 | π0.7 | richer context 和 steerability 更适合复杂任务控制 |
| 单一窄域小任务 | π0 或专门 policy | π0.5 未必在所有小任务上更优，窄域数据质量更关键 |
| 产品落地 | VLM planner + π0/π0.5/skill + safety shield | 端到端 policy 仍需要安全、控制和失败恢复兜底 |

一句话：π0 是基础 VLA，π0-FAST 是动作 token 化变体，π0.5 是开放世界泛化升级版，π0.6 是更强 base model，π*0.6 是经验学习增强版，π0.7 是更可控的通用模型；选择哪个，取决于你更重视连续控制、语言 token 统一、新环境泛化、真实部署学习，还是可控技能组合。

---

## 14. 和 RT-2、GR00T 的关系

| 模型 | 动作建模路线 | 架构倾向 |
| --- | --- | --- |
| RT-2 | 动作 token 化 | 把 VLM 直接扩展为 action token generator |
| π0 | Flow matching 连续动作 | VLM backbone + continuous action decoder |
| π0-FAST | FAST action token | 自回归 VLA，接近 RT-2 的 token 范式但动作压缩更高效 |
| π0.5 | Flow/action + 异构 co-training | 在 π0 上增强 open-world generalization |
| π0.6 | 更强 VLM/action base | 更强 base model，强调 prompt/metadata 和下游适配 |
| π*0.6 | RECAP 经验学习 | 从真实 rollout 和人工纠正中继续改进 |
| π0.7 | Steerable generalist | 更强调 richer conditioning 和技能组合 |
| GR00T | VLM System 2 + diffusion/action System 1 | 显式快慢系统分层 |

RT-2 的贡献是证明 web-scale VLM 知识可以迁移到机器人动作，动作 token 化是关键抓手。π0 则把重点放到连续动作生成，用 flow matching 更自然地处理机器人轨迹。π0-FAST 又把 π0 系列拉回 token 路线，但用了更高效的 action tokenizer。GR00T 和 Hi Robot 则更强调系统分层：高层 VLM 理解和规划，低层 action model 快速执行。

---

## 15. 面试高频问题与参考答案

### Q1：π0 和 RT-2 最大区别是什么？

RT-2 更典型地把机器人动作表示成 token，让 VLM 像生成文本一样生成动作；π0 则使用预训练 VLM 作为语义 backbone，再用 flow matching action decoder 生成连续 action chunk。前者更接近 token-based VLA，后者更适合连续、平滑、灵巧的机器人控制。

### Q2：为什么 π0.5 比 π0 更强调 open-world generalization？

因为 π0.5 不只是做低层动作模仿，而是把机器人 demonstration、高层语义子任务、物体检测、语言指令、web 视觉语言数据等进行 co-training。这样模型不仅学会怎么动，还学会在新环境里识别对象、理解任务阶段、迁移语义知识，所以更适合未见家庭环境中的长链路任务。

### Q3：π0-FAST 是 π0.5 的前身吗？

不是。π0-FAST 是 π0 系列中的动作建模变体，核心是 FAST tokenizer + 自回归预测；π0.5 是 π0 的开放世界泛化升级版，核心是异构数据 co-training。二者解决的问题不同，一个偏动作表示和训练范式，一个偏泛化和任务能力。

### Q4：π0 系列是否可以直接用于产品机器人？

不能简单直接用。π0 系列提供了很强的 VLA policy 基线，但产品落地还需要 robot-specific fine-tuning、动作接口适配、实时控制、碰撞检测、异常恢复、任务管理、安全规则和日志回流。更现实的方式是把 π0/π0.5 作为低层 skill 或 action policy，外面套 VLM planner、behavior tree 和 safety shield。

### Q5：如果我有一个新机器人，应该怎么用 π0 系列？

首先统一数据格式：图像、多视角、语言、proprioception、动作、时间戳。然后确认动作空间和 `action_dim/action_horizon`，选择 π0 或 π0.5 做 LoRA 或全量微调。如果任务很窄、数据很少，π0 未必比专门 policy 更好；如果目标是开放环境泛化和长链路任务，π0.5 更值得尝试。无论哪种，都要搭建离线 replay、仿真/实机评测和安全兜底。

### Q6：π0.6 和 π0.5 的区别是什么？

π0.5 的核心是证明 open-world generalization，通过异构 co-training 让 VLA 能在未见环境中执行长链路任务；π0.6 更像这个路线之后的强 base model，进一步升级 VLM backbone、prompt/metadata 和训练数据组织，使模型 out-of-the-box 能力和下游微调起点更强。简单说，π0.5 更像能力方向的证明，π0.6 更像更成熟的底座。

### Q7：π*0.6 的星号是什么意思？

π*0.6 可以理解为在 π0.6 基础上经过真实经验学习强化的版本。它通过 RECAP 一类流程收集真实机器人 rollout、失败案例、人工纠正和 reward/advantage 信号，再继续训练模型，目标是解决离线 VLA 在真实部署中遇到的 distribution shift、失败恢复和长期稳定性问题。

### Q8：π0.7 又比 π0.6 多了什么？

π0.7 更强调 steerability，也就是让通用机器人模型更可控。它不只是输入一句指令和图像，而是通过更丰富的 prompt、metadata、subgoal images、任务上下文和多源数据，让模型知道要用哪个 embodiment、执行哪个子目标、遵守什么约束、最终状态应该是什么。它解决的是“通用模型会很多技能，但怎么让它按我想要的方式组合技能”的问题。

---

## 16. 针对转岗面试的讲法

可以这样把 π0 系列和你的 GUI-Agent 背景连起来：

> 我理解 π 系列的价值在于，它把 VLM 的语义理解和机器人连续动作生成结合起来。π0 用 VLM backbone 加 flow matching action decoder 解决从视觉语言到连续动作的问题；π0-FAST 探索把动作压缩成 token，用自回归方式统一文本和动作；π0.5 通过异构数据 co-training 走向开放世界泛化；π0.6 把这条路线进一步做成更强 base model；π*0.6 强调从真实机器人经验、人工纠正和 reward 中继续学习；π0.7 则进一步强调 steerability，让通用模型更可控地组合技能。这个方向和 GUI-Agent 很像：GUI-Agent 是把截图和 query 转成点击、滑动、输入；π 系列是把图像、语言和机器人状态转成抓取、移动、放置等连续动作。差别在于机器人需要处理 3D 空间、物理约束和安全控制，所以 VLA 外面仍然要有 planner、safety shield 和数据闭环。

---

## 17. 资料来源

- Physical Intelligence, π0: Our First Generalist Policy: https://www.pi.website/blog/pi0
- π0 paper, A Vision-Language-Action Flow Model for General Robot Control: https://arxiv.org/html/2410.24164v1
- Physical Intelligence, FAST: Efficient Robot Action Tokenization: https://www.pi.website/research/fast
- FAST paper: https://arxiv.org/html/2501.09747v1
- Physical Intelligence, Open Sourcing π0: https://www.pi.website/blog/openpi
- Physical Intelligence OpenPI GitHub: https://github.com/Physical-Intelligence/openpi
- Physical Intelligence, Hi Robot: Teaching Robots to Listen and Think Harder: https://www.pi.website/research/hirobot
- Physical Intelligence, π0.5 blog: https://www.pi.website/blog/pi05
- π0.5 paper: https://arxiv.org/abs/2504.16054
- π0.5 PDF: https://www.pi.website/download/pi05.pdf
- π0.6 model card: https://website.pi-asset.com/pi06star/PI06_model_card.pdf
- Physical Intelligence, Learning from Experience: https://www.pi.website/research/recap
- π*0.6 / RECAP paper: https://arxiv.org/abs/2511.06938
- π0.7 model card: https://www.pi.website/research/pi07
- LeRobot π0-FAST docs: https://huggingface.co/docs/lerobot/pi0fast
- LeRobot π0.5 model card: https://huggingface.co/lerobot/pi05_base
