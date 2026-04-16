from __future__ import annotations

from collections import deque
from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from typing import Protocol
from uuid import uuid4

from backend.app.domain import TaskExecutionJob, TaskJobStatus


class TaskExecutionQueue(Protocol):
    def enqueue(self, *, task_id: str, owner_user_id: str, payload: dict[str, object]) -> TaskExecutionJob: ...

    def get(self, job_id: str) -> TaskExecutionJob | None: ...

    def claim(self, job_id: str) -> TaskExecutionJob | None: ...

    def claim_next(self) -> TaskExecutionJob | None: ...

    def complete(self, job_id: str, *, result_task_id: str) -> TaskExecutionJob: ...

    def fail(self, job_id: str, *, error_message: str) -> TaskExecutionJob: ...


class InMemoryTaskExecutionQueue:
    """In-process M4 queue foundation.

    This is intentionally not a production durable queue. It exists to define
    lifecycle semantics and worker wiring without adding Redis/Celery/RQ in M4.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, TaskExecutionJob] = {}
        self._queue: deque[str] = deque()
        self._lock = Lock()

    def enqueue(self, *, task_id: str, owner_user_id: str, payload: dict[str, object]) -> TaskExecutionJob:
        with self._lock:
            job = TaskExecutionJob(
                id=f"job_{uuid4().hex}",
                task_id=task_id,
                owner_user_id=owner_user_id,
                payload=dict(payload),
                status=TaskJobStatus.QUEUED,
            )
            self._jobs[job.id] = job
            self._queue.append(job.id)
            return job

    def get(self, job_id: str) -> TaskExecutionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def claim(self, job_id: str) -> TaskExecutionJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.status is not TaskJobStatus.QUEUED:
                return job
            claimed = replace(job, status=TaskJobStatus.RUNNING, started_at=datetime.now(timezone.utc))
            self._jobs[job_id] = claimed
            return claimed

    def claim_next(self) -> TaskExecutionJob | None:
        with self._lock:
            while self._queue:
                job_id = self._queue.popleft()
                job = self._jobs.get(job_id)
                if job is None or job.status is not TaskJobStatus.QUEUED:
                    continue
                claimed = replace(job, status=TaskJobStatus.RUNNING, started_at=datetime.now(timezone.utc))
                self._jobs[job_id] = claimed
                return claimed
            return None

    def complete(self, job_id: str, *, result_task_id: str) -> TaskExecutionJob:
        with self._lock:
            job = self._require_job(job_id)
            completed = replace(
                job,
                status=TaskJobStatus.SUCCEEDED,
                result_task_id=result_task_id,
                error_message=None,
                completed_at=datetime.now(timezone.utc),
            )
            self._jobs[job_id] = completed
            return completed

    def fail(self, job_id: str, *, error_message: str) -> TaskExecutionJob:
        with self._lock:
            job = self._require_job(job_id)
            failed = replace(
                job,
                status=TaskJobStatus.FAILED,
                error_message=error_message,
                completed_at=datetime.now(timezone.utc),
            )
            self._jobs[job_id] = failed
            return failed

    def _require_job(self, job_id: str) -> TaskExecutionJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job
