# V12 Engineering Simulation Architecture

V12 keeps the V11.5 pipeline and `mechanism-envelope/v1` outer trace. Three lazy-loaded L3 adapters add `physics_oscillator`, `can_arbitration`, and `motor_foc`; each owns execution, domain validation, and a visual plan. The existing production CLI still owns cache identity, run isolation, storyboard, `mechanism-timeline/v1`, renderer routing, media QA, and report writing.

```text
request/config -> registry -> adapter -> validated envelope + domain payload
               -> trace-backed storyboard -> integer-frame timeline -> Manim
               -> 30 fps MP4 -> delivery full-decode -> production_report.json
```

`core/mechanism/engineering_trace.py` validates SI-labelled sampled signals and integer event ticks. A signal can carry its own `timestamps`; it is not forced to use the payload-wide solver clock. Source simulation time is kept in the timeline separately from presentation frames. Renderer downsampling affects only plotted points, never saved trace data.

The shared engineering renderer is `MechanismTraceScene`'s `engineering` plan kind. It reuses the existing Manim runtime and theme, and builds trace waveforms, digital bit lanes, equation states, labels, and event markers. It does not claim physical execution where the adapter does not provide it.

The execution cache now fingerprints the three adapters, trace validators and their engine versions. Cache hits still pass the adapter's domain validator. Presentation changes remain in the render/run identity and do not invalidate the engine's computation cache.

| Topic | Executed engine | Evidence/limits |
|---|---|---|
| `physics_oscillator` | SymPy `dsolve`, SciPy `solve_ivp` DOP853, python-control state space | Linear single-DOF mass/spring/viscous damper; optional sinusoid; symbolic solution only when SymPy supports it |
| `can_arbitration` | Deterministic Classical CAN 2.0A bit/event model; python-can VirtualBus; cantools DBC | Standard 11-bit frames; VirtualBus is a transport smoke test, not bit arbitration or an electrical bus |
| `motor_foc` | motulator 0.9 PMSM and vector controller | Demonstration motor values, sensored model-state feedback, averaged voltage-source converter; no PWM switching trace |

Battery, firmware, RTOS, Renode, CAN FD, BLDC six-step, and coupled co-simulation remain planned. None is registered as executable.
