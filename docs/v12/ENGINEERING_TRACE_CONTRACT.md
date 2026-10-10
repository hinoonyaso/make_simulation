# Engineering trace contract

Outer envelope remains `mechanism-envelope/v1` and includes topic/domain, execution type, inputs, operations, outputs, source timestamps, provenance, software version, and limitations.

Continuous engineering payload:

```json
{"kind":"time_series","time_unit":"s","timestamps":[0.0,0.01],
 "signals":{"position":{"unit":"m","values":[0.2,0.1]},
             "controller":{"unit":"A","timestamps":[0.0,0.005,0.01],"values":[0,1,0]}}}
```

Each signal must have a unit and a strictly increasing finite time base of matching length. A signal-specific clock overrides payload timestamps. Raw samples are retained; `display_stride` is renderer-only.

Discrete event payloads use `kind=discrete_events`, `time_unit=bit_time` (or another explicit integer tick unit), and ordered nonnegative integer `events[].timestamp`. Classical CAN uses physical wire-bit ticks for events, while the envelope's primary timestamps are seconds at the configured bitrate. Presentation frames never reinterpret raw ticks.

All numeric arrays must be finite. Domain validators independently recompute or check relationships that matter, such as oscillator energy, CAN arbitration/frame bits, and rad/s to rpm conversion.
