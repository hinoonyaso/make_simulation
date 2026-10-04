"""Validate the final Blender/Manim videos and prove audio was preserved."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(path)]))


def audio_hash(path):
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','adts','-'])
    return hashlib.sha256(data).hexdigest()


def main():
    original_hash=audio_hash(OUT/'robot_manipulator_clean_ko.mp4')
    report={'geometry':json.loads((OUT/'blender/geometry_validation.json').read_text()),
            'saved_project':json.loads((OUT/'blender/saved_project_validation.json').read_text()),'videos':[]}
    for name in ['robot_manipulator_blender_ko.mp4','robot_manipulator_blender_clean_ko.mp4']:
        path=OUT/name;data=probe(path)
        v=next(s for s in data['streams'] if s['codec_type']=='video')
        a=next(s for s in data['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',10407)
        assert abs(float(data['format']['duration'])-346.9)<.05
        assert v['codec_name']=='h264' and a['codec_name']=='aac'
        assert len(data['chapters'])==12
        assert audio_hash(path)==original_hash,'Narration changed during composition'
        result=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True)
        assert result.returncode==0 and not result.stderr,result.stderr
        report['videos'].append({'file':name,'duration':346.9,'resolution':'1920x1080',
            'fps':30,'frames':10407,'audio_bitstream_preserved':True,'full_decode':'passed','bytes':path.stat().st_size})
    (OUT/'blender/final_validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
