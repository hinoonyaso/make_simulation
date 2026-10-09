"""Backend preflight. No environment is READY until a backend load test is recorded."""
from __future__ import annotations
import importlib.util
import shutil
from .registry import EnvironmentRegistry

class EnvironmentLoader:
    def __init__(self, registry=None): self.registry = registry or EnvironmentRegistry()
    @staticmethod
    def backend_status(environment):
        required = environment["required_simulator"].casefold()
        if "gazebo" in required:
            missing = [name for name in ("ros2", "gz") if shutil.which(name) is None]
        elif "sapien" in required:
            missing = ["sapien"] if importlib.util.find_spec("sapien") is None else []
        elif "mujoco" in required:
            missing = ["mujoco"] if importlib.util.find_spec("mujoco") is None else []
        else: missing = ["unregistered simulator backend"]
        return {"status": "blocked" if missing else "available_for_load_test", "missing": missing,
                "load_test_status": environment["load_test_status"], "render_test_status": environment["render_test_status"]}
    def preflight(self, env_id: str):
        env = self.registry.get(env_id)
        return {"environment": env, "backend": self.backend_status(env),
                "ready": False, "reason": "preflight does not substitute for a world load, physics run, and render validation"}
    def load(self, env_id: str, **_options):
        result = self.preflight(env_id)
        raise RuntimeError(f"environment loading is not implemented as a validated backend: {env_id}; {result['backend']}")
