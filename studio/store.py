"""Project state, per-project config, and secrets for Story Studio."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
PIPELINE_DIR = ROOT / "pipeline"
BASE_CONFIG_PATH = PIPELINE_DIR / "config.json"
STUDIO_DIR = Path(__file__).resolve().parent
UI_DIR = STUDIO_DIR / "ui"
SECRETS_PATH = STUDIO_DIR / ".secrets.json"

# OpenCode Go and Console are served from different OpenAI-compatible bases.
OPENCODE_GO_BASE = "https://opencode.ai/inference/go/openai/v1"
OPENCODE_ZEN_BASE = "https://opencode.ai/inference/openai/v1"
DEFAULT_API_BASE = OPENCODE_GO_BASE
GENERIC_NEGATIVE = (
    "low quality, blurry, text, watermark, logo, signature, deformed, extra fingers, bad anatomy"
)

STAGE_PATHS = (
    "story",
    "scenes",
    "samples.voice",
    "samples.image",
    "samples.music",
    "samples.clip",
    "production",
    "final",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def base_config() -> dict:
    return load_json(BASE_CONFIG_PATH, {})


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title or "").strip("-").lower()
    if not slug:
        slug = "story-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    return slug[:60]


def default_settings() -> dict:
    cfg = base_config()
    return {
        "llm": {
            "provider": "ollama",
            "model": cfg.get("story_model", "aya-expanse:8b"),
            "ollama_url": cfg.get("ollama_url", "http://127.0.0.1:11434"),
            "api_base": DEFAULT_API_BASE,
            "temperature": 0.85,
            "num_predict": 4096,
            "session_id": "ses_" + uuid.uuid4().hex,
        },
        "image": {
            "engine": "zimage",
            **{k: v for k, v in cfg.get("image", {}).items()},
        },
        "tts": {**cfg.get("tts", {})},
        "music": {**cfg.get("music", {}), "volume": 0.10, "enabled": True},
        "publish": {
            "channel_name": "Osho Seekhe",
            "channel_tagline": "हर कहानी, एक सीख",
            "contact_email": "oshosheekhe@gmail.com",
            "hashtags": "#HindiKahani #MoralStory #OshoSeekhe",
            "cta": "नई कहानी हर मंगलवार और शुक्रवार शाम 7 बजे।",
        },
        "subtitles": True,
        "video": {"width": 1920, "height": 1080, "fps": 30},
        "comfy_url": cfg.get("comfy_url", "http://127.0.0.1:8188"),
        "ollama_url": cfg.get("ollama_url", "http://127.0.0.1:11434"),
        "story_chapters": 5,
        "story_minutes": 5,
        "story_instructions": "",
    }


def _blank_stage() -> dict:
    return {"status": "empty", "approved": False, "updated_at": None, "notes": ""}


def new_state(pid: str, title: str) -> dict:
    return {
        "project_id": pid,
        "title": title,
        "created_at": now(),
        "updated_at": now(),
        "settings": default_settings(),
        "stages": {
            "story": _blank_stage(),
            "scenes": _blank_stage(),
            "samples": {
                "voice": _blank_stage(),
                "image": _blank_stage(),
                "music": _blank_stage(),
                "clip": _blank_stage(),
            },
            "production": _blank_stage(),
            "final": _blank_stage(),
            "publish": _blank_stage(),
        },
        "versions": {"story": 0, "scenes": 0},
        "history": [],
    }


def project_paths(pid: str) -> dict:
    safe = re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,80}", pid or "")
    if not safe or pid in (".", ".."):
        raise ValueError("invalid project id")
    root = PROJECTS_DIR / pid
    return {
        "root": root,
        "images": root / "images",
        "audio": root / "audio",
        "video": root / "video",
        "studio": root / "studio",
        "samples": root / "studio" / "samples",
        "versions": root / "studio" / "versions",
        "logs": root / "studio" / "logs",
        "state": root / "studio" / "state.json",
        "config": root / "studio" / "config.json",
        "story": root / "story.md",
        "scenes": root / "scenes.json",
        "project": root / "project.json",
    }


def ensure_dirs(pid: str) -> dict:
    paths = project_paths(pid)
    for key in ("root", "images", "audio", "video", "studio", "samples", "versions", "logs"):
        paths[key].mkdir(parents=True, exist_ok=True)
    for kind in ("voice", "image", "music", "clip"):
        (paths["samples"] / kind).mkdir(parents=True, exist_ok=True)
    return paths


def _import_stage_state(state: dict, pid: str) -> None:
    """Give existing (pre-studio) projects sensible stage states."""
    paths = project_paths(pid)
    if paths["story"].exists():
        state["stages"]["story"] = {
            "status": "approved", "approved": True, "updated_at": now(),
            "notes": "Imported existing story",
        }
    if paths["scenes"].exists():
        state["stages"]["scenes"] = {
            "status": "approved", "approved": True, "updated_at": now(),
            "notes": "Imported existing scene plan",
        }
    if (paths["images"] / "scene_001.png").exists():
        state["stages"]["samples"]["image"] = {
            "status": "approved", "approved": True, "updated_at": now(),
            "notes": "Imported existing images",
        }
    if (paths["audio"] / "scene_001.wav").exists():
        state["stages"]["samples"]["voice"] = {
            "status": "approved", "approved": True, "updated_at": now(),
            "notes": "Imported existing narration",
        }
    if (paths["audio"] / "music.mp3").exists():
        state["stages"]["samples"]["music"] = {
            "status": "approved", "approved": True, "updated_at": now(),
            "notes": "Imported existing music",
        }
    if (paths["video"] / "pilot.mp4").exists() or (paths["video"] / "final.mp4").exists():
        state["stages"]["production"] = {
            "status": "done", "approved": True, "updated_at": now(),
            "notes": "Imported existing production",
        }


def load_state(pid: str) -> dict:
    paths = project_paths(pid)
    if not paths["root"].is_dir():
        raise FileNotFoundError(pid)
    state = load_json(paths["state"], {})
    if not state:
        project = load_json(paths["project"], {})
        state = new_state(pid, project.get("title", pid))
        _import_stage_state(state, pid)
        save_state(pid, state)
    # Defensive fill for older state files.
    state.setdefault("settings", default_settings())
    settings = state["settings"]
    settings.setdefault("story_minutes", 5)
    settings.setdefault("story_chapters", 5)
    settings.setdefault("story_instructions", "")
    music = settings.setdefault("music", {})
    music.setdefault("enabled", True)
    publish = settings.setdefault("publish", {})
    for key, value in default_settings().get("publish", {}).items():
        publish.setdefault(key, value)
    llm = settings.setdefault("llm", {})
    llm.setdefault("provider", "ollama")
    llm.setdefault("model", "aya-expanse:8b")
    llm.setdefault("ollama_url", settings.get("ollama_url", "http://127.0.0.1:11434"))
    llm.setdefault("api_base", DEFAULT_API_BASE)
    llm.setdefault("temperature", 0.85)
    llm.setdefault("num_predict", 4096)
    if not llm.get("session_id"):
        llm["session_id"] = "ses_" + uuid.uuid4().hex
    if llm.get("api_base") in ("https://opencode.ai/zen/v1", "https://opencode.ai/zen"):
        # The old Zen URL was replaced by Console's inference base.
        llm["api_base"] = OPENCODE_ZEN_BASE
        if llm.get("provider") == "openai":
            llm["provider"] = "opencode"

    base_image = base_config().get("image", {})
    image = settings.setdefault("image", {})
    image.setdefault("engine", "zimage")
    image.setdefault("style_prefix", base_image.get("style_prefix", ""))
    image.setdefault("character", base_image.get("character", ""))
    if not image.get("negative_prompt"):
        style = str(image.get("style_prefix", "")).lower()
        if "minimalist" in style or "webcomic" in style:
            image["negative_prompt"] = base_image.get("negative_prompt", GENERIC_NEGATIVE)
        else:
            image["negative_prompt"] = GENERIC_NEGATIVE

    state.setdefault("stages", {})
    state["stages"].setdefault("story", _blank_stage())
    state["stages"].setdefault("scenes", _blank_stage())
    state["stages"].setdefault("samples", {})
    for kind in ("voice", "image", "music", "clip"):
        state["stages"]["samples"].setdefault(kind, _blank_stage())
    state["stages"].setdefault("production", _blank_stage())
    state["stages"].setdefault("final", _blank_stage())
    state["stages"].setdefault("publish", _blank_stage())
    state.setdefault("versions", {"story": 0, "scenes": 0})
    state.setdefault("history", [])
    # Clean up keys created by an early buggy path helper.
    for key in ("story", "scenes", "samples", "production", "final"):
        if key in state and key not in ("stages", "settings", "versions", "history"):
            state.pop(key, None)
    return state


def save_state(pid: str, state: dict) -> None:
    state["updated_at"] = now()
    save_json(project_paths(pid)["state"], state)


def list_projects() -> list[dict]:
    out: list[dict] = []
    if not PROJECTS_DIR.is_dir():
        return out
    for entry in sorted(PROJECTS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith(("_", ".")):
            continue
        try:
            project = load_json(entry / "project.json", {})
            try:
                state = load_state(entry.name)
            except Exception:
                state = load_json(entry / "studio" / "state.json", {})
            images = len(list((entry / "images").glob("scene_*.png"))) if (entry / "images").is_dir() else 0
            audio = len(list((entry / "audio").glob("scene_*.wav"))) if (entry / "audio").is_dir() else 0
            final = None
            for name in ("final.mp4", "pilot.mp4", "pilot_consistent.mp4"):
                if (entry / "video" / name).exists():
                    final = name
                    break
            out.append({
                "id": entry.name,
                "title": project.get("title", state.get("title", entry.name)),
                "pipeline_type": project.get("pipeline_type", "story"),
                "updated_at": state.get("updated_at") or datetime.fromtimestamp(
                    entry.stat().st_mtime, timezone.utc
                ).isoformat(timespec="seconds"),
                "stage_status": {
                    "story": state.get("stages", {}).get("story", {}).get("status", "empty"),
                    "scenes": state.get("stages", {}).get("scenes", {}).get("status", "empty"),
                    "samples": _samples_status(state),
                    "production": state.get("stages", {}).get("production", {}).get("status", "empty"),
                    "final": state.get("stages", {}).get("final", {}).get("status", "empty"),
                },
                "images": images,
                "audio": audio,
                "final": final,
            })
        except Exception:
            continue
    out.sort(key=lambda p: p.get("updated_at") or "", reverse=True)
    return out


def _samples_status(state: dict) -> str:
    samples = state.get("stages", {}).get("samples", {})
    statuses = [samples.get(k, {}).get("status", "empty") for k in ("voice", "image", "music", "clip")]
    if all(s == "approved" for s in statuses):
        return "approved"
    if any(s in ("running", "draft", "ready") for s in statuses):
        return "draft"
    return "empty"


def create_project(
    title: str,
    topic: str = "",
    minutes: float = 5,
    chapters: int = 5,
    slug_source: str | None = None,
) -> dict:
    pid = slugify(slug_source or title)
    candidate = pid
    counter = 2
    while (PROJECTS_DIR / candidate).exists():
        candidate = f"{pid}-{counter}"
        counter += 1
    pid = candidate
    paths = ensure_dirs(pid)
    project = {
        "pipeline_type": "animated-explainer",
        "title": title,
        "language": "hi",
        "status": "draft",
        "created_by": "story studio",
        "notes": topic,
    }
    save_json(paths["project"], project)
    state = new_state(pid, title)
    state["settings"]["story_chapters"] = chapters
    state["settings"]["story_minutes"] = minutes
    state["settings"]["story_topic"] = topic
    save_state(pid, state)
    write_project_config(pid, state)
    add_history(state, "project_created", title)
    save_state(pid, state)
    return state


def write_project_config(pid: str, state: dict) -> Path:
    paths = ensure_dirs(pid)
    cfg = base_config()
    settings = state.get("settings", default_settings())
    cfg["comfy_url"] = settings.get("comfy_url", cfg.get("comfy_url"))
    cfg["ollama_url"] = settings.get("ollama_url", cfg.get("ollama_url"))
    cfg["project_dir"] = str(paths["root"]).replace("\\", "/")
    if settings.get("llm", {}).get("provider") == "ollama":
        cfg["story_model"] = settings["llm"].get("model", cfg.get("story_model"))

    image = dict(settings.get("image", {}))
    image.pop("engine", None)
    cfg.setdefault("image", {}).update(image)

    cfg.setdefault("tts", {}).update(settings.get("tts", {}))
    music = dict(settings.get("music", {}))
    volume = float(music.pop("volume", 0.10))
    cfg.setdefault("music", {}).update(music)
    cfg["music"]["volume"] = volume
    cfg["video"] = settings.get("video", {"width": 1920, "height": 1080, "fps": 30})
    save_json(paths["config"], cfg)
    return paths["config"]


def write_config_for_dir(target_dir: Path, state: dict) -> Path:
    """Write a config whose project_dir points at an arbitrary preview project."""
    cfg = base_config()
    settings = state.get("settings", default_settings())
    cfg["comfy_url"] = settings.get("comfy_url", cfg.get("comfy_url"))
    cfg["ollama_url"] = settings.get("ollama_url", cfg.get("ollama_url"))
    cfg["project_dir"] = str(target_dir).replace("\\", "/")
    image = dict(settings.get("image", {}))
    image.pop("engine", None)
    cfg.setdefault("image", {}).update(image)
    cfg.setdefault("tts", {}).update(settings.get("tts", {}))
    music = dict(settings.get("music", {}))
    volume = float(music.pop("volume", 0.10))
    cfg.setdefault("music", {}).update(music)
    cfg["music"]["volume"] = volume
    path = target_dir / "studio" / "config.json"
    save_json(path, cfg)
    return path


def stage(state: dict, path: str) -> dict:
    node = state.setdefault("stages", {})
    for part in path.split("."):
        node = node.setdefault(part, {})
    return node


def set_stage(state: dict, stage_path: str, status: str, **values: Any) -> None:
    node = stage(state, stage_path)
    node["status"] = status
    node["updated_at"] = now()
    node.update(values)
    add_history(state, f"{stage_path}:{status}", values.get("notes", ""))


def invalidate(state: dict, paths: list[str], reason: str = "upstream change") -> None:
    for path in paths:
        node = stage(state, path)
        if node.get("status") not in ("empty",):
            node["status"] = "stale"
            node["approved"] = False
            node["updated_at"] = now()
            node["notes"] = f"Invalidated: {reason}"
    add_history(state, "invalidate", f"{reason}: {', '.join(paths)}")


def add_history(state: dict, event: str, detail: str = "") -> None:
    state.setdefault("history", []).append({"ts": now(), "event": event, "detail": detail})
    if len(state["history"]) > 300:
        state["history"] = state["history"][-300:]


def version_artifact(pid: str, state: dict, name: str, source: Path) -> int:
    if not source.exists():
        return state.get("versions", {}).get(name, 0)
    state.setdefault("versions", {})
    state["versions"][name] = int(state["versions"].get(name, 0)) + 1
    n = state["versions"][name]
    dest = project_paths(pid)["versions"] / f"{name}_v{n:03d}{source.suffix}"
    shutil.copy2(source, dest)
    return n


def load_secrets() -> dict:
    return load_json(SECRETS_PATH, {})


def save_secrets(data: dict) -> None:
    current = load_secrets()
    current.update(data)
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")


def get_api_key() -> str:
    for env in ("STUDIO_LLM_API_KEY", "OPENCODE_API_KEY", "OPENAI_API_KEY"):
        if os.environ.get(env):
            return os.environ[env]
    return load_secrets().get("llm_api_key", "")


def public_settings(state: dict) -> dict:
    settings = json.loads(json.dumps(state.get("settings", {})))
    settings["llm"]["has_api_key"] = bool(get_api_key())
    return settings


def public_state(state: dict) -> dict:
    out = json.loads(json.dumps(state))
    out["settings"] = public_settings(state)
    return out


def media_path(pid: str, rel: str) -> Path:
    root = project_paths(pid)["root"].resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PermissionError("path escapes project") from exc
    return target
