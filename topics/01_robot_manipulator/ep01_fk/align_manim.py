"""Remove float-rounding extra boundary frames from Manim's animation clips."""
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/manim'

def main():
    bounds=[int(x) for x in re.findall(r'self.advance\((\d+)',(ROOT/'manim_scene.py').read_text())]
    bounds.insert(1,457)  # 21-frame title transition inside beat B02
    render=OUT/'final/videos/manim_scene/1080p30'
    playlist=render/'partial_movie_files/EP01ForwardKinematics/partial_movie_file_list.txt'
    paths=[line.split("'")[1].removeprefix('file:') for line in playlist.read_text().splitlines() if line.startswith('file ')]
    assert len(paths)==len(bounds)
    start=frame=0; drops=[]
    for path,end in zip(paths,bounds):
        count=int(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','default=nw=1:nk=1',path]))
        expected=end-start
        assert expected<=count<=expected+1,(path,count,expected)
        drops.extend(range(frame+expected,frame+count))
        frame+=count;start=end
    assert start==5351
    filters='select=not('+ '+'.join(f'eq(n\\,{n})' for n in drops)+'),setpts=N/(30*TB)' if drops else 'setpts=N/(30*TB)'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(render/'lesson.mp4'),'-vf',filters,'-r','30','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',str(OUT/'lesson.mp4')],check=True)
    (OUT/'frame_alignment.json').write_text(json.dumps(dict(original_frames=frame,target_frames=start,drop_duplicate_end_frames=drops),indent=2))

if __name__=='__main__':main()
