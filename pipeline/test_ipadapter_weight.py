import json
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch
from images import CONFIG, PROJECT, build_prompt

scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
scene = scenes[0]
prompt = (
    build_prompt(scene)
    + ", wide establishing shot, full body visible, character standing in the environment, "
    "street and buildings clearly visible, character occupies less than half the frame"
)
client = ComfyClient(CONFIG["comfy_url"])
variants = [(0.55, 1.0), (0.65, 0.7), (0.50, 0.8)]
for index, (weight, end_at) in enumerate(variants, 1):
    wf = load_workflow(Path(__file__).resolve().parent / "workflows" / "sdxl_ipadapter_api.json")
    patch(wf, "5", {"text": prompt})
    patch(wf, "4", {"weight": weight, "end_at": end_at})
    patch(wf, "8", {"seed": 1001})
    patch(wf, "10", {"filename_prefix": f"story/ipadapter_test_{index}"})
    dest = PROJECT / "images_consistent" / f"ipadapter_test_{index}.png"
    client.generate(wf, dest, timeout=900)
    print("saved", dest, "weight", weight, "end_at", end_at)
