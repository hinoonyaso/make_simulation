import bpy
import time
from pathlib import Path
root = Path(__file__).resolve().parent
scene = bpy.context.scene
print('BLENDER', bpy.app.version_string)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 900
scene.render.resolution_y = 680
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(root / 'output' / 'blender_probe.png')
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
start = time.time()
bpy.ops.render.render(write_still=True)
print('RENDER_SECONDS', time.time()-start)
for frame in range(2,5):
    bpy.data.objects['Cube'].rotation_euler.z += .1
    start = time.time()
    bpy.ops.render.render(write_still=False)
    print('WARM_RENDER_SECONDS', frame, time.time()-start)
