"""Turn a Hindi story into a scene list with English image prompts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from ollama_client import chat, extract_json

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG", ROOT / "config.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROJECT = Path(CONFIG["project_dir"])


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"^#.*$", "", text, flags=re.M)
    text = re.sub(r"^>.*$", "", text, flags=re.M)
    text = re.sub(r"\n{2,}", "\n", text)
    parts = re.split(r"(?<=[।?!])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def normalize_camera(value: object) -> str:
    text = str(value).lower()
    if "pull" in text or "out" in text:
        return "slow pull back"
    if "left" in text:
        return "slow pan left"
    if "right" in text:
        return "slow pan right"
    return "slow push in"


def chunk_sentences(sentences: list[str], target: int = 24) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in sentences:
        words = len(sentence.split())
        if current and count + words > target + 8:
            chunks.append(" ".join(current))
            current, count = [], 0
        current.append(sentence)
        count += words
        if count >= target:
            chunks.append(" ".join(current))
            current, count = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", default=str(PROJECT / "story.md"))
    parser.add_argument("--out", default=str(PROJECT / "scenes.json"))
    parser.add_argument("--model", default=CONFIG["story_model"])
    parser.add_argument("--batch", type=int, default=12)
    parser.add_argument("--target-words", type=int, default=24)
    args = parser.parse_args()

    story = Path(args.story).read_text(encoding="utf-8")
    chunks = chunk_sentences(split_sentences(story), target=args.target_words)
    print(f"[scenes] {len(chunks)} narration chunks")

    scenes: list[dict] = []
    system = (
        "You are a storyboard artist for a flat-vector Hindi YouTube story channel. "
        "For each Hindi narration chunk, write one concrete English image prompt. "
        "Keep the same character across scenes. Describe setting, action, emotion, and composition. "
        "No text in the image. Return only a JSON array."
    )
    for start in range(0, len(chunks), args.batch):
        batch = chunks[start : start + args.batch]
        numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(batch))
        user = f"""
For each narration chunk below, create one scene entry.

Return a JSON array with exactly {len(batch)} objects:
[
  {{"image_prompt": "English visual description", "camera": "slow push in|slow pull back|slow pan left|slow pan right", "mood": "one or two English words"}}
]

Narration chunks:
{numbered}
"""
        try:
            raw = chat(
                CONFIG["ollama_url"],
                args.model,
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                num_predict=4096,
                temperature=0.7,
            )
            items = extract_json(raw)
            if not isinstance(items, list):
                raise ValueError(f"expected a JSON array, got {type(items).__name__}")
            if len(items) != len(batch):
                print(f"[scenes] batch {start // args.batch + 1}: got {len(items)} items for {len(batch)} chunks; padding/trimming")
                while len(items) < len(batch):
                    items.append(
                        {
                            "image_prompt": "Indian middle-class setting, cinematic flat vector illustration, emotional storytelling scene",
                            "camera": "slow push in",
                            "mood": "emotional",
                        }
                    )
                items = items[: len(batch)]
        except Exception as exc:
            print(f"[scenes] batch {start // args.batch + 1} failed ({exc}); using fallback prompts")
            items = [
                {
                    "image_prompt": "Indian middle-class setting, cinematic flat vector illustration, emotional storytelling scene",
                    "camera": "slow push in",
                    "mood": "emotional",
                }
                for _ in batch
            ]

        for offset, (narration, item) in enumerate(zip(batch, items)):
            scenes.append(
                {
                    "id": len(scenes) + 1,
                    "chapter": 0,
                    "narration": narration,
                    "image_prompt": item.get("image_prompt", ""),
                    "camera": normalize_camera(item.get("camera", "slow push in")),
                    "mood": item.get("mood", "emotional"),
                }
            )
        print(f"[scenes] batch {start // args.batch + 1}: {len(scenes)}/{len(chunks)}")

    out = Path(args.out)
    out.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[scenes] saved {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
