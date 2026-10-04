"""Extract each chapter's final state and a nine-panel contact sheet for review."""
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent
if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--prefix",default="review_v2")
    args=p.parse_args()
    recs=json.loads((ROOT/"assets/audio/manifest.json").read_text())
    folder=ROOT/"output"/args.prefix
    folder.mkdir(exist_ok=True)
    canvas=Image.new("RGB",(1920,1080),"white")
    for ci in range(9):
        rec=[r for r in recs if r["chapter"]==ci][-1]
        file=folder/f"{ci+1:02d}.png"
        subprocess.run(["ffmpeg","-v","error","-y","-ss",str(rec["end"]-1.3),"-i",args.source,
            "-frames:v","1",str(file)],check=True)
        with Image.open(file) as im:
            canvas.paste(im.resize((640,360)),((ci%3)*640,(ci//3)*360))
    canvas.save(ROOT/"output"/f"{args.prefix}.png")
