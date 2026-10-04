"""Optical camera, virtual image plane, ray, depth plane and reconstructed point.
Run with Blender --background --factory-startup --python blender_scene.py -- --render.
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
from geometry import FPS,point,project,state
OUT=ROOT/'output/blender';FRAMES=OUT/'frames'
M={}


def world(p):
    x,y,z=p
    return Vector((x,z,-y))


def mat(name,color):
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);M[name]=m


def finish(o,name,color):
    o.name=name;o.data.materials.append(M[color]);return o


def tube(name,pts,color,r=.009):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts):p.co=(*v,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o)
    return finish(o,name,color)


def update(o,pts):
    for p,v in zip(o.data.splines[0].points,pts):p.co=(*v,1)


def sphere(name,p,color,r=.05):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r,location=p)
    return finish(bpy.context.object,name,color)


def box(name,p,scale,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    o=finish(bpy.context.object,name,color);o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Soft edges','BEVEL');b.width=.025;b.segments=3
    o.modifiers.new('Normals','WEIGHTED_NORMAL');return o


def label(name,body,p,color,size=.105):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.align_x='CENTER';c.align_y='CENTER'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location=p
    o.rotation_euler=bpy.context.scene.camera.rotation_euler
    return finish(o,name,color)


def arrow(name,end,color):
    end=world(end);tube(name,[world((0,0,0)),end],color,.012)
    bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.037,radius2=0,depth=.11,location=end)
    o=finish(bpy.context.object,name+' head',color)
    o.rotation_euler=end.to_track_quat('Z','Y').to_euler()


def setup(total):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for n,c in [('bg','#F7F9FC'),('dark','#202D43'),('grid','#DDE5EF'),('metal','#8797AA'),
                ('X','#D34F55'),('Y','#198F70'),('Z','#2676D5'),('ray','#ED941D'),('white','#FFFFFF')]:mat(n,c)
    s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.fps=30
    s.frame_start=1;s.frame_end=total
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.resolution_x=880;s.render.resolution_y=640;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
    s.view_settings.view_transform='Standard';s.view_settings.look='None'
    sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True
    sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True
    sh.background_type='WORLD';s.world.color=M['bg'].diffuse_color[:3]
    bpy.ops.object.camera_add(location=(4.5,-3.0,2.9));cam=bpy.context.object;cam.name='Teaching_view'
    cam.rotation_euler=(Vector((.08,1.10,-.06))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=3.9;s.camera=cam
    for pos,energy in [((2,-3,6),1000),((-3,2,4),700)]:
        bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=energy;bpy.context.object.data.size=5
    return s


def build():
    box('Camera housing',(0,-.23,0),(.44,.36,.32),'dark')
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.13,depth=.12,location=(0,-.055,0),rotation=(math.pi/2,0,0))
    finish(bpy.context.object,'Lens barrel','metal')
    sphere('Optical center',world((0,0,0)),'white',.035)
    for end,c in [((.8,0,0),'X'),((0,.7,0),'Y'),((0,0,2.85),'Z')]:
        arrow('Optical '+c,end,c);label('Axis '+c,c,world(end)+Vector((.04,.05,.03)),c,.145)
    label('Camera origin','C',(-.31,-.26,.17),'dark',.14)
    corners=[world((x,y,.75)) for x,y in [(-.4,-.3),(.4,-.3),(.4,.3),(-.4,.3),(-.4,-.3)]]
    tube('Virtual image frame',corners,'Z',.012)
    for c in corners[:4]:tube('Frustum edge',[(0,0,0),c],'grid',.005)
    for x in [-.2,0,.2]:tube('Image u grid',[world((x,-.3,.75)),world((x,.3,.75))],'grid',.004)
    for y in [-.15,0,.15]:tube('Image v grid',[world((-.4,y,.75)),world((.4,y,.75))],'grid',.004)
    sphere('Principal point',world((0,0,.75)),'Z',.024)
    sphere('Selected pixel',world(point(.75)),'ray',.039)
    label('Virtual image label','virtual image',world((-.10,-.45,.75)),'Z',.10)
    tube('Backprojected ray',[(0,0,0),world(point(2.72))],'ray',.012)
    target=sphere('Reconstructed_P',world(point(2)),'ray',.063)
    plabel=label('Point label','P',world(point(2))+Vector((.1,0,.15)),'ray',.15)
    depth=bpy.data.objects.new('Depth_plane_Z',None);bpy.context.collection.objects.link(depth)
    edges=[world((x,y,0)) for x,y in [(-.6,-.45),(.6,-.45),(.6,.45),(-.6,.45),(-.6,-.45)]]
    plane=tube('Depth plane boundary',edges,'Z',.008);plane.parent=depth
    for x in [-.3,0,.3]:
        o=tube('Depth plane grid',[world((x,-.45,0)),world((x,.45,0))],'grid',.003);o.parent=depth
    for y in [-.225,0,.225]:
        o=tube('Depth plane grid',[world((-.6,y,0)),world((.6,y,0))],'grid',.003);o.parent=depth
    dlabel=label('Depth plane label','Z plane',world((-.48,-.56,2)),'Z',.1)
    gx=tube('X component',[world((0,0,2)),world((.4,0,2))],'X',.01)
    gy=tube('Y component',[world((.4,0,2)),world(point(2))],'Y',.01)
    measure=tube('Optical depth dimension',[world((-.4,.5,0)),world((-.4,.5,2))],'Z',.009)
    zlabel=label('Z measure','Z',world((-.5,.65,1)),'Z',.14)
    rlabel=label('Range label','R = 2.049 m',world((.28,-.19,1.8)),'ray',.105)
    candidates=[sphere('Candidate_'+str(i),world(point(z)),'metal',.042) for i,z in enumerate([1.,1.6,2.5])]
    return dict(target=target,plabel=plabel,depth=depth,dlabel=dlabel,gx=gx,gy=gy,
                zlabel=zlabel,measure=measure,rlabel=rlabel,candidates=candidates)


def apply(o,st):
    z=st['z'];p=point(z)
    o['target'].location=world(p);o['plabel'].location=world(p)+Vector((.1,0,.15))
    o['depth'].location=(0,z,0);o['dlabel'].location=world((-.48,-.56,z))
    update(o['gx'],[world((0,0,z)),world((p[0],0,z))])
    update(o['gy'],[world((p[0],0,z)),world(p)])
    update(o['measure'],[world((-.4,.5,0)),world((-.4,.5,z))])
    o['zlabel'].location=world((-.5,.65,z/2))
    o['rlabel'].hide_render=not st['show_range'];o['rlabel'].hide_viewport=not st['show_range']
    for obj in o['candidates']:
        obj.hide_render=not st['show_candidates'];obj.hide_viewport=not st['show_candidates']


def keyframe(o,f):
    for k in ['target','plabel','depth','dlabel','zlabel']:o[k].keyframe_insert(data_path='location',frame=f)
    for k in ['gx','gy','measure']:
        for p in o[k].data.splines[0].points:p.keyframe_insert(data_path='co',frame=f)
    for obj in [o['rlabel'],*o['candidates']]:
        obj.keyframe_insert(data_path='hide_render',frame=f);obj.keyframe_insert(data_path='hide_viewport',frame=f)


def signature(st):return (round(st['z'],7),st['show_range'],st['show_candidates'])


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--render',action='store_true');a=p.parse_args(args)
    OUT.mkdir(parents=True,exist_ok=True);FRAMES.mkdir(exist_ok=True)
    recs=json.loads((ROOT/'assets/audio/manifest.json').read_text());total=round(recs[-1]['end']*FPS)
    s=setup(total);o=build()
    if a.preview:
        for z,range_mode,name in [(1,False,'near'),(2,False,'example'),(2,True,'range')]:
            apply(o,dict(z=z,show_range=range_mode,show_candidates=False));s.render.filepath=str(OUT/f'preview_{name}.png');bpy.ops.render.render(write_still=True)
        return
    seen={};mapping=[];max_error=0.;previous=None;started=time.time()
    for f in range(1,total+1):
        st=state(f,recs)
        sig=signature(st);s.frame_set(f);apply(o,st)
        nextsig=signature(state(f+1,recs)) if f<total else None
        if sig!=previous or sig!=nextsig:keyframe(o,f)
        previous=sig
        if not st['visible']:mapping.append(None);continue
        if sig not in seen:
            index=len(seen);seen[sig]=index
            file=FRAMES/f'{index:05}.png'
            if a.render:
                s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
        mapping.append(seen[sig])
        uv=project(point(st['z']));max_error=max(max_error,abs(uv[0]-440),abs(uv[1]-300))
        actual=o['target'].location;expected=world(point(st['z']))
        assert (actual-expected).length<1e-6
    (OUT/'frame_map.json').write_text(json.dumps(mapping))
    (OUT/'geometry_validation.json').write_text(json.dumps(dict(frame_count=total,unique_frames=len(seen),
        max_reprojection_error_px=max_error,example_xyz=point(2),example_range=math.sqrt(4.2),
        optical_to_blender='(X,Y,Z) -> (X,Z,-Y); proper rotation, determinant +1',seconds=time.time()-started),indent=2))
    for i,ch in enumerate(json.loads((ROOT/'storyboard.json').read_text())['chapters']):
        start=next(r['start'] for r in recs if r['chapter']==i)
        s.timeline_markers.new(ch['id'],frame=round(start*30)+1)
    s.frame_set(1);apply(o,state(1,recs));s.render.filepath=str(OUT/'direct_render/frame_')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pixel_depth_camera.blend'))
    print('COMPLETE',len(seen),'unique frames',flush=True)


if __name__=='__main__':main()
