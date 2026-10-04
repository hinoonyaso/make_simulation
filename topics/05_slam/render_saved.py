import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'output/trace.json').read_text())
for mode in ['scan','motion']:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'output/blender/{mode}.blend'))
 s=bpy.context.scene;s.camera.data.ortho_scale=14
 for f in range(96):
  s.frame_set(f+1)
  expected=D['truth'][0] if mode=='scan' else D['visual_truth'][f]
  assert abs(bpy.data.objects['AMR pose'].location.x-expected[0])<1e-5
  s.render.filepath=str(R/f'output/blender/{mode}/{f:04d}.png');bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(R/f'output/blender/{mode}.blend'))
