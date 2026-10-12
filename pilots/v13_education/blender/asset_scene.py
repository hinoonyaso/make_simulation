"""Render a V9-manifest-driven Blender lesson from a verified AssetFactory asset."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy
from mathutils import Vector
from core.education.blender_asset_loader import load_education_asset
from core.education.blender_primitives import exploded_view


def args_after_separator():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True); parser.add_argument("--timeline",required=True)
    parser.add_argument("--output",required=True); parser.add_argument("--width",type=int,default=960)
    parser.add_argument("--height",type=int,default=540); parser.add_argument("--fps",type=int,default=30)
    parser.add_argument("--samples",type=int,default=16); parser.add_argument("--still-frame",type=int,default=0)
    values=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def _action_curves(obj):
    animation=obj.animation_data
    action=animation.action if animation else None
    if action is None: return []
    curves=list(getattr(action,"fcurves",()))
    if not curves:
        for layer in getattr(action,"layers",()):
            for strip in layer.strips:
                if hasattr(strip,"channelbag"):
                    slot=getattr(animation,"action_slot",None)
                    bag=strip.channelbag(slot,ensure=False) if slot else None
                    if bag: curves.extend(bag.fcurves)
    return curves


def _retime_object(obj,start,end):
    for curve in _action_curves(obj):
        points=curve.keyframe_points
        if len(points)<2: continue
        source_start=min(p.co.x for p in points); source_end=max(p.co.x for p in points)
        if source_end<=source_start: continue
        scale=(end-start)/(source_end-source_start)
        for point in points:
            point.co.x=start+(point.co.x-source_start)*scale
        curve.update()


def _phase(beats,timeline,*phase_ids):
    ids=set(phase_ids)
    beat=next((b for b in beats if b.get("phase_id") in ids),None)
    return next((p for p in timeline["phases"] if beat and p["phase_id"]==beat["phase_id"]),None)


def _explosion_offsets(asset_id,objects):
    names={obj.name for obj in objects}; offsets={}
    if asset_id=="edu.bearing_6204.v1":
        candidates=["Outer_Ring","Inner_Ring","Cage_Assembly"]+[f"Ball_{i:02d}" for i in range(1,9)]
        for i,name in enumerate(candidates):
            if name in names: offsets[name]=(0,0,(1 if i%2 else -1)*(.014 if "Ball_" not in name else .008))
    elif asset_id=="edu.bldc_motor_concept.v1":
        for name,delta in (("Stator_Assembly",(-.055,0,0)),("Rotor_Assembly",(.055,0,0))):
            if name in names: offsets[name]=delta
    elif asset_id=="edu.pcb_layered.v1":
        for i in range(1,5):
            name=f"Copper_Layer_{i}"
            if name in names: offsets[name]=(0,0,(i-2.5)*.012)
    else:
        roots=[obj for obj in objects if obj.parent is None and obj.type=="MESH"]
        for i,obj in enumerate(roots): offsets[obj.name]=(0,0,(i-(len(roots)-1)/2)*.008)
    return offsets


def _apply_manifest_motion(asset_id,manifest,timeline,objects):
    beats=manifest["beats"]; phases=timeline["phases"]
    motion_beats=[b for b in beats if b.get("blueprint") in {"coordinate_transform","mechanism_motion"}
                  or b.get("animation",{}).get("rotate") is True]
    if asset_id=="edu.pcb_layered.v1":
        motion_beats=[b for b in beats if b.get("blueprint")=="layered_structure" or
                      b.get("animation",{}).get("separate_layers") is True]
    if motion_beats:
        beat=motion_beats[0]
        phase=next(p for p in phases if p["phase_id"]==beat["phase_id"])
        start=phase["presentation_start_frame"]
        end=max(start+1,phase["presentation_end_frame"]-1)
        for obj in objects:
            if obj.animation_data and obj.animation_data.action:
                _retime_object(obj,start,end)

    offsets=_explosion_offsets(asset_id,objects)
    base={obj.name:obj.delta_location.copy() for obj in objects if obj.name in offsets}
    exploded=_phase(beats,timeline,"exploded")
    if exploded is None:
        beat=next((b for b in beats if b.get("blueprint")=="exploded_assembly"),None)
        exploded=next((p for p in phases if beat and p["phase_id"]==beat["phase_id"]),None)
    reassemble=_phase(beats,timeline,"parts_reassemble")
    enabled=any(b.get("blueprint")=="exploded_assembly" and
                b.get("animation",{}).get("explode",True) for b in beats)
    separate=next((b for b in beats if b.get("animation",{}).get("separate_layers") is True),None)
    separate_phase=(next((p for p in phases if p["phase_id"]==separate["phase_id"]),None)
                    if separate else None)
    if separate_phase and offsets:
        start=separate_phase["presentation_start_frame"]
        end=max(start+2,separate_phase["presentation_end_frame"]-1)
        split=start+max(1,int((end-start)*.48))
        exploded_view(objects,offsets,base,start,split,explode=True)
        exploded_view(objects,offsets,base,split,end,explode=False)
        enabled=True
    if enabled and offsets and exploded:
        duration=exploded["presentation_end_frame"]-exploded["presentation_start_frame"]
        explode_start=exploded["presentation_start_frame"]
        explode_end=max(explode_start+1,explode_start+int(duration*.48))
        exploded_view(objects,offsets,base,explode_start,explode_end,explode=True)
        if reassemble:
            start=reassemble["presentation_start_frame"]
            end=max(start+1,reassemble["presentation_end_frame"]-1)
            exploded_view(objects,offsets,base,start,end,explode=False)
        else:
            exploded_view(objects,offsets,base,explode_end,max(explode_end+1,exploded["presentation_end_frame"]-1),explode=False)
    return {"motion_phase_ids":[b["phase_id"] for b in motion_beats],
            "exploded_view":bool(offsets and (exploded or separate_phase)),
            "exploded_object_names":sorted(offsets)}


def _setup_camera(scene,objects):
    points=[]
    for obj in objects:
        if obj.type=="MESH": points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points: raise ValueError("asset has no mesh bounds for camera framing")
    minimum=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    maximum=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center=(minimum+maximum)*.5; extent=max(maximum-minimum)
    extent=max(extent,.01)
    bpy.ops.object.camera_add(location=center+Vector((extent*1.45,-extent*1.8,extent*3.2)))
    camera=bpy.context.object; camera.name="Education_Asset_Camera"; camera.data.type="ORTHO"
    camera.data.ortho_scale=extent*2.15
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=camera
    bpy.ops.object.light_add(type="AREA",location=center+Vector((extent,-extent,extent*2)))
    key=bpy.context.object; key.name="Education_Key_Softbox"; key.data.energy=max(.75,extent*10); key.data.shape="DISK"; key.data.size=extent*1.8
    key.rotation_euler=(center-key.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.light_add(type="AREA",location=center+Vector((0,-extent*2,extent*.8)))
    fill=bpy.context.object; fill.data.energy=max(.45,extent*6); fill.data.size=extent*1.5
    fill.rotation_euler=(center-fill.location).to_track_quat("-Z","Y").to_euler()
    # A broad, low-power frontal fill keeps the bearing balls readable when
    # the camera settles overhead, without changing the approved camera path.
    bpy.ops.object.light_add(type="AREA",location=center+Vector((0,-extent*.35,extent*2.6)))
    ball_fill=bpy.context.object; ball_fill.name="Bearing_Ball_Readability_Fill"
    ball_fill.data.energy=max(.5,extent*4.5); ball_fill.data.shape="DISK"; ball_fill.data.size=extent*2.8
    ball_fill.rotation_euler=(center-ball_fill.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=extent*8,location=(center.x,center.y,minimum.z-extent*.08))
    floor=bpy.context.object; floor.name="Education_Stage"
    mat=bpy.data.materials.new("Education stage | deep slate"); mat.diffuse_color=(.012,.02,.034,1); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(.012,.02,.034,1)
    bsdf.inputs["Roughness"].default_value=.9
    floor.data.materials.append(mat)
    return {"bounds_min":list(minimum),"bounds_max":list(maximum),"center":list(center),"ortho_scale":camera.data.ortho_scale}


def _animate_camera_for_rolling(scene,center,extent):
    """Crane up, smoothly orbit a quarter turn, then settle into a top-down view."""
    camera=scene.camera
    if camera is None: return
    base=camera.location.copy(); horizontal=math.hypot(base.x-center.x,base.y-center.y)
    azimuth=math.atan2(base.y-center.y,base.x-center.x)
    final_azimuth=azimuth+math.pi/2
    high_z=extent*5.0
    high_scale=extent*2.6
    final_location=center+Vector((extent*.55*math.cos(final_azimuth),
                                  extent*.55*math.sin(final_azimuth),extent*4.0))
    poses=[
        (1,base,extent*2.15),
        (300,base,extent*2.15),
        # Separate the crane, quarter-turn orbit, and descent. The original
        # 30-frame orbit/descent compressed large camera moves into one second.
        (330,base,extent*2.15),
        (360,center+Vector((horizontal*math.cos(azimuth),horizontal*math.sin(azimuth),high_z)),high_scale),
    ]
    orbit_frames=45
    orbit_steps=6
    for step in range(1,orbit_steps+1):
        fraction=step/orbit_steps
        angle=azimuth+(final_azimuth-azimuth)*fraction
        location=center+Vector((horizontal*math.cos(angle),horizontal*math.sin(angle),high_z))
        poses.append((360+round(orbit_frames*fraction),location,high_scale))
    poses.extend(((435,final_location,extent*2.05),
                  (scene.frame_end,final_location,extent*2.05)))
    camera.rotation_mode="QUATERNION"
    for frame,location,ortho_scale in poses:
        camera.location=location
        camera.rotation_quaternion=(center-camera.location).to_track_quat("-Z","Y")
        camera.keyframe_insert(data_path="location",frame=frame)
        camera.keyframe_insert(data_path="rotation_quaternion",frame=frame)
        camera.data.ortho_scale=ortho_scale
        camera.data.keyframe_insert(data_path="ortho_scale",frame=frame)
    # Blender's default Bezier handles can overshoot during this large orbit
    # and crane move. Use smooth ease-in/out segments without changing poses.
    for owner in (camera,camera.data):
        if not owner.animation_data or not owner.animation_data.action: continue
        action=owner.animation_data.action
        fcurves=[]
        if hasattr(action,"fcurves"):
            fcurves.extend(action.fcurves)
        else:  # Blender 5.x layered Actions store curves in slot channel bags.
            for layer in action.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(owner.animation_data.action_slot)
                    if bag: fcurves.extend(bag.fcurves)
        for fcurve in fcurves:
            for point in fcurve.keyframe_points:
                point.interpolation="BEZIER"
                point.handle_left_type="AUTO_CLAMPED"
                point.handle_right_type="AUTO_CLAMPED"


def _soften_imported_materials(objects):
    """Reduce mirror-like highlights on compact teaching geometry per scene."""
    copied={}
    for obj in objects:
        if obj.type!="MESH": continue
        for slot in obj.material_slots:
            source=slot.material
            if source is None or not source.use_nodes: continue
            mat=copied.get(source.as_pointer())
            if mat is None:
                mat=source.copy(); copied[source.as_pointer()]=mat
                for node in mat.node_tree.nodes:
                    if node.type!="BSDF_PRINCIPLED": continue
                    metallic=node.inputs.get("Metallic")
                    roughness=node.inputs.get("Roughness")
                    if metallic: metallic.default_value=min(float(metallic.default_value),.48)
                    if roughness: roughness.default_value=max(float(roughness.default_value),.58)
                    specular=node.inputs.get("Specular IOR Level")
                    if specular: specular.default_value=min(float(specular.default_value),.32)
            slot.material=mat


def _add_ball_spin_markers(objects):
    """Make the source balls' recorded spin visible on otherwise uniform spheres."""
    balls=[obj for obj in objects if obj.type=="MESH" and obj.name.startswith("Ball_")]
    if not balls: return []
    marker_mat=bpy.data.materials.new("Rolling marker | teaching cyan")
    marker_mat.diffuse_color=(.035,.72,.9,1); marker_mat.use_nodes=True
    shader=marker_mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(.035,.72,.9,1)
    shader.inputs["Metallic"].default_value=.12
    shader.inputs["Roughness"].default_value=.4
    markers=[]
    for ball in balls:
        radius=max(ball.dimensions)*.5
        if radius<=0: continue
        curve=bpy.data.curves.new(f"{ball.name}_Spin_Marker_Curve","CURVE")
        curve.dimensions="3D"; curve.resolution_u=1; curve.bevel_depth=radius*.045; curve.bevel_resolution=2
        spline=curve.splines.new("POLY"); segments=48; spline.points.add(segments-1)
        stripe_radius=radius*1.015
        for index,point in enumerate(spline.points):
            angle=math.tau*index/segments
            point.co=(stripe_radius*math.cos(angle),0,stripe_radius*math.sin(angle),1)
        spline.use_cyclic_u=True
        marker=bpy.data.objects.new(f"{ball.name}_Spin_Marker",curve)
        bpy.context.scene.collection.objects.link(marker)
        marker.parent=ball
        marker.location=(0,0,0)
        curve.materials.append(marker_mat)
        markers.append(marker)
    return markers


