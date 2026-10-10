# Battery/BMS future design (not implemented)

Candidate optional dependency group: `sim-battery` with PyBaMM. Do not install it in the default engineering environment until Python, NumPy, SciPy, CasADi and solver compatibility are checked together.

First candidate model: Thevenin ECM with OCV(SOC), ohmic resistance, one or more RC polarization branches, coulomb-counted SOC and an explicitly declared thermal model. Record current, terminal voltage, internal states, SOC and BMS protection state with units, solver/time base, and parameter provenance. Use assumed cell parameters only when clearly labelled; never claim user-cell accuracy without validated data.

SPM, SPMe and DFN are later fidelity options. The battery topic remains absent from executable capability registration until runtime, tests, independent validation and render evidence exist.
