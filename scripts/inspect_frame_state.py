#!/usr/bin/env python3
"""Inspect recorded PID values at selected video frames (no simulation/render)."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.mechanism.pid_playback import PIDPlayback
from core.mechanism.adapters.mcu_pid import MCUPIDAdapter


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trace',required=True,type=Path)
    p.add_argument('--timeline',required=True,type=Path)
    p.add_argument('--frames',required=True,type=int,nargs='+')
    args=p.parse_args()
    trace=json.loads(args.trace.read_text())
    errors=MCUPIDAdapter().validate(trace)
    if errors: p.error('; '.join(errors))
    player=PIDPlayback(trace['payload'],json.loads(args.timeline.read_text()))
    print(json.dumps([player.state(i) for i in args.frames],ensure_ascii=False,indent=2))


if __name__=='__main__': main()
