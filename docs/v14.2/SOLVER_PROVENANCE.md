# Battery Solver Provenance

## Run record

- Solver: PyBaMM 26.10.0.0, `IDAKLUSolver`, CPU.
- Model / parameters: isothermal SPM / Chen2020.
- Scenario: initial SOC 1.0, 1C constant discharge, requested and observed duration 1800 s.
- Solver options: `rtol=1e-6`, `atol=1e-8`.
- Output sampling: 5 s fixed clock, 361 saved rows, 0 through 1800 s inclusive.
- Observed local solver execution: 0.1183 s.
- Termination: `final time`.
- Result SHA-256: `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`.
- Run ID: `v14.2-smoke-run2`.

## Early cutoff verification

- Config: `examples/education/battery_spm_early_termination_config.json`; same SPM / Chen2020 / 1C inputs, requested 7200 s, output interval 60 s.
- Observed termination: `event: Minimum voltage [V]` at `3606.549305848102` s, before the requested end. 61 regular samples through 3600 s plus the event state produce 62 rows.
- Result SHA-256: `23ca1050317fe899e43ce0c5ebbdf42dab3c5438d1d3e7dd1cb8676bffcb5b3e`.
- The stored SOC value at the exact event state is −0.00181925162447 from the solver's discharge capacity. It is preserved as calculated output; renderers may bound the gauge for display but do not alter the saved solver result.

The result JSON records exact Python/PyBaMM/solver backend versions, execution time, run ID, timestamp, parameter values, termination reason, config digest, CSV digest, assumptions and limitations. `load_validated_result()` checks the colocated config and CSV again before renderer execution. The shared trace sidecar points every computed beat at this same result digest and run ID.

`estimated_soc` is computed as initial SOC minus the change in PyBaMM discharge capacity divided by the parameter set's nominal cell capacity. The method is explicitly named `coulomb_counting_from_model_output`; it is not a PyBaMM-measured SOC variable.

The corrected source passed [Battery Simulation Actions run 38129252744](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252744). Blender 5.2.1 asset report, Manim context, trace, result, and renderer provenance agree on run `mixed-ci-38129252744-1` and result SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`. The final video is 720 frames with SHA-256 `d1d0fdab89e3506986a602224faaacff1737f92cf9e9ff2a89d81ebb0eff0e4a`; canonical timeline hash is `1ffd3c35a2852b56788572c8eaddbbff741586c32525bc8b2d5d4223cfcb531b`. Other workflow links are listed in the [integration report](INTEGRATION_REPORT.md).
