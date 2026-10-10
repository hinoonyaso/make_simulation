from __future__ import annotations
import copy
import json
import multiprocessing
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from core.mechanism.execution_cache import execute_cached, execution_request
from core.mechanism.run_management import canonical_hash, file_hash, make_run_identity
from core.mechanism.timeline import build_timeline
from core.mechanism.adapters.mujoco_arm import MuJoCoArmAdapter
from core.mechanism.adapters.object_detection import ObjectDetectionAdapter, SCHEMA


class FixtureAdapter:
    """Synthetic executor for process reservation tests, explicitly not inference."""
    def __init__(self, marker): self.marker=Path(marker)
    def prepare(self, request): return request.options
    def validate(self, trace): return []
    def execute(self, config):
        with self.marker.open('a') as f: f.write('execute\n')
        time.sleep(.12)
        return {'model':{'source_sha256':file_hash(Path(config['model']))}, 'samples':[]}


def worker(root, config, marker, queue):
    try:
        _, report=execute_cached('robot_kinematics',config,FixtureAdapter(marker),Path(root))
        queue.put(report['cache_status'])
    except Exception as e: queue.put(str(e))


class ExecutionCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.bundle=self.root/'bundle'; (self.bundle/'mjcf').mkdir(parents=True)
        self.model=self.bundle/'mjcf/h1.xml';self.model.write_text('<mujoco/>')
        self.config={'model':str(self.model)}
        self.cache=self.root/'executions'

    def fake(self):
        return FixtureAdapter(self.root/'calls')

    def test_actual_h1_adapter_execute_called_once_then_zero(self):
        adapter=MuJoCoArmAdapter()
        with patch.object(adapter,'execute',wraps=adapter.execute) as execute:
            a,first=execute_cached('robot_kinematics',{},adapter,self.cache)
            b,second=execute_cached('robot_kinematics',{},adapter,self.cache)
            self.assertEqual(execute.call_count,1)
            self.assertEqual(first['cache_status'],'MISS');self.assertEqual(second['adapter_execute_calls'],0)
            self.assertEqual(a,b)

    def test_yolo_adapter_spy_skips_second_inference(self):
        image=self.root/'image';image.write_bytes(b'image')
        weights=self.root/'weights';weights.write_bytes(b'mock-checkpoint')
        config={'image':str(image),'model':str(weights)}
        sha=file_hash(weights)
        trace={'schema':SCHEMA,'source':'Ultralytics YOLO11n image inference; class-aware NMS trace replay',
               'input_image':{'path':str(image),'sha256':file_hash(image)},'model':{'sha256':sha},
               'thresholds':{'confidence':.25,'iou':.45,'trace_display_floor':.05},
               'candidates':[],'confidence_pass_ids':[],'nms_steps':[],'kept_ids':[],
               'model_final_detections':[], 'visualization_candidate_ids':[]}
        adapter=ObjectDetectionAdapter()
        with patch('core.mechanism.adapters.object_detection.SUPPORTED_YOLO11N_SHA256',sha), patch.object(adapter,'execute',return_value=trace) as spy:
            _,first=execute_cached('object_detection',config,adapter,self.cache)
            _,second=execute_cached('object_detection',config,adapter,self.cache)
            self.assertEqual(spy.call_count,1)
            self.assertEqual(first['adapter_execute_calls'],1);self.assertEqual(second['adapter_execute_calls'],0)

    def test_execution_identity_changes_for_image_weights_parameters_and_runtime(self):
        image=self.root/'image';image.write_bytes(b'image')
        config={'image':str(image),'model':str(self.model)}
        first,_=execution_request('object_detection',config)
        image.write_bytes(b'changed')
        second,_=execution_request('object_detection',config)
        self.assertNotEqual(first['execution_id'],second['execution_id'])
        self.model.write_text('new weights')
        third,_=execution_request('object_detection',config)
        self.assertNotEqual(second['execution_id'],third['execution_id'])
        a,_=execution_request('robot_kinematics',self.config)
        b,_=execution_request('robot_kinematics',{**self.config,'duration':4})
        self.assertNotEqual(a['execution_id'],b['execution_id'])
        with patch('core.mechanism.execution_cache._version',return_value='different'):
            c,_=execution_request('robot_kinematics',self.config)
        self.assertNotEqual(a['execution_id'],c['execution_id'])

    def test_same_bytes_at_new_path_reuses_execution(self):
        adapter=self.fake()
        _,first=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        other=self.root/'other/mjcf';other.mkdir(parents=True)
        model=other/'h1.xml';model.write_bytes(self.model.read_bytes())
        self.model.unlink()
        _,second=execute_cached('robot_kinematics',{'model':str(model)},adapter,self.cache)
        self.assertEqual(second['cache_status'],'HIT')
        self.assertEqual((self.root/'calls').read_text().count('execute'),1)

    def test_timeline_renderer_resolution_changes_only_render_identity(self):
        adapter=self.fake()
        trace,first=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        _,second=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        self.assertEqual(second['cache_status'],'HIT')
        a=build_timeline([{'phase_id':'x','sec':1}]);b=build_timeline([{'phase_id':'x','sec':2}])
        def identity(renderer,tl):
            return make_run_identity(topic='robot_kinematics',config={},trace=trace,mode='executable',renderer=renderer,timeline=tl)['run_id']
        ref=identity('manim:preview',a)
        for renderer,tl in (('manim:preview',b),('blender:preview',a),('manim:final',a)):
            self.assertNotEqual(ref,identity(renderer,tl))
            _,hit=execute_cached('robot_kinematics',self.config,adapter,self.cache)
            self.assertEqual(hit['adapter_execute_calls'],0)

    def test_render_code_does_not_enter_execution_fingerprint(self):
        first,_=execution_request('robot_kinematics',self.config)
        from core.mechanism import execution_cache
        original=execution_cache.file_hash
        def altered(path):
            return 'different' if 'manim_scene' in str(path) else original(path)
        with patch.object(execution_cache,'file_hash',side_effect=altered):
            second,_=execution_request('robot_kinematics',self.config)
        self.assertEqual(first,second)

    def test_corrupt_trace_and_incomplete_reservation_rejected(self):
        adapter=self.fake();_,first=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        path=Path(first['directory']); original=(path/'trace.json').read_bytes()
        (path/'trace.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'REJECTED'):
            execute_cached('robot_kinematics',self.config,adapter,self.cache)
        (path/'trace.json').write_bytes(original)
        (path/'execution_report.json').unlink()
        with self.assertRaisesRegex(ValueError,'REJECTED'):
            execute_cached('robot_kinematics',self.config,adapter,self.cache)
        self.assertEqual((self.root/'calls').read_text().count('execute'),1)

    def test_domain_validation_runs_on_cache_hit(self):
        adapter=self.fake();execute_cached('robot_kinematics',self.config,adapter,self.cache)
        adapter.validate=Mock(return_value=['domain corruption'])
        with self.assertRaisesRegex(ValueError,'domain corruption'):
            execute_cached('robot_kinematics',self.config,adapter,self.cache)
        adapter.validate.assert_called_once()

    def test_force_preserves_completed_and_failed_results(self):
        adapter=self.fake();_,first=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        report=(Path(first['directory'])/'execution_report.json').read_bytes()
        _,forced=execute_cached('robot_kinematics',self.config,adapter,self.cache,force=True)
        self.assertNotEqual(first['directory'],forced['directory'])
        self.assertEqual((Path(first['directory'])/'execution_report.json').read_bytes(),report)
        _,hit=execute_cached('robot_kinematics',self.config,adapter,self.cache)
        self.assertEqual(hit['cache_status'],'HIT')

    def test_parallel_processes_reserve_only_one_execution(self):
        context=multiprocessing.get_context('fork');queue=context.Queue()
        jobs=[context.Process(target=worker,args=(self.cache,self.config,self.root/'calls',queue)) for _ in range(2)]
        for job in jobs: job.start()
        for job in jobs: job.join(10);self.assertEqual(job.exitcode,0)
        self.assertEqual(sorted([queue.get(timeout=1),queue.get(timeout=1)]),['HIT','MISS'])
        self.assertEqual((self.root/'calls').read_text().count('execute'),1)

    def test_failed_execution_kept_and_lock_released(self):
        adapter=self.fake();adapter.execute=Mock(side_effect=RuntimeError('crash'))
        with self.assertRaisesRegex(RuntimeError,'crash'):
            execute_cached('robot_kinematics',self.config,adapter,self.cache)
        with self.assertRaisesRegex(ValueError,'REJECTED'):
            execute_cached('robot_kinematics',self.config,self.fake(),self.cache,lock_timeout=.1)
        _,report=execute_cached('robot_kinematics',self.config,self.fake(),self.cache,force=True)
        self.assertEqual(report['cache_status'],'FORCED')
