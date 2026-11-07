"""Generate one illustration per scene with SDXL or Z-Image in ComfyUI."""

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


def build_prompt(scene: dict) -> str:
    image_cfg = CONFIG["image"]
    return (
        f"{image_cfg['style_prefix']}, "
        f"character: {image_cfg['character']}, "
        f"scene: {scene['image_prompt']}, "
        f"{scene['mood']} mood, {scene['camera']} camera move. "
        f"Follow the visual style and character description exactly. "
        f"No text, no watermark."
    )


def sdxl_workflow(scene: dict, seed: int | None = None) -> dict:
    image_cfg = CONFIG["image"]
    workflow = load_workflow(ROOT / "workflows" / "sdxl_api.json")
    patch(workflow, "2", {"text": build_prompt(scene)})
    if "negative_prompt" in image_cfg:
        patch(workflow, "3", {"text": str(image_cfg.get("negative_prompt") or "")})
    patch(
        workflow,
        "5",
        {
            "seed": seed if seed is not None else 1000 + scene["id"],
            "steps": 28,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
        },
    )
    patch(workflow, "7", {"filename_prefix": f"story/scene_{scene['id']:03d}"})
    return workflow


def zimage_workflow(scene: dict, seed: int | None = None) -> dict:
    image_cfg = CONFIG["image"]
    workflow = load_workflow(ROOT / "workflows" / "z_image_api.json")
    patch(workflow, "4", {"text": build_prompt(scene)})
    patch(workflow, "6", {"width": image_cfg["width"], "height": image_cfg["height"]})
    patch(
        workflow,
        "8",
        {
            "seed": seed if seed is not None else 1000 + scene["id"],
            "steps": image_cfg["steps"],
            "cfg": image_cfg["cfg"],
            "sampler_name": image_cfg["sampler"],
            "scheduler": image_cfg["scheduler"],
        },
    )
    patch(workflow, "10", {"filename_prefix": f"story/scene_{scene['id']:03d}"})
    return workflow


def ipadapter_workflow(scene: dict, seed: int | None = None) -> dict:
    image_cfg = CONFIG["image"]
    workflow = load_workflow(ROOT / "workflows" / "sdxl_ipadapter_api.json")
    patch(workflow, "5", {"text": build_prompt(scene)})
    if "negative_prompt" in image_cfg:
        patch(workflow, "6", {"text": str(image_cfg.get("negative_prompt") or "")})
    patch(workflow, "7", {"width": image_cfg["width"], "height": image_cfg["height"]})
    patch(
        workflow,
        "8",
        {
            "seed": seed if seed is not None else 1000 + scene["id"],
            "steps": 28,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
        },
    )
    patch(workflow, "10", {"filename_prefix": f"story/scene_{scene['id']:03d}"})
    return workflow


def faceid_workflow(scene: dict, seed: int | None = None) -> dict:
    image_cfg = CONFIG["image"]
    workflow = load_workflow(ROOT / "workflows" / "sdxl_faceid_api.json")
    patch(workflow, "5", {"text": build_prompt(scene)})
    fixed = (
        "close-up, headshot, face only, cropped body, out of frame, "
        "low quality, blurry, text, watermark, deformed, extra fingers, bad anatomy, different person"
    )
    negative = image_cfg.get("negative_prompt")
    patch(workflow, "6", {"text": f"{negative}, {fixed}" if negative else fixed})
    patch(workflow, "7", {"width": image_cfg["width"], "height": image_cfg["height"]})
    patch(
        workflow,
        "8",
        {
            "seed": seed if seed is not None else 1000 + scene["id"],
            "steps": 28,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
        },
    )
    patch(workflow, "10", {"filename_prefix": f"story/scene_{scene['id']:03d}"})
    return workflow


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["sdxl", "zimage", "ipadapter", "faceid"], default="sdxl")
    parser.add_argument("--out-dir", default="images")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--ids", default="")
    parser.add_argument("--seed", type=int, default=0, help="override the per-scene seed")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    if args.ids:
        wanted = {int(x) for x in args.ids.split(",") if x.strip()}
        scenes = [s for s in scenes if s["id"] in wanted]
    if args.limit:
        scenes = scenes[: args.limit]

    client = ComfyClient(CONFIG["comfy_url"])
    if not client.is_up():
        print("ComfyUI is not reachable at", CONFIG["comfy_url"])
        return 1

    out_dir = PROJECT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    for scene in scenes:
        dest = out_dir / f"scene_{scene['id']:03d}.png"
        if dest.exists() and not args.force:
            print(f"[skip] {dest.name}")
            continue

        seed = args.seed if args.seed > 0 else None
        if args.engine == "sdxl":
            workflow = sdxl_workflow(scene, seed)
        elif args.engine == "zimage":
            workflow = zimage_workflow(scene, seed)
        elif args.engine == "ipadapter":
            workflow = ipadapter_workflow(scene, seed)
        else:
            workflow = faceid_workflow(scene, seed)
        print(f"[{args.engine} {scene['id']:02d}/{len(scenes)}] {dest.name}")
        try:
            client.generate(workflow, dest, timeout=900)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            return 1
        print(f"  saved {dest.stat().st_size / 1024:.0f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
