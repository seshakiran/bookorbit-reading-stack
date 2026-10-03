#!/usr/bin/env python3
"""Apply the reviewed studio patch to the pinned BookOrbit source checkout."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
source=a.source.resolve();patch=ROOT/'patches/bookorbit-audiobook-studio.patch'
version=json.loads((ROOT/'native/versions.json').read_text())['bookorbit']
actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
if actual!=version: raise SystemExit('Version mismatch: use the pinned BookOrbit revision before applying this patch.')
command=['git','-C',str(source),'apply']
if subprocess.run(command+['--reverse','--check',str(patch)],capture_output=True).returncode==0:
 print('Studio patch already applied.')
else:
 subprocess.run(command+['--check',str(patch)],check=True)
 subprocess.run(command+[str(patch)],check=True)
 print('Studio patch applied. Rebuild BookOrbit before restarting.')
