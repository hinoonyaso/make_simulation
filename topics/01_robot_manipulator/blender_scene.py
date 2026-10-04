"""Procedural 2R robot, keyframed .blend and deduplicated Workbench renders.

blender --background --factory-startup --python blender_scene.py -- --preview
blender --background --factory-startup --python blender_scene.py -- --render
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from blender_motion import FPS, FRAME_COUNT, RECORDS, fk, pose, signature

OUT=ROOT/'output/blender'
FRAMES=OUT/'frames'
M={}
GROUPS={}


def color(hex):
    rgb=[int(hex[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1,)


def material(name,hex):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=color(hex)
    M[name]=mat
    return mat


def finish(obj,name,mat,parent=None,group=None):
    obj.name=name
    obj.data.materials.append(M[mat])
    if parent: obj.parent=parent
    if group: GROUPS.setdefault(group,[]).append(obj)
    return obj


def box(name,loc,size,mat,parent=None,group=None,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=finish(bpy.context.object,name,mat,parent,group)
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('Machined edges','BEVEL'); mod.width=bevel; mod.segments=3
        obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    return obj


def cylinder(name,loc,radius,depth,mat,parent=None,group=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=loc)
    obj=finish(bpy.context.object,name,mat,parent,group)
    mod=obj.modifiers.new('Edge chamfer','BEVEL');mod.width=.012;mod.segments=2
    obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    return obj


def tube(name,points,radius,mat,group=None):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1
    curve.bevel_depth=radius;curve.bevel_resolution=2
    poly=curve.splines.new('POLY');poly.points.add(len(points)-1)
    for p,co in zip(poly.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj)
    return finish(obj,name,mat,group=group)


def update_tube(obj,points):
    for p,co in zip(obj.data.splines[0].points,points):p.co=(*co,1)


def arrow(name,start,end,mat,group=None):
    shaft=tube(name+' shaft',[start,end],.018,mat,group)
    bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.058,radius2=0,depth=.15,location=end)
    head=finish(bpy.context.object,name+' arrowhead',mat,group=group)
    head.rotation_euler=(Vector(end)-Vector(start)).to_track_quat('Z','Y').to_euler()
    return shaft,head


def update_arrow(arrow_objects,start,end):
    shaft,head=arrow_objects
    update_tube(shaft,[start,end]);head.location=end
    if (Vector(end)-Vector(start)).length>1e-8:
        head.rotation_euler=(Vector(end)-Vector(start)).to_track_quat('Z','Y').to_euler()


def ring(name,center,r,mat,group=None,thick=.014):
    points=[(center[0]+r*math.cos(i*math.tau/96),center[1]+r*math.sin(i*math.tau/96),center[2]) for i in range(97)]
    return tube(name,points,thick,mat,group)


def text(name,body,loc,size,mat,group=None):
    curve=bpy.data.curves.new(name,'FONT');curve.body=body;curve.size=size
    curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=.0003
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.location=loc
    return finish(obj,name,mat,group=group)


def setup():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAME_COUNT
    scene.render.resolution_x=900;scene.render.resolution_y=680;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.compression=15
    scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.35
    scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
    scene.display.shading.curvature_ridge_factor=1.25;scene.display.shading.curvature_valley_factor=.8
    scene.display.shading.show_specular_highlight=True
    scene.display.shading.background_type='WORLD';scene.world.color=color('#F7F9FC')[:3]
    scene.display.render_aa='16'
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    for name,hex in {'body':'#805FC4','metal':'#BAC6D4','dark':'#26364A','white':'#F4F7FB',
                     'target':'#EF981F','x':'#D95358','y':'#299665','z':'#2979D9',
                     'grid':'#D9E1E9','path':'#1D9273','ghost':'#BAC4D1','pale':'#DEEBE4'}.items():material(name,hex)
    bpy.ops.object.camera_add(location=(2.7,-4.6,7))
    cam=bpy.context.object;cam.name='Teaching camera';cam.data.type='ORTHO';cam.data.lens=50
    scene.camera=cam
    for name,loc,power,size in [('Key softbox',(2,-3,7),1000,5),('Fill softbox',(-4,2,5),700,4)]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=size
        light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    return scene,cam


def build(scene,cam):
    # Planar grid sits below the moving geometry; XY measures joint-axis distances.
    for i in range(-4,5):
        c=i*.5
        tube('Grid x '+str(i),[(-2,c,-.065),(2,c,-.065)],.003,'grid')
        tube('Grid y '+str(i),[(c,-2,-.065),(c,2,-.065)],.003,'grid')
    box('Pedestal mounting plate',(0,0,-.005),(.48,.48,.10),'dark')
    cylinder('Pedestal',(0,0,.075),.19,.13,'metal')
    for x in [-.17,.17]:
        for y in [-.17,.17]:cylinder('Mounting screw',(x,y,.051),.025,.008,'white')
    shoulder=bpy.data.objects.new('Joint_1_theta1',None);bpy.context.collection.objects.link(shoulder)
    elbow=bpy.data.objects.new('Joint_2_theta2',None);bpy.context.collection.objects.link(elbow)
    elbow.parent=shoulder;elbow.location=(1,0,0)
    box('Link 1',(0.5,0,.21),(1,.16,.14),'body',shoulder)
    box('Link 1 metal inlay',(.5,0,.285),(.68,.075,.014),'metal',shoulder,bevel=.007)
    cylinder('Shoulder drive housing',(0,0,.20),.14,.19,'dark',shoulder)
    cylinder('Shoulder top cap',(0,0,.30),.115,.03,'metal',shoulder)
    cylinder('Shoulder encoder',(0,0,.323),.047,.015,'body',shoulder)
    box('Link 2',(.4,0,.36),(.8,.135,.12),'body',elbow)
    box('Link 2 metal inlay',(.4,0,.425),(.5,.06,.014),'metal',elbow,bevel=.007)
    cylinder('Elbow motor',(0,0,.285),.125,.23,'dark',elbow)
    cylinder('Elbow cap',(0,0,.413),.10,.025,'metal',elbow)
    cylinder('Elbow encoder',(0,0,.433),.043,.016,'body',elbow)
    for parent,z in [(shoulder,.322),(elbow,.439)]:
        for i in range(4):
            angle=i*math.pi/2
            cylinder('Cap screw',(.08*math.cos(angle),.08*math.sin(angle),z),.009,.008,'dark',parent)
    tip=bpy.data.objects.new('TCP_analytic_position',None);bpy.context.collection.objects.link(tip)
    tip.parent=elbow;tip.location=(.8,0,.43)
    cylinder('Tool flange',(.8,0,.36),.093,.14,'metal',elbow)
    cylinder('TCP marker',(.8,0,.442),.055,.018,'target',elbow)
    # Small open gripper sits behind the clearly defined orange TCP centre.
    for side in [-1,1]:
        box('Gripper finger',(.81,side*.095,.30),(.16,.033,.10),'dark',elbow,bevel=.009)
    arrow('X axis',(0,0,-.035),(1.98,0,-.035),'x')
    arrow('Y axis',(0,0,-.03),(0,1.98,-.03),'y')
    arrow('Z axis',(-.31,-.31,-.03),(-.31,-.31,.70),'z',group='zaxis')
    xlab=text('X label','X [m]',(2.04,-.12,.035),.125,'x')
    ylab=text('Y label','Y [m]',(-.10,2.06,.035),.125,'y')
    zlab=text('Z label','Z',(-.31,-.31,.85),.12,'z','zaxis')
    labels=[xlab,ylab,zlab]
    l1=text('L1 label','L1 = 1.0 m',(.5,-.20,.42),.105,'dark','lengths')
    l2=text('L2 label','L2 = 0.8 m',(1,1,.5),.105,'dark','lengths')
    labels.extend([l1,l2])
    target=ring('Goal ring',(0,0,.48),.12,'target','target',.018)
    tx=tube('Goal cross X',[(-.17,0,.48),(.17,0,.48)],.009,'target','target')
    ty=tube('Goal cross Y',[(0,-.17,.48),(0,.17,.48)],.009,'target','target')
    label_target=text('Goal label','TARGET',(0,0,.66),.115,'target','target_label');labels.append(label_target)
    label_noik=text('Unreachable label','NO IK',(1.7,1.29,.61),.115,'target','noik_label');labels.append(label_noik)
    projections=[tube('Projection '+str(i),[(0,0,.05),(1,1,.05)],.009,'ghost','projections') for i in range(4)]
    triangle=tube('Cosine law triangle',[(0,0,.465),(1,0,.465),(1,1,.465),(0,0,.465)],.012,'path','triangle')
    arcs=[tube('Angle arc '+str(i),[(0,0,.46)]*33,.011,'target','angles') for i in range(2)]
    theta1=text('Theta1','θ1',(0,0,.5),.11,'dark','angles')
    theta2=text('Theta2','θ2',(0,0,.5),.11,'dark','angles');labels.extend([theta1,theta2])
    ghost_a=math.pi/6;ghost_b=math.pi/3
    e=(math.cos(ghost_a),math.sin(ghost_a),.52);p=(*fk(ghost_a,ghost_b),.52)
    tube('Pose A wireframe',[(0,0,.52),e,p],.025,'ghost','ghost')
    ring('Pose A elbow',e,.10,'ghost','ghost')
    ring('Outer reach',(0,0,.02),1.8,'path','outer',.018)
    ring('Inner reach',(0,0,.51),.2,'x','inner',.013)
    for i in range(2,9):
        ring('Reachable annulus guide '+str(i),(0,0,-.035),i*.2,'pale','workspace',.006)
    path=tube('TCP joint interpolation trace',[(0,0,.455)]*121,.014,'path','trajectory')
    straight=tube('Cartesian straight reference',[(0,0,.44),(1,1,.44)],.006,'ghost','trajectory')
    velocity=arrow('Instantaneous velocity',(0,0,.5),(1,1,.5),'path','velocity')
    sing_up=arrow('Allowed upward velocity',(1.8,0,.5),(1.8,.6,.5),'path','singular')
    sing_down=arrow('Allowed downward velocity',(1.8,0,.5),(1.8,-.6,.5),'path','singular')
    tube('Unavailable radial velocity',[(1.45,0,.5),(2.02,0,.5)],.011,'x','singular')
    return locals()


def visibility(group,visible):
    for obj in GROUPS.get(group,[]):
        obj.hide_render=not visible
        obj.hide_viewport=not visible


def apply(state,o):
    ci,li,a,b=state['chapter'],state['line'],state['q1'],state['q2']
    o['shoulder'].rotation_euler.z=a;o['elbow'].rotation_euler.z=b
    top=ci in (1,2,3,6,9)
    centre=Vector((0,0,.10) if ci==6 else (.38,.54,.16))
    if ci==8:centre=Vector((0,.35,.16))
    cam=o['cam'];cam.location=centre+Vector((0,0,8) if top else (1.45,-3.7,7.6))
    cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=6.0 if ci==6 else 4.7
    for obj in o['labels']:obj.rotation_euler=cam.rotation_euler
    e=(math.cos(a),math.sin(a));p=fk(a,b)
    o['l1'].location=(e[0]*.5-.23*math.sin(a),e[1]*.5+.23*math.cos(a),.5)
    o['l2'].location=((e[0]+p[0])*.5+.46,(e[1]+p[1])*.5+.1,.56)
    visibility('zaxis',not top)
    visibility('lengths',ci==1 and li>=1)
    visible_target=ci in (0,4,5) or ci==3 and li==3 or ci==6 and li==3 or ci==11 and li==3
    visibility('target',visible_target)
    visibility('target_label',visible_target and ci!=6)
    visibility('noik_label',ci==6 and li==3)
    xy=(1.7,1.1) if ci==6 else ((1,.8) if ci==11 else fk(math.pi/6,math.pi/3))
    for obj in [o['target'],o['tx'],o['ty']]:obj.location=(xy[0],xy[1],0)
    o['label_target'].location=(xy[0],xy[1]+.19,.61)
    visibility('projections',ci==2 and li>=1)
    z=.05
    pairs=[[(0,0,z),(e[0],0,z)],[(e[0],0,z),(*e,z)],
           [(*e,z),(p[0],e[1],z)],[(p[0],e[1],z),(*p,z)]]
    for obj,pts in zip(o['projections'],pairs):update_tube(obj,pts)
    visibility('triangle',ci==4)
    update_tube(o['triangle'],[(0,0,.465),(*e,.465),(*p,.465),(0,0,.465)])
    visibility('angles',ci==1 and li>=2)
    update_tube(o['arcs'][0],[(.35*math.cos(a*i/32),.35*math.sin(a*i/32),.465) for i in range(33)])
    update_tube(o['arcs'][1],[(e[0]+.28*math.cos(a+b*i/32),e[1]+.28*math.sin(a+b*i/32),.475) for i in range(33)])
    o['theta1'].location=(.47,.07,.52);o['theta2'].location=(e[0]+.32,e[1]+.25,.53)
    visibility('ghost',ci==5 and li>=1)
    visibility('outer',ci==6);visibility('inner',ci==6 and li>=1);visibility('workspace',ci==6 and li>=2)
    visibility('trajectory',ci==7 and li>=2)
    pathpts=[]
    for i in range(121):
        u=i/120*state['progress'];qa=math.radians(-25+90*u);qb=math.radians(100-80*u)
        pathpts.append((*fk(qa,qb),.455))
    update_tube(o['path'],pathpts)
    update_tube(o['straight'],[(*fk(math.radians(-25),math.radians(100)),.44),(*fk(math.radians(65),math.radians(20)),.44)])
    visibility('velocity',ci==8 and li==3)
    vx=(-math.sin(a)-.8*math.sin(a+b))*.3-.8*math.sin(a+b)*.2
    vy=(math.cos(a)+.8*math.cos(a+b))*.3+.8*math.cos(a+b)*.2
    update_arrow(o['velocity'],(*p,.52),(p[0]+vx,p[1]+vy,.52))
    visibility('singular',ci==9 and li>=2)
    bpy.context.view_layer.update()


def keyframe(o,frame):
    for obj in [o['shoulder'],o['elbow'],o['cam']]+o['labels']+[o['target'],o['tx'],o['ty'],o['velocity'][1]]:
        obj.keyframe_insert(data_path='location',frame=frame)
        obj.keyframe_insert(data_path='rotation_euler',frame=frame)
    o['cam'].data.keyframe_insert(data_path='ortho_scale',frame=frame)
    for group in GROUPS.values():
        for obj in group:
            obj.keyframe_insert(data_path='hide_render',frame=frame)
            obj.keyframe_insert(data_path='hide_viewport',frame=frame)
    for name in ['projections','arcs']:
        for obj in o[name]:
            for p in obj.data.splines[0].points:p.keyframe_insert(data_path='co',frame=frame)
    for obj in [o['triangle'],o['path'],o['straight'],o['velocity'][0]]:
        for p in obj.data.splines[0].points:p.keyframe_insert(data_path='co',frame=frame)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--render',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(parents=True,exist_ok=True);FRAMES.mkdir(exist_ok=True)
    scene,cam=setup();o=build(scene,cam)
    if args.preview:
        for ci in range(12):
            if ci==10:continue
            frame=round((RECORDS[ci*4+3]['end']-1)*FPS)+1
            apply(pose(frame),o)
            scene.render.filepath=str(OUT/f'preview_{ci:02d}.png')
            bpy.ops.render.render(write_still=True)
        return
    cache={};timeline=[];errors=[]
    started=time.time()
    for frame in range(1,FRAME_COUNT+1):
        state=pose(frame);sig=signature(state)
        # Pipeline is composited from the original Manim video without a 3D inset.
        if state['chapter']==10:
            timeline.append(None);continue
        if sig not in cache:
            scene.frame_set(frame)
            apply(state,o)
            analytic=fk(state['q1'],state['q2']);actual=o['tip'].matrix_world.translation
            err=math.hypot(actual.x-analytic[0],actual.y-analytic[1]);errors.append(err)
            if err>2e-6:raise AssertionError(f'TCP mismatch: {err}')
            keyframe(o,frame)
            idx=len(cache);cache[sig]=idx
            if args.render:
                path=FRAMES/f'{idx:05d}.png'
                scene.render.filepath=str(path)
                bpy.ops.render.render(write_still=True)
            if idx%100==0:print(f'PROGRESS {frame}/{FRAME_COUNT}; unique={idx}; seconds={time.time()-started:.1f}',flush=True)
        else:
            # Hold poses up to the final repeated frame so interpolation cannot drift.
            next_state=pose(frame+1) if frame<FRAME_COUNT else None
            if next_state is None or signature(next_state)!=sig:keyframe(o,frame)
        timeline.append(cache[sig])
    # Explicit linear interpolation for sampled motion; constant for visibility.
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='CONSTANT' if 'hide_' in curve.data_path else 'LINEAR'
    for ci,ch in enumerate(json.loads((ROOT/'storyboard.json').read_text())['chapters']):
        marker=scene.timeline_markers.new(ch['id'],frame=round(RECORDS[ci*4]['start']*FPS)+1)
    (OUT/'frame_map.json').write_text(json.dumps(timeline))
    (OUT/'geometry_validation.json').write_text(json.dumps({'max_tcp_xy_error_m':max(errors),'unique_frames':len(cache),'total_frames':FRAME_COUNT,'blender':bpy.app.version_string},indent=2))
    scene.frame_set(1)
    scene.render.filepath='//renders/frame_'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.color_type='MATERIAL'
                area.spaces.active.overlay.show_overlays=False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'robot_manipulator_3d.blend'))
    print('COMPLETE',len(cache),'unique frames',time.time()-started,'seconds',flush=True)


if __name__=='__main__':main()
