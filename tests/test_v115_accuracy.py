from __future__ import annotations
import copy
import math
import unittest
from core.mechanism.joint_motion import analyze_joint_motion
from core.mechanism.timeline import build_timeline, validate_timeline, source_time_for_frame, phase_playback, timeline_hash
from core.mechanism.renderer_routing import decide_renderer
from core.mechanism.pid_playback import PIDPlayback
from core.mechanism.adapters.mcu_pid import MCUPIDAdapter
from scripts.produce_video import _build_run_timeline


def route(**kwargs):
    return decide_renderer(**{ "requested_renderer":"auto", "visual_goal":"auto", "trace":{}, **kwargs})

def joints(values, dt=1.):
    return {'samples': [{'t': i*dt, 'qpos': v if isinstance(v,list) else [v]} for i,v in enumerate(values)]}


class MotionTests(unittest.TestCase):
    def test_out_and_back_and_monotonic(self):
        for q in ([0,math.pi/3,0], [0,math.pi/3]):
            e=analyze_joint_motion(joints(q))
            self.assertTrue(e['motion_detected'])
            self.assertGreaterEqual(e['cumulative_travel'][0],math.pi/3)

    def test_stationary_and_small_noise(self):
        for q in ([0,0,0], [0,1e-5,-1e-5]*100):
            self.assertFalse(analyze_joint_motion(joints(q))['motion_detected'])

    def test_one_joint_and_multiple_joint_round_trip(self):
        for q,count in (([[0,0],[0,1],[0,0]],1), ([[0,0],[1,-1],[0,0]],2)):
            self.assertEqual(analyze_joint_motion(joints(q))['active_joint_count'],count)

    def test_isolated_implausible_spike_and_repeated_movement(self):
        e=analyze_joint_motion(joints([0,0,2,0,0],.01))
        self.assertFalse(e['motion_detected']); self.assertEqual(len(e['isolated_outliers']),1)
        self.assertTrue(analyze_joint_motion(joints([0,.02,0,.02,0],.1))['motion_detected'])

    def test_rejects_nonfinite_shape_and_time(self):
        cases=[joints([0,v]) for v in (float('nan'),float('inf'))]
        cases += [joints([[0,0],[1]]),joints([0,1],-1),joints([0,1],0)]
        for trace in cases:
            with self.subTest(trace=trace),self.assertRaises(ValueError): analyze_joint_motion(trace)
        for bad in ([float('inf')], [0,1]):
            trace=joints([0,1]); trace['samples'][0]['qvel']=bad
            trace['samples'][1]['qvel']=[0]
            with self.assertRaises(ValueError): analyze_joint_motion(trace)

    def test_prismatic_units_and_continuous_wrap(self):
        e=analyze_joint_motion(joints([[0,0],[.0005,.0005]]), {'joint_types':['revolute','prismatic']})
        self.assertEqual(e['active_joint_count'],1); self.assertEqual(e['units'],['rad','m'])
        q=joints([0,2*math.pi,4*math.pi])
        self.assertAlmostEqual(analyze_joint_motion(q,{'joint_types':['continuous']})['cumulative_travel'][0],4*math.pi)
        e=analyze_joint_motion(joints([3.13,-3.13]),{'joint_types':['continuous'], 'wrapped_joint_names':['joint_0']})
        self.assertLess(e['cumulative_travel'][0],.03)

    def test_renderer_regressions(self):
        for q,expected in (([0,1,0],'blender_h1_trace_playback'),([0,0,0],'manim')):
            decision=route(topic='robot_kinematics',trace=joints(q),preflight_result={'status':'PASS'})
            self.assertEqual(decision['selected_renderer'],expected)
            self.assertEqual(decision['motion_evidence']['motion_detected'],expected!='manim')
        for goal,expected in (('motion_3d','blender_h1_trace_playback'),('comparative_analysis','manim')):
            self.assertEqual(route(topic='robot_kinematics',trace=joints([0,1,0]),visual_goal=goal,
                preflight_result={'status':'PASS'})['selected_renderer'],expected)
        for topic in ('mcu_pid','self_attention','quantization'):
            self.assertEqual(route(topic=topic,preflight_result={'status':'PASS'})['selected_renderer'],'manim')
        for requested in ('auto','blender'):
            self.assertEqual(route(topic='robot_kinematics',trace=joints([0,1,0]),requested_renderer=requested,
                preflight_result={'status':'BLOCKED'})['status'],'BLOCKED')


