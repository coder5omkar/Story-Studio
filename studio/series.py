"""Series Bible, recurring cast and episode board for Story Studio.

Phase 1 keeps one active series ("Simplify Life") with a recurring world and
cast. Episodes are generated from the series bible + cast + continuity memory,
then turned into normal projects with the series style, protagonist and narrator
voice applied.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import providers, store

LIBRARY_PATH = store.STUDIO_DIR / ".series.json"

DEFAULT_SETTINGS = {
    "provider": "opencode-go",
    "model": "claude-haiku-5-5",
    "api_base": store.OPENCODE_GO_BASE,
    "temperature": 0.9,
}

PILLARS = ["Finance", "Relationships", "Education", "Food", "Shelter"]

SERIES_FIELDS = (
    "title", "title_hi", "tagline", "premise", "world", "tone", "pillars",
    "visual_style", "narrator", "narrator_voice_reference", "intro", "outro",
    "continuity_rules", "story_so_far",
)

CAST_FIELDS = (
    "name", "name_hi", "age", "role", "pillar", "appearance", "wardrobe",
    "signature_prop", "voice_reference", "speaking_style", "relationships",
    "face_reference",
)

DEFAULT_SERIES = {
    "id": "simplify-life",
    "title": "Simplify Life",
    "title_hi": "सिंपलीफाई लाइफ",
    "tagline": "छोटी कहानी, आसान ज़िंदगी",
    "premise": (
        "A warm, practical anthology series about the Sharma family and their Shanti Nagar "
        "neighbours. Every episode starts with an ordinary modern-life problem — money, love, "
        "school, food or home — and ends with one small, usable simplification. Episodes are "
        "standalone, but they share one continuing world and cast."
    ),
    "world": (
        "Shanti Nagar, a middle-class housing society in a North Indian city. Recurring locations: "
        "the Sharma family's 2BHK, the society park and notice board, the local market, the bank "
        "branch, the school gate and the chai stall."
    ),
    "tone": "warm, honest, gently funny, practical, never preachy",
    "pillars": list(PILLARS),
    "visual_style": (
        "warm Indian watercolor storybook illustration, delicate ink lines, visible paper texture, "
        "warm muted washes, gentle natural light, consistent character designs, Indian middle-class "
        "homes and neighbourhoods, no text, no watermark"
    ),
    "narrator": (
        "A calm, observant Hindi narrator who speaks like a thoughtful friend, never like a lecturer."
    ),
    "narrator_voice_reference": "",
    "intro": "Shanti Nagar. Har flat mein ek kahani, har kahani mein ek chhoti si seekh.",
    "outro": "Zindagi ko simple karna koi badi cheez nahi — bas ek chhota sa faisla.",
    "continuity_rules": (
        "- Episodes are standalone, but the world remembers.\n"
        "- Characters keep their names, ages, jobs, homes, signature props and relationships.\n"
        "- No character becomes rich, famous or a different person without an on-screen reason.\n"
        "- Recurring locations stay consistent.\n"
        "- The lesson must emerge from the plot, never from a speech."
    ),
    "story_so_far": "",
}

DEFAULT_CAST = [
    {
        "id": "rajiv",
        "name": "Rajiv Sharma",
        "name_hi": "राजीव शर्मा",
        "age": 38,
        "role": "Father / salaried operations manager",
        "pillar": "Finance",
        "appearance": (
            "Indian man, 38, short black hair, light stubble, average build, tired but kind eyes, "
            "wearing a simple office shirt and dark trousers"
        ),
        "wardrobe": "pale blue office shirt, dark trousers, brown belt",
        "signature_prop": "an old silver watch",
        "voice_reference": "",
        "speaking_style": "measured, dry humour, avoids asking for help",
        "relationships": "Meera's husband, Aarav's father, Nani's son-in-law, friendly with Verma ji",
        "face_reference": "",
    },
    {
        "id": "meera",
        "name": "Meera Sharma",
        "name_hi": "मीरा शर्मा",
        "age": 35,
        "role": "Mother / school teacher",
        "pillar": "Relationships",
        "appearance": (
            "Indian woman, 35, shoulder-length black hair, warm eyes, practical cotton kurti and "
            "saree, average build"
        ),
        "wardrobe": "simple cotton kurti with a green dupatta",
        "signature_prop": "a green cotton dupatta",
        "voice_reference": "",
        "speaking_style": "warm, precise, emotionally direct, quietly firm",
        "relationships": "Rajiv's wife, Aarav's mother, Nani's daughter",
        "face_reference": "",
    },
    {
        "id": "aarav",
        "name": "Aarav Sharma",
        "name_hi": "आरव शर्मा",
        "age": 14,
        "role": "Son / class 9 student",
        "pillar": "Education",
        "appearance": (
            "Indian teenage boy, 14, messy black hair, skinny, school uniform or a hoodie, curious "
            "and slightly defensive eyes"
        ),
        "wardrobe": "school uniform, or a grey hoodie with jeans",
        "signature_prop": "over-ear headphones",
        "voice_reference": "",
        "speaking_style": "fast, curious, defensive, uses school slang",
        "relationships": "Rajiv and Meera's son, Nani's grandson",
        "face_reference": "",
    },
    {
        "id": "nani",
        "name": "Savitri (Nani)",
        "name_hi": "सावित्री (नानी)",
        "age": 66,
        "role": "Grandmother / retired homemaker",
        "pillar": "Food",
        "appearance": (
            "Indian woman, 66, silver hair in a bun, thin, sharp eyes, simple cotton saree, "
            "reading glasses around her neck"
        ),
        "wardrobe": "simple cotton saree, reading glasses",
        "signature_prop": "a steel tiffin box",
        "voice_reference": "",
        "speaking_style": "slow, witty, warm, cuts through nonsense with one line",
        "relationships": "Meera's mother, Aarav's grandmother, Rajiv's mother-in-law",
        "face_reference": "",
    },
    {
        "id": "verma-ji",
        "name": "Verma ji",
        "name_hi": "वर्मा जी",
        "age": 48,
        "role": "Neighbour / society secretary",
        "pillar": "Shelter",
        "appearance": (
            "Indian man, 48, balding, thick moustache, checked shirt, polyester trousers, "
            "self-important posture"
        ),
        "wardrobe": "checked shirt, polyester trousers, sandals",
        "signature_prop": "a large key ring",
        "voice_reference": "",
        "speaking_style": "comic, self-important, gossipy, loves rules",
        "relationships": "Neighbour of the Sharma family, society secretary",
        "face_reference": "",
    },
]

EPISODE_SYSTEM = (
    "You are the head writer of 'Simplify Life', a Hindi family dramedy series. "
    "You write warm, specific, standalone episodes with a recurring cast and a "
    "continuing world. Every episode contains one modern-life mistake, a real "
    "consequence, and one practical simplification. You never preach. Return only valid JSON."
)

EPISODE_PROMPT = """
Series: {title} ({title_hi})
Tagline: {tagline}
Premise: {premise}
World: {world}
Tone: {tone}
Visual world: {visual_style}
Continuity rules:
{continuity_rules}

