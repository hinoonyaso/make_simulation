import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());checks=[]
for mode in ['scan','motion']:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'output/blender/{mode}.blend'))
 for f in [1,49,96]:
  bpy.context.scene.frame_set(f);k=0 if mode=='scan' else f-1;p=D['truth'][0] if mode=='scan' else D['visual_truth'][k]
  o=bpy.data.objects['AMR pose'];err=math.dist(o.location[:2],p[:2]);assert err<1e-5
  q=D['scans'][0][0] if mode=='scan' else D['visual_scans'][k][0]
  end=(p[0]+math.cos(p[2])*q[0]-math.sin(p[2])*q[1],p[1]+math.sin(p[2])*q[0]+math.cos(p[2])*q[1])
  actual=bpy.data.objects['Ray 0'].data.splines[0].points[1].co
  re=math.dist(actual[:2],end);assert re<1e-5
  checks.append(dict(mode=mode,frame=f,pose_error=err,ray_endpoint_error=re))
(R/'output/blender/reopen_validation.json').write_text(json.dumps(checks,indent=2))
print('Saved Blender trace checks passed')
