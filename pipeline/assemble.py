"""Assemble the pilot: Ken Burns clips + narration + music + Hindi subtitles."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG", ROOT / "config.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROJECT = Path(CONFIG["project_dir"])
FPS = 30
WIDTH, HEIGHT = 1920, 1080


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("  $", " ".join(str(c) for c in cmd[:8]), "...")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}):\n{proc.stderr[-4000:]}")


def make_clip(image: Path, dest: Path, duration: float, camera: str) -> None:
    frames = max(2, round(duration * FPS))
    base = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT}"
    )
    if "pull" in camera or "out" in camera:
        zoom = f"if(lte(on,1),1.10,max(1.0,zoom-0.00035))"
    elif "pan" in camera:
        zoom = "1.08"
    else:
        zoom = f"min(zoom+0.00035,1.10)"
    vf = (
        f"{base},zoompan=z='{zoom}':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )
    run(
        [
            "ffmpeg", "-y", "-i", str(image), "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an", "-t", f"{duration:.3f}", str(dest),
        ]
    )


def concat_clips(clips: list[Path], dest: Path) -> None:
    list_file = dest.parent / "clips.txt"
    list_file.write_text(
        "\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8"
    )
    run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(dest),
        ]
    )


def concat_audio(files: list[Path], dest: Path) -> None:
    list_file = dest.parent / "audio_list.txt"
    list_file.write_text(
        "\n".join(f"file '{f.as_posix()}'" for f in files), encoding="utf-8"
    )
    run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:a", "pcm_s16le", str(dest),
        ]
    )


def mix_music(narration: Path, music: Path, dest: Path, volume: float = 0.10) -> None:
    run(
        [
            "ffmpeg", "-y", "-i", str(narration), "-stream_loop", "-1", "-i", str(music),
            "-filter_complex",
            f"[1:a]volume={volume:.4f},afade=t=in:st=0:d=2[m];"
            "[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "[a]", "-c:a", "pcm_s16le", str(dest),
        ]
    )


def fmt_ts(seconds: float) -> str:
    td = timedelta(seconds=max(0.0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    h, rem = divmod(total_ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_srt(scenes: list[dict], timings: list[dict], dest: Path) -> None:
    by_id = {t["id"]: t["duration"] for t in timings}
    cursor = 0.0
    blocks = []
    index = 1
    for scene in scenes:
        duration = float(by_id[scene["id"]])
        text = scene["narration"].strip()
        parts = [p.strip() for p in text.replace("?", "?|").replace("!", "!|").replace("।", "।|").split("|") if p.strip()]
        if not parts:
            parts = [text]
        total_chars = sum(len(p) for p in parts) or 1
        local = cursor
        for part in parts:
            part_dur = duration * len(part) / total_chars
            blocks.append(
                f"{index}\n{fmt_ts(local)} --> {fmt_ts(local + part_dur)}\n{part}\n"
            )
            index += 1
            local += part_dur
        cursor += duration
    dest.write_text("\n".join(blocks), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-subs", action="store_true")
    parser.add_argument("--no-music", action="store_true")
    parser.add_argument("--music-volume", type=float, default=None)
    parser.add_argument("--images-dir", default=str(PROJECT / "images"))
    parser.add_argument("--out-name", default="pilot.mp4")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    timings_path = PROJECT / "audio" / "timings.json"
    if not timings_path.exists():
        print("Missing audio/timings.json; run tts.py first.")
        return 1
    timings = json.loads(timings_path.read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in timings}

    clips_dir = PROJECT / "video" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for scene in scenes:
        if scene["id"] not in by_id:
            print(f"Missing timing for scene {scene['id']}")
            return 1
        image = images_dir / f"scene_{scene['id']:03d}.png"
        if not image.exists():
            print(f"Missing image {image}")
            return 1
        clip = clips_dir / f"scene_{scene['id']:03d}.mp4"
        duration = float(by_id[scene["id"]]["duration"])
        print(f"[clip {scene['id']:02d}/{len(scenes)}] {duration:.1f}s")
        make_clip(image, clip, duration, scene.get("camera", ""))
        clips.append(clip)

    silent = PROJECT / "video" / "silent.mp4"
    print("[concat] video")
    concat_clips(clips, silent)

    audio_files = [PROJECT / "audio" / f"scene_{s['id']:03d}.wav" for s in scenes]
    narration = PROJECT / "audio" / "narration.wav"
    print("[concat] narration")
    concat_audio(audio_files, narration)

    music = PROJECT / "audio" / "music.mp3"
    mixed = PROJECT / "audio" / "final_audio.wav"
    if args.no_music:
        mixed = narration
        print("[mix] narration only")
    else:
        if not music.exists():
            print("Missing audio/music.mp3; run music.py first or pass --no-music.")
            return 1
        volume = args.music_volume
        if volume is None:
            volume = float(CONFIG.get("music", {}).get("volume", 0.10))
        print(f"[mix] narration + music (music volume {volume:.2f})")
        mix_music(narration, music, mixed, volume)

    srt = PROJECT / "video" / "subtitles.srt"
    make_srt(scenes, timings, srt)
    print(f"[subs] {srt}")

    final = PROJECT / "video" / args.out_name
    print("[render] final")
    if args.no_subs:
        run(
            [
                "ffmpeg", "-y", "-i", str(silent), "-i", str(mixed),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", str(final),
            ]
        )
    else:
        run(
            [
                "ffmpeg", "-y", "-i", "silent.mp4", "-i", str(mixed),
                "-vf",
                "subtitles=subtitles.srt:force_style='FontName=Nirmala UI,FontSize=22,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
                "Outline=1,Shadow=0,MarginV=36'",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k", "-shortest", args.out_name,
            ],
            cwd=PROJECT / "video",
        )
    print(f"[done] {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
