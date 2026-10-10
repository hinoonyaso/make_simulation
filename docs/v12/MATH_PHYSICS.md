# Math and classical physics: oscillator

Run `uv run python scripts/produce_video.py --topic physics_oscillator --config examples/v12/oscillator.json --preview`. The adapter computes `m*x'' + c*x' + k*x = F(t)` for a linear translational single-DOF model. Mass is kg, damping N·s/m, stiffness N/m, displacement m, velocity m/s, force N, and energy J.

SymPy expresses and solves the configured ODE with initial conditions using its constant-coefficient homogeneous or sinusoidal undetermined-coefficients solver. If no supported symbolic solution is available, the trace says so; it never fabricates an analytic comparison. SciPy `solve_ivp` DOP853 supplies recorded numerical state samples. python-control receives the equivalent state-space matrices. Solver tolerances are stored with the trace.

Validation compares supported symbolic and numerical positions, recomputes kinetic/potential/total energy, checks unforced damped energy does not increase beyond tolerance, and records the work/energy balance residual. It also runs same-mass/spring/initial-state SciPy responses for zero, critical (`2√mk`) and overdamping (`1.5 × critical`) and recomputes them during trace validation. The final scene displays these computed trajectories against the configured damping response.
