# Math and classical physics: oscillator

Run `uv run python scripts/produce_video.py --topic physics_oscillator --config examples/v12/oscillator.json --preview`. The adapter computes `m*x'' + c*x' + k*x = F(t)` for a linear translational single-DOF model. Mass is kg, damping N·s/m, stiffness N/m, displacement m, velocity m/s, force N, and energy J.

SymPy expresses and solves the configured ODE with initial conditions using its constant-coefficient homogeneous or sinusoidal undetermined-coefficients solver. If no supported symbolic solution is available, the trace says so; it never fabricates an analytic comparison. SciPy `solve_ivp` DOP853 supplies recorded numerical state samples. python-control receives the equivalent state-space matrices. Solver tolerances are stored with the trace.

Validation compares supported symbolic and numerical positions, recomputes kinetic/potential/total energy, checks unforced damped energy does not increase beyond tolerance, and records the work/energy balance residual. It also runs same-mass/spring/initial-state SciPy responses for zero, critical (`2√mk`) and overdamping (`1.5 × critical`) and recomputes them during trace validation. The final scene displays these computed trajectories against the configured damping response.

## V12.1 terminal sample handling

The former count was calculated before a non-grid-aligned stop time was appended. For `duration_s=1.05` and `sample_period_s=0.1`, the trace therefore had 12 timestamps while the solver shape check expected 11. `_build_timestamps()` now creates the complete finite, strictly increasing clock first, includes the exact requested stop time once, applies the 2..1,000,000 sample bound to the final array, then derives the solver count from its length. The same output clock is used for the response, damping sweep, energy and analytic comparison. Older traces without `duration_s` remain replayable by treating their last stored timestamp as the stop time.

The regression case produces 12 samples from `0.0` through `1.0` and a final `1.05 s`; the current solver reports a maximum analytic position error below `2e-7 m`, and the trace validator checks the terminal timestamp, signal lengths, sample count, envelope clock, energy equation and damping recomputation.
