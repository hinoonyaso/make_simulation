"""Motion evidence for scalar joints; fixed-base H1 positions are radians.

Noise is filtered by a deadband, never by comparing only trajectory endpoints.
Continuous coordinates are unwrapped ONLY when metadata explicitly declares a
wrapped recording. Unwrapped multi-turn recordings retain their full travel.
"""
from __future__ import annotations
import numpy as np


def analyze_joint_motion(trace: dict, model_metadata: dict | None = None) -> dict:
    rows = trace.get('samples', [])
    if not rows:
        raise ValueError('joint motion requires samples')
    try:
        q = np.asarray([s['qpos'] for s in rows], dtype=float)
        t = np.asarray([s['t'] for s in rows], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('invalid joint shape or timestamp') from exc
    if q.ndim != 2 or q.shape[1] == 0 or not np.isfinite(q).all() or not np.isfinite(t).all():
        raise ValueError('joint positions/timestamps must be finite with consistent shape')
    if np.any(np.diff(t) <= 0):
        raise ValueError('joint timestamps must strictly increase')
    meta = model_metadata or trace.get('model', {})
    names = meta.get('joint_names_in_qpos_order', [f'joint_{i}' for i in range(q.shape[1])])
    kinds = meta.get('joint_types', ['revolute'] * q.shape[1])
    if len(names) != q.shape[1] or len(kinds) != q.shape[1]:
        raise ValueError('joint metadata does not match qpos order/shape')
    if any(k not in {'revolute', 'continuous', 'prismatic'} for k in kinds):
        raise ValueError('motion analyzer supports scalar revolute/continuous/prismatic joints only')
    thresholds = np.array([0.0001 if k == 'prismatic' else 0.001 for k in kinds])
    # Conservative anomaly guard, not a hardware velocity specification.
    speed_limits = np.array([5.0 if k == 'prismatic' else 30.0 for k in kinds])
    wrapped = meta.get('wrapped_joint_names', [])
    for j, (name, kind) in enumerate(zip(names, kinds)):
        if name in wrapped:
            if kind != 'continuous':
                raise ValueError('wrapped coordinates must identify continuous joints')
            q[:, j] = np.unwrap(q[:, j])
    peak_qvel = None
    if any('qvel' in row for row in rows):
        try:
            v = np.asarray([row['qvel'] for row in rows], dtype=float)
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError('invalid qvel samples') from exc
        if v.shape != q.shape or not np.isfinite(v).all():
            raise ValueError('qvel must be finite and match scalar joint shape')
        peak_qvel = np.max(np.abs(v), axis=0).tolist()
    filtered = q.copy()
    outliers = []
    for i in range(1, len(t)-1):
        for j in range(q.shape[1]):
            before = q[i,j]-q[i-1,j]; after = q[i+1,j]-q[i,j]
            if (before * after < 0 and abs(q[i+1,j]-q[i-1,j]) <= thresholds[j]
                    and abs(before)/(t[i]-t[i-1]) > speed_limits[j]
                    and abs(after)/(t[i+1]-t[i]) > speed_limits[j]):
                filtered[i,j] = q[i-1,j]
                outliers.append({'sample_index': i, 'joint': names[j]})
    displacement = np.max(np.abs(filtered-filtered[0]), axis=0)
    travel = np.zeros(q.shape[1]); anchor = filtered[0].copy()
    active_duration = np.zeros(q.shape[1])
    for i in range(1, len(t)):
        delta = np.abs(filtered[i]-anchor)
        active = delta > thresholds
        travel += np.where(active, delta, 0)
        active_duration += np.where(active, t[i]-t[i-1], 0)
        anchor = np.where(active, filtered[i], anchor)
    active = (displacement > thresholds) & (travel > thresholds)
    return {'motion_detected': bool(np.any(active)), 'active_joint_count': int(np.sum(active)),
            'max_displacement': displacement.tolist(), 'cumulative_travel': travel.tolist(),
            'threshold': thresholds.tolist(), 'units': ['m' if k == 'prismatic' else 'rad' for k in kinds],
            'joint_names': names, 'active_duration_sec': active_duration.tolist(),
            'duration_sec': float(t[-1]-t[0]), 'peak_recorded_qvel': peak_qvel,
            'isolated_outliers': outliers,
            'detection_reason': ('trajectory exceeds joint-specific deadband' if np.any(active) else
                                 'stationary within deadband after isolated-spike screening')}
