"""Validated execution cache, reserved before heavyweight adapter.execute().

Linux advisory flock serializes each content identity across processes. The OS
releases reservations on crash; incomplete directories are preserved and rejected.
A forced execution is an independent sibling and never replaces a successful run.
"""
from __future__ import annotations
import copy
import fcntl
from importlib import metadata
import json
import math
import os
from pathlib import Path
import platform
import tempfile
import time
import uuid

from core.mechanism.protocol import MechanismRequest
from core.mechanism.run_management import ROOT, canonical_hash, file_hash, asset_tree_hash

SCHEMA = 'mechanism-execution-cache/v1'


def _version(name):
    try: return metadata.version(name)
    except metadata.PackageNotFoundError: return 'NOT_INSTALLED'


def execution_request(topic: str, options: dict) -> tuple[dict, dict]:
    """Cheap normalization and byte hashes; no model import/loading/simulation."""
    config = {k: v for k, v in options.items() if k not in {'topic', 'output_dir'}}
    files = []
    runtime = {'python': platform.python_version(), 'numpy': _version('numpy'),
               'platform': platform.platform(), 'machine': platform.machine()}
    if topic == 'robot_kinematics':
        allowed = {'model', 'duration', 'timestep', 'sample_period'}
        if set(config)-allowed:
            raise ValueError(f'unsupported H1 execution options: {sorted(set(config)-allowed)}')
        defaults = {'duration': 2., 'timestep': .002, 'sample_period': .02}
        model = Path(config.get('model', ROOT/'assets/unitree_h1/mjcf/h1_with_hand.xml')).resolve()
        config = {key: float(config.get(key, value)) for key, value in defaults.items()}
        if not all(math.isfinite(v) and v > 0 for v in config.values()):
            raise ValueError('H1 execution parameters must be finite and positive')
        for key in ('duration', 'sample_period'):
            ratio = config[key]/config['timestep']
            if not math.isclose(ratio, round(ratio), abs_tol=1e-9):
                raise ValueError(f'{key} must be divisible by timestep')
        config['model'] = str(model)
        source = {'model_sha256': file_hash(model), 'model_bundle_sha256': asset_tree_hash(model.parent.parent)}
        runtime['mujoco'] = _version('mujoco')
        files = ['core/mechanism/adapters/mujoco_arm.py', 'core/robotics-simulation/mujoco_adapter.py',
                 'core/shared-data/validate_trace.py']
        fixed = {'seed': None, 'randomness': 'none; deterministic zero initial state',
                 'controller': 'fixed-base H1 PD; constants and target trajectory covered by code hash',
                 'solver': 'MJCF solver covered by model hash'}
    elif topic == 'object_detection':
        allowed = {'image','model','confidence_threshold','iou_threshold','trace_display_floor','imgsz','display_limit'}
        if set(config)-allowed:
            raise ValueError(f'unsupported YOLO execution options: {sorted(set(config)-allowed)}')
        defaults = {'confidence_threshold': .25,'iou_threshold': .45,'trace_display_floor': .05,
                    'imgsz': 640,'display_limit': 12}
        normalized = {k: type(v)(config.get(k,v)) for k,v in defaults.items()}
        if not (0 <= normalized['trace_display_floor'] <= normalized['confidence_threshold'] <= 1
                and 0 <= normalized['iou_threshold'] <= 1 and normalized['imgsz'] >= 32 and normalized['display_limit'] >= 1):
            raise ValueError('invalid YOLO thresholds/image size/display limit')
        normalized.update({k: str(Path(config[k]).resolve()) for k in ('image','model')})
        config = normalized
        source = {'image_sha256': file_hash(Path(config['image'])), 'model_sha256': file_hash(Path(config['model']))}
        runtime.update({k: _version(k) for k in ('ultralytics','torch','torchvision','Pillow','opencv-python')})
        files = ['core/mechanism/adapters/object_detection.py','scripts/run_yolo_inference.py']
        fixed = {'seed': 0,'device': 'cpu','half': False,'rect': False,'max_det': 300,'agnostic_nms': False}
    else:
        raise ValueError('execution cache currently supports H1 and YOLO only')
    files += ['core/mechanism/execution_cache.py','core/mechanism/protocol.py']
    fingerprint = canonical_hash({p: file_hash(ROOT/p) for p in files})
    material = {'schema': SCHEMA, 'topic': topic, 'adapter_version': 'execution/v1',
                'normalized_config': {k:v for k,v in config.items() if k not in {'image','model'}},
                'input_provenance': source,'runtime': runtime,'fixed_execution_settings': fixed,
                'execution_code_fingerprint': fingerprint}
    return {'execution_id': canonical_hash(material), **material}, config


