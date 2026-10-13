from __future__ import annotations

import bpy
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.visual_primitives.design_tokens import (
    TOKENS as DESIGN_TOKENS,
    hex_to_linear_rgba,
    profile_color,
)


def _rgba(value):
    if len(value) == 3:
        return (*value, 1.0)
    return tuple(value)


def principled_material(
    name,
    base_color=(0.5, 0.5, 0.5, 1.0),
    metallic=0.0,
    roughness=0.45,
    emission_color=None,
    emission_strength=0.0,
    transmission=0.0,
):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = _rgba(base_color)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    transmission_socket = bsdf.inputs.get('Transmission Weight') or bsdf.inputs.get('Transmission')
    if transmission_socket is not None:
        transmission_socket.default_value = transmission

    # Blender 4.x/5.x Principled input names.
    if emission_color is not None:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = _rgba(emission_color)
        elif 'Emission' in bsdf.inputs:  # compatibility fallback
            bsdf.inputs['Emission'].default_value = _rgba(emission_color)
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat


def visual_material(name, color_role, *, profile='technical_dark', material_role='plastic'):
    """Create a semantic Blender material from shared design and material tokens."""
    try:
        color = profile_color(color_role, profile)
    except KeyError as exc:
        raise KeyError(f"unknown visual color role {color_role!r}") from exc
    try:
        material = DESIGN_TOKENS['material_roles'][material_role]
    except KeyError as exc:
        raise ValueError(f"unknown material role {material_role!r}") from exc
    return principled_material(name, hex_to_linear_rgba(color),
                               metallic=material['metallic'], roughness=material['roughness'],
                               transmission=material.get('transmission', 0.0))


def assign_material(obj, material):
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material
    return obj


def default_material_library():
    return {
        'neutral_primary': principled_material('M_NeutralPrimary', (0.28, 0.32, 0.38, 1), metallic=0.25, roughness=0.36),
        'neutral_secondary': principled_material('M_NeutralSecondary', (0.58, 0.62, 0.68, 1), metallic=0.08, roughness=0.48),
        'sensor': principled_material('M_Sensor', (0.045, 0.055, 0.07, 1), metallic=0.15, roughness=0.38),
        'active': principled_material('M_Active', (0.0, 0.45, 0.82, 1), roughness=0.30),
        'output': principled_material('M_Output', (0.05, 0.63, 0.30, 1), roughness=0.34),
        'error': principled_material('M_Error', (0.82, 0.08, 0.09, 1), roughness=0.36),
        'ground_truth': principled_material('M_GroundTruth', (0.07, 0.08, 0.10, 1), roughness=0.42),
        'floor': principled_material('M_Floor', (0.72, 0.75, 0.79, 1), roughness=0.82),
    }
