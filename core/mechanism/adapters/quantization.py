"""Reference integer quantization calculations for educational traces."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


def quantize_array(values: np.ndarray, bits: int, scheme: str, granularity: str) -> dict[str, Any]:
    if values.ndim not in {1, 2} or not values.size or not np.isfinite(values).all():
        raise ValueError("quantization input must be a non-empty finite 1D or 2D array")
    if granularity == "per_channel" and values.ndim != 2:
        raise ValueError("per_channel requires a 2D tensor; rows are output channels")
    signed = scheme == "symmetric"
    qmin, qmax = (-(2 ** (bits - 1)) + 1, 2 ** (bits - 1) - 1) if signed else (0, 2**bits - 1)
    reduction_axes = None if granularity == "per_tensor" else tuple(range(1, values.ndim))
    if signed:
        bound = np.max(np.abs(values), axis=reduction_axes, keepdims=granularity == "per_channel")
        scale = np.where(bound > 0, bound / qmax, 1.0)
        zero_point = np.zeros_like(scale, dtype=np.int64)
    else:
        low = np.min(values, axis=reduction_axes, keepdims=granularity == "per_channel")
        high = np.max(values, axis=reduction_axes, keepdims=granularity == "per_channel")
        scale = np.where(high > low, (high - low) / (qmax - qmin), 1.0)
        zero_point = np.clip(np.rint(qmin - low / scale), qmin, qmax).astype(np.int64)
    quantized = np.clip(np.rint(values / scale + zero_point), qmin, qmax).astype(np.int64)
    restored = (quantized - zero_point) * scale
    error = np.abs(values - restored)
    relative = np.divide(error, np.abs(values), out=np.zeros_like(error), where=values != 0)
    return {"qmin": qmin, "qmax": qmax, "scale": np.asarray(scale).tolist(),
            "zero_point": np.asarray(zero_point).tolist(), "original": values.tolist(),
            "quantized_integer": quantized.tolist(), "dequantized": restored.tolist(),
            "absolute_error": error.tolist(), "relative_error": relative.tolist(),
            "max_absolute_error": float(error.max())}


class QuantizationAdapter:
    def __init__(self, capability: dict[str, Any] | None = None):
        self.capability = capability or {}

    def describe_capability(self):
        return self.capability

    def prepare(self, request: MechanismRequest):
        return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        weights = np.asarray(config.get("weights", [-1.0, -0.73, -0.2, 0.0, 0.24, 0.61, 1.0]), dtype=np.float64)
        bits = int(config.get("bits", 8))
        if bits not in {4, 8}:
            raise ValueError("bits must be 4 or 8")
        scheme = str(config.get("scheme", "symmetric"))
        granularity = str(config.get("granularity", "per_tensor"))
        if scheme not in {"symmetric", "asymmetric"}:
            raise ValueError("scheme must be symmetric or asymmetric")
        if granularity not in {"per_tensor", "per_channel"}:
            raise ValueError("granularity must be per_tensor or per_channel")
        scope = str(config.get("scope", "weight_only"))
        if scope not in {"weight_only", "weight_and_activation"}:
            raise ValueError("scope must be weight_only or weight_and_activation")
        if scope == "weight_and_activation" and "activations" not in config:
            raise ValueError("weight_and_activation scope requires an activations tensor")

        weight = quantize_array(weights, bits, scheme, granularity)
        activation = None
        if scope == "weight_and_activation":
            activation = quantize_array(np.asarray(config["activations"], dtype=np.float64),
                                       bits, scheme, granularity)
        payload = {"bits": bits, "scheme": scheme, "granularity": granularity,
                   "scope": scope, **weight, "activation_quantization": activation,
                   "hardware_kernel_executed": False}
        inputs = [{"id": "weights", "shape": list(weights.shape), "dtype": "float64",
                   "value": weights.tolist()}]
        operations = [{"id": "quantize_weights", "scheme": scheme, "bits": bits,
                       "scale": weight["scale"], "zero_point": weight["zero_point"]},
                      {"id": "dequantize_weights_and_compare",
                       "max_absolute_error": weight["max_absolute_error"]}]
        outputs = [{"id": "restored_weights", "value": weight["dequantized"]}]
        if activation is not None:
            values = np.asarray(config["activations"], dtype=np.float64)
            inputs.append({"id": "activations", "shape": list(values.shape), "dtype": "float64",
                           "value": values.tolist()})
            operations.extend([
                {"id": "quantize_activations", "scheme": scheme, "bits": bits,
                 "scale": activation["scale"], "zero_point": activation["zero_point"]},
                {"id": "dequantize_activations_and_compare",
                 "max_absolute_error": activation["max_absolute_error"]},
            ])
            outputs.append({"id": "restored_activations", "value": activation["dequantized"]})
        return make_envelope(domain="ai_deep_learning", topic="quantization",
            execution_type="numerical_simulation", inputs=inputs, operations=operations,
            outputs=outputs, payload=payload,
            provenance={"backend": "NumPy reference arithmetic", "hardware_execution": False},
            limitations=["No accelerator, packed INT4 kernel, model inference, or quality benchmark was run."])

    def validate(self, trace):
        errors = validate_envelope(trace)
        payload = trace.get("payload", {})
        try:
            for name, item in (("weights", payload), ("activations", payload.get("activation_quantization"))):
                if item is None:
                    continue
                original = np.asarray(item["original"], dtype=float)
                quantized = np.asarray(item["quantized_integer"], dtype=float)
                restored = np.asarray(item["dequantized"], dtype=float)
                scale = np.asarray(item["scale"], dtype=float)
                zero = np.asarray(item["zero_point"], dtype=float)
                if (original.shape != quantized.shape or original.shape != restored.shape or
                        not np.allclose((quantized - zero) * scale, restored)):
                    errors.append(f"{name} quantization shape or dequantization equation mismatch")
                if not np.isfinite(original).all() or not np.isfinite(restored).all():
                    errors.append(f"{name} quantization contains non-finite values")
            if payload.get("scope") == "weight_and_activation" and payload.get("activation_quantization") is None:
                errors.append("weight_and_activation scope is missing activation results")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid quantization payload: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        activation = p.get("activation_quantization")
        return {"kind": "quantization", "original": p["original"], "quantized": p["quantized_integer"],
                "dequantized": p["dequantized"], "bits": p["bits"], "scheme": p["scheme"],
                "scale": p["scale"], "zero_point": p["zero_point"], "scope": p["scope"],
                "max_absolute_error": p["max_absolute_error"],
                "activation_max_absolute_error": activation["max_absolute_error"] if activation else None}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
