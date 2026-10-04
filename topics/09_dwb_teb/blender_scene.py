"""Shared-trace spatial playback; poses are computed in model.py, not authored motion."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());O=R/'output/blender';O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1080;s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.fps=15;s.world.color=(.93,.947,.969);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
def mat(name,c):
 m=bpy.data.materials.new(name);m.use_fake_user=True;m.diffuse_color=(*c,1);return m
white=mat('Shell',(.83,.88,.93));blue=mat('Blue',(.03,.44,.68));dark=mat('Wheels',(.07,.1,.15));gray=mat('Walls',(.65,.72,.80));floor=mat('Floor',(.91,.94,.97));red=mat('Obstacle',(.8,.26,.23));green=mat('Selected DWB',(.07,.53,.36));purple=mat('Optimized TEB',(.48,.3,.66));light=mat('Reference',(.58,.66,.75))
def cube(name,loc,scale,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);o.parent=parent;return o
def empty(name,parent=None):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=parent;return o
def curve(name,points,m,thickness=.015):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=thickness;sp=data.splines.new('POLY');sp.points.add(len(points)-1)
 for p,q in zip(sp.points,points):p.co=(*q,1)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
cube('Floor',(0,0,-.06),(7.6,2.65,.12),floor)
for y in [-1.3,1.3]:cube('Corridor wall',(0,y,.16),(7.6,.1,.32),gray)
for i in range(30):curve('Global path',[(-3+i*.2,0,.022),(-2.9+i*.2,0,.022)],light,.012)
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=D['obstacle_radius'],depth=.62,location=(*D['obstacle'],.31));bpy.context.object.name='Local obstacle';bpy.context.object.data.materials.append(red)
root=empty('AMR pose');cube('Chassis',(0,0,.18),(.34,.26,.2),white,root);cube('Front bumper',(.18,0,.18),(.03,.24,.08),blue,root);wheels=[]
for name,y in [('Left wheel',.21),('Right wheel',-.21)]:
 pivot=empty(name,root);pivot.location=(0,y,.1);wheels.append(pivot);bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.1,depth=.03);o=bpy.context.object;o.name=name+' tire';o.parent=pivot;o.rotation_euler.x=math.pi/2;o.data.materials.append(dark);cube(name+' marker',(0,0,0),(.16,.035,.018),white,pivot)
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.065,depth=.06,location=(0,0,.31));o=bpy.context.object;o.parent=root;o.data.materials.append(blue)
curve('Goal',[(3+.22*math.cos(a),.22*math.sin(a),.025) for a in [i*2*math.pi/48 for i in range(49)]],green,.025)
bpy.ops.object.camera_add(location=(3.5,-6,10));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.2;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=(0,-3,8));bpy.context.object.data.energy=1000
for mode in ['dwb','teb']:
 for ob in list(bpy.data.objects):
  if ob.name.startswith('Prediction') or ob.name.startswith('Executed'):bpy.data.objects.remove(ob,do_unlink=True)
 for ob in [root,*wheels]:ob.animation_data_clear()
 rows=D['runs'][mode+'_obstacle']['rows'];predictions=[];histories=[]
 for row in rows:
  detail=row['detail'];pts=detail['candidates'][detail['selected']]['trajectory'] if mode=='dwb' and detail.get('selected') is not None else detail.get('poses',[])
  predictions.append(curve('Prediction',[(p[0],p[1],.035) for p in pts],green if mode=='dwb' else purple,.022) if len(pts)>1 else None)
  past=[r['pose'] for r in rows[:row['k']+1]];past=([past[0],past[0]] if len(past)==1 else past);histories.append(curve('Executed',[(p[0],p[1],.032) for p in past],blue,.014))
 folder=O/mode;folder.mkdir(exist_ok=True);mapping=[];n=213
 for f in range(n):
  t=14.2 if f==n-1 else f/15;k=min(int(t/.2+1e-8),len(rows)-1);row=rows[k];alpha=min(1,max(0,(t-row['time'])/.2));p=[row['pose'][j]+alpha*(row['next_pose'][j]-row['pose'][j]) for j in range(3)]
  s.frame_set(f+1);root.location=(*p[:2],0);root.rotation_euler.z=p[2];root.keyframe_insert(data_path='location',frame=f+1);root.keyframe_insert(data_path='rotation_euler',frame=f+1)
  for j,w in enumerate(wheels):w.rotation_euler.y=row['wheel_angles'][j]-(1-alpha)*.2*row['wheel_rates'][j];w.keyframe_insert(data_path='rotation_euler',frame=f+1)
  for i,ob in enumerate(predictions):
   if ob:ob.hide_render=i!=k or t>=len(rows)*.2;ob.keyframe_insert(data_path='hide_render',frame=f+1)
  for i,ob in enumerate(histories):ob.hide_render=i!=k;ob.keyframe_insert(data_path='hide_render',frame=f+1)
  mapping.append(dict(frame=f+1,sample=k,simulation_time=min(t,len(rows)*.2),pose=p,wheel_angles=[w.rotation_euler.y for w in wheels]));s.render.filepath=str(folder/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 s.frame_start=1;s.frame_end=n;bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{mode}.blend'));(O/f'{mode}_frames.json').write_text(json.dumps(mapping))
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{mode}.blend'));s=bpy.context.scene;root=bpy.data.objects['AMR pose'];wheels=[bpy.data.objects['Left wheel'],bpy.data.objects['Right wheel']];green=bpy.data.materials['Selected DWB'];purple=bpy.data.materials['Optimized TEB'];blue=bpy.data.materials['Blue']
 for f in [1,107,213]:
  s.frame_set(f);e=mapping[f-1];assert max(abs(root.location[j]-e['pose'][j]) for j in range(2))<1e-5;assert abs(root.rotation_euler.z-e['pose'][2])<1e-5;assert max(abs(w.rotation_euler.y-e['wheel_angles'][j]) for j,w in enumerate(wheels))<1e-5
 (O/f'{mode}_validation.json').write_text(json.dumps(dict(reopened=True,frames=n,checked=[1,107,213],source='trace.json')))
