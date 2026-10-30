#!/usr/bin/env python3
"""Шаг 1: large-v3 без подсказки-глоссария (она «эхом» вставлялась в тишину),
без опоры на предыдущий текст (обрывает зацикливание), с отбрасыванием пустых сегментов.
Термины исправляются после распознавания по replacements.txt."""
import sys, os, gc, subprocess
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.expanduser("~/VideoAutomation"))
from clean_lib import clean

video = sys.argv[1]
stem = os.path.splitext(os.path.basename(video))[0]
out = os.path.expanduser("~/VideoAutomation/transcripts"); os.makedirs(out, exist_ok=True)

try:
    free = int(subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True).stdout.split()[0])
except Exception:
    free = 0
modes = (["float16"] if free >= 6000 else []) + (["int8_float16"] if free >= 3500 else [])
model = None
for ct in modes:
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type=ct)
        print(f"Устройство: cuda ({ct}), свободно VRAM {free} МБ"); break
    except Exception as e:
        print(f"  {ct} не поднялся: {e}")
if model is None:
    print(f"VRAM мало ({free} МБ) — CPU int8, будет медленно")
    model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=16)

segs, _ = model.transcribe(video, language="ru", beam_size=5,
                           vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
                           condition_on_previous_text=False,
                           no_speech_threshold=0.6, log_prob_threshold=-1.0,
                           compression_ratio_threshold=2.4)
kept = dropped = 0; texts = []
for s in segs:
    if s.no_speech_prob > 0.6 and s.avg_logprob < -0.8:   # скорее тишина/шум, чем речь
        dropped += 1; continue
    texts.append(s.text.strip()); kept += 1
raw = " ".join(texts)
open(f"{out}/{stem}.raw.txt", "w", encoding="utf-8").write(raw)
text = clean(raw)
open(f"{out}/{stem}.txt", "w", encoding="utf-8").write(text)
del model; gc.collect()
print(f"Готово: {stem}.txt ({len(text.split())} слов; сегментов {kept}, отброшено как тишина {dropped})")
