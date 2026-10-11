"""Small Blender API compatibility helpers kept importable outside Blender."""
from __future__ import annotations


def configure_eevee(scene, samples: int) -> str:
    """Select an Eevee engine exposed by this Blender build and configure TAA."""
    try:
        engine_property = scene.render.bl_rna.properties["engine"]
        engines = {item.identifier for item in engine_property.enum_items}
    except (AttributeError, KeyError, TypeError) as exc:
        raise RuntimeError("Blender render engine identifiers are unavailable") from exc
    engine = next((name for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT") if name in engines), None)
    if engine is None:
        raise RuntimeError(f"Supported Eevee renderer unavailable; available engines: {sorted(engines)}")
    scene.render.engine = engine
    eevee = getattr(scene, "eevee", None)
    if eevee is None or not hasattr(eevee, "taa_render_samples"):
        raise RuntimeError(f"Blender Eevee API for render samples is unavailable for {engine}")
    eevee.taa_render_samples = max(8, int(samples))
    return engine