class PlaybackTests(unittest.TestCase):
    def timeline(self, duration=4., fps=30, source=(0,2)):
        return build_timeline([{'phase_id':'setup','sec':1},{'phase_id':'motion','sec':duration},
                               {'phase_id':'analysis','sec':1}],fps=fps,source_range=source,phase_source={
            'setup':{'playback_mode':'hold'}, 'motion':{'playback_mode':'slow_motion'},
            'analysis':{'playback_mode':'hold_and_analysis'}})

    def test_speed_uses_only_motion_phase(self):
        for dur,speed in ((4,.5),(8,.25),(2,1.)):
            tl=self.timeline(dur)
            self.assertEqual(phase_playback(tl,tl['phases'][1])['playback_speed'],speed)
            self.assertEqual(phase_playback(tl,tl['phases'][0])['playback_state'],'hold')

    def test_boundaries_last_frame_and_reverse_replay(self):
        tl=self.timeline()
        for frame,expected in ((29,('setup',0.)),(30,('motion',0.)),(149,('motion',2.)),(150,('analysis',2.)),(179,('analysis',2.))):
            self.assertEqual(source_time_for_frame(tl,frame),expected)
        reverse=build_timeline([{'phase_id':'r','sec':4}],fps=30,source_range=(0,2),phase_source={
            'r':{'playback_mode':'replay','source_start_sec':2,'source_end_sec':0}})
        self.assertEqual(source_time_for_frame(reverse,119),('r',0.))
        self.assertEqual(phase_playback(reverse,reverse['phases'][0])['playback_speed'],-.5)

    def test_source_range_all_endpoints_and_tampering(self):
        for a,b in ((3,0),(2,-1),(-1,1),(0,3)):
            with self.assertRaises(ValueError):
                build_timeline([{'phase_id':'r','sec':4}],source_range=(0,2),phase_source={
                    'r':{'playback_mode':'replay','source_start_sec':a,'source_end_sec':b}})
        tl=self.timeline(); tl['phases'][1]['source_start_sec']=3
        tl['phases'][1]['playback_mode']='replay';tl['timeline_sha256']=timeline_hash(tl)
        self.assertTrue(validate_timeline(tl))  # stored source bounds suffice
        for value in (float('nan'),float('inf')):
            bad=self.timeline();bad['phases'][1]['source_start_sec']=value
            self.assertTrue(validate_timeline(bad))
        tl=self.timeline();tl['phases'][1]['presentation_start_sec']+=.1
        self.assertTrue(validate_timeline(tl))


class PIDFrameTests(unittest.TestCase):
    def setUp(self):
        self.trace=MCUPIDAdapter().execute({'duration':1.,'dt':.1,'target_rad_s':40})
        self.p=self.trace['payload']

    def player(self,duration=1.,fps=11):
        tl=build_timeline([{'phase_id':'response','sec':duration}],fps=fps,source_range=(0,1),
                          phase_source={'response':{'playback_mode':'replay'}})
        return PIDPlayback(self.p,tl)

    def test_first_last_and_discrete_terms_saturation(self):
        player=self.player()
        for f in range(11):
            s=player.state(f); row=self.p['samples'][f]
            self.assertEqual(s['sample_index'],f)
            for key in ('pwm_duty','encoder_count','error_rad_s','motor_speed_rad_s','encoder_speed_rad_s'):
                self.assertEqual(s[key],row[key])
            self.assertAlmostEqual(s['p_term']+s['i_term']+s['d_term'],row['raw_pwm'])
        self.assertEqual(player.state(0)['pwm_duty'],1.)
        self.assertEqual(player.state(10)['sample_time_sec'],1.)

    def test_sample_boundary_before_after_and_encoder_pwm_updates(self):
        player=self.player(fps=101)
        self.assertEqual(player.state(9)['sample_index'],0)
        self.assertEqual(player.state(10)['sample_index'],1)
        self.assertEqual(player.state(11)['sample_index'],1)
        self.assertEqual(player.state(9)['encoder_count'],0)
        self.assertGreater(player.state(10)['encoder_count'],0)
        for f in range(101):
            s=player.state(f);self.assertEqual(s['pwm_duty'],self.p['samples'][s['sample_index']]['pwm_duty'])

    def test_duration_fps_and_replay_preserve_same_samples(self):
        first=self.player(1,11);second=self.player(3,7)
        for f in (0,2,4,6,8,10):
            a=first.state(f);b=second.state(f*2)
            self.assertEqual(a['sample_index'],b['sample_index'])
            self.assertEqual(a['pwm_duty'],b['pwm_duty'])
        manifest={'beats':[{'phase_id':p,'sec':2} for p in ('setpoint','motor_response','pid_terms')]}
        tl=_build_run_timeline('mcu_pid',self.trace,manifest,'numerical_explanation')
        player=PIDPlayback(self.p,tl)
        self.assertEqual(player.state(59)['sample_index'],0)
        self.assertEqual(player.state(75)['sample_index'],player.state(135)['sample_index'])
        self.assertEqual(player.state(135)['playback_state'],'replay')

    def test_recorded_setpoint_change_is_not_interpolated(self):
        self.p['samples'][1]['target_rad_s']=5
        player=self.player(fps=101)
        self.assertEqual(player.state(9)['target_rad_s'],40)
        self.assertEqual(player.state(10)['target_rad_s'],5)

    def test_rejects_out_of_range_frames_source_and_nonfinite(self):
        player=self.player()
        for f in (-1,11,True):
            with self.assertRaises(ValueError): player.state(f)
        tl=build_timeline([{'phase_id':'response','sec':1}],source_range=(0,2),phase_source={'response':{'playback_mode':'replay'}})
        with self.assertRaises(ValueError): PIDPlayback(self.p,tl)
        for field in ('pwm_duty','encoder_speed_rad_s','time_s','error_rad_s'):
            p=copy.deepcopy(self.p);p['samples'][0][field]=float('nan')
            with self.assertRaises(ValueError): PIDPlayback(p,player.timeline)


