# Environment catalog

The machine-readable source is [`core/simulation/environments/registry.json`](../../../core/simulation/environments/registry.json). An environment is a candidate until a pinned source, dependency closure, simulator load, physics step, and render are recorded. `not_downloaded`, `not_run`, and `blocked_*` values are intentional and never imply READY.

| ID | Candidate | Simulator | Source / revision | Current state |
|---|---|---|---|---|
| `clearpath.office.v1` | indoor mobile navigation | ROS 2 Jazzy + Gazebo Harmonic | [official repo](https://github.com/clearpathrobotics/clearpath_simulator), revision not pinned | Not downloaded; required executables absent; dependent model licenses not audited |
| `maniskill.pickcube.v1` | tabletop manipulation | ManiSkill / SAPIEN | [official repo](https://github.com/mani-skill/ManiSkill), revision not pinned | Not downloaded; `sapien` absent; WSL rendering unsupported by project's system matrix |
| `robosuite.lift.v1` | robot-arm lift task | robosuite / MuJoCo | [official repo](https://github.com/ARISE-Initiative/robosuite), revision not pinned | MuJoCo installed, robosuite absent; package acquisition blocked by DNS/network |

The Clearpath repository README lists office, warehouse, construction, orchard, pipeline, and solar_farm worlds and instructs users to install ROS 2 Jazzy/Gazebo Harmonic and build the simulator workspace. A world SDF alone does not prove its `model://` / Fuel dependency closure. The ManiSkill framework repository uses Apache-2.0, but individual third-party assets require their own attribution/license review. These environment entries therefore keep asset licenses unknown until every model and texture is inventoried.

`uv run python scripts/manage_assets.py search --category environment` lists candidates. `fetch` refuses entries without pinned revision, HTTPS source, SHA-256, declared size, allowlisted host, and reviewed install path. The generic archive helper caps downloads at 100 MiB and rejects traversal, symlinks, special files, hash mismatch, and oversized extraction. It never executes downloaded scripts. This catalog currently has no environment archive satisfying the fetch contract.
