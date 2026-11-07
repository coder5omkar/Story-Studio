import wave
from pathlib import Path

from piper import PiperVoice

base = Path(r"D:\AI_Story_Channel\models\piper")
voice = PiperVoice.load(
    str(base / "hi_IN-pratham-medium.onnx"),
    config_path=str(base / "hi_IN-pratham-medium.onnx.json"),
)
text = (base / "ref_text.txt").read_text(encoding="utf-8").strip()
with wave.open(str(base / "hindi_ref.wav"), "wb") as wav_file:
    voice.synthesize_wav(text, wav_file)
print("saved", base / "hindi_ref.wav")
