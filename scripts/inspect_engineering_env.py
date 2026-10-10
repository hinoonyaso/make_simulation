#!/usr/bin/env python3
"""Report the installed V12 engineering runtimes without changing the host."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GROUPS = {
    "sim-math": {"sympy": ("sympy", "sympy"), "scipy": ("scipy", "scipy"),
                 "python_control": ("control", "control")},
    "sim-can": {"python_can": ("can", "python-can"), "cantools": ("cantools", "cantools")},
    "sim-motor": {"motulator": ("motulator", "motulator")},
}


def _distribution(module: str, package: str) -> dict:
    installed = importlib.util.find_spec(module) is not None
    try:
        version = importlib.metadata.version(package) if installed else None
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    return {"status": "READY" if installed else "OPTIONAL_MISSING", "version": version}


def _command(name: str, args: list[str] | None = None) -> dict:
    binary = shutil.which(name)
    if not binary:
        return {"status": "OPTIONAL_MISSING", "path": None, "version": None}
    version = None
    if args:
        try:
            result = subprocess.run([binary, *args], capture_output=True, text=True,
                                    timeout=15, check=True)
            version = (result.stdout or result.stderr).splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError) as exc:
            return {"status": "BLOCKED", "path": binary, "version": None, "reason": str(exc)}
    return {"status": "READY", "path": binary, "version": version}


def _recorded_blender_host_evidence() -> dict | None:
    """Return a previously recorded successful host-side Blender render, if any."""
    report = ROOT / "docs/v11/TEST_RESULTS.md"
    try:
        content = report.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"Installed Blender discovery / H1 mesh render\s*\|\s*PASS\s*\|\s*"
                      r"Windows Blender ([^;]+);", content)
    if not match:
        return None
    return {"status": "READY", "version": match.group(1).strip(),
            "evidence": "docs/v11/TEST_RESULTS.md: Installed Blender discovery / H1 mesh render"}


def inspect() -> dict:
    release = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            key, _, value = line.partition("=")
            release[key] = value.strip('"')
    except OSError:
        pass
    wsl_text = ""
    try:
        wsl_text = Path("/proc/version").read_text().lower()
    except OSError:
        pass
    py = {"status": "READY" if sys.version_info >= (3, 12) and sys.version_info < (3, 13)
          else "UNSUPPORTED", "version": platform.python_version()}
    uv = _command("uv", ["--version"])
    manim_runner = os.environ.get("V11_MANIM_BIN", "uv run manim").split()
    try:
        manim = subprocess.run([*manim_runner, "--version"], capture_output=True, text=True,
                               timeout=30, check=True)
        manim_info = {"status": "READY", "version": next(
            (line.strip() for line in (manim.stdout + manim.stderr).splitlines()
             if "Manim Community v" in line), "version available")}
    except (OSError, subprocess.SubprocessError) as exc:
        manim_info = {"status": "BLOCKED", "reason": str(exc)}
    blender_info = _command("blender", ["--version"])
    if blender_info["status"] != "READY":
        try:
            from core.mechanism.renderer import _blender_binary
            executable = _blender_binary()
            result = subprocess.run([executable, "--version"], capture_output=True,
                                    text=True, timeout=25, check=True)
            blender_info = {"status": "READY", "path": executable,
                            "version": result.stdout.splitlines()[0]}
        except (OSError, subprocess.SubprocessError, FileNotFoundError) as exc:
            blender_info = {"status": "OPTIONAL_MISSING", "installed": False,
                            "reason": str(exc)}
            try:
                executable = _blender_binary()
                if Path(executable).is_file():
                    blender_info = {"status": "BLOCKED", "installed": True,
                        "path": executable, "version": None,
                        "reason": "Blender is installed, but this process cannot launch it. "
                                  "On WSL, Windows Blender may require the approved host-execution route."}
                    host_evidence = _recorded_blender_host_evidence()
                    if host_evidence:
                        blender_info["host_execution_evidence"] = host_evidence
            except (OSError, FileNotFoundError):
                pass
    vcan = {"status": "OPTIONAL_MISSING", "interface": None}
    ip = shutil.which("ip")
    if ip:
        try:
            result = subprocess.run([ip, "-details", "link", "show"], capture_output=True,
                                    text=True, timeout=5)
            if result.returncode:
                vcan = {"status": "BLOCKED", "reason": result.stderr.strip() or
                        f"ip returned {result.returncode}; Linux network administration permission may be required"}
            else:
                for row in result.stdout.splitlines():
                    if ": vcan" in row:
                        vcan = {"status": "READY", "interface": row.split(":", 2)[1].strip().split("@", 1)[0]}
                        break
        except (OSError, subprocess.SubprocessError) as exc:
            vcan = {"status": "BLOCKED", "reason": str(exc)}
    checks = {key: {module: _distribution(*spec) for module, spec in items.items()}
              for key, items in GROUPS.items()}
    optional = {"pybamm": _distribution("pybamm", "pybamm"),
                "renode": _command("renode"), "socketcan_vcan": vcan}
    group_status = {key: "READY" if all(item["status"] == "READY" for item in row.values())
                    else "OPTIONAL_MISSING" for key, row in checks.items()}
    memory = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                memory = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    disk = shutil.disk_usage(Path(__file__).resolve().parents[1])
    return {"platform": {"system": platform.system(), "distribution": release.get("PRETTY_NAME", "unknown"),
                         "architecture": platform.machine(), "wsl": "microsoft" in wsl_text,
                         "memory_bytes": memory,
                         "disk_free_bytes": disk.free},
            "python": py, "uv": uv,
            "groups": group_status, "packages": checks,
            "manim": manim_info, "ffmpeg": _command("ffmpeg", ["-version"]),
            "blender": blender_info, "optional": optional}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", choices=("all", *GROUPS), default="all")
    args = parser.parse_args()
    report = inspect()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.check == "all":
        status = [report["python"]["status"], report["manim"]["status"],
                  report["ffmpeg"]["status"], *report["groups"].values()]
    else:
        status = [report["groups"][args.check]]
    return 1 if any(value in {"BLOCKED", "UNSUPPORTED"} for value in status) else 0


if __name__ == "__main__":
    raise SystemExit(main())
