"""Generate Hindi narration with Chatterbox Multilingual (local, MIT)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import torch
import soundfile as sf

from hindi_text import normalize_for_tts

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG", ROOT / "config.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROJECT = Path(CONFIG["project_dir"])


def split_text(text: str, max_chars: int = 160) -> list[str]:
    parts = [p.strip() for p in re.split(r"(?<=[।?!])\s+", text.strip()) if p.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts:
        while len(part) > max_chars:
            cut = part.rfind(",", 0, max_chars)
            if cut < max_chars // 2:
                cut = part.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            piece, part = part[:cut].strip(), part[cut:].lstrip(" ,")
            if current:
                chunks.append(current)
                current = ""
            if piece:
                chunks.append(piece)
        if not part:
            continue
        if len(current) + len(part) + 1 <= max_chars:
            current = f"{current} {part}".strip()
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def synth(model, text: str, tts_cfg: dict, sample_rate: int):
    """Synthesize normalized text and return a 1xN float tensor."""
    chunks = split_text(text)
    pieces = []
    for chunk in chunks:
        wav = model.generate(
            chunk,
            language_id=tts_cfg["language_id"],
            audio_prompt_path=tts_cfg.get("reference") or None,
            exaggeration=tts_cfg["exaggeration"],
            cfg_weight=tts_cfg["cfg_weight"],
            temperature=tts_cfg["temperature"],
        )
        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        pieces.append(wav.cpu())

    if len(pieces) > 1:
        gap = torch.zeros((1, int(sample_rate * 0.25)))
        merged = []
        for i, piece in enumerate(pieces):
            merged.append(piece)
            if i < len(pieces) - 1:
                merged.append(gap)
        return torch.cat(merged, dim=-1)
    return pieces[0]


def write_wav(path: Path, wav, sample_rate: int) -> float:
    """Write a peak-normalized WAV with short fades to avoid clipping/clicks."""
    data = wav.squeeze(0).cpu().numpy().astype("float32")
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak > 1e-4:
        data = data * (0.90 / peak)
    fade = min(int(sample_rate * 0.03), len(data) // 2)
    if fade > 0:
        data[:fade] *= np.linspace(0.0, 1.0, fade, dtype="float32")
        data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype="float32")
    sf.write(str(path), data, sample_rate)
    return len(data) / sample_rate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--ids", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--out-dir", default="", help="override output directory")
    parser.add_argument("--out", default="", help="single output file (used with --text)")
    parser.add_argument("--text", default="", help="synthesize arbitrary text instead of scenes")
    parser.add_argument("--reference", default="")
    parser.add_argument("--exaggeration", type=float, default=None)
    parser.add_argument("--cfg-weight", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    args = parser.parse_args()

    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    import chatterbox.mtl_tts as _mtl

    _mtl.snapshot_download = lambda *args, **kwargs: r"D:\AI_Story_Channel\models\chatterbox"

    tts = dict(CONFIG["tts"])
    if args.reference:
        tts["reference"] = args.reference
    if args.exaggeration is not None:
        tts["exaggeration"] = args.exaggeration
    if args.cfg_weight is not None:
        tts["cfg_weight"] = args.cfg_weight
    if args.temperature is not None:
        tts["temperature"] = args.temperature

    print("[tts] loading Chatterbox Multilingual ...")
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    sample_rate = int(model.sr)
    print(f"[tts] ready, sample rate {sample_rate}")

    if args.text.strip():
        dest = Path(args.out) if args.out else PROJECT / "studio" / "samples" / "voice" / "sample.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize_for_tts(args.text.strip())
        preview = normalized[:600] + ("…" if len(normalized) > 600 else "")
        print(f"[tts normalized] {preview}")
        wav = synth(model, normalized, tts, sample_rate)
        duration = write_wav(dest, wav, sample_rate)
        print(f"[tts sample] {dest} -> {duration:.1f}s")
        return 0

    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    if args.ids:
        wanted = {int(x) for x in args.ids.split(",") if x.strip()}
        scenes = [s for s in scenes if s["id"] in wanted]
    if args.limit:
        scenes = scenes[: args.limit]

    out_dir = Path(args.out_dir) if args.out_dir else PROJECT / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    timings = []
    for scene in scenes:
        dest = out_dir / f"scene_{scene['id']:03d}.wav"
        if dest.exists() and not args.force:
            duration = sf.info(str(dest)).duration
            timings.append({"id": scene["id"], "file": dest.name, "duration": round(duration, 3)})
            print(f"[skip] {dest.name} ({duration:.1f}s)")
            continue

        normalized = normalize_for_tts(scene["narration"])
        wav = synth(model, normalized, tts, sample_rate)
        duration = write_wav(dest, wav, sample_rate)
        timings.append({"id": scene["id"], "file": dest.name, "duration": round(duration, 3)})
        print(f"[tts {scene['id']:02d}/{len(scenes)}] {dest.name} -> {duration:.1f}s ({len(normalized)} chars)")

    timings_path = out_dir / "timings.json"
    if args.ids or args.limit:
        # Partial runs must not erase timings for the rest of the project.
        merged = {}
        if timings_path.exists():
            try:
                merged = {t["id"]: t for t in json.loads(timings_path.read_text(encoding="utf-8"))}
            except Exception:
                merged = {}
        for item in timings:
            merged[item["id"]] = item
        timings = [merged[k] for k in sorted(merged)]
    timings_path.write_text(
        json.dumps(timings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total = sum(t["duration"] for t in timings)
    print(f"[tts] done: {total:.1f}s total -> {timings_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
