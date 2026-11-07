"""Genre and story-idea library for the Story Studio idea lab.

The library is a local JSON file so ideas survive across projects. The LLM is
only used to propose genres and story blueprints; the user always chooses what
gets produced.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import providers, store

LIBRARY_PATH = store.STUDIO_DIR / ".story_ideas.json"

DEFAULT_SETTINGS = {
    "provider": "opencode-go",
    "model": "claude-haiku-5-5",
    "api_base": store.OPENCODE_GO_BASE,
    "temperature": 0.9,
}

GENRE_SYSTEM = (
    "You are a YouTube audience strategist who designs channel portfolios for "
    "Hindi audio-story channels. You think in terms of retention, bingeability, "
    "search demand and repeatable story engines. You return only valid JSON."
)

GENRE_PROMPT = """
Design exactly 5 genre pillars for Hindi audio-story YouTube channels.

Rules:
- Each genre must support its own channel identity and an endless supply of fresh stories.
- Genres must be mutually distinct in audience, tone, emotional promise and visual world. No overlapping niches.
- Optimize for narrated audio: strong first-15-second hooks, open loops, chapter cliffhangers,
  and emotional payoffs every 2-3 minutes.
- Indian middle-class settings and universal emotions. Avoid party politics, sensitive religious
  claims, real people, companies and brands.
- Avoid generic labels such as "comedy" or "drama"; each genre needs a repeatable story engine.
- Give each genre a Hindi channel name and a Hindi tagline that sound like a real channel.

Return a JSON array of exactly 5 objects with this shape:
{
  "name": "English genre name",
  "name_hi": "Hindi name",
  "description": "2-3 sentences in English: the promise and the world of this genre",
  "why_it_works": "2 sentences in English: retention and audience logic",
  "audience": "who this is for, in English",
  "channel_name": "Hindi channel name",
  "channel_tagline": "Hindi tagline",
  "tone": "English tone words",
  "themes": ["3 repeatable story engines"],
  "visual_style": "one short English description of the visual world",
  "example_titles": ["3 Hindi title examples"]
}
""".strip()

IDEA_SYSTEM = (
    "You are a master story architect for Hindi audio dramas and a YouTube "
    "retention editor. You create original, emotionally addictive, "
    "production-ready plots. You write concrete plots with scenes, reveals and "
    "payoffs, never vague premises. You return only valid JSON."
)

IDEA_PROMPT = """
Create exactly 3 distinct, production-ready story concepts for this channel.

Genre: {name} ({name_hi})
Channel: {channel_name} — {channel_tagline}
Audience: {audience}
Tone: {tone}
Core story engines: {themes}
Target: about {minutes} minutes of Hindi narration (~{words} words), {chapters} chapters.

Craft rules:
1. The first 15 seconds must open a question the listener needs answered.
2. The protagonist wants something concrete and is flawed in a way that costs them.
3. A midpoint reversal must change what the listener thinks the story is about.
4. There must be a dark moment where the easy way out is tempting.
5. The climax must be caused by the protagonist's own choice, not coincidence.
6. The ending must be surprising yet inevitable, and must pay off an early detail.
7. The final chapter must resolve the central question and show the consequence of the
   protagonist's choice. Do not end on a cliffhanger or an open-ended final line.
8. Every chapter except the last must end on an unresolved question or a new complication.
9. Keep locations limited and the story producible as 30-60 narrated scenes.
10. Use Indian middle-class specificity, small physical details and moral dilemmas.
11. No clichés, no melodrama for its own sake, no evil-for-no-reason villain,
    no dream sequences used to escape a corner, no deus ex machina.
12. Each of the 3 concepts must differ in central conflict, twist and emotional question.

Avoid these existing ideas for this genre:
{existing}

