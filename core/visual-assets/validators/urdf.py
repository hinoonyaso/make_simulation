"""Conservative URDF reference/structure validator; does not load physics or xacro."""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


PACKAGE_URI = re.compile(r"^package://([^/]+)/(.+)$")


def validate_urdf_asset(root: str | Path, entry: dict) -> dict:
    project_root = Path(root).resolve()
    asset_root = (project_root / entry["source"]).resolve()
    if not asset_root.is_relative_to(project_root):
        raise ValueError("asset source escapes project root")
    urdf_path = (project_root / entry["root_file"]).resolve()
    if not urdf_path.is_relative_to(asset_root) or not urdf_path.is_file():
        raise FileNotFoundError(f"URDF root is missing or outside the asset: {urdf_path}")
    robot = ET.parse(urdf_path).getroot()
    if robot.tag != "robot" or not robot.get("name"):
        raise ValueError("URDF root must be <robot name=...>")

    errors: list[str] = []
    links = [node.get("name") for node in robot.findall("link")]
    joints = robot.findall("joint")
    joint_names = [node.get("name") for node in joints]
    if not links or any(not value for value in links) or len(set(links)) != len(links):
        errors.append("link names must exist and be unique")
    if any(not value for value in joint_names) or len(set(joint_names)) != len(joint_names):
        errors.append("joint names must exist and be unique")
    link_set = set(links)
    parents = set()
    actuated: dict[str, int] = {}
    mesh_refs: set[str] = set()
    package_name = entry.get("ros_package_name")

    for joint in joints:
        name = joint.get("name", "?")
        kind = joint.get("type")
        parent = joint.find("parent")
        child = joint.find("child")
        parent_name = parent.get("link") if parent is not None else None
        child_name = child.get("link") if child is not None else None
        if parent_name not in link_set or child_name not in link_set or parent_name == child_name:
            errors.append(f"joint {name} has an invalid parent/child link reference")
        if child_name in parents:
            errors.append(f"link {child_name} has multiple parent joints")
        if child_name:
            parents.add(child_name)
        if kind in {"revolute", "continuous", "prismatic"}:
            actuated[kind] = actuated.get(kind, 0) + 1
            axis = joint.find("axis")
            if axis is not None:
                try:
                    values = [float(v) for v in axis.get("xyz", "").split()]
                    if len(values) != 3 or not all(math.isfinite(v) for v in values) or sum(v*v for v in values) == 0:
                        errors.append(f"joint {name} has invalid axis")
                except ValueError:
                    errors.append(f"joint {name} has invalid axis")
            if kind != "continuous":
                limit = joint.find("limit")
                if limit is None:
                    errors.append(f"joint {name} is missing limits")
                else:
                    try:
                        lower, upper = float(limit.attrib["lower"]), float(limit.attrib["upper"])
                        if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper:
                            errors.append(f"joint {name} has invalid lower/upper limits")
                    except (KeyError, ValueError):
                        errors.append(f"joint {name} has invalid lower/upper limits")

    for mesh in robot.findall(".//mesh"):
        filename = mesh.get("filename", "")
        match = PACKAGE_URI.match(filename)
        if not match or (package_name and match.group(1) != package_name):
            errors.append(f"unsupported or unexpected mesh URI: {filename}")
            continue
        relative = Path(match.group(2))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"mesh URI escapes package: {filename}")
            continue
        target = (asset_root / relative).resolve()
        if not target.is_relative_to(asset_root) or not target.is_file():
            errors.append(f"missing mesh reference: {filename}")
        else:
            mesh_refs.add(relative.as_posix())
        scale = mesh.get("scale")
        if scale:
            try:
                values = [float(v) for v in scale.split()]
                if len(values) != 3 or not all(math.isfinite(v) and v > 0 for v in values):
                    errors.append(f"mesh {filename} has invalid scale")
            except ValueError:
                errors.append(f"mesh {filename} has invalid scale")

    for mass in robot.findall(".//inertial/mass"):
        try:
            value = float(mass.get("value", "nan"))
            if not math.isfinite(value) or value < 0:
                errors.append("inertial mass must be finite and nonnegative")
        except ValueError:
            errors.append("inertial mass must be numeric")

    if errors:
        raise ValueError("URDF validation failed: " + "; ".join(errors))
    return {"asset_id": entry["id"], "urdf": str(urdf_path),
            "robot_name": robot.get("name"), "link_count": len(links),
            "joint_count": len(joints), "actuated_joint_counts": actuated,
            "resolved_mesh_count": len(mesh_refs), "resolved_meshes": sorted(mesh_refs),
            "xml_parse": "pass", "link_joint_references": "pass",
            "mesh_resolution": "pass", "joint_limits_axes_and_scales": "pass",
            "dynamics_engine_load": "not_run", "xacro_expansion": "not_run"}
