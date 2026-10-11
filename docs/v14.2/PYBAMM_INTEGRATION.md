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

## Solver early termination

The adapter samples the regular output clock only through `solution.t[-1]`, then stores that exact final solver time when it falls between regular samples. For event termination, `event_time_s` must match that last saved timestamp; `actual_end_time_s` comes from the solved solution, never from the requested duration. The validator checks CSV row count, regular sample spacing (allowing a shorter final event interval), configured output interval, termination reason, event time, config identity, units and file hashes. Event-reported Coulomb-counting SOC is preserved as computed, including a small negative value if the model reaches the voltage cutoff after nominal capacity; it is not clamped to zero.

## Observed local output

The normal run ended at 1800 s with 361 samples and `termination_reason = "final time"`. A second actual run requested 7200 s and terminated on `event: Minimum voltage [V]` at 3606.549305848152 s; it contains 61 regular 60-second samples through 3600 s plus the event endpoint, for 62 rows. Both results passed persisted CSV/config/hash validation. Their digests and environment limitations are recorded in [the QA report](BATTERY_EDUCATIONAL_QA.md).

## References

- [PyBaMM 26.10.0.0 on PyPI](https://pypi.org/project/pybamm/26.10.0.0/)
- [PyBaMM documentation](https://docs.pybamm.org/en/latest/)
- [PyBaMM source repository](https://github.com/pybamm-team/PyBaMM)
- [PyBaMM learning resources](https://pybamm.org/learn/)
