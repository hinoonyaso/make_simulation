import json,subprocess
from pathlib import Path
from model import reference_distance,heuristic,neighbors
R=Path(__file__).resolve().parent;O=R/'output';D=json.loads((O/'trace.json').read_text());A=json.loads((R/'assets/audio/manifest.json').read_text())
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(O/'astar_education_ko.mp4')]))
v=next(s for s in p['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1');assert any(s['codec_type']=='audio' for s in p['streams']);assert abs(float(p['format']['duration'])-A[-1]['end'])<.1;assert len(p['chapters'])==8
cues=json.loads((O/'caption_timing.json').read_text());assert len(cues)==len(A)==25
for cue,a in zip(cues,A):assert a['start']<=cue['start']<cue['end']<=a['end'] and cue['timing_source']=='whisper'
assert D['astar']['cost']==D['dijkstra']['cost']==reference_distance()==16
for row in D['astar']['rows']:
 assert row['f']==row['g']+row['h']==min(c['f'] for c in row['candidates'])
 assert row['h']==heuristic(row['current'])
 assert not set(map(tuple,row['open']))&set(map(tuple,row['closed']))
for a,b in zip(D['astar']['path'],D['astar']['path'][1:]):assert tuple(b) in neighbors(tuple(a))
events=json.loads((O/'render_events.json').read_text());previous=-1
for event in events:
 assert previous<=event['video_time']<A[-1]['end'];previous=event['video_time']
 source=D['dijkstra'] if event['chapter']==1 else D['astar'];row=source['rows'][event['search_step']];assert row['current']==event['current'] and row['f']==event['f']
subprocess.run(['ffmpeg','-v','error','-i',str(O/'astar_education_ko.mp4'),'-f','null','-'],check=True)
report=dict(status='passed',video='full decode',duration_seconds=float(p['format']['duration']),resolution=[1920,1080],fps=30,caption_cues=25,chapters=8,recorded_visual_events=len(events),metrics=D['metrics'],limits='one static unit-cost grid; no Nav2 execution or physical robot motion')
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
