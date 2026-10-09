"""Traceable single-head self-attention arithmetic for educational examples."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


class SelfAttentionAdapter:
    def __init__(self, capability: dict[str, Any] | None = None): self.capability = capability or {}
    def describe_capability(self): return self.capability
    def prepare(self, request: MechanismRequest): return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        tokens = np.asarray(config.get("tokens", [[1., 0.], [0., 1.], [1., 1.]]), dtype=float)
        wq = np.asarray(config.get("w_q", np.eye(tokens.shape[-1])), dtype=float)
        wk = np.asarray(config.get("w_k", np.eye(tokens.shape[-1])), dtype=float)
        wv = np.asarray(config.get("w_v", np.eye(tokens.shape[-1])), dtype=float)
        if tokens.ndim != 2 or not tokens.size or not all(np.isfinite(a).all() for a in (tokens,wq,wk,wv)):
            raise ValueError("tokens and projection matrices must be finite 2D arrays")
        d = tokens.shape[1]
        if any(a.shape != (d,d) for a in (wq,wk,wv)):
            raise ValueError("W_Q, W_K and W_V must be square matrices matching token width")
        q, k, v = tokens @ wq, tokens @ wk, tokens @ wv
        raw = q @ k.T
        scaled = raw / np.sqrt(d)
        mask_future = bool(config.get("causal_mask", False))
        mask = np.triu(np.ones_like(scaled, dtype=bool), k=1) if mask_future else np.zeros_like(scaled, dtype=bool)
        logits = np.where(mask, -np.inf, scaled)
        shifted = logits - np.max(logits, axis=1, keepdims=True)
        exp = np.exp(shifted)
        weights = exp / exp.sum(axis=1, keepdims=True)
        output = weights @ v
        payload = {"tokens": tokens.tolist(), "w_q":wq.tolist(), "w_k":wk.tolist(), "w_v":wv.tolist(),
                   "q":q.tolist(), "k":k.tolist(), "v":v.tolist(), "raw_scores":raw.tolist(),
                   "scaled_scores":scaled.tolist(), "causal_mask":mask.tolist(),
                   "attention_weights":weights.tolist(), "output":output.tolist(),
                   "scale_factor":float(np.sqrt(d)), "causal_mask_enabled":mask_future,
                   "model_inference_executed":False}
        trace=make_envelope(domain="ai_deep_learning", topic="self_attention", execution_type="numerical_simulation",
            inputs=[{"id":"token_vectors","shape":list(tokens.shape),"value":tokens.tolist()}],
            operations=[{"id":"qkv_projection"},{"id":"query_key_dot_product","value":raw.tolist()},
                       {"id":"scale","divisor":float(np.sqrt(d))},{"id":"mask","causal":mask_future},
                       {"id":"row_softmax","value":weights.tolist()},{"id":"weighted_value_sum","value":output.tolist()}],
            outputs=[{"id":"context_vectors","value":output.tolist()}],payload=payload,
            provenance={"backend":"NumPy single-head self-attention reference arithmetic","model_execution":False},
            limitations=["Educational single-head arithmetic only; no Transformer model, tokenizer, trained weights, or inference runtime was executed."])
        return trace

    def validate(self, trace):
        errors=validate_envelope(trace)
        if trace.get("topic") != "self_attention" or trace.get("domain") != "ai_deep_learning":
            errors.append("self-attention trace domain/topic mismatch")
        try:
            p=trace["payload"]; tokens=np.asarray(p["tokens"],float); d=tokens.shape[1]
            q,k,v=(tokens@np.asarray(p[name],float) for name in ("w_q","w_k","w_v"))
            raw=q@k.T; scaled=raw/np.sqrt(d); mask=np.asarray(p["causal_mask"],bool)
            expected_mask=np.triu(np.ones_like(scaled,dtype=bool),k=1) if p["causal_mask_enabled"] else np.zeros_like(scaled,dtype=bool)
            if mask.shape != scaled.shape or not np.array_equal(mask,expected_mask): errors.append("attention mask does not match the configured causal-mask mode")
            logits=np.where(mask,-np.inf,scaled); exp=np.exp(logits-np.max(logits,axis=1,keepdims=True)); weights=exp/exp.sum(axis=1,keepdims=True)
            for name,got,want in (("q",p["q"],q),("k",p["k"],k),("v",p["v"],v),
                    ("raw_scores",p["raw_scores"],raw),("scaled_scores",p["scaled_scores"],scaled),
                    ("attention_weights",p["attention_weights"],weights),("output",p["output"],weights@v)):
                if not np.allclose(np.asarray(got,float),want,rtol=1e-9,atol=1e-10): errors.append(f"attention {name} does not match its recorded computation")
            if np.any(mask & (weights != 0)): errors.append("masked attention positions must have zero weight")
            if not np.allclose(weights.sum(axis=1),1): errors.append("attention weights must sum to one per query")
        except (KeyError,TypeError,ValueError,IndexError) as exc: errors.append(f"invalid attention trace: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p=trace["payload"]
        return {"kind":"self_attention","tokens":p["tokens"],"raw_scores":p["raw_scores"],
                "scaled_scores":p["scaled_scores"],"attention_weights":p["attention_weights"],
                "v":p["v"],"output":p["output"],"scale_factor":p["scale_factor"],"causal_mask":p["causal_mask"]}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan,Path(manifest["_path"]),output,manifest.get("render_mode","preview"))
