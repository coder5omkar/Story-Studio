"""Generation and production operations for Story Studio."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import providers, qa, store
from .jobs import Job
from . import thumbnail

ROOT = store.ROOT
PIPELINE_DIR = store.PIPELINE_DIR
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
from hindi_text import normalize_for_tts  # noqa: E402

PIPELINE_PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PIPELINE_PY.exists():
    PIPELINE_PY = ROOT / "OpenMontage" / ".venv" / "Scripts" / "python.exe"
TTS_PY = ROOT / "tts_env" / "Scripts" / "python.exe"
COMFY_SITE = Path(os.environ.get(
    "COMFY_SITE_PACKAGES",
    r"D:\ComfyUI\ComfyUI_windows_portable\python_embeded\Lib\site-packages",
))

SYSTEM_STORY = (
    "आप एक अनुभवी हिंदी कहानीकार और पटकथा लेखक हैं। "
    "आप केवल शुद्ध, स्वाभाविक हिंदी (देवनागरी) में लिखते हैं। "
    "उपयोगकर्ता के विषय और निर्देशों का ठीक-ठीक पालन करते हैं। "
    "विषय से असंबंधित शैली, संदेश या उपकथा अपने से नहीं जोड़ते। "
    "भावनात्मक, सिनेमाई और सरल भाषा लिखते हैं।"
)


def _py() -> Path:
    return PIPELINE_PY if PIPELINE_PY.exists() else Path(sys.executable)


def _tts_py() -> Path:
    return TTS_PY if TTS_PY.exists() else Path(sys.executable)


def _clean_markdown(text: str) -> str:
    text = re.sub(r"^```(?:markdown|md)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip() + "\n"


def _line_progress(job: Job, line: str, prefix: str, base: float, span: float) -> None:
    """Map lines like [tts 03/30] to progress within a stage."""
    m = re.search(rf"\[(?:{prefix})\s+(\d+)/(\d+)\]", line)
    if m:
        cur, total = int(m.group(1)), max(1, int(m.group(2)))
        job.set_progress(base + span * cur / total, f"{prefix}: {cur}/{total}")


def _run_script(
    pid: str,
    state: dict,
    script: str,
    args: list[str],
    job: Job,
    *,
    python: Path | None = None,
    config_path: Path | None = None,
    on_line=None,
) -> None:
    cfg = config_path or store.write_project_config(pid, state)
    env = os.environ.copy()
    env["PIPELINE_CONFIG"] = str(cfg)
    env["PYTHONIOENCODING"] = "utf-8"
    if COMFY_SITE.exists():
        env["PYTHONPATH"] = str(COMFY_SITE) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [str(python or _py()), str(PIPELINE_DIR / script), *args]
    job.log("$ " + " ".join(str(c) for c in cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=str(PIPELINE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip()
        if not line:
            continue
        job.log(line)
        if on_line:
            on_line(line)
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"{script} exited with code {code}")


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------


def story_prompt(topic: str, words: int, minutes: float, chapters: int, instructions: str = "") -> str:
    extra = f"\nअतिरिक्त निर्देश:\n{instructions.strip()}\n" if instructions.strip() else ""
    return f"""
एक काल्पनिक हिंदी कहानी लिखें।

विषय: {topic}
लक्ष्य लंबाई: लगभग {words} शब्द (लगभग {minutes:g} मिनट का नैरेशन)।
{extra}
संरचना:
- कुल {chapters} अध्याय; हर अध्याय में कहानी को आगे बढ़ाने वाला एक स्पष्ट मोड़।
- मुख्य पात्र, उनकी परिस्थिति और केंद्रीय समस्या विषय और निर्देशों से ही लें।
- हर अध्याय के अंत में अगले अध्याय को जानने की उत्सुकता छोड़ें।
- कहानी का संतोषजनक अंत करें; कोई वाक्य अधूरा न छोड़ें।
- केवल वही ठोस विवरण जोड़ें जो कहानी की दुनिया और निर्देशों के अनुरूप हों।

नियम:
- असली व्यक्तियों, कंपनियों या ब्रांडों के नाम न रखें।
- विषय से असंबंधित शैली, संदेश या उपकथा न जोड़ें।
- भाषा सरल, भावनात्मक और संवाद-प्रधान हो।
- केवल कहानी लौटाएँ, कोई अतिरिक्त चर्चा नहीं।
""".strip()


def generate_story(
    pid: str,
    state: dict,
    job: Job,
    *,
    topic: str,
    minutes: float,
    chapters: int,
    instructions: str = "",
) -> dict:
    settings = state["settings"]
    target = max(200, int(minutes * 130))
    chapters = max(1, int(chapters or settings.get("story_chapters", 5)))
    instructions = (instructions or "").strip()
    state["settings"]["story_instructions"] = instructions
    extra = f"\nअतिरिक्त निर्देश:\n{instructions}\n" if instructions else ""

    if chapters <= 1:
        job.set_progress(5, "Writing story")
        text = providers.chat(
            settings,
            [
                {"role": "system", "content": SYSTEM_STORY},
                {"role": "user", "content": story_prompt(topic, target, minutes, chapters, instructions)},
            ],
            num_predict=min(8192, max(2048, target * 3)),
        )
        chunks = [_clean_markdown(text)]
    else:
        job.set_progress(2, "Writing chapter outline")
        outline_prompt = f"""
एक {chapters}-अध्याय वाली हिंदी कहानी की रूपरेखा बनाएँ।

विषय: {topic}
कुल लक्ष्य: लगभग {target} शब्द।
{extra}
हर अध्याय के लिए दें:
- अध्याय शीर्षक
- 3 मुख्य घटनाएँ/मोड़
- अध्याय का अंत जो अगले अध्याय की उत्सुकता बनाए

केवल क्रमांकित सूची लौटाएँ, कोई कहानी नहीं।
""".strip()
        outline = providers.chat(
            settings,
            [
                {"role": "system", "content": SYSTEM_STORY},
                {"role": "user", "content": outline_prompt},
            ],
            num_predict=min(4096, max(1200, chapters * 180)),
        )
        job.log("Outline ready")
        job.log(outline[:1200])

        part_words = max(80, round(target / chapters))
        chunks = []
        previous = ""
        for i in range(chapters):
            pct = 5 + 88 * i / chapters
            job.set_progress(pct, f"Writing chapter {i + 1}/{chapters}")
            ending_rule = (
                "- इस अंतिम अध्याय में कहानी का संतोषजनक अंत करें; कोई वाक्य अधूरा न छोड़ें।"
                if i == chapters - 1
                else "- अध्याय के अंत में अगले अध्याय की उत्सुकता छोड़ें; कहानी अभी समाप्त न करें।"
            )
            part_prompt = f"""
