# Grasp Dataset Registry

Schema version: `1.0`
Updated at: `2026-09-10`

## Category Counts

- `teleop`: 4
- `ego`: 2
- `umi`: 1
- `sim`: 3

## Datasets

| id | category | action | language | 3d/depth | role |
| --- | --- | --- | --- | --- | --- |
| droid | teleop | yes | yes | yes | Real robot teleoperation source for BC/SFT and multi-embodiment robustness. |
| open_x_embodiment | teleop | yes | yes | no | Broad co-training source for embodiment-aware pi0.5/pi0.7-ready experiments. |
| bridgedata_v2 | teleop | yes | yes | no | Language-conditioned tabletop manipulation source for BC/SFT. |
| libero | teleop | yes | yes | no | Primary v1 training and MuJoCo/LIBERO evaluation loop. |
| ego4d | ego | no | yes | no | Semantic hand-object interaction, affordance, subgoal, and failure annotation source. |
| egodex | ego | no | yes | yes | Dexterous hand-object affordance and subgoal supervision; not low-level robot action training. |
| umi | umi | yes | yes | yes | Human-in-the-wild demonstration source for gripper-centric grasping policies. |
| maniskill3 | sim | yes | yes | yes | High-throughput simulation, RL rollout, and multi-task generalization evaluation. |
| robocasa | sim | yes | yes | yes | Household scene generalization and long-horizon manipulation evaluation. |
| robotwin2 | sim | yes | yes | yes | Future bimanual/generalist simulation evaluation once v1 LIBERO is stable. |
