import bpy,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from experiment import to_world
out=ROOT/'output';trace=json.loads((out/'trace.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(out/'blender/camera_observation_experiment.blend'))
errors=[]
for f in [0,100,330,800,1550,2200,2500,2700,3000,3100,3300,3800,4802]:
 bpy.context.scene.frame_set(f+1);st=trace['states'][trace['video_map'][f]]
 for name,key in [('Target_surface','center'),('Ground_truth_surface','true_surface'),('Reconstructed_point','estimated')]:
  err=float(np.linalg.norm(np.array(bpy.data.objects[name].location)-to_world(st[key])));errors.append(err);assert err<1e-5,(f,name,err)
(out/'blender/saved_project_validation.json').write_text(json.dumps(dict(status='passed',sampled_frames=13,max_position_error_m=max(errors)),indent=2))
print('SAVED PROJECT VALIDATED',max(errors))