आप एक {chapters}-अध्याय वाली हिंदी कहानी लिख रहे हैं।

विषय: {topic}
कुल लक्ष्य: लगभग {target} शब्द।
यह भाग: अध्याय {i + 1} / {chapters}
इस अध्याय का लक्ष्य: लगभग {part_words} शब्द।
{extra}
पूरी कहानी की रूपरेखा:
{outline[:3500]}

पिछले अध्याय का अंत:
{previous[-1400:] if previous else "(यह पहला अध्याय है)"}

निर्देश:
- केवल अध्याय {i + 1} लिखें, पूरी कहानी नहीं।
- शुरुआत में "## अध्याय {i + 1}: <शीर्षक>" लिखें।
- सरल, भावनात्मक, संवाद-प्रधान हिंदी।
{ending_rule}
- असली व्यक्तियों, कंपनियों या ब्रांडों के नाम न रखें।
""".strip()
            part = providers.chat(
                settings,
                [
                    {"role": "system", "content": SYSTEM_STORY},
                    {"role": "user", "content": part_prompt},
                ],
                num_predict=min(8192, max(2048, part_words * 3)),
            )
            part = _clean_markdown(part)
            if not re.match(r"(?m)^\s*#", part):
                part = f"## अध्याय {i + 1}\n\n{part}"
            part_count = len(re.findall(r"\S+", part))
            if part_count < max(40, int(part_words * 0.6)):
                job.log(f"Chapter {i + 1} is short ({part_count} words); retrying once")
                retry = providers.chat(
                    settings,
                    [
                        {"role": "system", "content": SYSTEM_STORY},
                        {"role": "user", "content": part_prompt + f"\n\nपिछला प्रयास बहुत छोटा रह गया था। इस बार अध्याय को लगभग {part_words} शब्दों तक पूरा लिखें और अधूरा वाक्य न छोड़ें।"},
                    ],
                    num_predict=min(8192, max(2048, part_words * 3)),
                )
                retry = _clean_markdown(retry)
                if not re.match(r"(?m)^\s*#", retry):
                    retry = f"## अध्याय {i + 1}\n\n{retry}"
                retry_count = len(re.findall(r"\S+", retry))
                if retry_count > part_count:
                    part = retry
                    part_count = retry_count
            chunks.append(part)
            previous = part
            job.log(f"Chapter {i + 1}/{chapters} ready ({part_count} words)")

    text = "\n\n".join(chunks).strip() + "\n"
    paths = store.ensure_dirs(pid)
    store.version_artifact(pid, state, "story", paths["story"])
    paths["story"].write_text(text, encoding="utf-8")

    store.set_stage(state, "story", "draft", approved=False, notes="Generated draft")
    store.invalidate(state, [
        "scenes", "samples.voice", "samples.image", "samples.clip", "production", "final", "publish",
    ], "story changed")
    state["settings"]["story_topic"] = topic
    state["settings"]["story_minutes"] = minutes
    state["settings"]["story_chapters"] = chapters

    validation = qa.validate_story(text, target, expected_chapters=chapters)
    state["stages"]["story"]["validation"] = validation
    state["stages"]["story"]["words"] = len(re.findall(r"\S+", text))
    state["stages"]["story"]["target_words"] = target
    state["stages"]["story"]["expected_chapters"] = chapters
    store.save_state(pid, state)
    job.set_progress(100, "Story ready for review")
    return {"words": state["stages"]["story"]["words"], "validation": validation}


def save_story(pid: str, state: dict, text: str) -> dict:
    paths = store.ensure_dirs(pid)
    store.version_artifact(pid, state, "story", paths["story"])
    paths["story"].write_text(text, encoding="utf-8")
    store.set_stage(state, "story", "draft", approved=False, notes="Edited draft")
    store.invalidate(state, [
        "scenes", "samples.voice", "samples.image", "samples.clip", "production", "final", "publish",
    ], "story edited")
    target = int(float(state["settings"].get("story_minutes", 5)) * 130)
    expected = int(state["settings"].get("story_chapters", 0) or 0)
    validation = qa.validate_story(text, target, expected_chapters=expected)
    state["stages"]["story"]["validation"] = validation
    state["stages"]["story"]["words"] = len(re.findall(r"\S+", text))
    state["stages"]["story"]["target_words"] = target
    state["stages"]["story"]["expected_chapters"] = expected
    store.save_state(pid, state)
    return validation


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"^#.*$", "", text, flags=re.M)
    text = re.sub(r"^>.*$", "", text, flags=re.M)
    text = re.sub(r"\n{2,}", "\n", text)
    parts = re.split(r"(?<=[।?!])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _chunk_sentences(sentences: list[str], target: int = 24) -> list[str]:
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


def _normalize_camera(value: object) -> str:
    text = str(value).lower()
    if "pull" in text or "out" in text:
        return "slow pull back"
    if "left" in text:
        return "slow pan left"
    if "right" in text:
        return "slow pan right"
    return "slow push in"


FALLBACK_IMAGE_PROMPT = (
    "Indian middle-class story scene, clear composition, detailed background, "
    "emotional staging, no text, no watermark"
)


def _has_devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097f" for ch in text)


def _prompt_usable(prompt: object) -> bool:
    """Image models need English prompts of a useful length."""
    text = str(prompt or "").strip()
    return len(text) >= 20 and len(text.split()) >= 6 and not _has_devanagari(text)


TRANSLATE_SYSTEM = (
    "You are a bilingual translator. You read Hindi scene descriptions and write English "
    "image-generation prompts. You never write Devanagari in your output. "
    "You answer with plain English lines only."
)

TRANSLATE_EXAMPLES = """
Example 1
Hindi: एक आदमी सड़क पर चलता है, चिंतित।
English: A worried Indian man in his thirties walks along a busy Jaipur street, holding a smartphone, warm morning light, cinematic flat vector illustration, medium shot.

