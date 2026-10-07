import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'))
out=[{'overrides':[(v.name,v.material_override.name if v.material_override else None) for v in bpy.context.scene.view_layers]}]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('TB3'):
  out.append({'name':o.name,'parent':o.parent.name if o.parent else None,'materials':[(m.name,[(n.type,n.name) for n in m.node_tree.nodes] if m.node_tree else []) for m in o.data.materials]})
(H/'output/material_inspection.json').write_text(json.dumps(out,indent=2))
