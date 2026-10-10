# Ubuntu 24.04 setup

Target: Linux x86_64, Python 3.12, uv. ARM64/Jetson has not been validated. Check without changing the host:

```bash
bash scripts/setup_v12_ubuntu.sh --check
uv run python scripts/inspect_engineering_env.py --check sim-math
uv run python scripts/inspect_engineering_env.py --check sim-can
uv run python scripts/inspect_engineering_env.py --check sim-motor
```

Install only when requested by the operator:

```bash
bash scripts/setup_v12_ubuntu.sh --install
```

The installer checks each apt package first and only installs missing packages. It does not upgrade the system. It requires administrator rights for missing system packages, then runs `uv sync --group sim-math --group sim-can --group sim-motor` and an import smoke check. A JSONL action record is appended to `output/v12_setup_history.jsonl`.

Current Python groups are separately declared in `pyproject.toml`; `uv.lock` pins the resolved versions. Import names: `control`, `can`, `cantools`, `motulator`.

Example renders:

```bash
uv run python scripts/produce_video.py --topic physics_oscillator --config examples/v12/oscillator.json --preview
uv run python scripts/produce_video.py --topic can_arbitration --config examples/v12/can_arbitration.json --preview
uv run python scripts/produce_video.py --topic motor_foc --config examples/v12/pmsm_foc.json --preview
```

Omit `--preview` for 1920×1080 at 30 fps. Add `--mode replay --trace <saved trace.json>` to render a saved envelope without rerunning its model. Runs are isolated; default outputs are under the repository output route and can be overridden with `--output-dir` and `--execution-cache-dir`.
