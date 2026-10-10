# Dependency matrix

| Group | Locked packages | Used for |
|---|---|---|
| `sim-math` | SymPy 1.14.0, SciPy 1.18.1, control 0.10.2 | ODE expression/solution, integration, state-space representation |
| `sim-can` | python-can 4.6.1, cantools 44.2.1 | VirtualBus API check and DBC round trip |
| `sim-motor` | motulator 0.9.0 | PMSM and vector-control execution |
| `sim-render` | Manim 0.21.x constraint | Optional isolated renderer/test install |

NumPy is supplied transitively by SciPy/Manim in these execution paths and remains aligned with the lock. No Slycot, PyBaMM, Renode, or CAN hardware package is required. `python3-tk`, `can-utils`, and `python3-venv` are missing in the observed Ubuntu image; administrator installation was unavailable. Optional host/runtime checks do not block the three simulation adapters.

motulator is pinned to 0.9.0 because its installed Python 3.12 API was inspected and used. Its project is MIT-licensed; consult the installed distribution metadata and upstream release page before redistributing bundled source. No motulator example implementation was copied into this repository.
