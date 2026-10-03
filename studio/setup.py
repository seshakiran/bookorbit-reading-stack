#!/usr/bin/env python3
"""Configure a private Apple Silicon narrator and connect it to native BookOrbit."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import wave
import struct

ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--native', type=Path, default=ROOT.parent/'native')
    p.add_argument('--reference', type=Path, help='Optional original/authorized voice WAV with adjacent .txt transcript')
    p.add_argument('--python', type=Path, help='Existing MLX Audio environment; otherwise create studio/venv')
    p.add_argument('--qa-python', type=Path, help='Existing faster-whisper environment')
    args = p.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise SystemExit('MLX creation requires Apple Silicon. Linux playback is supported by the stack; this creator is Mac-only.')
    native = args.native.resolve()
    config_path = native/'config/bookorbit.json'
    if not config_path.exists():
        raise SystemExit('Install native BookOrbit first.')
    python = args.python.absolute() if args.python else ROOT/'venv/bin/python'
    if not args.python:
        subprocess.run([sys.executable, '-m', 'venv', str(ROOT/'venv')], check=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT/'requirements.txt')], check=True)
    private = native/'data/audiobook-studio'
    private.mkdir(parents=True, exist_ok=True)
    private.chmod(0o700)
    reference = args.reference.resolve() if args.reference else private/'storyteller.wav'
    if not reference.exists() and not args.reference:
        subprocess.run([str(python), str(ROOT/'voice.py'), str(reference)], check=True)
    if not reference.is_file() or not reference.with_suffix('.txt').is_file():
        raise SystemExit('The reference WAV and its matching .txt transcript are required.')
    cue = private/'chapter-cue.wav'
    if not cue.exists():
        with wave.open(str(cue), 'wb') as out:
            out.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
            notes = [261.63, 329.63, 392, 523.25, 392, 329.63, 293.66, 392]
            frames = bytearray()
            for i in range(6*48000):
                t=i/48000; local=t % .375
                value=.12*math.sin(2*math.pi*notes[int(t/.375)%len(notes)]*local)*math.exp(-local*12)*min(1,t*20)*min(1,(6-t)*3)
                frames.extend(struct.pack('<h', round(value*32767)))
            out.writeframes(frames)
    config = {'jobs_directory': str(private/'jobs'), 'python': str(python), 'qa_python': str(args.qa_python.absolute()) if args.qa_python else str(python),
              'reference_audio': str(reference), 'music_path': str(cue), 'narrator': 'Storyteller'}
    studio_config = private/'config.json'
    studio_config.write_text(json.dumps(config, indent=2));studio_config.chmod(0o600)
    env = json.loads(config_path.read_text())
    env.update(STUDIO_PYTHON=sys.executable, STUDIO_WORKER=str(ROOT/'worker.py'), STUDIO_CONFIG=str(studio_config))
    config_path.write_text(json.dumps(env, indent=2));config_path.chmod(0o600)
    print('Private studio configured. Apply/build the BookOrbit patch, then restart BookOrbit.')

if __name__ == '__main__': main()
