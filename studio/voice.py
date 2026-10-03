"""Generate an original narrator reference. No celebrity voice or external recording."""
import os
from pathlib import Path
import sys
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model
path = Path(sys.argv[1])
os.environ.setdefault('HF_HOME', str(path.parent/'models'))
text = 'Every discovery starts with a question. Sometimes the answer arrives quietly, and sometimes it changes everything. Let us follow the story together, one surprising idea at a time.'
model = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16')
results = list(model.generate(text=text, instruct='An original adult male narrator with a warm, clear, uplifting conversational delivery. Engaging and lightly curious, restrained emotion, natural moderate pace. No exaggerated drama.', language='English'))
sf.write(path, np.concatenate([np.asarray(r.audio) for r in results]), results[0].sample_rate)
path.with_suffix('.txt').write_text(text)
