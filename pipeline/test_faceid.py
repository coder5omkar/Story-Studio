import json
import sys
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch
from images import CONFIG, PROJECT, build_prompt

reference = sys.argv[1] if len(sys.argv) > 1 else "character_ref.png"
out_name = sys.argv[2] if len(sys.argv) > 2 else "faceid_test.png"

scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
scene = scenes[0]
wf = load_workflow(Path(__file__).resolve().parent / "workflows" / "sdxl_faceid_api.json")
patch(wf, "3", {"image": reference})
patch(wf, "5", {"text": build_prompt(scene)})
patch(wf, "8", {"seed": 1001})
patch(wf, "10", {"filename_prefix": f"story/{Path(out_name).stem}"})
client = ComfyClient(CONFIG["comfy_url"])
dest = PROJECT / "images_consistent" / out_name
client.generate(wf, dest, timeout=1800)
print("saved", dest)