Return a JSON array of exactly 3 objects:
{{
  "title": "Hindi title, 4-9 words, curiosity without clickbait",
  "title_en": "English translation",
  "logline": "one Hindi sentence",
  "hook": "2-4 Hindi sentences that open the story",
  "premise": "300-450 Hindi words: full plot with beginning, midpoint reversal, climax and ending",
  "ending": "2-3 Hindi sentences with the final resolution, the protagonist's choice and the emotional payoff",
  "protagonist": "2 sentences, Hindi or English",
  "antagonist": "2 sentences, Hindi or English",
  "emotional_arc": "1-2 Hindi sentences",
  "retention_beats": ["exactly 5 short English beats"],
  "chapter_breaks": ["exactly {chapters} Hindi chapter-ending beats; the last one is the resolution/payoff, not a cliffhanger"],
  "why_it_hooks": "2 English sentences",
  "thumbnail_moment": "one English sentence",
  "minutes": {minutes},
  "chapters": {chapters}
}}
""".strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()
    return slug[:48] or f"genre-{uuid.uuid4().hex[:8]}"


def _list(value, limit: int = 8) -> list[str]:
    if isinstance(value, str):
        value = re.split(r"[,;]\s*", value)
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        text = _clean(item)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def load_library() -> dict:
    data: dict = {}
    if LIBRARY_PATH.exists():
        try:
            data = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("version", 1)
    settings = data.setdefault("settings", {})
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)
    settings.setdefault("session_id", "ses_" + uuid.uuid4().hex)
    data.setdefault("genres", [])
    data.setdefault("ideas", [])
    if not isinstance(data["genres"], list):
        data["genres"] = []
    if not isinstance(data["ideas"], list):
        data["ideas"] = []
    return data


def save_library(data: dict) -> None:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = LIBRARY_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(LIBRARY_PATH)


def public_library(data: dict) -> dict:
    counts: dict[str, int] = {}
    for idea in data.get("ideas", []):
        gid = idea.get("genre_id", "")
        counts[gid] = counts.get(gid, 0) + 1
    genres = []
    for genre in data.get("genres", []):
        item = {**genre, "idea_count": counts.get(genre.get("id", ""), 0)}
        genres.append(item)
    genres.sort(key=lambda item: 0 if item.get("source") == "user" else 1)
    ideas = sorted(
        data.get("ideas", []),
        key=lambda item: str(item.get("created_at", "")),
        reverse=True,
    )
    return {
        "settings": data.get("settings", {}),
        "genres": genres,
        "ideas": ideas,
    }


def update_settings(data: dict, payload: dict) -> dict:
    settings = data.setdefault("settings", {})
    provider = _clean(payload.get("provider") or settings.get("provider"))
    model = _clean(payload.get("model") or settings.get("model"))
    api_base = _clean(payload.get("api_base") or settings.get("api_base"))
    if provider:
        settings["provider"] = provider
    if model:
        settings["model"] = model
    if api_base:
        settings["api_base"] = providers.normalize_api_base(api_base)
    if "temperature" in payload:
        try:
            settings["temperature"] = max(0.1, min(1.2, float(payload["temperature"])))
        except Exception:
            pass
    settings.setdefault("session_id", "ses_" + uuid.uuid4().hex)
    return settings


def _chat(data: dict, messages: list[dict], *, num_predict: int, temperature: float | None = None) -> str:
    settings = data["settings"]
    return providers.chat(
        {"llm": settings},
        messages,
        model=settings.get("model"),
        temperature=settings.get("temperature", 0.9) if temperature is None else temperature,
        num_predict=num_predict,
    )


def _as_list(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("genres", "ideas", "items", "data", "stories"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _normalize_genre(item: dict, source: str) -> dict | None:
    if not isinstance(item, dict):
        return None
    name = _clean(item.get("name"))
    if not name:
        return None
    return {
        "id": _slug(name),
        "name": name,
        "name_hi": _clean(item.get("name_hi")) or name,
        "description": _clean(item.get("description")),
        "why_it_works": _clean(item.get("why_it_works")),
        "audience": _clean(item.get("audience")),
        "channel_name": _clean(item.get("channel_name")),
        "channel_tagline": _clean(item.get("channel_tagline")),
        "tone": _clean(item.get("tone")),
        "themes": _list(item.get("themes"), 5),
        "visual_style": _clean(item.get("visual_style")),
        "example_titles": _list(item.get("example_titles"), 5),
        "source": source,
        "created_at": _now(),
    }


def suggest_genres(data: dict) -> dict:
    prompt = GENRE_PROMPT
    items: list = []
    for attempt in range(2):
        raw = _chat(
            data,
            [{"role": "system", "content": GENRE_SYSTEM}, {"role": "user", "content": prompt}],
            num_predict=5000,
            temperature=0.9,
        )
        items = _as_list(providers.extract_json(raw))
        if len(items) >= 5:
            items = items[:5]
            break
        prompt = (
            GENRE_PROMPT
            + f"\n\nYour previous response contained {len(items)} genres. "
            + "Return exactly 5 distinct genres this time."
        )
    if len(items) < 5:
        raise RuntimeError(f"The model returned {len(items)} genres; expected 5. Try again.")

    genres = [_normalize_genre(item, "llm") for item in items]
    genres = [genre for genre in genres if genre]
    if len(genres) < 5:
        raise RuntimeError("The model returned genres with missing names; try again.")

    existing = data.get("genres", [])
    kept: list[dict] = []
    for genre in existing:
        if genre.get("source") == "user":
            kept.append(genre)
        elif any(idea.get("genre_id") == genre.get("id") for idea in data.get("ideas", [])):
            # Never orphan ideas the user may already be producing.
            kept.append(genre)
    used_ids = {genre.get("id") for genre in kept}
    for genre in genres:
        base = genre["id"]
        candidate = base
        counter = 2
        while candidate in used_ids:
            candidate = f"{base}-{counter}"
            counter += 1
        genre["id"] = candidate
        used_ids.add(candidate)
        kept.append(genre)
    data["genres"] = kept
    save_library(data)
    return public_library(data)


def add_user_genre(data: dict, payload: dict) -> dict:
    name = _clean(payload.get("name"))
    if not name:
        raise RuntimeError("Genre name is required")
    genre = _normalize_genre(
        {
            "name": name,
            "name_hi": payload.get("name_hi"),
            "description": payload.get("description"),
            "why_it_works": payload.get("why_it_works"),
            "audience": payload.get("audience"),
            "tone": payload.get("tone"),
            "channel_name": payload.get("channel_name"),
            "channel_tagline": payload.get("channel_tagline"),
            "themes": payload.get("themes"),
            "visual_style": payload.get("visual_style"),
        },
        "user",
    )
    if not genre:
        raise RuntimeError("Could not save this genre")
    used_ids = {item.get("id") for item in data.get("genres", [])}
    base = genre["id"]
    candidate = base
    counter = 2
    while candidate in used_ids:
        candidate = f"{base}-{counter}"
        counter += 1
    genre["id"] = candidate
    data.setdefault("genres", []).append(genre)
    save_library(data)
    return public_library(data)


def _normalize_idea(item: dict, genre: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    title = _clean(item.get("title"))
    if not title:
        return None
    try:
        minutes = max(3, min(60, float(item.get("minutes") or 10)))
    except Exception:
        minutes = 10.0
    try:
        chapters = max(1, min(20, int(item.get("chapters") or 5)))
    except Exception:
        chapters = 5
    breaks = _list(item.get("chapter_breaks"), chapters)
    return {
        "id": uuid.uuid4().hex[:12],
        "genre_id": genre["id"],
        "title": title,
        "title_en": _clean(item.get("title_en")) or title,
        "logline": _clean(item.get("logline")),
        "hook": _clean(item.get("hook")),
        "premise": str(item.get("premise") or "").strip(),
        "ending": str(item.get("ending") or "").strip(),
        "protagonist": _clean(item.get("protagonist")),
        "antagonist": _clean(item.get("antagonist")),
        "emotional_arc": _clean(item.get("emotional_arc")),
        "retention_beats": _list(item.get("retention_beats"), 7),
        "chapter_breaks": breaks,
        "why_it_hooks": _clean(item.get("why_it_hooks")),
        "thumbnail_moment": _clean(item.get("thumbnail_moment")),
        "minutes": int(round(minutes)),
        "chapters": chapters,
        "status": "idea",
        "project_id": "",
        "source": "llm",
        "created_at": _now(),
    }


def generate_ideas(
    data: dict,
    genre_id: str,
    *,
    minutes: float = 10,
    chapters: int = 5,
) -> dict:
    genre = next((item for item in data.get("genres", []) if item.get("id") == genre_id), None)
    if not genre:
        raise RuntimeError("Genre not found")
    minutes = max(3, min(60, int(minutes or 10)))
    chapters = max(1, min(20, int(chapters or 5)))
    words = int(minutes * 130)
    existing = [
        idea for idea in data.get("ideas", [])
        if idea.get("genre_id") == genre_id
    ][:14]
    existing_text = "\n".join(
        f"- {idea.get('title', '')}: {idea.get('logline', '')}" for idea in existing
    ) or "- (none yet)"
    prompt = IDEA_PROMPT.format(
        name=genre.get("name", ""),
        name_hi=genre.get("name_hi", ""),
        channel_name=genre.get("channel_name", ""),
        channel_tagline=genre.get("channel_tagline", ""),
        audience=genre.get("audience", ""),
        tone=genre.get("tone", ""),
        themes=", ".join(genre.get("themes", [])) or genre.get("description", ""),
        minutes=minutes,
        words=words,
        chapters=chapters,
        existing=existing_text,
    )
    items: list = []
    for attempt in range(2):
        raw = _chat(
            data,
            [{"role": "system", "content": IDEA_SYSTEM}, {"role": "user", "content": prompt}],
            num_predict=8000,
            temperature=0.95,
        )
        items = _as_list(providers.extract_json(raw))
        if len(items) >= 2:
            items = items[:3]
            break
        prompt = (
            prompt
            + f"\n\nYour previous response contained {len(items)} concepts. "
            + "Return exactly 3 complete concepts this time."
        )
    if len(items) < 2:
        raise RuntimeError(f"The model returned {len(items)} story concepts; expected 3. Try again.")

    ideas = []
    existing_titles = {str(idea.get("title", "")).strip().lower() for idea in existing}
    for item in items:
        idea = _normalize_idea(item, genre)
        if not idea:
            continue
        if idea["title"].strip().lower() in existing_titles:
            continue
        ideas.append(idea)
    if len(ideas) < 2:
        raise RuntimeError("The model repeated existing story ideas; try again.")

    data.setdefault("ideas", []).extend(ideas)
    save_library(data)
    return {"library": public_library(data), "ideas": ideas}


def mark_idea_project(idea_id: str, project_id: str) -> None:
    data = load_library()
    for idea in data.get("ideas", []):
        if idea.get("id") == idea_id:
            idea["status"] = "project"
            idea["project_id"] = project_id
            idea["used_at"] = _now()
            break
    save_library(data)


def blueprint_for(idea: dict, genre: dict) -> tuple[str, str]:
    """Build the topic blueprint and writing instructions for a selected idea."""
    breaks = idea.get("chapter_breaks") or []
    breaks_text = "\n".join(
        f"{index}. {text}" for index, text in enumerate(breaks, 1)
    ) or "(use the chapter turns in the premise)"
    blueprint = f"""कहानी का शीर्षक: {idea.get('title', '')}