Story so far:
{story_so_far}

Recurring cast:
{cast}

Previous produced episodes (canon):
{previous}

Unused pitches already in the bank (avoid repeating):
{unused}

Episode focus: {pillar_focus}
Target: about {minutes} minutes of Hindi narration (~{words} words), {chapters} chapters.

Write exactly 3 distinct episode concepts.

Rules:
1. Pick one lead from the recurring cast. The episode belongs to that character.
2. The lead makes a believable modern-life mistake connected to this pillar: {pillar_focus}.
3. Show a concrete consequence in the family or society. No vague anxiety.
4. The lead simplifies one thing by the end. The lesson must be shown through action, not a speech.
5. Standalone episode, but respect the series continuity and previous episodes.
6. Use at least two other recurring cast members naturally.
7. Keep locations limited to the series world.
8. Indian middle-class specificity: prices, objects, rooms, rituals, small humiliations and small wins.
9. No clichés, no melodrama for its own sake, no evil-for-no-reason villain, no deus ex machina.
10. The final chapter must resolve the episode's central question. Do not end on a cliffhanger.
11. Avoid repeating previous episode titles, lessons or central conflicts.
12. Write Hindi creative fields naturally; use English only for `why_it_works`, `continuity_impact` and `thumbnail_moment`.

Return a JSON array of exactly 3 objects:
{{
  "title": "Hindi episode title, 4-9 words",
  "title_en": "English translation",
  "pillar": "Finance|Relationships|Education|Food|Shelter",
  "logline": "one Hindi sentence",
  "hook": "2-4 Hindi sentences that open the episode",
  "premise": "250-400 Hindi words: full episode plot with beginning, turn, climax and ending",
  "ending": "2-3 Hindi sentences with the final resolution and the lead's choice",
  "lesson": "one practical Hindi sentence, not a sermon",
  "protagonist_name": "exact name from the recurring cast",
  "supporting_cast": ["2-3 exact names from the recurring cast"],
  "continuity_impact": "1-2 English sentences: what changes in the series world after this episode",
  "next_hook": "one Hindi sentence that teases the next episode without a cliffhanger",
  "why_it_works": "2 English sentences about retention and emotional payoff",
  "thumbnail_moment": "one English sentence",
  "minutes": {minutes},
  "chapters": {chapters}
}}
""".strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def _list(value, limit: int = 8) -> list[str]:
    if isinstance(value, str):
        value = re.split(r"[,;\n]+", value)
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _clean(item)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _seed_library() -> dict:
    return {
        "version": 1,
        "settings": {
            **DEFAULT_SETTINGS,
            "session_id": "ses_" + uuid.uuid4().hex,
        },
        "series": {**DEFAULT_SERIES},
        "cast": [dict(item) for item in DEFAULT_CAST],
        "episodes": [],
    }


def load_library() -> dict:
    data: dict = {}
    if LIBRARY_PATH.exists():
        try:
            data = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    if not data:
        data = _seed_library()
        save_library(data)
        return data
    data.setdefault("version", 1)
    settings = data.setdefault("settings", {})
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)
    settings.setdefault("session_id", "ses_" + uuid.uuid4().hex)
    if not isinstance(data.get("series"), dict):
        data["series"] = {**DEFAULT_SERIES}
    for key, value in DEFAULT_SERIES.items():
        data["series"].setdefault(key, value)
    if not isinstance(data.get("cast"), list) or not data["cast"]:
        data["cast"] = [dict(item) for item in DEFAULT_CAST]
    if not isinstance(data.get("episodes"), list):
        data["episodes"] = []
    return data


def save_library(data: dict) -> None:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = LIBRARY_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(LIBRARY_PATH)


def public_library(data: dict) -> dict:
    episodes = sorted(
        data.get("episodes", []),
        key=lambda item: (
            0 if item.get("project_id") else 1,
            item.get("episode_number") or 999,
            str(item.get("created_at", "")),
        ),
    )
    next_number = max(
        [int(item.get("episode_number") or 0) for item in data.get("episodes", [])] or [0]
    ) + 1
    return {
        "settings": data.get("settings", {}),
        "series": data.get("series", {}),
        "cast": data.get("cast", []),
        "episodes": episodes,
        "next_episode_number": next_number,
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


def save_bible(data: dict, payload: dict) -> dict:
    series = data.setdefault("series", {})
    incoming = payload.get("series") or {}
    for field in SERIES_FIELDS:
        if field in incoming:
            if field == "continuity_rules" or field == "story_so_far":
                series[field] = str(incoming.get(field) or "").strip()
            elif field == "pillars":
                series[field] = _list(incoming.get(field), 8)
            else:
                series[field] = _clean(incoming.get(field))
    cast_payload = payload.get("cast")
    if isinstance(cast_payload, list):
        cleaned: list[dict] = []
        seen: set[str] = set()
        for item in cast_payload:
            if not isinstance(item, dict):
                continue
            name = _clean(item.get("name"))
            if not name:
                continue
            cid = _clean(item.get("id")) or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if not cid or cid in seen:
                cid = f"cast-{uuid.uuid4().hex[:8]}"
            seen.add(cid)
            entry = {"id": cid}
            for field in CAST_FIELDS:
                if field == "age":
                    try:
                        entry[field] = int(item.get(field) or 0)
                    except Exception:
                        entry[field] = 0
                else:
                    entry[field] = _clean(item.get(field))
            cleaned.append(entry)
        if cleaned:
            data["cast"] = cleaned
    save_library(data)
    return public_library(data)


def _chat(data: dict, messages: list[dict], *, num_predict: int, temperature: float = 0.9) -> str:
    settings = data["settings"]
    return providers.chat(
        {"llm": settings},
        messages,
        model=settings.get("model"),
        temperature=temperature,
        num_predict=num_predict,
    )


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("episodes", "items", "data", "stories"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def cast_context(cast: list[dict]) -> str:
    lines = []
    for person in cast:
        lines.append(
            f"- {person.get('name')} ({person.get('age')}, {person.get('role')}; pillar: "
            f"{person.get('pillar')}): {person.get('appearance')}. Wardrobe: {person.get('wardrobe')}. "
            f"Signature prop: {person.get('signature_prop')}. Speaking style: {person.get('speaking_style')}."
        )
    return "\n".join(lines) or "- (no cast yet)"


def _previous_context(episodes: list[dict]) -> str:
    lines = []
    for episode in episodes[:12]:
        lines.append(
            f"- {episode.get('title', '')} (EP {episode.get('episode_number', '')}, "
            f"{episode.get('pillar', '')}, lead: {episode.get('protagonist_name', '')}): "
            f"{episode.get('lesson', '')} Continuity: {episode.get('continuity_impact', '')}"
        )
    return "\n".join(lines) or "- (this is the first produced episode)"


def _unused_context(episodes: list[dict]) -> str:
    lines = []
    for episode in episodes[:15]:
        lines.append(
            f"- {episode.get('title', '')}: {episode.get('logline', '')}"
        )
    return "\n".join(lines) or "- (none yet)"


def _match_cast(name: str, cast: list[dict]) -> dict | None:
    needle = _clean(name).lower()
    if not needle:
        return None
    for person in cast:
        if _clean(person.get("name")).lower() == needle:
            return person
    for person in cast:
        full = _clean(person.get("name")).lower()
        if needle in full or full in needle:
            return person
        first = full.split()[0]
        if first and first == needle.split()[0]:
            return person
    return None


def suggest_episodes(
    data: dict,
    *,
    pillar: str = "",
    minutes: float = 10,
    chapters: int = 5,
) -> dict:
    series = data.get("series", {})
    cast = data.get("cast", [])
    pillar = _clean(pillar)
    if pillar and pillar not in PILLARS:
        raise RuntimeError("Unknown pillar")
    minutes = max(3, min(60, int(minutes or 10)))
    chapters = max(1, min(20, int(chapters or 5)))
    words = int(minutes * 130)
    focus = (
        f"{pillar} — choose the cast member whose life fits this pillar"
        if pillar
        else "Auto — choose the pillar and lead that make the most compelling next episode"
    )
    all_episodes = data.get("episodes", [])
    produced = [item for item in all_episodes if item.get("project_id")]
    unused = [item for item in all_episodes if not item.get("project_id")]
    prompt = EPISODE_PROMPT.format(
        title=series.get("title", ""),
        title_hi=series.get("title_hi", ""),
        tagline=series.get("tagline", ""),
        premise=series.get("premise", ""),
        world=series.get("world", ""),
        tone=series.get("tone", ""),
        visual_style=series.get("visual_style", ""),
        continuity_rules=series.get("continuity_rules", ""),
        story_so_far=series.get("story_so_far", "") or "- (nothing yet)",
        cast=cast_context(cast),
        previous=_previous_context(produced),
        unused=_unused_context(unused),
        pillar_focus=focus,
        minutes=minutes,
        words=words,
        chapters=chapters,
    )
    items: list = []
    for attempt in range(2):
        raw = _chat(
            data,
            [{"role": "system", "content": EPISODE_SYSTEM}, {"role": "user", "content": prompt}],
            num_predict=8000,
            temperature=0.94,
        )
        items = _as_list(providers.extract_json(raw))
        if len(items) >= 2:
            items = items[:3]
            break
        prompt = (
            prompt
            + f"\n\nYour previous response contained {len(items)} episodes. "
            + "Return exactly 3 complete, distinct episodes this time."
        )
    if len(items) < 2:
        raise RuntimeError(f"The model returned {len(items)} episodes; expected 3. Try again.")

    existing_titles = {
        _clean(item.get("title")).lower() for item in data.get("episodes", []) if item.get("title")
    }
    episodes = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = _clean(item.get("title"))
        if not title or title.lower() in existing_titles:
            continue
        lead = _match_cast(item.get("protagonist_name"), cast)
        if pillar:
            candidates = [p for p in cast if p.get("pillar") == pillar]
            if candidates and (not lead or lead.get("pillar") != pillar):
                lead = candidates[0]
        if not lead:
            lead = next((p for p in cast if p.get("pillar") == pillar), cast[0] if cast else {})
        support_names = _list(item.get("supporting_cast"), 4)
        support = []
        for name in support_names:
            person = _match_cast(name, cast)
            if person and person.get("id") != lead.get("id"):
                support.append(person.get("name"))
        episodes.append({
            "id": uuid.uuid4().hex[:12],
            "title": title,
            "title_en": _clean(item.get("title_en")) or title,
            "pillar": pillar or _clean(item.get("pillar")) or lead.get("pillar", ""),
            "minute_target": minutes,
            "chapter_target": chapters,
            "logline": _clean(item.get("logline")),
            "hook": _clean(item.get("hook")),
            "premise": str(item.get("premise") or "").strip(),
            "ending": str(item.get("ending") or "").strip(),
            "lesson": _clean(item.get("lesson")),
            "protagonist_id": lead.get("id", ""),
            "protagonist_name": lead.get("name", ""),
            "supporting_cast": support,
            "continuity_impact": _clean(item.get("continuity_impact")),
            "next_hook": _clean(item.get("next_hook")),
            "why_it_works": _clean(item.get("why_it_works")),
            "thumbnail_moment": _clean(item.get("thumbnail_moment")),
            "minutes": minutes,
            "chapters": chapters,
            "status": "idea",
            "episode_number": 0,
            "project_id": "",
            "created_at": _now(),
        })
    if len(episodes) < 2:
        raise RuntimeError("The model repeated existing episodes; try again.")
    data.setdefault("episodes", []).extend(episodes)
    save_library(data)
    return {"library": public_library(data), "episodes": episodes}


def episode_blueprint(episode: dict, series: dict, cast: list[dict], episode_number: int) -> tuple[str, str]:
    lead = next((p for p in cast if p.get("id") == episode.get("protagonist_id")), {})
    support = ", ".join(episode.get("supporting_cast") or []) or "the recurring cast"
    blueprint = f"""Series: {series.get('title', '')} ({series.get('title_hi', '')})