class FinalHardeningTests(unittest.TestCase):
    def timeline(self, stored=(0., 2.), phase=(.5, 1.5), mode='replay'):
        tl = build_timeline([{'phase_id': 'motion', 'sec': 1}], source_range=(0, 2),
                            phase_source={'motion': {'playback_mode': mode}})
        tl['source_range_sec'] = list(stored)
        tl['phases'][0].update(source_start_sec=phase[0], source_end_sec=phase[1])
        tl['timeline_sha256'] = timeline_hash(tl)
        return tl

    def test_ranges_are_independent(self):
        for stored, external, phase, valid in (
            ((0, 1), (0, 2), (1.5, 1.8), False),
            ((0, 2), (0, 1), (1.5, 1.8), False),
            ((0, 2), (0, 2), (.5, 1.5), True),
            ((0, 2), (0, 2), (1.5, .5), True),
            ((0, 2), (0, 2), (2.5, .5), False),
        ):
            with self.subTest(stored=stored, external=external, phase=phase):
                errors = validate_timeline(self.timeline(stored, phase), source_range=external)
                self.assertFalse(any('sha256' in e for e in errors))
                self.assertEqual(not errors, valid, errors)

    def test_hold_and_invalid_ranges(self):
        self.assertEqual(validate_timeline(self.timeline(phase=(.5, .5), mode='hold')), [])
        self.assertTrue(validate_timeline(self.timeline(phase=(.5, .6), mode='hold')))
        for bounds in ((2, 0), (0,), (), (0, float('nan')), (0, float('inf'))):
            with self.subTest(bounds=bounds):
                self.assertTrue(validate_timeline(self.timeline(), source_range=bounds))
        for bounds in ((2, 0), (0,), ()):
            self.assertTrue(validate_timeline(self.timeline(stored=bounds)))
        for value in (float('nan'), float('inf')):
            tl = self.timeline()
            tl['source_range_sec'] = [0, value]
            self.assertTrue(any('source range' in e and 'finite' in e
                                for e in validate_timeline(tl)))

    def test_nonfinite_phase_times(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            for key in ('source_start_sec', 'source_end_sec'):
                tl = self.timeline()
                tl['phases'][0][key] = value
                # Nonfinite JSON cannot have a valid canonical hash; check the range error itself.
                errors = validate_timeline(tl)
                self.assertTrue(any(key in e and 'finite' in e for e in errors))

    def player(self):
        payload = MCUPIDAdapter().execute({'duration': 1., 'dt': .1})['payload']
        return PIDPlayback(payload, self.timeline(phase=(0, 1), stored=(0, 1)))

    def test_pid_endpoint_tolerance_never_selects_negative_index(self):
        player = self.player()
        for source, expected in ((0., 0), (-1e-10, 0), (1., 10), (1.+1e-10, 10)):
            with self.subTest(source=source):
                # Exercise the actual frame mapping, including tolerated endpoint drift.
                tl = self.timeline(stored=(0, 1), phase=(source, source), mode='hold')
                p = PIDPlayback({'samples': player.rows, 'pid': player.gains}, tl)
                state = p.state(0)
                self.assertEqual(state['sample_index'], expected)
                self.assertEqual(state['encoder_count'], player.rows[expected]['encoder_count'])
                self.assertEqual(state['pwm_duty'], player.rows[expected]['pwm_duty'])

    def test_pid_outside_tolerance_and_nonfinite(self):
        from unittest.mock import patch
        player = self.player()
        for source in (-2e-9, 1.+2e-9, float('nan'), float('inf'), -float('inf')):
            with self.subTest(source=source), patch('core.mechanism.pid_playback.source_time_for_frame',
                                                   return_value=('motion', source)):
                with self.assertRaises(ValueError):
                    player.state(0)

    def test_empty_pid_samples(self):
        with self.assertRaisesRegex(ValueError, 'requires samples'):
            PIDPlayback({'samples': [], 'pid': {}}, self.timeline())
