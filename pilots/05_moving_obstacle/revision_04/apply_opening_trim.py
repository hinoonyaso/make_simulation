"""Remove an unsupported opening sentence locally, without another external TTS request."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    assets=HERE/'assets/audio';wav=assets/'B01.wav';original=assets/'B01_original.wav'
    if not original.exists():shutil.copy2(wav,original)
    doc_path=HERE/'visual_manifest.json';doc=json.loads(doc_path.read_text());records_path=assets/'manifest.json';records=json.loads(records_path.read_text())
    start=4.0;seconds=3.7  # Existing measured word “길은” starts at 4.10; retain 0.10s pre-roll.
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(original),'-af',f'atrim=start={start},asetpts=PTS-STARTPTS','-t',str(seconds),'-ar','48000',str(wav)],check=True)
    text='길은 같은데 무엇이 달라졌을까요?'
    records[0].update(text=text,caption=text,duration=seconds)
    doc['beats'][0].update(text=text,caption=text,sec=seconds)
    now=0.
    for rec in records:rec['start']=now;now+=rec['duration'];rec['end']=now
    records_path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    doc_path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(assets/'concat.txt'),'-c:a','pcm_s16le',str(HERE/'output/narration.wav')],check=True)
    (HERE/'output/local_audio_edit.json').write_text(json.dumps({'beat':'B01','source':'assets/audio/B01_original.wav','source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'trim_start_s':start,'duration_s':seconds,'reason':'Remove implication that the robot already traversed the whole stored south route; retain the existing question.'},indent=2)+'\n')
    print(f'Local opening trim applied; total {now:.2f}s')
if __name__=='__main__':main()
