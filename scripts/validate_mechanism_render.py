#!/usr/bin/env python3
"""Technical media/trace/timeline gate; does not claim visual or educational QA."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.mechanism.run_management import canonical_hash, file_hash, media_metadata, validate_replay_trace
from core.mechanism.timeline import validate_timeline, source_time_for_frame, phase_playback
from core.mechanism.registry import MechanismRegistry
from core.mechanism.pid_playback import PIDPlayback


def validate(report_path, pid_frames=None):
    report=json.loads(Path(report_path).read_text())
    timeline=json.loads(Path(report['timeline']).read_text())
    trace=json.loads(Path(report['trace']).read_text())
    spec=report['identity']['render_spec']
    adapter=MechanismRegistry().load_adapter(report['topic'])
    errors=adapter.validate(trace)+validate_timeline(timeline,expected_phase_ids=report['storyboard_phase_ids'])
    if errors: raise ValueError('; '.join(errors))
    if canonical_hash(trace)!=report['identity']['trace_hash']: raise ValueError('trace hash mismatch')
    if timeline['timeline_sha256']!=report['identity']['timeline_hash']: raise ValueError('timeline identity mismatch')
    if timeline['timeline_sha256']!=report['timeline_sha256']: raise ValueError('timeline report mismatch')
    if report['renderer']!=report['identity']['renderer'].split(':')[0]: raise ValueError('renderer mismatch')
    media=Path(report['media'])
    if file_hash(media)!=report['media_sha256']: raise ValueError('media hash mismatch')
    subprocess.run([sys.executable,str(ROOT/'scripts/validate_delivery.py'),str(media),
        '--min-width',str(spec['width']),'--min-height',str(spec['height']),'--fps',str(spec['fps']),'--full-decode'],check=True)
    metadata=media_metadata(media)
    if metadata['frame_count']!=timeline['total_frames']: raise ValueError('frame count mismatch')
    checks={'topic':report['topic'],'frames':metadata['frame_count'],'full_decode':'PASS',
            'trace_sha256':file_hash(Path(report['trace'])),'timeline_sha256':timeline['timeline_sha256'],
            'visual_review':'NOT_RUN','motion_playback_review':'NOT_RUN'}
    if report['topic']=='robot_kinematics' and report['renderer']=='blender_h1_trace_playback':
        payload=json.loads((Path(report_path).parent/'blender_backend/blender_payload.json').read_text())
        if payload['trace_sha256']!=file_hash(Path(report['trace'])): raise ValueError('H1 payload trace mismatch')
        phases={p['phase_id']:phase_playback(timeline,p) for p in timeline['phases']}
        if report['renderer_details']['phase_playback']!=payload['phase_playback']: raise ValueError('H1 playback report mismatch')
        for i,frame in enumerate(payload['frames']):
            phase,source=source_time_for_frame(timeline,i)
            if (frame['phase_id']!=phase or frame['source_time_sec']!=source or
                frame['playback_speed']!=phases[phase]['playback_speed'] or frame['playback_state']!=phases[phase]['playback_state']):
                raise ValueError(f'H1 frame {i} mapping mismatch')
        checks['H1_export_frame_mapping']='PASS'
    if pid_frames:
        frames=json.loads(Path(pid_frames).read_text())
        player=PIDPlayback(trace['payload'],timeline)
        if len(frames)!=timeline['total_frames']: raise ValueError('PID renderer debug frame count mismatch')
        for i,frame in enumerate(frames):
            if frame!=player.state(i): raise ValueError(f'PID displayed state mismatch at frame {i}')
        checks['PID_render_update_sample_mapping']='PASS'
    return checks


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path);p.add_argument('--pid-frames',type=Path)
    args=p.parse_args()
    print(json.dumps(validate(args.report,args.pid_frames),ensure_ascii=False,indent=2))
