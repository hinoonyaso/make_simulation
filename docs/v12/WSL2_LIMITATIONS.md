# WSL2 status and limits

The observed environment is Ubuntu 24.04.4 LTS, x86_64, Python 3.12.3, uv 0.12.3 on a Microsoft WSL2 kernel. SymPy 1.14.0, SciPy 1.18.1, python-control 0.10.2, python-can 4.6.1, cantools 44.2.1, motulator 0.9.0, Manim 0.21.0, and FFmpeg 6.1.1 were available after dependency synchronization.

`python-can` VirtualBus is the required CPU-only CAN transport check. The environment doctor attempted to inspect link devices, but `ip -details link show` returned `Cannot open netlink socket: Operation not permitted`. No vcan interface was created and no host networking or kernel configuration was changed. `can-utils`, `python3-tk`, and `python3-venv` apt packages were absent; this session has no passwordless sudo. The optional PyBaMM and Renode runtimes are absent.

Windows Blender 5.2.1 is installed. A normal subprocess launch from the WSL environment doctor failed, while a read-only probe through the approved host-execution route succeeded. A previous actual H1 mesh render is recorded in `docs/v11/TEST_RESULTS.md`. The doctor reports this distinction as installed-but-blocked for its own process, with the historical successful-render evidence attached. V12's engineering scenes use Manim and do not require Blender. This is a process/permission boundary, not a claim that Blender cannot run on this PC or under WSL2 generally.
