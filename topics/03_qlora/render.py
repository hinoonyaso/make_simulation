"""Reproduce the narrated QLoRA v2 package in the shared uv environment."""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--preview", action="store_true", help="480p, 30 fps; narration must exist")
    p.add_argument("--prepare-audio", action="store_true", help="Generate TTS (network) and Whisper captions")
    args = p.parse_args()
    if args.prepare_audio:
        run("uv", "run", "--offline", "python", "prepare_audio.py", "tts")
        run("uv", "run", "--offline", "python", "prepare_audio.py", "captions")
    run("uv", "run", "--offline", "manim", "-ql" if args.preview else "-qh", "--fps", "30",
        "--media_dir", "media_v2", "qlora_video_v2.py", "QLoRAEnhanced")
    if not args.preview:
        run("uv", "run", "--offline", "python", "finish_video.py")
        run("uv", "run", "--offline", "python", "validate_video.py")
