from backend.app.domain import TaskJobStatus
from backend.app.integrations.queue import InMemoryTaskExecutionQueue


def test_m4_in_memory_queue_lifecycle_is_explicit() -> None:
    queue = InMemoryTaskExecutionQueue()

    job = queue.enqueue(
        task_id="task_1",
        owner_user_id="alice",
        payload={"content": "hello"},
    )
    assert job.status is TaskJobStatus.QUEUED

    claimed = queue.claim(job.id)
    assert claimed is not None
    assert claimed.status is TaskJobStatus.RUNNING
    assert claimed.started_at is not None

    completed = queue.complete(job.id, result_task_id="task_1")
    assert completed.status is TaskJobStatus.SUCCEEDED
    assert completed.result_task_id == "task_1"
    assert completed.completed_at is not None


def test_m4_in_memory_queue_failure_is_explicit() -> None:
    queue = InMemoryTaskExecutionQueue()
    job = queue.enqueue(task_id="task_1", owner_user_id="alice", payload={})

    queue.claim(job.id)
    failed = queue.fail(job.id, error_message="boom")

    assert failed.status is TaskJobStatus.FAILED
    assert failed.error_message == "boom"
    assert failed.completed_at is not None
