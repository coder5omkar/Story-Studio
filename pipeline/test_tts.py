import torch
import soundfile as sf
import chatterbox.mtl_tts as _mtl
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

_mtl.snapshot_download = lambda *args, **kwargs: r"D:\AI_Story_Channel\models\chatterbox"

print("loading model ...", flush=True)
model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
print("sample rate:", model.sr, flush=True)

text = "नमस्ते। मेरा नाम अर्जुन है। आज मैं आपको अपनी कहानी सुनाऊँगा।"
wav = model.generate(
    text,
    language_id="hi",
    audio_prompt_path=r"D:\AI_Story_Channel\models\piper\hindi_ref.wav",
    exaggeration=0.5,
    cfg_weight=0.3,
    temperature=0.8,
)
print("wav shape:", tuple(wav.shape), flush=True)
sf.write(
    r"D:\AI_Story_Channel\projects\pilot_001\audio\test_tts.wav",
    wav.squeeze(0).cpu().numpy(),
    model.sr,
)
print("saved", flush=True)
