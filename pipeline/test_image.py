import json
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch

root = Path(__file__).resolve().parent
config = json.loads((root / "config.json").read_text(encoding="utf-8"))
project = Path(config["project_dir"])
scenes = json.loads((project / "scenes.json").read_text(encoding="utf-8"))
scene = scenes[0]
prompt = (
    f"{config['image']['style_prefix']}, {config['image']['character']}, "
    f"{scene['image_prompt']}, {scene['mood']} mood"
)
wf = load_workflow(root / "workflows" / "sdxl_api.json")
patch(wf, "2", {"text": prompt})
patch(wf, "5", {"seed": 1234})
patch(wf, "7", {"filename_prefix": "story/test_sdxl"})
client = ComfyClient(config["comfy_url"])
print("up:", client.is_up())
dest = project / "images" / "test_sdxl.png"
client.generate(wf, dest, timeout=900)
print("saved", dest, dest.stat().st_size)
