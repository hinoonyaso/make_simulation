"""Blender spatial view, same scene geometry and sampled poses as the numerical trace."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'output/trace.json').read_text());OUT=ROOT/'output/blender';OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1200;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=30
s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world.color=(.93,.947,.969);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG'
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
white=mat('Shell',(.83,.88,.93));blue=mat('Lidar',(.03,.44,.68));dark=mat('Wheels',(.07,.1,.15));wallmat=mat('Walls',(.65,.72,.80));floor=mat('Floor',(.91,.94,.97));raymat=mat('Rays',(.1,.68,.83));hitmat=mat('Hits',(.98,.42,.06))
def box(name,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);return o
box('Floor',(.5,.5,-.1),(10,8,.15),floor)
walls=[]
for a,b in D['walls']:
 o=box('Wall',((a[0]+b[0])/2,(a[1]+b[1])/2,.35),(math.dist(a,b),.09,.7),wallmat);o.rotation_euler.z=math.atan2(b[1]-a[1],b[0]-a[0]);walls.append(o)
root=bpy.data.objects.new('AMR pose',None);bpy.context.collection.objects.link(root)
def child(o):o.parent=root;return o
child(box('AMR chassis',(0,0,.22),(.68,.50,.3),white));child(box('Front bumper',(.34,0,.22),(.05,.44,.12),blue))
for y in [-.28,.28]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.16,depth=.09,location=(0,y,.17));o=bpy.context.object;o.rotation_euler.x=math.pi/2;o.data.materials.append(dark);child(o)
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.13,depth=.13,location=(0,0,.44));o=bpy.context.object;o.data.materials.append(blue);child(o)
bpy.ops.object.camera_add(location=(9,-12,13));cam=bpy.context.object;cam.rotation_euler=(Vector((.3,.5,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=14;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=(0,-3,8));bpy.context.object.data.energy=1200
rays=[];hits=[]
for j in range(0,240,5):
 curve=bpy.data.curves.new('Ray','CURVE');curve.dimensions='3D';curve.bevel_depth=.009;sp=curve.splines.new('POLY');sp.points.add(1)
 o=bpy.data.objects.new(f'Ray {j}',curve);bpy.context.collection.objects.link(o);o.data.materials.append(raymat);rays.append(o)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.05);o=bpy.context.object;o.data.materials.append(hitmat);hits.append(o)
def apply(k,reveal=48,dense=False):
 p=D['visual_truth' if dense else 'truth'][k];root.location=(p[0],p[1],0);root.rotation_euler.z=p[2]
 for n,(ray,hit,j) in enumerate(zip(rays,hits,range(0,240,5))):
  q=D['visual_scans' if dense else 'scans'][k][j];x=p[0]+math.cos(p[2])*q[0]-math.sin(p[2])*q[1];y=p[1]+math.sin(p[2])*q[0]+math.cos(p[2])*q[1]
  ray.data.splines[0].points[0].co=(p[0],p[1],.44,1);ray.data.splines[0].points[1].co=(x,y,.44,1);hit.location=(x,y,.44)
  ray.hide_render=hit.hide_render=n>=reveal
apply(0,0)
for w in walls:w.hide_render=True
cam.data.ortho_scale=5.5
s.render.filepath=str(OUT/'intro.png');bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=14
for w in walls:w.hide_render=False
for mode in ['scan','motion']:
 folder=OUT/mode;folder.mkdir(exist_ok=True)
 for f in range(96):
  s.frame_set(f+1)
  k=0 if mode=='scan' else f;apply(k,min(48,f+1) if mode=='scan' else 48,dense=mode=='motion')
  for ray,hit in zip(rays,hits):
   for point in ray.data.splines[0].points:point.keyframe_insert(data_path='co',frame=f+1)
   ray.keyframe_insert(data_path='hide_render',frame=f+1);hit.keyframe_insert(data_path='hide_render',frame=f+1);hit.keyframe_insert(data_path='location',frame=f+1)
  root.keyframe_insert(data_path='location',frame=f+1);root.keyframe_insert(data_path='rotation_euler',frame=f+1)
  s.render.filepath=str(folder/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 s.frame_start=1;s.frame_end=96;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{mode}.blend'))
(OUT/'validation.json').write_text(json.dumps({'frames_per_clip':96,'sample_indices':list(range(16)),'source':'trace.json','sensor':'240 rays, every fifth ray displayed','pose_units':'meters/radians'}))
