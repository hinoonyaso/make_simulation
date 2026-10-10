# PMSM field-oriented control

Run `uv run python scripts/produce_video.py --topic motor_foc --config examples/v12/pmsm_foc.json --preview`. The adapter uses motulator 0.9.0 `SynchronousMachine`, `MechanicalSystem`, `VoltageSourceConverter`, `CurrentVectorController`, `VectorControlSystem`, and speed PI control. The configured speed step and load-torque step are applied to the actual model.

The motor values in the example are demonstration parameters, not measurements or specifications for a JetRover or any user motor. Signals include phase currents, dq currents, q-axis current reference/feedback, torque, load, mechanical rad/s and the equivalent rpm. Adaptive solver timestamps and controller sample timestamps are retained independently. A sensored model state is available to the controller; this does not claim encoder hardware.

The converter is averaged (`Drive(..., pwm=False)`). The scene therefore does not display or claim high-frequency PWM switching, transistor losses, or a measured inverter. PMSM sinusoidal FOC is distinct from BLDC six-step commutation.

## V12.1 playback and chart contract

The renderer uses the timeline's common source range on every chart; a controller trace ending at `0.2999 s` is not stretched to the motor solver's `0.3001 s` endpoint. Source timestamps remain attached to each signal. Speed/torque/current references and sampled controller feedback use zero-order hold; continuous motor states use linear display interpolation, with endpoint hold when a signal clock ends before the shared range. Interpolation changes only the displayed frame state and never rewrites the execution trace. Different physical units are drawn in separate scaled rows with each signal's unit and numeric range shown; same-unit curves may share an axis. A frame cursor and source-time label are derived from presentation frame → unified timeline → source time → signal policy.

## V12.1 final plot accuracy

Within a plotted comparison group, signals with the same unit now share one range computed from all original samples (including zero where applicable); values from different units use independent lanes. The label for each signal shows the common physical range and unit. A same-unit value therefore maps to the same vertical position regardless of which trace contains it. Constant-valued signals get a nonzero range, and mixed-sign signals retain zero as a visible reference where the range crosses it.

Plot-only decimation is separate from trace data. Continuous signals use bucket extrema so local peaks are retained. ZOH signals retain the sample immediately before and after every transition, including one-sample pulses. When transition detail exceeds the point budget, the plot uses an extrema-preserving overview and marks the affected signal `OVERVIEW`; this is a display simplification, not a changed controller trace. The common timeline, independent sample clocks and endpoint hold remain unchanged.
