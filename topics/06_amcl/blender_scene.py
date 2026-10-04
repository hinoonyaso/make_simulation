"""Reuse previous episode's procedural room; render adaptive particle trace."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());O=R/'output/blender';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'05_slam/output/blender/motion.blend'))
# Preserve authored room and AMR geometry, remove previous sensor overlays and animation.
for o in list(bpy.data.objects):
 if o.name.startswith('Ray ') or any(m and m.name in ['Hits','Rays'] for m in getattr(o.data,'materials',[])):
  bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:o.animation_data_clear()
s=bpy.context.scene;s.camera.data.ortho_scale=14;s.render.resolution_x=1200;s.render.resolution_y=720;s.render.fps=30
root=bpy.data.objects['AMR pose']
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
blue=mat('Particle blue',(.05,.48,.74));green=mat('Estimate green',(.02,.66,.37))
mesh=bpy.data.meshes.new('Particle direction glyph');mesh.from_pydata([(.11,0,0),(-.055,.055,0),(-.055,-.055,0)],[],[(0,1,2)]);mesh.materials.append(blue)
particles=[]
for i in range(900):
 o=bpy.data.objects.new(f'Particle {i:04d}',mesh);bpy.context.collection.objects.link(o);particles.append(o)
bpy.ops.mesh.primitive_torus_add(major_radius=.42,minor_radius=.035,location=(0,0,.12));estimate=bpy.context.object;estimate.name='Estimated pose';estimate.data.materials.append(green)
checks=[]
for f in range(120):
 s.frame_set(f+1)
 if f<18:
  row=D['rows'][0];cloud=D['initial'];est=row['estimate']
 else:
  k=min(21,int((f-18)/102*22));row=D['rows'][k];cloud=row['resampled'];est=row['estimate']
 truth=row['truth'];root.location=(truth[0],truth[1],0);root.rotation_euler.z=truth[2];estimate.location=(est[0],est[1],.70);estimate.hide_render=f<18
 for o in [root,estimate]:
  o.keyframe_insert(data_path='location',frame=f+1);o.keyframe_insert(data_path='rotation_euler',frame=f+1);o.keyframe_insert(data_path='hide_render',frame=f+1)
 for i,o in enumerate(particles):
  o.hide_render=i>=len(cloud)
  if i<len(cloud):o.location=(*cloud[i][:2],.65);o.rotation_euler.z=cloud[i][2]
  o.keyframe_insert(data_path='location',frame=f+1);o.keyframe_insert(data_path='rotation_euler',frame=f+1);o.keyframe_insert(data_path='hide_render',frame=f+1)
 s.render.filepath=str(O/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 if f in [0,18,65,119]:checks.append(dict(frame=f+1,truth=truth,estimate=est,particle_count=len(cloud)))
s.frame_start=1;s.frame_end=120;bpy.ops.wm.save_as_mainfile(filepath=str(O/'amcl.blend'))
bpy.ops.wm.open_mainfile(filepath=str(O/'amcl.blend'))
for r in checks:
 s=bpy.context.scene;s.frame_set(r['frame']);o=bpy.data.objects['AMR pose'];e=bpy.data.objects['Estimated pose']
 assert math.dist(o.location[:2],r['truth'][:2])<1e-5
 assert math.dist(e.location[:2],r['estimate'][:2])<1e-5
 assert sum(not bpy.data.objects[f'Particle {i:04d}'].hide_render for i in range(900))==r['particle_count']
(O/'validation.json').write_text(json.dumps(checks,indent=2));print('Blender saved trace checks passed')
