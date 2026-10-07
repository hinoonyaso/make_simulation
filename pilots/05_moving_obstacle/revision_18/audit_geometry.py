"""Same asset vertex/topology coordinates before and after local optical treatment."""
import bpy,sys,json,hashlib,array
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from surface_treatment import apply_surface
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'))
def fingerprint():
 out={}
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith('TB3'):continue
  coords=array.array('f',[x for v in o.data.vertices for x in v.co]);faces=array.array('i',[x for p in o.data.polygons for x in p.vertices])
  out[o.name]={'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'geometry_sha256':hashlib.sha256(coords.tobytes()+faces.tobytes()).hexdigest(),'local_position':list(o.location),'local_rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None}
 return out
before=fingerprint();settings=apply_surface(bpy.context.scene,'selected',baseline='avoidance');after=fingerprint();assert before==after
(H/'output/geometry_audit.json').write_text(json.dumps({'status':'PASS','mesh_and_local_transform_before_after':before,'selected_settings':settings},indent=2)+'\n')
