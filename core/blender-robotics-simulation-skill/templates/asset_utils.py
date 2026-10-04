from __future__ import annotations
import bpy
from pathlib import Path

def append_collection(blend_path, collection_name):
    """Append a reusable collection from a .blend asset file into the current scene."""
    blend_path=str(Path(blend_path).expanduser().resolve())
    before=set(bpy.data.collections.keys())
    directory=blend_path + '/Collection/'
    bpy.ops.wm.append(directory=directory, filename=collection_name)
    created=[bpy.data.collections[n] for n in bpy.data.collections.keys() if n not in before]
    target=bpy.data.collections.get(collection_name)
    return target or (created[-1] if created else None)