Example 2
Hindi: घर में बिलों के ढेर के सामने बैठा आदमी।
English: An Indian man sits at a cluttered dining table surrounded by unpaid bills, looking exhausted under a single warm lamp, flat vector illustration, wide shot.
""".strip()


def _parse_prompt_lines(raw: str) -> list[str]:
    text = (raw or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    if text[:1] in ("[", "{"):
        try:
            data = providers.extract_json(text)
            if isinstance(data, dict):
                for key in ("prompts", "images", "scenes", "results", "items"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break
                else:
                    data = list(data.values())
            if isinstance(data, list):
                out = []
                for item in data:
                    if isinstance(item, dict):
                        item = item.get("image_prompt") or item.get("prompt") or item.get("english") or ""
                    if isinstance(item, str):
                        out.append(item.strip())
                if out:
                    return out
        except Exception:
            pass
    out = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*• ").strip()
        line = re.sub(r"^\d+[.)]\s*", "", line)
        line = re.sub(r"^(?:English|Prompt)\s*:\s*", "", line, flags=re.I).strip()
        if not line or line.lower().startswith("hindi:"):
            continue
        out.append(line)
    return out


def _translate_prompt_lines(settings: dict, descriptions: list[str], job: Job) -> list[str]:
    """Line-based translation with few-shot examples. This is the most reliable
    shape for local multilingual models, which tend to ignore a JSON-only
    English instruction and answer in Hindi."""
    lines = "\n".join(f"Hindi: {text[:500]}" for text in descriptions)
    user = f"""
Translate every Hindi line below into one English image prompt of 25-45 words.
Describe subject, setting, action, emotion, lighting and camera framing.
English only. Never use Hindi words or Devanagari. No text inside the image.

{TRANSLATE_EXAMPLES}

Now translate these:
{lines}

Write exactly {len(descriptions)} lines. Start every line with "English:".
""".strip()
    job.log(f"Translating {len(descriptions)} prompt(s) into English")
    raw = providers.chat(
        settings,
        [{"role": "system", "content": TRANSLATE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.3,
        num_predict=max(900, len(descriptions) * 150),
    )
    parsed = _parse_prompt_lines(raw)
    values = [parsed[i] if i < len(parsed) else "" for i in range(len(descriptions))]
    good = sum(1 for value in values if _prompt_usable(value))
    job.log(f"English translation: {good}/{len(descriptions)} usable")
    return values


def _translate_prompt_json(settings: dict, descriptions: list[str], job: Job) -> list[str]:
    """Second attempt for models that prefer strict JSON output."""
    numbered = "\n".join(f"{n + 1}. {text[:500]}" for n, text in enumerate(descriptions))
    system = (
        "You convert Hindi or mixed-language scene descriptions into English image prompts "
        "for a flat-vector 2D animation. Return only valid JSON."
    )
    user = f"""
Rewrite each scene description as one English image prompt of 25-45 words.
Describe subject, setting, action, emotion, lighting and camera framing.
Use English only. Do not put any Hindi text in the prompt. No text inside the image.

Return a JSON array of exactly {len(descriptions)} strings:
["prompt one", "prompt two"]

Scene descriptions:
{numbered}
""".strip()
    job.log("Retrying prompt translation as JSON")
    raw = providers.chat(
        settings,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
        num_predict=max(1500, len(descriptions) * 170),
    )
    parsed = _parse_prompt_lines(raw)
    return [parsed[i] if i < len(parsed) else "" for i in range(len(descriptions))]


def _repair_image_prompts(settings: dict, prompts: list[str], job: Job) -> list[str]:
    """Rewrite Hindi/short image prompts into usable English prompts.

    Local models sometimes ignore the English-only instruction. We retry with a
    focused translation call (line format, few-shot), then JSON, and finally a
    safe generic prompt per scene so a batch can never be polluted with
    Devanagari prompts.
    """
    prompts = [str(p or "").strip() for p in prompts]
    bad = [i for i, p in enumerate(prompts) if not _prompt_usable(p)]
    if not bad:
        return prompts

    job.log(f"Restyling {len(bad)} image prompts into English")
    descriptions = [prompts[i] for i in bad]
    values: list[str] = [""] * len(bad)
    try:
        values = _translate_prompt_lines(settings, descriptions, job)
    except Exception as exc:
        job.log(f"Line translation failed ({exc})")

    missing = [i for i, value in enumerate(values) if not _prompt_usable(value)]
    if missing:
        try:
            retry = _translate_prompt_json(
                settings, [descriptions[i] for i in missing], job
            )
            for n, idx in enumerate(missing):
                if n < len(retry):
                    values[idx] = retry[n]
        except Exception as exc:
            job.log(f"JSON translation failed ({exc})")

    repaired = 0
    for n, idx in enumerate(bad):
        candidate = values[n] if n < len(values) else ""
        if _prompt_usable(candidate):
            prompts[idx] = candidate
            repaired += 1
        else:
            prompts[idx] = FALLBACK_IMAGE_PROMPT
    if repaired < len(bad):
        job.log(f"Used a safe fallback prompt for {len(bad) - repaired} scene(s)")
    job.log(f"Prompt repair done: {repaired}/{len(bad)} translated")
    return prompts


def repair_scene_prompts(pid: str, state: dict, job: Job) -> dict:
    """Fix non-English or too-short image prompts in an existing scene plan."""
    paths = store.ensure_dirs(pid)
    if not paths["scenes"].exists():
        raise RuntimeError("No scene plan to repair")
    scenes = json.loads(paths["scenes"].read_text(encoding="utf-8"))
    if not scenes:
        raise RuntimeError("Scene plan is empty")
    job.set_progress(10, "Restyling image prompts into English")
    repaired = _repair_image_prompts(
        state["settings"], [scene.get("image_prompt", "") for scene in scenes], job
    )
    changed = 0
    for scene, prompt in zip(scenes, repaired):
        if prompt != str(scene.get("image_prompt", "")).strip():
            scene["image_prompt"] = prompt
            changed += 1
    store.version_artifact(pid, state, "scenes", paths["scenes"])
    paths["scenes"].write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    validation = qa.validate_scenes(scenes)
    store.set_stage(
        state, "scenes", "draft", approved=False,
        notes=f"Repaired {changed} image prompt(s)", validation=validation,
    )
    store.invalidate(
        state, ["samples.image", "samples.clip", "production", "final"],
        "image prompts repaired",
    )
    store.save_state(pid, state)
    job.set_progress(100, f"Repaired {changed} prompt(s)")
    return {"changed": changed, "validation": validation}


def generate_scenes(pid: str, state: dict, job: Job, *, target_words: int = 24, batch_size: int = 12) -> dict:
    paths = store.ensure_dirs(pid)
    story = paths["story"].read_text(encoding="utf-8")
    chunks = _chunk_sentences(_split_sentences(story), target=target_words)
    if not chunks:
        raise RuntimeError("Story has no usable sentences")
    job.log(f"{len(chunks)} narration chunks")

    image_cfg = state.get("settings", {}).get("image", {})
    style_prefix = str(image_cfg.get("style_prefix", "")).strip()
    character = str(image_cfg.get("character", "")).strip()

    system = (
        "You are a storyboard artist for a Hindi story channel. "
        f"Visual style: {style_prefix}. "
        f"Character: {character}. "
        "For each Hindi narration chunk, write one concrete English image prompt of 25-45 words. "
        "Describe setting, action, emotion, camera framing and background. "
        "Follow the visual style and character description exactly; never contradict them. "
        "If the character is described as a simplified or non-realistic figure, do not add age, "
        "hair, beard, facial features or realistic clothing. "
        "English only: never use Devanagari or Hindi words in image_prompt. "
        "No text in the image. Return only a JSON array."
    )
    scenes: list[dict] = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(batch))
        user = f"""
