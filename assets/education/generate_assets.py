#!/usr/bin/env python3
"""Generate simple, animation-ready engineering teaching assemblies in Blender.

All authored dimensions are metres. These are explicit educational models,
not replicas of a particular commercial product or solver-ready CAD.
Run: blender --background --python generate_assets.py -- --output-root <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "generated"


def material(name, color, metallic=0.0, roughness=0.35):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


STEEL = material("Steel | educational", (0.48, 0.58, 0.68), 0.78)
DARK = material("Graphite", (0.075, 0.105, 0.14), 0.35)
COPPER = material("Copper winding", (0.8, 0.27, 0.08), 0.65)
BLUE = material("Electrical blue", (0.04, 0.32, 0.82), 0.25)
RED = material("Electrical red", (0.85, 0.08, 0.07), 0.18)
GOLD = material("Contact gold", (0.9, 0.62, 0.12), 0.7)
GREEN = material("PCB green", (0.025, 0.28, 0.16), 0.15)
WHITE = material("Ceramic", (0.82, 0.86, 0.88), 0.08)


def reset_scene(name):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.collections):
        if block.name != "Collection":
            bpy.data.collections.remove(block)
    scene = bpy.context.scene
    scene.name = name
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.world.color = (0.035, 0.045, 0.06)
    scene.frame_start, scene.frame_end, scene.render.fps = 1, 72, 30
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -3.0
    return scene


def add_obj(obj, name, mat, collection=None):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if collection:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def cube(name, loc, scale, mat, bevel=0.0, coll=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = add_obj(bpy.context.object, name, mat, coll)
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Soft manufactured edges", "BEVEL")
        mod.width, mod.segments = bevel, 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=64, axis="Z", coll=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = add_obj(bpy.context.object, name, mat, coll)
    if axis == "Y":
        obj.rotation_euler[0] = math.pi / 2
    elif axis == "X":
        obj.rotation_euler[1] = math.pi / 2
    bevel = obj.modifiers.new("Edge highlights", "BEVEL")
    bevel.width = min(radius * 0.08, depth * 0.08)
    bevel.segments = 2
    obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def torus(name, loc, major, minor, mat, coll=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=96, minor_segments=16, location=loc)
    return add_obj(bpy.context.object, name, mat, coll)


def mesh_obj(name, verts, faces, mat, coll=None):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    (coll or bpy.context.collection).objects.link(obj)
    obj.data.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def ring_mesh(name, r_outer, r_inner, z0, z1, mat, coll, segments=128, groove=0.0):
    # Radial section: flat inner/outer shoulders with a shallow concave race groove.
    profile = [(r_inner,z0),(r_outer,z0),(r_outer,z1),(r_inner,z1)]
    if groove:
        profile = [(r_inner,z0),(r_outer,z0),(r_outer,z1),(r_inner,z1),
                   (r_inner+groove,z1*0.65+z0*0.35),(r_inner+2*groove,(z0+z1)/2),
                   (r_inner+groove,z0*0.65+z1*0.35)]
    verts=[]; faces=[]
    for r,z in profile:
        verts.extend([(r*math.cos(2*math.pi*i/segments),r*math.sin(2*math.pi*i/segments),z)
                      for i in range(segments)])
    n=len(profile)
    for j in range(n):
        jj=(j+1)%n
        for i in range(segments):
            ni=(i+1)%segments
            faces.append((j*segments+i,j*segments+ni,jj*segments+ni,jj*segments+i))
    return mesh_obj(name,verts,faces,mat,coll)


def gear(name, teeth, module, center, mat, coll, bore_radius):
    """Polygonal teaching gear with visibly defined teeth, not an involute CAD gear."""
    rp=module*teeth/2
    root=max(module*0.5,rp-module*1.25)
    tip=rp+module
    z0,z1=-0.004,0.004
    points=[]
    for i in range(teeth):
        a=2*math.pi*i/teeth
        for frac,r in ((0,root),(0.18,root),(0.28,tip),(0.72,tip),(0.82,root),(1,root)):
            points.append((center[0]+r*math.cos(a+frac*2*math.pi/teeth),
                           center[1]+r*math.sin(a+frac*2*math.pi/teeth)))
    n=len(points)
    verts=[]
    verts.extend((x,y,z0) for x,y in points)
    verts.extend((x,y,z1) for x,y in points)
    for z in (z0,z1):
        verts.extend((center[0]+bore_radius*math.cos(2*math.pi*i/n),
                      center[1]+bore_radius*math.sin(2*math.pi*i/n),z) for i in range(n))
    ob,ot,ib,it=0,n,2*n,3*n
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((ot+i,ot+j,it+j,it+i),
                      (ob+j,ob+i,ib+i,ib+j),
                      (ob+i,ob+j,ot+j,ot+i),
                      (ib+j,ib+i,it+i,it+j)))
    obj=mesh_obj(name,verts,faces,mat,coll)
    for poly in obj.data.polygons: poly.use_smooth=False
    obj["teeth"]=teeth; obj["module_m"]=module; obj["pitch_radius_m"]=rp
    obj["root_radius_m"]=root
    obj["tip_radius_m"]=tip
    obj["tooth_profile"]="stylized polygonal teaching profile; not involute"
    return obj


def gear_stage():
    sc=reset_scene("EDU | Spur gears | 20:40")
    c=collection("Gear pair | separate animated bodies")
    module=0.002
    g1=gear("Pinion_20T",20,module,(-0.03,0,0),GOLD,c,0.003)
    g2=gear("Gear_40T",40,module,(0.03,0,0),STEEL,c,0.005)
    # Each tooth is explicitly represented by the profile; add shallow hub and shafts.
    cylinder("Pinion_Hub",(-0.03,0,0.006),0.006,0.008,DARK,axis="Z",coll=c)
    cylinder("Gear_Hub",(0.03,0,0.006),0.010,0.008,DARK,axis="Z",coll=c)
    for frame in (1,72):
        t=(frame-1)/71
        g1.rotation_euler[2]=t*2*math.pi
        g2.rotation_euler[2]=-t*math.pi+math.pi/40
        g1.keyframe_insert("rotation_euler",frame=frame)
        g2.keyframe_insert("rotation_euler",frame=frame)
    linearize_object_animation([g1,g2])
    return {"main":g1,"focus":[g1,g2]}, {"ratio":2.0,"center_distance_m":0.06,
        "module_m":module,"pinion_teeth":20,"gear_teeth":40,
        "profile":"stylized polygonal teeth, non-involute; pitch radii give 0.06 m center distance"}


def bearing_stage():
    sc=reset_scene("EDU | Deep groove bearing assembly | 6204 envelope")
    c=collection("6204 envelope and estimated internal teaching geometry")
    # Standard 6204 boundary envelope 20 x 47 x 14 mm; internal details are estimates.
    ring_mesh("Outer_Ring",0.0235,0.0185,-0.007,0.007,STEEL,c,groove=0.0017)
    inner=ring_mesh("Inner_Ring",0.0130,0.0100,-0.007,0.007,GOLD,c,groove=0.0015)
    balls=[]
    inner_contact=0.0130
    outer_contact=0.0185
    br=(outer_contact-inner_contact)/2
    pitch=(inner_contact+outer_contact)/2
    cage_ratio=inner_contact/(inner_contact+outer_contact)
    ball_spin_ratio=-inner_contact/(2*br)
    for i in range(8):
        a=2*math.pi*i/8
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=br,
            location=(pitch*math.cos(a),pitch*math.sin(a),0))
        ball=add_obj(bpy.context.object,f"Ball_{i+1:02d}",WHITE,c)
        balls.append(ball)
    cage=torus("Cage_Ring",(0,0,0),pitch,0.00055,GOLD,c)
    cage_root=bpy.data.objects.new("Cage_Assembly",None); c.objects.link(cage_root)
    cage.parent=cage_root
    for i in range(8):
        a=2*math.pi*i/8
        pocket=torus(f"Cage_Pocket_Land_{i+1:02d}",(pitch*math.cos(a),pitch*math.sin(a),0),br,0.00028,GOLD,c)
        pocket.parent=cage_root
    # Create a bearing group empty for assembly/exploded view; keep parts separate.
    root=bpy.data.objects.new("Bearing_6204_Assembly",None); c.objects.link(root)
    for obj in list(c.objects):
        if obj != root and obj.parent is None: obj.parent=root
    for frame,angle in ((1,0),(72,math.pi*2)):
        inner.rotation_euler[2]=angle
        cage_root.rotation_euler[2]=angle*cage_ratio
        inner.keyframe_insert("rotation_euler",frame=frame)
        cage_root.keyframe_insert("rotation_euler",frame=frame)
    for i,ball in enumerate(balls):
        ball.rotation_mode="QUATERNION"
        for frame in range(1,73):
            angle=(frame-1)/71*(2*math.pi)
            a=2*math.pi*i/len(balls)+angle*cage_ratio
            ball.location=(pitch*math.cos(a),pitch*math.sin(a),0)
            tangent=Vector((-math.sin(a),math.cos(a),0)).normalized()
            ball.rotation_quaternion=Quaternion(tangent,angle*ball_spin_ratio)
            ball.keyframe_insert("location",frame=frame)
            ball.keyframe_insert("rotation_quaternion",frame=frame)
    linearize_object_animation([inner,cage_root,*balls])
    return {"main":root,"focus":[root,inner,cage_root,*balls]}, {
        "reference_envelope":"6204 boundary dimensions 20x47x14 mm",
        "internal_geometry":"estimated educational geometry; 8 balls, not manufacturer internal design",
        "motion":{"assumption":"ideal rolling at inner/outer race contacts; outer race fixed; prescribed kinematics, no contact solver",
                  "inner_contact_radius_m":inner_contact,"outer_contact_radius_m":outer_contact,
                  "ball_radius_m":br,"cage_angular_speed_over_inner":cage_ratio,
                  "ball_spin_angular_speed_over_inner":ball_spin_ratio,"ball_pose_keyframes":72},
        "objects":[o.name for o in c.objects]}


def motor_stage():
    sc=reset_scene("EDU | Three phase BLDC motor concept")
    c=collection("Motor assembly | separated stator, coils, magnets and rotor")
    # Stator lamination ring, 9 teeth and simplified 3-phase coils.
    ring_mesh("Stator_Core",0.080,0.038,-0.012,0.012,DARK,c)
    for i in range(9):
        a=2*math.pi*i/9
        tooth=cube(f"Stator_Tooth_{i+1:02d}",(0.053*math.cos(a),0.053*math.sin(a),0),
                   (0.040,0.017,0.024),STEEL,0.002,c)
        tooth.rotation_euler[2]=a
        coil=torus(f"Phase_{'ABC'[i%3]}_Coil_{i+1:02d}",
                   (0.066*math.cos(a),0.066*math.sin(a),0),0.009,0.003,
                   (RED,BLUE,COPPER)[i%3],c)
        coil.rotation_euler[1]=math.pi/2
        coil.rotation_euler[2]=a
    rotor=cylinder("Rotor_Core",(0,0,0),0.033,0.022,STEEL,axis="Z",coll=c)
    for i in range(6):
        a=2*math.pi*i/6
        magnet=cube(f"Rotor_Magnet_{i+1:02d}",(0.027*math.cos(a),0.027*math.sin(a),0),
                    (0.015,0.020,0.018),RED if i%2==0 else BLUE,0.002,c)
        magnet.rotation_euler[2]=a
        magnet["pole"]="N" if i%2==0 else "S"
    cylinder("Motor_Shaft",(0,0,0.028),0.006,0.070,STEEL,axis="Z",coll=c)
    for frame,angle in ((1,0),(72,math.pi*2)):
        rotor.rotation_euler[2]=angle; rotor.keyframe_insert("rotation_euler",frame=frame)
        for obj in c.objects:
            if obj.name.startswith("Rotor_Magnet"):
                obj.rotation_euler[2]=obj.rotation_euler[2]+angle
                obj.keyframe_insert("rotation_euler",frame=frame)
    linearize_object_animation(list(c.objects))
    root=bpy.data.objects.new("BLDC_Assembly",None); c.objects.link(root)
    return {"main":root,"focus":list(c.objects)}, {
        "topology":"9-slot/6-pole educational concept, not product specification",
        "phase_colors":{"A":"red","B":"blue","C":"copper"},
        "magnet_poles":"alternating N/S labels; color is explanatory",
        "motion":"rotor angle is keyframed; no electromagnetic field or torque solver"}


def pcb_stage():
    reset_scene("EDU | Layered PCB teaching model")
    c=collection("PCB | visible laminate, copper, vias, MCU and connectors")
    cube("FR4_Substrate",(0,0,0),(0.18,0.12,0.003),GREEN,0.003,c)
    # Four thin copper layers with explicit vertical offsets for legible section/exploded views.
    for i,z in enumerate((-0.00125,-0.00055,0.00055,0.00125)):
        cube(f"Copper_Layer_{i+1}",(0,0,z),(0.17,0.11,0.00018),GOLD,0,c)
    # Routing traces are actual narrow mesh bars, deliberately schematic, not routed net data.
    routes=[((-0.065,-0.035),(-0.015,0.018)),((-0.015,0.018),(0.035,0.018)),
            ((0.035,0.018),(0.065,0.040)),((-0.06,0.04),(-0.01,0.04)),
            ((0.01,-0.04),(0.065,-0.04)),((-0.07,-0.01),(-0.04,-0.01))]
    for i,((x1,y1),(x2,y2)) in enumerate(routes):
        dx,dy=x2-x1,y2-y1; length=math.hypot(dx,dy)
        obj=cube(f"Trace_Top_{i+1:02d}",((x1+x2)/2,(y1+y2)/2,0.0017),(length,0.0016,0.00045),COPPER,0.0003,c)
        obj.rotation_euler[2]=math.atan2(dy,dx)
    for i,(x,y) in enumerate(((-.04,-.01),(.035,.018),(.065,-.04),(-.015,.04))):
        cylinder(f"Through_Via_{i+1:02d}",(x,y,0),0.0022,0.006,GOLD,vertices=24,axis="Z",coll=c)
        cylinder(f"Via_Bore_{i+1:02d}",(x,y,0),0.0011,0.007,DARK,vertices=20,axis="Z",coll=c)
    cube("MCU_Package",(0.015,0.005,0.006),(0.040,0.032,0.009),DARK,0.002,c)
    for x in (-.008,-.002,.004,.010,.016,.022,.028,.034):
        for y in (-.014,.024): cube(f"MCU_Pin_{x:.3f}_{y:.3f}",(x,y,0.004),(0.002,0.006,0.001),GOLD,0,c)
    cube("USB_Connector",(-.065,0,0.007),(0.028,0.020,0.012),STEEL,0.002,c)
    cube("Power_Connector",(.060,.040,0.006),(0.018,0.015,0.010),WHITE,0.001,c)
    # Three-frame layer separation animation; the layer objects remain individually selectable.
    for i,z in enumerate((-0.00125,-0.00055,0.00055,0.00125)):
        obj=bpy.data.objects.get(f"Copper_Layer_{i+1}")
        for frame,spread in ((1,0),(24,(i-1.5)*0.003),(48,(i-1.5)*0.003),(72,0)):
            obj.location.z=z+spread
            obj.keyframe_insert("location",frame=frame)
    return {"main":bpy.data.objects["FR4_Substrate"],"focus":list(c.objects)}, {
        "stack":"FR4 plus four illustrative copper planes; not a fabrication stackup",
        "traces":"schematic geometry not electrical netlist routing",
        "via_types":["through-hole via"],"objects":[o.name for o in c.objects]}


def mechanism_stage():
    sc=reset_scene("EDU | Shafts, coupling, spring, fasteners and battery")
    c=collection("Parametric engineering primitives")
    shaft=cylinder("Stepped_Shaft",(-.15,0,0),.018,.18,STEEL,axis="X",coll=c)
    cylinder("Shaft_Step",(-.03,0,0),.028,.08,GOLD,axis="X",coll=c)
    cylinder("Key",(-.03,.027,0),.004,.055,DARK,axis="X",coll=c)
    cylinder("Flexible_Coupling",(.08,0,0),.035,.07,BLUE,axis="X",coll=c)
    for i in range(5):
        torus(f"Coupling_Groove_{i+1}",(.05+i*.015,0,0),.035,.002,WHITE,c)
    # Helical spring as a curve; named and grouped for future parameter changes.
    curve=bpy.data.curves.new("Compression_Spring_Path","CURVE"); curve.dimensions="3D"; curve.bevel_depth=.002; curve.bevel_resolution=3
    spline=curve.splines.new("POLY"); turns=8; n=turns*32; spline.points.add(n-1)
    for i,p in enumerate(spline.points):
        t=i/(n-1); a=2*math.pi*turns*t
        p.co=(.25+.03*math.cos(a),.04*math.sin(a),-.055+.11*t,1)
    spring=bpy.data.objects.new("Compression_Spring",curve); c.objects.link(spring); curve.materials.append(COPPER)
    for i in range(4):
        x=.18+i*.03
        cylinder(f"M6_Bolt_{i+1}",(x,.08,0),.006,.06,STEEL,vertices=6,axis="Z",coll=c)
        cylinder(f"M6_Washer_{i+1}",(x,.08,-.012),.010,.002,GOLD,axis="Z",coll=c)
        cylinder(f"M6_Nut_{i+1}",(x,.08,-.020),.009,.008,STEEL,vertices=6,axis="Z",coll=c)
    # Battery cell, can and educational cutaway layers.
    cylinder("Cell_18650_Can",(-.05,.12,0),.009,.065,DARK,axis="Z",coll=c)
    cylinder("Cell_Cathode_Can",(-.05,.12,.034),.007,.002,RED,axis="Z",coll=c)
    cylinder("Cell_Anode_Cap",(-.05,.12,-.034),.006,.002,BLUE,axis="Z",coll=c)
    cylinder("Cathode_Electrode",(-.025,.12,0),.0025,.05,RED,axis="Z",coll=c)
    cylinder("Separator",(-.015,.12,0),.001,.05,WHITE,axis="Z",coll=c)
    cylinder("Anode_Electrode",(-.005,.12,0),.0025,.05,BLUE,axis="Z",coll=c)
    for frame,angle in ((1,0),(72,2*math.pi)):
        shaft.rotation_euler[0]=angle
        shaft.keyframe_insert("rotation_euler",frame=frame)
    linearize_object_animation([shaft])
    return {"main":shaft,"focus":list(c.objects)}, {
        "shaft":"parametric stepped shaft, keyed section is illustrative",
        "coupling":"flexible coupling shown as simplified grooved cylinder",
        "spring":"geometric compression spring; no force law",
        "fasteners":"generic M6 educational geometry",
        "cell":"18650 envelope-inspired concept; internal layers simplified, not cell construction data"}


def structure_fluid_stage():
    sc=reset_scene("EDU | Bracket, beam, heatsink and fan")
    c=collection("Structural and thermal fluid teaching geometry")
    # Cantilever block and perforated plate bracket as separated pieces.
    cube("Cantilever_Beam",(-.10,0,.03),(.24,.035,.035),STEEL,.002,c)
    cube("Fixed_Wall",(-.24,0,0),(.025,.10,.12),DARK,.004,c)
    cube("L_Bracket_Base",(.08,0,0),(.12,.08,.012),BLUE,.002,c)
    cube("L_Bracket_Web",(.08,-.034,.04),(.12,.012,.08),BLUE,.002,c)
    for i,x in enumerate((.035,.125)):
        cylinder(f"Bracket_Bolt_Hole_Rim_{i+1}",(x,-.041,.04),.009,.004,GOLD,vertices=48,axis="Y",coll=c)
    # Simplified fin stack and axial fan.
    cube("Heat_Sink_Base",(.26,0,0),(.10,.08,.010),STEEL,.002,c)
    for i in range(9): cube(f"Heat_Sink_Fin_{i+1:02d}",(.26-.044+i*.011,0,.027),(.003,.07,.045),STEEL,.0008,c)
    torus("Fan_Frame",(.42,0,.025),.038,.004,DARK,c)
    cylinder("Fan_Hub",(.42,0,.025),.010,.018,GOLD,axis="Y",coll=c)
    for i in range(5):
        a=2*math.pi*i/5
        blade=cube(f"Fan_Blade_{i+1}",(.42+.022*math.cos(a),.0,.025+.022*math.sin(a)),(.034,.003,.010),BLUE,.003,c)
        blade.rotation_euler[1]=-a
        for frame,angle in ((1,0),(72,2*math.pi)):
            blade.rotation_euler[1]=-a+angle; blade.keyframe_insert("rotation_euler",frame=frame)
    linearize_object_animation([obj for obj in c.objects if obj.name.startswith("Fan_Blade_")])
    return {"main":bpy.data.objects["Cantilever_Beam"],"focus":list(c.objects)}, {
        "beam":"visual load-transfer example only; no stress field",
        "bracket":"conceptual L-bracket with symbolic hole rims",
        "heatsink":"regular fins for heat-flow explanation, not thermal CFD geometry",
        "fan":"5-blade simplified impeller; no aerodynamic performance claim"}


def add_stage(scene, targets):
    subject=targets["main"]
    subject["education_asset_scene"]=scene.name
    subject["units"]="m"


def linearize_object_animation(objects):
    """Use constant-rate key interpolation across Blender 4.x and layered 5.x actions."""
    for obj in objects:
        animation = obj.animation_data
        action = animation.action if animation else None
        if action is None:
            continue
        curves = list(getattr(action, "fcurves", ()))
        if not curves:
            for layer in getattr(action, "layers", ()):
                for strip in layer.strips:
                    if hasattr(strip, "channelbag"):
                        slot = getattr(animation, "action_slot", None)
                        bag = strip.channelbag(slot, ensure=False) if slot else None
                        if bag:
                            curves.extend(bag.fcurves)
        for curve in curves:
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"


def configure_camera(scene, focus_objects, camera_loc, target, ortho=0.34):
    bpy.ops.object.camera_add(location=camera_loc)
    cam=bpy.context.object; cam.name="Preview_Camera"; cam.data.type="ORTHO"; cam.data.ortho_scale=ortho
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.camera=cam; cam.data.lens=50
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type=="VIEW_3D":
            area.spaces.active.region_3d.view_perspective="CAMERA"


def setup_lighting(scene):
    bpy.ops.object.light_add(type="AREA",location=(0.2,-0.35,0.35)); key=bpy.context.object; key.name="Key_Softbox"; key.data.energy=28; key.data.shape="DISK"; key.data.size=.4
    key.rotation_euler=(Vector((0,0,0))-key.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.light_add(type="AREA",location=(-.28,.18,.18)); fill=bpy.context.object; fill.name="Fill_Softbox"; fill.data.energy=15; fill.data.size=.32
    fill.rotation_euler=(Vector((0,0,0))-fill.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.light_add(type="AREA",location=(0,.25,.3)); rim=bpy.context.object; rim.name="Rim_Softbox"; rim.data.energy=18; rim.data.size=.22
    rim.rotation_euler=(Vector((0,0,0))-rim.location).to_track_quat("-Z","Y").to_euler()


def render_preview(scene, output, cam_loc, target, scale):
    configure_camera(scene,[],cam_loc,target,scale); setup_lighting(scene)
    scene.render.filepath=str(output)
    scene.render.image_settings.file_format="PNG"
    # Keep the frame clean and deterministic; no external fonts or downloaded textures.
    bpy.ops.render.render(write_still=True)


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument("--output-root",type=Path,default=DEFAULT_OUT)
    parser.add_argument("--render",action="store_true"); args=parser.parse_args(argv)
    out=args.output_root.resolve(); out.mkdir(parents=True,exist_ok=True)
    definitions=[("bearing_6204",bearing_stage,(-.09,-.12,.13),(0,0,0),.12),
                 ("spur_gears_20_40",gear_stage,(-.04,-.08,.10),(0,0,0),.16),
                 ("bldc_motor_concept",motor_stage,(-.13,-.22,.21),(0,0,0),.24),
                 ("pcb_layered",pcb_stage,(-.20,-.25,.24),(0,0,0),.24),
                 ("shaft_coupling_spring_fastener_battery",mechanism_stage,(-.13,-.18,.25),(.02,.07,0),.45),
                 ("beam_bracket_heatsink_fan",structure_fluid_stage,(-.16,-.20,.22),(.08,0,.02),.56)]
    reports=[]
    for name,build,cam,target,scale in definitions:
        meta={"scene":name,"schema":"education-asset-metadata/v1","units":"m",
              "license":"CC0-1.0","youtube_commercial_use":"allowed",
              "redistribution":"allowed with CC0 dedication","generator":"assets/education/generate_assets.py"}
        reset_scene("EDU | "+name)
        targets,notes=build(); add_stage(bpy.context.scene,targets); meta.update(notes)
        model=out/(name+".blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(model),compress=True)
        digest=hashlib.sha256(model.read_bytes()).hexdigest()
        if args.render:
            render_preview(bpy.context.scene,out/(name+".png"),cam,target,scale)
        meta["blend_file"]=model.name
        meta["source_sha256"]=digest
        meta["objects"]=[o.name for o in bpy.context.scene.objects if o.type in {"MESH","CURVE","EMPTY"}]
        meta["animation_ready"]=any(obj.animation_data and obj.animation_data.action
                                     for obj in bpy.context.scene.objects)
        (out/(name+".json")).write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        reports.append(meta)
    (out/"generation_report.json").write_text(json.dumps(reports,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


if __name__=="__main__": main()
