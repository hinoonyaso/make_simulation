"""Spatial playback of validated traces, meters/radians. Ideal kinematics, no rigid-body physics."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());O=R/'output/blender';O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1080;s.render.resolution_y=648;s.render.resolution_percentage=100;s.render.fps=15;s.world.color=(.93,.947,.969);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
white=mat('Shell',(.83,.88,.93));blue=mat('Lidar',(.03,.44,.68));dark=mat('Wheels',(.07,.1,.15));gray=mat('Walls',(.58,.66,.75));floor=mat('Floor',(.91,.94,.97));cyan=mat('Rays',(.1,.68,.83));orange=mat('Person',(.8,.26,.23));green=mat('Path',(.07,.53,.36))
def cube(name,loc,scale,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);o.parent=parent;return o
def empty(name,parent=None):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=parent;return o
def curve(name,points,m,thickness=.015):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=thickness;sp=data.splines.new('POLY');sp.points.add(len(points)-1)
 for p,q in zip(sp.points,points):p.co=(*q,1)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
cube('Floor',(0,0,-.08),(9.2,6.2,.15),floor)
for x0,y0,x1,y1 in D['boxes']:cube('Static obstacle',((x0+x1)/2,(y0+y1)/2,.4),(x1-x0,y1-y0,.8),gray)
for a,b in [((-4.5,-3),(4.5,-3)),((4.5,-3),(4.5,3)),((4.5,3),(-4.5,3)),((-4.5,3),(-4.5,-3))]:
 curve('Boundary',[(*a,.03),(*b,.03)],gray,.025)
root=empty('AMR pose');cube('Chassis',(0,0,.18),(.38,.32,.20),white,root);cube('Front bumper',(.2,0,.18),(.04,.29,.09),blue,root)
wheels=[]
for name,y in [('Left wheel',.225),('Right wheel',-.225)]:
 pivot=empty(name,root);pivot.location=(0,y,.1);wheels.append(pivot)
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.1,depth=.045);o=bpy.context.object;o.name=name+' tire';o.parent=pivot;o.rotation_euler.x=math.pi/2;o.data.materials.append(dark)
 cube(name+' marker',(0,0,0),(.16,.05,.022),white,pivot)
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.075,depth=.07,location=(0,0,.315));o=bpy.context.object;o.name='LiDAR';o.parent=root;o.data.materials.append(blue)
person=empty('Person pose')
bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=.2,depth=.7,location=(0,0,.65));o=bpy.context.object;o.parent=person;o.data.materials.append(orange)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.16,location=(0,0,1.14));o=bpy.context.object;o.parent=person;o.data.materials.append(orange)
for y in [-.12,.12]:cube('Leg',(0,y,.18),(.12,.12,.36),dark,person)
curve('Goal ring',[(3+.27*math.cos(a),.27*math.sin(a),.025) for a in [i*2*math.pi/48 for i in range(49)]],green,.025)
curve('Goal heading',[(3,0,.025),(3.5,0,.025)],green,.025)
bpy.ops.object.camera_add(location=(5,-9,12));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=10.8;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=(0,-3,8));bpy.context.object.data.energy=1000
for mode in ['baseline','dynamic']:
 # Remove previous run animation channels before writing independent scene.
 for obj in [root,person,*wheels]:obj.animation_data_clear()
 for ob in list(bpy.data.objects):
  if ob.name.startswith('Plan '):bpy.data.objects.remove(ob,do_unlink=True)
 run=D[mode];paths=[]
 for i,p in enumerate(run['plans']):
  ob=curve(f'Plan {i}',[(x,y,.025) for x,y in p['path']],green,.022);paths.append(ob)
 folder=O/mode;folder.mkdir(exist_ok=True);mapping=[];n=math.ceil(run['metrics']['duration_s']*15)
 for f in range(n):
  t=min(f/15,run['rows'][-1]['time']);k=min(int(t/.1+1e-8),len(run['rows'])-1);row=run['rows'][k];alpha=(t-row['time'])/.1;p=[row['pose'][j]+alpha*(row['next_pose'][j]-row['pose'][j]) for j in range(3)]
  s.frame_set(f+1);root.location=(*p[:2],0);root.rotation_euler.z=p[2];root.keyframe_insert(data_path='location',frame=f+1);root.keyframe_insert(data_path='rotation_euler',frame=f+1)
  for j,wheel in enumerate(wheels):
   angle=row['wheel_angles'][j]-(1-alpha)*.1*row['wheel_rates'][j];wheel.rotation_euler.y=angle;wheel.keyframe_insert(data_path='rotation_euler',frame=f+1)
  if row['person'] is None:person.location=(0,0,-10)
  else:person.location=(*row['person'],0)
  person.keyframe_insert(data_path='location',frame=f+1)
  for i,ob in enumerate(paths):ob.hide_render=i!=row['path_id'];ob.keyframe_insert(data_path='hide_render',frame=f+1)
  mapping.append(dict(frame=f+1,sample=k,time=t,pose=p,wheel_angles=[w.rotation_euler.y for w in wheels],path_id=row['path_id']))
  s.render.filepath=str(folder/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 s.frame_start=1;s.frame_end=n;bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{mode}.blend'));(O/f'{mode}_frames.json').write_text(json.dumps(mapping))
 # Reopen saved scene, evaluate keyframed samples and verify playback identity.
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{mode}.blend'));s=bpy.context.scene;green=bpy.data.materials['Path'];root=bpy.data.objects['AMR pose'];person=bpy.data.objects['Person pose'];wheels=[bpy.data.objects['Left wheel'],bpy.data.objects['Right wheel']]
 for f in [1,n//2,n]:
  s.frame_set(f);expected=mapping[f-1];assert max(abs(root.location[j]-expected['pose'][j]) for j in range(2))<1e-5
  assert abs(root.rotation_euler.z-expected['pose'][2])<1e-5
  assert max(abs(w.rotation_euler.y-expected['wheel_angles'][j]) for j,w in enumerate(wheels))<1e-5
 (O/f'{mode}_validation.json').write_text(json.dumps(dict(saved_scene_reopened=True,checked_frames=[1,n//2,n],source='trace.json',frames=n)))
