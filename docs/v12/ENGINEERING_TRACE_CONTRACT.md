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

## V12.1 presentation mapping

The rendering clock is distinct from both the motor solver clock and the controller sample clock. `engineering_state_for_frame(trace, timeline, frame_index)` resolves a presentation frame through the unified timeline, selects its source time (including replay and hold phases), and samples each signal with its named display policy. References and controller sample signals use zero-order hold; continuous states use linear interpolation within their own clock and endpoint hold outside it. The renderer maps each signal's absolute timestamp onto one shared source-time X axis. This is a presentation operation only; the underlying trace and its independent clocks are unchanged.

CAN event timestamps are physical wire-bit ticks, while the envelope clock is in seconds at the configured bitrate. Domain validation recomputes event records and primary timestamps from the same protocol inputs before allowing cache reuse.