def _emission_material(name,color):
    material=bpy.data.materials.new(name)
    material.diffuse_color=(*color,1)
    material.use_nodes=True
    nodes=material.node_tree.nodes; nodes.clear()
    emission=nodes.new("ShaderNodeEmission"); emission.inputs["Color"].default_value=(*color,1)
    emission.inputs["Strength"].default_value=10.0
    output=nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs["Emission"],output.inputs["Surface"])
    return material


def _add_bearing_part_legend(scene,camera,timeline):
    """Show a compact, camera-locked part key while the assembly is exploded."""
    phases={phase["phase_id"]:phase for phase in timeline["phases"]}
    phase=phases.get("exploded")
    if phase is None: return
    start=int(phase["presentation_start_frame"])
    end=int(phase["presentation_end_frame"])-1
    panel_mat=_emission_material("Bearing legend | navy",(.012,.025,.045))
    text_mat=_emission_material("Bearing legend | text",(.82,.90,.98))
    accent_mat=_emission_material("Bearing legend | active",(.08,.78,.94))

    bpy.ops.mesh.primitive_plane_add(size=2)
    panel=bpy.context.object; panel.name="Bearing_Part_Legend_Panel"
    panel.parent=camera; panel.location=(.0395,.008,-.14); panel.scale=(.0095,.0125,1)
    panel.data.materials.append(panel_mat)
    objects=[panel]

    font=None
    font_path=Path("C:/Windows/Fonts/malgun.ttf")
    if font_path.is_file(): font=bpy.data.fonts.load(str(font_path))
    title_data=bpy.data.curves.new("Bearing_Part_Legend_Title","FONT")
    title_data.body="부품"
    title_data.size=.0025
    title_data.materials.append(accent_mat)
    if font is not None: title_data.font=font
    title=bpy.data.objects.new("Bearing_Part_Legend_Title",title_data)
    scene.collection.objects.link(title); title.parent=camera
    title.location=(.0315,.0175,-.135); objects.append(title)

    names=("외륜","내륜","볼","케이지")
    row_y=(.0125,.008,.0035,-.001)
    for index,(name,y) in enumerate(zip(names,row_y),start=1):
        text_data=bpy.data.curves.new(f"Bearing_Part_Name_{index:02d}","FONT")
        text_data.body=f"{index:02d}  {name}"; text_data.size=.00255
        text_data.materials.append(text_mat)
        if font is not None: text_data.font=font
        label=bpy.data.objects.new(f"Bearing_Part_Name_{index:02d}",text_data)
        scene.collection.objects.link(label); label.parent=camera
        label.location=(.0315,y,-.135); objects.append(label)

    bpy.ops.mesh.primitive_plane_add(size=2)
    marker=bpy.context.object; marker.name="Bearing_Part_Legend_Active_Marker"
    marker.parent=camera; marker.scale=(.0007,.0012,1); marker.location=(.0295,row_y[0]+.001,-.132)
    marker.data.materials.append(accent_mat); objects.append(marker)
    for obj in objects:
        obj.hide_render=True; obj.keyframe_insert(data_path="hide_render",frame=1)
        obj.hide_render=False; obj.keyframe_insert(data_path="hide_render",frame=start)
        obj.hide_render=False; obj.keyframe_insert(data_path="hide_render",frame=end)
        obj.hide_render=True; obj.keyframe_insert(data_path="hide_render",frame=min(scene.frame_end,end+1))
    segment=max(1,(end-start)//len(row_y))
    for index,y in enumerate(row_y):
        frame=min(end,start+index*segment)
        marker.location.y=y+.001
        marker.keyframe_insert(data_path="location",frame=frame)
    return objects


def make_scene(manifest,timeline,output,width,height,fps,samples=16,still_frame=0):
    asset_id=manifest.get("asset_id")
    if not asset_id: raise ValueError("asset-backed Blender lesson requires manifest.asset_id")
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    engine_items=scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_items else "BLENDER_EEVEE"
    scene.render.resolution_x=width; scene.render.resolution_y=height; scene.render.resolution_percentage=100
    scene.render.fps=fps; scene.frame_start=1; scene.frame_end=timeline["total_frames"]
    scene.render.image_settings.media_type="VIDEO"; scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="HIGH"
    scene.render.filepath=str(output); scene.render.film_transparent=False
    scene.world.color=(.018,.026,.043); scene.view_settings.view_transform="AgX"
    scene.view_settings.look="AgX - Medium High Contrast"; scene.view_settings.exposure=-3.1
    if scene.world and scene.world.use_nodes:
        background=scene.world.node_tree.nodes.get("Background")
        if background:
            background.inputs["Color"].default_value=(.018,.026,.043,1)
            background.inputs["Strength"].default_value=.25
    asset=load_education_asset(asset_id,scene,animation_mode="PLAY")
    _soften_imported_materials(asset["objects"])
    _add_ball_spin_markers(asset["objects"])
    motion=_apply_manifest_motion(asset_id,manifest,timeline,asset["objects"])
    framing=_setup_camera(scene,asset["objects"])
    if asset_id=="edu.bearing_6204.v1":
        _animate_camera_for_rolling(scene,Vector(framing["center"]),
            max(framing["bounds_max"][i]-framing["bounds_min"][i] for i in range(3)))
        _add_bearing_part_legend(scene,scene.camera,timeline)
    scene.frame_set(max(1,min(scene.frame_end,still_frame or 1)))
    output=Path(output)
    scene.render.filepath=str(output)
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
    evidence={"asset_id":asset_id,"source":str(asset["path"]),"source_sha256":asset["sha256"],
              "license":asset["license"],"collection":asset["collection"],"animation":motion,
              "framing":framing,"blueprints":sorted({b.get("blueprint") for b in manifest["beats"] if b.get("blueprint")})}
    output.with_name("blender_asset_evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if still_frame:
        scene.render.image_settings.media_type="IMAGE"; scene.render.image_settings.file_format="PNG"
        scene.render.filepath=str(output.with_name(f"{output.stem}_frame_{still_frame:04d}.png"))
        bpy.ops.render.render(write_still=True)
    else: bpy.ops.render.render(animation=True)
    return evidence


def main():
    args=args_after_separator()
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    timeline=json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    make_scene(manifest,timeline,Path(args.output),args.width,args.height,args.fps,args.samples,args.still_frame)


if __name__=="__main__": main()