For each narration chunk below, create one scene entry.

Visual style: {style_prefix}
Character: {character}

Follow that visual style and character consistently.

Return a JSON array with exactly {len(batch)} objects:
[
  {{"image_prompt": "English visual description", "camera": "slow push in|slow pull back|slow pan left|slow pan right", "mood": "one or two English words"}}
]

Narration chunks:
{numbered}
""".strip()
        try:
            raw = providers.chat(
                state["settings"],
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                num_predict=4096,
            )
            items = providers.extract_json(raw)
            if not isinstance(items, list):
                raise ValueError(f"expected JSON array, got {type(items).__name__}")
            while len(items) < len(batch):
                items.append({
                    "image_prompt": FALLBACK_IMAGE_PROMPT,
                    "camera": "slow push in",
                    "mood": "emotional",
                })
            items = items[:len(batch)]
            items = [item if isinstance(item, dict) else {"image_prompt": str(item)} for item in items]
        except Exception as exc:
            job.log(f"Batch {start // batch_size + 1} failed ({exc}); using fallback prompts")
            items = [{
                "image_prompt": FALLBACK_IMAGE_PROMPT,
                "camera": "slow push in",
                "mood": "emotional",
            } for _ in batch]

        repaired = _repair_image_prompts(
            state["settings"], [item.get("image_prompt", "") for item in items], job
        )
        for item, prompt in zip(items, repaired):
            item["image_prompt"] = prompt

        for narration, item in zip(batch, items):
            scenes.append({
                "id": len(scenes) + 1,
                "chapter": 0,
                "narration": narration,
                "image_prompt": item.get("image_prompt", ""),
                "camera": _normalize_camera(item.get("camera", "slow push in")),
                "mood": str(item.get("mood") or "emotional").strip()[:60],
            })
        done = min(len(chunks), start + len(batch))
        job.set_progress(5 + 90 * done / len(chunks), f"Scenes: {done}/{len(chunks)}")
        job.log(f"Batch {start // batch_size + 1}: {len(scenes)}/{len(chunks)}")

    store.version_artifact(pid, state, "scenes", paths["scenes"])
    paths["scenes"].write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    validation = qa.validate_scenes(scenes)
    store.set_stage(state, "scenes", "draft", approved=False, notes="Generated scene plan", validation=validation)
    store.invalidate(state, [
        "samples.voice", "samples.image", "samples.clip", "production", "final",
    ], "scene plan changed")
    store.save_state(pid, state)
    job.set_progress(100, "Scene plan ready for review")
    return {"scenes": len(scenes), "validation": validation}


def save_scenes(pid: str, state: dict, scenes: list) -> dict:
    paths = store.ensure_dirs(pid)
    store.version_artifact(pid, state, "scenes", paths["scenes"])
    paths["scenes"].write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    validation = qa.validate_scenes(scenes)
    store.set_stage(state, "scenes", "draft", approved=False, notes="Edited scene plan", validation=validation)
    store.invalidate(state, [
        "samples.voice", "samples.image", "samples.clip", "production", "final",
    ], "scene plan edited")
    store.save_state(pid, state)
    return validation


RESTYLE_SYSTEM = (
    "You rewrite scene descriptions to match a specific visual style for a Hindi story video. "
    "You keep the setting, action and emotion from the narration, and describe one concrete "
    "English image prompt per scene. Return only valid JSON."
)


def restyle_scene_prompts(pid: str, state: dict, job: Job) -> dict:
    """Rewrite existing scene prompts into the project's current visual style."""
    paths = store.ensure_dirs(pid)
    if not paths["scenes"].exists():
        raise RuntimeError("No scene plan to restyle")
    scenes = json.loads(paths["scenes"].read_text(encoding="utf-8"))
    if not scenes:
        raise RuntimeError("Scene plan is empty")

    image_cfg = state.get("settings", {}).get("image", {})
    style_prefix = str(image_cfg.get("style_prefix", "")).strip()
    character = str(image_cfg.get("character", "")).strip()
    job.set_progress(5, "Rewriting prompts for the current visual style")
    lines = []
    for i, scene in enumerate(scenes, 1):
        lines.append(
            f"{i}. Narration: {str(scene.get('narration', ''))[:700]}\n"
            f"   Old prompt: {str(scene.get('image_prompt', ''))[:350]}"
        )
    user = f"""
Rewrite each scene as one English image prompt of 25-45 words for this visual style.

Visual style: {style_prefix}
Character: {character}

Rules:
- Keep the setting, action and emotion from the narration.
- Follow the visual style and character description exactly; never contradict them.
- Remove details that conflict with the style or character.
- If the character is described as a simplified or non-realistic figure, do not add age, hair,
  beard, facial features or realistic clothing.
- Describe the background and camera framing. No text in the image.

Return a JSON array of exactly {len(scenes)} strings, in scene order.

Scenes:
{chr(10).join(lines)}
""".strip()
    raw = providers.chat(
        state["settings"],
        [{"role": "system", "content": RESTYLE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.4,
        num_predict=max(2000, len(scenes) * 160),
    )
    parsed = _parse_prompt_lines(raw)
    if not parsed:
        raise RuntimeError("The model returned no rewritten prompts; scene plan left unchanged")
    job.log(f"Rewrote {len(parsed)} prompt(s) for {len(scenes)} scene(s)")

    changed = 0
    for i, scene in enumerate(scenes):
        candidate = parsed[i] if i < len(parsed) else ""
        prompt = candidate if _prompt_usable(candidate) else FALLBACK_IMAGE_PROMPT
        if prompt != str(scene.get("image_prompt", "")).strip():
            scene["image_prompt"] = prompt
            changed += 1

    store.version_artifact(pid, state, "scenes", paths["scenes"])
    paths["scenes"].write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    validation = qa.validate_scenes(scenes)
    store.set_stage(
        state, "scenes", "draft", approved=False,
        notes=f"Restyled {changed} image prompt(s) for the current visual style",
        validation=validation,
    )
    store.invalidate(
        state, ["samples.image", "samples.clip", "production", "final"],
        "scene prompts restyled",
    )
    store.save_state(pid, state)
    job.set_progress(100, f"Restyled {changed} prompt(s)")
    return {"changed": changed, "validation": validation}


# ---------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------


def _scene_by_id(pid: str, scene_id: int) -> dict:
    scenes = json.loads(store.project_paths(pid)["scenes"].read_text(encoding="utf-8"))
    for scene in scenes:
        if int(scene.get("id", 0)) == int(scene_id):
            return scene
    raise RuntimeError(f"Scene {scene_id} not found")


def _rel(pid: str, path: Path) -> str:
    return path.relative_to(store.project_paths(pid)["root"]).as_posix()


def normalize_tts_text(text: str) -> str:
    return normalize_for_tts(text)


def generate_voice_sample(
    pid: str,
    state: dict,
    job: Job,
    *,
    text: str,
    scene_id: int | None = None,
    overrides: dict | None = None,
) -> dict:
    if not text.strip():
        raise RuntimeError("Voice sample text is empty")
    normalized = normalize_for_tts(text.strip())
    out = store.ensure_dirs(pid)["samples"] / "voice" / "sample.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    args = ["--text", text.strip(), "--out", str(out), "--force"]
    ov = overrides or {}
    if ov.get("reference"):
        args += ["--reference", str(ov["reference"])]
    if ov.get("exaggeration") is not None:
        args += ["--exaggeration", str(ov["exaggeration"])]
    if ov.get("cfg_weight") is not None:
        args += ["--cfg-weight", str(ov["cfg_weight"])]
    if ov.get("temperature") is not None:
        args += ["--temperature", str(ov["temperature"])]
    job.set_progress(10, "Loading Chatterbox")
    _run_script(pid, state, "tts.py", args, job, python=_tts_py())
    job.set_progress(90, "Checking audio and spoken text")
    validation = qa.merge_validation(
        qa.validate_audio(out),
        qa.validate_tts_text(normalized),
    )
    store.set_stage(state, "samples.voice", "ready" if validation["ok"] else "draft",
                    approved=False, notes="Voice sample generated")
    state["stages"]["samples"]["voice"].update({
        "path": _rel(pid, out),
        "text": text.strip(),
        "normalized_text": normalized,
        "scene_id": scene_id,
        "overrides": ov,
        "validation": validation,
    })
    store.invalidate(state, ["samples.clip", "production", "final"], "voice sample changed")
    store.save_state(pid, state)
    job.set_progress(100, "Voice sample ready")
    return {"path": _rel(pid, out), "validation": validation}


def generate_image_sample(
    pid: str,
    state: dict,
    job: Job,
    *,
    scene_id: int,
    engine: str,
    seed: int = 0,
) -> dict:
    scene = _scene_by_id(pid, scene_id)
    out_dir = store.ensure_dirs(pid)["samples"] / "image"
    args = ["--engine", engine, "--ids", str(scene_id), "--out-dir", str(out_dir), "--force"]
    if seed:
        args += ["--seed", str(seed)]
    job.set_progress(10, f"Rendering scene {scene_id} with {engine}")
    _run_script(pid, state, "images.py", args, job)
    out = out_dir / f"scene_{scene_id:03d}.png"
    if not out.exists():
        raise RuntimeError("Image was not produced; check ComfyUI")
    validation = qa.validate_image(out)
    store.set_stage(state, "samples.image", "ready" if validation["ok"] else "draft",
                    approved=False, notes=f"Image sample scene {scene_id}")
    state["stages"]["samples"]["image"].update({
        "path": _rel(pid, out),
        "scene_id": scene_id,
        "engine": engine,
        "seed": seed,
        "validation": validation,
        "scene": scene,
    })
    store.invalidate(state, ["samples.clip", "production", "final"], "image sample changed")
    store.save_state(pid, state)
    job.set_progress(100, "Image sample ready")
    return {"path": _rel(pid, out), "validation": validation}


def generate_music_sample(
    pid: str,
    state: dict,
    job: Job,
    *,
    prompt: str,
    duration: float,
    bpm: int,
    key: str,
) -> dict:
    out = store.ensure_dirs(pid)["samples"] / "music" / "sample.mp3"
    args = [
        "--duration", str(duration),
        "--prompt", prompt,
        "--bpm", str(bpm),
        "--key", key,
        "--out", str(out),
        "--force",
    ]
    job.set_progress(10, "Generating music with ACE-Step")
    _run_script(pid, state, "music.py", args, job)
    if not out.exists():
        raise RuntimeError("Music was not produced; check ComfyUI")
    validation = qa.validate_audio(out)
    store.set_stage(state, "samples.music", "ready" if validation["ok"] else "draft",
                    approved=False, notes="Music sample generated")
    state["stages"]["samples"]["music"].update({
        "path": _rel(pid, out),
        "prompt": prompt,
        "duration": duration,
        "bpm": bpm,
        "key": key,
        "validation": validation,
    })
    store.invalidate(state, ["samples.clip", "production", "final"], "music sample changed")
    store.save_state(pid, state)
    job.set_progress(100, "Music sample ready")
    return {"path": _rel(pid, out), "validation": validation}


def _duration(path: Path) -> float:
    try:
        return float(qa.probe(path).get("format", {}).get("duration") or 0)
    except Exception:
        return 0.0


def build_preview_clip(
    pid: str,
    state: dict,
    job: Job,
    *,
    scene_id: int,
    subtitles: bool,
    with_music: bool,
) -> dict:
    scene = _scene_by_id(pid, scene_id)
    paths = store.ensure_dirs(pid)
    sample = state["stages"]["samples"]

    image_sample = sample.get("image", {})
    image_path = None
    image_dir = paths["images"]
    if image_sample.get("scene_id") == scene_id and image_sample.get("path"):
        candidate = paths["root"] / image_sample["path"]
        if candidate.exists():
            image_path = candidate
            image_dir = candidate.parent
    if image_path is None:
        candidate = paths["images"] / f"scene_{scene_id:03d}.png"
        if candidate.exists():
            image_path = candidate
    if image_path is None:
        raise RuntimeError("No image available for this scene. Generate an image sample first.")

    voice_sample = sample.get("voice", {})
    voice_path = None
    if voice_sample.get("scene_id") == scene_id and voice_sample.get("path"):
        candidate = paths["root"] / voice_sample["path"]
        if candidate.exists():
            voice_path = candidate
    if voice_path is None:
        candidate = paths["audio"] / f"scene_{scene_id:03d}.wav"
        if candidate.exists():
            voice_path = candidate
    if voice_path is None:
        raise RuntimeError("No voice available for this scene. Generate a voice sample first.")

    music_sample = sample.get("music", {})
    music_path = None
    if with_music:
        if music_sample.get("path"):
            candidate = paths["root"] / music_sample["path"]
            if candidate.exists():
                music_path = candidate
        if music_path is None and (paths["audio"] / "music.mp3").exists():
            music_path = paths["audio"] / "music.mp3"

    preview = paths["samples"] / "clip" / "preview"
    if preview.exists():
        shutil.rmtree(preview)
    (preview / "audio").mkdir(parents=True, exist_ok=True)
    (preview / "video").mkdir(parents=True, exist_ok=True)
    (preview / "studio").mkdir(parents=True, exist_ok=True)

    one_scene = dict(scene)
    one_scene["id"] = scene_id
    (preview / "scenes.json").write_text(
        json.dumps([one_scene], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dest_voice = preview / "audio" / f"scene_{scene_id:03d}.wav"
    shutil.copy2(voice_path, dest_voice)
    duration = _duration(dest_voice)
    (preview / "audio" / "timings.json").write_text(
        json.dumps([{"id": scene_id, "file": dest_voice.name, "duration": round(duration, 3)}],
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if music_path:
        shutil.copy2(music_path, preview / "audio" / "music.mp3")

    cfg = store.write_config_for_dir(preview, state)
    args = [
        "--images-dir", str(image_dir),
        "--out-name", "preview.mp4",
    ]
    if not subtitles:
        args.append("--no-subs")
    if not music_path:
        args.append("--no-music")

    job.set_progress(10, "Rendering subtitle/voice/image preview")
    _run_script(pid, state, "assemble.py", args, job, config_path=cfg)
    out = preview / "video" / "preview.mp4"
    if not out.exists():
        raise RuntimeError("Preview clip was not produced")
    validation = qa.validate_video(out)
    store.set_stage(state, "samples.clip", "ready" if validation["ok"] else "draft",
                    approved=False, notes=f"Preview clip scene {scene_id}")
    state["stages"]["samples"]["clip"].update({
        "path": _rel(pid, out),
        "scene_id": scene_id,
        "subtitles": subtitles,
        "with_music": bool(music_path),
        "validation": validation,
        "duration": round(duration, 3),
    })
    store.invalidate(state, ["production", "final"], "preview clip changed")
    store.save_state(pid, state)
    job.set_progress(100, "Preview clip ready")
    return {"path": _rel(pid, out), "validation": validation}


# ---------------------------------------------------------------------------
# Production + final
# ---------------------------------------------------------------------------


def _require_approved(state: dict, path: str, label: str) -> None:
    node = store.stage(state, path)
    if not node.get("approved"):
        raise RuntimeError(f"Gate not approved: {label}. Approve it before starting batch production.")


def check_gates(state: dict, *, need_music: bool | None = None) -> dict:
    if need_music is None:
        need_music = bool(state.get("settings", {}).get("music", {}).get("enabled", True))
    gates = {
        "story": bool(store.stage(state, "story").get("approved")),
        "scenes": bool(store.stage(state, "scenes").get("approved")),
        "voice": bool(store.stage(state, "samples.voice").get("approved")),
        "image": bool(store.stage(state, "samples.image").get("approved")),
        "clip": bool(store.stage(state, "samples.clip").get("approved")),
        "music": bool(store.stage(state, "samples.music").get("approved")) or not need_music,
    }
    return {"ok": all(gates.values()), "gates": gates}


def start_production(
    pid: str,
    state: dict,
    job: Job,
    *,
    stages: list[str] | None = None,
    subtitles: bool | None = None,
) -> dict:
    stages = stages or ["images", "music", "tts", "assemble"]
    subtitles = bool(state["settings"].get("subtitles", True) if subtitles is None else subtitles)
    music_enabled = bool(state["settings"].get("music", {}).get("enabled", True))
    if not music_enabled:
        stages = [stage for stage in stages if stage != "music"]
    paths = store.ensure_dirs(pid)
    has_music = (paths["audio"] / "music.mp3").exists()
    # Only require the music gate when music will actually be mixed into the video.
    need_music = music_enabled and ("music" in stages or ("assemble" in stages and has_music))
    gates = check_gates(state, need_music=need_music)
    if not gates["ok"]:
        missing = [k for k, v in gates["gates"].items() if not v]
        raise RuntimeError("Approval gates missing: " + ", ".join(missing))

    scenes = json.loads(paths["scenes"].read_text(encoding="utf-8"))
    total = max(1, len(scenes))
    store.set_stage(state, "production", "running", approved=False, notes="Batch production started")
    store.save_state(pid, state)

    settings = state["settings"]
    engine = settings.get("image", {}).get("engine", "sdxl")
    weights = {"images": 45, "music": 15, "tts": 35, "assemble": 5}
    base = 0.0
    try:
        for stage_name in stages:
            span = weights.get(stage_name, 10)
            if stage_name == "images":
                job.set_progress(base, "Generating images")

                def image_line(line: str) -> None:
                    _line_progress(job, line, r"sdxl|zimage|ipadapter|faceid", base, span)

                _run_script(pid, state, "images.py", ["--engine", engine], job, on_line=image_line)
            elif stage_name == "music":
                job.set_progress(base, "Generating music bed")
                music = settings.get("music", {})
                if not (paths["audio"] / "music.mp3").exists():
                    _run_script(pid, state, "music.py", [
                        "--duration", str(music.get("duration", 300)),
                        "--prompt", str(music.get("prompt", "")),
                        "--bpm", str(music.get("bpm", 78)),
                        "--key", str(music.get("key", "C minor")),
                    ], job)
                else:
                    job.log("music.mp3 already exists; skipping")
            elif stage_name == "tts":
                job.set_progress(base, "Generating narration")

                def tts_line(line: str) -> None:
                    _line_progress(job, line, "tts", base, span)

                _run_script(pid, state, "tts.py", [], job, python=_tts_py(), on_line=tts_line)
            elif stage_name == "assemble":
                job.set_progress(base, "Assembling final video")
                args = ["--out-name", "final.mp4"]
                if not subtitles:
                    args.append("--no-subs")
                has_music = (paths["audio"] / "music.mp3").exists()
                if not music_enabled or not has_music:
                    args.append("--no-music")
                if music_enabled and not has_music:
                    job.log("Music file is missing; assembling without music.")
                _run_script(pid, state, "assemble.py", args, job)
            base += span
            job.set_progress(base, f"{stage_name} done")
    except Exception:
        store.set_stage(state, "production", "failed", approved=False, notes="Batch production failed")
        store.save_state(pid, state)
        raise

    final_path = paths["video"] / "final.mp4"
    validation = qa.validate_video(final_path) if final_path.exists() else None
    store.set_stage(state, "production", "done", approved=False,
                    notes="Batch production complete", validation=validation)
    store.set_stage(state, "final", "ready", approved=False,
                    notes="Final render ready for review",
                    path=_rel(pid, final_path) if final_path.exists() else "",
                    validation=validation)
    store.save_state(pid, state)
    job.set_progress(100, "Production complete")
    return {"final": _rel(pid, final_path) if final_path.exists() else "", "validation": validation}


def render_final(
    pid: str,
    state: dict,
    job: Job,
    *,
    subtitles: bool,
    out_name: str = "final.mp4",
) -> dict:
    paths = store.ensure_dirs(pid)
    args = ["--out-name", out_name]
    if not subtitles:
        args.append("--no-subs")
    has_music = (paths["audio"] / "music.mp3").exists()
    if not bool(state["settings"].get("music", {}).get("enabled", True)) or not has_music:
        args.append("--no-music")
    if not has_music:
        job.log("Music file is missing; assembling without music.")
    job.set_progress(5, "Assembling final video")
    _run_script(pid, state, "assemble.py", args, job)
    out = paths["video"] / out_name
    if not out.exists():
        raise RuntimeError("Final video was not produced")
    validation = qa.validate_video(out)
    store.set_stage(state, "final", "ready" if validation["ok"] else "draft",
                    approved=False, notes="Final render ready for review",
                    path=_rel(pid, out), validation=validation, subtitles=subtitles)
    store.set_stage(state, "production", "done", notes="Final assembled",
                    approved=store.stage(state, "production").get("approved", False))
    store.save_state(pid, state)
    job.set_progress(100, "Final render ready")
    return {"path": _rel(pid, out), "validation": validation}


def _publish_settings(state: dict) -> dict:
    defaults = store.default_settings().get("publish", {})
    current = state.get("settings", {}).get("publish", {})
    return {**defaults, **current}


PUBLISH_SYSTEM = (
    "You are a YouTube packaging editor for a Hindi storytelling channel. "
    "You write honest, curiosity-driven titles, descriptions and thumbnail text. "
    "Never reveal the ending. Never invent facts. Return only valid JSON."
)


def generate_publish_kit(pid: str, state: dict, job: Job) -> dict:
    paths = store.ensure_dirs(pid)
    story = paths["story"].read_text(encoding="utf-8").strip() if paths["story"].exists() else ""
    if not story:
        raise RuntimeError("Generate or write the story first")
    pub = _publish_settings(state)
    job.set_progress(10, "Writing titles and description")
    prompt = f"""
Channel name: {pub.get('channel_name', '')}
Channel tagline: {pub.get('channel_tagline', '')}
Contact email: {pub.get('contact_email', '')}
Default CTA: {pub.get('cta', '')}
Default hashtags: {pub.get('hashtags', '')}

Story:
{story[:12000]}

Create a YouTube publish kit for this story.

Requirements:
- titles: 5 catchy Hindi titles, each 35-70 characters. Honest curiosity, no fake claims, no ending spoilers. Include search-friendly words such as "Hindi Kahani" or "Emotional Story" where natural.
- best_title: the single strongest title. Include the channel name if it fits naturally.
- description: 1200-1800 characters in Hindi. Paragraph 1: hook and premise without spoiling the ending. Paragraph 2: what the viewer will feel/learn. Paragraph 3: moral, CTA, contact email and hashtags. Include a short fictional-story disclaimer. Use \n\n between paragraphs.
- tags: 12-18 short YouTube tags in Hindi/English, no # symbols.
- thumbnail_text: 3-5 high-impact Hindi words, maximum 28 characters, no punctuation other than a comma if needed.
- thumbnail_prompt: one English image-generation prompt, 25-50 words, for a cinematic YouTube thumbnail. Show the protagonist's face/emotion and one key story object or moment. Strong composition, leave negative space on the left or bottom for text, no text in the image, no watermark.

Return only this JSON object:
{{
  "titles": ["...", "..."],
  "best_title": "...",
  "description": "...",
  "tags": ["...", "..."],
  "thumbnail_text": "...",
  "thumbnail_prompt": "..."
}}
""".strip()
    raw = providers.chat(
        state["settings"],
        [{"role": "system", "content": PUBLISH_SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.75,
        num_predict=3200,
    )
    job.set_progress(70, "Parsing publish kit")
    data = providers.extract_json(raw)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected a JSON object, got {type(data).__name__}")

    titles = data.get("titles") or []
    if isinstance(titles, str):
        titles = [titles]
    titles = [str(t).strip() for t in titles if str(t).strip()][:6]
    best = str(data.get("best_title") or "").strip()
    if not best and titles:
        best = titles[0]
    if not best:
        best = f"{state.get('title', 'Hindi Story')} | Hindi Kahani"
    if best not in titles:
        titles.insert(0, best)

    description = str(data.get("description") or "").strip()
    if not description:
        raise RuntimeError("The model did not return a description; try regenerating")

    tags_raw = data.get("tags") or []
    if isinstance(tags_raw, str):
        tags_raw = re.split(r"[,;]+", tags_raw)
    tags = [str(tag).strip().lstrip("#") for tag in tags_raw if str(tag).strip()][:20]
    thumbnail_text = str(data.get("thumbnail_text") or "").strip()[:28]
    if not thumbnail_text:
        thumbnail_text = best.split("|")[0].strip()[:28]
    thumbnail_prompt = str(data.get("thumbnail_prompt") or "").strip()
    if not thumbnail_prompt:
        thumbnail_prompt = (
            "Cinematic YouTube thumbnail of the protagonist in a tense emotional moment, "
            "strong face lighting, one symbolic story object, Indian middle-class setting, "
            "dramatic composition with empty space on the left for text, no text, no watermark"
        )

    store.set_stage(state, "publish", "ready", approved=False, notes="Publish kit generated")
    state["stages"]["publish"].update({
        "title_options": titles,
        "title": best,
        "description": description,
        "tags": ", ".join(tags),
        "thumbnail_text": thumbnail_text,
        "thumbnail_prompt": thumbnail_prompt,
        "thumbnail_path": "",
        "thumbnail_status": "empty",
        "generated_at": store.now(),
    })
    store.save_state(pid, state)
    job.set_progress(100, "Publish kit ready")
    return {"title": best, "description_chars": len(description), "tags": len(tags)}


def save_publish_kit(pid: str, state: dict, payload: dict) -> dict:
    node = store.stage(state, "publish")
    old_text = str(node.get("thumbnail_rendered_text") or node.get("thumbnail_text") or "")
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    tags = str(payload.get("tags", "")).strip()
    thumbnail_text = str(payload.get("thumbnail_text", "")).strip()[:28]
    if not title:
        raise RuntimeError("Title cannot be empty")
    if not description:
        raise RuntimeError("Description cannot be empty")
    node.update({
        "title": title,
        "description": description,
        "tags": tags,
        "thumbnail_text": thumbnail_text,
    })
    if node.get("thumbnail_path"):
        node["thumbnail_status"] = "ready" if thumbnail_text == old_text else "stale"
    store.set_stage(state, "publish", "ready", approved=False, notes="Publish kit edited")
    store.save_state(pid, state)
    return {"ok": True, "thumbnail_status": node.get("thumbnail_status", "empty")}

def generate_thumbnail(pid: str, state: dict, job: Job, *, engine: str | None = None) -> dict:
    paths = store.ensure_dirs(pid)
    node = store.stage(state, "publish")
    prompt = str(node.get("thumbnail_prompt") or "").strip()
    if not prompt:
        raise RuntimeError("Generate the publish kit first so a thumbnail prompt exists")
    settings = state["settings"]
    engine = engine or settings.get("image", {}).get("engine", "zimage")
    work = paths["samples"] / "thumbnail"
    render = work / "render"
    if render.exists():
        shutil.rmtree(render)
    (render / "images").mkdir(parents=True, exist_ok=True)
    scene = {
        "id": 1,
        "chapter": 0,
        "narration": "",
        "image_prompt": prompt,
        "camera": "slow push in",
        "mood": "dramatic",
    }
    (render / "scenes.json").write_text(
        json.dumps([scene], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cfg = store.write_config_for_dir(render, state)
    job.set_progress(10, "Rendering thumbnail base")
    _run_script(
        pid, state, "images.py",
        ["--engine", engine, "--ids", "1", "--out-dir", str(render / "images"), "--force"],
        job, config_path=cfg,
    )
    base = render / "images" / "scene_001.png"
    if not base.exists():
        raise RuntimeError("Thumbnail base image was not produced; check ComfyUI")
    job.set_progress(85, "Adding thumbnail text")
    pub = _publish_settings(state)
    out = work / "thumbnail.png"
    width, height = thumbnail.render_thumbnail(
        base,
        out,
        str(node.get("thumbnail_text") or node.get("title") or "एक कहानी"),
        str(pub.get("channel_name") or ""),
        str(pub.get("channel_tagline") or ""),
    )
    validation = qa.validate_image(out)
    store.set_stage(state, "publish", "ready", approved=False, notes="Thumbnail generated")
    node.update({
        "thumbnail_path": _rel(pid, out),
        "thumbnail_status": "ready",
        "thumbnail_rendered_text": str(node.get("thumbnail_text") or ""),
        "thumbnail_engine": engine,
        "thumbnail_validation": validation,
        "thumbnail_size": [width, height],
        "thumbnail_updated_at": store.now(),
    })
    store.save_state(pid, state)
    job.set_progress(100, "Thumbnail ready")
    return {"path": _rel(pid, out), "validation": validation}


def retry_scene(pid: str, state: dict, job: Job, *, scene_id: int, kind: str) -> dict:
    if kind == "image":
        engine = state["settings"].get("image", {}).get("engine", "sdxl")
        _run_script(pid, state, "images.py", ["--engine", engine, "--ids", str(scene_id), "--force"], job)
    elif kind == "voice":
        _run_script(pid, state, "tts.py", ["--ids", str(scene_id), "--force"], job, python=_tts_py())
    else:
        raise RuntimeError(f"Unknown retry kind: {kind}")
    job.set_progress(100, f"Scene {scene_id} {kind} regenerated")
    return {"scene_id": scene_id, "kind": kind}
