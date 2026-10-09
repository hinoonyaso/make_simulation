# Scenario examples and current runner boundary

The environment catalog and backend preflight are implemented at `core/simulation/environments/`. The loader currently reports dependencies and explicitly refuses to call a backend load validated. Scenario execution is planned; this file is not an executable scenario contract.

## Mobile navigation (planned)

```yaml
environment: clearpath.office.v1
robot: clearpath_jackal  # choose only after source/config verification
initial_pose: unknown     # world frame, meters, radians
goal: unknown
sensors: unknown
physics_dt_s: unknown
stop_condition: unknown
trace: robotics-visual-trace/v1
```

## Manipulation PickCube (planned)

```yaml
environment: maniskill.pickcube.v1
task: PickCube-v1
robot: task_default  # must be read from the pinned task definition
initial_state: task_reset
action: not_run
object_state: not_run
camera: task_default
trace: mechanism-specific simulation trace (schema to be defined with a working backend)
```

These templates deliberately contain unresolved fields. No backend runner or validated environment trace exists yet.
