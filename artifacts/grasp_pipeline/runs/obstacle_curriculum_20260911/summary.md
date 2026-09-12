# LIBERO Obstacle Curriculum

Updated: 2026-09-11T01:57:32

- Task group: `libero_goal`
- Task ids: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`
- Scenario count: `50`
- Planned episodes: `450`

## Difficulty Mix

- `easy`: 10 scenarios, 50 episodes
- `medium`: 20 scenarios, 200 episodes
- `hard`: 20 scenarios, 200 episodes

## Metrics

- `task_success`: original LIBERO sparse success
- `collision_count`: robot-obstacle contacts
- `min_clearance_m`: minimum robot-obstacle clearance
- `safety_success`: no collision and clearance above margin
- `avoidance_success`: task success and safety success

## Next Execution Hook

Use this JSON as input for the MuJoCo/Isaac obstacle injector and expert trajectory collector.
