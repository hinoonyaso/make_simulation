# PMSM field-oriented control

Run `uv run python scripts/produce_video.py --topic motor_foc --config examples/v12/pmsm_foc.json --preview`. The adapter uses motulator 0.9.0 `SynchronousMachine`, `MechanicalSystem`, `VoltageSourceConverter`, `CurrentVectorController`, `VectorControlSystem`, and speed PI control. The configured speed step and load-torque step are applied to the actual model.

The motor values in the example are demonstration parameters, not measurements or specifications for a JetRover or any user motor. Signals include phase currents, dq currents, q-axis current reference/feedback, torque, load, mechanical rad/s and the equivalent rpm. Adaptive solver timestamps and controller sample timestamps are retained independently. A sensored model state is available to the controller; this does not claim encoder hardware.

The converter is averaged (`Drive(..., pwm=False)`). The scene therefore does not display or claim high-frequency PWM switching, transistor losses, or a measured inverter. PMSM sinusoidal FOC is distinct from BLDC six-step commutation.
