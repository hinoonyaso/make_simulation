"""Actual Blender scene intersections -> depth/mask observations -> independent inverse.

--simulate exports observations and numerical trace, without video rendering.
--render replays the trace through the real calibrated camera and observer camera.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from experiment import *
OUT=ROOT/'output';DATA=OUT/'data';RENDER=OUT/'blender'
MAT={}


def material(name,hex):
    rgb=[int(hex[i:i+2],16)/255 for i in (1,3,5)]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);MAT[name]=m


def finish(o,name,mat):
    o.name=name;o.data.materials.append(MAT[mat]);return o


def box(name,loc,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=finish(bpy.context.object,name,mat)
    o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o


def sphere(name,loc,r,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=r,location=loc)
    o=finish(bpy.context.object,name,mat)
    for p in o.data.polygons:p.use_smooth=True
    return o


def tube(name,pts,mat,r=.007):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
    sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return finish(o,name,mat)


def update(o,pts):
    for p,v in zip(o.data.splines[0].points,pts):p.co=(*v,1)


def setup():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for n,c in [('bg','#F7F9FC'),('dark','#202D43'),('grid','#DDE5EF'),('orange','#ED941D'),('green','#198F70'),('red','#D34F55'),('blue','#2676D5'),('gray','#B7C6D8')]:material(n,c)
    s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.fps=FPS
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.view_settings.view_transform='Standard';s.view_settings.look='None'
    sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
    sh.background_type='WORLD';s.world.color=MAT['bg'].diffuse_color[:3]
    physical=[]
    target=sphere('Target_surface',to_world(center('common',0)),.28,'orange');physical.append(target)
    physical.append(box('Floor',(0,2,-.62),(5,6,.04),'gray'))
    physical.append(box('Background',(0,4.4,0),(5,.04,3),'bg'))
    physical.append(box('Blue_reference',(-.85,3.35,-.34),(.35,.35,.5),'blue'))
    physical.append(box('Green_reference',(.87,3.6,-.39),(.28,.28,.4),'green'))
    bpy.ops.object.camera_add(location=(0,0,0),rotation=(math.pi/2,0,0))
    sensor=bpy.context.object;sensor.name='Calibrated_sensor';sensor.data.type='PERSP'
    sensor.data.lens=50;sensor.data.sensor_width=W*50/FX;sensor.data.sensor_fit='HORIZONTAL';sensor.data.clip_start=.01;sensor.data.clip_end=10
    sensor['fx']=FX;sensor['fy']=FY;sensor['cx']=CX;sensor['cy']=CY
    bpy.ops.object.camera_add(location=(4.3,-3.8,2.7));observer=bpy.context.object;observer.name='Observer_view'
    observer.rotation_euler=(Vector((0,1.4,-.12))-observer.location).to_track_quat('-Z','Y').to_euler()
    observer.data.type='ORTHO';observer.data.ortho_scale=4.7
    for pos,power in [((2,-2,5),1000),((-3,2,4),600)]:
        bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=5
    s.camera=sensor;s.render.resolution_x=W;s.render.resolution_y=H
    return s,physical,target,sensor,observer


def bvh_scene(physical):
    verts=[];polys=[];ids=[]
    for oi,o in enumerate(physical):
        offset=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices)
        polys.extend(tuple(offset+i for i in p.vertices) for p in o.data.polygons)
        ids.extend([oi]*len(o.data.polygons))
    return BVHTree.FromPolygons(verts,polys),ids


def observe(scene,physical,target,sensor,kind,j,directions):
    target.location=to_world(center(kind,j));bpy.context.view_layer.update()
    tree,ids=bvh_scene(physical)
    depth=np.zeros((H,W),dtype=np.float32);mask=np.zeros((H,W),dtype=np.uint8)
    for index,direction in enumerate(directions):
        loc,normal,face,dist=tree.ray_cast(Vector((0,0,0)),direction,10)
        if loc is not None:
            v,u=divmod(index,W);depth[v,u]=loc.y;mask[v,u]=ids[face]+1
    vv,uu=np.where(mask==1)
    assert len(uu)>10,'Target must be visible'
    u=int(round((int(uu.min())+int(uu.max()))/2));v=int(round((int(vv.min())+int(vv.max()))/2))
    assert mask[v,u]==1
    loc,_,_,_=tree.ray_cast(Vector((0,0,0)),directions[v*W+u],10)
    truth=np.array(from_world(loc),dtype=float)
    ndc=world_to_camera_view(scene,sensor,loc)
    projected=np.array([ndc.x*W-.5,(1-ndc.y)*H-.5])
    assert np.max(np.abs(projected-[u,v]))<2e-4,(projected,u,v)
    return depth,mask,dict(kind=kind,sample=j,center=center(kind,j),uv=[u,v],true_surface=truth.tolist(),projection_error_px=float(np.max(np.abs(projected-[u,v]))))


def simulate():
    for p in [OUT,DATA,RENDER]:p.mkdir(parents=True,exist_ok=True)
    scene,physical,target,sensor,observer=setup()
    directions=[Vector(((u-CX)/FX,1,-(v-CY)/FY)).normalized() for v in range(H) for u in range(W)]
    observations=[];started=time.time()
    for kind in ['common','depth']:
        for j in range(SAMPLES):
            gid=len(observations);file=DATA/f'observation_{gid:04}.npz';meta=DATA/f'observation_{gid:04}.json'
            depth,mask,ob=observe(scene,physical,target,sensor,kind,j,directions)
            np.savez_compressed(file,depth=depth,mask=mask);meta.write_text(json.dumps(ob))
            ob['id']=gid;observations.append(ob)
            if j%30==0:print('OBSERVATION',kind,j,'elapsed',round(time.time()-started,1),flush=True)
    states=[];phase_states=[];seen_views={};depth_files={};metrics={}
    for ci,name in enumerate(PHASES):
        indices=[SAMPLES-1] if ci==7 else list(range(SAMPLES))
        phase=[];errs=[]
        for j in indices:
            gid=(SAMPLES+j) if name=='depth' else j
            ob=observations[gid];data=np.load(DATA/f'observation_{gid:04}.npz');zmap=data['depth'].copy();u,v=ob['uv']
            if name=='noise':
                rng=np.random.default_rng(SEED+j)
                noise=rng.normal(0,SIGMA_Z,zmap.shape)
                zmap=np.where(zmap>0,np.maximum(.01,zmap+noise),0).astype(np.float32)
            depth_id=f'noise_{j:04}' if name=='noise' else f'clean_{gid:04}'
            if depth_id not in depth_files:
                np.save(DATA/f'{depth_id}.npy',zmap);depth_files[depth_id]=True
            z=float(zmap[v,u]);fx=FX*.8 if name=='bad_k' else FX
            estimate=reconstruct(u,v,z,fx);truth=np.array(ob['true_surface'])
            err=estimate-truth;error_mm=float(np.linalg.norm(err)*1000);errs.append(error_mm)
            key=(gid,*(round(float(x),7) for x in estimate))
            view_id=seen_views.setdefault(key,len(seen_views))
            st=dict(id=len(states),phase=ci,mode=name,sample=j,sim_time=j/FPS,geometry_id=gid,view_id=view_id,
                depth_id=depth_id,center=ob['center'],uv=ob['uv'],z_true=float(truth[2]),z_observed=z,
                fx_used=fx,true_surface=truth.tolist(),estimated=estimate.tolist(),error_vector_m=err.tolist(),
                error_mm=error_mm,rmse_running_mm=float(np.sqrt(np.mean(np.square(errs)))))
            phase.append(st['id']);states.append(st)
        phase_states.append(phase);metrics[name]=dict(samples=len(errs),rmse_mm=float(np.sqrt(np.mean(np.square(errs)))),max_mm=max(errs))
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text());total=round(records[-1]['end']*FPS)
    video_map=[]
    for f in range(total):
        t=f/FPS;rec=next((r for r in records if r['start']<=t+1e-8<r['end']),records[-1]);ci=rec['chapter']
        start=next(r['start'] for r in records if r['chapter']==ci)
        j=min(SAMPLES-1,max(0,int((t-start-1)*FPS+1e-7)))
        ids=phase_states[ci];video_map.append(ids[min(j,len(ids)-1)])
    output=dict(sensor=dict(width=W,height=H,fx=FX,fy=FY,cx=CX,cy=CY,pixel_centers='integer indices',optical_axes='X right, Y down, Z forward'),
        noise_sigma_m=SIGMA_Z,seed=SEED,fps=FPS,states=states,phase_states=phase_states,video_map=video_map,
        observations=observations,metrics=metrics,unique_views=len(seen_views),frame_count=total)
    (OUT/'trace.json').write_text(json.dumps(output,indent=2))
    import csv
    with (OUT/'samples.csv').open('w',newline='') as fh:
        writer=csv.writer(fh);writer.writerow(['mode','sample','t_sim','u','v','Z_observed_m','fx_used','true_X','true_Y','true_Z','estimated_X','estimated_Y','estimated_Z','error_mm','running_RMSE_mm'])
        for st in states:writer.writerow([st['mode'],st['sample'],st['sim_time'],*st['uv'],st['z_observed'],st['fx_used'],*st['true_surface'],*st['estimated'],st['error_mm'],st['rmse_running_mm']])
    print('SIMULATION COMPLETE',json.dumps(metrics),flush=True)


def annotations(observer):
    before=set(bpy.data.objects)
    body=box('Camera_body',(0,-.22,0),(.37,.32,.27),'dark')
    sphere('Camera_origin',(0,0,0),.025,'blue')
    tube('Optical_Z_axis',[(0,0,0),to_world((0,0,.8))],'blue',.013)
    corners=[to_world((x*.75,y*.75,.75)) for x,y in [(-W/2/FX,-H/2/FY),(W/2/FX,-H/2/FY),(W/2/FX,H/2/FY),(-W/2/FX,H/2/FY)]]
    tube('Sensor_frustum',corners+[corners[0]],'blue',.007)
    for p in corners:tube('Frustum_edge',[(0,0,0),p],'gray',.005)
    gt=sphere('Ground_truth_surface',(0,0,0),.024,'green')
    estimate=bpy.data.objects.new('Reconstructed_point',None);bpy.context.collection.objects.link(estimate)
    for axis in range(3):
        pts=[]
        for i in range(33):
            a=i*2*math.pi/32;q=[0.,0.,0.];q[(axis+1)%3]=.045*math.cos(a);q[(axis+2)%3]=.045*math.sin(a);pts.append(q)
        ring=tube('Estimate_ring',pts,'red',.005);ring.parent=estimate
    ray=tube('Observed_ray',[(0,0,0),(0,2,0)],'orange',.008)
    error=tube('Position_error',[(0,0,0),(.001,0,0)],'red',.01)
    return dict(gt=gt,estimate=estimate,ray=ray,error=error,all=list(set(bpy.data.objects)-before))


def apply(target,ann,st):
    target.location=to_world(st['center']);ann['gt'].location=to_world(st['true_surface']);ann['estimate'].location=to_world(st['estimated'])
    update(ann['ray'],[(0,0,0),to_world(st['true_surface'])])
    update(ann['error'],[to_world(st['true_surface']),to_world(st['estimated'])])


def keyframe(target,ann,f):
    for o in [target,ann['gt'],ann['estimate']]:o.keyframe_insert(data_path='location',frame=f)
    for name in ['ray','error']:
        for p in ann[name].data.splines[0].points:p.keyframe_insert(data_path='co',frame=f)


def render():
    trace=json.loads((OUT/'trace.json').read_text());scene,physical,target,sensor,observer=setup();ann=annotations(observer)
    for p in [RENDER/'rgb',RENDER/'world']:p.mkdir(parents=True,exist_ok=True)
    scene.camera=sensor;scene.render.resolution_x=W;scene.render.resolution_y=H
    for o in ann['all']:o.hide_render=True
    for ob in trace['observations']:
        file=RENDER/'rgb'/f"{ob['id']:04}.png"
        target.location=to_world(ob['center']);bpy.context.view_layer.update()
        if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    for o in ann['all']:o.hide_render=False
    scene.camera=observer;scene.render.resolution_x=840;scene.render.resolution_y=540
    seen=set()
    for st in trace['states']:
        vid=st['view_id']
        if vid in seen:continue
        seen.add(vid);apply(target,ann,st);bpy.context.view_layer.update()
        file=RENDER/'world'/f'{vid:04}.png'
        if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    scene.frame_start=1;scene.frame_end=len(trace['video_map'])
    for f,sid in enumerate(trace['video_map'],1):
        previous=trace['video_map'][f-2] if f>1 else None
        nxt=trace['video_map'][f] if f<len(trace['video_map']) else None
        if sid!=previous or sid!=nxt:
            scene.frame_set(f);apply(target,ann,trace['states'][sid]);keyframe(target,ann,f)
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    for r in records:
        if r['line']==0:scene.timeline_markers.new(PHASES[r['chapter']],frame=round(r['start']*FPS)+1)
    scene.frame_set(1);apply(target,ann,trace['states'][trace['video_map'][0]])
    scene.render.filepath=str(RENDER/'direct/frame_')
    bpy.ops.wm.save_as_mainfile(filepath=str(RENDER/'camera_observation_experiment.blend'))
    print('RENDER COMPLETE',len(seen),'world states',flush=True)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--simulate',action='store_true');p.add_argument('--render',action='store_true');a=p.parse_args(args)
    if a.simulate:simulate()
    if a.render:render()
