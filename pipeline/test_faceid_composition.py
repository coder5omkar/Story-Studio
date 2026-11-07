import json
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch
from images import CONFIG, PROJECT, build_prompt

scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
scene = scenes[0]
base = build_prompt(scene)
variants = [
    (
        base + ", full body shot from head to toe, wide-angle lens, character small in frame, entire Jaipur street and buildings visible, environmental portrait, (close-up:0.6)",
        "close-up, headshot, portrait, face only, cropped body, out of frame, low quality, blurry, text, watermark, deformed, extra fingers, bad anatomy",
        "faceid_comp_1.png",
    ),
    (
        base + ", 35mm lens, full body visible, the man stands far from the camera in a wide Jaipur street, full architecture and sky visible, character occupies one third of the frame",
        "close-up, headshot, portrait, face only, cropped body, out of frame, low quality, blurry, text, watermark, deformed, extra fingers, bad anatomy",
        "faceid_comp_2.png",
    ),
]
client = ComfyClient(CONFIG["comfy_url"])
for positive, negative, out_name in variants:
    wf = load_workflow(Path(__file__).resolve().parent / "workflows" / "sdxl_faceid_api.json")
    patch(wf, "5", {"text": positive})
    patch(wf, "6", {"text": negative})
    patch(wf, "8", {"seed": 1001})
    patch(wf, "10", {"filename_prefix": f"story/{Path(out_name).stem}"})
    dest = PROJECT / "images_consistent" / out_name
    client.generate(wf, dest, timeout=1800)
    print("saved", dest)
