# PyBaMM Integration

## Model and input

The optional `sim-battery` group pins PyBaMM 26.10.0.0. The registered adapter permits only PyBaMM, Single Particle Model (SPM), and Chen2020 for this first scenario. SPM was selected as a CPU-friendly first model for illustrating terminal voltage over a bounded discharge; it does not represent all electrolyte or thermal behavior.

Input is `examples/education/battery_spm_config.json`: initial SOC 1.0, constant 1C discharge, requested duration 1800 s, 5 s samples, IDAKLUSolver with `rtol=1e-6` and `atol=1e-8`. The adapter reads Chen2020 nominal capacity and cutoff voltages from installed PyBaMM rather than hard-coding them. Positive `Current [A]` is treated as discharge for this scenario.

## Run boundaries

1. `produce_lesson.py --plan-only` validates the allow-listed input and records `PLANNED`; it does not import or call the solver.
2. `run_battery_simulation.py` performs the actual PyBaMM execution and writes `simulation_config.json`, `battery_timeseries.csv`, and `result.json`.
3. `validate_battery_result.py` verifies schema, execution provenance, hashes, units, arrays, current/capacity integral, Coulomb Counting SOC and voltage boundaries.
4. Renderer invocation requires `--solver-result`. It revalidates the saved result before making the output directory, copies the evidence into the lesson run and emits a shared `battery_trace.json`.
5. Blender and Manim consume that one CSV/run ID; renderers do not rerun PyBaMM. The V12 integer-frame timeline maps presentation progress only within the saved solver time range. Manim uses linear interpolation between neighboring saved samples for its moving marker; it does not extend beyond the run.

## Observed local output

The verified local run ended at 1800 s with 361 samples and `termination_reason = "final time"`. `Voltage [V]`, `Current [A]`, and `Discharge capacity [A.h]` are evaluated from the PyBaMM solution at the declared fixed sample clock. The result SHA-256 is recorded in [the QA report](BATTERY_EDUCATIONAL_QA.md).

## References

- [PyBaMM 26.10.0.0 on PyPI](https://pypi.org/project/pybamm/26.10.0.0/)
- [PyBaMM documentation](https://docs.pybamm.org/en/latest/)
- [PyBaMM source repository](https://github.com/pybamm-team/PyBaMM)
- [PyBaMM learning resources](https://pybamm.org/learn/)
