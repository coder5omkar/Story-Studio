"""Generate the background score with ACE-Step 1.5 in ComfyUI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from comfy_client import ComfyClient, load_workflow, patch

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG", ROOT / "config.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROJECT = Path(CONFIG["project_dir"])
WORKFLOW = ROOT / "workflows" / "ace_step_15_api.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=CONFIG["music"]["duration"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prompt", default=CONFIG["music"]["prompt"])
    parser.add_argument("--bpm", type=int, default=CONFIG["music"].get("bpm", 78))
    parser.add_argument("--key", default=CONFIG["music"].get("key", "C minor"))
    parser.add_argument("--out", default=str(PROJECT / "audio" / "music.mp3"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    dest = Path(args.out)
    if dest.exists() and not args.force:
        print(f"[skip] {dest} already exists")
        return 0

    client = ComfyClient(CONFIG["comfy_url"])
    if not client.is_up():
        print("ComfyUI is not reachable at", CONFIG["comfy_url"])
        return 1

    music = CONFIG["music"]
    workflow = load_workflow(WORKFLOW)
    patch(
        workflow,
        "2",
        {
            "tags": args.prompt,
            "bpm": args.bpm,
            "duration": float(args.duration),
            "keyscale": args.key,
            "seed": args.seed,
            "language": "en",
        },
    )
    patch(workflow, "5", {"seconds": float(args.duration)})
    patch(workflow, "6", {"seed": args.seed})
    patch(workflow, "8", {"filename_prefix": "story/music"})

    print(f"[music] {args.duration:.0f}s -> {dest.name}")
    client.generate(workflow, dest, timeout=1800)
    print(f"  saved {dest.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
