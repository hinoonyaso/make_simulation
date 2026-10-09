# V11 roadmap

1. Add optional CPU/Windows CI for the Blender H1 mesh trace renderer and actual local YOLO adapter path; current local renders are validated, but remote render integration has not run.
2. Connect ready V11 visual plans to measured Korean narration, sentence captions, Reviewer and final delivery QA before claiming L4.
3. Expand the YOLO adapter to other models only after each checkpoint, runtime version, and license is separately verified; keep synthetic NMS separate.
4. Dispatch the revised GitHub Actions integration workflow on a clean remote runner and record artifact/decode results.
5. Provision supported simulator runners only when those physical environments are in scope; this V11.2 request excludes acquiring new maps/worlds.

These are future tasks; they are not represented as implemented capabilities.

6. Enable Blender process execution from the normal WSL renderer context (or provide a supported Linux Blender runner) so H1 `motion_3d` preflight and render do not require elevated process permissions.
7. Run the V11.4 manual integration workflow on GitHub Actions and capture H1/YOLO/RAG artifacts on a runner with Blender, model assets, and local browser capture enabled.
