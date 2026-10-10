# V12 extension roadmap

1. Keep the executed Math/Physics, Classical CAN, and PMSM FOC adapters stable and evidence-backed.
2. Add Battery ECM only after the PyBaMM environment and cell-parameter provenance are validated.
3. Add a Python interrupt/event scheduler before considering Renode firmware emulation.
4. Add BLDC six-step as a distinct machine/controller model, never as an alias for PMSM FOC.
5. Consider CAN FD and SocketCAN integration as separate protocol/host capability steps.
6. Design coupled battery/DC bus/motor/firmware/CAN co-simulation around explicit solver clocks, sample/hold, event synchronization, causality, unit conversion, determinism, and numerical stability. A shared screen alone is not co-simulation.

Keep optional environments in separate groups. Add READY/L3 to a capability only after execution, validation, test, replay, renderer and media evidence exist.
