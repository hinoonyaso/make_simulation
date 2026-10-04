import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'
def main():
 file=OUT/'pixel_depth_simulation_ko_v3.mp4'
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)]))
 video=next(s for s in info['streams'] if s['codec_type']=='video');audio=next(s for s in info['streams'] if s['codec_type']=='audio')
 trace=json.loads((OUT/'trace.json').read_text());timeline=json.loads((OUT/'render_timeline.json').read_text());cues=json.loads((OUT/'caption_timing.json').read_text())
 assert (video['width'],video['height'],video['r_frame_rate'])==(1920,1080,'30/1')
 assert int(video['nb_frames'])==trace['frame_count']
 assert abs(float(video['duration'])-float(audio['duration']))<.1
 assert max(abs(r['render_end']-r['end']) for r in timeline)<1/30+.001
 assert all(0<=c['start']<c['end']<=float(video['duration']) for c in cues)
 assert json.loads((OUT/'model_validation.json').read_text())['status']=='passed'
 assert json.loads((OUT/'blender/saved_project_validation.json').read_text())['status']=='passed'
 subprocess.run(['ffmpeg','-v','error','-i',str(file),'-f','null','-'],check=True)
 report=dict(status='passed',duration_s=float(video['duration']),frames=int(video['nb_frames']),resolution=[1920,1080],fps=30,captions=len(cues),full_decode='passed',model='passed',saved_blender='passed',timeline_max_error_s=max(abs(r['render_end']-r['end']) for r in timeline))
 (OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
