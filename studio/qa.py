"""Automated quality checks used by the studio approval gates."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def _check(cid: str, label: str, status: str, detail: str) -> dict:
    return {"id": cid, "label": label, "status": status, "detail": detail}


def _result(checks: list[dict]) -> dict:
    fails = sum(1 for c in checks if c["status"] == "fail")
    warns = sum(1 for c in checks if c["status"] == "warn")
    score = round(100 * (len(checks) - fails - 0.5 * warns) / max(1, len(checks)))
    return {"ok": fails == 0, "score": max(0, score), "checks": checks}


def _devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    dev = sum(1 for c in letters if "\u0900" <= c <= "\u097f")
    return dev / len(letters)


def _words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def validate_story(text: str, target_words: int, expected_chapters: int | None = None) -> dict:
    text = text or ""
    words = _words(text)
    checks = []

    low, high = target_words * 0.65, target_words * 1.45
    if words == 0:
        checks.append(_check("length", "Story length", "fail", "Story is empty"))
    elif words < low:
        checks.append(
            _check(
                "length", "Story length", "fail",
                f"Only {words} words; target ~{target_words}. The story is incomplete.",
            )
        )
    elif words <= high:
        checks.append(_check("length", "Story length", "pass", f"{words} words (target ~{target_words})"))
    else:
        checks.append(_check("length", "Story length", "warn", f"{words} words; target ~{target_words}"))

    chapter_lines = re.findall(r"(?m)^\s*#{2,3}\s+.+$", text)
    chapters = len(chapter_lines)
    if chapters == 0:
        chapters = len(re.findall(r"अध्याय\s*[0-9०-९一二三四五六七八九十]+", text))
    required = int(expected_chapters or 3)
    if chapters >= required:
        checks.append(_check("structure", "Chapter structure", "pass", f"{chapters} chapter headings found"))
    elif chapters == 0:
        checks.append(_check("structure", "Chapter structure", "warn", "No chapter headings detected"))
    else:
        checks.append(
            _check(
                "structure", "Chapter structure", "warn",
                f"Only {chapters} chapter headings; expected about {required}",
            )
        )

    ratio = _devanagari_ratio(text)
    if ratio >= 0.55:
        checks.append(_check("language", "Hindi language", "pass", f"{ratio:.0%} Devanagari letters"))
    elif ratio >= 0.25:
        checks.append(_check("language", "Hindi language", "warn", f"{ratio:.0%} Devanagari letters"))
    else:
        checks.append(_check("language", "Hindi language", "fail", f"Only {ratio:.0%} Devanagari letters"))

    stripped = re.sub(r"[\s*_`#]+$", "", text.strip())
    completed = bool(stripped) and stripped.endswith(("।", "!", "?", ".", "…", '"', "”", "’", "'"))
    if completed:
        checks.append(_check("ending", "Story ending", "pass", "Ends with completed punctuation"))
    else:
        checks.append(_check("ending", "Story ending", "fail", "Story ends mid-sentence or without terminal punctuation"))

    numbers = re.findall(r"\d[\d,]*", text)
    checks.append(
        _check(
            "details", "Concrete details", "pass" if len(numbers) >= 3 else "warn",
            f"{len(numbers)} numeric details found" if numbers else "Add concrete details only if the story needs them",
        )
    )

    sentences = [s.strip() for s in re.split(r"[।?!]\s*", text) if len(s.strip()) > 12]
    repeated = max((sentences.count(s) for s in set(sentences)), default=0)
    checks.append(
        _check("repetition", "Repetition", "pass" if repeated <= 2 else "warn",
               f"Most repeated sentence appears {repeated} times")
    )
    return _result(checks)


def validate_scenes(scenes: list) -> dict:
    checks = []
    if not isinstance(scenes, list) or not scenes:
        return _result([_check("scenes", "Scene plan", "fail", "No scenes found")])

    checks.append(_check("count", "Scene count", "pass" if len(scenes) >= 1 else "fail", f"{len(scenes)} scenes"))

    ids = [s.get("id") for s in scenes]
    sequential = ids == list(range(1, len(scenes) + 1))
    checks.append(
        _check("ids", "Scene IDs", "pass" if sequential else "warn",
               "IDs are sequential" if sequential else "IDs are not sequential")
    )

    empty = sum(1 for s in scenes if not str(s.get("narration", "")).strip())
    checks.append(
        _check("narration", "Narration text", "pass" if empty == 0 else "fail",
               f"{empty} scenes missing narration" if empty else "Every scene has narration")
    )

    bad_prompts = 0
    for s in scenes:
        prompt = str(s.get("image_prompt", ""))
        if _devanagari_ratio(prompt) > 0.05 or len(prompt.strip()) < 12:
            bad_prompts += 1
    checks.append(
        _check("prompts", "English image prompts", "pass" if bad_prompts == 0 else "warn",
               f"{bad_prompts} prompts look non-English or too short" if bad_prompts else "All prompts look usable")
    )

    cameras = {"slow push in", "slow pull back", "slow pan left", "slow pan right"}
    bad_camera = sum(1 for s in scenes if s.get("camera") not in cameras)
    checks.append(
        _check("camera", "Camera moves", "pass" if bad_camera == 0 else "warn",
               f"{bad_camera} scenes use an unknown camera move" if bad_camera else "Camera vocabulary is valid")
    )

    word_counts = [_words(str(s.get("narration", ""))) for s in scenes]
    avg = sum(word_counts) / max(1, len(word_counts))
    if 8 <= avg <= 55:
        checks.append(_check("pacing", "Scene pacing", "pass", f"Average {avg:.0f} words/scene"))
    else:
        checks.append(_check("pacing", "Scene pacing", "warn", f"Average {avg:.0f} words/scene; review pacing"))

    missing_mood = sum(1 for s in scenes if not str(s.get("mood", "")).strip())
    checks.append(
        _check("mood", "Mood tags", "pass" if missing_mood == 0 else "warn",
               f"{missing_mood} scenes missing mood" if missing_mood else "Mood tags present")
    )

    total_words = sum(word_counts)
    minutes = total_words / 2.4 / 60
    checks.append(
        _check("duration", "Estimated duration", "pass", f"~{minutes:.1f} min at 2.4 words/sec")
    )
    return _result(checks)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
    )


def probe(path: Path) -> dict:
    proc = _run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,channels,sample_rate",
        "-of", "json", str(path),
    ])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:] or "ffprobe failed")
    return json.loads(proc.stdout or "{}")


def audio_stats(path: Path) -> dict:
    info = probe(path)
    duration = float(info.get("format", {}).get("duration") or 0)
    streams = info.get("streams", [])
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    vol = _run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    text = (vol.stderr or "") + (vol.stdout or "")
    mean = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", text)
    peak = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", text)
    return {
        "duration": round(duration, 3),
        "codec": audio.get("codec_name", ""),
        "channels": audio.get("channels"),
        "sample_rate": audio.get("sample_rate"),
        "mean_db": float(mean.group(1)) if mean else None,
        "peak_db": float(peak.group(1)) if peak else None,
        "size": int(info.get("format", {}).get("size") or path.stat().st_size),
    }


def validate_tts_text(text: str) -> dict:
    """Check that narration has been converted to spoken Hindi before TTS."""
    text = (text or "").strip()
    checks = []
    if not text:
        return _result([_check("text", "Spoken text", "fail", "Normalized narration is empty")])

    digits = re.findall(r"[0-9०-९]", text)
    checks.append(
        _check(
            "digits",
            "Digits spelled out",
            "pass" if not digits else "fail",
            "No digits remain" if not digits else f"{len(digits)} digit(s) still present",
        )
    )
    symbols = [s for s in ("₹", "%", "Rs", "INR") if s in text]
    checks.append(
        _check(
            "symbols",
            "Currency / percent",
            "pass" if not symbols else "fail",
            "Currency and percentages were converted" if not symbols else f"Still present: {', '.join(symbols)}",
        )
    )
    latin = sorted(set(re.findall(r"[A-Za-z]{2,}", text)))
    checks.append(
        _check(
            "latin",
            "English words",
            "pass" if not latin else "warn",
            "No Latin words" if not latin else f"Check pronunciation: {', '.join(latin[:6])}",
        )
    )
    checks.append(
        _check(
            "length",
            "Spoken length",
            "pass" if len(text) > 20 else "warn",
            f"{len(text)} characters",
        )
    )
    return _result(checks)


def merge_validation(*results: dict) -> dict:
    checks: list[dict] = []
    for result in results:
        checks.extend(result.get("checks", []))
    return _result(checks)


def validate_audio(path: Path) -> dict:
    checks = []
    try:
        s = audio_stats(path)
    except Exception as exc:
        return _result([_check("readable", "Audio file", "fail", str(exc))])

    checks.append(
        _check("duration", "Duration", "pass" if s["duration"] > 1 else "fail",
               f"{s['duration']:.1f} seconds")
    )
    if s["mean_db"] is None:
        checks.append(_check("level", "Audio level", "warn", "Could not measure volume"))
    elif s["mean_db"] > -35:
        checks.append(_check("level", "Audio level", "pass", f"Mean {s['mean_db']:.1f} dB"))
    elif s["mean_db"] > -45:
        checks.append(_check("level", "Audio level", "warn", f"Quiet: mean {s['mean_db']:.1f} dB"))
    else:
        checks.append(_check("level", "Audio level", "fail", f"Too quiet: mean {s['mean_db']:.1f} dB"))

    if s["peak_db"] is not None and s["peak_db"] > -0.5:
        checks.append(_check("clip", "Clipping", "warn", f"Peak {s['peak_db']:.1f} dB may clip"))
    else:
        checks.append(_check("clip", "Clipping", "pass", "No clipping detected"))
    return _result(checks)


def image_stats(path: Path) -> dict:
    from PIL import Image, ImageStat

    with Image.open(path) as img:
        img = img.convert("RGB")
        width, height = img.size
        stat = ImageStat.Stat(img.convert("L"))
        brightness = float(stat.mean[0])
    return {
        "width": width,
        "height": height,
        "brightness": round(brightness, 1),
        "size": path.stat().st_size,
        "ratio": round(width / height, 3) if height else 0,
    }


def validate_image(path: Path) -> dict:
    checks = []
    try:
        s = image_stats(path)
    except Exception as exc:
        return _result([_check("readable", "Image file", "fail", str(exc))])

    checks.append(
        _check("size", "Resolution", "pass" if min(s["width"], s["height"]) >= 512 else "warn",
               f"{s['width']}x{s['height']}")
    )
    checks.append(
        _check("aspect", "Aspect ratio", "pass" if 1.5 <= s["ratio"] <= 2.1 else "warn",
               f"{s['ratio']:.2f} (16:9 is 1.78)")
    )
    if 12 <= s["brightness"] <= 245:
        checks.append(_check("brightness", "Exposure", "pass", f"Mean brightness {s['brightness']}"))
    else:
        checks.append(_check("brightness", "Exposure", "warn", f"Mean brightness {s['brightness']}"))
    checks.append(
        _check("filesize", "File size", "pass" if s["size"] > 20_000 else "warn",
               f"{s['size'] / 1024:.0f} KB")
    )
    return _result(checks)


def validate_video(path: Path) -> dict:
    checks = []
    try:
        info = probe(path)
    except Exception as exc:
        return _result([_check("readable", "Video file", "fail", str(exc))])

    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(info.get("format", {}).get("duration") or 0)
    size = int(info.get("format", {}).get("size") or path.stat().st_size)

    checks.append(_check("video", "Video stream", "pass" if video else "fail",
                         f"{video.get('codec_name')} {video.get('width')}x{video.get('height')}" if video else "Missing video stream"))
    checks.append(_check("audio", "Audio stream", "pass" if audio else "warn",
                         f"{audio.get('codec_name')} {audio.get('channels')}ch" if audio else "No audio stream"))
    checks.append(_check("duration", "Duration", "pass" if duration > 1 else "fail", f"{duration:.1f} seconds"))
    checks.append(_check("filesize", "File size", "pass" if size > 500_000 else "warn", f"{size / 1024 / 1024:.1f} MB"))
    return _result(checks)


def summarize_scene_status(scenes: list, project_root: Path) -> list[dict]:
    timings = {}
    timing_path = project_root / "audio" / "timings.json"
    if timing_path.exists():
        try:
            timings = {t["id"]: t for t in json.loads(timing_path.read_text(encoding="utf-8"))}
        except Exception:
            timings = {}
    out = []
    for scene in scenes:
        sid = scene.get("id")
        image = project_root / "images" / f"scene_{sid:03d}.png"
        audio = project_root / "audio" / f"scene_{sid:03d}.wav"
        timing = timings.get(sid, {})
        out.append({
            "id": sid,
            "image": image.exists(),
            "audio": audio.exists(),
            "duration": timing.get("duration"),
            "words": _words(str(scene.get("narration", ""))),
        })
    return out
