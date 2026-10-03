#!/usr/bin/env python3
"""Transcribe a local take and flag possible narration errors for human review."""
import argparse,json,re
from difflib import SequenceMatcher
from pathlib import Path
from faster_whisper import WhisperModel
p=argparse.ArgumentParser();p.add_argument('take');args=p.parse_args()
take=Path(args.take).resolve();manifest=json.loads((take/'manifest.json').read_text())
model=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4,download_root=str(Path(__file__).resolve().parent/'models/whisper'))
def words(text): return re.findall(r"[a-z0-9]+(?:'[a-z]+)?",text.lower().replace('’',"'"))
report=[]
for c in manifest['chunks']:
    segments,_=model.transcribe(str(take/c['file']),language='en',beam_size=5)
    transcript=' '.join(s.text.strip() for s in segments)
    expected=words(c['text']);actual=words(transcript)
    differences=[]
    for op,a,b,x,y in SequenceMatcher(None,expected,actual,autojunk=False).get_opcodes():
        if op!='equal': differences.append({'operation':op,'expected':' '.join(expected[a:b]),'heard':' '.join(actual[x:y])})
    report.append({'file':c['file'],'transcript':transcript,'possible_errors':differences,'words_per_minute':len(expected)*60/c['seconds']})
(take/'quality-review.json').write_text(json.dumps({'note':'ASR differences are review flags, not proof of incorrect speech. Listen before approving.','chunks':report},indent=2))
print('Quality review saved; chunks needing review:',sum(bool(r['possible_errors']) for r in report),'of',len(report))