English title: {idea.get('title_en', '')}
Genre: {genre.get('name', '')} / {genre.get('name_hi', '')}
Logline: {idea.get('logline', '')}

Hook:
{idea.get('hook', '')}

पूरा प्लॉट / Premise:
{idea.get('premise', '')}

Ending / Resolution:
{idea.get('ending', '')}

Protagonist: {idea.get('protagonist', '')}
Antagonist / obstacle: {idea.get('antagonist', '')}
Emotional arc: {idea.get('emotional_arc', '')}

Chapter-ending beats:
{breaks_text}

Thumbnail moment: {idea.get('thumbnail_moment', '')}
"""
    instructions = f"""इस कहानी को दिए गए ब्लूप्रिंट के अनुसार लिखें।

Genre: {genre.get('name', '')} / {genre.get('name_hi', '')}
Channel promise: {genre.get('channel_name', '')} — {genre.get('channel_tagline', '')}
Tone: {genre.get('tone', '')}
Audience: {genre.get('audience', '')}

नियम:
- ब्लूप्रिंट के मुख्य पात्र, मध्य-कहानी का मोड़, climax और अंत को बदलें नहीं।
- अंतिम अध्याय में केंद्रीय सवाल का स्पष्ट, भावनात्मक जवाब दें और नायक का अंतिम निर्णय दिखाएँ।
- आखिरी पंक्ति को रहस्यमय, खुला या cliffhanger की तरह न छोड़ें; कहानी पूरी तरह समाप्त हो।
- पहले 15 सेकंड में एक ऐसा सवाल खड़ा करें जिसका जवाब सुनने के लिए श्रोता रुके।
- हर 60-90 सेकंड में नई जानकारी, नया खतरा या भावनात्मक मोड़ दें; भराव या सारांश नहीं।
- अंतिम अध्याय से पहले हर अध्याय को एक अनसुलझे सवाल या नई उलझन पर समाप्त करें।
- संवाद-प्रधान, दृश्यात्मक और भावनात्मक हिंदी लिखें; पात्रों के फैसलों से कहानी आगे बढ़े।
- कोई नई उपकथा, dream escape या सुविधाजनक संयोग न जोड़ें।
- अंत चौंकाने वाला हो, लेकिन शुरुआत के किसी संकेत से जुड़ा हो और भावनात्मक रूप से संतोष दे।
"""
    return blueprint.strip(), instructions.strip()
