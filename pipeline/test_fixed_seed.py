import json
from pathlib import Path

from comfy_client import ComfyClient
from images import CONFIG, PROJECT, sdxl_workflow

scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
scene = scenes[1]
wf = sdxl_workflow(scene)
wf["5"]["inputs"]["seed"] = 1001
client = ComfyClient(CONFIG["comfy_url"])
dest = PROJECT / "images" / "test_fixed_seed.png"
client.generate(wf, dest, timeout=900)
print("saved", dest)
