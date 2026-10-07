"""Local optical candidates. Faithful mesh, collision/state and protected kits unchanged."""
import bpy
from mathutils import Vector

def apply_surface(scene,variant,baseline='case'):
 assert variant in ['baseline','material','light','combined','combined_v2','selected']
 material=variant in ['material','combined','combined_v2','selected'];lighting=variant in ['light','combined','combined_v2','selected']
 settings={'variant':variant,'baseline':baseline,'materials':{},'lights':{}}
 root=bpy.data.objects['TurtleBot3']
 for obj in bpy.data.objects:
  if obj.type!='MESH' or not obj.name.startswith('TB3'):continue
  if obj.name=='TB3Base':color,metal,rough=((.060,.073,.090,1),.15,.34) if material else ((.075,.10,.135,1),.12,.58) if baseline=='case' else ((.025,.029,.035,1),.15,.5)
  elif obj.name=='TB3Lidar':color,metal,rough=((.012,.014,.018,1),.05,.30) if material else ((.006,.007,.009,1),.05,.52 if baseline=='case' else .38)
  elif obj.name.startswith('TB3Tyre'):color,metal,rough=(.018,.018,.020,1),0,.76 if material else .9
  elif obj.name.startswith('TB3Caster'):color,metal,rough=(.7,.72,.75,1),1,.52 if baseline=='case' else .25
  else:continue
  if variant=='selected':
   if obj.name=='TB3Base':rough=.42
   if obj.name=='TB3Lidar':rough=.48
   if obj.name.startswith('TB3Tyre'):rough=.82
  mat=bpy.data.materials.new('R18_'+variant+'_'+obj.name);mat.use_nodes=True;shader=mat.node_tree.nodes['Principled BSDF']
  shader.inputs['Base Color'].default_value=color;shader.inputs['Metallic'].default_value=metal;shader.inputs['Roughness'].default_value=rough
  obj.data.materials.clear();obj.data.materials.append(mat)
  for polygon in obj.data.polygons:polygon.material_index=0
  for slot in obj.material_slots:slot.link='DATA';slot.material=mat
  settings['materials'][obj.name]={'color':color,'metallic':metal,'roughness':rough}
 if lighting:
  # Existing emitters, deliberately directional key and lower fill; no exposure change.
  rig={'Key':((-1.8,-1.6,2.6),500,1.4),'Fill':((2.5,-1.2,3.),160,4.),'Rim':((1.5,2.,2.5),220,2.)}
  if variant=='combined_v2':rig={'Key':((-1.5,2.5,3.),650,1.5),'Fill':((2.5,-1.2,3.),220,4.),'Rim':((1.5,2.,2.5),220,2.)}
  if variant=='selected':rig={'Key':((-1.5,2.5,3.6),850,2.2),'Fill':((2.5,-1.2,3.),240,4.),'Rim':((1.5,2.,2.5),300,2.5)}
  for name,(position,energy,size) in rig.items():
   obj=bpy.data.objects.get(name);assert obj and obj.type=='LIGHT',name
   obj.animation_data_clear();obj.location=position;obj.rotation_euler=(Vector((0,0,.08))-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=energy;obj.data.size=size
  scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.26 if variant=='selected' else .22
 for name in ['Key','Fill','Rim']:
  obj=bpy.data.objects[name];settings['lights'][name]={'position':list(obj.location),'rotation':list(obj.rotation_euler),'energy':obj.data.energy,'size':obj.data.size}
 settings['world_strength']=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value
 settings['exposure']=scene.view_settings.exposure;settings['view_transform']=scene.view_settings.view_transform;settings['look']=scene.view_settings.look
 return settings