def _atomic_json(path: Path, value: dict):
    temporary = path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    try:
        with temporary.open('x',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,sort_keys=True,allow_nan=False)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def _bound_trace(trace, topic, config):
    # Rebind only provenance paths after byte identity is verified. Same bytes at
    # a different path may reuse execution even after the original path is gone.
    value = copy.deepcopy(trace)
    if topic == 'object_detection':
        value['input_image']['path'] = config['image']
        value['model']['checkpoint'] = config['model']
    else:
        value['model']['source_file'] = config['model']
    return value


def _validate(trace, topic, config, identity, adapter):
    source = identity['input_provenance']
    if topic == 'object_detection':
        if trace['input_image']['sha256'] != source['image_sha256'] or trace['model']['sha256'] != source['model_sha256']:
            raise ValueError('cached trace source/model provenance mismatch')
    elif trace['model']['source_sha256'] != source['model_sha256']:
        raise ValueError('cached trace model provenance mismatch')
    bound = _bound_trace(trace, topic, config)
    errors = adapter.validate(bound)
    if errors: raise ValueError('execution trace validation failed: '+'; '.join(errors))
    return bound


def execute_cached(topic: str, options: dict, adapter, root: Path, *, enabled=True,
                   force=False, lock_timeout=120.) -> tuple[dict, dict]:
    started = time.perf_counter()
    identity, config = execution_request(topic, options)
    identity_sec = time.perf_counter()-started
    folder = Path(root).resolve()/topic
    folder.mkdir(parents=True,exist_ok=True)
    base = folder/identity['execution_id']
    with (folder/('.'+identity['execution_id']+'.lock')).open('a') as lock:
        while True:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); break
            except BlockingIOError:
                if time.perf_counter()-started > lock_timeout:
                    raise TimeoutError('execution reservation is busy; no cache modified')
                time.sleep(.05)
        lookup_start = time.perf_counter()
        if enabled and not force and base.exists():
            try:
                report = json.loads((base/'execution_report.json').read_text())
                stored = json.loads((base/'trace.json').read_text())
                if (report.get('status') != 'COMPLETE' or report.get('identity') != identity
                        or report.get('trace_sha256') != file_hash(base/'trace.json')):
                    raise ValueError('incomplete execution or hash/identity mismatch')
                validate_start = time.perf_counter()
                trace = _validate(stored,topic,config,identity,adapter)
                validation_sec = time.perf_counter()-validate_start
            except (OSError,ValueError,TypeError,KeyError) as exc:
                raise ValueError(f'execution cache REJECTED: {base}: {exc}; use --force-execution to preserve it and run independently') from exc
            return trace, {'cache_status':'HIT','execution_id':identity['execution_id'],'directory':str(base),
                           'adapter_execute_calls':0,'adapter_execute_sec':0.,'model_loading_sec':0.,
                           'trace_validation_sec':validation_sec,'identity_sec':identity_sec,
                           'cache_lookup_sec':time.perf_counter()-lookup_start-validation_sec,
                           'total_sec':time.perf_counter()-started}
        directory = base if enabled and not force else folder/(identity['execution_id']+'-rerun-'+uuid.uuid4().hex[:12])
        directory.mkdir(exist_ok=False)
        _atomic_json(directory/'request.json', {'identity':identity,'normalized_config':config})
        _atomic_json(directory/'execution_report.json', {'status':'INCOMPLETE','identity':identity})
        lookup_sec = time.perf_counter()-lookup_start
        try:
            execute_start = time.perf_counter()
            with tempfile.TemporaryDirectory(prefix='v115-execution-') as temp:
                execute_config = {**config, **({'output_dir':temp} if topic == 'robot_kinematics' else {})}
                trace = adapter.execute(adapter.prepare(MechanismRequest(topic=topic,options=execute_config)))
            execute_sec = time.perf_counter()-execute_start
            # Reject mutable input races: never promote a trace against stale provenance.
            after, _ = execution_request(topic,options)
            if after != identity:
                raise ValueError('execution inputs changed while adapter was running')
            validate_start = time.perf_counter()
            trace = _validate(trace,topic,config,identity,adapter)
            validation_sec = time.perf_counter()-validate_start
            metrics = {'cache_status':'FORCED' if force else 'MISS' if enabled else 'DISABLED',
                       'execution_id':identity['execution_id'],'directory':str(directory),
                       'adapter_execute_calls':1,'adapter_execute_sec':execute_sec,
                       'model_loading_sec':getattr(adapter,'last_execution_metrics',{}).get('model_loading_sec'),
                       'trace_validation_sec':validation_sec,'identity_sec':identity_sec,'cache_lookup_sec':lookup_sec,
                       'total_sec':time.perf_counter()-started}
            _atomic_json(directory/'trace.json',trace)
            _atomic_json(directory/'execution_report.json', {'status':'COMPLETE','identity':identity,
                         'trace_sha256':file_hash(directory/'trace.json'),'metrics':metrics})
            return trace,metrics
        except BaseException:
            # Incomplete reservation remains inspectable. OS lock is released on exit/crash.
            raise
