import json
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch

root = Path(__file__).resolve().parent
config = json.loads((root / "config.json").read_text(encoding="utf-8"))
project = Path(config["project_dir"])
prompt = (
    "photorealistic close-up portrait of a 29-year-old Indian man with short black hair, "
    "a light mustache, warm brown eyes, average build, wearing a white shirt, neutral warm background, "
    "front-facing, symmetrical, natural skin texture, soft studio lighting, sharp focus, 85mm lens, no text"
)
wf = load_workflow(root / "workflows" / "sdxl_api.json")
patch(wf, "2", {"text": prompt})
patch(wf, "4", {"width": 1024, "height": 1024})
patch(wf, "5", {"seed": 5678, "steps": 30, "cfg": 7.0})
patch(wf, "7", {"filename_prefix": "story/character_ref_real"})
client = ComfyClient(config["comfy_url"])
dest = project / "images" / "character_ref_real.png"
client.generate(wf, dest, timeout=900)
print("saved", dest)
