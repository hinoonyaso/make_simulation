# Asset validation report

Command: `uv run python scripts/manage_assets.py validate --asset blender.open_manipulator_x.v1`.

Result: PASS for local file hash, URDF XML, unique link/joint names, link references, joint limit/axis/mesh scale fields, and all referenced package meshes. Root URDF: `assets/open_manipulator_x/urdf/open_manipulator_x/open_manipulator_x.urdf`. 13 files; 9 links; 8 joints (4 revolute and 2 prismatic actuated joints); 7 unique mesh references; aggregate SHA-256 `68f4a7a8336a5a1696280f24b8309efbd50b5358a294263153853446498c596e`.

Not run: xacro expansion, ROS package resolution, MuJoCo/Blender load, dynamics, or hardware validation. File and mesh presence does not prove simulator compatibility.
