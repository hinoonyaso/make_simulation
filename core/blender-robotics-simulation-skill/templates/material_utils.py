from __future__ import annotations

import bpy


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
):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = _rgba(base_color)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness

    # Blender 4.x/5.x Principled input names.
    if emission_color is not None:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = _rgba(emission_color)
        elif 'Emission' in bsdf.inputs:  # compatibility fallback
            bsdf.inputs['Emission'].default_value = _rgba(emission_color)
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat


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
