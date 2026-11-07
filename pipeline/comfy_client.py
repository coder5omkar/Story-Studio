"""Minimal ComfyUI HTTP client for the story pipeline."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import requests


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188") -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    def is_up(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return r.ok
        except requests.RequestException:
            return False

    def queue(self, workflow: dict) -> str:
        r = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": workflow, "client_id": self.client_id},
            timeout=30,
        )
        if not r.ok:
            raise ComfyError(f"Queue failed ({r.status_code}): {r.text[:2000]}")
        data = r.json()
        if data.get("node_errors"):
            raise ComfyError(f"Workflow node errors: {json.dumps(data['node_errors'])[:3000]}")
        return data["prompt_id"]

    def wait(self, prompt_id: str, timeout: float = 1800) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=15)
            if r.ok:
                data = r.json()
                if prompt_id in data:
                    return data[prompt_id]
            time.sleep(1.0)
        raise ComfyError(f"Timed out waiting for prompt {prompt_id}")

    def generate(self, workflow: dict, dest: Path, timeout: float = 1800) -> Path:
        prompt_id = self.queue(workflow)
        history = self.wait(prompt_id, timeout=timeout)
        item = self._first_output(history)
        data = self._download(item)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest

    def _first_output(self, history: dict) -> dict:
        outputs = history.get("outputs", {})
        for node_output in outputs.values():
            for key in ("images", "audio", "gifs", "videos"):
                items = node_output.get(key)
                if items:
                    return items[0]
        raise ComfyError(f"No downloadable output in history: {json.dumps(history)[:2000]}")

    def _download(self, item: dict) -> bytes:
        params = {
            "filename": item["filename"],
            "subfolder": item.get("subfolder", ""),
            "type": item.get("type", "output"),
        }
        r = requests.get(f"{self.base_url}/view", params=params, timeout=120)
        if not r.ok:
            raise ComfyError(f"Download failed ({r.status_code}): {r.text[:1000]}")
        return r.content


def load_workflow(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def patch(workflow: dict, node_id: str, values: dict) -> dict:
    node = workflow[str(node_id)]
    node.setdefault("inputs", {}).update(values)
    return workflow
