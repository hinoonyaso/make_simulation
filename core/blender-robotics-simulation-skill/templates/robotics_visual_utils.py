from __future__ import annotations

import math
import bpy
from mathutils import Vector, Matrix
from geometry_utils import curve_between, add_sphere

AXIS_COLORS = {
    'x': (0.86, 0.08, 0.10, 1.0),
    'y': (0.08, 0.65, 0.20, 1.0),
    'z': (0.05, 0.32, 0.90, 1.0),
}

LIDAR_STATE_COLORS = {
    'hit': (0.05, 0.63, 0.30, 1.0),          # matches material_utils 'output'
    'no_hit': (0.07, 0.08, 0.10, 1.0),       # matches material_utils 'ground_truth'
    'range_limit': (0.82, 0.08, 0.09, 1.0),  # matches material_utils 'error'
}


def create_emission_material(name, color, strength=2.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    if 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = color
    elif 'Emission' in bsdf.inputs:
        bsdf.inputs['Emission'].default_value = color
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = strength
    bsdf.inputs['Roughness'].default_value = 0.4
    return mat


def add_coordinate_frame(name='Frame', origin=(0, 0, 0), scale=0.6):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = origin
    mats = {k: create_emission_material(f'{name}_{k.upper()}_Mat', c, 1.3) for k, c in AXIS_COLORS.items()}
    axes = {
        'x': curve_between(f'{name}_X', (0, 0, 0), (scale, 0, 0), radius=0.012, material=mats['x']),
        'y': curve_between(f'{name}_Y', (0, 0, 0), (0, scale, 0), radius=0.012, material=mats['y']),
        'z': curve_between(f'{name}_Z', (0, 0, 0), (0, 0, scale), radius=0.012, material=mats['z']),
    }
    for obj in axes.values():
        obj.parent = root
    return root, axes


def add_point(name, location, material=None, radius=0.06):
    p = add_sphere(name, location, radius)
    if material is not None:
        p.data.materials.append(material)
    return p


def add_trajectory(name, points, material=None, radius=0.015):
    if len(points) < 2:
        raise ValueError('Trajectory needs at least two points')
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for dst, p in zip(spline.points, points):
        dst.co = (*p, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    if material is not None:
        obj.data.materials.append(material)
    return obj


def apply_matrix(obj, matrix_4x4):
    obj.matrix_world = Matrix(matrix_4x4)
    return obj


def _link_between(name, start, end, radius=0.10, material=None, bevel=0.025):
    from mathutils import Vector
    from geometry_utils import add_cylinder, apply_bevel
    a, b = Vector(start), Vector(end)
    v = b - a
    length = v.length
    if length <= 1e-6:
        raise ValueError("Link endpoints must differ")
    obj = add_cylinder(name, location=(a+b)/2, radius=radius, depth=length, bevel=bevel)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = v.to_track_quat('Z', 'Y')
    if material is not None:
        if len(obj.data.materials): obj.data.materials[0] = material
        else: obj.data.materials.append(material)
    return obj


def add_stylized_robot_arm(name='RobotArm', points=((0,0,0.35),(0.9,0,0.85),(1.55,0,1.35)),
                            link_material=None, joint_material=None, base_material=None, scale=1.0):
    """Reusable abstract arm with beveled links and readable joints. Points define joint centers."""
    from geometry_utils import add_cylinder, add_sphere
    pts=[Vector(p) for p in points]
    root=bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    base=add_cylinder(f'{name}_Base', pts[0]-(Vector((0,0,0.16))*scale), radius=.25*scale, depth=.28*scale, bevel=.035*scale)
    if base_material: base.data.materials.append(base_material)
    base.parent=root
    joints=[]; links=[]
    for i,p in enumerate(pts):
        j=add_sphere(f'{name}_J{i}', p, radius=.14*scale)
        if joint_material: j.data.materials.append(joint_material)
        j.parent=root; joints.append(j)
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        l=_link_between(f'{name}_L{i}', a, b, radius=.09*scale, material=link_material, bevel=.025*scale)
        l.parent=root; links.append(l)
    # small end-effector cue
    ee=add_cylinder(f'{name}_EE', pts[-1], radius=.09*scale, depth=.20*scale, bevel=.02*scale)
    ee.rotation_euler[1]=1.5708
    if joint_material: ee.data.materials.append(joint_material)
    ee.parent=root
    return {'root':root,'base':base,'joints':joints,'links':links,'ee':ee}


def add_planar_arm_rig(name='PlanarArm', origin=(0,0,0.4), lengths=(1.0,0.8),
                       link_material=None, joint_material=None, link_radius=0.10, joint_radius=0.14):
    """Original lightweight FK rig: each joint is a parent pivot rotating about local Z."""
    from geometry_utils import add_cube, add_sphere
    root=bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root); root.location=origin
    pivots=[]; links=[]; joint_meshes=[]
    parent=root
    for i,L in enumerate(lengths):
        pivot=bpy.data.objects.new(f'{name}_Joint{i}', None); bpy.context.collection.objects.link(pivot)
        pivot.parent=parent
        pivot.location=(0,0,0) if i==0 else (float(lengths[i-1]),0,0)
        pivots.append(pivot)
        jm=add_sphere(f'{name}_JointMesh{i}', (0,0,0), radius=joint_radius)
        jm.parent=pivot; jm.location=(0,0,0)
        if joint_material: jm.data.materials.append(joint_material)
        joint_meshes.append(jm)
        link=add_cube(f'{name}_Link{i}', (0,0,0), scale=(float(L)/2, link_radius, link_radius), bevel=link_radius*.35)
        link.parent=pivot; link.location=(float(L)/2,0,0)
        if link_material:
            if len(link.data.materials): link.data.materials[0]=link_material
            else: link.data.materials.append(link_material)
        links.append(link)
        parent=pivot
    ee=bpy.data.objects.new(f'{name}_EE', None); bpy.context.collection.objects.link(ee)
    ee.parent=pivots[-1]; ee.location=(float(lengths[-1]),0,0)
    ee_mesh=add_sphere(f'{name}_EEMesh',(0,0,0),radius=joint_radius*.75); ee_mesh.parent=ee; ee_mesh.location=(0,0,0)
    if joint_material: ee_mesh.data.materials.append(joint_material)
    return {'root':root,'pivots':pivots,'links':links,'joint_meshes':joint_meshes,'ee':ee,'ee_mesh':ee_mesh,'lengths':tuple(lengths)}


def add_lidar_scan(name, origin, ranges, angle_min, angle_increment, range_max,
                    z=0.0, hit_radius=0.03, ray_radius=0.006, materials=None):
    """Visualize a planar lidar scan from precomputed samples (sensor_msgs/LaserScan convention:
    ranges[i] is the distance at angle angle_min + i*angle_increment). A sample is 'no_hit' if its
    value is None/NaN/inf, 'range_limit' if it is >= range_max, otherwise a 'hit'. Never invent
    ranges here -- pass real driver output or real raycast results computed elsewhere; this only
    draws what it is given, per the lidar topic's evidence rule."""
    mats = dict(materials) if materials else {}
    for state, color in LIDAR_STATE_COLORS.items():
        mats.setdefault(state, create_emission_material(f'{name}_{state}_Mat', color, 1.1))

    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = (origin[0], origin[1], origin[2] + z)

    rays, hits, counts = [], [], {'hit': 0, 'no_hit': 0, 'range_limit': 0}
    for i, r in enumerate(ranges):
        angle = angle_min + i * angle_increment
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        if r is None or (isinstance(r, float) and (math.isnan(r) or math.isinf(r))):
            state, dist = 'no_hit', float(range_max)
        elif r >= range_max:
            state, dist = 'range_limit', float(range_max)
        else:
            state, dist = 'hit', float(r)
        counts[state] += 1
        end = direction * dist
        ray = curve_between(f'{name}_Ray{i}', (0, 0, 0), end, radius=ray_radius, material=mats[state])
        ray.parent = root
        rays.append(ray)
        if state == 'hit':
            hit = add_point(f'{name}_Hit{i}', end, material=mats['hit'], radius=hit_radius)
            hit.parent = root
            hits.append(hit)
    return {'root': root, 'rays': rays, 'hits': hits, 'counts': counts, 'materials': mats}


def keyframe_joint_angles(rig, frame, angles_rad):
    """Keyframe relative planar joint angles; child transforms propagate FK automatically."""
    if len(angles_rad) != len(rig['pivots']):
        raise ValueError('angles_rad length must match number of joints')
    for pivot,theta in zip(rig['pivots'],angles_rad):
        pivot.rotation_mode='XYZ'; pivot.rotation_euler[2]=float(theta)
        pivot.keyframe_insert(data_path='rotation_euler', frame=int(frame), index=2)
    return rig
