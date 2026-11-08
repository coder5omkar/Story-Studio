"""Tiny in-process job manager with progress + log polling."""

from __future__ import annotations

import os
import subprocess
import threading
import time
import traceback
import uuid
from collections import deque
from typing import Callable


class JobCancelled(RuntimeError):
    """Raised inside a job when the user requests cancellation."""


def _kill_process_tree(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
            )
            return
        except Exception:
            pass
    try:
        proc.terminate()
    except Exception:
        pass


class Job:
    def __init__(self, project_id: str, kind: str) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.project_id = project_id
        self.kind = kind
        self.status = "queued"
        self.progress = 0
        self.message = "Queued"
        self.logs: deque[str] = deque(maxlen=800)
        self.result = None
        self.error = ""
        self.created_at = time.time()
        self.finished_at = None
        self.cancel_event = threading.Event()
        self._process: subprocess.Popen | None = None
        self._process_lock = threading.Lock()

    def log(self, line: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        for part in str(line).replace("\r", "").split("\n"):
            if part.strip():
                self.logs.append(f"[{stamp}] {part.rstrip()}")

    def set_progress(self, pct: float, message: str = "") -> None:
        self.progress = max(0, min(100, round(float(pct), 1)))
        if message:
            self.message = message

    def set_process(self, proc: subprocess.Popen) -> None:
        with self._process_lock:
            self._process = proc

    def clear_process(self, proc: subprocess.Popen | None = None) -> None:
        with self._process_lock:
            if proc is None or self._process is proc:
                self._process = None

    def cancel(self) -> bool:
        if self.status not in ("queued", "running", "cancelling"):
            return False
        self.cancel_event.set()
        if self.status != "cancelling":
            self.status = "cancelling"
            self.message = "Cancelling…"
            self.log("Cancel requested")
        with self._process_lock:
            proc = self._process
        _kill_process_tree(proc)
        return True

    def check_cancelled(self) -> None:
        if self.cancel_event.is_set():
            raise JobCancelled("Job cancelled")

    def to_dict(self, include_logs: bool = True) -> dict:
        out = {
            "id": self.id,
            "project_id": self.project_id,
            "kind": self.kind,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "result": self.result,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }
        if include_logs:
            out["logs"] = list(self.logs)
        return out


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._active: dict[str, str] = {}
        self._lock = threading.Lock()

    def active_for_project(self, project_id: str) -> Job | None:
        with self._lock:
            job_id = self._active.get(project_id)
            return self._jobs.get(job_id) if job_id else None

    def start(self, project_id: str, kind: str, fn: Callable[[Job], object]) -> Job:
        with self._lock:
            active = self._active.get(project_id)
            if active and self._jobs.get(active) and self._jobs[active].status in ("queued", "running", "cancelling"):
                raise RuntimeError(f"A job is already running for this project: {self._jobs[active].kind}")
            job = Job(project_id, kind)
            self._jobs[job.id] = job
            self._active[project_id] = job.id
        thread = threading.Thread(target=self._run, args=(job, fn), daemon=True)
        thread.start()
        return job

    def cancel(self, job_id: str) -> Job | None:
        job = self.get(job_id)
        if not job or not job.cancel():
            return None
        return job

    def _run(self, job: Job, fn: Callable[[Job], object]) -> None:
        job.status = "running"
        job.message = "Running"
        try:
            job.check_cancelled()
            job.result = fn(job)
            job.check_cancelled()
            job.status = "done"
            job.progress = 100
            job.message = "Done"
        except JobCancelled:
            job.status = "cancelled"
            job.error = ""
            job.message = "Cancelled"
            job.log("Job cancelled")
        except Exception as exc:
            if job.cancel_event.is_set():
                job.status = "cancelled"
                job.error = ""
                job.message = "Cancelled"
                job.log("Job cancelled")
            else:
                job.status = "failed"
                job.error = str(exc)
                job.message = "Failed"
                job.log(f"ERROR: {exc}")
                job.log(traceback.format_exc())
        finally:
            job.finished_at = time.time()
            job.clear_process()
            with self._lock:
                self._active.pop(job.project_id, None)
            self._prune()

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, project_id: str | None = None) -> list[dict]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        if project_id:
            jobs = [j for j in jobs if j.project_id == project_id]
        return [j.to_dict(include_logs=False) for j in jobs[:30]]

    def _prune(self) -> None:
        with self._lock:
            if len(self._jobs) <= 60:
                return
            finished = sorted(
                (j for j in self._jobs.values() if j.status in ("done", "failed", "cancelled")),
                key=lambda j: j.created_at,
            )
            for job in finished[: len(self._jobs) - 60]:
                self._jobs.pop(job.id, None)


manager = JobManager()
