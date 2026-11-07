"""Run the pilot pipeline step by step."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
TTS_PY = Path(r"D:\AI_Story_Channel\tts_env\Scripts\python.exe")
COMFY_SITE = r"D:\ComfyUI\ComfyUI_windows_portable\python_embeded\Lib\site-packages"


def run(script: str, *args: str, python: Path | None = None) -> int:
    cmd = [str(python or PY), str(ROOT / script), *args]
    env = os.environ.copy()
    env["PYTHONPATH"] = COMFY_SITE
    env["PYTHONIOENCODING"] = "utf-8"
    print("\n$", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT, env=env)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        choices=["all", "images", "music", "tts", "assemble"],
        default="all",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    steps = ["images", "music", "tts", "assemble"] if args.step == "all" else [args.step]
    for step in steps:
        if step == "images":
            code = run("images.py", *(["--limit", str(args.limit)] if args.limit else []), *(["--force"] if args.force else []))
        elif step == "music":
            code = run("music.py", *(["--force"] if args.force else []))
        elif step == "tts":
            if not TTS_PY.exists():
                print(f"TTS environment missing: {TTS_PY}")
                return 1
            code = run("tts.py", *(["--limit", str(args.limit)] if args.limit else []), *(["--force"] if args.force else []), python=TTS_PY)
        else:
            code = run("assemble.py")
        if code != 0:
            print(f"\nStep failed: {step} (exit {code})")
            return code
    print("\nPilot complete: projects/pilot_001/video/pilot.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
