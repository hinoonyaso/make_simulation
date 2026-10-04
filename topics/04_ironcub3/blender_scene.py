"""Procedural educational humanoid. Render recorded planar dynamics, no fake physics."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/blender'
BG=(.93,.947,.969,1)

def material(name,color,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.metallic=metal;m.roughness=.35;return m
def finish(obj,name,mat,parent=None):
    obj.name=name;obj.data.materials.append(mat)
    if parent:obj.parent=parent
    return obj
def cube(name,loc,size,mat,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Soft edges','BEVEL');bevel.width=.035;bevel.segments=3
    o.modifiers.new('Normals','WEIGHTED_NORMAL');return finish(o,name,mat,parent)
def sphere(name,loc,size,mat,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.scale=size
    for f in o.data.polygons:f.use_smooth=True
    return finish(o,name,mat,parent)
def cylinder(name,loc,radius,depth,mat,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc)
    o=bpy.context.object
    for f in o.data.polygons:f.use_smooth=True
    return finish(o,name,mat,parent)
def segment(name,a,b,r,mat,parent=None):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,mat,parent)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def curve(name,pts,r,mat):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o

def setup():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.fps=30
    s.render.resolution_x=900;s.render.resolution_y=560;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
    s.render.image_settings.compression=20
    s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl'
    s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True
    s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.background_type='WORLD';s.world.color=BG[:3]
    s.view_settings.view_transform='Standard'
    white=material('Ivory shells',(.79,.85,.89));dark=material('Graphite joints',(.065,.1,.15))
    blue=material('Blue accents',(.03,.34,.69));metal=material('Turbines',(.27,.31,.35),.7)
    orange=material('Qualitative exhaust',(.98,.41,.035));green=material('Reference',(.02,.6,.39))
    muted=material('Grid',(.72,.77,.82));floor=material('Floor',(.90,.925,.95))
    cube('Floor',(0,0,-.055),(7,6,.1),floor)
    for i in range(-6,7):
        segment('Grid X',(-3,i*.5,.002),(3,i*.5,.002),.0025,muted)
        segment('Grid Y',(i*.5,-3,.002),(i*.5,3,.002),.0025,muted)
    root=bpy.data.objects.new('Computed robot state',None);bpy.context.collection.objects.link(root)
    cube('Torso',(0,0,.22),(.42,.28,.49),white,root)
    cube('Chest inset',(0,-.15,.25),(.29,.025,.23),blue,root)
    cube('Pelvis',(0,0,-.13),(.34,.25,.18),dark,root)
    cylinder('Neck',(0,0,.53),.075,.15,dark,root)
    sphere('Head',(0,-.025,.69),(.17,.14,.18),white,root)
    for x in [-.067,.067]:sphere('Eye',(x,-.157,.71),(.025,.017,.025),dark,root)
    for side in [-1,1]:
        x=side*.13
        sphere('Hip',(x,0,-.2),(.085,.09,.085),blue,root)
        segment('Thigh',(x,0,-.22),(x,0,-.52),.085,white,root)
        sphere('Knee',(x,0,-.54),(.077,.077,.077),dark,root)
        segment('Shin',(x,0,-.57),(x,-.025,-.84),.069,white,root)
        cube('Foot',(x,-.085,-.91),(.15,.29,.10),dark,root)
        sphere('Shoulder',(side*.25,0,.39),(.095,.095,.095),blue,root)
        segment('Upper arm',(side*.26,0,.39),(side*.32,-.13,.17),.07,white,root)
        sphere('Elbow',(side*.32,-.13,.15),(.06,.06,.06),dark,root)
    cube('Jetpack',(0,.20,.27),(.40,.13,.40),dark,root)
    plumes=[]
    # All effective lever arms equal the planar model's +/-0.32 m.
    for j,(x,y) in enumerate([(-.32,-.13),(.32,-.13),(-.32,.23),(.32,.23)]):
        z=.01 if y<0 else .29
        cylinder(f'Turbine {j+1}',(x,y,z),.09,.29,metal,root)
        cylinder(f'Turbine band {j+1}',(x,y,z+.05),.095,.045,blue,root)
        cylinder(f'Nozzle {j+1}',(x,y,z-.16),.065,.07,dark,root)
        bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.008,radius2=.057,depth=1,
                                      location=(x,y,z-.19))
        plume=finish(bpy.context.object,f'Qualitative plume {j+1}',orange,root)
        plumes.append((plume,z-.19))
    target=sphere('Target CoM',(.5,0,1.8),(.045,.045,.045),green)
    bpy.ops.object.camera_add(location=(4.2,-7,3.4));cam=bpy.context.object
    cam.rotation_euler=(Vector((.22,0,1.55))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=4.4;s.camera=cam
    # Explicit lights retained for switching to Eevee/Cycles.
    bpy.ops.object.light_add(type='AREA',location=(2,-4,6));bpy.context.object.data.energy=800
    bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
    return root,plumes,target,blue,orange

def apply(objects,row):
    root,plumes,target,*_=objects
    root.location=(row['x'],0,row['z']);root.rotation_euler=(0,row['pitch'],0)
    target.location=(row['target'][0],0,row['target'][1])
    for (plume,nozzle),force in zip(plumes,row['jets']):
        length=.08+.5*force/250
        plume.scale=(1,1,length);plume.location.z=nozzle-length/2

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args(args)
    OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'output/simulation.json').read_text())
    objects=setup();s=bpy.context.scene
    if a.preview:
        apply(objects,data['nominal']['frames'][0]);s.render.filepath=str(OUT/'preview.png')
        bpy.ops.render.render(write_still=True);return
    report={}
    for mode in ['nominal','mismatch']:
        dest=OUT/mode;dest.mkdir(exist_ok=True)
        for obj in [objects[0],objects[2],*[p[0] for p in objects[1]]]:obj.animation_data_clear()
        rows=data[mode]['frames'];s.frame_start=1;s.frame_end=361
        s['source']='Original planar educational simulation, not paper reproduction'
        s['mode']=mode
        for frame in range(361):
            row=rows[round(frame*100/30)];s.frame_set(frame+1);apply(objects,row)
            for obj in [objects[0],objects[2],*[p[0] for p in objects[1]]]:
                obj.keyframe_insert(data_path='location',frame=frame+1)
                obj.keyframe_insert(data_path='rotation_euler',frame=frame+1)
                obj.keyframe_insert(data_path='scale',frame=frame+1)
            path=dest/f'{frame:04d}.png'
            if a.render and not path.exists():
                s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        s.frame_set(1);apply(objects,rows[0]);s.render.filepath=str(dest/'direct_')
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{mode}.blend'))
    # Reopen saved projects and compare sampled keyframed states with the trace.
    for mode in ['nominal','mismatch']:
        bpy.ops.wm.open_mainfile(filepath=str(OUT/f'{mode}.blend'))
        for frame in [1,181,361]:
            bpy.context.scene.frame_set(frame);row=data[mode]['frames'][round((frame-1)*100/30)]
            root=bpy.data.objects['Computed robot state']
            assert abs(root.location.x-row['x'])<1e-5 and abs(root.location.z-row['z'])<1e-5
            assert abs(root.rotation_euler.y-row['pitch'])<1e-5
        report[mode]='saved project sampled states match trace'
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
