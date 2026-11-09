"""Story Studio — local approval-gated production UI.

Run from the repository root:

    D:\\AI_Story_Channel\\OpenMontage\\.venv\\Scripts\\python.exe -m studio.server

Then open http://127.0.0.1:4780
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from studio import ideas, ops, pov, providers, qa, series, store
from studio.jobs import manager

UI_DIR = store.UI_DIR
PORT = int(os.environ.get("STUDIO_PORT", "4780"))
IDEAS_LOCK = threading.Lock()
SERIES_LOCK = threading.Lock()

app = FastAPI(title="Story Studio", docs_url=None, redoc_url=None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project(pid: str) -> dict:
    try:
        return store.load_state(pid)
    except FileNotFoundError:
        raise HTTPException(404, f"Unknown project: {pid}")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


def _story(pid: str) -> str:
    path = store.project_paths(pid)["story"]
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _scenes(pid: str) -> list:
    path = store.project_paths(pid)["scenes"]
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _target_words(state: dict) -> int:
    return max(200, int(float(state.get("settings", {}).get("story_minutes", 5)) * 130))


def _media_url(pid: str, rel: str) -> str:
    return f"/api/projects/{pid}/media/{urllib.parse.quote(rel, safe='/')}"


def _versioned_media_url(pid: str, rel: str, path: Path) -> str:
    """Append a file version so regenerated assets bypass browser cache."""
    url = _media_url(pid, rel)
    try:
        return f"{url}?v={path.stat().st_mtime_ns}"
    except OSError:
        return url


def _sample_payload(pid: str, state: dict) -> dict:
    root = store.project_paths(pid)["root"]
    out = {}
    for kind, node in state["stages"]["samples"].items():
        item = dict(node)
        if item.get("path"):
            item["url"] = _versioned_media_url(pid, item["path"], root / item["path"])
        out[kind] = item
    return out


def _project_payload(pid: str) -> dict:
    state = _project(pid)
    story = _story(pid)
    scenes = _scenes(pid)
    story_validation = state["stages"]["story"].get("validation") or (
        qa.validate_story(
            story,
            _target_words(state),
            expected_chapters=int(state["settings"].get("story_chapters", 0) or 0),
        ) if story else None
    )
    scenes_validation = state["stages"]["scenes"].get("validation") or (
        qa.validate_scenes(scenes) if scenes else None
    )
    gates = ops.check_gates(state)
    paths = store.project_paths(pid)
    outputs = {}
    for name in ("final.mp4", "pilot.mp4", "pilot_consistent.mp4"):
        candidate = paths["video"] / name
        if candidate.exists():
            outputs[name] = {
                "url": _versioned_media_url(pid, f"video/{name}", candidate),
                "size": candidate.stat().st_size,
            }
    active = manager.active_for_project(pid)
    music_path = paths["audio"] / "music.mp3"
    scene_status = qa.summarize_scene_status(scenes, paths["root"])
    for item in scene_status:
        sid = int(item["id"])
        image = paths["root"] / "images" / f"scene_{sid:03d}.png"
        audio = paths["root"] / "audio" / f"scene_{sid:03d}.wav"
        if item.get("image"):
            item["image_url"] = _versioned_media_url(
                pid, f"images/scene_{sid:03d}.png", image
            )
        if item.get("audio"):
            item["audio_url"] = _versioned_media_url(
                pid, f"audio/scene_{sid:03d}.wav", audio
            )
    publish = json.loads(json.dumps(state["stages"].get("publish", {})))
    if publish.get("thumbnail_path"):
        publish["thumbnail_url"] = _versioned_media_url(
            pid, publish["thumbnail_path"], paths["root"] / publish["thumbnail_path"]
        )
    return {
        "project": {
            "id": pid,
            "title": state.get("title", pid),
            "root": str(paths["root"]),
        },
        "state": store.public_state(state),
        "story": story,
        "story_validation": story_validation,
        "scenes": scenes,
        "scenes_validation": scenes_validation,
        "scene_status": scene_status,
        "samples": _sample_payload(pid, state),
        "project_audio": {
            "music": _versioned_media_url(pid, "audio/music.mp3", music_path) if music_path.exists() else "",
        },
        "publish": publish,
        "gates": gates,
        "outputs": outputs,
        "active_job": active.to_dict(include_logs=False) if active else None,
        "jobs": manager.list(pid),
    }


def _fail(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(404, str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(403, str(exc))
    return HTTPException(400, str(exc))


def _start(pid: str, kind: str, fn) -> dict:
    try:
        job = manager.start(pid, kind, fn)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    return {"job": job.to_dict(include_logs=False)}


def _deep_merge(base: dict, patch: dict) -> dict:
    out = json.loads(json.dumps(base))
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_llm_payload(state: dict, payload: dict) -> None:
    """Persist model/provider choices made on the Story or Scenes page."""
    llm = state["settings"].setdefault("llm", {})
    if payload.get("provider"):
        llm["provider"] = str(payload["provider"])
    if payload.get("model"):
        llm["model"] = str(payload["model"])
    if payload.get("api_base"):
        llm["api_base"] = providers.normalize_api_base(str(payload["api_base"]))
    if payload.get("temperature") is not None:
        llm["temperature"] = float(payload["temperature"])


# ---------------------------------------------------------------------------
# Health / models
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    def ping(url: str) -> bool:
        try:
            return requests.get(url, timeout=2).ok
        except Exception:
            return False

    return {
        "ok": True,
        "ollama": ping(str(store.default_settings()["ollama_url"]).rstrip("/") + "/api/tags"),
        "comfy": ping(str(store.base_config().get("comfy_url", "http://127.0.0.1:8188")).rstrip("/") + "/system_stats"),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "tts_env": ops.TTS_PY.exists(),
        "pipeline_env": ops.PIPELINE_PY.exists(),
        "secrets": bool(store.get_api_key()),
    }


@app.get("/api/models")
def models(provider: str = "ollama", base_url: str = "") -> dict:
    defaults = store.default_settings()
    if provider == "opencode-go":
        base = base_url or store.OPENCODE_GO_BASE
    elif provider == "opencode":
        base = base_url or store.OPENCODE_ZEN_BASE
    else:
        base = base_url or defaults["llm"]["api_base"]
    settings = {
        "llm": {
            "provider": provider,
            "ollama_url": base_url or defaults["ollama_url"],
            "api_base": base,
        }
    }
    return providers.list_models(settings)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@app.get("/api/projects")
def projects() -> list:
    return store.list_projects()


@app.post("/api/projects")
def create_project(payload: dict = Body(...)) -> dict:
    title = str(payload.get("title", "")).strip() or "Untitled story"
    topic = str(payload.get("topic", "")).strip()
    minutes = float(payload.get("minutes", 5) or 5)
    chapters = int(payload.get("chapters", 5) or 5)
    try:
        state = store.create_project(title, topic, minutes, chapters)
    except Exception as exc:
        raise _fail(exc)
    template = str(payload.get("template", "")).strip()
    if template == "pov_finance":
        pov.apply_template(state)
        store.write_project_config(state["project_id"], state)
        store.add_history(state, "project_template", "POV Finance")
        store.save_state(state["project_id"], state)
    return {"id": state["project_id"], "state": store.public_state(state)}


@app.get("/api/projects/{pid}")
def project(pid: str) -> dict:
    return _project_payload(pid)


@app.patch("/api/projects/{pid}/settings")
def patch_settings(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    old = state.get("settings", {})
    new = _deep_merge(old, payload.get("settings", {}))
    state["settings"] = new
    store.write_project_config(pid, state)

    invalidate: list[str] = []
    if old.get("image") != new.get("image"):
        invalidate += ["samples.image", "samples.clip", "production", "final", "publish"]
    if old.get("tts") != new.get("tts"):
        invalidate += ["samples.voice", "samples.clip", "production", "final"]
    if old.get("music") != new.get("music"):
        invalidate += ["samples.music", "samples.clip", "production", "final"]
    if old.get("subtitles") != new.get("subtitles"):
        invalidate += ["samples.clip", "final"]
    if old.get("publish") != new.get("publish"):
        invalidate += ["publish"]
    if invalidate:
        store.invalidate(state, sorted(set(invalidate)), "settings changed")
    store.save_state(pid, state)
    return {"state": store.public_state(state), "invalidated": sorted(set(invalidate))}


@app.post("/api/projects/{pid}/settings/api-key")
def save_api_key(pid: str, payload: dict = Body(...)) -> dict:
    _project(pid)
    key = str(payload.get("key", "")).strip()
    store.save_secrets({"llm_api_key": key})
    return {"ok": True, "has_api_key": bool(key)}


# ---------------------------------------------------------------------------
# Story table / idea lab
# ---------------------------------------------------------------------------


@app.get("/api/ideas")
def get_idea_library() -> dict:
    return ideas.public_library(ideas.load_library())


@app.post("/api/ideas/genres/suggest")
def suggest_idea_genres(payload: dict = Body(default={})) -> dict:
    with IDEAS_LOCK:
        data = ideas.load_library()
        ideas.update_settings(data, payload)
        ideas.save_library(data)
        try:
            return ideas.suggest_genres(data)
        except Exception as exc:
            raise _fail(exc)


@app.post("/api/ideas/genres")
def add_idea_genre(payload: dict = Body(...)) -> dict:
    with IDEAS_LOCK:
        data = ideas.load_library()
        try:
            return ideas.add_user_genre(data, payload)
        except Exception as exc:
            raise _fail(exc)


@app.post("/api/ideas/genres/{genre_id}/ideas")
def generate_genre_ideas(genre_id: str, payload: dict = Body(default={})) -> dict:
    with IDEAS_LOCK:
        data = ideas.load_library()
        ideas.update_settings(data, payload)
        ideas.save_library(data)
        try:
            minutes = float(payload.get("minutes", 10) or 10)
            chapters = int(payload.get("chapters", 5) or 5)
            return ideas.generate_ideas(data, genre_id, minutes=minutes, chapters=chapters)
        except Exception as exc:
            raise _fail(exc)


@app.post("/api/ideas/{idea_id}/project")
def project_from_idea(idea_id: str, payload: dict = Body(default={})) -> dict:
    with IDEAS_LOCK:
        data = ideas.load_library()
        idea = next((item for item in data.get("ideas", []) if item.get("id") == idea_id), None)
        if not idea:
            raise HTTPException(404, "Story idea not found")
        genre = next(
            (item for item in data.get("genres", []) if item.get("id") == idea.get("genre_id")),
            {},
        )
        existing_pid = str(idea.get("project_id") or "").strip()
        if existing_pid and (store.PROJECTS_DIR / existing_pid).is_dir():
            return {
                "project_id": existing_pid,
                "title": idea.get("title", ""),
                "existing": True,
                "job": None,
            }

        ideas.update_settings(data, payload)
        ideas.save_library(data)
        blueprint, instructions = ideas.blueprint_for(idea, genre)
        minutes = max(3, min(60, int(idea.get("minutes") or payload.get("minutes") or 10)))
        chapters = max(1, min(20, int(idea.get("chapters") or payload.get("chapters") or 5)))
        title = str(idea.get("title") or idea.get("title_en") or "Hindi story").strip()
        slug_source = str(idea.get("title_en") or title).strip()
        try:
            state = store.create_project(
                title, blueprint, minutes, chapters, slug_source=slug_source
            )
        except Exception as exc:
            raise _fail(exc)

        pid = state["project_id"]
        settings = state["settings"]
        settings["story_instructions"] = instructions
        settings["story_genre"] = str(genre.get("name", ""))
        settings["story_genre_id"] = str(genre.get("id", ""))
        settings["story_idea_id"] = idea_id
        settings["story_thumbnail_moment"] = str(idea.get("thumbnail_moment", ""))
        publish = settings.setdefault("publish", {})
        if genre.get("channel_name"):
            publish["channel_name"] = genre["channel_name"]
        if genre.get("channel_tagline"):
            publish["channel_tagline"] = genre["channel_tagline"]
        idea_settings = data.get("settings", {})
        llm = settings.setdefault("llm", {})
        for key in ("provider", "model", "api_base", "temperature"):
            if idea_settings.get(key) not in (None, ""):
                llm[key] = idea_settings[key]
        store.write_project_config(pid, state)
        store.save_state(pid, state)
        ideas.mark_idea_project(idea_id, pid)

        job = None
        if bool(payload.get("generate")):
            try:
                job = manager.start(pid, "story", lambda worker: ops.generate_story(
                    pid, state, worker,
                    topic=blueprint, minutes=minutes, chapters=chapters,
                    instructions=instructions,
                ))
            except Exception as exc:
                raise _fail(exc)
        return {
            "project_id": pid,
            "title": title,
            "existing": False,
            "job": job.to_dict(include_logs=False) if job else None,
        }


# ---------------------------------------------------------------------------
# Series room
# ---------------------------------------------------------------------------


@app.get("/api/series")
def get_series_library() -> dict:
    return series.public_library(series.load_library())


@app.put("/api/series")
def save_series_bible(payload: dict = Body(...)) -> dict:
    with SERIES_LOCK:
        data = series.load_library()
        try:
            series.update_settings(data, payload)
            return series.save_bible(data, payload)
        except Exception as exc:
            raise _fail(exc)


@app.post("/api/series/episodes/generate")
def generate_series_episodes(payload: dict = Body(default={})) -> dict:
    with SERIES_LOCK:
        data = series.load_library()
        series.update_settings(data, payload)
        series.save_library(data)
        try:
            pillar = str(payload.get("pillar", "")).strip()
            minutes = float(payload.get("minutes", 10) or 10)
            chapters = int(payload.get("chapters", 5) or 5)
            return series.suggest_episodes(
                data, pillar=pillar, minutes=minutes, chapters=chapters
            )
        except Exception as exc:
            raise _fail(exc)


@app.post("/api/series/episodes/{episode_id}/project")
def project_from_episode(episode_id: str, payload: dict = Body(default={})) -> dict:
    with SERIES_LOCK:
        data = series.load_library()
        episode = next(
            (item for item in data.get("episodes", []) if item.get("id") == episode_id),
            None,
        )
        if not episode:
            raise HTTPException(404, "Episode not found")
        existing_pid = str(episode.get("project_id") or "").strip()
        if existing_pid and (store.PROJECTS_DIR / existing_pid).is_dir():
            return {
                "project_id": existing_pid,
                "title": episode.get("title", ""),
                "existing": True,
                "job": None,
            }

        series.update_settings(data, payload)
        series.save_library(data)
        bible = data.get("series", {})
        cast = data.get("cast", [])
        number = series.next_episode_number(data)
        blueprint, instructions = series.episode_blueprint(episode, bible, cast, number)
        minutes = max(3, min(60, int(episode.get("minutes") or payload.get("minutes") or 10)))
        chapters = max(1, min(20, int(episode.get("chapters") or payload.get("chapters") or 5)))
        title = str(episode.get("title") or episode.get("title_en") or "Simplify Life").strip()
        slug_source = str(episode.get("title_en") or title).strip()
        try:
            state = store.create_project(
                title, blueprint, minutes, chapters, slug_source=slug_source
            )
        except Exception as exc:
            raise _fail(exc)

        pid = state["project_id"]
        settings = state["settings"]
        settings["story_instructions"] = instructions
        settings["story_genre"] = str(bible.get("title", ""))
        settings["series_id"] = str(bible.get("id", ""))
        settings["series_title"] = str(bible.get("title", ""))
        settings["episode_number"] = number
        settings["episode_pillar"] = str(episode.get("pillar", ""))
        settings["protagonist"] = str(episode.get("protagonist_name", ""))
        lead = next(
            (person for person in cast if person.get("id") == episode.get("protagonist_id")),
            {},
        )
        if lead:
            image = settings.setdefault("image", {})
            if bible.get("visual_style"):
                image["style_prefix"] = str(bible["visual_style"])
            if bible.get("negative_prompt"):
                image["negative_prompt"] = str(bible["negative_prompt"])
            image["protagonist_name"] = str(lead.get("name", ""))
            image["cast"] = series.cast_reference_map(cast, str(lead.get("id", "")))
            appearance = str(lead.get("appearance", ""))
            age = str(lead.get("age") or "")
            age_prefix = "" if (not age or age in appearance) else f"{age}-year-old, "
            image["character"] = (
                f"the protagonist is {lead.get('name', '')}, {age_prefix}{appearance}; "
                f"wardrobe: {lead.get('wardrobe', '')}; "
                f"signature prop: {lead.get('signature_prop', '')}; keep the same face, hair, "
                f"outfit and age consistent across scenes"
            )
        if bible.get("narrator_voice_reference"):
            settings.setdefault("tts", {})["reference"] = bible["narrator_voice_reference"]
        publish = settings.setdefault("publish", {})
        if bible.get("title"):
            publish["channel_name"] = bible["title"]
        if bible.get("tagline"):
            publish["channel_tagline"] = bible["tagline"]
        publish["hashtags"] = "#SimplifyLife #HindiKahani #LifeLessons"
        if bible.get("outro"):
            publish["cta"] = bible["outro"]
        idea_settings = data.get("settings", {})
        llm = settings.setdefault("llm", {})
        for key in ("provider", "model", "api_base", "temperature"):
            if idea_settings.get(key) not in (None, ""):
                llm[key] = idea_settings[key]
        store.write_project_config(pid, state)
        store.save_state(pid, state)
        series.mark_episode_project(episode_id, pid, number)

        job = None
        if bool(payload.get("generate")):
            try:
                job = manager.start(pid, "story", lambda worker: ops.generate_story(
                    pid, state, worker,
                    topic=blueprint, minutes=minutes, chapters=chapters,
                    instructions=instructions,
                ))
            except Exception as exc:
                raise _fail(exc)
        return {
            "project_id": pid,
            "title": title,
            "episode_number": number,
            "existing": False,
            "job": job.to_dict(include_logs=False) if job else None,
        }


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------


@app.post("/api/projects/{pid}/story/generate")
def generate_story(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    topic = str(payload.get("topic", "")).strip()
    minutes = float(payload.get("minutes", 5) or 5)
    chapters = int(payload.get("chapters", 5) or 5)
    instructions = str(payload.get("instructions", "")).strip()
    if not topic:
        raise HTTPException(400, "Topic is required")
    _apply_llm_payload(state, payload)
    state["settings"]["story_topic"] = topic
    state["settings"]["story_minutes"] = minutes
    state["settings"]["story_chapters"] = chapters
    state["settings"]["story_instructions"] = instructions
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "story", lambda job: ops.generate_story(
        pid, state, job, topic=topic, minutes=minutes, chapters=chapters,
        instructions=instructions,
    ))


@app.post("/api/projects/{pid}/story/adapt")
def adapt_story(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    source = str(payload.get("source", "")).strip()
    if not source:
        raise HTTPException(400, "Paste a source story or transcript first")
    if len(source) < 200:
        raise HTTPException(400, "The source story is too short to adapt")
    minutes = float(payload.get("minutes", 25) or 25)
    chapters = int(payload.get("chapters", 8) or 8)
    _apply_llm_payload(state, payload)
    state["settings"]["story_topic"] = "POV Finance adaptation"
    state["settings"]["story_minutes"] = minutes
    state["settings"]["story_chapters"] = chapters
    state["settings"]["story_instructions"] = pov.POV_ADAPT_INSTRUCTIONS
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "story_adapt", lambda job: ops.adapt_story(
        pid, state, job,
        source=source, minutes=minutes, chapters=chapters,
    ))


@app.put("/api/projects/{pid}/story")
def save_story(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    text = str(payload.get("text", ""))
    try:
        validation = ops.save_story(pid, state, text)
    except Exception as exc:
        raise _fail(exc)
    return {"validation": validation}


@app.post("/api/projects/{pid}/story/approve")
def approve_story(pid: str) -> dict:
    state = _project(pid)
    text = _story(pid)
    expected = int(state["settings"].get("story_chapters", 0) or 0)
    validation = qa.validate_story(text, _target_words(state), expected_chapters=expected)
    if not validation["ok"]:
        raise HTTPException(409, detail={"message": "Story checks failed", "validation": validation})
    store.set_stage(state, "story", "approved", approved=True,
                    notes="Story approved", validation=validation)
    store.save_state(pid, state)
    return {"ok": True, "validation": validation}


@app.post("/api/projects/{pid}/story/request-changes")
def request_story_changes(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    store.set_stage(state, "story", "changes_requested", approved=False,
                    notes=str(payload.get("notes", "Changes requested")))
    store.save_state(pid, state)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


@app.post("/api/projects/{pid}/scenes/generate")
def generate_scenes(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    if not _story(pid):
        raise HTTPException(400, "Generate or write the story first")
    _apply_llm_payload(state, payload)
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    target_words = int(payload.get("target_words", 24) or 24)
    batch_size = int(payload.get("batch_size", 12) or 12)
    return _start(pid, "scenes", lambda job: ops.generate_scenes(
        pid, state, job, target_words=target_words, batch_size=batch_size,
    ))


@app.put("/api/projects/{pid}/scenes")
def save_scenes(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    scenes = payload.get("scenes", [])
    if not isinstance(scenes, list):
        raise HTTPException(400, "scenes must be a list")
    try:
        validation = ops.save_scenes(pid, state, scenes)
    except Exception as exc:
        raise _fail(exc)
    return {"validation": validation}


@app.put("/api/projects/{pid}/scenes/{scene_id}")
def save_single_scene(pid: str, scene_id: int, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    try:
        return ops.save_scene_review(pid, state, scene_id, payload)
    except Exception as exc:
        raise _fail(exc)


@app.post("/api/projects/{pid}/scenes/approve")
def approve_scenes(pid: str) -> dict:
    state = _project(pid)
    scenes = _scenes(pid)
    validation = qa.validate_scenes(scenes)
    if not validation["ok"]:
        raise HTTPException(409, detail={"message": "Scene checks failed", "validation": validation})
    store.set_stage(state, "scenes", "approved", approved=True,
                    notes="Scene plan approved", validation=validation)
    store.save_state(pid, state)
    return {"ok": True, "validation": validation}


@app.post("/api/projects/{pid}/scenes/request-changes")
def request_scene_changes(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    store.set_stage(state, "scenes", "changes_requested", approved=False,
                    notes=str(payload.get("notes", "Changes requested")))
    store.save_state(pid, state)
    return {"ok": True}


@app.post("/api/projects/{pid}/scenes/{scene_id}/regenerate-prompt")
def regenerate_scene_prompt(pid: str, scene_id: int, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    if not _scenes(pid):
        raise HTTPException(400, "Generate the scene plan first")
    _apply_llm_payload(state, payload)
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "scene_prompt", lambda job: ops.regenerate_scene_prompt(
        pid, state, job, scene_id=scene_id,
    ))


@app.post("/api/projects/{pid}/scenes/regenerate-prompts")
def regenerate_all_prompts(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    if not _scenes(pid):
        raise HTTPException(400, "Generate the scene plan first")
    _apply_llm_payload(state, payload)
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "scene_prompts", lambda job: ops.regenerate_all_prompts(
        pid, state, job,
    ))


@app.post("/api/projects/{pid}/scenes/repair-prompts")
def repair_scene_prompts(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    _apply_llm_payload(state, payload)
    if not _scenes(pid):
        raise HTTPException(400, "Generate the scene plan first")
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "repair_prompts", lambda job: ops.repair_scene_prompts(
        pid, state, job,
    ))


@app.post("/api/projects/{pid}/scenes/restyle-prompts")
def restyle_scene_prompts(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    _apply_llm_payload(state, payload)
    if not _scenes(pid):
        raise HTTPException(400, "Generate the scene plan first")
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "restyle_prompts", lambda job: ops.restyle_scene_prompts(
        pid, state, job,
    ))


# ---------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------


@app.post("/api/projects/{pid}/tts/normalize")
def normalize_tts(pid: str, payload: dict = Body(...)) -> dict:
    _project(pid)
    text = str(payload.get("text", "")).strip()
    return {"text": ops.normalize_tts_text(text)}


@app.post("/api/projects/{pid}/samples/voice")
def sample_voice(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    text = str(payload.get("text", "")).strip()
    scene_id = payload.get("scene_id")
    overrides = payload.get("overrides", {}) or {}
    if scene_id is not None:
        scene_id = int(scene_id)
    return _start(pid, "voice_sample", lambda job: ops.generate_voice_sample(
        pid, state, job, text=text, scene_id=scene_id, overrides=overrides,
    ))


@app.post("/api/projects/{pid}/samples/image")
def sample_image(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    scene_id = int(payload.get("scene_id", 1) or 1)
    engine = str(payload.get("engine", state["settings"].get("image", {}).get("engine", "sdxl")))
    seed = int(payload.get("seed", 0) or 0)
    return _start(pid, "image_sample", lambda job: ops.generate_image_sample(
        pid, state, job, scene_id=scene_id, engine=engine, seed=seed,
    ))


@app.post("/api/projects/{pid}/samples/music")
def sample_music(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    music = state["settings"].setdefault("music", {})
    prompt = str(payload.get("prompt", music.get("prompt", "")))
    duration = float(payload.get("duration", music.get("duration", 60)) or 60)
    bpm = int(payload.get("bpm", music.get("bpm", 78)) or 78)
    key = str(payload.get("key", music.get("key", "C minor")))
    music.update({"prompt": prompt, "duration": duration, "bpm": bpm, "key": key})
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "music_sample", lambda job: ops.generate_music_sample(
        pid, state, job, prompt=prompt, duration=duration, bpm=bpm, key=key,
    ))


@app.post("/api/projects/{pid}/samples/clip")
def sample_clip(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    scene_id = int(payload.get("scene_id", 1) or 1)
    subtitles = bool(payload.get("subtitles", state["settings"].get("subtitles", True)))
    with_music = bool(payload.get("with_music", True))
    return _start(pid, "clip_sample", lambda job: ops.build_preview_clip(
        pid, state, job, scene_id=scene_id, subtitles=subtitles, with_music=with_music,
    ))


@app.post("/api/projects/{pid}/samples/{kind}/approve")
def approve_sample(pid: str, kind: str) -> dict:
    if kind not in ("voice", "image", "music", "clip"):
        raise HTTPException(404, "Unknown sample kind")
    state = _project(pid)
    node = state["stages"]["samples"].get(kind, {})
    if not node.get("path") or not (store.project_paths(pid)["root"] / node["path"]).exists():
        raise HTTPException(409, f"No {kind} sample to approve")
    validation = node.get("validation")
    if validation and not validation.get("ok", True):
        raise HTTPException(409, detail={"message": f"{kind} checks failed", "validation": validation})
    store.set_stage(state, f"samples.{kind}", "approved", approved=True,
                    notes=f"{kind} sample approved")
    store.save_state(pid, state)
    return {"ok": True}


@app.post("/api/projects/{pid}/samples/{kind}/reject")
def reject_sample(pid: str, kind: str, payload: dict = Body(default={})) -> dict:
    if kind not in ("voice", "image", "music", "clip"):
        raise HTTPException(404, "Unknown sample kind")
    state = _project(pid)
    notes = str(payload.get("notes", "")).strip() or f"{kind} sample rejected"
    store.set_stage(state, f"samples.{kind}", "changes_requested", approved=False, notes=notes)
    store.save_state(pid, state)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Production / final
# ---------------------------------------------------------------------------


@app.post("/api/projects/{pid}/production/start")
def start_production(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    stages = payload.get("stages") or ["images", "music", "tts", "assemble"]
    subtitles = bool(payload.get("subtitles", state["settings"].get("subtitles", True)))
    state["settings"]["subtitles"] = subtitles
    music_enabled = bool(state["settings"].get("music", {}).get("enabled", True))
    if not music_enabled:
        stages = [stage for stage in stages if stage != "music"]
    need_music = music_enabled and ("music" in stages or "assemble" in stages)
    gates = ops.check_gates(state, need_music=need_music)
    if not gates["ok"]:
        raise HTTPException(409, detail={"message": "Approval gates missing", "gates": gates})
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "production", lambda job: ops.start_production(
        pid, state, job, stages=list(stages), subtitles=subtitles,
    ))


@app.post("/api/projects/{pid}/production/retry")
def retry_scene(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    scene_id = int(payload.get("scene_id", 0) or 0)
    kind = str(payload.get("kind", "image"))
    if not scene_id:
        raise HTTPException(400, "scene_id is required")
    return _start(pid, f"retry_{kind}", lambda job: ops.retry_scene(
        pid, state, job, scene_id=scene_id, kind=kind,
    ))


@app.post("/api/projects/{pid}/final/render")
def render_final(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    subtitles = bool(payload.get("subtitles", state["settings"].get("subtitles", True)))
    out_name = str(payload.get("out_name", "final.mp4")).strip() or "final.mp4"
    if "/" in out_name or "\\" in out_name or not out_name.endswith(".mp4"):
        raise HTTPException(400, "out_name must be a simple .mp4 filename")
    gates = ops.check_gates(state)
    if not gates["ok"]:
        raise HTTPException(409, detail={"message": "Approval gates missing", "gates": gates})
    if store.stage(state, "production").get("status") != "done":
        raise HTTPException(409, "Run batch production before rendering the final video")
    state["settings"]["subtitles"] = subtitles
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "final", lambda job: ops.render_final(
        pid, state, job, subtitles=subtitles, out_name=out_name,
    ))


@app.post("/api/projects/{pid}/final/approve")
def approve_final(pid: str) -> dict:
    state = _project(pid)
    node = state["stages"]["final"]
    rel = node.get("path")
    if not rel:
        raise HTTPException(409, "No final render to approve")
    path = store.project_paths(pid)["root"] / rel
    if not path.exists():
        raise HTTPException(409, "Final render file is missing")
    validation = qa.validate_video(path)
    if not validation["ok"]:
        raise HTTPException(409, detail={"message": "Final render checks failed", "validation": validation})
    store.set_stage(state, "final", "approved", approved=True,
                    notes="Final render approved", validation=validation)
    store.save_state(pid, state)
    return {"ok": True, "validation": validation}


# ---------------------------------------------------------------------------
# Publish kit
# ---------------------------------------------------------------------------


@app.post("/api/projects/{pid}/publish/generate")
def generate_publish(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    if not _story(pid):
        raise HTTPException(400, "Generate or write the story first")
    _apply_llm_payload(state, payload)
    store.write_project_config(pid, state)
    store.save_state(pid, state)
    return _start(pid, "publish_kit", lambda job: ops.generate_publish_kit(pid, state, job))


@app.put("/api/projects/{pid}/publish")
def save_publish(pid: str, payload: dict = Body(...)) -> dict:
    state = _project(pid)
    try:
        return ops.save_publish_kit(pid, state, payload)
    except Exception as exc:
        raise _fail(exc)


@app.post("/api/projects/{pid}/publish/thumbnail")
def generate_publish_thumbnail(pid: str, payload: dict = Body(default={})) -> dict:
    state = _project(pid)
    node = state["stages"].get("publish", {})
    if not node.get("thumbnail_prompt"):
        raise HTTPException(409, "Generate the publish kit first")
    engine = str(payload.get("engine", "")).strip() or None
    return _start(pid, "publish_thumbnail", lambda job: ops.generate_thumbnail(
        pid, state, job, engine=engine,
    ))


# ---------------------------------------------------------------------------
# Jobs / media
# ---------------------------------------------------------------------------


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown job")
    return job.to_dict(include_logs=True)


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    job = manager.cancel(job_id)
    if not job:
        raise HTTPException(409, "Job is not running")
    return {"job": job.to_dict(include_logs=False)}


@app.get("/api/projects/{pid}/jobs")
def project_jobs(pid: str) -> list:
    _project(pid)
    return manager.list(pid)


@app.get("/api/projects/{pid}/media/{path:path}")
def project_media(pid: str, path: str) -> FileResponse:
    _project(pid)
    try:
        target = store.media_path(pid, path)
    except (PermissionError, ValueError) as exc:
        raise HTTPException(403, str(exc))
    if not target.is_file():
        raise HTTPException(404, "Media not found")
    return FileResponse(target)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((UI_DIR / "index.html").read_text(encoding="utf-8"))


@app.middleware("http")
async def no_cache(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/ui"):
        response.headers["Cache-Control"] = "no-cache"
    elif path.startswith("/api/") and "/media/" not in path:
        response.headers["Cache-Control"] = "no-store"
    return response


if UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["127.0.0.1", "localhost"],
    www_redirect=False,
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