Episode: {episode_number}
Pillar: {episode.get('pillar', '')}
Title: {episode.get('title', '')}
English title: {episode.get('title_en', '')}

Logline:
{episode.get('logline', '')}

Hook:
{episode.get('hook', '')}

Full plot:
{episode.get('premise', '')}

Ending:
{episode.get('ending', '')}

Lesson (must be shown, not preached):
{episode.get('lesson', '')}

Lead: {episode.get('protagonist_name', '')}
Supporting cast: {support}
Continuity impact: {episode.get('continuity_impact', '')}
Next episode tease: {episode.get('next_hook', '')}
Thumbnail moment: {episode.get('thumbnail_moment', '')}
"""
    instructions = f"""आप "Simplify Life" सीरीज़ का एक एपिसोड लिख रहे हैं।

Series: {series.get('title', '')} / {series.get('title_hi', '')}
Tagline: {series.get('tagline', '')}
World: {series.get('world', '')}
Tone: {series.get('tone', '')}
Episode: {episode_number} · {episode.get('pillar', '')}

Recurring cast:
{cast_context(cast)}

Story so far:
{series.get('story_so_far', '') or '- (this is an early episode)'}

नियम:
- यह एक standalone episode है, लेकिन series की दुनिया और पात्रों की continuity बनी रहे।
- Lead {episode.get('protagonist_name', '')} की उम्र, काम, रिश्ते, पहनावा, signature prop और बोलने का तरीका वही रहे।
- Supporting cast {support} को स्वाभाविक रूप से शामिल करें।
- कहानी एक ठोस modern-life गलती से शुरू हो, उसका असली परिणाम दिखे, और अंत में lead एक छोटी practical चीज़ simplify करे।
- Lesson को किसी भाषण से नहीं, पात्र के फैसले और परिणाम से दिखाएँ।
- Indian middle-class की ठोस details रखें: कीमतें, कमरे, सामान, रस्में, छोटी शर्म और छोटी जीत।
- पहले 15 सेकंड में सवाल खड़ा करें; हर 60-90 सेकंड में नया मोड़ या भावनात्मक बदलाव दें।
- अंतिम अध्याय में मुख्य सवाल का स्पष्ट, संतोषजनक जवाब दें; आखिरी पंक्ति खुली न छोड़ें।
- कोई नया lead, नई उपकथा, dream escape या सुविधाजनक संयोग न जोड़ें।
- भाषा सरल, भावनात्मक, दृश्यात्मक और संवाद-प्रधान हिंदी हो; उपदेश नहीं।
"""
    return blueprint.strip(), instructions.strip()


def next_episode_number(data: dict) -> int:
    return max(
        [int(item.get("episode_number") or 0) for item in data.get("episodes", [])] or [0]
    ) + 1


def mark_episode_project(episode_id: str, project_id: str, episode_number: int) -> dict:
    data = load_library()
    for episode in data.get("episodes", []):
        if episode.get("id") == episode_id:
            episode["status"] = "project"
            episode["project_id"] = project_id
            episode["episode_number"] = episode_number
            episode["used_at"] = _now()
            break
    save_library(data)
    return public_library(data)
