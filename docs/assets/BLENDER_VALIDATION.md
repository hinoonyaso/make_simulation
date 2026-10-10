# Blender Validation

Blender: 5.2.1 LTS
All preview PNGs present: `True`

Each `.blend` file was reopened in Blender and checked for metric units, nonzero mesh bounds, object counts and keyframed state. This validates file/runtime integrity, not manufacturing or solver accuracy.

| File | Objects | Meshes | Keyframed | Bounds X/Y/Z (m) | Result |
|---|---:|---:|---:|---|---|
| `bearing_6204.blend` | 21 | 19 | 10 | 0.0055–0.0470 / 0.0055–0.0470 / 0.0006–0.0140 | PASS |
| `spur_gears_20_40.blend` | 4 | 4 | 2 | 0.0120–0.0839 / 0.0120–0.0839 / 0.0080–0.0080 | PASS |
| `bldc_motor_concept.blend` | 28 | 27 | 7 | 0.0120–0.1600 / 0.0120–0.1600 / 0.0060–0.0700 | PASS |
| `pcb_layered.blend` | 38 | 38 | 4 | 0.0020–0.1800 / 0.0016–0.1200 / 0.0002–0.0120 | PASS |
| `shaft_coupling_spring_fastener_battery.blend` | 28 | 27 | 1 | 0.0020–0.0740 / 0.0020–0.0740 / 0.0020–0.1800 | PASS |
| `beam_bracket_heatsink_fan.blend` | 23 | 23 | 5 | 0.0030–0.2400 / 0.0030–0.1000 / 0.0040–0.1200 | PASS |

Rendered PNGs:

- `assets/education/generated/beam_bracket_heatsink_fan.png`
- `assets/education/generated/bearing_6204.png`
- `assets/education/generated/bldc_motor_concept.png`
- `assets/education/generated/pcb_layered.png`
- `assets/education/generated/shaft_coupling_spring_fastener_battery.png`
- `assets/education/generated/spur_gears_20_40.png`
